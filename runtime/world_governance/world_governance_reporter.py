"""Reporting for NEXRYN world governance decisions."""

from __future__ import annotations

from typing import Any


WORLD_GOVERNANCE_REPORT_FIELDS: tuple[str, ...] = (
    "candidate_name",
    "candidate_type",
    "decision",
    "admission_level",
    "evolution_value",
    "identity_risk",
    "truth_risk",
    "governance_risk",
    "protected_core_touched",
    "allowed_actions",
    "blocked_actions",
    "reason",
)


class WorldGovernanceReporter:
    def __init__(self):
        self.decisions: list[dict[str, Any]] = []
        self.potential_worlds_reports: list[dict[str, Any]] = []
        self.cognitive_evolution_reports: list[dict[str, Any]] = []
        self.cognitive_parliament_reports: list[dict[str, Any]] = []
        self.autonomous_direction_reports: list[dict[str, Any]] = []
        self.constitutional_incentive_reports: list[dict[str, Any]] = []

    def record_decision(
        self,
        decision,
        protected_core_touched: bool = False,
    ) -> dict[str, Any]:
        payload = (
            decision.as_dict()
            if hasattr(decision, "as_dict")
            else dict(decision)
        )
        payload["protected_core_touched"] = bool(protected_core_touched)
        self.decisions.append(payload)
        return payload

    def record_potential_worlds_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(report)
        self.potential_worlds_reports.append(payload)
        return payload

    def record_cognitive_evolution_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(report)
        self.cognitive_evolution_reports.append(payload)
        return payload

    def record_cognitive_parliament_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(report)
        self.cognitive_parliament_reports.append(payload)
        return payload

    def record_autonomous_direction_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(report)
        self.autonomous_direction_reports.append(payload)
        return payload

    def record_constitutional_incentive_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(report)
        self.constitutional_incentive_reports.append(payload)
        return payload

    def build_report(self) -> dict[str, Any]:
        latest = self.decisions[-1] if self.decisions else {}
        latest_potential = (
            self.potential_worlds_reports[-1]
            if self.potential_worlds_reports
            else {}
        )
        latest_evolution = (
            self.cognitive_evolution_reports[-1]
            if self.cognitive_evolution_reports
            else {}
        )
        latest_parliament = (
            self.cognitive_parliament_reports[-1]
            if self.cognitive_parliament_reports
            else {}
        )
        latest_direction = (
            self.autonomous_direction_reports[-1]
            if self.autonomous_direction_reports
            else {}
        )
        latest_incentive = (
            self.constitutional_incentive_reports[-1]
            if self.constitutional_incentive_reports
            else {}
        )
        world_report = {
            field: latest.get(field)
            for field in WORLD_GOVERNANCE_REPORT_FIELDS
        }
        return {
            "WORLD_GOVERNANCE_REPORT": world_report,
            "POTENTIAL_WORLDS_REPORT": latest_potential.get(
                "POTENTIAL_WORLDS_REPORT",
                {},
            ),
            "COGNITIVE_EVOLUTION_REPORT": latest_evolution.get(
                "COGNITIVE_EVOLUTION_REPORT",
                {},
            ),
            "COGNITIVE_PARLIAMENT_REPORT": latest_parliament.get(
                "COGNITIVE_PARLIAMENT_REPORT",
                {},
            ),
            "AUTONOMOUS_DIRECTION_REPORT": latest_direction.get(
                "AUTONOMOUS_DIRECTION_REPORT",
                {},
            ),
            "CONSTITUTIONAL_INCENTIVE_REPORT": latest_incentive.get(
                "CONSTITUTIONAL_INCENTIVE_REPORT",
                {},
            ),
            "COGNITIVE_ECONOMY_REPORT": latest_incentive.get(
                "COGNITIVE_ECONOMY_REPORT",
                {},
            ),
            "world_governance_decisions": list(self.decisions[-200:]),
            "potential_worlds_reports": list(self.potential_worlds_reports[-100:]),
            "cognitive_evolution_reports": list(self.cognitive_evolution_reports[-100:]),
            "cognitive_parliament_reports": list(self.cognitive_parliament_reports[-100:]),
            "autonomous_direction_reports": list(self.autonomous_direction_reports[-100:]),
            "constitutional_incentive_reports": list(self.constitutional_incentive_reports[-100:]),
        }

    def reset(self) -> None:
        self.decisions.clear()
        self.potential_worlds_reports.clear()
        self.cognitive_evolution_reports.clear()
        self.cognitive_parliament_reports.clear()
        self.autonomous_direction_reports.clear()
        self.constitutional_incentive_reports.clear()


world_governance_reporter = WorldGovernanceReporter()


__all__ = [
    "WORLD_GOVERNANCE_REPORT_FIELDS",
    "WorldGovernanceReporter",
    "world_governance_reporter",
]
