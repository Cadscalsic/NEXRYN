"""Detect and mitigate representative or perspective domination."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from runtime.world_governance.deliberation_engine import RepresentativeOpinion
from runtime.world_governance.representative_registry import CognitiveRepresentative


class RepresentationBalancer:
    def evaluate(
        self,
        opinions: list[RepresentativeOpinion],
        representatives: list[CognitiveRepresentative],
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = dict(runtime_context or {})
        domain_counts = Counter(
            representative.domain
            for representative in representatives
            if representative.voting_enabled
        )
        recommendation_counts = Counter(opinion.recommendation for opinion in opinions)
        total = max(1, len(opinions))
        dominant_recommendation_share = (
            recommendation_counts.most_common(1)[0][1] / total
            if recommendation_counts
            else 0.0
        )
        dominant_domain_share = (
            domain_counts.most_common(1)[0][1] / max(1, len(representatives))
            if domain_counts
            else 0.0
        )
        repeated = set(context.get("dominant_representatives", []) or [])

        risks: list[str] = []
        if self._number(context.get("dominant_strategy_share")) >= 0.65:
            risks.append("strategy_domination")
        if self._number(context.get("dominant_concept_share")) >= 0.65:
            risks.append("concept_monopoly")
        if dominant_recommendation_share >= 0.80:
            risks.append("single_perspective_reasoning")
        if repeated:
            risks.append("repeated_representative_dominance")

        penalties: dict[str, float] = {}
        for representative in representatives:
            penalty = 0.0
            if representative.name in repeated:
                penalty += 0.20
            if dominant_domain_share >= 0.35 and domain_counts[representative.domain] > 1:
                penalty += 0.05
            if "strategy_domination" in risks and representative.domain == "strategy":
                penalty += 0.20
            penalties[representative.name] = min(0.60, penalty)

        diversity_score = min(
            1.0,
            max(0.0, 1.0 - dominant_recommendation_share * 0.25 - dominant_domain_share * 0.20 - len(risks) * 0.05),
        )
        return {
            "diversity_score": diversity_score,
            "domination_risks": risks,
            "balancing_penalties": penalties,
            "dominant_recommendation_share": dominant_recommendation_share,
        }

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


representation_balancer = RepresentationBalancer()


__all__ = [
    "RepresentationBalancer",
    "representation_balancer",
]
