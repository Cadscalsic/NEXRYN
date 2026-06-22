"""NEXRYN inner world governance kernel."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.world_governance.admission_policy import admission_policy
from runtime.world_governance.constitutional_identity import (
    LOCKED_CORE_PRINCIPLE_NAMES,
)
from runtime.world_governance.evolution_policy import evolution_policy
from runtime.world_governance.governance_decision import (
    WorldGovernanceDecision,
)
from runtime.world_governance.world_governance_reporter import (
    world_governance_reporter,
)
from runtime.world_governance.world_state import WorldState


class WorldKernel:
    def __init__(self, world_state: WorldState | None = None):
        self.world_state = world_state or WorldState()

    def evaluate_world_change(self, change_request):
        return self._evaluate(change_request, "change")

    def evaluate_concept_admission(self, concept):
        return self._evaluate(concept, "concept")

    def evaluate_strategy_admission(self, strategy):
        return self._evaluate(strategy, "strategy")

    def evaluate_identity_impact(self, candidate):
        return self._evaluate(candidate, "identity")

    def evaluate_evolution_permission(self, candidate):
        return self._evaluate(candidate, "evolution")

    def build_report(self) -> dict[str, Any]:
        report = world_governance_reporter.build_report()
        report["world_state"] = self.world_state.as_report()
        report["locked_core_principles"] = list(LOCKED_CORE_PRINCIPLE_NAMES)
        return report

    def _evaluate(
        self,
        candidate: Mapping[str, Any] | Any,
        candidate_type: str,
    ) -> WorldGovernanceDecision:
        data = self._data(candidate)
        admission = admission_policy.evaluate(data, candidate_type)
        protected_core_touched = admission_policy.touches_protected_core(data)

        if protected_core_touched:
            decision = WorldGovernanceDecision(
                admission.candidate_name,
                admission.candidate_type,
                "PROTECT_CORE",
                "OUTSIDE_WORLD",
                admission.reason,
                admission.evolution_value,
                admission.identity_risk,
                admission.truth_risk,
                admission.governance_risk,
                True,
                [],
                [
                    "modify_constitutional_principles",
                    "override_truth_governance",
                    "commit_world_change",
                ],
            )
            return self._record(decision, protected_core_touched)

        if not admission.allowed:
            decision_name = self._blocked_decision(admission.reason)
            evolution = evolution_policy.evaluate(data)
            decision = WorldGovernanceDecision(
                admission.candidate_name,
                admission.candidate_type,
                decision_name,
                admission.admission_level,
                admission.reason,
                evolution["evolution_value"],
                admission.identity_risk,
                admission.truth_risk,
                admission.governance_risk,
                True,
                ["observe_in_sandbox"] if decision_name == "REQUIRE_MORE_EVIDENCE" else [],
                self._blocked_actions(decision_name),
            )
            return self._record(decision, protected_core_touched)

        decision_name = (
            "ADMIT"
            if admission.admission_level in {"CANDIDATE", "OBSERVED_USEFUL"}
            else "ADMIT_WITH_LIMITS"
        )
        requires_review = admission.admission_level in {
            "WORLD_CITIZEN",
            "IDENTITY_SUPPORTING_COMPONENT",
        }
        decision = WorldGovernanceDecision(
            admission.candidate_name,
            admission.candidate_type,
            decision_name,
            admission.admission_level,
            admission.reason,
            admission.evolution_value,
            admission.identity_risk,
            admission.truth_risk,
            admission.governance_risk,
            requires_review,
            self._allowed_actions(admission.admission_level),
            self._blocked_actions(decision_name, admission.admission_level),
        )
        return self._record(decision, protected_core_touched)

    def _record(
        self,
        decision: WorldGovernanceDecision,
        protected_core_touched: bool,
    ) -> WorldGovernanceDecision:
        self.world_state.record_decision(decision)
        world_governance_reporter.record_decision(
            decision,
            protected_core_touched,
        )
        return decision

    def _blocked_decision(self, reason: str) -> str:
        if reason == "locked_core_requires_strict_governance_and_manual_review":
            return "REQUIRE_MORE_EVIDENCE"
        if reason == "candidate_risk_exceeds_world_admission_threshold":
            return "QUARANTINE"
        if reason == "candidate_has_no_clear_evolution_value":
            return "REQUIRE_MORE_EVIDENCE"
        return "REJECT"

    def _allowed_actions(self, admission_level: str) -> list[str]:
        if admission_level == "CANDIDATE":
            return ["observe", "sandbox_trial"]
        if admission_level == "OBSERVED_USEFUL":
            return ["observe", "sandbox_trial", "limited_reuse"]
        if admission_level == "TRUSTED_TOOL":
            return ["observe", "sandbox_trial", "limited_reuse", "tool_reuse"]
        if admission_level == "WORLD_CITIZEN":
            return ["observe", "sandbox_trial", "limited_reuse", "governed_reuse"]
        if admission_level == "IDENTITY_SUPPORTING_COMPONENT":
            return ["observe", "sandbox_trial", "governance_review"]
        return ["observe"]

    def _blocked_actions(
        self,
        decision_name: str,
        admission_level: str | None = None,
    ) -> list[str]:
        blocked = [
            "bypass_truth_governance",
            "lower_validation_thresholds",
            "alter_identity",
            "modify_locked_core",
        ]
        if decision_name != "ADMIT":
            blocked.append("commit_without_review")
        if admission_level != "LOCKED_CORE":
            blocked.append("locked_core_promotion")
        return blocked

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


world_governance_kernel = WorldKernel()


__all__ = [
    "WorldKernel",
    "world_governance_kernel",
]
