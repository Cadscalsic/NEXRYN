"""Minimal candidate revision from counterfactual evidence."""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping


class MinimalRevisionEngine:
    system_name = "minimal_revision_engine"

    def revise(self, original_candidate: Mapping, simulations: list[Mapping], comparison_report: Mapping) -> dict:
        better = [row for row in comparison_report.get("counterfactual_comparisons", []) or [] if row.get("evidence_class") == "SUPPORTS_ALTERNATIVE"]
        if not better:
            return {
                "system": self.system_name,
                "revision_required": False,
                "original_candidate_id": original_candidate.get("candidate_id"),
                "revised_candidate": None,
                "revision_operations": [],
                "revision_cost": 0.0,
                "expected_residual_reduction": 0.0,
                "requires_arena_reentry": False,
            }
        best = sorted(better, key=lambda row: (row.get("residual_delta", 0), row.get("accuracy_delta", 0)), reverse=True)[0]
        revised = deepcopy(dict(original_candidate))
        revised["candidate_id"] = f"revision:{original_candidate.get('candidate_id')}:{best.get('counterfactual_id')}"
        revised.setdefault("metadata", {})["revision_from_counterfactual"] = best.get("counterfactual_id")
        return {
            "system": self.system_name,
            "revision_required": True,
            "original_candidate_id": original_candidate.get("candidate_id"),
            "revised_candidate": revised,
            "revision_operations": [best.get("counterfactual_id")],
            "revision_cost": 0.1,
            "expected_residual_reduction": best.get("residual_delta", 0),
            "requires_arena_reentry": True,
        }


minimal_revision_engine = MinimalRevisionEngine()

__all__ = ["MinimalRevisionEngine", "minimal_revision_engine"]
