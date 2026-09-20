"""Dynamic voting eligibility for cognitive representatives."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from runtime.world_governance.incentives.constitutional_veto import (
    constitutional_veto,
)


SUSPENSION_LEVELS: tuple[str, ...] = (
    "WARNING",
    "RESTRICTED",
    "PROBATION",
    "SUSPENDED",
    "QUARANTINED",
)


@dataclass
class VotingEligibility:
    can_vote: bool
    trust_score: float
    performance_score: float
    alignment_score: float
    suspension_level: str | None
    suspension_reason: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class VotingEligibilityManager:
    def evaluate(
        self,
        subsystem_name: str,
        metrics: Mapping[str, Any] | None = None,
    ) -> VotingEligibility:
        data = dict(metrics or {})
        veto = constitutional_veto.evaluate(data)
        trust = self._score(data.get("trust_score", 0.5))
        performance = self._score(data.get("performance_score", 0.5))
        alignment = self._score(data.get("alignment_score", data.get("identity_alignment", 0.5)))
        compliance = self._score(data.get("governance_compliance", 1.0))
        resource_efficiency = self._score(data.get("resource_efficiency", data.get("budget_efficiency", 0.5)))
        historical = self._score(data.get("historical_reliability", trust))
        reward_hacking = data.get("reward_hacking_detected") is True

        level = None
        reason = None
        can_vote = True
        if not veto["allowed"]:
            level = "QUARANTINED"
            reason = "constitutional_violation"
            can_vote = False
        elif reward_hacking and data.get("persistent_reward_hacking") is True:
            level = "SUSPENDED"
            reason = "persistent_reward_hacking"
            can_vote = False
        elif reward_hacking:
            level = "PROBATION"
            reason = "reward_hacking_detected"
        elif data.get("inflated_task_complexity") is True:
            level = "PROBATION"
            reason = "inflated_complexity_reporting"
        elif resource_efficiency < 0.30 or data.get("repeated_inefficient_reasoning") is True:
            level = "RESTRICTED"
            reason = "repeated_inefficient_reasoning"
        elif data.get("minor_budget_overrun") is True or data.get("budget_compliance") is False:
            level = "WARNING"
            reason = "budget_overrun"

        if min(trust, performance, alignment, compliance, historical) < 0.20:
            can_vote = False
            level = level or "SUSPENDED"
            reason = reason or "insufficient_reliability_alignment_or_compliance"

        return VotingEligibility(
            can_vote,
            trust,
            performance,
            alignment,
            level,
            reason,
        )

    def _score(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


voting_eligibility_manager = VotingEligibilityManager()


__all__ = [
    "SUSPENSION_LEVELS",
    "VotingEligibility",
    "VotingEligibilityManager",
    "voting_eligibility_manager",
]
