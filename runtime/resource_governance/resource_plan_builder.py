"""Initial resource cost estimation for task profiles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from runtime.resource_governance.complexity_estimator import ComplexityLevel


class ResourceCostLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


@dataclass(frozen=True)
class ResourcePlan:
    expected_reasoning_cost: ResourceCostLevel
    expected_memory_cost: ResourceCostLevel
    expected_report_cost: ResourceCostLevel
    expected_execution_cost: ResourceCostLevel

    def as_dict(self) -> dict[str, str]:
        return {
            "expected_reasoning_cost": self.expected_reasoning_cost.value,
            "expected_memory_cost": self.expected_memory_cost.value,
            "expected_report_cost": self.expected_report_cost.value,
            "expected_execution_cost": self.expected_execution_cost.value,
        }


class ResourcePlanBuilder:
    def build(
        self,
        complexity: Mapping[str, ComplexityLevel],
        expected_capabilities: set[str],
    ) -> ResourcePlan:
        reasoning_score = max(
            _level_score(complexity.get("transformation_complexity")),
            _level_score(complexity.get("spatial_complexity")),
            _level_score(complexity.get("topology_complexity")),
            _level_score(complexity.get("dependency_complexity")),
        )
        memory_score = max(
            _level_score(complexity.get("semantic_complexity")),
            2 if "semantic_memory_integration" in expected_capabilities else 1,
            2 if "knowledge_fabric" in expected_capabilities else 1,
        )
        report_score = max(1, reasoning_score - 1)
        execution_score = max(
            reasoning_score,
            memory_score,
            _level_score(complexity.get("execution_uncertainty")),
        )
        return ResourcePlan(
            expected_reasoning_cost=_score_to_cost(reasoning_score),
            expected_memory_cost=_score_to_cost(memory_score),
            expected_report_cost=_score_to_cost(report_score),
            expected_execution_cost=_score_to_cost(execution_score),
        )


def _level_score(level: Any) -> int:
    if level == ComplexityLevel.EXTREME:
        return 4
    if level == ComplexityLevel.HIGH:
        return 3
    if level == ComplexityLevel.MEDIUM:
        return 2
    return 1


def _score_to_cost(score: int) -> ResourceCostLevel:
    if score >= 4:
        return ResourceCostLevel.EXTREME
    if score == 3:
        return ResourceCostLevel.HIGH
    if score == 2:
        return ResourceCostLevel.MEDIUM
    return ResourceCostLevel.LOW


__all__ = [
    "ResourceCostLevel",
    "ResourcePlan",
    "ResourcePlanBuilder",
]
