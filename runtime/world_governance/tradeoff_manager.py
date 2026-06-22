"""Explainable trade-off management for autonomous direction."""

from __future__ import annotations

from typing import Any, Mapping


class TradeoffManager:
    def analyze(
        self,
        runtime_context: Mapping[str, Any] | None = None,
        selected_direction: str | None = None,
    ) -> list[dict[str, Any]]:
        context = dict(runtime_context or {})
        direction = str(selected_direction or "")
        tradeoffs = [
            self._tradeoff(
                "exploration_vs_exploitation",
                self._number(context.get("exploration_need")),
                self._number(context.get("reuse_pressure")),
                "EXPLORE" if direction == "EXPLORE" else "reuse_when_reliable_explore_when_coverage_is_low",
            ),
            self._tradeoff(
                "reuse_vs_innovation",
                self._number(context.get("strategy_reuse_rate")),
                self._number(context.get("innovation_need")),
                "prefer_reuse_unless_generalization_gap_requires_innovation",
            ),
            self._tradeoff(
                "speed_vs_accuracy",
                self._number(context.get("runtime_efficiency")),
                self._number(context.get("accuracy_need", context.get("generalization"))),
                "do_not_buy_speed_by_lowering_truth_or_accuracy",
            ),
            self._tradeoff(
                "diversity_vs_stability",
                self._number(context.get("diversity_score")),
                self._number(context.get("stability_need")),
                "diversify_inside_identity_and_truth_constraints",
            ),
            self._tradeoff(
                "reasoning_vs_memory",
                self._number(context.get("reasoning_pressure")),
                self._number(context.get("memory_reuse_rate")),
                "prefer_memory_reuse_when evidence is stable; reason when gaps remain",
            ),
        ]
        return tradeoffs

    def _tradeoff(
        self,
        name: str,
        left: float,
        right: float,
        policy: str,
    ) -> dict[str, Any]:
        if abs(left - right) < 0.10:
            posture = "BALANCED"
        elif left > right:
            posture = "LEFT_PRESSURE"
        else:
            posture = "RIGHT_PRESSURE"
        return {
            "tradeoff": name,
            "left_signal": left,
            "right_signal": right,
            "posture": posture,
            "policy": policy,
        }

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


tradeoff_manager = TradeoffManager()


__all__ = [
    "TradeoffManager",
    "tradeoff_manager",
]
