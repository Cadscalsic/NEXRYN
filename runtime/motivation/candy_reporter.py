"""Build public cognitive candy reports."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.motivation.candy_decay_engine import candy_decay_engine
from runtime.motivation.candy_types import CANDY_TYPES, CONSTITUTIONAL_CONSTRAINTS


class CandyReporter:
    def build(
        self,
        balances: Mapping[str, float],
        dominant_motivation: str,
        reward_hacking_risk: float,
        reuse_bonus: float,
        budget_adjustments: Mapping[str, Any],
    ) -> dict[str, Any]:
        report = {
            key: round(float(balances.get(key, 0.0)), 4)
            for key in CANDY_TYPES
        }
        report.update({
            "system": "COGNITIVE_CANDY_REPORT",
            "dominant_motivation": dominant_motivation,
            "reward_hacking_risk": round(float(reward_hacking_risk), 4),
            "average_decay": candy_decay_engine.average_decay(CANDY_TYPES),
            "reuse_bonus": round(float(reuse_bonus), 4),
            "budget_adjustments": dict(budget_adjustments),
            "constitutional_constraints": dict(CONSTITUTIONAL_CONSTRAINTS),
        })
        return report


candy_reporter = CandyReporter()


__all__ = [
    "CandyReporter",
    "candy_reporter",
]
