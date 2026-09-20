"""Estimate cognitive trajectory without executing learning."""

from __future__ import annotations

from typing import Any, Mapping


class TrajectoryEstimator:
    def estimate(
        self,
        direction: str,
        target_domains: list[str],
        runtime_context: Mapping[str, Any] | None = None,
        objective_distance: Mapping[str, float] | None = None,
    ) -> dict[str, float]:
        context = dict(runtime_context or {})
        distances = dict(objective_distance or {})
        relevant_gap = sum(float(distances.get(domain, 0.0)) for domain in target_domains)
        relevant_gap = relevant_gap / max(1, len(target_domains))
        base_progress = {
            "EXPAND": 0.55,
            "STABILIZE": 0.35,
            "FREEZE": 0.05,
            "DIVERSIFY": 0.45,
            "OPTIMIZE": 0.50,
            "EXPLORE": 0.40,
        }.get(direction, 0.25)
        estimated_cost = min(1.0, max(0.05, len(target_domains) * 0.12 + base_progress * 0.25))
        identity_impact = max(
            self._number(context.get("identity_risk")),
            self._number(context.get("identity_impact")),
        )
        generalization_gain = min(1.0, base_progress * 0.6 + self._number(context.get("generalization")) * 0.4)
        reuse_gain = min(
            1.0,
            base_progress * 0.4
            + max(self._number(context.get("strategy_reuse_rate")), self._number(context.get("context_reuse_rate"))) * 0.6,
        )
        expected_progress = min(1.0, max(0.0, base_progress * 0.5 + relevant_gap * 0.5))
        return {
            "expected_progress": expected_progress,
            "estimated_cost": estimated_cost,
            "identity_impact": identity_impact,
            "generalization_gain": generalization_gain,
            "reuse_gain": reuse_gain,
        }

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


trajectory_estimator = TrajectoryEstimator()


__all__ = [
    "TrajectoryEstimator",
    "trajectory_estimator",
]
