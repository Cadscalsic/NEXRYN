"""Potential Worlds Engine for cognitive possibility evaluation."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.world_governance.admission_policy import admission_policy
from runtime.world_governance.constitutional_identity import protect_core
from runtime.world_governance.evolution_path_ranker import evolution_path_ranker
from runtime.world_governance.possibility_space import possibility_space
from runtime.world_governance.world_governance_reporter import (
    world_governance_reporter,
)
from runtime.world_governance.world_kernel import world_governance_kernel
from runtime.world_governance.world_simulator import CandidateWorld, world_simulator


class PotentialWorldsEngine:
    def __init__(
        self,
        kernel=world_governance_kernel,
    ):
        self.kernel = kernel
        self.possibility_space = possibility_space
        self.world_simulator = world_simulator
        self.path_ranker = evolution_path_ranker

    def evaluate(
        self,
        candidate: Mapping[str, Any] | Any,
        runtime_budget: Mapping[str, Any] | int | None = None,
    ) -> dict[str, Any]:
        data = self._data(candidate)
        candidate_name = self._candidate_name(data)
        candidate_type = str(data.get("candidate_type") or "concept")

        core_protection = protect_core(data)
        kernel_decision = self.kernel.evaluate_evolution_permission(data)
        admission_decision = admission_policy.evaluate_candidate(data, candidate_type)

        if core_protection["protected_core_touched"]:
            worlds = [
                CandidateWorld(
                    world_id=f"{candidate_name}::protected_core_block",
                    candidate_name=candidate_name,
                    candidate_type=candidate_type,
                    proposed_admission_level="OUTSIDE_WORLD",
                    expected_accuracy_gain=0.0,
                    expected_efficiency_gain=0.0,
                    expected_generalization_gain=0.0,
                    conceptual_diversity_gain=0.0,
                    identity_risk=1.0,
                    truth_risk=1.0,
                    governance_risk=1.0,
                    resource_cost=0.0,
                    recommendation="REJECT",
                )
            ]
            ranked_worlds = worlds
            reason = "protected_core_touched_worlds_rejected"
        else:
            futures = self.possibility_space.generate(data, runtime_budget)
            worlds = [
                self.world_simulator.simulate(data, future)
                for future in futures
            ]
            ranked_worlds = self.path_ranker.rank(worlds)
            reason = self._reason(
                ranked_worlds[0] if ranked_worlds else None,
                kernel_decision,
                admission_decision,
            )

        best_world = ranked_worlds[0] if ranked_worlds else None
        report = self._build_report(
            candidate_name,
            candidate_type,
            ranked_worlds,
            best_world,
            reason,
            kernel_decision,
            admission_decision,
        )
        world_governance_reporter.record_potential_worlds_report(report)
        return report

    def _build_report(
        self,
        candidate_name: str,
        candidate_type: str,
        ranked_worlds: list[CandidateWorld],
        best_world: CandidateWorld | None,
        reason: str,
        kernel_decision,
        admission_decision,
    ) -> dict[str, Any]:
        if best_world is None:
            potential_report = {
                "candidate_name": candidate_name,
                "candidate_type": candidate_type,
                "worlds_evaluated": 0,
                "best_world": None,
                "world_score": None,
                "recommendation": "REQUIRE_MORE_EVIDENCE",
                "identity_risk": None,
                "truth_risk": None,
                "governance_risk": None,
                "resource_cost": None,
                "reason": "no_candidate_worlds_generated",
            }
        else:
            recommendation = self._bounded_recommendation(
                best_world,
                kernel_decision,
                admission_decision,
            )
            potential_report = {
                "candidate_name": candidate_name,
                "candidate_type": candidate_type,
                "worlds_evaluated": len(ranked_worlds),
                "best_world": best_world.world_id,
                "world_score": best_world.world_score,
                "recommendation": recommendation,
                "identity_risk": best_world.identity_risk,
                "truth_risk": best_world.truth_risk,
                "governance_risk": best_world.governance_risk,
                "resource_cost": best_world.resource_cost,
                "reason": reason,
            }

        return {
            "POTENTIAL_WORLDS_REPORT": potential_report,
            "candidate_worlds": [
                world.as_dict()
                for world in ranked_worlds
            ],
            "kernel_decision": (
                kernel_decision.as_dict()
                if hasattr(kernel_decision, "as_dict")
                else dict(kernel_decision)
            ),
            "admission_decision": (
                admission_decision.as_dict()
                if hasattr(admission_decision, "as_dict")
                else dict(admission_decision)
            ),
        }

    def _bounded_recommendation(
        self,
        best_world: CandidateWorld,
        kernel_decision,
        admission_decision,
    ) -> str:
        if getattr(kernel_decision, "decision", None) in {"PROTECT_CORE", "REJECT"}:
            return "REJECT"
        if getattr(kernel_decision, "decision", None) == "QUARANTINE":
            return "QUARANTINE"
        if getattr(admission_decision, "allowed", False) is False:
            if best_world.recommendation == "ADOPT":
                return "ADOPT_WITH_LIMITS"
            return best_world.recommendation
        return best_world.recommendation

    def _reason(
        self,
        best_world: CandidateWorld | None,
        kernel_decision,
        admission_decision,
    ) -> str:
        if best_world is None:
            return "no_candidate_worlds_generated"
        if best_world.recommendation in {"REJECT", "QUARANTINE"}:
            return "best_world_blocked_by_cognitive_risk"
        if getattr(kernel_decision, "requires_review", False):
            return "best_world_informs_kernel_review_without_override"
        if getattr(admission_decision, "allowed", False) is False:
            return "best_world_requires_more_evidence_before_admission"
        return "best_world_balances_gain_risk_and_cost"

    def _candidate_name(self, data: Mapping[str, Any]) -> str:
        return str(data.get("candidate_name") or data.get("name") or "unnamed_candidate")

    def _data(self, value: Mapping[str, Any] | Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        data = {}
        for key in dir(value):
            if key.startswith("_"):
                continue
            item = getattr(value, key)
            if not callable(item):
                data[key] = item
        return data


potential_worlds_engine = PotentialWorldsEngine()


__all__ = [
    "PotentialWorldsEngine",
    "potential_worlds_engine",
]
