"""Temporary influence control with anti-domination limits."""

from __future__ import annotations

from typing import Any, Mapping


class InfluenceController:
    max_influence = 0.85
    decay_rate = 0.05

    def __init__(self):
        self.influence_scores: dict[str, float] = {}

    def update(
        self,
        subsystem_name: str,
        trust_score: float,
        metrics: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = dict(metrics or {})
        previous = self.influence_scores.get(subsystem_name, 0.5)
        decayed = max(0.0, previous - self.decay_rate)
        temporary_gain = max(0.0, float(trust_score) - 0.5) * 0.30
        penalty = self._number(data.get("influence_reduction"))
        if data.get("reward_hacking_detected") is True:
            penalty += 0.20
        influence = min(self.max_influence, max(0.0, decayed + temporary_gain - penalty))
        if data.get("dominance_share") is not None and self._number(data.get("dominance_share")) > 0.35:
            influence = min(influence, 0.60)
        self.influence_scores[subsystem_name] = influence
        return {
            "subsystem_name": subsystem_name,
            "trust_score": trust_score,
            "influence_score": influence,
            "authority_score": data.get("authority_score"),
            "constitutional_authority_modified": False,
            "anti_domination_limit": self.max_influence,
        }

    def get(self, subsystem_name: str, default: float = 0.5) -> float:
        return self.influence_scores.get(subsystem_name, default)

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


influence_controller = InfluenceController()


__all__ = [
    "InfluenceController",
    "influence_controller",
]
