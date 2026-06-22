"""Track objective progress, regressions, stagnation, and efficiency."""

from __future__ import annotations

from typing import Any, Mapping


class ObjectiveTracker:
    def track(
        self,
        runtime_context: Mapping[str, Any] | None = None,
        objective_distance: Mapping[str, float] | None = None,
    ) -> dict[str, Any]:
        context = dict(runtime_context or {})
        distances = dict(objective_distance or {})
        progress = {
            key: max(0.0, 1.0 - float(value))
            for key, value in distances.items()
        }
        regressions = [
            key for key, value in context.get("objective_deltas", {}).items()
            if self._number(value) < -0.05
        ] if isinstance(context.get("objective_deltas"), Mapping) else []
        stagnation = []
        if self._number(context.get("learning_improvement_rate")) <= 0.01 and "learning_improvement_rate" in context:
            stagnation.append("learning")
        if self._number(context.get("strategy_reuse_delta")) <= 0.0 and "strategy_reuse_delta" in context:
            stagnation.append("strategy_reuse")
        resource_efficiency = self._resource_efficiency(context)
        misaligned = [
            item for item in context.get("recent_investments", []) or []
            if isinstance(item, Mapping)
            and self._number(item.get("purpose_alignment")) < 0.35
        ]
        conflicts = [
            key for key, value in distances.items()
            if float(value) > 0.45
        ]
        return {
            "objective_progress": progress,
            "regressions": regressions,
            "stagnation": stagnation,
            "resource_efficiency": resource_efficiency,
            "misaligned_investments": list(misaligned),
            "objective_conflicts": conflicts,
        }

    def _resource_efficiency(self, context: Mapping[str, Any]) -> float:
        value = context.get("resource_efficiency")
        if value is not None:
            return self._number(value)
        gain = self._number(context.get("recent_value_gain"))
        cost = self._number(context.get("recent_resource_cost"))
        if cost <= 0.0:
            return gain
        return min(1.0, max(0.0, gain / max(cost, 0.01)))

    def _number(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


objective_tracker = ObjectiveTracker()


__all__ = [
    "ObjectiveTracker",
    "objective_tracker",
]
