"""Time and attempt budget controller for localization."""

from __future__ import annotations

import time

from runtime.transformation_localization.localization_metrics import (
    MAX_LOCALIZATION_ATTEMPTS,
    MAX_LOCALIZATION_TIME,
    MAX_OBJECT_MATCHES,
)


class LocalizationBudgetController:
    def start(self) -> dict[str, float | int]:
        return {
            "started_at": time.perf_counter(),
            "attempts": 0,
        }

    def record_attempt(self, budget: dict[str, float | int]) -> bool:
        budget["attempts"] = int(budget.get("attempts", 0)) + 1
        return self.exceeded(budget)

    def exceeded(self, budget: dict[str, float | int]) -> bool:
        return (
            self.duration(budget) > MAX_LOCALIZATION_TIME
            or int(budget.get("attempts", 0)) >= MAX_LOCALIZATION_ATTEMPTS
        )

    def duration(self, budget: dict[str, float | int]) -> float:
        return time.perf_counter() - float(budget.get("started_at", time.perf_counter()))

    def report(self, budget: dict[str, float | int]) -> dict[str, float | int | bool]:
        return {
            "localization_duration": round(self.duration(budget), 4),
            "localization_attempts": int(budget.get("attempts", 0)),
            "max_localization_time": MAX_LOCALIZATION_TIME,
            "max_localization_attempts": MAX_LOCALIZATION_ATTEMPTS,
            "max_object_matches": MAX_OBJECT_MATCHES,
            "budget_exceeded": self.exceeded(budget),
        }


localization_budget_controller = LocalizationBudgetController()


__all__ = [
    "LocalizationBudgetController",
    "localization_budget_controller",
]
