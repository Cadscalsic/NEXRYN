"""Initial execution planning from lightweight task profiles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from runtime.resource_governance.execution_plan import ExecutionPlan
from runtime.resource_governance.layer_state_registry import LayerState
from runtime.resource_governance.task_profiler import TaskProfile


class ExecutionStrategy(str, Enum):
    LIGHT_EXECUTION = "LIGHT_EXECUTION"
    BALANCED_EXECUTION = "BALANCED_EXECUTION"
    DEEP_EXECUTION = "DEEP_EXECUTION"
    RECOVERY_EXECUTION = "RECOVERY_EXECUTION"
    DIAGNOSTIC_EXECUTION = "DIAGNOSTIC_EXECUTION"
    DEEP_EXECUTION_REQUIRED = "DEEP_EXECUTION_REQUIRED"
    UNCERTAIN_EXECUTION = "UNCERTAIN_EXECUTION"


CAPABILITY_LAYER_MAP = {
    "object_tracking": "object_tracking",
    "color_mapping": "color_mapping",
    "transformation_reasoning": "transformation_reasoning",
    "semantic_compilation": "semantic_compilation",
    "spatial_reasoning": "spatial_reasoning",
    "topology_reasoning": "topology_reasoning",
    "gravity_reasoning": "gravity_reasoning",
    "rotation_execution": "rotation_execution",
    "reflection_execution": "reflection_execution",
    "scaling_execution": "scaling_execution",
    "path_reasoning": "path_reasoning",
    "path_execution": "path_execution",
    "localized_repair": "localized_repair",
    "counterfactual_repair": "counterfactual_repair",
    "contradiction_resolution": "contradiction_resolution",
    "alternative_proposal_source": "alternative_proposal_source",
    "dependency_reasoning": "dependency_reasoning",
    "knowledge_fabric": "knowledge_fabric",
    "semantic_memory_integration": "semantic_memory",
    "candidate_arena": "candidate_arena",
    "diagnostic_probe": "diagnostic_probe",
}


@dataclass(frozen=True)
class InitialExecutionResourcePlan:
    task_profile: TaskProfile
    execution_strategy: ExecutionStrategy
    execution_plan: ExecutionPlan

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_profile": self.task_profile.as_dict(),
            "execution_strategy": self.execution_strategy.value,
            "execution_plan": self.execution_plan.as_dict(),
        }


class InitialExecutionPlanner:
    def plan(self, profile: TaskProfile) -> InitialExecutionResourcePlan:
        strategy = _strategy_for_profile(profile)
        plan = ExecutionPlan()

        expected_layers = _capabilities_to_layers(profile.expected_capabilities)
        potential_layers = _capabilities_to_layers(profile.potential_capabilities)
        not_required_layers = _capabilities_to_layers(profile.not_required_capabilities)

        if "object_tracking" in expected_layers:
            plan.record("object_tracking", LayerState.REQUIRED)
            expected_layers.discard("object_tracking")

        for layer_name in sorted(expected_layers):
            plan.record(layer_name, LayerState.ACTIVE)

        for layer_name in sorted(potential_layers):
            plan.record(layer_name, LayerState.ON_DEMAND)

        for layer_name in sorted(not_required_layers):
            if layer_name in {"knowledge_fabric", "semantic_memory", "report_binding", "report_rendering"}:
                plan.record(layer_name, LayerState.DEFERRED)
            else:
                plan.record(layer_name, LayerState.BLOCKED)

        if "report_binding" not in plan.deferred_layers:
            plan.record("report_binding", LayerState.DEFERRED)
        if "report_rendering" not in plan.deferred_layers:
            plan.record("report_rendering", LayerState.DEFERRED)

        return InitialExecutionResourcePlan(
            task_profile=profile,
            execution_strategy=strategy,
            execution_plan=plan,
        )

    def build_report(self, resource_plan: InitialExecutionResourcePlan) -> dict[str, Any]:
        profile = resource_plan.task_profile
        plan = resource_plan.execution_plan
        return {
            "TASK_RESOURCE_PROFILE_REPORT": True,
            "task_complexity": profile.task_complexity,
            "expected_capabilities": sorted(profile.expected_capabilities),
            "execution_strategy": resource_plan.execution_strategy.value,
            "estimated_costs": profile.resource_plan.as_dict(),
            "required_layers": len(plan.required_layers),
            "active_layers": len(plan.active_layers),
            "on_demand_layers": len(plan.on_demand_layers),
            "deferred_layers": len(plan.deferred_layers),
            "blocked_layers": len(plan.blocked_layers),
            "execution_plan": plan.as_dict(),
            "task_profile": profile.as_dict(),
        }

    def render_report(self, resource_plan: InitialExecutionResourcePlan) -> str:
        report = self.build_report(resource_plan)
        return "\n".join([
            "==================================================",
            "TASK RESOURCE PROFILE REPORT",
            "==================================================",
            "",
            "Task Complexity:",
            "",
            report["task_complexity"],
            "",
            "Execution Strategy:",
            "",
            report["execution_strategy"],
            "",
            "Expected Capabilities:",
            "",
            *[f"- {item}" for item in report["expected_capabilities"]],
            "",
            "Required Layers:",
            "",
            str(report["required_layers"]),
            "",
            "Active Layers:",
            "",
            str(report["active_layers"]),
            "",
            "On Demand Layers:",
            "",
            str(report["on_demand_layers"]),
            "",
            "Deferred Layers:",
            "",
            str(report["deferred_layers"]),
            "",
            "Blocked Layers:",
            "",
            str(report["blocked_layers"]),
            "",
            "Estimated Execution Cost:",
            "",
            report["estimated_costs"]["expected_execution_cost"],
        ])


def _strategy_for_profile(profile: TaskProfile) -> ExecutionStrategy:
    if profile.uncertainty_score in {"HIGH", "EXTREME"}:
        return ExecutionStrategy.UNCERTAIN_EXECUTION
    if profile.task_complexity in {"HIGH", "EXTREME"}:
        return ExecutionStrategy.DEEP_EXECUTION_REQUIRED
    if profile.task_complexity == "MEDIUM":
        return ExecutionStrategy.BALANCED_EXECUTION
    return ExecutionStrategy.LIGHT_EXECUTION


def _capabilities_to_layers(capabilities: set[str]) -> set[str]:
    return {
        CAPABILITY_LAYER_MAP.get(capability, capability)
        for capability in capabilities
    }


__all__ = [
    "CAPABILITY_LAYER_MAP",
    "ExecutionStrategy",
    "InitialExecutionPlanner",
    "InitialExecutionResourcePlan",
]
