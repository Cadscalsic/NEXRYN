"""Budget and loop control for counterfactual reasoning."""

from __future__ import annotations

from typing import Mapping


class CounterfactualBudgetManager:
    system_name = "counterfactual_budget_manager"

    def __init__(self):
        self.seen: set[str] = set()

    def allow(self, counterfactual_id: str, used: int, budget: Mapping) -> dict:
        if counterfactual_id in self.seen:
            return {"allowed": False, "stop_reason": "NO_INFORMATION_GAIN"}
        if used >= int(budget.get("max_counterfactuals", 4) or 4):
            return {"allowed": False, "stop_reason": "BUDGET_EXHAUSTED"}
        self.seen.add(counterfactual_id)
        return {"allowed": True, "stop_reason": None}

    def stop_reason(self, stability_report: Mapping, falsification_report: Mapping, generated: int) -> str:
        if falsification_report.get("falsification_state") in {"STRONGLY_FALSIFIED", "FULLY_FALSIFIED"}:
            return "FALSIFICATION_CONFIRMED"
        if stability_report.get("stability_state") == "STABLE_WINNER":
            return "WINNER_STABLE"
        if generated <= 0:
            return "NO_VALID_ALTERNATIVES"
        return "EVIDENCE_COLLECTED"


counterfactual_budget_manager = CounterfactualBudgetManager()

__all__ = ["CounterfactualBudgetManager", "counterfactual_budget_manager"]
