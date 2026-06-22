"""Reporting and orchestration for constitutional incentives."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.world_governance.incentives.accountability_manager import (
    accountability_manager,
)
from runtime.world_governance.incentives.cognitive_budget_controller import (
    cognitive_budget_controller,
)
from runtime.world_governance.incentives.constitutional_veto import (
    constitutional_veto,
)
from runtime.world_governance.incentives.incentive_engine import incentive_engine
from runtime.world_governance.incentives.influence_controller import (
    influence_controller,
)
from runtime.world_governance.incentives.performance_evaluator import (
    performance_evaluator,
)
from runtime.world_governance.incentives.reward_hacking_detector import (
    reward_hacking_detector,
)
from runtime.world_governance.incentives.trust_score_manager import (
    trust_score_manager,
)
from runtime.world_governance.incentives.voting_eligibility_manager import (
    voting_eligibility_manager,
)


class IncentiveReporter:
    def __init__(self):
        self.incentive_reports: list[dict[str, Any]] = []
        self.economy_reports: list[dict[str, Any]] = []

    def evaluate_subsystem(
        self,
        subsystem_name: str,
        metrics: Mapping[str, Any] | None = None,
        task_profile: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = dict(metrics or {})
        budget = cognitive_budget_controller.assign_budget(
            task_profile or data,
            data.get("available_resources"),
        )
        budget_report = cognitive_budget_controller.evaluate_usage(
            budget,
            data.get("budget_usage", data),
        )
        veto_report = constitutional_veto.evaluate(data)
        hacking_report = reward_hacking_detector.detect(subsystem_name, data)
        performance_report = performance_evaluator.evaluate({
            **data,
            "budget_compliance": budget_report["budget_compliance"],
            "average_budget_utilization": budget_report["average_budget_utilization"],
        })
        incentive_report = incentive_engine.evaluate(
            subsystem_name,
            data,
            hacking_report["reward_hacking_penalty"],
            budget_report["budget_compliance"],
        )
        trust_report = trust_score_manager.update(
            subsystem_name,
            {
                **data,
                **performance_report,
                "reward_hacking_detected": hacking_report["reward_hacking_detected"],
                "budget_compliance": budget_report["budget_compliance"],
            },
        )
        influence_report = influence_controller.update(
            subsystem_name,
            trust_report["trust_score"],
            {
                **data,
                "reward_hacking_detected": hacking_report["reward_hacking_detected"],
                "influence_reduction": hacking_report["influence_reduction"],
            },
        )
        eligibility = voting_eligibility_manager.evaluate(
            subsystem_name,
            {
                **data,
                "trust_score": trust_report["trust_score"],
                "performance_score": performance_report["performance_score"],
                "reward_hacking_detected": hacking_report["reward_hacking_detected"],
                "budget_compliance": budget_report["budget_compliance"],
            },
        )
        accountability = accountability_manager.evaluate(
            subsystem_name,
            budget_report,
            hacking_report,
            veto_report,
        )

        report = {
            "CONSTITUTIONAL_INCENTIVE_REPORT": {
                "subsystem_name": subsystem_name,
                "reward_score": incentive_report["reward_score"],
                "trust_score": trust_report["trust_score"],
                "influence_score": influence_report["influence_score"],
                "budget_usage": budget_report["usage"],
                "budget_compliance": budget_report["budget_compliance"],
                "voting_eligibility": eligibility.as_dict(),
                "suspension_level": eligibility.suspension_level,
                "reward_hacking_detected": hacking_report["reward_hacking_detected"],
                "constitutional_violations": veto_report["constitutional_violations"],
            },
            "budget_report": budget_report,
            "veto_report": veto_report,
            "reward_hacking_report": hacking_report,
            "performance_report": performance_report,
            "trust_report": trust_report,
            "influence_report": influence_report,
            "accountability_report": accountability,
        }
        economy = self.build_economy_report()
        report["COGNITIVE_ECONOMY_REPORT"] = economy["COGNITIVE_ECONOMY_REPORT"]
        self.incentive_reports.append(report)
        self.economy_reports.append(economy)
        try:
            from runtime.world_governance.world_governance_reporter import (
                world_governance_reporter,
            )

            world_governance_reporter.record_constitutional_incentive_report(report)
        except ImportError:
            pass
        return report

    def build_economy_report(self) -> dict[str, Any]:
        economy = performance_evaluator.economy_report()
        return {
            "COGNITIVE_ECONOMY_REPORT": {
                "cost_per_success": economy.get("cost_per_success", 0.0),
                "cost_per_strategy": economy.get("cost_per_strategy", 0.0),
                "reuse_rate": economy.get("reuse_rate", 0.0),
                "thinking_avoidance_rate": economy.get("thinking_avoidance_rate", 0.0),
                "average_reasoning_depth": economy.get("average_reasoning_depth", 0.0),
                "average_budget_utilization": economy.get("average_budget_utilization", 0.0),
                "governance_cost": economy.get("governance_cost", 0.0),
            }
        }

    def build_report(self) -> dict[str, Any]:
        latest = self.incentive_reports[-1] if self.incentive_reports else {}
        economy = self.build_economy_report()
        return {
            "CONSTITUTIONAL_INCENTIVE_REPORT": latest.get(
                "CONSTITUTIONAL_INCENTIVE_REPORT",
                {},
            ),
            "COGNITIVE_ECONOMY_REPORT": economy["COGNITIVE_ECONOMY_REPORT"],
            "constitutional_incentive_reports": list(self.incentive_reports[-100:]),
        }

    def reset(self) -> None:
        self.incentive_reports.clear()
        self.economy_reports.clear()


incentive_reporter = IncentiveReporter()


__all__ = [
    "IncentiveReporter",
    "incentive_reporter",
]
