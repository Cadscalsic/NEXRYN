"""Weighted voting policy for cognitive parliament deliberation."""

from __future__ import annotations

from typing import Mapping

from runtime.world_governance.deliberation_engine import RepresentativeOpinion
from runtime.world_governance.representative_registry import CognitiveRepresentative


RECOMMENDATION_VALUES: dict[str, float] = {
    "SUPPORT": 1.0,
    "SUPPORT_WITH_LIMITS": 0.65,
    "REQUEST_MORE_EVIDENCE": 0.25,
    "QUARANTINE": -0.45,
    "REJECT": -1.0,
}


class VotingPolicy:
    def vote_score(
        self,
        representative: CognitiveRepresentative,
        domain_relevance: float,
        balancing_penalty: float = 0.0,
    ) -> float:
        score = (
            representative.authority_weight * 0.30
            + representative.trust_score * 0.30
            + domain_relevance * 0.25
            + representative.diversity_weight * 0.15
        )
        return min(1.0, max(0.0, score * (1.0 - balancing_penalty)))

    def aggregate(
        self,
        opinions: list[RepresentativeOpinion],
        representatives: Mapping[str, CognitiveRepresentative],
        domain_relevance: Mapping[str, float],
        balancing_penalties: Mapping[str, float] | None = None,
    ) -> dict:
        penalties = dict(balancing_penalties or {})
        total_weight = 0.0
        weighted_sum = 0.0
        support_count = 0
        reject_count = 0
        weighted_by_representative: dict[str, float] = {}

        for opinion in opinions:
            representative = representatives[opinion.representative]
            weight = self.vote_score(
                representative,
                domain_relevance.get(opinion.representative, 0.35),
                penalties.get(opinion.representative, 0.0),
            )
            value = RECOMMENDATION_VALUES.get(opinion.recommendation, 0.0)
            total_weight += weight
            weighted_sum += weight * value * opinion.confidence
            weighted_by_representative[opinion.representative] = weight
            if opinion.recommendation in {"SUPPORT", "SUPPORT_WITH_LIMITS"}:
                support_count += 1
            if opinion.recommendation in {"REJECT", "QUARANTINE"}:
                reject_count += 1

        consensus_score = 0.0
        if total_weight > 0.0:
            consensus_score = (weighted_sum / total_weight + 1.0) / 2.0

        return {
            "consensus_score": min(1.0, max(0.0, consensus_score)),
            "support_count": support_count,
            "reject_count": reject_count,
            "total_weight": total_weight,
            "representative_weights": weighted_by_representative,
        }


voting_policy = VotingPolicy()


__all__ = [
    "RECOMMENDATION_VALUES",
    "VotingPolicy",
    "voting_policy",
]
