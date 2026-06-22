"""Cognitive Parliament for multi-perspective deliberation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from runtime.world_governance.consensus_builder import consensus_builder
from runtime.world_governance.conflict_resolver import conflict_resolver
from runtime.world_governance.constitutional_identity import protect_core
from runtime.world_governance.deliberation_engine import deliberation_engine
from runtime.world_governance.representation_balancer import representation_balancer
from runtime.world_governance.representative_registry import representative_registry
from runtime.world_governance.voting_policy import voting_policy
from runtime.world_governance.world_governance_reporter import (
    world_governance_reporter,
)
from runtime.world_governance.world_kernel import world_governance_kernel


PARLIAMENT_TRIGGER_TYPES: frozenset[str] = frozenset({
    "new_concept_admission",
    "strategy_promotion",
    "program_promotion",
    "context_promotion",
    "resource_allocation",
    "evolution_investment",
    "concept_freezing",
    "concept_deprecation",
    "identity_impacting_change",
    "high_risk_self_repair",
})


@dataclass
class ParliamentProposal:
    proposal_name: str
    proposal_type: str
    candidate_type: str = "concept"
    expected_value: float = 0.0
    identity_risk: float = 0.0
    truth_risk: float = 0.0
    governance_risk: float = 0.0
    resource_cost: float = 0.0
    touches_constitutional_identity: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CognitiveParliament:
    def __init__(self, kernel=world_governance_kernel):
        self.kernel = kernel
        self.registry = representative_registry
        self.deliberation_engine = deliberation_engine
        self.representation_balancer = representation_balancer
        self.conflict_resolver = conflict_resolver
        self.consensus_builder = consensus_builder
        self.voting_policy = voting_policy

    def should_deliberate(self, proposal: Mapping[str, Any] | ParliamentProposal) -> bool:
        data = self._data(proposal)
        return str(data.get("proposal_type") or data.get("decision_type") or "") in PARLIAMENT_TRIGGER_TYPES

    def deliberate(
        self,
        proposal: Mapping[str, Any] | ParliamentProposal,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = self._data(proposal)
        context = dict(runtime_context or {})
        proposal_name = str(data.get("proposal_name") or data.get("candidate_name") or data.get("target") or "unnamed_proposal")
        proposal_type = str(data.get("proposal_type") or data.get("decision_type") or "routine_task")

        if not self.should_deliberate(data):
            report = self._skipped_report(proposal_name, proposal_type)
            world_governance_reporter.record_cognitive_parliament_report(report)
            return report

        constitutional = self._constitutional_status(data)
        representatives = self.registry.voting_representatives()
        opinions = self.deliberation_engine.collect_opinions(
            data,
            representatives,
            context,
        )
        representative_by_name = {
            representative.name: representative
            for representative in representatives
        }
        relevance = {
            representative.name: self.deliberation_engine.domain_relevance(
                representative,
                data,
            )
            for representative in representatives
        }
        balance = self.representation_balancer.evaluate(
            opinions,
            representatives,
            context,
        )
        vote_report = self.voting_policy.aggregate(
            opinions,
            representative_by_name,
            relevance,
            balance.get("balancing_penalties", {}),
        )
        conflicts = self.conflict_resolver.analyze(data, opinions)
        max_risk = max(
            [opinion.estimated_risk for opinion in opinions]
            + [
                self._number(data.get("identity_risk")),
                self._number(data.get("truth_risk")),
                self._number(data.get("governance_risk")),
            ]
        )
        consensus = self.consensus_builder.build(
            vote_report,
            balance,
            conflicts,
            constitutional["status"],
            max_risk,
        )

        kernel_decision = None
        final_decision = consensus["outcome"]
        decision_reason = consensus["reason"]
        if consensus["outcome"] != "CONSTITUTIONAL_BLOCK":
            kernel_decision = self.kernel.evaluate_evolution_permission(data)
            final_decision, decision_reason = self._finalize_with_kernel(
                consensus,
                kernel_decision,
            )

        report = {
            "COGNITIVE_PARLIAMENT_REPORT": {
                "proposal_name": proposal_name,
                "representatives_consulted": len(representatives),
                "support_count": vote_report["support_count"],
                "reject_count": vote_report["reject_count"],
                "diversity_score": balance["diversity_score"],
                "conflict_count": conflicts["conflict_count"],
                "consensus_score": vote_report["consensus_score"],
                "constitutional_status": constitutional["status"],
                "final_decision": final_decision,
                "decision_reason": decision_reason,
            },
            "proposal": dict(data),
            "representative_opinions": [opinion.as_dict() for opinion in opinions],
            "representation_balance": balance,
            "conflict_analysis": conflicts,
            "consensus": consensus,
            "kernel_decision": (
                kernel_decision.as_dict()
                if hasattr(kernel_decision, "as_dict")
                else kernel_decision
            ),
        }
        world_governance_reporter.record_cognitive_parliament_report(report)
        return report

    def _constitutional_status(self, proposal: Mapping[str, Any]) -> dict[str, Any]:
        if proposal.get("touches_constitutional_identity") is True:
            return {
                "status": "BLOCK",
                "reason": "proposal_declares_constitutional_identity_touch",
            }
        protection = protect_core(proposal)
        return {
            "status": "PASS" if protection["allowed"] else "BLOCK",
            "reason": protection["reason"],
            "protected_principles": protection.get("protected_principles", []),
        }

    def _finalize_with_kernel(
        self,
        consensus: Mapping[str, Any],
        kernel_decision,
    ) -> tuple[str, str]:
        kernel_name = getattr(kernel_decision, "decision", None)
        if kernel_name == "PROTECT_CORE":
            return "CONSTITUTIONAL_BLOCK", "world_kernel_protected_core"
        if kernel_name in {"REJECT", "QUARANTINE"}:
            return kernel_name, "world_kernel_rejected_or_quarantined_after_deliberation"
        if kernel_name == "REQUIRE_MORE_EVIDENCE":
            return "REQUIRE_MORE_EVIDENCE", "world_kernel_requires_more_evidence"
        return str(consensus["outcome"]), str(consensus["reason"])

    def _skipped_report(self, proposal_name: str, proposal_type: str) -> dict[str, Any]:
        return {
            "COGNITIVE_PARLIAMENT_REPORT": {
                "proposal_name": proposal_name,
                "representatives_consulted": 0,
                "support_count": 0,
                "reject_count": 0,
                "diversity_score": None,
                "conflict_count": 0,
                "consensus_score": None,
                "constitutional_status": "NOT_EVALUATED",
                "final_decision": "ROUTINE_TASK_NO_PARLIAMENT",
                "decision_reason": f"{proposal_type}_does_not_trigger_parliament",
            },
            "representative_opinions": [],
        }

    def _data(self, value: Mapping[str, Any] | ParliamentProposal) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        if hasattr(value, "as_dict"):
            return value.as_dict()
        return dict(getattr(value, "__dict__", {}))

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


cognitive_parliament = CognitiveParliament()


__all__ = [
    "PARLIAMENT_TRIGGER_TYPES",
    "CognitiveParliament",
    "ParliamentProposal",
    "cognitive_parliament",
]
