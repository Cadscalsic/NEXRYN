"""Generate representative opinions for major cognitive proposals."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from runtime.world_governance.representative_registry import (
    CognitiveRepresentative,
)


OPINION_RECOMMENDATIONS: tuple[str, ...] = (
    "SUPPORT",
    "SUPPORT_WITH_LIMITS",
    "REQUEST_MORE_EVIDENCE",
    "QUARANTINE",
    "REJECT",
)


@dataclass
class RepresentativeOpinion:
    representative: str
    recommendation: str
    confidence: float
    expected_benefit: float
    estimated_risk: float
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class DeliberationEngine:
    def collect_opinions(
        self,
        proposal: Mapping[str, Any],
        representatives: list[CognitiveRepresentative],
        runtime_context: Mapping[str, Any] | None = None,
    ) -> list[RepresentativeOpinion]:
        context = dict(runtime_context or {})
        return [
            self._opinion_for(proposal, representative, context)
            for representative in representatives
        ]

    def _opinion_for(
        self,
        proposal: Mapping[str, Any],
        representative: CognitiveRepresentative,
        context: Mapping[str, Any],
    ) -> RepresentativeOpinion:
        benefit = self._benefit(proposal, representative)
        risk = self._risk(proposal, representative, context)
        relevance = self.domain_relevance(representative, proposal)

        if risk >= 0.82:
            recommendation = "REJECT"
        elif risk >= 0.68:
            recommendation = "QUARANTINE"
        elif benefit < 0.20 or relevance < 0.20:
            recommendation = "REQUEST_MORE_EVIDENCE"
        elif risk >= 0.42:
            recommendation = "SUPPORT_WITH_LIMITS"
        else:
            recommendation = "SUPPORT"

        confidence = min(
            1.0,
            max(0.0, representative.trust_score * 0.55 + relevance * 0.30 + abs(benefit - risk) * 0.15),
        )
        return RepresentativeOpinion(
            representative.name,
            recommendation,
            confidence,
            benefit,
            risk,
            self._explanation(representative, recommendation, benefit, risk),
        )

    def domain_relevance(
        self,
        representative: CognitiveRepresentative,
        proposal: Mapping[str, Any],
    ) -> float:
        proposal_type = str(proposal.get("proposal_type") or proposal.get("candidate_type") or "")
        target_type = str(proposal.get("target_type") or proposal.get("candidate_type") or "")
        domain = representative.domain
        if domain in {proposal_type, target_type}:
            return 1.0
        related = {
            "truth": {"new_concept_admission", "concept_freezing", "concept_deprecation", "context_promotion"},
            "identity": {"identity_impacting_change", "high_risk_self_repair", "evolution_investment"},
            "security": {"high_risk_self_repair", "program_promotion", "strategy_promotion"},
            "strategy": {"strategy_promotion", "evolution_investment"},
            "program": {"program_promotion"},
            "context": {"context_promotion", "new_concept_admission"},
            "resource": {"resource_allocation", "evolution_investment"},
            "learning": {"evolution_investment", "new_concept_admission"},
            "self_repair": {"high_risk_self_repair"},
            "world_model": {"context_promotion", "program_promotion", "evolution_investment"},
            "meta": {"evolution_investment", "resource_allocation", "concept_deprecation"},
            "reasoning": {"new_concept_admission", "strategy_promotion", "program_promotion"},
        }
        if proposal_type in related.get(domain, set()):
            return 0.80
        return 0.35

    def _benefit(
        self,
        proposal: Mapping[str, Any],
        representative: CognitiveRepresentative,
    ) -> float:
        values = [
            proposal.get("expected_value"),
            proposal.get("world_score"),
            proposal.get("expected_accuracy_gain"),
            proposal.get("expected_generalization_gain"),
            proposal.get("evolution_value"),
        ]
        benefit = max(self._number(value) for value in values)
        relevance = self.domain_relevance(representative, proposal)
        return min(1.0, max(0.0, benefit * (0.70 + relevance * 0.30)))

    def _risk(
        self,
        proposal: Mapping[str, Any],
        representative: CognitiveRepresentative,
        context: Mapping[str, Any],
    ) -> float:
        base = max(
            self._number(proposal.get("identity_risk")),
            self._number(proposal.get("truth_risk")),
            self._number(proposal.get("governance_risk")),
            self._number(proposal.get("security_risk")),
            self._number(proposal.get("reward_hacking_risk")),
            self._number(proposal.get("resource_cost")),
        )
        if representative.domain == "security":
            base = max(base, self._number(proposal.get("security_risk")))
        if representative.domain == "truth":
            base = max(base, self._number(proposal.get("truth_risk")))
        if representative.domain == "identity":
            base = max(base, self._number(proposal.get("identity_risk")))
        if representative.domain == "resource":
            base = max(base, self._number(proposal.get("resource_cost")))
        if context.get("recent_reward_hacking_signal") is True:
            base = max(base, 0.65)
        return min(1.0, max(0.0, base))

    def _explanation(
        self,
        representative: CognitiveRepresentative,
        recommendation: str,
        benefit: float,
        risk: float,
    ) -> str:
        return (
            f"{representative.name} recommends {recommendation} "
            f"because benefit={benefit:.2f} and risk={risk:.2f} in {representative.domain}."
        )

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


deliberation_engine = DeliberationEngine()


__all__ = [
    "OPINION_RECOMMENDATIONS",
    "DeliberationEngine",
    "RepresentativeOpinion",
    "deliberation_engine",
]
