"""NEXRYN inner world governance kernel."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.world_governance.admission_policy import admission_policy
from runtime.world_governance.constitutional_identity import (
    LOCKED_CORE_PRINCIPLE_NAMES,
)
from runtime.world_governance.evolution_policy import evolution_policy
from runtime.world_governance.executive_cognitive_governor import (
    ExecutiveCognitiveGovernor,
    executive_cognitive_governor,
)
from runtime.world_governance.cognitive_intelligence_analytics import (
    cognitive_intelligence_analytics,
)
from runtime.world_governance.cognitive_situation_awareness import (
    cognitive_situation_awareness_engine,
)
from runtime.world_governance.governance_decision import (
    WorldGovernanceDecision,
)
from runtime.world_governance.world_governance_reporter import (
    world_governance_reporter,
)
from runtime.world_governance.world_state import WorldState


class WorldKernel:
    def __init__(
        self,
        world_state: WorldState | None = None,
        executive_governor: ExecutiveCognitiveGovernor | None = None,
    ):
        self.world_state = world_state or WorldState()
        self.executive_governor = executive_governor or ExecutiveCognitiveGovernor()

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

    def build_execution_intent(
        self,
        task: Mapping[str, Any] | Any,
        context: Mapping[str, Any] | None = None,
    ):
        return self.executive_governor.build_execution_intent(task, context)

    def evaluate_cognitive_policy(
        self,
        task: Mapping[str, Any] | Any,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = self.executive_governor.policy_engine.select_policy(
            task,
            context,
        )
        world_governance_reporter.record_policy_report(report)
        return report

    def evaluate_cognitive_decision(
        self,
        task: Mapping[str, Any] | Any,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        task_profile = self.executive_governor.policy_engine.classify_task(
            task,
            context,
        )
        evaluations = self.executive_governor.policy_engine.evaluate_policies(
            task_profile,
        )
        report = (
            self.executive_governor.policy_engine
            .decision_intelligence_engine
            .reason_over_policy_evaluations(
                task_profile,
                evaluations,
                self.executive_governor.policy_engine.policy_statistics,
            )
        )
        world_governance_reporter.record_decision_intelligence_report(report)
        return report

    def record_policy_outcome(
        self,
        policy_id: str,
        outcome: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.executive_governor.policy_engine.record_policy_outcome(
            policy_id,
            outcome,
        )

    def record_decision_outcome(
        self,
        decision_report: Mapping[str, Any],
        actual_outcome: Mapping[str, Any],
    ) -> dict[str, Any]:
        return (
            self.executive_governor.policy_engine
            .decision_intelligence_engine
            .record_decision_outcome(
                decision_report,
                actual_outcome,
            )
        )

    def analyze_cognitive_intelligence(
        self,
        telemetry: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = cognitive_intelligence_analytics.analyze(telemetry or {})
        world_governance_reporter.record_intelligence_analytics_report(report)
        return report

    def construct_cognitive_situation(
        self,
        artifacts: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = cognitive_situation_awareness_engine.construct_situation(
            artifacts or {}
        )
        world_governance_reporter.record_situation_report(report)
        return report

    def construct_execution_graph(self, execution_intent):
        return self.executive_governor.construct_execution_graph(execution_intent)

    def allocate_runtime_budgets(self, execution_intent, execution_graph):
        return self.executive_governor.allocate_runtime_budgets(
            execution_intent,
            execution_graph,
        )

    def authorize_runtime_activation(
        self,
        execution_graph: Mapping[str, Any],
        runtime_budgets: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.executive_governor.decide_runtime_activation(
            execution_graph,
            runtime_budgets,
        )

    def govern_artifact_transition(
        self,
        artifact: Mapping[str, Any],
        target_state: str,
    ) -> dict[str, Any]:
        return self.executive_governor.supervise_artifact_transition(
            artifact,
            target_state,
        )

    def govern_truth_promotion(
        self,
        truth_candidate: Mapping[str, Any],
        target_state: str = "validated_truth",
    ) -> dict[str, Any]:
        return self.executive_governor.validate_truth_promotion(
            truth_candidate,
            target_state,
        )

    def govern_world_model_update(
        self,
        knowledge: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.executive_governor.govern_world_model_update(knowledge)

    def govern_dna_evolution(
        self,
        signal: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self.executive_governor.govern_dna_evolution(signal)

    def govern_cognitive_cycle(
        self,
        task: Mapping[str, Any] | Any,
        context: Mapping[str, Any] | None = None,
        runtime_events: list[Mapping[str, Any]] | None = None,
        execution_result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = self.executive_governor.govern_cognitive_cycle(
            task,
            context=context,
            runtime_events=runtime_events,
            execution_result=execution_result,
        )
        analytics_report = cognitive_intelligence_analytics.analyze(report)
        report["COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"] = analytics_report[
            "COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"
        ]
        situation_report = (
            cognitive_situation_awareness_engine.construct_situation(report)
        )
        report["COGNITIVE_SITUATION_REPORT"] = situation_report[
            "COGNITIVE_SITUATION_REPORT"
        ]
        world_governance_reporter.record_executive_report(report)
        world_governance_reporter.record_intelligence_analytics_report(
            analytics_report
        )
        world_governance_reporter.record_situation_report(situation_report)
        return report

    def build_report(self) -> dict[str, Any]:
        report = world_governance_reporter.build_report()
        executive_report = self.executive_governor.build_report()
        if executive_report["WORLD_GOVERNANCE_EXECUTIVE_REPORT"]:
            report["WORLD_GOVERNANCE_EXECUTIVE_REPORT"] = executive_report[
                "WORLD_GOVERNANCE_EXECUTIVE_REPORT"
            ]
        if executive_report["COGNITIVE_POLICY_REPORT"]:
            report["COGNITIVE_POLICY_REPORT"] = executive_report[
                "COGNITIVE_POLICY_REPORT"
            ]
        if executive_report["COGNITIVE_DECISION_INTELLIGENCE_REPORT"]:
            report["COGNITIVE_DECISION_INTELLIGENCE_REPORT"] = executive_report[
                "COGNITIVE_DECISION_INTELLIGENCE_REPORT"
            ]
        if executive_report["EXECUTIVE_COGNITIVE_REPORT"]:
            report["EXECUTIVE_COGNITIVE_REPORT"] = executive_report[
                "EXECUTIVE_COGNITIVE_REPORT"
            ]
        analytics_report = cognitive_intelligence_analytics.build_report()
        if analytics_report["COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"]:
            report["COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"] = analytics_report[
                "COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"
            ]
        situation_report = cognitive_situation_awareness_engine.build_report()
        if situation_report["COGNITIVE_SITUATION_REPORT"]:
            report["COGNITIVE_SITUATION_REPORT"] = situation_report[
                "COGNITIVE_SITUATION_REPORT"
            ]
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
world_governance_kernel.executive_governor = executive_cognitive_governor


__all__ = [
    "WorldKernel",
    "world_governance_kernel",
]
