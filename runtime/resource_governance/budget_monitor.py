"""Runtime cognitive budget monitoring."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from runtime.resource_governance.cognitive_budget import BudgetPressureState, CognitiveBudget


@dataclass
class BudgetThresholds:
    elevated: float = 0.60
    high: float = 0.80
    critical: float = 0.95


class BudgetMonitor:
    def __init__(self, thresholds: BudgetThresholds | None = None):
        self.thresholds = thresholds or BudgetThresholds()

    def status(self, budget: CognitiveBudget) -> dict[str, Any]:
        self._refresh_wall_time(budget)
        limits = budget.limits()
        used = {name: budget.used(name) for name in limits}
        remaining = {name: budget.remaining(name) for name in limits}
        ratios = {
            name: (used[name] / limit if limit > 0 else 1.0)
            for name, limit in limits.items()
        }
        max_ratio = max(ratios.values(), default=0.0)
        pressure = self.pressure_for_ratio(max_ratio)
        exhausted = [name for name, ratio in ratios.items() if ratio >= 1.0]
        if exhausted:
            pressure = BudgetPressureState.EXHAUSTED
        return {
            "budget_used": used,
            "budget_remaining": remaining,
            "budget_usage_ratio": ratios,
            "budget_pressure_state": pressure.value,
            "projected_exhaustion": exhausted,
        }

    def pressure_for_ratio(self, ratio: float) -> BudgetPressureState:
        if ratio >= 1.0:
            return BudgetPressureState.EXHAUSTED
        if ratio >= self.thresholds.critical:
            return BudgetPressureState.CRITICAL
        if ratio >= self.thresholds.high:
            return BudgetPressureState.HIGH
        if ratio >= self.thresholds.elevated:
            return BudgetPressureState.ELEVATED
        return BudgetPressureState.NORMAL

    def _refresh_wall_time(self, budget: CognitiveBudget) -> None:
        if budget.created_at:
            elapsed = max(0.0, time.monotonic() - budget.created_at)
            budget.consumed["wall_time_seconds"] = max(
                budget.used("wall_time_seconds"),
                elapsed,
            )


__all__ = ["BudgetMonitor", "BudgetThresholds"]
