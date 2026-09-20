"""Build consensus outcomes from deliberative votes and constraints."""

from __future__ import annotations

from typing import Any, Mapping


CONSENSUS_OUTCOMES: tuple[str, ...] = (
    "CONSENSUS_REACHED",
    "CONSENSUS_WITH_LIMITS",
    "REQUIRE_MORE_EVIDENCE",
    "CONSTITUTIONAL_BLOCK",
    "ESCALATE_TO_WORLD_KERNEL",
)


class ConsensusBuilder:
    minimum_consensus_score = 0.62
    minimum_diversity_score = 0.45
    acceptable_risk_threshold = 0.60

    def build(
        self,
        vote_report: Mapping[str, Any],
        diversity_report: Mapping[str, Any],
        conflict_report: Mapping[str, Any],
        constitutional_status: str,
        max_risk: float,
    ) -> dict[str, Any]:
        if constitutional_status != "PASS":
            return {
                "outcome": "CONSTITUTIONAL_BLOCK",
                "consensus_score": vote_report.get("consensus_score", 0.0),
                "reason": "proposal_touches_constitutional_identity",
            }

        consensus_score = float(vote_report.get("consensus_score", 0.0))
        diversity_score = float(diversity_report.get("diversity_score", 0.0))
        conflict_count = int(conflict_report.get("conflict_count", 0))

        if max_risk > self.acceptable_risk_threshold:
            return {
                "outcome": "REQUIRE_MORE_EVIDENCE",
                "consensus_score": consensus_score,
                "reason": "estimated_risk_exceeds_consensus_threshold",
            }
        if diversity_score < self.minimum_diversity_score:
            return {
                "outcome": "REQUIRE_MORE_EVIDENCE",
                "consensus_score": consensus_score,
                "reason": "representation_diversity_below_threshold",
            }
        if consensus_score >= self.minimum_consensus_score and conflict_count == 0:
            return {
                "outcome": "CONSENSUS_REACHED",
                "consensus_score": consensus_score,
                "reason": "representatives_reached_safe_consensus",
            }
        if consensus_score >= self.minimum_consensus_score and conflict_count <= 2:
            return {
                "outcome": "CONSENSUS_WITH_LIMITS",
                "consensus_score": consensus_score,
                "reason": "consensus_requires_tradeoff_limits",
            }
        if consensus_score >= 0.50:
            return {
                "outcome": "ESCALATE_TO_WORLD_KERNEL",
                "consensus_score": consensus_score,
                "reason": "mixed_deliberation_requires_world_kernel_arbitration",
            }
        return {
            "outcome": "REQUIRE_MORE_EVIDENCE",
            "consensus_score": consensus_score,
            "reason": "insufficient_safe_consensus",
        }


consensus_builder = ConsensusBuilder()


__all__ = [
    "CONSENSUS_OUTCOMES",
    "ConsensusBuilder",
    "consensus_builder",
]
