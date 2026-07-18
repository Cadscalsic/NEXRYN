"""Post-execution maintenance and reporting governance."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from runtime.resource_governance.deferred_maintenance_plan import (
    MaintenanceWorkItem,
    MaintenanceWorkStatus,
    PostExecutionPlan,
)
from runtime.resource_governance.deferred_maintenance_ledger import DeferredMaintenanceLedger
from runtime.resource_governance.deferred_work_registry import DeferredWorkRegistry
from runtime.resource_governance.execution_policy import ExecutionPolicyName
from runtime.resource_governance.maintenance_budget import MaintenanceBudget
from runtime.resource_governance.maintenance_classifier import (
    MaintenanceClassifier,
    MaintenanceWorkCategory,
)
from runtime.resource_governance.maintenance_trigger_resolver import MaintenanceTriggerResolver
from runtime.resource_governance.persistence_governor import PersistenceGovernor
from runtime.resource_governance.post_success_guard import PostSuccessGuard
from runtime.resource_governance.post_processing_budget import (
    PostProcessingBudget,
    PostProcessingDecision,
)
from runtime.resource_governance.reporting_governor import ReportingGovernor
from runtime.resource_governance.serialization_governor import SerializationGovernor


DEFAULT_POST_EXECUTION_WORK = (
    "preserve_final_prediction",
    "preserve_final_evaluation",
    "preserve_terminal_state",
    "preserve_execution_identifier",
    "lightweight_timing_summary",
    "deferred_work_declaration",
    "compact_execution_summary",
    "small_registry_delta",
    "semantic_memory_consolidation",
    "knowledge_fabric_integration",
    "fabric_topology_intelligence",
    "reasoning_corridor_generation",
    "large_shared_state_persistence",
    "full_canonical_report_construction",
    "domain_constitution_validation",
    "program_ecosystem_aggregation",
    "complete_signal_ledger",
    "full_canonical_binding_validation",
    "candidate_expansion",
    "retry",
    "repair_after_exact_success",
)


class PostExecutionGovernor:
    def __init__(self):
        self.classifier = MaintenanceClassifier()
        self.registry = DeferredWorkRegistry()
        self.ledger = DeferredMaintenanceLedger()
        self.trigger_resolver = MaintenanceTriggerResolver()
        self.reporting_governor = ReportingGovernor()
        self.persistence_governor = PersistenceGovernor()
        self.serialization_governor = SerializationGovernor()
        self.post_success_guard = PostSuccessGuard()
        self.last_plan: PostExecutionPlan | None = None
        self.critical_completed: list[str] = []
        self.bounded_completed: list[str] = []
        self.result_available_timestamp: str | None = None
        self.maintenance_failures: list[dict[str, str]] = []
        self.post_processing_budget: PostProcessingBudget | None = None
        self.decision_counts: dict[str, int] = {}

    def build_plan(
        self,
        execution_id: str,
        task_id: str,
        terminal_state: str,
        policy: ExecutionPolicyName,
        task_profile: dict[str, Any] | None = None,
        work_types: list[str] | None = None,
        triggers: list[str] | None = None,
        state_versions: dict[str, Any] | None = None,
    ) -> PostExecutionPlan:
        budget = MaintenanceBudget.for_policy(policy)
        post_budget = PostProcessingBudget.for_policy(policy)
        self.post_processing_budget = post_budget
        trigger_result = self.trigger_resolver.evaluate(triggers, state_versions)
        report_contract = self.reporting_governor.select_projection(policy, terminal_state)
        persistence_contract = self.persistence_governor.select_contract(
            policy,
            state_changed=any(trigger_result["changes"].values()),
        )
        plan = PostExecutionPlan(
            execution_id=execution_id,
            task_id=task_id,
            terminal_state=terminal_state,
            execution_policy=policy.value,
            task_profile=dict(task_profile or {}),
            state_change_signatures=trigger_result["signatures"],
            synchronous_budget={
                "seconds": post_budget.maximum_sync_seconds,
                "serialization_budget_bytes": post_budget.maximum_serialized_bytes,
                "bounded_operations": post_budget.maximum_bounded_operations,
                "objects_visited": post_budget.maximum_objects_visited,
                "registry_scans": post_budget.maximum_registry_scans,
            },
            deferred_budget={"seconds": budget.deferred_budget_seconds},
            persistence_contract=persistence_contract.as_dict(),
            reporting_contract=report_contract.as_dict(),
        )
        for work_type in work_types or list(DEFAULT_POST_EXECUTION_WORK):
            classification = self.classifier.classify(work_type, policy=policy)
            item = MaintenanceWorkItem.create(
                execution_id=execution_id,
                work_type=work_type,
                component_name=classification.component_name,
                work_category=classification.category.value,
                trigger_reason=classification.reason,
                dependency_versions=state_versions,
                input_signature=trigger_result["signatures"].get(_signature_name_for(work_type), ""),
                max_duration=budget.synchronous_budget_seconds,
                max_serialized_bytes=budget.serialization_budget_bytes,
            )
            self._add_item(plan, item, classification.category, policy, trigger_result)
            plan.maintenance_reasons.append(classification.reason)
        plan.plan_status = "READY"
        self.last_plan = plan
        return plan

    def register_deferred(self, item: MaintenanceWorkItem) -> MaintenanceWorkItem:
        item.status = MaintenanceWorkStatus.DEFERRED.value
        self.ledger.register(item)
        return self.registry.register(item)

    def execute_critical(self, plan: PostExecutionPlan) -> list[MaintenanceWorkItem]:
        completed = []
        for item in plan.critical_sync_work:
            item.status = MaintenanceWorkStatus.COMPLETED.value
            item.completed_at = str(datetime.utcnow())
            completed.append(item)
            self.critical_completed.append(item.work_type)
            self.ledger.register(item)
            self._record_decision(item.work_type, PostProcessingDecision.RUN_CRITICAL_SYNC, "critical_completion_required")
        return completed

    def execute_bounded(self, plan: PostExecutionPlan, elapsed: float = 0.0) -> list[MaintenanceWorkItem]:
        completed = []
        budget = plan.synchronous_budget.get("seconds", 0.0)
        for item in plan.bounded_sync_work:
            allowed, _ = self.post_success_guard.allow(
                item.work_type,
                MaintenanceWorkCategory.BOUNDED_SYNC,
                ExecutionPolicyName(plan.execution_policy),
                elapsed,
                budget,
            )
            if allowed:
                budget_allowed = True
                if self.post_processing_budget is not None:
                    budget_allowed = self.post_processing_budget.consume_bounded(
                        item.work_type,
                        duration=elapsed,
                        serialized_bytes=min(item.max_serialized_bytes, 1_024),
                    )
                if not budget_allowed:
                    self.register_deferred(item)
                    continue
                item.status = MaintenanceWorkStatus.COMPLETED.value
                item.completed_at = str(datetime.utcnow())
                completed.append(item)
                self.bounded_completed.append(item.work_type)
                self.ledger.register(item)
                self._record_decision(item.work_type, PostProcessingDecision.RUN_BOUNDED_SYNC, "bounded_sync_budget_available")
            else:
                self.register_deferred(item)
                self._record_decision(item.work_type, PostProcessingDecision.DEFER, "bounded_sync_budget_exceeded")
        return completed

    def enter_result_available(self, plan: PostExecutionPlan) -> str:
        timestamp = str(datetime.utcnow())
        plan.result_available_timestamp = timestamp
        self.result_available_timestamp = timestamp
        return timestamp

    def _add_item(self, plan, item, category, policy, trigger_result):
        trigger_satisfied = _trigger_satisfied(item.work_type, trigger_result)
        if category == MaintenanceWorkCategory.CRITICAL_SYNC:
            plan.critical_sync_work.append(item)
            self._record_decision(item.work_type, PostProcessingDecision.RUN_CRITICAL_SYNC, "critical_sync")
        elif category == MaintenanceWorkCategory.BOUNDED_SYNC:
            plan.bounded_sync_work.append(item)
            self._record_decision(item.work_type, PostProcessingDecision.RUN_BOUNDED_SYNC, "bounded_sync_candidate")
        elif category == MaintenanceWorkCategory.DEFERRED:
            plan.deferred_work.append(self.register_deferred(item))
            self._record_decision(item.work_type, PostProcessingDecision.DEFER, "deferred_maintenance")
        elif category == MaintenanceWorkCategory.CHANGE_TRIGGERED:
            if trigger_satisfied:
                plan.change_triggered_work.append(item)
                self.ledger.register(item)
                self._record_decision(item.work_type, PostProcessingDecision.RUN_IF_CHANGED, "state_signature_changed")
            else:
                item.status = MaintenanceWorkStatus.SKIPPED_UNCHANGED.value
                plan.change_triggered_work.append(item)
                self.registry.register(item)
                self.ledger.register(item)
                self.registry.skip_unchanged(item.idempotency_key)
                self._record_decision(item.work_type, PostProcessingDecision.SKIP_UNCHANGED, "state_signature_unchanged")
        elif category == MaintenanceWorkCategory.DIAGNOSTIC_ONLY:
            if policy == ExecutionPolicyName.DIAGNOSTIC:
                plan.diagnostic_work.append(item)
                self.ledger.register(item)
                self._record_decision(item.work_type, PostProcessingDecision.RUN_BOUNDED_SYNC, "diagnostic_policy")
            else:
                item.status = MaintenanceWorkStatus.SKIPPED_POLICY.value
                plan.diagnostic_work.append(item)
                self._record_decision(item.work_type, PostProcessingDecision.SKIP_DIAGNOSTIC_ONLY, "diagnostic_policy_required")
        else:
            item.status = MaintenanceWorkStatus.CANCELLED.value
            plan.prohibited_work.append(item)
            self._record_decision(item.work_type, PostProcessingDecision.REJECT_AFTER_TERMINAL, "prohibited_after_terminal")

    def _record_decision(
        self,
        capability_id: str,
        decision: PostProcessingDecision,
        reason: str,
    ) -> None:
        self.decision_counts[decision.value] = self.decision_counts.get(decision.value, 0) + 1
        if self.post_processing_budget is not None:
            self.post_processing_budget.record_decision(capability_id, decision, reason)


def _signature_name_for(work_type: str) -> str:
    if "semantic_memory" in work_type:
        return "semantic_memory"
    if "fabric" in work_type:
        return "knowledge_fabric_relationships"
    if "program" in work_type:
        return "program_registry"
    if "domain" in work_type:
        return "cognitive_domain_registry"
    return "shared_cognitive_state"


def _trigger_satisfied(work_type: str, trigger_result: dict[str, Any]) -> bool:
    if work_type == "domain_constitution_validation":
        return bool(trigger_result["domain_constitution_validation"])
    if work_type == "knowledge_fabric_topology_rebuild":
        return bool(trigger_result["knowledge_fabric_topology_rebuild"])
    if work_type == "program_ecosystem_aggregation":
        return bool(trigger_result["program_ecosystem_aggregation"])
    return False


__all__ = ["DEFAULT_POST_EXECUTION_WORK", "PostExecutionGovernor"]
