"""Counterfactual prioritization with configurable weights."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_WEIGHTS = {
    "information_gain": 0.22,
    "residual_alignment": 0.18,
    "uncertainty_reduction": 0.16,
    "falsification_value": 0.14,
    "semantic_relevance": 0.10,
    "localization_relevance": 0.08,
    "candidate_similarity_value": 0.05,
    "novelty": 0.04,
    "execution_cost": -0.02,
    "governance_risk": -0.01,
}


class CounterfactualPrioritizer:
    system_name = "counterfactual_prioritizer"

    def __init__(self, weights: Mapping[str, float] | None = None):
        self.weights = dict(weights or DEFAULT_WEIGHTS)

    def prioritize(self, counterfactuals: list[Mapping[str, Any]], budget: Mapping[str, Any]) -> dict[str, Any]:
        max_count = int(budget.get("max_counterfactuals", 4) or 4)
        scored = []
        rejected = []
        for cf in counterfactuals:
            if cf.get("governance_state") == "BLOCK_COUNTERFACTUAL":
                rejected.append(dict(cf))
                continue
            row = dict(cf)
            row["priority_score"] = self._score(row)
            scored.append(row)
        scored.sort(key=lambda item: item["priority_score"], reverse=True)
        return {
            "system": self.system_name,
            "prioritized_counterfactuals": scored,
            "selected_for_simulation": scored[:max_count],
            "deferred_counterfactuals": scored[max_count:],
            "rejected_counterfactuals": rejected,
            "budget_used": len(scored[:max_count]),
        }

    def _score(self, cf):
        values = {
            "information_gain": _score(cf.get("expected_information_gain")),
            "residual_alignment": 1.0 if cf.get("change_type") == "residual_guided_mutation" else 0.5,
            "uncertainty_reduction": _score(cf.get("generation_confidence")),
            "falsification_value": 0.8 if cf.get("change_type") in {"operation_substitution", "hypothesis_negation"} else 0.6,
            "semantic_relevance": 0.7,
            "localization_relevance": 0.8 if "region" in str(cf.get("change_type")) or "residual" in str(cf.get("change_type")) else 0.4,
            "candidate_similarity_value": 0.7 if cf.get("source_hypothesis_id") else 0.4,
            "novelty": 0.5,
            "execution_cost": len(cf.get("counterfactual_program", {}).get("steps", []) or []) / 5,
            "governance_risk": 0.0,
        }
        return round(sum(values[key] * self.weights[key] for key in self.weights), 4)


def _score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


counterfactual_prioritizer = CounterfactualPrioritizer()

__all__ = ["CounterfactualPrioritizer", "counterfactual_prioritizer"]
