"""Configurable winner selection policy for arena candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class WinnerSelectionThresholds:
    strong_score: float = 0.90
    strong_margin: float = 0.05
    conditional_score: float = 0.80
    conditional_margin: float = 0.02
    tie_margin: float = 0.02
    minimum_score: float = 0.55
    minimum_accuracy: float = 0.60


class WinnerSelectionPolicy:
    """Select winners from scored simulated candidates using explicit thresholds."""

    system_name = "winner_selection_policy"

    def __init__(self, thresholds: WinnerSelectionThresholds | None = None):
        self.thresholds = thresholds or WinnerSelectionThresholds()

    def select(
        self,
        scored_candidates: list[Mapping[str, Any]] | None,
        simulations: Mapping[str, Mapping[str, Any]] | None = None,
        analysis_only: bool = False,
    ) -> dict[str, Any]:
        simulations = simulations if isinstance(simulations, Mapping) else {}
        eligible = [
            dict(item) for item in scored_candidates or []
            if isinstance(item, Mapping) and item.get("eligible_for_selection")
        ]
        if not eligible:
            scored = [dict(item) for item in scored_candidates or [] if isinstance(item, Mapping)]
            blocked = [
                item for item in scored
                if item.get("selection_blockers")
            ]
            state = "ALL_CANDIDATES_REJECTED" if blocked and len(blocked) == len(scored) else "NO_SAFE_WINNER"
            explanation = (
                "All candidates were rejected by blockers."
                if state == "ALL_CANDIDATES_REJECTED"
                else "Candidates were too weak for safe selection."
            )
            return self._result(state, None, None, 0.0, explanation)
        eligible.sort(key=lambda item: item.get("final_score", 0.0), reverse=True)
        top = eligible[0]
        second = eligible[1] if len(eligible) > 1 else None
        top_score = float(top.get("final_score", 0.0) or 0.0)
        second_score = float(second.get("final_score", 0.0) or 0.0) if second else 0.0
        margin = round(top_score - second_score, 4)
        simulation = simulations.get(top.get("candidate_id"), {})
        accuracy = float(simulation.get("prediction_accuracy", 0.0) or 0.0)
        if not analysis_only and not simulation.get("simulation_success") and simulation.get("simulation_errors"):
            return self._result("NO_SAFE_WINNER", top, second, margin, "Top candidate has critical simulation errors.")
        if accuracy < self.thresholds.minimum_accuracy:
            return self._result("NO_SAFE_WINNER", top, second, margin, "Prediction quality below minimum threshold.")
        if second and abs(margin) < self.thresholds.tie_margin:
            return self._result("TIE_REQUIRES_REVIEW", top, second, margin, "Top candidates are within tie margin.")
        if top_score >= self.thresholds.strong_score and margin >= self.thresholds.strong_margin:
            return self._result("WINNER_SELECTED", top, second, margin, "Winner selected from simulation and score evidence.")
        if top_score >= self.thresholds.conditional_score and margin >= self.thresholds.conditional_margin:
            return self._result("CONDITIONAL_WINNER", top, second, margin, "Conditional winner selected with adequate evidence margin.")
        if analysis_only and top_score >= self.thresholds.minimum_score:
            return self._result("SANDBOX_ONLY_WINNER", top, second, margin, "Analysis-only sandbox winner selected.")
        return self._result("NO_SAFE_WINNER", top, second, margin, "No candidate exceeded selection thresholds.")

    def _result(self, state, winner, second, margin, explanation):
        return {
            "system": self.system_name,
            "selection_state": state,
            "winner_candidate": dict(winner) if isinstance(winner, Mapping) else None,
            "second_best_candidate": dict(second) if isinstance(second, Mapping) else None,
            "selection_margin": margin,
            "selection_explanation": explanation,
            "thresholds": self.thresholds.__dict__,
        }


winner_selection_policy = WinnerSelectionPolicy()

__all__ = [
    "WinnerSelectionPolicy",
    "WinnerSelectionThresholds",
    "winner_selection_policy",
]
