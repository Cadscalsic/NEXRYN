"""Declarative Cognitive Policy Engine for World Governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from runtime.world_governance.cognitive_decision_intelligence import (
    CognitiveDecisionIntelligenceEngine,
    cognitive_decision_intelligence_engine,
)


POLICY_FAMILIES: tuple[str, ...] = (
    "execution",
    "reasoning",
    "search",
    "memory",
    "truth",
    "knowledge",
    "resource",
    "learning",
    "governance",
    "safety",
    "optimization",
    "evolution",
    "meta_cognitive",
)


@dataclass(frozen=True)
class CognitiveTaskProfile:
    novelty: float
    difficulty: float
    abstraction: float
    spatial_reasoning: float
    temporal_reasoning: float
    symbolic_reasoning: float
    logical_reasoning: float
    pattern_completion: float
    transformation_complexity: float
    required_confidence: float
    expected_search_cost: float
    knowledge_availability: float
    memory_availability: float
    risk: float
    similarity_to_previous_tasks: float
    priority: float

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class CognitivePolicy:
    policy_id: str
    policy_family: str
    purpose: str
    applicability: dict[str, tuple[float | None, float | None]]
    activation_conditions: list[str]
    required_context: list[str]
    required_evidence: list[str]
    priority: float
    execution_strategy: str
    runtime_selection: list[str]
    optional_runtimes: list[str]
    budget_allocation: dict[str, float]
    success_criteria: list[str]
    termination_criteria: list[str]
    fallback_strategy: str
    learning_hooks: list[str]
    cooperation_allowed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_family": self.policy_family,
            "purpose": self.purpose,
            "applicability": dict(self.applicability),
            "activation_conditions": list(self.activation_conditions),
            "required_context": list(self.required_context),
            "required_evidence": list(self.required_evidence),
            "priority": self.priority,
            "execution_strategy": self.execution_strategy,
            "runtime_selection": list(self.runtime_selection),
            "optional_runtimes": list(self.optional_runtimes),
            "budget_allocation": dict(self.budget_allocation),
            "success_criteria": list(self.success_criteria),
            "termination_criteria": list(self.termination_criteria),
            "fallback_strategy": self.fallback_strategy,
            "learning_hooks": list(self.learning_hooks),
            "cooperation_allowed": self.cooperation_allowed,
        }


@dataclass
class PolicyStatistics:
    activation_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    average_confidence: float = 0.0
    average_cost: float = 0.0
    average_runtime: float = 0.0
    knowledge_yield: float = 0.0
    truth_yield: float = 0.0
    memory_yield: float = 0.0
    reuse_yield: float = 0.0

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
            "average_confidence": round(self.average_confidence, 3),
            "average_cost": round(self.average_cost, 3),
            "average_runtime": round(self.average_runtime, 3),
            "knowledge_yield": round(self.knowledge_yield, 3),
            "truth_yield": round(self.truth_yield, 3),
            "memory_yield": round(self.memory_yield, 3),
            "reuse_yield": round(self.reuse_yield, 3),
        }


@dataclass(frozen=True)
class PolicyEvaluation:
    policy: CognitivePolicy
    applicability_score: float
    confidence: float
    estimated_cost: float
    estimated_benefit: float
    expected_runtime_usage: list[str]
    expected_search_depth: int
    expected_evidence_growth: float
    expected_truth_yield: float
    expected_learning_value: float
    utility_score: float
    selection_reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy.as_dict(),
            "applicability_score": round(self.applicability_score, 3),
            "confidence": round(self.confidence, 3),
            "estimated_cost": round(self.estimated_cost, 3),
            "estimated_benefit": round(self.estimated_benefit, 3),
            "expected_runtime_usage": list(self.expected_runtime_usage),
            "expected_search_depth": self.expected_search_depth,
            "expected_evidence_growth": round(self.expected_evidence_growth, 3),
            "expected_truth_yield": round(self.expected_truth_yield, 3),
            "expected_learning_value": round(self.expected_learning_value, 3),
            "utility_score": round(self.utility_score, 3),
            "selection_reason": self.selection_reason,
        }


class CognitivePolicyEngine:
    """Policy-driven decision core for Executive World Governance."""

    def __init__(
        self,
        policies: list[CognitivePolicy] | None = None,
        decision_intelligence_engine: CognitiveDecisionIntelligenceEngine | None = None,
    ) -> None:
        self.policies = policies or default_cognitive_policies()
        self.policy_statistics = {
            policy.policy_id: PolicyStatistics()
            for policy in self.policies
        }
        self.policy_reports: list[dict[str, Any]] = []
        self.decision_intelligence_engine = (
            decision_intelligence_engine
            or CognitiveDecisionIntelligenceEngine()
        )

    def classify_task(
        self,
        task: Mapping[str, Any] | Any,
        context: Mapping[str, Any] | None = None,
    ) -> CognitiveTaskProfile:
        task_data = self._data(task)
        context_data = dict(context or {})
        difficulty = self._score(task_data.get("difficulty", context_data.get("difficulty", 0.5)))
        novelty = self._score(task_data.get("novelty", context_data.get("novelty", 0.0)))
        risk = self._score(task_data.get("risk_level", context_data.get("risk", 0.3)))
        similarity = self._score(
            task_data.get(
                "similarity_to_previous_tasks",
                context_data.get("similarity_to_previous_tasks", 0.0),
            )
        )
        transformation = self._score(
            task_data.get(
                "transformation_complexity",
                context_data.get("transformation_complexity", difficulty),
            )
        )
        required_confidence = self._score(
            task_data.get(
                "required_confidence",
                context_data.get("required_confidence", 0.85),
            )
        )
        return CognitiveTaskProfile(
            novelty=novelty,
            difficulty=difficulty,
            abstraction=self._score(task_data.get("abstraction", context_data.get("abstraction", difficulty))),
            spatial_reasoning=self._score(task_data.get("spatial_reasoning", context_data.get("spatial_reasoning", 0.0))),
            temporal_reasoning=self._score(task_data.get("temporal_reasoning", context_data.get("temporal_reasoning", 0.0))),
            symbolic_reasoning=self._score(task_data.get("symbolic_reasoning", context_data.get("symbolic_reasoning", difficulty))),
            logical_reasoning=self._score(task_data.get("logical_reasoning", context_data.get("logical_reasoning", difficulty))),
            pattern_completion=self._score(task_data.get("pattern_completion", context_data.get("pattern_completion", 0.5))),
            transformation_complexity=transformation,
            required_confidence=required_confidence,
            expected_search_cost=self._score(task_data.get("expected_search_cost", context_data.get("expected_search_cost", max(novelty, difficulty)))),
            knowledge_availability=self._score(task_data.get("knowledge_availability", context_data.get("knowledge_availability", similarity))),
            memory_availability=self._score(task_data.get("memory_availability", context_data.get("memory_availability", similarity))),
            risk=risk,
            similarity_to_previous_tasks=similarity,
            priority=self._score(task_data.get("priority", max(required_confidence, risk, 1.0 - similarity))),
        )

    def evaluate_policies(
        self,
        task_profile: CognitiveTaskProfile,
    ) -> list[PolicyEvaluation]:
        evaluations = [
            self._evaluate_policy(policy, task_profile)
            for policy in self.policies
        ]
        return sorted(
            evaluations,
            key=lambda item: item.utility_score,
            reverse=True,
        )

    def select_policy(
        self,
        task: Mapping[str, Any] | Any,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        task_profile = self.classify_task(task, context)
        evaluations = self.evaluate_policies(task_profile)
        decision_report = (
            self.decision_intelligence_engine.reason_over_policy_evaluations(
                task_profile,
                evaluations,
                self.policy_statistics,
            )
        )
        cdi_report = decision_report[
            "COGNITIVE_DECISION_INTELLIGENCE_REPORT"
        ]
        selected_policy_id = cdi_report["Selected Decision"]["Decision"][
            "Associated Policy"
        ]["policy_id"]
        selected = next(
            item
            for item in evaluations
            if item.policy.policy_id == selected_policy_id
        )
        rejected = [
            item
            for item in evaluations
            if item.policy.policy_id != selected_policy_id
        ]
        self.policy_statistics[selected.policy.policy_id].activation_count += 1
        report = self._build_policy_report(
            task_profile,
            selected,
            rejected,
            decision_report,
        )
        self.policy_reports.append(report)
        return report

    def record_policy_outcome(
        self,
        policy_id: str,
        outcome: Mapping[str, Any],
    ) -> dict[str, Any]:
        stats = self.policy_statistics.setdefault(policy_id, PolicyStatistics())
        success = bool(outcome.get("success", False))
        if success:
            stats.success_count += 1
        else:
            stats.failure_count += 1
        stats.average_confidence = self._running_average(
            stats.average_confidence,
            float(outcome.get("confidence", 0.0)),
            max(1, stats.success_count + stats.failure_count),
        )
        stats.average_cost = self._running_average(
            stats.average_cost,
            float(outcome.get("cost", 0.0)),
            max(1, stats.success_count + stats.failure_count),
        )
        stats.average_runtime = self._running_average(
            stats.average_runtime,
            float(outcome.get("runtime", 0.0)),
            max(1, stats.success_count + stats.failure_count),
        )
        stats.knowledge_yield += float(outcome.get("knowledge_yield", 0.0))
        stats.truth_yield += float(outcome.get("truth_yield", 0.0))
        stats.memory_yield += float(outcome.get("memory_yield", 0.0))
        stats.reuse_yield += float(outcome.get("reuse_yield", 0.0))
        return {
            "policy_id": policy_id,
            "learning_update": stats.as_dict(),
            "policy_evolution_recommendation": self._evolution_recommendation(stats),
        }

    def build_report(self) -> dict[str, Any]:
        latest = self.policy_reports[-1] if self.policy_reports else {}
        return {
            "COGNITIVE_POLICY_REPORT": latest.get("COGNITIVE_POLICY_REPORT", {}),
            "policy_report_count": len(self.policy_reports),
            "policy_statistics": {
                policy_id: stats.as_dict()
                for policy_id, stats in self.policy_statistics.items()
            },
            "decision_intelligence": self.decision_intelligence_engine.build_report(),
        }

    def reset(self) -> None:
        self.policy_reports.clear()
        for stats in self.policy_statistics.values():
            stats.activation_count = 0
            stats.success_count = 0
            stats.failure_count = 0
            stats.average_confidence = 0.0
            stats.average_cost = 0.0
            stats.average_runtime = 0.0
            stats.knowledge_yield = 0.0
            stats.truth_yield = 0.0
            stats.memory_yield = 0.0
            stats.reuse_yield = 0.0
        self.decision_intelligence_engine.reset()

    def _evaluate_policy(
        self,
        policy: CognitivePolicy,
        profile: CognitiveTaskProfile,
    ) -> PolicyEvaluation:
        profile_data = profile.as_dict()
        matches = []
        for dimension, bounds in policy.applicability.items():
            low, high = bounds
            value = float(profile_data.get(dimension, 0.0))
            lower_ok = low is None or value >= low
            upper_ok = high is None or value <= high
            matches.append(1.0 if lower_ok and upper_ok else 0.0)
        applicability = sum(matches) / max(1, len(matches))
        cost = self._estimate_cost(policy, profile)
        benefit = self._estimate_benefit(policy, profile)
        confidence = min(1.0, 0.55 + applicability * 0.35 + policy.priority * 0.1)
        learning = self._learning_value(policy, profile)
        utility = (
            applicability * 0.35
            + confidence * 0.2
            + benefit * 0.25
            + learning * 0.1
            + policy.priority * 0.1
            - cost * 0.2
            - profile.risk * 0.05
        )
        return PolicyEvaluation(
            policy=policy,
            applicability_score=applicability,
            confidence=confidence,
            estimated_cost=cost,
            estimated_benefit=benefit,
            expected_runtime_usage=policy.runtime_selection + policy.optional_runtimes,
            expected_search_depth=max(1, int(round(policy.budget_allocation.get("search_budget", 1.0) * 4))),
            expected_evidence_growth=policy.budget_allocation.get("evidence_budget", 0.0),
            expected_truth_yield=policy.budget_allocation.get("truth_budget", 0.0),
            expected_learning_value=learning,
            utility_score=max(0.0, round(utility, 4)),
            selection_reason=self._selection_reason(policy, applicability, benefit, cost),
        )

    def _build_policy_report(
        self,
        task_profile: CognitiveTaskProfile,
        selected: PolicyEvaluation,
        rejected: list[PolicyEvaluation],
        decision_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        policy = selected.policy
        intent = {
            "goal_policy": policy.policy_id,
            "reasoning_profile": policy.execution_strategy,
            "runtime_sequence": list(policy.runtime_selection),
            "expected_outputs": self._expected_outputs(policy),
            "confidence_target": max(task_profile.required_confidence, 0.75),
            "resource_budget": dict(policy.budget_allocation),
            "stopping_conditions": list(policy.termination_criteria),
            "fallback_policy": policy.fallback_strategy,
            "learning_objective": ",".join(policy.learning_hooks),
        }
        report = {
            "COGNITIVE_POLICY_REPORT": {
                "Task Profile": task_profile.as_dict(),
                "Cognitive Decision Intelligence Report": (
                    dict(decision_report or {}).get(
                        "COGNITIVE_DECISION_INTELLIGENCE_REPORT",
                        {},
                    )
                ),
                "Candidate Policies": [selected.as_dict()] + [
                    item.as_dict()
                    for item in rejected
                ],
                "Selected Policy": selected.as_dict(),
                "Selection Score": round(selected.utility_score, 3),
                "Rejected Policies": [
                    {
                        "policy_id": item.policy.policy_id,
                        "utility_score": round(item.utility_score, 3),
                        "rejection_reason": "lower_policy_utility",
                    }
                    for item in rejected
                ],
                "Execution Intent": intent,
                "Decision Graph": self._decision_graph(policy),
                "Runtime Schedule": self._runtime_schedule(policy),
                "Budget Allocation": dict(policy.budget_allocation),
                "Policy Confidence": round(selected.confidence, 3),
                "Execution Outcome": {},
                "Learning Updates": [],
                "Policy Statistics": {
                    policy_id: stats.as_dict()
                    for policy_id, stats in self.policy_statistics.items()
                },
            }
        }
        return report

    def _decision_graph(self, policy: CognitivePolicy) -> dict[str, Any]:
        nodes = [
            {"node_id": "task", "node_type": "input"},
            {"node_id": policy.policy_id, "node_type": "policy"},
        ]
        edges = [{"source": "task", "target": policy.policy_id, "relation": "selected_policy"}]
        previous = policy.policy_id
        for runtime in policy.runtime_selection:
            nodes.append({"node_id": runtime, "node_type": "runtime"})
            edges.append({"source": previous, "target": runtime, "relation": "policy_runtime_step"})
            previous = runtime
        nodes.append({"node_id": "finish", "node_type": "termination"})
        edges.append({"source": previous, "target": "finish", "relation": "termination_criteria"})
        return {
            "graph_type": "policy_decision_graph",
            "nodes": nodes,
            "edges": edges,
        }

    def _runtime_schedule(self, policy: CognitivePolicy) -> dict[str, Any]:
        mandatory = list(policy.runtime_selection)
        optional = list(policy.optional_runtimes)
        return {
            "mandatory_runtimes": mandatory,
            "optional_runtimes": optional,
            "runtime_priorities": {
                runtime_id: max(0.1, policy.priority - index * 0.05)
                for index, runtime_id in enumerate(mandatory + optional)
            },
            "parallel_groups": [
                [
                    runtime_id
                    for runtime_id in ("program_runtime", "adaptive_search")
                    if runtime_id in mandatory
                ],
                [
                    runtime_id
                    for runtime_id in ("evidence_builder", "knowledge_integration")
                    if runtime_id in mandatory
                ],
            ],
        }

    def _estimate_cost(self, policy: CognitivePolicy, profile: CognitiveTaskProfile) -> float:
        budget_cost = sum(policy.budget_allocation.values()) / max(1, len(policy.budget_allocation))
        runtime_cost = len(policy.runtime_selection) / 10.0
        return min(1.0, budget_cost * 0.6 + runtime_cost * 0.4 + profile.expected_search_cost * 0.2)

    def _estimate_benefit(self, policy: CognitivePolicy, profile: CognitiveTaskProfile) -> float:
        truth_bonus = 0.15 if "truth_runtime" in policy.runtime_selection else 0.0
        memory_bonus = 0.15 if "memory_runtime" in policy.runtime_selection else 0.0
        reuse_bonus = 0.2 if "memory_runtime" in policy.runtime_selection and profile.memory_availability >= 0.6 else 0.0
        novelty_bonus = 0.2 if profile.novelty >= 0.6 and "adaptive_search" in policy.runtime_selection else 0.0
        return min(1.0, policy.priority * 0.4 + truth_bonus + memory_bonus + reuse_bonus + novelty_bonus)

    def _learning_value(self, policy: CognitivePolicy, profile: CognitiveTaskProfile) -> float:
        if "capture_new_knowledge" in policy.learning_hooks:
            return max(profile.novelty, profile.difficulty)
        if "reinforce_reuse" in policy.learning_hooks:
            return profile.similarity_to_previous_tasks
        return 0.4

    def _expected_outputs(self, policy: CognitivePolicy) -> list[str]:
        outputs = ["evaluation_report", "policy_trace"]
        if "evidence_builder" in policy.runtime_selection:
            outputs.append("evidence_report")
        if "truth_runtime" in policy.runtime_selection:
            outputs.append("truth_decision")
        if "memory_runtime" in policy.runtime_selection:
            outputs.append("memory_update")
        return outputs

    def _selection_reason(self, policy: CognitivePolicy, applicability: float, benefit: float, cost: float) -> str:
        return (
            f"{policy.policy_id}: applicability={round(applicability, 3)}, "
            f"benefit={round(benefit, 3)}, cost={round(cost, 3)}"
        )

    def _evolution_recommendation(self, stats: PolicyStatistics) -> str:
        data = stats.as_dict()
        if data["activation_count"] >= 5 and data["success_rate"] < 0.3:
            return "decline_or_retire_policy"
        if data["activation_count"] >= 3 and data["success_rate"] >= 0.75:
            return "increase_policy_priority"
        return "continue_observation"

    def _running_average(self, current: float, value: float, count: int) -> float:
        return current + (value - current) / max(1, count)

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

    def _score(self, value: Any) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


def default_cognitive_policies() -> list[CognitivePolicy]:
    common_termination = [
        "goal_achieved",
        "confidence_threshold_reached",
        "resource_exhaustion",
        "no_meaningful_progress",
    ]
    return [
        CognitivePolicy(
            policy_id="novel_task_policy",
            policy_family="execution",
            purpose="Explore unfamiliar tasks with evidence and truth protection.",
            applicability={"novelty": (0.6, None), "difficulty": (0.35, None)},
            activation_conditions=["novelty_high", "knowledge_uncertain"],
            required_context=["task_profile"],
            required_evidence=["initial_observation"],
            priority=0.86,
            execution_strategy="exploratory_evidence_first",
            runtime_selection=[
                "concept_runtime",
                "adaptive_search",
                "evidence_builder",
                "truth_runtime",
                "memory_runtime",
                "evaluation_runtime",
            ],
            optional_runtimes=["knowledge_integration", "meta_review"],
            budget_allocation={
                "cpu_budget": 0.7,
                "memory_budget": 0.65,
                "reasoning_budget": 0.85,
                "search_budget": 0.9,
                "truth_budget": 0.75,
                "evidence_budget": 0.85,
                "learning_budget": 0.8,
                "energy_budget": 0.75,
                "thermal_budget": 0.85,
            },
            success_criteria=["evidence_growth", "truth_candidate_validated"],
            termination_criteria=common_termination,
            fallback_strategy="deep_investigation_policy",
            learning_hooks=["capture_new_knowledge", "update_policy_statistics"],
        ),
        CognitivePolicy(
            policy_id="known_task_policy",
            policy_family="optimization",
            purpose="Reuse prior cognition for familiar low-risk tasks.",
            applicability={"similarity_to_previous_tasks": (0.65, None), "risk": (None, 0.45)},
            activation_conditions=["memory_available", "risk_low"],
            required_context=["task_profile", "memory_index"],
            required_evidence=["reuse_signal"],
            priority=0.82,
            execution_strategy="reuse_guided_reasoning",
            runtime_selection=["memory_runtime", "evaluation_runtime"],
            optional_runtimes=["truth_runtime"],
            budget_allocation={
                "cpu_budget": 0.35,
                "memory_budget": 0.7,
                "reasoning_budget": 0.35,
                "search_budget": 0.1,
                "truth_budget": 0.35,
                "evidence_budget": 0.2,
                "learning_budget": 0.4,
                "energy_budget": 0.3,
                "thermal_budget": 0.25,
            },
            success_criteria=["reused_solution_validated"],
            termination_criteria=common_termination + ["safe_early_stopping"],
            fallback_strategy="novel_task_policy",
            learning_hooks=["reinforce_reuse", "update_policy_statistics"],
        ),
        CognitivePolicy(
            policy_id="low_resource_policy",
            policy_family="resource",
            purpose="Conserve resources while preserving minimal safety governance.",
            applicability={"expected_search_cost": (None, 0.35), "risk": (None, 0.35)},
            activation_conditions=["resource_pressure", "risk_low"],
            required_context=["task_profile", "budget_state"],
            required_evidence=[],
            priority=0.72,
            execution_strategy="fast_reasoning_limited_search",
            runtime_selection=["concept_runtime", "program_runtime", "evaluation_runtime"],
            optional_runtimes=["memory_runtime"],
            budget_allocation={
                "cpu_budget": 0.25,
                "memory_budget": 0.35,
                "reasoning_budget": 0.25,
                "search_budget": 0.1,
                "truth_budget": 0.25,
                "evidence_budget": 0.15,
                "learning_budget": 0.2,
                "energy_budget": 0.2,
                "thermal_budget": 0.15,
            },
            success_criteria=["minimal_answer_validated"],
            termination_criteria=common_termination + ["safe_early_stopping"],
            fallback_strategy="known_task_policy",
            learning_hooks=["record_low_resource_outcome"],
        ),
        CognitivePolicy(
            policy_id="high_confidence_policy",
            policy_family="truth",
            purpose="Use existing knowledge when confidence requirements and knowledge availability align.",
            applicability={"required_confidence": (0.85, None), "knowledge_availability": (0.65, None), "risk": (None, 0.5)},
            activation_conditions=["knowledge_available", "search_not_required"],
            required_context=["task_profile", "knowledge_bus"],
            required_evidence=["validated_knowledge"],
            priority=0.78,
            execution_strategy="knowledge_reuse_with_evaluation",
            runtime_selection=["knowledge_integration", "truth_runtime", "evaluation_runtime"],
            optional_runtimes=["memory_runtime"],
            budget_allocation={
                "cpu_budget": 0.45,
                "memory_budget": 0.45,
                "reasoning_budget": 0.45,
                "search_budget": 0.05,
                "truth_budget": 0.75,
                "evidence_budget": 0.35,
                "learning_budget": 0.35,
                "energy_budget": 0.4,
                "thermal_budget": 0.25,
            },
            success_criteria=["knowledge_validated", "confidence_threshold_reached"],
            termination_criteria=common_termination,
            fallback_strategy="deep_investigation_policy",
            learning_hooks=["record_truth_yield", "update_policy_statistics"],
        ),
        CognitivePolicy(
            policy_id="deep_investigation_policy",
            policy_family="search",
            purpose="Expand search, evidence, truth, and memory for hard or risky tasks.",
            applicability={"difficulty": (0.65, None), "risk": (0.45, None)},
            activation_conditions=["difficulty_high", "risk_nontrivial"],
            required_context=["task_profile", "execution_registry"],
            required_evidence=["initial_evidence"],
            priority=0.9,
            execution_strategy="extended_search_truth_expansion",
            runtime_selection=[
                "concept_runtime",
                "adaptive_search",
                "evidence_builder",
                "knowledge_integration",
                "truth_runtime",
                "memory_runtime",
                "meta_review",
                "evaluation_runtime",
            ],
            optional_runtimes=[],
            budget_allocation={
                "cpu_budget": 0.9,
                "memory_budget": 0.85,
                "reasoning_budget": 1.0,
                "search_budget": 1.0,
                "truth_budget": 0.9,
                "evidence_budget": 1.0,
                "learning_budget": 0.85,
                "energy_budget": 0.9,
                "thermal_budget": 0.9,
            },
            success_criteria=["evidence_sufficient", "truth_committable"],
            termination_criteria=common_termination + ["maximum_reasoning_depth"],
            fallback_strategy="conflict_resolution_policy",
            learning_hooks=["capture_new_knowledge", "record_truth_yield", "update_policy_statistics"],
        ),
        CognitivePolicy(
            policy_id="conflict_resolution_policy",
            policy_family="safety",
            purpose="Resolve contradictions before truth, memory, or World Model promotion.",
            applicability={"risk": (0.65, None), "required_confidence": (0.8, None)},
            activation_conditions=["contradiction_detected", "world_model_protection_required"],
            required_context=["truth_registry", "world_model_state"],
            required_evidence=["conflicting_truth_candidates"],
            priority=0.95,
            execution_strategy="truth_guarded_conflict_resolution",
            runtime_selection=[
                "evidence_builder",
                "knowledge_integration",
                "truth_runtime",
                "meta_review",
                "evaluation_runtime",
            ],
            optional_runtimes=["memory_runtime"],
            budget_allocation={
                "cpu_budget": 0.75,
                "memory_budget": 0.65,
                "reasoning_budget": 0.85,
                "search_budget": 0.55,
                "truth_budget": 1.0,
                "evidence_budget": 0.85,
                "learning_budget": 0.55,
                "energy_budget": 0.7,
                "thermal_budget": 0.55,
            },
            success_criteria=["contradiction_resolved", "world_model_protected"],
            termination_criteria=common_termination + ["manual_review_required"],
            fallback_strategy="governance_review",
            learning_hooks=["record_conflict_resolution", "update_policy_statistics"],
        ),
    ]


cognitive_policy_engine = CognitivePolicyEngine(
    decision_intelligence_engine=cognitive_decision_intelligence_engine,
)


__all__ = [
    "POLICY_FAMILIES",
    "CognitivePolicy",
    "CognitivePolicyEngine",
    "CognitiveTaskProfile",
    "PolicyEvaluation",
    "PolicyStatistics",
    "cognitive_policy_engine",
    "default_cognitive_policies",
]
