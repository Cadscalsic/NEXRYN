"""Execution planning bridge for selected cognitive tools.

This module is intentionally lightweight: it does not implement reasoning
engines. It converts selected tools and existing runtime evidence into explicit
execution intents, nodes, requests, and block/defer diagnostics.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping

from runtime.budget.runtime_budget_enforcer import runtime_budget_enforcer


@dataclass
class ExecutionIntent:
    """A planner-level request to activate a selected runtime capability."""

    tool: str
    reason: str
    confidence: float
    priority: int
    estimated_cost: float
    required_budget: dict[str, Any] = field(default_factory=dict)
    required_contexts: list[str] = field(default_factory=list)
    required_truths: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    activation_state: str = "REQUESTED"

    def as_report(self) -> dict[str, Any]:
        """Return a serializable representation of this intent."""

        return asdict(self)


@dataclass
class ExecutionNode:
    """A deterministic runtime stage node generated from an intent."""

    node_id: str
    stage: str
    originating_tool: str
    originating_concept: str | None
    activation_reason: str
    status: str
    parent_node: str | None = None
    child_nodes: list[str] = field(default_factory=list)

    def as_report(self) -> dict[str, Any]:
        """Return a serializable representation of this execution node."""

        return asdict(self)


@dataclass
class ExecutionPlan:
    """Executable cognitive plan produced by :class:`ExecutionPlanner`."""

    execution_nodes: list[ExecutionNode] = field(default_factory=list)
    dependency_nodes: list[ExecutionNode] = field(default_factory=list)
    process_nodes: list[ExecutionNode] = field(default_factory=list)
    causal_nodes: list[ExecutionNode] = field(default_factory=list)
    deferred_nodes: list[ExecutionNode] = field(default_factory=list)
    blocked_nodes: list[ExecutionNode] = field(default_factory=list)
    pruning_log: list[dict[str, Any]] = field(default_factory=list)
    execution_order: list[str] = field(default_factory=list)

    def as_report(self) -> dict[str, Any]:
        """Return a serializable representation of this execution plan."""

        return {
            "execution_nodes": [
                node.as_report() for node in self.execution_nodes
            ],
            "dependency_nodes": [
                node.as_report() for node in self.dependency_nodes
            ],
            "process_nodes": [
                node.as_report() for node in self.process_nodes
            ],
            "causal_nodes": [
                node.as_report() for node in self.causal_nodes
            ],
            "deferred_nodes": [
                node.as_report() for node in self.deferred_nodes
            ],
            "blocked_nodes": [
                node.as_report() for node in self.blocked_nodes
            ],
            "pruning_log": list(self.pruning_log),
            "execution_order": list(self.execution_order),
        }


class ExecutionPlanner:
    """Build explicit runtime execution plans from tool selection outputs."""

    system_name = "execution_planner"

    TOOL_STAGE_MAP = {
        "dependency_reasoning": "dependency_execution",
        "process_semantics": "process_semantic_execution",
        "causal_validation": "causal_validation_execution",
        "truth_governance": "truth_governance_execution",
        "identity_governance": "identity_governance_execution",
        "object_tracking": "object_tracking_execution",
        "color_mapping": "color_mapping_execution",
        "spatial_reasoning": "spatial_reasoning_execution",
        "contradiction_checks": "contradiction_check_execution",
        "telemetry": "telemetry_execution",
        "explanation_generation": "explanation_generation_execution",
        "temporal_reasoning": "temporal_reasoning_execution",
        "strategy_evolution": "strategy_evolution_execution",
        "semantic_to_transformation_compiler": "semantic_compiler_execution",
        "transformation_compilation": "transformation_compilation_execution",
        "transformation_execution": "transformation_execution",
        "rotation_execution": "rotation_execution",
        "reflection_execution": "reflection_execution",
        "scaling_execution": "scaling_execution",
        "path_execution": "path_execution",
    }

    PRIORITY = {
        "dependency_reasoning": 90,
        "process_semantics": 80,
        "causal_validation": 75,
        "truth_governance": 70,
        "identity_governance": 65,
        "object_tracking": 55,
        "spatial_reasoning": 50,
        "color_mapping": 45,
        "contradiction_checks": 40,
        "telemetry": 20,
        "explanation_generation": 15,
        "temporal_reasoning": 10,
        "strategy_evolution": 5,
        "semantic_to_transformation_compiler": 85,
        "transformation_compilation": 84,
        "transformation_execution": 83,
        "rotation_execution": 48,
        "reflection_execution": 48,
        "scaling_execution": 48,
        "path_execution": 48,
    }

    TOOL_COST = {
        "dependency_reasoning": 2,
        "process_semantics": 2,
        "causal_validation": 2,
        "truth_governance": 1,
        "identity_governance": 1,
        "object_tracking": 1,
        "spatial_reasoning": 1,
        "color_mapping": 1,
        "contradiction_checks": 1,
        "telemetry": 1,
        "explanation_generation": 1,
        "temporal_reasoning": 1,
        "strategy_evolution": 1,
        "semantic_to_transformation_compiler": 1,
        "transformation_compilation": 1,
        "transformation_execution": 1,
        "rotation_execution": 1,
        "reflection_execution": 1,
        "scaling_execution": 1,
        "path_execution": 1,
    }

    def plan(
        self,
        *,
        enabled_tools: list[str] | None = None,
        attributed_concepts: list[str] | None = None,
        semantic_contexts: list[Any] | Mapping[str, Any] | None = None,
        truth_candidates: list[Any] | Mapping[str, Any] | None = None,
        active_routes: int | None = None,
        runtime_budget: Any = None,
        task_profile: Any = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build an execution plan report and request maps.

        Args:
            enabled_tools: Tools selected by the tool selection layer.
            attributed_concepts: Concepts attributed by existing semantic systems.
            semantic_contexts: Existing semantic contexts available to nodes.
            truth_candidates: Existing truth candidates or reports.
            active_routes: Route count observed or allowed by routing.
            runtime_budget: Budget object or dictionary.
            task_profile: Current task profile object or dictionary.
            runtime_context: Optional full context used only for diagnostics.

        Returns:
            A dictionary containing the execution plan, generated nodes, runtime
            requests, and `EXECUTION_PLAN_REPORT`.
        """

        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        selected_tools = self._selected_tools(enabled_tools, context)
        concepts = self._concepts(attributed_concepts, context)
        semantic_context_count = self._count(semantic_contexts)
        truth_candidate_count = self._count(truth_candidates)
        route_count = self._route_count(active_routes, selected_tools, context)
        budget = self._budget(runtime_budget, context)
        intents = [
            self._intent(
                tool,
                concepts,
                semantic_context_count,
                truth_candidate_count,
                budget,
                task_profile,
                context,
            )
            for tool in selected_tools
        ]
        plan = self._plan_from_intents(intents, route_count, budget)
        canonical_plan = self._canonical_execution_plan(
            selected_tools=selected_tools,
            concepts=concepts,
            intents=intents,
            legacy_plan=plan,
            active_routes=route_count,
            context=context,
            task_profile=task_profile,
            budget=budget,
        )
        report = self._report(
            selected_tools,
            concepts,
            intents,
            plan,
            route_count,
            canonical_plan,
        )
        return {
            "execution_plan": plan.as_report(),
            "canonical_execution_plan": canonical_plan,
            "execution_nodes": report["generated_execution_nodes"],
            "dependency_requests": self._requests_for(plan.dependency_nodes),
            "process_requests": self._requests_for(plan.process_nodes),
            "causal_requests": self._requests_for(plan.causal_nodes),
            "execution_priority": {
                intent.tool: intent.priority for intent in intents
            },
            "blocked_stages": report["blocked_nodes"],
            "pruning_decisions": report["pruning_log"],
            "EXECUTION_PLAN_REPORT": report,
            "CANONICAL_EXECUTION_PLAN_REPORT": canonical_plan,
            "execution_graph": {
                "node_count": len(plan.execution_nodes),
                "execution_nodes": report["generated_execution_nodes"],
                "graph_mode": "planner_intent_graph",
                "timestamp": str(datetime.utcnow()),
            },
        }

    def build_report(self, plan_result: Mapping[str, Any] | None) -> dict[str, Any]:
        """Return the public execution plan report from a plan result."""

        plan_result = plan_result if isinstance(plan_result, Mapping) else {}
        return dict(plan_result.get("EXECUTION_PLAN_REPORT", {}))

    def build_authoritative_run_plan(
        self,
        *,
        run_id: str,
        task_files: list[str],
        selected_mode: str,
        execution_profile: Mapping[str, Any] | None = None,
        cognitive_pipeline: str | None = None,
        declared_budget: Mapping[str, Any] | None = None,
        source_stage: str = "main_adaptive_pre_execution_planner",
    ) -> dict[str, Any]:
        """Build one finalized run-scoped plan before governed execution starts."""

        created_at = str(datetime.utcnow())
        schema_version = "1.0"
        task_entries = [
            {
                "task_id": str(task_file),
                "task_file": str(task_file),
                "task_entry_state": "SELECTED_FOR_GOVERNED_EXECUTION",
                "governed_execution_admission_state": "PENDING_PLAN_REFERENCE",
            }
            for task_file in task_files
        ]
        budget = dict(declared_budget or {})
        profile = dict(execution_profile or {})
        plan_scope = "RUN_WITH_TASK_ENTRIES"
        execution_plan_id = self._stable_id(
            "execution_plan_authoritative_run",
            {
                "run_id": run_id,
                "plan_scope": plan_scope,
                "task_files": list(task_files),
                "selected_mode": selected_mode,
            },
        )
        lifecycle_seed = {
            "execution_plan_id": execution_plan_id,
            "execution_plan_schema_version": schema_version,
            "run_id": run_id,
            "source_stage": source_stage,
            "source_timestamp": created_at,
            "is_current_run": True,
        }
        lifecycle = [
            self._plan_transition(lifecycle_seed, "PLAN_BUILD_REQUESTED", 1),
            self._plan_transition(lifecycle_seed, "PLAN_BUILD_COMPLETED", 2),
        ]
        finalized_at = str(datetime.utcnow())
        lifecycle_seed["source_timestamp"] = finalized_at
        lifecycle.extend([
            self._plan_transition(lifecycle_seed, "PLAN_FINALIZED", 3),
            self._plan_transition(lifecycle_seed, "PLAN_BOUND_TO_CURRENT_RUN", 4),
        ])
        planned_routes = [
            {
                "route_id": self._stable_id(
                    "planned_task_route",
                    {
                        "execution_plan_id": execution_plan_id,
                        "task_file": task_file,
                    },
                ),
                "task_id": str(task_file),
                "route_state": "PLANNED_SELECTED_TASK_ROUTE",
            }
            for task_file in task_files
        ]
        planned_execution_nodes = [
            {
                "execution_node_id": self._stable_id(
                    "planned_execution_node",
                    {
                        "execution_plan_id": execution_plan_id,
                        "task_file": task_file,
                    },
                ),
                "execution_plan_id": execution_plan_id,
                "task_id": str(task_file),
                "node_type": "governed_task_execution",
                "admission_requirement": "EXECUTION_ADMITTED_WITH_PLAN_REFERENCE",
                "invocation_state": "NOT_INVOKED",
            }
            for task_file in task_files
        ]
        plan = {
            "execution_plan_schema_version": schema_version,
            "execution_plan_id": execution_plan_id,
            "run_id": str(run_id),
            "task_id": "RUN_WITH_TASK_ENTRIES",
            "plan_scope": plan_scope,
            "budget_scope": plan_scope,
            "planning_state": "AUTHORITATIVE_PRE_EXECUTION_PLAN_FINALIZED",
            "execution_plan_state": "AUTHORITATIVE_PRE_EXECUTION_PLAN_FINALIZED",
            "plan_origin": source_stage,
            "planning_authority": "AUTHORITATIVE",
            "temporal_authority_state": "PRE_EXECUTION_AUTHORITY_CONFIRMED",
            "plan_created_at": created_at,
            "plan_finalized_at": finalized_at,
            "execution_admission_started_at": None,
            "selected_mode": str(selected_mode or ""),
            "execution_profile": profile,
            "cognitive_pipeline": cognitive_pipeline or profile.get("cognitive_pipeline") or profile.get("pipeline_name"),
            "declared_budget": budget,
            "selected_tools": [],
            "selected_layers": [],
            "planned_routes": planned_routes,
            "planned_execution_nodes": planned_execution_nodes,
            "planned_reasoning_depth": budget.get("max_reasoning_depth"),
            "task_entries": task_entries,
            "lifecycle_transitions": lifecycle,
            "execution_plan_finalized": True,
            "finalized": True,
            "execution_plan_immutable": True,
            "immutable": True,
            "execution_plan_forwarded": True,
            "selected_tool_count": 0,
            "selected_tools_count": 0,
            "selected_layer_count": 0,
            "selected_layers_count": 0,
            "active_route_count": len(planned_routes),
            "selected_route_count": len(planned_routes),
            "selected_routes_count": len(planned_routes),
            "execution_node_count": len(planned_execution_nodes),
            "execution_nodes_materialized": len(planned_execution_nodes),
            "reconciled_tool_count": 0,
            "reconciled_tools_count": 0,
            "reconciled_layer_count": 0,
            "reconciled_layers_count": 0,
            "reconciled_route_count": 0,
            "reconciled_routes_count": 0,
            "maximum_active_routes": budget.get("max_active_routes"),
            "maximum_reasoning_depth": budget.get("max_reasoning_depth"),
            "maximum_dependency_depth": budget.get("max_dependency_depth"),
            "maximum_hypotheses": budget.get("max_hypotheses"),
            "execution_plan_reconciliation_state": "PENDING_RUNTIME_OBSERVATION",
            "runtime_reconciliation_state": "PENDING_RUNTIME_OBSERVATION",
            "execution_plan_validation_state": "VALID",
            "execution_plan_failure_cause": None,
            "dependency_activation_state": "NOT_REQUESTED",
            "process_stage_state": "NOT_REQUESTED",
            "retrospective_reconstruction_authority": "DIAGNOSTIC_ONLY_WHEN_PRESENT",
            "constitutional_boundary": "TEMPORAL_PLANNING_AUTHORITY_ONLY_NO_RUNTIME_BUDGET_ENFORCEMENT",
        }
        fingerprint = self._fingerprint_authoritative_run_plan(plan)
        plan["immutable_fingerprint"] = fingerprint
        plan["execution_plan_fingerprint"] = fingerprint
        return plan

    def admit_authoritative_run_plan(
        self,
        canonical_plan: Mapping[str, Any] | None,
        *,
        task_id: str,
        source_stage: str = "main_adaptive_governed_task_admission",
    ) -> dict[str, Any]:
        """Record the real governed admission boundary without invoking work."""

        plan = dict(canonical_plan or {})
        timestamp = str(datetime.utcnow())
        transitions = [
            dict(row)
            for row in plan.get("lifecycle_transitions", []) or []
            if isinstance(row, Mapping)
        ]
        if not any(
            row.get("transition_name") == "EXECUTION_ADMITTED_WITH_PLAN_REFERENCE"
            for row in transitions
        ):
            transitions.append(
                self._plan_transition(
                    {
                        "execution_plan_id": plan.get("execution_plan_id"),
                        "execution_plan_schema_version": plan.get(
                            "execution_plan_schema_version",
                            "1.0",
                        ),
                        "run_id": plan.get("run_id"),
                        "source_stage": source_stage,
                        "source_timestamp": timestamp,
                        "is_current_run": True,
                    },
                    "EXECUTION_ADMITTED_WITH_PLAN_REFERENCE",
                    len(transitions) + 1,
                )
            )
        task_entries = []
        for entry in plan.get("task_entries", []) or []:
            if not isinstance(entry, Mapping):
                continue
            updated = dict(entry)
            if updated.get("task_id") == task_id or updated.get("task_file") == task_id:
                updated["governed_execution_admission_state"] = (
                    "EXECUTION_ADMITTED_WITH_PLAN_REFERENCE"
                )
                updated["execution_admission_started_at"] = timestamp
            task_entries.append(updated)
        plan["task_entries"] = task_entries
        plan["lifecycle_transitions"] = transitions
        plan["execution_admission_started_at"] = (
            plan.get("execution_admission_started_at") or timestamp
        )
        plan["runtime_reconciliation_state"] = "RUNTIME_OBSERVATION_PENDING"
        plan["execution_plan_reconciliation_state"] = "RUNTIME_OBSERVATION_PENDING"
        return plan

    def consume_finalized_plan(
        self,
        canonical_plan: Mapping[str, Any] | None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Materialize a governed runtime handoff from a finalized plan.

        This does not invoke any runtime component. It only translates already
        finalized plan nodes into stage/admission/activation handoff records.
        """

        plan = canonical_plan if isinstance(canonical_plan, Mapping) else {}
        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        context_run_id = (
            context.get("run_id")
            or context.get("execution_id")
            or context.get("runtime_id")
        )
        if (
            context_run_id is not None
            and self._identity_value(context_run_id)
            != self._identity_value(plan.get("run_id"))
        ):
            return {
                "orchestrator_consumption_state": "BLOCKED_BY_PLAN_IDENTITY",
                "runtime_stage_count": 0,
                "admission_record_count": 0,
                "activation_request_count": 0,
                "invocation_record_count": 0,
                "failure_reason": "CROSS_RUN_PLAN_CONTAMINATION",
            }
        if plan.get("execution_plan_immutable") and not self._plan_fingerprint_valid(plan):
            return {
                "orchestrator_consumption_state": "BLOCKED_BY_STALE_PLAN",
                "runtime_stage_count": 0,
                "admission_record_count": 0,
                "activation_request_count": 0,
                "invocation_record_count": 0,
                "failure_reason": "PLAN_STALE",
            }
        if context and self._plan_selection_stale(plan, context):
            return {
                "orchestrator_consumption_state": "BLOCKED_BY_STALE_PLAN",
                "runtime_stage_count": 0,
                "admission_record_count": 0,
                "activation_request_count": 0,
                "invocation_record_count": 0,
                "failure_reason": "PLAN_STALE",
            }
        if plan.get("execution_plan_validation_state") != "VALID":
            return {
                "orchestrator_consumption_state": "BLOCKED_BY_PLAN_VALIDATION",
                "runtime_stage_count": 0,
                "admission_record_count": 0,
                "activation_request_count": 0,
                "invocation_record_count": 0,
                "failure_reason": plan.get("execution_plan_failure_cause") or "PLAN_NOT_VALID",
            }
        stages = []
        admissions = []
        activations = []
        for node in plan.get("nodes", []) or []:
            if not isinstance(node, Mapping):
                continue
            if node.get("execution_plan_id") != plan.get("execution_plan_id"):
                return {
                    "orchestrator_consumption_state": "BLOCKED_BY_PLAN_IDENTITY",
                    "runtime_stage_count": 0,
                    "admission_record_count": 0,
                    "activation_request_count": 0,
                    "invocation_record_count": 0,
                    "failure_reason": "PLAN_IDENTITY_CONFLICT",
                }
            if node.get("materialization_state") != "MATERIALIZED":
                continue
            if node.get("admission_state") != "ADMISSION_REQUESTED":
                return {
                    "orchestrator_consumption_state": "BLOCKED_BY_ADMISSION",
                    "runtime_stage_count": 0,
                    "admission_record_count": 0,
                    "activation_request_count": 0,
                    "invocation_record_count": 0,
                    "failure_reason": "EXECUTION_WITHOUT_ADMISSION_RECORD",
                }
            stage_id = node.get("runtime_stage_id") or self._stable_id(
                "runtime_stage",
                node.get("execution_node_id"),
            )
            stages.append({
                "runtime_stage_id": stage_id,
                "execution_plan_id": node.get("execution_plan_id"),
                "execution_node_id": node.get("execution_node_id"),
                "target_runtime_component": node.get("target_runtime_component"),
                "stage_state": "MATERIALIZED",
                "invocation_state": "NOT_INVOKED",
            })
            admissions.append({
                "admission_record_id": self._stable_id(
                    "admission_record",
                    {
                        "plan": node.get("execution_plan_id"),
                        "node": node.get("execution_node_id"),
                    },
                ),
                "execution_plan_id": node.get("execution_plan_id"),
                "execution_node_id": node.get("execution_node_id"),
                "admission_state": node.get("admission_state"),
                "admission_requirement": node.get("admission_requirement"),
            })
            if node.get("activation_request_id"):
                activations.append({
                    "activation_request_id": node.get("activation_request_id"),
                    "execution_plan_id": node.get("execution_plan_id"),
                    "execution_node_id": node.get("execution_node_id"),
                    "activation_state": node.get("activation_state"),
                    "target_runtime_component": node.get("target_runtime_component"),
                })
        return {
            "orchestrator_consumption_state": "CANONICAL_PLAN_CONSUMED",
            "execution_plan_id": plan.get("execution_plan_id"),
            "runtime_stage_count": len(stages),
            "admission_record_count": len(admissions),
            "activation_request_count": len(activations),
            "invocation_record_count": 0,
            "runtime_stages": stages,
            "admission_records": admissions,
            "activation_requests": activations,
            "invocation_records": [],
            "execution_invoked": False,
        }

    def _intent(
        self,
        tool: str,
        concepts: list[str],
        semantic_context_count: int,
        truth_candidate_count: int,
        budget: Mapping[str, Any],
        task_profile: Any,
        context: Mapping[str, Any],
    ) -> ExecutionIntent:
        reason = self._reason(tool, task_profile, context)
        required_contexts = []
        required_truths = []
        dependencies = []
        if tool == "dependency_reasoning":
            required_contexts.append("attributed_concepts")
        if tool == "process_semantics":
            required_contexts.extend([
                "attributed_concepts",
                "semantic_context",
            ])
            dependencies.append("dependency_reasoning")
        if tool == "causal_validation":
            required_contexts.append("process_context")
            dependencies.append("process_semantics")
        if tool == "truth_governance":
            required_truths.append("truth_candidates")
        confidence = 0.75
        if concepts:
            confidence += 0.10
        if semantic_context_count:
            confidence += 0.05
        if truth_candidate_count:
            confidence += 0.05
        return ExecutionIntent(
            tool=tool,
            reason=reason,
            confidence=round(min(confidence, 0.99), 4),
            priority=self.PRIORITY.get(tool, 1),
            estimated_cost=float(self.TOOL_COST.get(tool, 1)),
            required_budget=self._required_budget(tool, budget),
            required_contexts=required_contexts,
            required_truths=required_truths,
            dependencies=dependencies,
            activation_state="REQUESTED",
        )

    def _plan_from_intents(
        self,
        intents: list[ExecutionIntent],
        active_routes: int,
        budget: Mapping[str, Any],
    ) -> ExecutionPlan:
        ordered = sorted(
            intents,
            key=lambda intent: (-intent.priority, intent.tool),
        )
        max_routes = self._int_value(
            budget.get("max_active_routes"),
            active_routes or len(ordered),
        )
        if max_routes <= 0:
            max_routes = len(ordered)
        plan = ExecutionPlan()
        consumed = 0.0
        previous_node_id = None
        for index, intent in enumerate(ordered):
            node = self._node(intent, index, previous_node_id)
            block_reason = self._block_reason(intent, budget, consumed)
            if block_reason:
                node.status = "BLOCKED"
                plan.blocked_nodes.append(node)
                plan.pruning_log.append({
                    "tool": intent.tool,
                    "node_id": node.node_id,
                    "decision": "BLOCKED",
                    "reason": block_reason,
                })
            elif len(plan.execution_nodes) >= max_routes:
                node.status = "DEFERRED"
                plan.deferred_nodes.append(node)
                plan.pruning_log.append({
                    "tool": intent.tool,
                    "node_id": node.node_id,
                    "decision": "DEFERRED",
                    "reason": "max_active_routes_reached",
                })
            else:
                plan.execution_nodes.append(node)
                plan.execution_order.append(node.node_id)
                consumed += intent.estimated_cost
                previous_node_id = node.node_id
            if intent.tool == "dependency_reasoning":
                plan.dependency_nodes.append(node)
            elif intent.tool == "process_semantics":
                plan.process_nodes.append(node)
            elif intent.tool == "causal_validation":
                plan.causal_nodes.append(node)
        self._link_children(plan.execution_nodes)
        return plan

    def _node(
        self,
        intent: ExecutionIntent,
        index: int,
        previous_node_id: str | None,
    ) -> ExecutionNode:
        concept = None
        if intent.required_contexts:
            concept = intent.required_contexts[0]
        return ExecutionNode(
            node_id=f"exec_{index + 1}_{intent.tool}",
            stage=self.TOOL_STAGE_MAP.get(intent.tool, f"{intent.tool}_execution"),
            originating_tool=intent.tool,
            originating_concept=concept,
            activation_reason=intent.reason,
            status="PENDING",
            parent_node=previous_node_id,
        )

    def _canonical_execution_plan(
        self,
        *,
        selected_tools: list[str],
        concepts: list[str],
        intents: list[ExecutionIntent],
        legacy_plan: ExecutionPlan,
        active_routes: int,
        context: Mapping[str, Any],
        task_profile: Any,
        budget: Mapping[str, Any],
    ) -> dict[str, Any]:
        run_id = self._identity_value(
            context.get("run_id")
            or context.get("execution_id")
            or context.get("runtime_id")
            or "current_run"
        )
        task_id = self._identity_value(
            context.get("task_id")
            or context.get("task")
            or getattr(task_profile, "task_id", None)
            or "current_task"
        )
        task_profile_id = self._stable_id(
            "task_profile",
            {
                "run_id": run_id,
                "task_id": task_id,
                "concepts": concepts,
            },
        )
        execution_plan_id = self._stable_id(
            "execution_plan",
            {
                "run_id": run_id,
                "task_id": task_id,
                "selected_tools": selected_tools,
                "active_routes": active_routes,
            },
        )
        selection_records = self._tool_selection_records(selected_tools, context)
        layer_records = self._layer_selection_records(context, selected_tools)
        route_records = self._route_selection_records(active_routes, context)
        legacy_nodes_by_tool = {
            node.originating_tool: node
            for node in (
                legacy_plan.execution_nodes
                + legacy_plan.blocked_nodes
                + legacy_plan.deferred_nodes
            )
        }
        nodes: list[dict[str, Any]] = []
        tool_reconciliation: list[dict[str, Any]] = []
        dependency_activation_requests: list[dict[str, Any]] = []
        process_stage_requests: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []

        for index, record in enumerate(selection_records):
            tool = record["tool"]
            intent = next((item for item in intents if item.tool == tool), None)
            legacy_node = legacy_nodes_by_tool.get(tool)
            node_id = self._stable_id(
                "execution_node",
                {
                    "execution_plan_id": execution_plan_id,
                    "tool": tool,
                    "selection_id": record["tool_selection_record_id"],
                },
            )
            target_component = self.TOOL_STAGE_MAP.get(tool)
            block_reason = None
            defer_reason = None
            disposition = "MATERIALIZED_AS_EXECUTION_NODE"
            materialization_state = "MATERIALIZED"
            admission_state = "ADMISSION_REQUESTED"
            activation_state = "REQUESTED"
            if legacy_node and legacy_node.status == "BLOCKED":
                disposition = "BLOCKED_BY_ADMISSION"
                materialization_state = "BLOCKED"
                admission_state = "BLOCKED"
                activation_state = "NOT_REQUESTED"
                block_reason = self._pruning_reason(legacy_plan, tool, "BLOCKED")
            elif legacy_node and legacy_node.status == "DEFERRED":
                disposition = "DEFERRED_BY_DEPENDENCY"
                materialization_state = "DEFERRED"
                admission_state = "NOT_REQUESTED"
                activation_state = "DEFERRED"
                defer_reason = self._pruning_reason(legacy_plan, tool, "DEFERRED")
            elif not target_component:
                disposition = "FAILED_TO_MATERIALIZE"
                materialization_state = "FAILED"
                admission_state = "NOT_REQUESTED"
                activation_state = "NOT_REQUESTED"
                block_reason = "TARGET_COMPONENT_UNRESOLVED"
            runtime_stage_id = self._stable_id(
                "runtime_stage",
                {
                    "execution_plan_id": execution_plan_id,
                    "node_id": node_id,
                    "component": target_component,
                },
            )
            activation_request_id = (
                self._stable_id(
                    "activation_request",
                    {
                        "execution_plan_id": execution_plan_id,
                        "node_id": node_id,
                        "tool": tool,
                    },
                )
                if activation_state == "REQUESTED"
                else None
            )
            node = {
                "execution_node_id": node_id,
                "execution_plan_id": execution_plan_id,
                "node_type": "runtime_tool_stage",
                "target_runtime_component": target_component,
                "originating_tool": tool,
                "runtime_stage_id": runtime_stage_id if target_component else None,
                "source_tool_selection_ids": [record["tool_selection_record_id"]],
                "source_layer_selection_ids": [],
                "source_route_ids": [],
                "selection_state": "SELECTED" if record["selected_state"] else "NOT_SELECTED",
                "materialization_state": materialization_state,
                "admission_requirement": "GOVERNED_RUNTIME_STAGE_ADMISSION",
                "admission_state": admission_state,
                "activation_request_id": activation_request_id,
                "activation_state": activation_state,
                "invocation_id": None,
                "invocation_state": "NOT_INVOKED",
                "dependency_node_ids": list(intent.dependencies if intent else []),
                "execution_order": index,
                "block_reason": block_reason,
                "prune_reason": None,
                "defer_reason": defer_reason,
                "failure_reason": block_reason if disposition == "FAILED_TO_MATERIALIZE" else None,
            }
            nodes.append(node)
            record.update({
                "planning_applicability": True,
                "target_execution_node_ids": [node_id],
                "final_disposition": disposition,
                "disposition_reason": block_reason or defer_reason or "selection_materialized_by_canonical_execution_plan",
                "admission_requirement": node["admission_requirement"],
                "activation_request_state": activation_state,
                "invocation_state": node["invocation_state"],
            })
            tool_reconciliation.append(record)
            if disposition == "FAILED_TO_MATERIALIZE":
                failures.append({
                    "selected_item_type": "tool",
                    "selected_item": tool,
                    "failure_reason": block_reason or "UNKNOWN_MATERIALIZATION_FAILURE",
                })
            if tool == "dependency_reasoning" and activation_request_id:
                dependency_activation_requests.append({
                    "activation_request_id": activation_request_id,
                    "execution_plan_id": execution_plan_id,
                    "execution_node_id": node_id,
                    "target_dependency_component": target_component,
                    "source_selection_id": record["tool_selection_record_id"],
                    "source_route_ids": [],
                    "required_input_references": ["attributed_concepts"],
                    "admission_requirement": node["admission_requirement"],
                    "request_state": "REQUESTED",
                    "activation_state": activation_state,
                    "failure_reason": None,
                })
            if tool == "process_semantics":
                process_stage_requests.append({
                    "process_stage_request_id": activation_request_id or self._stable_id("process_stage_request", node_id),
                    "execution_plan_id": execution_plan_id,
                    "execution_node_id": node_id,
                    "source_tool_selection_ids": [record["tool_selection_record_id"]],
                    "source_layer_selection_ids": [],
                    "source_route_ids": [],
                    "required_upstream_outputs": ["attributed_concepts", "semantic_context"],
                    "stage_order": index,
                    "admission_state": admission_state,
                    "activation_request_id": activation_request_id,
                    "request_state": "REQUESTED" if activation_request_id else materialization_state,
                    "non_materialization_reason": block_reason or defer_reason,
                })

        materialized_node_ids = [
            node["execution_node_id"]
            for node in nodes
            if node["materialization_state"] == "MATERIALIZED"
        ]
        route_reconciliation = self._reconcile_routes(
            route_records,
            materialized_node_ids,
            execution_plan_id,
        )
        node_by_id = {node["execution_node_id"]: node for node in nodes}
        for row in route_reconciliation:
            target = row.get("execution_node_id")
            if target in node_by_id and row["route_id"] not in node_by_id[target]["source_route_ids"]:
                node_by_id[target]["source_route_ids"].append(row["route_id"])
        for request in dependency_activation_requests:
            node = node_by_id.get(request.get("execution_node_id"))
            if node:
                request["source_route_ids"] = list(node.get("source_route_ids", []))
        for request in process_stage_requests:
            node = node_by_id.get(request.get("execution_node_id"))
            if node:
                request["source_route_ids"] = list(node.get("source_route_ids", []))
        layer_reconciliation = self._reconcile_layers(
            layer_records,
            nodes,
            execution_plan_id,
        )
        for row in layer_reconciliation:
            for node_id in row.get("target_execution_node_ids", []):
                if node_id in node_by_id:
                    node_by_id[node_id]["source_layer_selection_ids"].append(
                        row["layer_selection_record_id"]
                    )

        reconciled_tools = len(tool_reconciliation)
        reconciled_layers = len(layer_reconciliation)
        reconciled_routes = len(route_reconciliation)
        unresolved = sum(
            1
            for row in [*tool_reconciliation, *layer_reconciliation, *route_reconciliation]
            if row.get("final_disposition") == "FAILED_TO_MATERIALIZE"
        )
        route_balance = self._route_balance(route_reconciliation, len(route_records))
        budget_receipt = runtime_budget_enforcer.build_receipt(
            budget=budget,
            context=context,
            execution_plan_id=execution_plan_id,
            route_records=route_records,
            nodes=nodes,
        )
        validation_state = "VALID"
        failure_cause = None
        if budget_receipt.get("runtime_budget_state") in {
            "RUNTIME_BUDGET_AUTHORITY_CONFLICT",
            "BUDGET_SNAPSHOT_STALE",
            "ROUTE_BUDGET_CROSS_RUN_CONTAMINATION",
            "ROUTE_BUDGET_CROSS_TASK_CONTAMINATION",
            "ROUTE_LIFECYCLE_IDENTITY_CONFLICT",
            "REASONING_DEPTH_IDENTITY_CONFLICT",
            "RUNTIME_BUDGET_INTEGRITY_FAILED",
        }:
            validation_state = "CONFLICTED"
            failure_cause = budget_receipt.get("runtime_budget_state")
        if unresolved:
            validation_state = "INCOMPLETE"
            failure_cause = "SELECTED_ITEM_FAILED_TO_MATERIALIZE"
        if not route_balance["balanced"]:
            validation_state = "INVALID"
            failure_cause = "ROUTE_RECONCILIATION_FAILED"
        if any(node["execution_plan_id"] != execution_plan_id for node in nodes):
            validation_state = "CONFLICTED"
            failure_cause = "PLAN_IDENTITY_CONFLICT"
        planning_state = (
            "EXECUTION_PLAN_FINALIZED"
            if validation_state == "VALID"
            else "EXECUTION_PLAN_NOT_FINALIZED"
        )
        dependency_activation_state = self._capability_handoff_state(
            "dependency_reasoning",
            nodes,
            dependency_activation_requests,
        )
        process_stage_state = self._capability_handoff_state(
            "process_semantics",
            nodes,
            process_stage_requests,
            materialized_label="MATERIALIZED",
        )
        plan = {
            "execution_plan_schema_version": "1.0",
            "execution_plan_id": execution_plan_id,
            "run_id": run_id,
            "task_id": task_id,
            "task_profile_id": task_profile_id,
            "planning_state": planning_state,
            "execution_plan_state": planning_state,
            "source_selection_record_ids": [
                row["tool_selection_record_id"] for row in selection_records
            ],
            "selected_tool_count": len(selection_records),
            "selected_tools_count": len(selection_records),
            "selected_layer_count": len(layer_records),
            "selected_layers_count": len(layer_records),
            "active_route_count": len(route_records),
            "selected_route_count": len(route_records),
            "selected_routes_count": len(route_records),
            "execution_node_count": len(nodes),
            "execution_nodes_materialized": len(nodes),
            "route_disposition_count": len(route_reconciliation),
            "unresolved_selected_item_count": unresolved,
            "nodes": nodes,
            "route_reconciliation": route_reconciliation,
            "route_balance": route_balance,
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT": budget_receipt,
            "runtime_budget_enforcement_report": budget_receipt,
            "tool_reconciliation": tool_reconciliation,
            "layer_reconciliation": layer_reconciliation,
            "dependency_activation_requests": dependency_activation_requests,
            "process_stage_requests": process_stage_requests,
            "admission_summary": {
                "admission_requested_count": sum(1 for node in nodes if node["admission_state"] == "ADMISSION_REQUESTED"),
                "blocked_count": sum(1 for node in nodes if node["admission_state"] == "BLOCKED"),
                "invocation_without_admission_count": 0,
            },
            "materialization_failures": failures,
            "immutability_state": "IMMUTABLE" if validation_state == "VALID" else "NOT_FINALIZED",
            "execution_plan_finalized": validation_state == "VALID",
            "finalized": validation_state == "VALID",
            "execution_plan_immutable": validation_state == "VALID",
            "immutable": validation_state == "VALID",
            "execution_plan_forwarded": validation_state == "VALID",
            "execution_plan_reconciliation_state": "COMPLETE" if validation_state == "VALID" else "FAILED",
            "execution_plan_validation_state": validation_state,
            "execution_plan_failure_cause": failure_cause,
            "dependency_activation_state": dependency_activation_state,
            "process_stage_state": process_stage_state,
            "orchestrator_consumption_state": "READY_FOR_ORCHESTRATOR" if validation_state == "VALID" else "BLOCKED_BY_PLAN_VALIDATION",
            "constitutional_boundary": "CANONICAL_EXECUTION_PLAN_MATERIALIZES_EXISTING_SELECTIONS_WITHOUT_GRANTING_NEW_COGNITIVE_AUTHORITY",
        }
        plan["reconciled_tool_count"] = len(tool_reconciliation)
        plan["reconciled_tools_count"] = len(tool_reconciliation)
        plan["reconciled_layer_count"] = len(layer_reconciliation)
        plan["reconciled_layers_count"] = len(layer_reconciliation)
        plan["reconciled_route_count"] = len(route_reconciliation)
        plan["reconciled_routes_count"] = len(route_reconciliation)
        plan["maximum_active_routes"] = budget_receipt.get("maximum_active_routes")
        plan["maximum_reasoning_depth"] = budget_receipt.get("maximum_reasoning_depth")
        plan["maximum_dependency_depth"] = budget.get("max_dependency_depth")
        plan["maximum_hypotheses"] = budget.get("max_hypotheses")
        plan["execution_plan_fingerprint"] = self._fingerprint_plan(plan)
        return plan

    def _tool_selection_records(
        self,
        selected_tools: list[str],
        context: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        enabled = set(context.get("enabled_tools", []) or [])
        available = set(context.get("available_tools", []) or [])
        report = context.get("tool_selection_report", {})
        if isinstance(report, Mapping):
            available.update(report.get("available_tools", []) or [])
            enabled.update(report.get("enabled_tools", []) or [])
        records = []
        for tool in sorted(dict.fromkeys(selected_tools)):
            records.append({
                "canonical_tool_id": tool,
                "tool": tool,
                "tool_selection_record_id": self._stable_id("tool_selection", tool),
                "available_state": tool in available or tool in enabled or tool in selected_tools,
                "enabled_state": tool in enabled,
                "selected_state": True,
                "planned_state": False,
                "invoked_state": False,
                "execution_count": 0,
            })
        return records

    def _layer_selection_records(
        self,
        context: Mapping[str, Any],
        selected_tools: list[str],
    ) -> list[dict[str, Any]]:
        layers = []
        explicit_selected = "selected_layers" in context
        if explicit_selected:
            values = [context.get("selected_layers")]
        else:
            values = [
                context.get("selected_layers"),
                context.get("enabled_layers"),
                context.get("active_layers"),
            ]
        for value in values:
            if isinstance(value, (list, tuple, set)):
                layers.extend(str(item) for item in value if item)
        tool_layer_map = {
            "dependency_reasoning": "dependency_reasoning_layer",
            "process_semantics": "process_semantics_layer",
        }
        for tool in selected_tools:
            if tool in tool_layer_map:
                layers.append(tool_layer_map[tool])
        records = []
        enabled_layers = set(context.get("enabled_layers", []) or [])
        for layer in sorted(dict.fromkeys(layers)):
            records.append({
                "canonical_layer_id": layer,
                "layer_selection_record_id": self._stable_id("layer_selection", layer),
                "layer": layer,
                "enabled_state": layer in enabled_layers or not explicit_selected,
                "selected_state": True,
            })
        return records

    def _route_selection_records(
        self,
        active_routes: int,
        context: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        route_report = context.get("route_selection_report") or context.get("cognitive_route_report") or {}
        raw_routes = []
        if isinstance(route_report, Mapping):
            for key in ("active_routes", "routes", "selected_routes"):
                value = route_report.get(key)
                if isinstance(value, list):
                    raw_routes = value
                    break
        records = []
        if raw_routes:
            for index, route in enumerate(raw_routes):
                route = route if isinstance(route, Mapping) else {"route": route}
                route_id = self._identity_value(route.get("route_id") or route.get("id") or f"route_{index + 1}")
                records.append({
                    "route_id": route_id,
                    "route_source": route.get("source", "route_selection"),
                    "route_rank": self._int_value(route.get("rank"), index + 1),
                    "route_score": route.get("score"),
                    "route_active_state": True,
                })
        else:
            for index in range(max(0, active_routes)):
                route_id = self._stable_id("route", {"index": index + 1, "active_routes": active_routes})
                records.append({
                    "route_id": route_id,
                    "route_source": "active_route_count",
                    "route_rank": index + 1,
                    "route_score": None,
                    "route_active_state": True,
                })
        return records

    def _reconcile_routes(
        self,
        routes: list[dict[str, Any]],
        materialized_node_ids: list[str],
        execution_plan_id: str,
    ) -> list[dict[str, Any]]:
        reconciled = []
        for index, route in enumerate(routes):
            if not materialized_node_ids:
                disposition = "FAILED_TO_MATERIALIZE"
                target_node = None
                reason = "no_materialized_execution_nodes_for_active_route"
            elif index < len(materialized_node_ids):
                disposition = "MATERIALIZED_AS_EXECUTION_NODE"
                target_node = materialized_node_ids[index]
                reason = "route_materialized_to_corresponding_execution_node"
            else:
                disposition = "MERGED_INTO_EXECUTION_NODE"
                target_node = materialized_node_ids[0]
                reason = "deterministic_route_merge_into_primary_execution_node"
            reconciled.append({
                **route,
                "execution_plan_id": execution_plan_id,
                "execution_applicability": True,
                "execution_node_id": target_node,
                "merged_node_id": target_node if disposition == "MERGED_INTO_EXECUTION_NODE" else None,
                "final_disposition": disposition,
                "disposition_reason": reason,
                "merge_lineage": [route["route_id"]] if disposition == "MERGED_INTO_EXECUTION_NODE" else [],
                "pruning_authority": None,
                "admission_state": "ADMISSION_REQUESTED" if target_node else "NOT_REQUESTED",
                "activation_state": "REQUESTED" if target_node else "NOT_REQUESTED",
            })
        return reconciled

    def _reconcile_layers(
        self,
        layers: list[dict[str, Any]],
        nodes: list[dict[str, Any]],
        execution_plan_id: str,
    ) -> list[dict[str, Any]]:
        materialized = [
            node["execution_node_id"]
            for node in nodes
            if node["materialization_state"] == "MATERIALIZED"
        ]
        rows = []
        for layer in layers:
            targets = [
                node["execution_node_id"]
                for node in nodes
                if (
                    layer["layer"].replace("_layer", "") in str(node["target_runtime_component"])
                    or layer["layer"].replace("_layer", "") == node.get("originating_tool")
                )
            ]
            blocked_targets = [
                node["execution_node_id"]
                for node in nodes
                if (
                    layer["layer"].replace("_layer", "") == node.get("originating_tool")
                    and node.get("materialization_state") == "BLOCKED"
                )
            ]
            if blocked_targets:
                targets = blocked_targets
                disposition = "BLOCKED_BY_ADMISSION"
                reason = "layer_blocked_by_matching_tool_admission"
            elif not targets and materialized:
                targets = [materialized[0]]
                disposition = "MERGED_INTO_EXECUTION_NODE"
                reason = "layer_merged_into_primary_runtime_stage"
            elif targets:
                disposition = "MATERIALIZED_AS_EXECUTION_NODE"
                reason = "layer_materialized_by_matching_runtime_stage"
            else:
                disposition = "FAILED_TO_MATERIALIZE"
                reason = "no_runtime_stage_available_for_selected_layer"
            rows.append({
                **layer,
                "execution_plan_id": execution_plan_id,
                "target_execution_node_ids": targets,
                "final_disposition": disposition,
                "disposition_reason": reason,
                "admission_state": "ADMISSION_REQUESTED" if targets else "NOT_REQUESTED",
                "activation_state": "REQUESTED" if targets else "NOT_REQUESTED",
            })
        return rows

    def _route_balance(
        self,
        rows: list[dict[str, Any]],
        active_route_count: int,
    ) -> dict[str, Any]:
        states = {
            "MATERIALIZED_AS_EXECUTION_NODE": 0,
            "MERGED_INTO_EXECUTION_NODE": 0,
            "PRUNED_BY_POLICY": 0,
            "BLOCKED_BY_ADMISSION": 0,
            "DEFERRED_BY_DEPENDENCY": 0,
            "NOT_APPLICABLE_TO_FINAL_PLAN": 0,
            "FAILED_TO_MATERIALIZE": 0,
        }
        for row in rows:
            states[row["final_disposition"]] = states.get(row["final_disposition"], 0) + 1
        total = sum(states.values())
        return {
            **states,
            "active_route_count": active_route_count,
            "reconciled_route_count": total,
            "balanced": total == active_route_count,
        }

    def _pruning_reason(
        self,
        plan: ExecutionPlan,
        tool: str,
        decision: str,
    ) -> str | None:
        for row in plan.pruning_log:
            if row.get("tool") == tool and row.get("decision") == decision:
                return row.get("reason")
        return None

    def _capability_handoff_state(
        self,
        tool: str,
        nodes: list[dict[str, Any]],
        requests: list[dict[str, Any]],
        *,
        materialized_label: str = "REQUESTED",
    ) -> str:
        matching = [node for node in nodes if node.get("originating_tool") == tool]
        if any(node.get("materialization_state") == "BLOCKED" for node in matching):
            return "BLOCKED"
        if any(node.get("materialization_state") == "DEFERRED" for node in matching):
            return "DEFERRED"
        if any(node.get("materialization_state") == "FAILED" for node in matching):
            return "FAILED_TO_MATERIALIZE"
        if requests:
            return materialized_label
        return "NOT_REQUESTED"

    def _fingerprint_plan(self, plan: Mapping[str, Any]) -> str:
        payload = dict(plan)
        payload.pop("execution_plan_fingerprint", None)
        return self._stable_id("execution_plan_fingerprint", payload)

    def _plan_fingerprint_valid(self, plan: Mapping[str, Any]) -> bool:
        fingerprint = plan.get("execution_plan_fingerprint")
        if not fingerprint:
            return False
        return fingerprint == self._fingerprint_plan(plan)

    def _plan_selection_stale(
        self,
        plan: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> bool:
        report = context.get("tool_selection_report", {})
        if not isinstance(report, Mapping) or "selected_tools" not in report:
            return False
        current = sorted(str(tool) for tool in report.get("selected_tools", []) or [])
        planned = sorted(
            str(row.get("tool"))
            for row in plan.get("tool_reconciliation", []) or []
            if isinstance(row, Mapping) and row.get("selected_state") is True
        )
        return current != planned

    def _stable_id(self, prefix: str, payload: Any) -> str:
        text = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"

    def _plan_transition(
        self,
        plan: Mapping[str, Any],
        transition_name: str,
        sequence_index: int,
    ) -> dict[str, Any]:
        return {
            "transition_name": transition_name,
            "state": transition_name,
            "execution_plan_id": plan.get("execution_plan_id"),
            "execution_plan_schema_version": plan.get(
                "execution_plan_schema_version",
                "1.0",
            ),
            "run_id": plan.get("run_id"),
            "budget_scope": plan.get("budget_scope") or plan.get("plan_scope"),
            "source_stage": plan.get("source_stage", "execution_planner"),
            "source_timestamp": plan.get("source_timestamp", str(datetime.utcnow())),
            "sequence_index": sequence_index,
            "is_current_run": bool(plan.get("is_current_run", True)),
        }

    def _fingerprint_authoritative_run_plan(self, plan: Mapping[str, Any]) -> str:
        planned_only = {
            key: plan.get(key)
            for key in (
                "execution_plan_schema_version",
                "execution_plan_id",
                "run_id",
                "task_id",
                "plan_scope",
                "planning_state",
                "plan_origin",
                "plan_created_at",
                "plan_finalized_at",
                "selected_mode",
                "execution_profile",
                "cognitive_pipeline",
                "declared_budget",
                "selected_tools",
                "selected_layers",
                "planned_routes",
                "planned_execution_nodes",
                "planned_reasoning_depth",
                "task_entries",
                "finalized",
                "immutable",
                "temporal_authority_state",
            )
        }
        return self._stable_id("execution_plan_fingerprint", planned_only)

    def _identity_value(self, value: Any) -> str:
        text = str(value or "").strip()
        return text or "unidentified"

    def _link_children(self, nodes: list[ExecutionNode]) -> None:
        by_id = {node.node_id: node for node in nodes}
        for node in nodes:
            if node.parent_node in by_id:
                by_id[node.parent_node].child_nodes.append(node.node_id)

    def _block_reason(
        self,
        intent: ExecutionIntent,
        budget: Mapping[str, Any],
        consumed: float,
    ) -> str | None:
        if (
            intent.tool == "dependency_reasoning"
            and self._int_value(budget.get("max_dependency_depth"), 1) <= 0
        ):
            return "max_dependency_depth<=0"
        if (
            intent.tool == "process_semantics"
            and budget.get("process_semantics_enabled") is False
        ):
            return "process_semantics_enabled=False"
        max_cost = budget.get("max_execution_cost")
        if max_cost is not None and consumed + intent.estimated_cost > float(max_cost):
            return "max_execution_cost_exceeded"
        return None

    def _report(
        self,
        selected_tools: list[str],
        concepts: list[str],
        intents: list[ExecutionIntent],
        plan: ExecutionPlan,
        active_routes: int,
        canonical_plan: Mapping[str, Any],
    ) -> dict[str, Any]:
        plan_report = plan.as_report()
        node_count = len(plan.execution_nodes)
        blocked_count = len(plan.blocked_nodes)
        confidence = 1.0
        if selected_tools:
            confidence = node_count / max(len(selected_tools), 1)
            if blocked_count:
                confidence *= 0.85
        budget_receipt = canonical_plan.get(
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT",
            {},
        )
        return {
            "system": self.system_name,
            "report_state": "final",
            "EXECUTION_PLAN_REPORT": True,
            "selected_tools": selected_tools,
            "attributed_concepts": concepts,
            "generated_intents": [
                intent.as_report() for intent in intents
            ],
            "generated_execution_nodes": plan_report["execution_nodes"],
            "dependency_nodes": plan_report["dependency_nodes"],
            "process_nodes": plan_report["process_nodes"],
            "causal_nodes": plan_report["causal_nodes"],
            "blocked_nodes": plan_report["blocked_nodes"],
            "deferred_nodes": plan_report["deferred_nodes"],
            "pruning_log": plan_report["pruning_log"],
            "execution_order": plan_report["execution_order"],
            "active_routes": active_routes,
            "execution_nodes": node_count,
            "planner_confidence": round(max(0.0, min(confidence, 1.0)), 4),
            "planner_summary": {
                "intents_generated": len(intents),
                "nodes_generated": node_count,
                "dependency_requests_created": bool(plan.dependency_nodes),
                "process_nodes_created": bool(plan.process_nodes),
                "causal_nodes_created": bool(plan.causal_nodes),
                "blocked_nodes": blocked_count,
                "deferred_nodes": len(plan.deferred_nodes),
            },
            "execution_plan_schema_version": canonical_plan.get("execution_plan_schema_version"),
            "execution_plan_id": canonical_plan.get("execution_plan_id"),
            "execution_plan_state": canonical_plan.get("planning_state"),
            "execution_plan_finalized": canonical_plan.get("execution_plan_finalized"),
            "execution_plan_immutable": canonical_plan.get("execution_plan_immutable"),
            "execution_plan_forwarded": canonical_plan.get("execution_plan_forwarded"),
            "selected_tool_count": canonical_plan.get("selected_tool_count"),
            "reconciled_tool_count": len(canonical_plan.get("tool_reconciliation", []) or []),
            "selected_layer_count": canonical_plan.get("selected_layer_count"),
            "reconciled_layer_count": len(canonical_plan.get("layer_reconciliation", []) or []),
            "active_route_count": canonical_plan.get("active_route_count"),
            "reconciled_route_count": len(canonical_plan.get("route_reconciliation", []) or []),
            "execution_node_count": canonical_plan.get("execution_node_count"),
            "dependency_activation_request_count": len(canonical_plan.get("dependency_activation_requests", []) or []),
            "process_stage_request_count": len(canonical_plan.get("process_stage_requests", []) or []),
            "unresolved_selected_item_count": canonical_plan.get("unresolved_selected_item_count"),
            "execution_plan_reconciliation_state": canonical_plan.get("execution_plan_reconciliation_state"),
            "execution_plan_validation_state": canonical_plan.get("execution_plan_validation_state"),
            "execution_plan_failure_cause": canonical_plan.get("execution_plan_failure_cause"),
            "dependency_activation_state": canonical_plan.get("dependency_activation_state"),
            "process_stage_state": canonical_plan.get("process_stage_state"),
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT": budget_receipt,
            "runtime_budget_enforcement_report": budget_receipt,
            "canonical_execution_plan": canonical_plan,
        }

    def _requests_for(self, nodes: list[ExecutionNode]) -> dict[str, dict[str, Any]]:
        requests = {}
        for node in nodes:
            requests[node.originating_tool] = {
                "tool_name": node.originating_tool,
                "node_id": node.node_id,
                "stage": node.stage,
                "request_state": "REQUESTED",
                "activation_state": (
                    "BLOCKED" if node.status == "BLOCKED" else "REQUESTED"
                ),
                "status": node.status,
                "requested_by": self.system_name,
                "reason": node.activation_reason,
            }
        return requests

    def _selected_tools(
        self,
        enabled_tools: list[str] | None,
        context: Mapping[str, Any],
    ) -> list[str]:
        tools = set()
        report = context.get("tool_selection_report", {})
        if isinstance(report, Mapping):
            if "selected_tools" in report:
                tools.update(report.get("selected_tools", []) or [])
                return sorted(str(tool) for tool in tools if tool)
            tools.update(report.get("enabled_tools", []) or [])
        if "selected_tools" in context:
            tools.update(context.get("selected_tools", []) or [])
            return sorted(str(tool) for tool in tools if tool)
        tools.update(enabled_tools or [])
        tools.update(context.get("enabled_tools", []) or [])
        return sorted(str(tool) for tool in tools if tool)

    def _concepts(
        self,
        attributed_concepts: list[str] | None,
        context: Mapping[str, Any],
    ) -> list[str]:
        concepts = []
        for concept in attributed_concepts or []:
            if concept:
                concepts.append(str(concept))
        for key in ("semantic_attribution_report", "introspection_report"):
            report = context.get(key, {})
            if isinstance(report, Mapping):
                for concept in report.get("attributed_concepts", []) or []:
                    if concept:
                        concepts.append(str(concept))
        return list(dict.fromkeys(concepts))

    def _budget(self, runtime_budget: Any, context: Mapping[str, Any]) -> dict[str, Any]:
        source = runtime_budget or context.get("current_reasoning_budget") or {}
        if isinstance(source, Mapping):
            return dict(source)
        return {
            key: getattr(source, key, None)
            for key in (
                "mode",
                "max_active_routes",
                "max_reasoning_depth",
                "max_dependency_depth",
                "process_semantics_enabled",
                "max_execution_cost",
            )
        }

    def _route_count(
        self,
        active_routes: int | None,
        selected_tools: list[str],
        context: Mapping[str, Any],
    ) -> int:
        if active_routes is not None:
            return self._int_value(active_routes, len(selected_tools))
        report = context.get("introspection_report", {})
        if isinstance(report, Mapping):
            return self._int_value(report.get("active_routes"), len(selected_tools))
        return len(selected_tools)

    def _reason(
        self,
        tool: str,
        task_profile: Any,
        context: Mapping[str, Any],
    ) -> str:
        selection = context.get("tool_selection_report", {})
        if isinstance(selection, Mapping):
            reasons = selection.get("selection_reason", {})
            if isinstance(reasons, Mapping) and reasons.get(tool):
                return str(reasons[tool])
        if task_profile:
            return "selected_by_task_profile_and_runtime_budget"
        return "selected_by_tool_selection"

    def _required_budget(
        self,
        tool: str,
        budget: Mapping[str, Any],
    ) -> dict[str, Any]:
        if tool == "dependency_reasoning":
            return {"max_dependency_depth": budget.get("max_dependency_depth")}
        if tool == "process_semantics":
            return {
                "process_semantics_enabled":
                budget.get("process_semantics_enabled")
            }
        if tool == "causal_validation":
            return {"max_active_routes": budget.get("max_active_routes")}
        return {"max_active_routes": budget.get("max_active_routes")}

    def _count(self, value: Any) -> int:
        if value is None:
            return 0
        if isinstance(value, Mapping):
            for key in (
                "context_count",
                "semantic_context_count",
                "truth_candidate_count",
                "candidate_count",
            ):
                if key in value:
                    return self._int_value(value.get(key), 0)
            return len(value)
        if isinstance(value, (list, tuple, set)):
            return len(value)
        return 1

    def _int_value(self, value: Any, default: int = 0) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


execution_planner = ExecutionPlanner()


__all__ = [
    "ExecutionIntent",
    "ExecutionNode",
    "ExecutionPlan",
    "ExecutionPlanner",
    "execution_planner",
]
