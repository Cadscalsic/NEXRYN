"""Structured falsification review for counterfactual evidence."""

from __future__ import annotations

from typing import Mapping


class FalsificationEngine:
    system_name = "falsification_engine"

    def review(self, comparison_report: Mapping, committed_truth: bool = False) -> dict:
        rows = comparison_report.get("counterfactual_comparisons", []) or []
        falsifying = [row for row in rows if row.get("evidence_class") == "SUPPORTS_ALTERNATIVE" and row.get("significance", 0) >= 0.1]
        supporting = [row for row in rows if row.get("evidence_class") == "SUPPORTS_ORIGINAL"]
        inconclusive = [row for row in rows if row.get("evidence_class") == "INCONCLUSIVE"]
        strength = round(sum(row.get("significance", 0.0) for row in falsifying), 4)
        if not rows:
            state = "NOT_CHALLENGED"
        elif strength >= 0.75:
            state = "STRONGLY_FALSIFIED"
        elif strength >= 0.30:
            state = "PARTIALLY_FALSIFIED"
        elif falsifying:
            state = "WEAKLY_CHALLENGED"
        elif inconclusive and not supporting:
            state = "INCONCLUSIVE"
        else:
            state = "NOT_CHALLENGED"
        return {
            "system": self.system_name,
            "falsification_state": state,
            "falsification_strength": min(strength, 1.0),
            "falsifying_counterfactuals": falsifying,
            "supporting_counterfactuals": supporting,
            "inconclusive_counterfactuals": inconclusive,
            "truth_review_required": bool(committed_truth and state in {"STRONGLY_FALSIFIED", "FULLY_FALSIFIED"}),
            "truth_revocation_performed": False,
            "hypothesis_revision_required": state in {"WEAKLY_CHALLENGED", "PARTIALLY_FALSIFIED", "STRONGLY_FALSIFIED"},
        }


falsification_engine = FalsificationEngine()

__all__ = ["FalsificationEngine", "falsification_engine"]
