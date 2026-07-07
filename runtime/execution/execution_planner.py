"""Execution planning bridge for selected cognitive tools.

This module is intentionally lightweight: it does not implement reasoning
engines. It converts selected tools and existing runtime evidence into explicit
execution intents, nodes, requests, and block/defer diagnostics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping


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
        report = self._report(
            selected_tools,
            concepts,
            intents,
            plan,
            route_count,
        )
        return {
            "execution_plan": plan.as_report(),
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
    ) -> dict[str, Any]:
        plan_report = plan.as_report()
        node_count = len(plan.execution_nodes)
        blocked_count = len(plan.blocked_nodes)
        confidence = 1.0
        if selected_tools:
            confidence = node_count / max(len(selected_tools), 1)
            if blocked_count:
                confidence *= 0.85
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
        tools = set(enabled_tools or [])
        report = context.get("tool_selection_report", {})
        if isinstance(report, Mapping):
            tools.update(report.get("enabled_tools", []) or [])
            tools.update(report.get("selected_tools", []) or [])
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
