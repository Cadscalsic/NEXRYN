"""Accountability enforcement for cognitive economy behavior."""

from __future__ import annotations

from typing import Any, Mapping


class AccountabilityManager:
    def evaluate(
        self,
        subsystem_name: str,
        budget_report: Mapping[str, Any],
        hacking_report: Mapping[str, Any],
        veto_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        actions: list[str] = []
        if budget_report.get("budget_compliance") is False:
            actions.extend(["reduce_reward_score", "decrease_trust_score", "trigger_efficiency_review"])
        if hacking_report.get("reward_hacking_detected") is True:
            actions.extend(["apply_reward_hacking_penalty", "reduce_influence"])
        if veto_report.get("allowed") is False:
            actions.extend(["constitutional_quarantine", "remove_voting_eligibility"])
        return {
            "subsystem_name": subsystem_name,
            "accountability_actions": sorted(set(actions)),
            "requires_review": bool(actions),
        }


accountability_manager = AccountabilityManager()


__all__ = [
    "AccountabilityManager",
    "accountability_manager",
]
