"""Translate candy balances into future budget recommendations."""

from __future__ import annotations

from typing import Mapping

from runtime.motivation.motivation_state import clamp


class MotivationPolicy:
    def recommend(self, balances: Mapping[str, float] | None = None) -> dict[str, object]:
        balances = balances if isinstance(balances, Mapping) else {}
        adjustments = {
            "reasoning_budget_multiplier": 1.0,
            "governance_budget_multiplier": 1.0,
            "exploration_budget_multiplier": 1.0,
            "self_repair_priority_delta": 0.0,
            "strategy_reuse_priority_delta": 0.0,
            "learning_priority_delta": 0.0,
        }
        if clamp(balances.get("reuse_candy")) > 0.80:
            adjustments["reasoning_budget_multiplier"] *= 0.80
            adjustments["strategy_reuse_priority_delta"] += 0.20
        if clamp(balances.get("efficiency_candy")) > 0.80:
            adjustments["governance_budget_multiplier"] *= 0.90
        if clamp(balances.get("curiosity_candy")) < 0.30:
            adjustments["exploration_budget_multiplier"] *= 0.50
        if clamp(balances.get("recovery_candy")) < 0.20:
            adjustments["self_repair_priority_delta"] += 0.20
        if clamp(balances.get("generalization_candy")) > 0.70:
            adjustments["learning_priority_delta"] += 0.10
        return {
            "system": "motivation_policy",
            "budget_adjustments": {
                key: round(value, 4)
                for key, value in adjustments.items()
            },
            "direct_execution_control": False,
            "governance_decides": True,
        }


motivation_policy = MotivationPolicy()


__all__ = [
    "MotivationPolicy",
    "motivation_policy",
]
