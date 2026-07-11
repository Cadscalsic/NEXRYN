"""Cognitive Decision Intelligence for executive policy selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
from uuid import uuid4


@dataclass(frozen=True)
class CognitiveDecision:
    decision_id: str
    decision_version: str
    associated_policy: dict[str, Any]
    task_profile: dict[str, Any]
    applicability_score: float
    confidence: float
    expected_benefit: float
    expected_cost: float
    expected_search_depth: int
    expected_runtime_budget: dict[str, Any]
    expected_truth_yield: float
    expected_memory_yield: float
    expected_knowledge_gain: float
    expected_world_model_impact: float
    expected_dna_impact: float
    expected_risk: float
    expected_stability: float
    expected_learning_value: float
    fallback_strategy: str
    decision_explanation: str
    decision_trace: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "Decision ID": self.decision_id,
            "Decision Version": self.decision_version,
            "Associated Policy": dict(self.associated_policy),
            "Task Profile": dict(self.task_profile),
            "Applicability Score": round(self.applicability_score, 3),
            "Confidence": round(self.confidence, 3),
            "Expected Benefit": round(self.expected_benefit, 3),
            "Expected Cost": round(self.expected_cost, 3),
            "Expected Search Depth": self.expected_search_depth,
            "Expected Runtime Budget": dict(self.expected_runtime_budget),
            "Expected Truth Yield": round(self.expected_truth_yield, 3),
            "Expected Memory Yield": round(self.expected_memory_yield, 3),
            "Expected Knowledge Gain": round(self.expected_knowledge_gain, 3),
            "Expected World Model Impact": round(self.expected_world_model_impact, 3),
            "Expected DNA Impact": round(self.expected_dna_impact, 3),
            "Expected Risk": round(self.expected_risk, 3),
            "Expected Stability": round(self.expected_stability, 3),
            "Expected Learning Value": round(self.expected_learning_value, 3),
            "Fallback Strategy": self.fallback_strategy,
            "Decision Explanation": self.decision_explanation,
            "Decision Trace": dict(self.decision_trace),
        }


@dataclass
class DecisionStatistics:
    activation_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    average_utility: float = 0.0
    average_confidence: float = 0.0
    average_cost: float = 0.0
    average_risk: float = 0.0
    average_truth_yield: float = 0.0
    average_memory_yield: float = 0.0
    average_learning_value: float = 0.0
    prediction_accuracy: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        success_rate = (
            self.success_count / self.activation_count
            if self.activation_count
            else 0.0
        )
        failure_rate = (
            self.failure_count / self.activation_count
            if self.activation_count
            else 0.0
        )
        return {
            "activation_count": self.activation_count,
            "success_rate": round(success_rate, 3),
            "failure_rate": round(failure_rate, 3),
            "average_utility": round(self.average_utility, 3),
            "average_confidence": round(self.average_confidence, 3),
            "average_cost": round(self.average_cost, 3),
            "average_risk": round(self.average_risk, 3),
            "average_truth_yield": round(self.average_truth_yield, 3),
            "average_memory_yield": round(self.average_memory_yield, 3),
            "average_learning_value": round(self.average_learning_value, 3),
            "prediction_accuracy": round(self.prediction_accuracy, 3),
        }


class CognitiveDecisionIntelligenceEngine:
    """Executive reasoning layer that explains policy selection."""

    def __init__(self) -> None:
        self.decision_reports: list[dict[str, Any]] = []
        self.decision_statistics: dict[str, DecisionStatistics] = {}
        self.rejected_decision_memory: list[dict[str, Any]] = []

    def reason_over_policy_evaluations(
        self,
        task_profile: Any,
        policy_evaluations: list[Any],
        policy_statistics: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        profile = (
            task_profile.as_dict()
            if hasattr(task_profile, "as_dict")
            else dict(task_profile)
        )
        candidate_decisions = self.construct_decision_space(
            profile,
            policy_evaluations,
            policy_statistics or {},
        )
        simulations = [
            self.simulate_decision(decision)
            for decision in candidate_decisions
        ]
        comparisons = [
            self.evaluate_decision(decision, simulation)
            for decision, simulation in zip(candidate_decisions, simulations)
        ]
        ranked = sorted(
            comparisons,
            key=lambda item: item["Decision Utility"],
            reverse=True,
        )
        selected = ranked[0]
        rejected = ranked[1:]
        self.decision_statistics.setdefault(
            selected["Decision"]["Associated Policy"]["policy_id"],
            DecisionStatistics(),
        ).activation_count += 1
        rejected_records = [
            self._rejected_decision_record(item)
            for item in rejected
        ]
        self.rejected_decision_memory.extend(rejected_records)
        report = {
            "COGNITIVE_DECISION_INTELLIGENCE_REPORT": {
                "Task Profile": profile,
                "Decision Space": {
                    "decision_count": len(candidate_decisions),
                    "candidate_policy_ids": [
                        decision.associated_policy.get("policy_id")
                        for decision in candidate_decisions
                    ],
                },
                "Candidate Decisions": [
                    decision.as_dict()
                    for decision in candidate_decisions
                ],
                "Policy Ranking": [
                    {
                        "policy_id": item["Decision"]["Associated Policy"]["policy_id"],
                        "decision_id": item["Decision"]["Decision ID"],
                        "utility": round(item["Decision Utility"], 3),
                        "confidence": item["Decision Confidence"]["Decision Confidence"],
                    }
                    for item in ranked
                ],
                "Simulation Results": simulations,
                "Expected Outcomes": selected["Expected Outcomes"],
                "Risk Analysis": selected["Risk Analysis"],
                "Selected Decision": selected,
                "Decision Justification": self.justify_decision(selected, rejected),
                "Rejected Alternatives": rejected_records,
                "Decision Confidence": selected["Decision Confidence"],
                "Decision Cost": selected["Decision Cost"],
                "Prediction Accuracy": None,
                "Actual Outcomes": {},
                "Learning Updates": [],
                "Decision Evolution": self._decision_evolution(selected),
            }
        }
        self.decision_reports.append(report)
        return report

    def construct_decision_space(
        self,
        task_profile: Mapping[str, Any],
        policy_evaluations: list[Any],
        policy_statistics: Mapping[str, Any],
    ) -> list[CognitiveDecision]:
        decisions = []
        for evaluation in policy_evaluations:
            data = (
                evaluation.as_dict()
                if hasattr(evaluation, "as_dict")
                else dict(evaluation)
            )
            policy = dict(data["policy"])
            policy_id = policy["policy_id"]
            stats = policy_statistics.get(policy_id)
            stats_data = stats.as_dict() if hasattr(stats, "as_dict") else dict(stats or {})
            risk = self._risk_for_policy(policy, task_profile, data, stats_data)
            stability = self._stability_for_policy(data, stats_data, task_profile)
            explanation = self._decision_explanation(
                policy,
                data,
                risk,
                stability,
                stats_data,
            )
            decisions.append(
                CognitiveDecision(
                    decision_id=f"cdi_{uuid4().hex}",
                    decision_version="1.0",
                    associated_policy=policy,
                    task_profile=dict(task_profile),
                    applicability_score=float(data["applicability_score"]),
                    confidence=float(data["confidence"]),
                    expected_benefit=float(data["estimated_benefit"]),
                    expected_cost=float(data["estimated_cost"]),
                    expected_search_depth=int(data["expected_search_depth"]),
                    expected_runtime_budget=dict(policy.get("budget_allocation", {})),
                    expected_truth_yield=float(data["expected_truth_yield"]),
                    expected_memory_yield=(
                        0.75
                        if "memory_runtime" in policy.get("runtime_selection", [])
                        else 0.25
                    ),
                    expected_knowledge_gain=float(data["expected_evidence_growth"]),
                    expected_world_model_impact=self._world_model_impact(policy, risk),
                    expected_dna_impact=self._dna_impact(policy, stability),
                    expected_risk=risk,
                    expected_stability=stability,
                    expected_learning_value=float(data["expected_learning_value"]),
                    fallback_strategy=policy.get("fallback_strategy", "governance_review"),
                    decision_explanation=explanation,
                    decision_trace={
                        "inputs": dict(task_profile),
                        "observations": self._observations(task_profile),
                        "candidate_policy": policy_id,
                        "policy_statistics": stats_data,
                        "assumptions": [
                            "simulation_is_pre_execution_estimate",
                            "runtime_cost_is_policy_budget_proxy",
                            "truth_and_memory_yield_are_expected_values",
                        ],
                    },
                )
            )
        return decisions

    def simulate_decision(self, decision: CognitiveDecision) -> dict[str, Any]:
        success = self._clamp(
            decision.confidence * 0.45
            + decision.expected_benefit * 0.35
            + decision.expected_stability * 0.25
            - decision.expected_risk * 0.25
        )
        failure = self._clamp(1.0 - success)
        runtime_count = len(decision.associated_policy.get("runtime_selection", []))
        resource_usage = self._clamp(decision.expected_cost * 0.65 + runtime_count / 12.0)
        evidence_growth = self._clamp(decision.expected_knowledge_gain)
        truth_generation = self._clamp(decision.expected_truth_yield * success)
        memory_promotion = self._clamp(decision.expected_memory_yield * success)
        confidence = self._clamp(decision.confidence * 0.75 + success * 0.25)
        return {
            "decision_id": decision.decision_id,
            "policy_id": decision.associated_policy.get("policy_id"),
            "Expected Success": round(success, 3),
            "Expected Failure": round(failure, 3),
            "Expected Runtime Cost": round(decision.expected_cost, 3),
            "Expected Search Expansion": decision.expected_search_depth,
            "Expected Evidence Growth": round(evidence_growth, 3),
            "Expected Truth Generation": round(truth_generation, 3),
            "Expected Memory Promotion": round(memory_promotion, 3),
            "Expected Knowledge Integration": round(evidence_growth * success, 3),
            "Expected Confidence": round(confidence, 3),
            "Expected Resource Usage": round(resource_usage, 3),
        }

    def evaluate_decision(
        self,
        decision: CognitiveDecision,
        simulation: Mapping[str, Any],
    ) -> dict[str, Any]:
        expected_outcomes = self._expected_outcomes(decision, simulation)
        risk_analysis = self._risk_analysis(decision)
        confidence = self._decision_confidence(decision, simulation)
        cost = self._decision_cost(decision)
        utility = self._utility(decision, simulation, risk_analysis, confidence)
        return {
            "Decision": decision.as_dict(),
            "Simulation": dict(simulation),
            "Expected Outcomes": expected_outcomes,
            "Risk Analysis": risk_analysis,
            "Decision Confidence": confidence,
            "Decision Cost": cost,
            "Decision Utility": round(utility, 4),
            "Decision Trace": decision.decision_trace,
        }

    def justify_decision(
        self,
        selected: Mapping[str, Any],
        rejected: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        decision = selected["Decision"]
        policy = decision["Associated Policy"]
        top_rejected = rejected[0] if rejected else None
        margin = selected["Decision Utility"] - (
            top_rejected["Decision Utility"]
            if top_rejected
            else 0.0
        )
        return {
            "why_selected": decision["Decision Explanation"],
            "policy_selected": policy["policy_id"],
            "observations_influenced": decision["Decision Trace"].get("observations", []),
            "supporting_evidence": [
                "highest_decision_utility",
                "pre_execution_simulation_completed",
                "risk_analysis_completed",
            ],
            "assumptions": decision["Decision Trace"].get("assumptions", []),
            "confidence_support": selected["Decision Confidence"],
            "risks_remaining": [
                key
                for key, value in selected["Risk Analysis"].items()
                if key.endswith("Risk") and value >= 0.5
            ],
            "rejection_summary": [
                {
                    "policy_id": item["Decision"]["Associated Policy"]["policy_id"],
                    "reason": "lower_decision_utility",
                    "utility_delta": round(
                        selected["Decision Utility"] - item["Decision Utility"],
                        3,
                    ),
                }
                for item in rejected
            ],
            "selection_margin": round(margin, 3),
        }

    def record_decision_outcome(
        self,
        decision_report: Mapping[str, Any],
        actual_outcome: Mapping[str, Any],
    ) -> dict[str, Any]:
        report = dict(decision_report)
        cdi_report = report.get("COGNITIVE_DECISION_INTELLIGENCE_REPORT", report)
        selected = cdi_report.get("Selected Decision", {})
        decision = selected.get("Decision", {})
        policy_id = decision.get("Associated Policy", {}).get("policy_id", "unknown_policy")
        stats = self.decision_statistics.setdefault(policy_id, DecisionStatistics())
        success = bool(actual_outcome.get("success", False))
        if success:
            stats.success_count += 1
        else:
            stats.failure_count += 1
        count = max(1, stats.success_count + stats.failure_count)
        stats.average_utility = self._running_average(
            stats.average_utility,
            float(selected.get("Decision Utility", 0.0)),
            count,
        )
        stats.average_confidence = self._running_average(
            stats.average_confidence,
            float(selected.get("Decision Confidence", {}).get("Decision Confidence", 0.0)),
            count,
        )
        stats.average_cost = self._running_average(
            stats.average_cost,
            float(selected.get("Decision Cost", {}).get("Decision Cost", 0.0)),
            count,
        )
        stats.average_risk = self._running_average(
            stats.average_risk,
            float(decision.get("Expected Risk", 0.0)),
            count,
        )
        stats.average_truth_yield = self._running_average(
            stats.average_truth_yield,
            float(actual_outcome.get("truth_yield", 0.0)),
            count,
        )
        stats.average_memory_yield = self._running_average(
            stats.average_memory_yield,
            float(actual_outcome.get("memory_yield", 0.0)),
            count,
        )
        stats.average_learning_value = self._running_average(
            stats.average_learning_value,
            float(actual_outcome.get("learning_value", 0.0)),
            count,
        )
        predicted_success = float(
            selected.get("Simulation", {}).get("Expected Success", 0.0)
        )
        actual_success = 1.0 if success else 0.0
        prediction_error = abs(predicted_success - actual_success)
        stats.prediction_accuracy = self._running_average(
            stats.prediction_accuracy,
            1.0 - prediction_error,
            count,
        )
        update = {
            "policy_id": policy_id,
            "decision_statistics": stats.as_dict(),
            "prediction_error": round(prediction_error, 3),
            "simulation_accuracy": round(1.0 - prediction_error, 3),
            "decision_quality": self._decision_quality(stats),
            "world_model_decision_knowledge": {
                "task_family": policy_id,
                "preferred_policy": policy_id if success else None,
                "avoid_policy": None if success else policy_id,
            },
            "dna_decision_traits": {
                "risk_preference": "conservative"
                if stats.average_risk >= 0.6
                else "balanced",
                "evidence_preference": "increase"
                if stats.average_truth_yield >= 0.5
                else "observe",
                "decision_stability": stats.as_dict()["prediction_accuracy"],
            },
        }
        cdi_report["Actual Outcomes"] = dict(actual_outcome)
        cdi_report["Prediction Accuracy"] = update["simulation_accuracy"]
        cdi_report.setdefault("Learning Updates", []).append(update)
        return update

    def build_report(self) -> dict[str, Any]:
        latest = self.decision_reports[-1] if self.decision_reports else {}
        return {
            "COGNITIVE_DECISION_INTELLIGENCE_REPORT": latest.get(
                "COGNITIVE_DECISION_INTELLIGENCE_REPORT",
                {},
            ),
            "decision_report_count": len(self.decision_reports),
            "decision_statistics": {
                policy_id: stats.as_dict()
                for policy_id, stats in self.decision_statistics.items()
            },
            "rejected_decision_memory": list(self.rejected_decision_memory[-100:]),
        }

    def reset(self) -> None:
        self.decision_reports.clear()
        self.rejected_decision_memory.clear()
        self.decision_statistics.clear()

    def _risk_for_policy(
        self,
        policy: Mapping[str, Any],
        task_profile: Mapping[str, Any],
        evaluation: Mapping[str, Any],
        stats: Mapping[str, Any],
    ) -> float:
        base = float(task_profile.get("risk", 0.0))
        cost_risk = float(evaluation.get("estimated_cost", 0.0)) * 0.25
        failure = float(stats.get("failure_rate", 0.0)) * 0.25
        truth_guard = -0.1 if "truth_runtime" in policy.get("runtime_selection", []) else 0.05
        return self._clamp(base * 0.55 + cost_risk + failure + truth_guard)

    def _stability_for_policy(
        self,
        evaluation: Mapping[str, Any],
        stats: Mapping[str, Any],
        task_profile: Mapping[str, Any],
    ) -> float:
        historical = float(stats.get("success_rate", 0.0))
        confidence = float(evaluation.get("confidence", 0.0))
        novelty_penalty = float(task_profile.get("novelty", 0.0)) * 0.2
        return self._clamp(confidence * 0.55 + historical * 0.3 + 0.25 - novelty_penalty)

    def _world_model_impact(
        self,
        policy: Mapping[str, Any],
        risk: float,
    ) -> float:
        if "truth_runtime" not in policy.get("runtime_selection", []):
            return 0.1
        return self._clamp(0.65 - risk * 0.25)

    def _dna_impact(
        self,
        policy: Mapping[str, Any],
        stability: float,
    ) -> float:
        if "update_policy_statistics" not in policy.get("learning_hooks", []):
            return 0.05
        return self._clamp(stability * 0.45)

    def _decision_explanation(
        self,
        policy: Mapping[str, Any],
        evaluation: Mapping[str, Any],
        risk: float,
        stability: float,
        stats: Mapping[str, Any],
    ) -> str:
        return (
            f"{policy['policy_id']} is viable because applicability is "
            f"{round(float(evaluation['applicability_score']), 3)}, expected benefit is "
            f"{round(float(evaluation['estimated_benefit']), 3)}, expected risk is "
            f"{round(risk, 3)}, and decision stability is {round(stability, 3)}. "
            f"Historical success is {stats.get('success_rate', 0.0)}."
        )

    def _observations(self, task_profile: Mapping[str, Any]) -> list[str]:
        observations = []
        if float(task_profile.get("novelty", 0.0)) >= 0.6:
            observations.append("novelty_high")
        if float(task_profile.get("similarity_to_previous_tasks", 0.0)) >= 0.65:
            observations.append("memory_reuse_available")
        if float(task_profile.get("risk", 0.0)) >= 0.6:
            observations.append("risk_high")
        if float(task_profile.get("required_confidence", 0.0)) >= 0.85:
            observations.append("confidence_requirement_high")
        return observations or ["standard_task_profile"]

    def _expected_outcomes(
        self,
        decision: CognitiveDecision,
        simulation: Mapping[str, Any],
    ) -> dict[str, Any]:
        runtimes = decision.associated_policy.get("runtime_selection", [])
        return {
            "Expected Concepts": 1 if "concept_runtime" in runtimes else 0,
            "Expected Programs": 1 if "program_runtime" in runtimes else 0,
            "Expected Search Routes": decision.expected_search_depth,
            "Expected Evidence": simulation["Expected Evidence Growth"],
            "Expected Truth Candidates": simulation["Expected Truth Generation"],
            "Expected Memory Entries": simulation["Expected Memory Promotion"],
            "Expected Confidence": simulation["Expected Confidence"],
            "Expected Execution Time": round(decision.expected_cost * 10, 3),
            "Expected Resource Consumption": simulation["Expected Resource Usage"],
            "Expected Learning Value": round(decision.expected_learning_value, 3),
        }

    def _risk_analysis(self, decision: CognitiveDecision) -> dict[str, float]:
        risk = decision.expected_risk
        return {
            "Execution Risk": round(risk, 3),
            "Search Risk": round(self._clamp(risk + decision.expected_search_depth / 20.0), 3),
            "Truth Risk": round(self._clamp(risk - decision.expected_truth_yield * 0.2), 3),
            "Memory Risk": round(self._clamp(risk - decision.expected_memory_yield * 0.15), 3),
            "Knowledge Risk": round(self._clamp(risk - decision.expected_knowledge_gain * 0.1), 3),
            "Resource Risk": round(self._clamp(decision.expected_cost), 3),
            "Governance Risk": round(self._clamp(risk * 0.8), 3),
            "Policy Risk": round(self._clamp(1.0 - decision.applicability_score), 3),
            "World Model Risk": round(self._clamp(risk - decision.expected_world_model_impact * 0.2), 3),
            "DNA Risk": round(self._clamp(risk - decision.expected_dna_impact * 0.2), 3),
        }

    def _decision_confidence(
        self,
        decision: CognitiveDecision,
        simulation: Mapping[str, Any],
    ) -> dict[str, float]:
        decision_confidence = self._clamp(
            decision.confidence * 0.45
            + simulation["Expected Success"] * 0.35
            + decision.expected_stability * 0.2
        )
        robustness = self._clamp(1.0 - decision.expected_risk)
        consistency = self._clamp(
            (decision.applicability_score + decision.expected_stability) / 2.0
        )
        return {
            "Decision Confidence": round(decision_confidence, 3),
            "Decision Stability": round(decision.expected_stability, 3),
            "Decision Robustness": round(robustness, 3),
            "Decision Consistency": round(consistency, 3),
            "Decision Reliability": round((decision_confidence + robustness) / 2.0, 3),
            "Decision Maturity": round(self._clamp(decision.expected_stability * 0.8), 3),
            "Decision Novelty": round(float(decision.task_profile.get("novelty", 0.0)), 3),
            "Decision Generalization": round(
                float(decision.task_profile.get("similarity_to_previous_tasks", 0.0)),
                3,
            ),
        }

    def _decision_cost(self, decision: CognitiveDecision) -> dict[str, float]:
        complexity = self._clamp(
            len(decision.associated_policy.get("runtime_selection", [])) / 10.0
            + decision.expected_search_depth / 20.0
        )
        return {
            "Decision Time": round(0.05 + complexity * 0.2, 3),
            "Decision Complexity": round(complexity, 3),
            "Decision Cost": round(decision.expected_cost, 3),
            "Simulation Cost": round(complexity * 0.25, 3),
            "Evaluation Cost": round(complexity * 0.2, 3),
            "Comparison Cost": round(complexity * 0.15, 3),
            "Reasoning Cost": round(complexity * 0.3, 3),
        }

    def _utility(
        self,
        decision: CognitiveDecision,
        simulation: Mapping[str, Any],
        risk_analysis: Mapping[str, float],
        confidence: Mapping[str, float],
    ) -> float:
        return self._clamp(
            simulation["Expected Success"] * 0.3
            + decision.applicability_score * 0.18
            + decision.expected_benefit * 0.16
            + confidence["Decision Confidence"] * 0.18
            + decision.expected_learning_value * 0.1
            + decision.expected_truth_yield * 0.08
            + decision.expected_memory_yield * 0.05
            + decision.expected_world_model_impact * 0.04
            + decision.expected_dna_impact * 0.03
            - risk_analysis["Execution Risk"] * 0.15
            - risk_analysis["Policy Risk"] * 0.15
            - decision.expected_cost * 0.16
        )

    def _rejected_decision_record(
        self,
        item: Mapping[str, Any],
    ) -> dict[str, Any]:
        decision = item["Decision"]
        return {
            "decision_id": decision["Decision ID"],
            "policy_id": decision["Associated Policy"]["policy_id"],
            "reason_for_rejection": "lower_decision_utility",
            "confidence": item["Decision Confidence"]["Decision Confidence"],
            "utility": round(item["Decision Utility"], 3),
            "expected_outcomes": item["Expected Outcomes"],
            "historical_performance": decision["Decision Trace"].get("policy_statistics", {}),
            "potential_future_applicability": decision["Applicability Score"],
        }

    def _decision_evolution(
        self,
        selected: Mapping[str, Any],
    ) -> dict[str, Any]:
        policy_id = selected["Decision"]["Associated Policy"]["policy_id"]
        stats = self.decision_statistics.get(policy_id, DecisionStatistics())
        stats_data = stats.as_dict()
        if stats_data["activation_count"] >= 5 and stats_data["success_rate"] < 0.3:
            action = "weaken_decision_strategy"
        elif stats_data["activation_count"] >= 3 and stats_data["success_rate"] >= 0.75:
            action = "strengthen_decision_strategy"
        else:
            action = "continue_observation"
        return {
            "selected_policy": policy_id,
            "evolution_action": action,
            "merge_redundant_strategies": False,
            "retire_obsolete_strategies": action == "weaken_decision_strategy",
            "novel_strategy_emergence": "observe_rejected_decision_memory",
        }

    def _decision_quality(self, stats: DecisionStatistics) -> str:
        data = stats.as_dict()
        if data["success_rate"] >= 0.75 and data["prediction_accuracy"] >= 0.7:
            return "high_quality_decision_strategy"
        if data["failure_rate"] >= 0.5:
            return "decision_strategy_needs_review"
        return "decision_strategy_under_observation"

    def _running_average(self, current: float, value: float, count: int) -> float:
        return current + (value - current) / max(1, count)

    def _clamp(self, value: Any) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


cognitive_decision_intelligence_engine = CognitiveDecisionIntelligenceEngine()


__all__ = [
    "CognitiveDecision",
    "CognitiveDecisionIntelligenceEngine",
    "DecisionStatistics",
    "cognitive_decision_intelligence_engine",
]
