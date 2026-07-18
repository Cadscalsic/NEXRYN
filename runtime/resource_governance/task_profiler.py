"""Task profiling for the adaptive execution governor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.resource_governance.capability_requirement_resolver import (
    CapabilityRequirement,
    CapabilityRequirementResolver,
)
from runtime.resource_governance.complexity_estimator import (
    ComplexityEstimate,
    ComplexityEstimator,
)
from runtime.resource_governance.resource_plan_builder import (
    ResourcePlan,
    ResourcePlanBuilder,
)


@dataclass(frozen=True)
class TaskProfile:
    object_complexity: str
    transformation_complexity: str
    spatial_complexity: str
    topology_complexity: str
    dependency_complexity: str
    semantic_novelty: str
    uncertainty_score: str
    estimated_execution_cost: str
    expected_reasoning_families: set[str]
    expected_capabilities: set[str]
    potential_capabilities: set[str]
    not_required_capabilities: set[str]
    task_complexity: str
    resource_plan: ResourcePlan

    def as_dict(self) -> dict[str, Any]:
        return {
            "object_complexity": self.object_complexity,
            "transformation_complexity": self.transformation_complexity,
            "spatial_complexity": self.spatial_complexity,
            "topology_complexity": self.topology_complexity,
            "dependency_complexity": self.dependency_complexity,
            "semantic_novelty": self.semantic_novelty,
            "uncertainty_score": self.uncertainty_score,
            "estimated_execution_cost": self.estimated_execution_cost,
            "expected_reasoning_families": sorted(self.expected_reasoning_families),
            "expected_capabilities": sorted(self.expected_capabilities),
            "potential_capabilities": sorted(self.potential_capabilities),
            "not_required_capabilities": sorted(self.not_required_capabilities),
            "task_complexity": self.task_complexity,
            "resource_plan": self.resource_plan.as_dict(),
        }


class TaskProfiler:
    def __init__(
        self,
        complexity_estimator: ComplexityEstimator | None = None,
        capability_resolver: CapabilityRequirementResolver | None = None,
        resource_plan_builder: ResourcePlanBuilder | None = None,
    ):
        self.complexity_estimator = complexity_estimator or ComplexityEstimator()
        self.capability_resolver = (
            capability_resolver or CapabilityRequirementResolver()
        )
        self.resource_plan_builder = resource_plan_builder or ResourcePlanBuilder()

    def profile(self, task: Any) -> TaskProfile:
        complexity = self.complexity_estimator.estimate(task)
        complexity_map = _complexity_map(complexity)
        requirement = self.capability_resolver.resolve(task, complexity_map)
        resource_plan = self.resource_plan_builder.build(
            complexity_map,
            requirement.expected_capabilities,
        )
        return _build_profile(complexity, requirement, resource_plan)


def _complexity_map(complexity: ComplexityEstimate):
    return {
        "object_complexity": complexity.object_complexity,
        "transformation_complexity": complexity.transformation_complexity,
        "spatial_complexity": complexity.spatial_complexity,
        "topology_complexity": complexity.topology_complexity,
        "dependency_complexity": complexity.dependency_complexity,
        "semantic_complexity": complexity.semantic_complexity,
        "execution_uncertainty": complexity.execution_uncertainty,
        "task_complexity": complexity.task_complexity,
    }


def _build_profile(
    complexity: ComplexityEstimate,
    requirement: CapabilityRequirement,
    resource_plan: ResourcePlan,
) -> TaskProfile:
    return TaskProfile(
        object_complexity=complexity.object_complexity.value,
        transformation_complexity=complexity.transformation_complexity.value,
        spatial_complexity=complexity.spatial_complexity.value,
        topology_complexity=complexity.topology_complexity.value,
        dependency_complexity=complexity.dependency_complexity.value,
        semantic_novelty=complexity.semantic_complexity.value,
        uncertainty_score=complexity.execution_uncertainty.value,
        estimated_execution_cost=resource_plan.expected_execution_cost.value,
        expected_reasoning_families=requirement.reasoning_families,
        expected_capabilities=requirement.expected_capabilities,
        potential_capabilities=requirement.potential_capabilities,
        not_required_capabilities=requirement.not_required_capabilities,
        task_complexity=complexity.task_complexity.value,
        resource_plan=resource_plan,
    )


__all__ = [
    "TaskProfile",
    "TaskProfiler",
]
