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
        self.executive_reports: list[dict[str, Any]] = []
        self.policy_reports: list[dict[str, Any]] = []
        self.decision_intelligence_reports: list[dict[str, Any]] = []
        self.intelligence_analytics_reports: list[dict[str, Any]] = []
        self.situation_reports: list[dict[str, Any]] = []

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

    def record_executive_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(report)
        self.executive_reports.append(payload)
        if payload.get("COGNITIVE_DECISION_INTELLIGENCE_REPORT"):
            self.decision_intelligence_reports.append({
                "COGNITIVE_DECISION_INTELLIGENCE_REPORT":
                payload["COGNITIVE_DECISION_INTELLIGENCE_REPORT"],
            })
        if payload.get("COGNITIVE_POLICY_REPORT"):
            self.policy_reports.append({
                "COGNITIVE_POLICY_REPORT": payload["COGNITIVE_POLICY_REPORT"],
            })
        if payload.get("COGNITIVE_SITUATION_REPORT"):
            self.situation_reports.append({
                "COGNITIVE_SITUATION_REPORT": payload["COGNITIVE_SITUATION_REPORT"],
            })
        return payload

    def record_policy_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(report)
        self.policy_reports.append(payload)
        policy_report = payload.get("COGNITIVE_POLICY_REPORT", {})
        decision_report = policy_report.get(
            "Cognitive Decision Intelligence Report",
            {},
        )
        if decision_report:
            self.decision_intelligence_reports.append({
                "COGNITIVE_DECISION_INTELLIGENCE_REPORT": decision_report,
            })
        return payload

    def record_decision_intelligence_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(report)
        self.decision_intelligence_reports.append(payload)
        return payload

    def record_intelligence_analytics_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(report)
        self.intelligence_analytics_reports.append(payload)
        return payload

    def record_situation_report(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        payload = dict(report)
        self.situation_reports.append(payload)
        return payload

    def build_report(self) -> dict[str, Any]:
        from runtime.governance.world_governance_introspection import (
            world_governance_introspection,
        )

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
        latest_executive = (
            self.executive_reports[-1]
            if self.executive_reports
            else {}
        )
        latest_policy = (
            self.policy_reports[-1]
            if self.policy_reports
            else {}
        )
        latest_decision_intelligence = (
            self.decision_intelligence_reports[-1]
            if self.decision_intelligence_reports
            else {}
        )
        latest_intelligence_analytics = (
            self.intelligence_analytics_reports[-1]
            if self.intelligence_analytics_reports
            else {}
        )
        latest_situation = (
            self.situation_reports[-1]
            if self.situation_reports
            else {}
        )
        world_report = {
            field: latest.get(field)
            for field in WORLD_GOVERNANCE_REPORT_FIELDS
        }
        return {
            "WORLD_GOVERNANCE_REPORT": world_report,
            "WORLD GOVERNANCE INTROSPECTION REPORT":
            world_governance_introspection.build_report().get(
                "WORLD GOVERNANCE INTROSPECTION REPORT",
                {},
            ),
            "GOVERNANCE DECISION MEMORY":
            world_governance_introspection.build_report().get(
                "GOVERNANCE DECISION MEMORY",
                {},
            ),
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
            "WORLD_GOVERNANCE_EXECUTIVE_REPORT": latest_executive.get(
                "WORLD_GOVERNANCE_EXECUTIVE_REPORT",
                {},
            ),
            "COGNITIVE_POLICY_REPORT": latest_policy.get(
                "COGNITIVE_POLICY_REPORT",
                {},
            ),
            "COGNITIVE_DECISION_INTELLIGENCE_REPORT":
            latest_decision_intelligence.get(
                "COGNITIVE_DECISION_INTELLIGENCE_REPORT",
                {},
            ),
            "COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT":
            latest_intelligence_analytics.get(
                "COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT",
                {},
            ),
            "COGNITIVE_SITUATION_REPORT": latest_situation.get(
                "COGNITIVE_SITUATION_REPORT",
                {},
            ),
            "world_governance_decisions": list(self.decisions[-200:]),
            "potential_worlds_reports": list(self.potential_worlds_reports[-100:]),
            "cognitive_evolution_reports": list(self.cognitive_evolution_reports[-100:]),
            "cognitive_parliament_reports": list(self.cognitive_parliament_reports[-100:]),
            "autonomous_direction_reports": list(self.autonomous_direction_reports[-100:]),
            "constitutional_incentive_reports": list(self.constitutional_incentive_reports[-100:]),
            "executive_reports": list(self.executive_reports[-100:]),
            "policy_reports": list(self.policy_reports[-100:]),
            "decision_intelligence_reports":
            list(self.decision_intelligence_reports[-100:]),
            "intelligence_analytics_reports":
            list(self.intelligence_analytics_reports[-100:]),
            "situation_reports": list(self.situation_reports[-100:]),
        }

    def reset(self) -> None:
        self.decisions.clear()
        self.potential_worlds_reports.clear()
        self.cognitive_evolution_reports.clear()
        self.cognitive_parliament_reports.clear()
        self.autonomous_direction_reports.clear()
        self.constitutional_incentive_reports.clear()
        self.executive_reports.clear()
        self.policy_reports.clear()
        self.decision_intelligence_reports.clear()
        self.intelligence_analytics_reports.clear()
        self.situation_reports.clear()


world_governance_reporter = WorldGovernanceReporter()


__all__ = [
    "WORLD_GOVERNANCE_REPORT_FIELDS",
    "WorldGovernanceReporter",
    "world_governance_reporter",
]
