"""Post-execution maintenance work classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from runtime.resource_governance.execution_policy import ExecutionPolicyName


class MaintenanceWorkCategory(str, Enum):
    CRITICAL_SYNC = "CRITICAL_SYNC"
    BOUNDED_SYNC = "BOUNDED_SYNC"
    DEFERRED = "DEFERRED"
    CHANGE_TRIGGERED = "CHANGE_TRIGGERED"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    PROHIBITED_AFTER_TERMINAL = "PROHIBITED_AFTER_TERMINAL"


class MaintenanceTriggerType(str, Enum):
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    EXACT_SUCCESS = "EXACT_SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILURE_RECORDED = "FAILURE_RECORDED"
    SEMANTIC_MEMORY_CHANGED = "SEMANTIC_MEMORY_CHANGED"
    CONCEPT_REGISTRY_CHANGED = "CONCEPT_REGISTRY_CHANGED"
    PROGRAM_REGISTRY_CHANGED = "PROGRAM_REGISTRY_CHANGED"
    DOMAIN_REGISTRY_CHANGED = "DOMAIN_REGISTRY_CHANGED"
    CAPABILITY_OWNERSHIP_CHANGED = "CAPABILITY_OWNERSHIP_CHANGED"
    KNOWLEDGE_FABRIC_CHANGED = "KNOWLEDGE_FABRIC_CHANGED"
    NEW_EXECUTION_PACKAGE = "NEW_EXECUTION_PACKAGE"
    GOVERNANCE_VIOLATION = "GOVERNANCE_VIOLATION"
    DIAGNOSTIC_REQUESTED = "DIAGNOSTIC_REQUESTED"
    MAINTENANCE_WINDOW_OPENED = "MAINTENANCE_WINDOW_OPENED"


@dataclass(frozen=True)
class MaintenanceClassification:
    work_type: str
    component_name: str
    category: MaintenanceWorkCategory
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "work_type": self.work_type,
            "component_name": self.component_name,
            "category": self.category.value,
            "reason": self.reason,
        }


CRITICAL_WORK = {
    "preserve_final_prediction",
    "preserve_final_evaluation",
    "preserve_terminal_state",
    "preserve_execution_identifier",
    "preserve_minimal_failure_information",
    "lightweight_timing_summary",
    "deferred_work_declaration",
    "critical_governance_violation",
    "minimal_recovery_checkpoint",
}

BOUNDED_WORK = {
    "compact_execution_summary",
    "minimal_semantic_attribution_summary",
    "minimal_program_decision_provenance",
    "small_registry_delta",
    "lightweight_state_checksum",
    "bounded_telemetry_summary",
}

DEFERRED_WORK = {
    "semantic_memory_consolidation",
    "semantic_memory_enrichment",
    "knowledge_fabric_integration",
    "cross_domain_relationship_discovery",
    "fabric_topology_intelligence",
    "reasoning_corridor_generation",
    "concept_lifecycle_aggregation",
    "program_lifecycle_aggregation",
    "domain_ecosystem_aggregation",
    "large_shared_state_persistence",
    "deep_report_appendix_compression",
    "full_canonical_report_construction",
    "historical_analytics",
    "training_aggregation",
}

CHANGE_TRIGGERED_WORK = {
    "domain_constitution_validation",
    "knowledge_fabric_topology_rebuild",
    "program_ecosystem_aggregation",
    "capability_registry_validation",
}

DIAGNOSTIC_WORK = {
    "full_profiling_dump",
    "complete_signal_ledger",
    "complete_transition_ledger",
    "full_dependency_graph",
    "raw_timing_nodes",
    "complete_candidate_simulations",
    "deep_appendix_serialization",
    "complete_registry_snapshots",
    "duplicate_object_size_scan",
    "full_canonical_binding_validation",
}

PROHIBITED_WORK = {
    "new_reasoning_route_activation",
    "candidate_expansion",
    "hypothesis_generation",
    "retry",
    "repair_after_exact_success",
    "semantic_search_expansion",
    "counterfactual_search",
    "deep_dependency_expansion",
    "new_transformation_execution",
    "program_competition",
}


class MaintenanceClassifier:
    def classify(
        self,
        work_type: str,
        component_name: str = "",
        policy: ExecutionPolicyName = ExecutionPolicyName.BALANCED,
    ) -> MaintenanceClassification:
        work_type = str(work_type)
        if work_type in CRITICAL_WORK:
            category = MaintenanceWorkCategory.CRITICAL_SYNC
            reason = "critical_result_preservation"
        elif work_type in BOUNDED_WORK:
            category = MaintenanceWorkCategory.BOUNDED_SYNC
            reason = "bounded_post_execution_enrichment"
        elif work_type in CHANGE_TRIGGERED_WORK:
            category = MaintenanceWorkCategory.CHANGE_TRIGGERED
            reason = "requires_relevant_state_change"
        elif work_type in DIAGNOSTIC_WORK:
            category = MaintenanceWorkCategory.DIAGNOSTIC_ONLY
            reason = "diagnostic_contract_required"
        elif work_type in PROHIBITED_WORK:
            category = MaintenanceWorkCategory.PROHIBITED_AFTER_TERMINAL
            reason = "terminal_state_restriction"
        else:
            category = MaintenanceWorkCategory.DEFERRED
            reason = "heavy_or_noncritical_maintenance"
        if category == MaintenanceWorkCategory.DIAGNOSTIC_ONLY and policy == ExecutionPolicyName.DIAGNOSTIC:
            reason = "diagnostic_policy_permits_observability"
        return MaintenanceClassification(work_type, component_name or work_type, category, reason)


__all__ = [
    "MaintenanceClassification",
    "MaintenanceClassifier",
    "MaintenanceTriggerType",
    "MaintenanceWorkCategory",
]
