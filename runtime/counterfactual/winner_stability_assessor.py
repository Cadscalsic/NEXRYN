"""Assess preliminary winner stability after counterfactual testing."""

from __future__ import annotations

from typing import Mapping


class WinnerStabilityAssessor:
    system_name = "winner_stability_assessor"

    def assess(self, winner_candidate_id: str, comparison_report: Mapping, falsification_report: Mapping) -> dict:
        rows = comparison_report.get("counterfactual_comparisons", []) or []
        failed = [row for row in rows if row.get("evidence_class") == "SUPPORTS_ALTERNATIVE"]
        surviving = [row for row in rows if row.get("evidence_class") == "SUPPORTS_ORIGINAL"]
        strength = float(falsification_report.get("falsification_strength", 0.0) or 0.0)
        stability_score = round(max(0.0, 1.0 - strength), 4)
        replacement = comparison_report.get("best_counterfactual_id") if failed else None
        if strength >= 0.75:
            state = "WINNER_REPLACED"
            recommendation = "REVISE"
        elif strength >= 0.30:
            state = "FRAGILE_WINNER"
            recommendation = "SANDBOX"
        elif strength > 0.0:
            state = "CONDITIONALLY_STABLE"
            recommendation = "SANDBOX"
        elif rows:
            state = "STABLE_WINNER"
            recommendation = "REAL"
        else:
            state = "REQUIRES_ADDITIONAL_SEARCH"
            recommendation = "BLOCK"
        return {
            "system": self.system_name,
            "winner_candidate_id": winner_candidate_id,
            "stability_state": state,
            "stability_score": stability_score,
            "challenged_assumptions": [row.get("counterfactual_id") for row in rows],
            "surviving_assumptions": [row.get("counterfactual_id") for row in surviving],
            "failed_assumptions": [row.get("counterfactual_id") for row in failed],
            "replacement_candidate_id": replacement,
            "execution_recommendation": recommendation,
        }


winner_stability_assessor = WinnerStabilityAssessor()

__all__ = ["WinnerStabilityAssessor", "winner_stability_assessor"]
