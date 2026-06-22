"""Outcome-oriented constitutional incentive engine."""

from __future__ import annotations

from typing import Any, Mapping


class IncentiveEngine:
    def evaluate(
        self,
        subsystem_name: str,
        metrics: Mapping[str, Any] | None = None,
        reward_hacking_penalty: float = 0.0,
        budget_compliance: bool = True,
    ) -> dict[str, Any]:
        data = dict(metrics or {})
        accuracy_gain = self._score(data.get("accuracy_gain", data.get("accuracy_improvement", 0.0)))
        reuse_gain = max(
            self._score(data.get("reuse_gain")),
            self._score(data.get("strategy_reuse_rate")),
            self._score(data.get("program_reuse_rate")),
            self._score(data.get("context_reuse_rate")),
        )
        efficiency_gain = self._score(data.get("efficiency_gain", data.get("runtime_efficiency", 0.0)))
        identity_alignment = self._score(data.get("identity_alignment", 0.5))
        truth_alignment = self._score(data.get("truth_alignment", 0.5))
        reward_score = (
            accuracy_gain * 0.30
            + reuse_gain * 0.25
            + efficiency_gain * 0.20
            + identity_alignment * 0.15
            + truth_alignment * 0.10
        )
        if not budget_compliance:
            reward_score -= 0.15
        reward_score -= max(0.0, float(reward_hacking_penalty)) * 0.10
        reward_score = self._score(reward_score)
        return {
            "subsystem_name": subsystem_name,
            "reward_score": reward_score,
            "reward_components": {
                "accuracy_gain": accuracy_gain,
                "reuse_gain": reuse_gain,
                "efficiency_gain": efficiency_gain,
                "identity_alignment": identity_alignment,
                "truth_alignment": truth_alignment,
            },
            "not_rewarded": [
                "reasoning_depth",
                "number_of_hypotheses",
                "execution_duration",
                "governance_cycles",
                "memory_writes",
            ],
        }

    def _score(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


incentive_engine = IncentiveEngine()


__all__ = [
    "IncentiveEngine",
    "incentive_engine",
]
