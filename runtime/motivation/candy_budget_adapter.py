"""Apply motivation policy to budget reports as recommendations only."""

from __future__ import annotations

from typing import Any, Mapping


class CandyBudgetAdapter:
    def adapt(
        self,
        current_budget: Mapping[str, Any] | None,
        policy_report: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        budget = dict(current_budget or {})
        adjustments = dict((policy_report or {}).get("budget_adjustments", {}))
        return {
            "system": "candy_budget_adapter",
            "current_budget": budget,
            "budget_adjustments": adjustments,
            "recommended_budget": self._recommended_budget(budget, adjustments),
            "recommendation_only": True,
            "direct_execution_control": False,
        }

    def _recommended_budget(
        self,
        budget: dict[str, Any],
        adjustments: dict[str, Any],
    ) -> dict[str, Any]:
        recommended = dict(budget)
        if self._is_number(recommended.get("max_reasoning_depth")):
            recommended["max_reasoning_depth"] = max(
                1,
                int(
                    recommended["max_reasoning_depth"]
                    * adjustments.get("reasoning_budget_multiplier", 1.0)
                ),
            )
        if self._is_number(recommended.get("max_active_routes")):
            recommended["max_active_routes"] = max(
                1,
                int(
                    recommended["max_active_routes"]
                    * adjustments.get("reasoning_budget_multiplier", 1.0)
                ),
            )
        recommended["motivation_policy_applied"] = False
        return recommended

    def _is_number(self, value: Any) -> bool:
        try:
            float(value)
            return value is not None
        except (TypeError, ValueError):
            return False


candy_budget_adapter = CandyBudgetAdapter()


__all__ = [
    "CandyBudgetAdapter",
    "candy_budget_adapter",
]
