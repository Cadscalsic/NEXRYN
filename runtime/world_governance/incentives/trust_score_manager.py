"""Trust scoring separated from constitutional authority."""

from __future__ import annotations

from typing import Any, Mapping


class TrustScoreManager:
    def __init__(self):
        self.trust_scores: dict[str, float] = {}

    def update(
        self,
        subsystem_name: str,
        metrics: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = dict(metrics or {})
        reliability = self._score(data.get("reliability", data.get("performance_score", 0.5)))
        alignment = self._score(data.get("alignment", data.get("identity_alignment", 0.5)))
        efficiency = self._score(data.get("efficiency", data.get("runtime_efficiency", 0.5)))
        reuse = self._score(data.get("reuse_effectiveness", data.get("reuse_gain", 0.5)))
        trust_score = (reliability + alignment + efficiency + reuse) / 4.0
        if data.get("budget_compliance") is False:
            trust_score -= 0.10
        if data.get("reward_hacking_detected") is True:
            trust_score -= 0.25
        trust_score = self._score(trust_score)
        self.trust_scores[subsystem_name] = trust_score
        return {
            "subsystem_name": subsystem_name,
            "trust_score": trust_score,
            "components": {
                "reliability": reliability,
                "alignment": alignment,
                "efficiency": efficiency,
                "reuse_effectiveness": reuse,
            },
            "constitutional_authority_modified": False,
        }

    def get(self, subsystem_name: str, default: float = 0.5) -> float:
        return self.trust_scores.get(subsystem_name, default)

    def _score(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


trust_score_manager = TrustScoreManager()


__all__ = [
    "TrustScoreManager",
    "trust_score_manager",
]
