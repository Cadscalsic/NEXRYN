"""Detect early signs of cognitive stagnation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass
class StagnationAssessment:
    stagnation_level: str
    affected_domains: list[str]
    recommended_actions: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class StagnationDetector:
    def assess(self, runtime_context: Mapping[str, Any] | None = None) -> StagnationAssessment:
        context = dict(runtime_context or {})
        affected: list[str] = []
        actions: list[str] = []
        score = 0

        if self._number(context.get("repeated_governance_cycles")) >= 3:
            affected.append("governance")
            actions.append("stabilize_governance_loop")
            score += 2

        if self._number(context.get("learning_improvement_rate")) <= 0.01 and (
            "learning_improvement_rate" in context
        ):
            affected.append("learning")
            actions.append("redirect_learning_to_high_value_gaps")
            score += 2

        if self._number(context.get("strategy_novelty")) <= 0.10 and (
            "strategy_novelty" in context
        ):
            affected.append("strategy")
            actions.append("diversify_strategy_search")
            score += 1

        if self._number(context.get("cache_miss_rate")) >= 0.50:
            affected.append("memory")
            actions.append("optimize_memory_indexing")
            score += 1

        if (
            self._number(context.get("reasoning_cycles_without_accuracy_gain")) >= 3
        ):
            affected.append("reasoning")
            actions.append("freeze_unproductive_reasoning_path")
            score += 2

        if score >= 5:
            level = "HIGH"
        elif score >= 3:
            level = "MEDIUM"
        elif score > 0:
            level = "LOW"
        else:
            level = "NONE"

        return StagnationAssessment(
            level,
            sorted(set(affected)),
            sorted(set(actions)),
        )

    def _number(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


stagnation_detector = StagnationDetector()


__all__ = [
    "StagnationAssessment",
    "StagnationDetector",
    "stagnation_detector",
]
