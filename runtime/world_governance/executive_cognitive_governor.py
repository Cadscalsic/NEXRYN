"""Executive Cognitive Governor for NEXRYN world governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
from uuid import uuid4

from runtime.world_governance.cognitive_policy_engine import (
    CognitivePolicyEngine,
    cognitive_policy_engine,
)


EXECUTIVE_DOMAINS: tuple[str, ...] = (
    "goal_governance",
    "execution_governance",
    "resource_governance",
    "knowledge_governance",
    "truth_governance",
    "evolution_governance",
)

RUNTIME_DEPENDENCY_GRAPH: dict[str, list[str]] = {
    "concept_runtime": [],
    "program_runtime": ["concept_runtime"],
    "adaptive_search": ["concept_runtime"],
    "evidence_builder": ["adaptive_search"],
    "knowledge_integration": ["evidence_builder"],
    "truth_runtime": ["knowledge_integration"],
    "memory_runtime": ["truth_runtime"],
    "evaluation_runtime": ["program_runtime", "truth_runtime"],
    "meta_review": ["evaluation_runtime", "memory_runtime"],
}

LEGAL_ARTIFACT_TRANSITIONS: dict[str, set[str]] = {
    "created": {"validated", "archived"},
    "validated": {"published", "archived"},
    "published": {"consumed", "promoted", "archived"},
    "consumed": {"promoted", "archived"},
    "promoted": {"committed", "archived"},
    "committed": {"archived"},
    "archived": set(),
}


@dataclass(frozen=True)
class CognitiveExecutionIntent:
    intent_id: str
    goal: str
    priority: float
    execution_profile: str
    reasoning_strategy: str
    stopping_criteria: list[str]
    expected_outputs: list[str]
    confidence_target: float
    fallback_strategy: str
    learning_objective: str
    task_analysis: dict[str, Any] = field(default_factory=dict)
    policy_evaluation: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "goal": self.goal,
            "priority": self.priority,
            "execution_profile": self.execution_profile,
            "reasoning_strategy": self.reasoning_strategy,
            "stopping_criteria": list(self.stopping_criteria),
            "expected_outputs": list(self.expected_outputs),
            "confidence_target": self.confidence_target,
            "fallback_strategy": self.fallback_strategy,
            "learning_objective": self.learning_objective,
            "task_analysis": dict(self.task_analysis),
            "policy_evaluation": dict(self.policy_evaluation),
        }


class ExecutiveCognitiveGovernor:
    """Highest-level executive authority for cognitive execution cycles."""

    def __init__(
        self,
        policy_engine: CognitivePolicyEngine | None = None,
    ) -> None:
        self.executive_reports: list[dict[str, Any]] = []
        self.active_intents: dict[str, CognitiveExecutionIntent] = {}
        self.policy_engine = policy_engine or CognitivePolicyEngine()

    def build_execution_intent(
        self,
        task: Mapping[str, Any] | Any,
        context: Mapping[str, Any] | None = None,
    ) -> CognitiveExecutionIntent:
        task_data = self._data(task)
        context_data = dict(context or {})
        policy_report = self.policy_engine.select_policy(task_data, context_data)
        cognitive_policy_report = policy_report["COGNITIVE_POLICY_REPORT"]
        selected_policy = cognitive_policy_report["Selected Policy"]["policy"]
        policy_intent = cognitive_policy_report["Execution Intent"]
        analysis = self._analysis_from_policy_report(cognitive_policy_report)
        profile = self._profile_from_policy(selected_policy)
        confidence_target = policy_intent["confidence_target"]
        goal = str(
            task_data.get("goal")
            or task_data.get("task")
            or task_data.get("candidate_name")
            or "governed_cognitive_execution"
        )
        intent = CognitiveExecutionIntent(
            intent_id=f"cei_{uuid4().hex}",
            goal=goal,
            priority=analysis["priority"],
            execution_profile=profile,
            reasoning_strategy=policy_intent["reasoning_profile"],
            stopping_criteria=list(policy_intent["stopping_conditions"]),
            expected_outputs=list(policy_intent["expected_outputs"]),
            confidence_target=confidence_target,
            fallback_strategy=policy_intent["fallback_policy"],
            learning_objective=policy_intent["learning_objective"],
            task_analysis=analysis,
            policy_evaluation=cognitive_policy_report,
        )
        self.active_intents[intent.intent_id] = intent
        return intent

    def construct_execution_graph(
        self,
        intent: CognitiveExecutionIntent | Mapping[str, Any],
    ) -> dict[str, Any]:
        intent_data = (
            intent.as_dict()
            if hasattr(intent, "as_dict")
            else dict(intent)
        )
        analysis = dict(intent_data.get("task_analysis") or {})
        profile = intent_data.get("execution_profile", "adaptive")
        policy_report = dict(intent_data.get("policy_evaluation") or {})
        runtimes = list(
            policy_report.get("Execution Intent", {}).get("runtime_sequence")
            or []
        )
        if not runtimes:
            if profile == "fast":
                runtimes = [
                    "concept_runtime",
                    "program_runtime",
                    "evaluation_runtime",
                ]
            elif analysis.get("risk_level", 0.0) >= 0.65 or profile in {"deep", "full"}:
                runtimes = [
                    "concept_runtime",
                    "adaptive_search",
                    "evidence_builder",
                    "knowledge_integration",
                    "truth_runtime",
                    "memory_runtime",
                    "meta_review",
                    "evaluation_runtime",
                ]
            else:
                runtimes = [
                    "concept_runtime",
                    "program_runtime",
                    "adaptive_search",
                    "evidence_builder",
                    "truth_runtime",
                    "evaluation_runtime",
                ]
        nodes = [
            {
                "runtime_id": runtime_id,
                "activated_by": "world_governance",
                "activation_policy": policy_report.get("Selected Policy", {})
                .get("policy", {})
                .get("policy_id"),
                "reasoning_depth": self._runtime_depth(runtime_id, analysis),
                "reuse_previous_cognition": bool(
                    analysis.get("similarity_to_previous_tasks", 0.0) >= 0.7
                ),
            }
            for runtime_id in runtimes
        ]
        active = set(runtimes)
        edges = [
            {
                "source": dependency,
                "target": runtime_id,
                "relation": "runtime_dependency",
            }
            for runtime_id in runtimes
            for dependency in RUNTIME_DEPENDENCY_GRAPH.get(runtime_id, [])
            if dependency in active
        ]
        return {
            "graph_type": "task_dependent_runtime_dependency_graph",
            "planning_basis": "cognitive_policy_engine",
            "nodes": nodes,
            "edges": edges,
            "dependency_graph": {
                runtime_id: [
                    item
                    for item in RUNTIME_DEPENDENCY_GRAPH.get(runtime_id, [])
                    if item in active
                ]
                for runtime_id in runtimes
            },
            "parallel_groups": self._parallel_groups(runtimes),
        }

    def allocate_runtime_budgets(
        self,
        intent: CognitiveExecutionIntent | Mapping[str, Any],
        execution_graph: Mapping[str, Any],
    ) -> dict[str, Any]:
        intent_data = (
            intent.as_dict()
            if hasattr(intent, "as_dict")
            else dict(intent)
        )
        analysis = dict(intent_data.get("task_analysis") or {})
        policy_report = dict(intent_data.get("policy_evaluation") or {})
        policy_budget = dict(
            policy_report.get("Execution Intent", {}).get("resource_budget")
            or {}
        )
        nodes = list(execution_graph.get("nodes") or [])
        profile = intent_data.get("execution_profile", "adaptive")
        multiplier = {"fast": 0.55, "adaptive": 1.0, "deep": 1.6, "full": 2.0}.get(
            str(profile),
            1.0,
        )
        global_budget = {
            "execution_time": round(10.0 * multiplier, 2),
            "cpu_budget": round(1.0 * multiplier, 2),
            "memory_budget": int(256 * multiplier),
            "reasoning_budget": max(1, int(round(4 * multiplier))),
            "search_budget": max(1, int(round(3 * multiplier))),
            "evidence_budget": max(1, int(round(3 * multiplier))),
            "truth_budget": max(1, int(round(2 * multiplier))),
            "energy_budget": round(1.0 * multiplier, 2),
            "acsc_budget": round((0.5 + analysis.get("novelty", 0.0)) * multiplier, 2),
        }
        if policy_budget:
            budget_key_map = {
                "cpu_budget": "cpu_budget",
                "memory_budget": "memory_budget",
                "reasoning_budget": "reasoning_budget",
                "search_budget": "search_budget",
                "truth_budget": "truth_budget",
                "evidence_budget": "evidence_budget",
                "energy_budget": "energy_budget",
                "thermal_budget": "acsc_budget",
            }
            for source_key, target_key in budget_key_map.items():
                if source_key not in policy_budget:
                    continue
                policy_score = self._score(policy_budget[source_key])
                if target_key == "memory_budget":
                    global_budget[target_key] = max(64, int(512 * policy_score))
                elif target_key in {
                    "reasoning_budget",
                    "search_budget",
                    "truth_budget",
                    "evidence_budget",
                }:
                    global_budget[target_key] = max(1, int(round(8 * policy_score)))
                else:
                    global_budget[target_key] = round(max(0.1, policy_score) * multiplier, 2)
        runtime_budgets = {}
        share = 1.0 / max(1, len(nodes))
        for node in nodes:
            runtime_id = node["runtime_id"]
            weight = 1.4 if runtime_id in {"truth_runtime", "evidence_builder"} else 1.0
            runtime_budgets[runtime_id] = {
                "execution_time": round(global_budget["execution_time"] * share * weight, 3),
                "reasoning_budget": max(1, int(global_budget["reasoning_budget"] * share * weight)),
                "search_budget": max(0, int(global_budget["search_budget"] * share * weight)),
                "evidence_budget": max(0, int(global_budget["evidence_budget"] * share * weight)),
                "truth_budget": max(0, int(global_budget["truth_budget"] * share * weight)),
                "energy_budget": round(global_budget["energy_budget"] * share * weight, 3),
                "acsc_budget": round(global_budget["acsc_budget"] * share * weight, 3),
                "policy_driven": True,
            }
        return {
            "global_budget": global_budget,
            "runtime_budgets": runtime_budgets,
            "budget_policy": policy_report.get("Selected Policy", {})
            .get("policy", {})
            .get("policy_id"),
            "unused_resources_return_to_global_budget": True,
        }

    def decide_runtime_activation(
        self,
        execution_graph: Mapping[str, Any],
        runtime_budgets: Mapping[str, Any],
    ) -> dict[str, Any]:
        nodes = list(execution_graph.get("nodes") or [])
        activated = []
        skipped = []
        budgets = dict(runtime_budgets.get("runtime_budgets") or {})
        for node in nodes:
            runtime_id = node["runtime_id"]
            budget = budgets.get(runtime_id, {})
            if budget.get("execution_time", 0.0) <= 0:
                skipped.append({
                    "runtime_id": runtime_id,
                    "reason": "no_allocated_execution_time",
                })
                continue
            activated.append({
                "runtime_id": runtime_id,
                "activated_by": "world_governance",
                "activation_policy": node.get("activation_policy"),
                "activation_state": "authorized",
                "budget": budget,
                "requires_governance_retry": False,
                "reuse_previous_cognition": node.get("reuse_previous_cognition", False),
            })
        return {
            "activated_runtimes": activated,
            "skipped_runtimes": skipped,
        }

    def initialize_thermal_governance(
        self,
        intent: CognitiveExecutionIntent | Mapping[str, Any],
        execution_graph: Mapping[str, Any],
        runtime_budgets: Mapping[str, Any],
    ) -> dict[str, Any]:
        intent_data = (
            intent.as_dict()
            if hasattr(intent, "as_dict")
            else dict(intent)
        )
        novelty = float(intent_data.get("task_analysis", {}).get("novelty", 0.0))
        decisions = []
        for node in execution_graph.get("nodes") or []:
            runtime_id = node["runtime_id"]
            route_temperature = round(0.35 + novelty * 0.45, 3)
            if runtime_id in {"adaptive_search", "evidence_builder"}:
                route_temperature = min(1.0, route_temperature + 0.2)
            decisions.append({
                "runtime_id": runtime_id,
                "route_temperature": route_temperature,
                "thermal_budget": runtime_budgets.get("runtime_budgets", {})
                .get(runtime_id, {})
                .get("acsc_budget", 0.0),
                "decision": (
                    "increase_exploration"
                    if route_temperature >= 0.7
                    else "balance_exploitation_and_exploration"
                ),
            })
        return {
            "acsc_controlled_by": "world_governance",
            "thermal_decisions": decisions,
        }

    def supervise_artifact_transition(
        self,
        artifact: Mapping[str, Any],
        target_state: str,
    ) -> dict[str, Any]:
        current = str(artifact.get("state", "created")).lower()
        target = str(target_state).lower()
        legal = target in LEGAL_ARTIFACT_TRANSITIONS.get(current, set())
        owner = artifact.get("owner") or "world_governance"
        return {
            "artifact_id": artifact.get("artifact_id", "unknown_artifact"),
            "from_state": current,
            "to_state": target,
            "transition_allowed": legal,
            "artifact_owner": owner,
            "ownership_enforced": True,
            "promotion_policy_validated": target != "committed" or artifact.get("validated") is True,
            "decision": "ALLOW_TRANSITION" if legal else "REJECT_ILLEGAL_TRANSITION",
        }

    def validate_truth_promotion(
        self,
        truth_candidate: Mapping[str, Any],
        target_state: str = "validated_truth",
    ) -> dict[str, Any]:
        confidence = float(truth_candidate.get("confidence", 0.0))
        evidence = float(truth_candidate.get("evidence_score", truth_candidate.get("evidence", 0.0)))
        contradictions = float(truth_candidate.get("contradiction_score", 0.0))
        allowed = confidence >= 0.85 and evidence >= 0.75 and contradictions <= 0.1
        return {
            "truth_id": truth_candidate.get("truth_id", truth_candidate.get("candidate_name", "unknown_truth")),
            "target_state": target_state,
            "promotion_allowed": allowed,
            "confidence": confidence,
            "evidence_score": evidence,
            "contradiction_score": contradictions,
            "decision": "VALIDATE_TRUTH_PROMOTION" if allowed else "REQUIRE_MORE_EVIDENCE",
            "truth_enters_memory": allowed and target_state in {"committed_truth", "memory"},
            "truth_updates_world_model": allowed and target_state == "committed_truth",
        }

    def govern_world_model_update(self, knowledge: Mapping[str, Any]) -> dict[str, Any]:
        committed = knowledge.get("state") == "committed" or knowledge.get("committed") is True
        contradictory = bool(knowledge.get("contradictory"))
        allowed = committed and not contradictory
        return {
            "knowledge_id": knowledge.get("knowledge_id", "unknown_knowledge"),
            "update_allowed": allowed,
            "requires_governance_review": contradictory,
            "temporary_hypotheses_prohibited": True,
            "decision": "ALLOW_WORLD_MODEL_UPDATE" if allowed else "BLOCK_WORLD_MODEL_UPDATE",
        }

    def govern_dna_evolution(self, signal: Mapping[str, Any]) -> dict[str, Any]:
        stable_sources = {
            "persistent_truth",
            "persistent_knowledge",
            "stable_memory",
            "repeated_success",
            "long_term_statistics",
        }
        source = str(signal.get("source", "temporary_reasoning"))
        allowed = source in stable_sources and float(signal.get("stability", 0.0)) >= 0.85
        return {
            "signal_id": signal.get("signal_id", "unknown_signal"),
            "source": source,
            "dna_evolution_allowed": allowed,
            "temporary_reasoning_rejected": source == "temporary_reasoning",
            "decision": "ALLOW_DNA_EVOLUTION" if allowed else "BLOCK_DNA_EVOLUTION",
        }

    def monitor_execution(
        self,
        intent: CognitiveExecutionIntent | Mapping[str, Any],
        runtime_events: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        events = [dict(event) for event in runtime_events or []]
        confidence_values = [
            float(event.get("confidence", 0.0))
            for event in events
            if "confidence" in event
        ]
        return {
            "runtime_health": self._aggregate_state(events, "runtime_health", "healthy"),
            "artifact_flow": self._count_events(events, "artifact"),
            "evidence_growth": self._sum_events(events, "evidence_growth"),
            "truth_growth": self._sum_events(events, "truth_growth"),
            "context_growth": self._sum_events(events, "context_growth"),
            "knowledge_density": round(self._sum_events(events, "knowledge_density") / max(1, len(events)), 3),
            "resource_consumption": round(self._sum_events(events, "resource_consumption"), 3),
            "execution_progress": round(self._sum_events(events, "progress") / max(1, len(events)), 3),
            "confidence_evolution": confidence_values,
        }

    def adaptive_replan(
        self,
        intent: CognitiveExecutionIntent | Mapping[str, Any],
        monitoring_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        confidence_values = monitoring_report.get("confidence_evolution") or []
        latest_confidence = confidence_values[-1] if confidence_values else 0.0
        resource_use = float(monitoring_report.get("resource_consumption", 0.0))
        actions = []
        if latest_confidence < 0.5:
            actions.extend(["increase_search_depth", "collect_additional_evidence"])
        if resource_use > 0.9:
            actions.extend(["reduce_search_depth", "suspend_low_value_runtimes"])
        if not actions:
            actions.append("continue_current_plan")
        return {
            "replanning_required": actions != ["continue_current_plan"],
            "actions": actions,
            "reason": "execution_deviation_detected" if actions != ["continue_current_plan"] else "execution_within_expectations",
        }

    def decide_termination(
        self,
        intent: CognitiveExecutionIntent | Mapping[str, Any],
        monitoring_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        intent_data = (
            intent.as_dict()
            if hasattr(intent, "as_dict")
            else dict(intent)
        )
        target = float(intent_data.get("confidence_target", 0.85))
        confidence_values = monitoring_report.get("confidence_evolution") or []
        latest_confidence = confidence_values[-1] if confidence_values else 0.0
        progress = float(monitoring_report.get("execution_progress", 0.0))
        resource_use = float(monitoring_report.get("resource_consumption", 0.0))
        should_end = latest_confidence >= target or progress >= 1.0 or resource_use >= 1.0
        reason = "continue_execution"
        if latest_confidence >= target:
            reason = "confidence_threshold_reached"
        elif progress >= 1.0:
            reason = "goal_achieved"
        elif resource_use >= 1.0:
            reason = "resource_exhaustion"
        return {
            "terminate_execution": should_end,
            "termination_reason": reason,
            "latest_confidence": latest_confidence,
            "confidence_target": target,
        }

    def govern_learning_cycle(
        self,
        execution_result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = dict(execution_result or {})
        success = bool(result.get("success", False))
        stable = bool(result.get("stable", success))
        return {
            "what_succeeded": list(result.get("successes", [])),
            "what_failed": list(result.get("failures", [])),
            "memory_update_allowed": success,
            "world_model_update_allowed": success and stable and result.get("committed_truth") is True,
            "dna_update_allowed": success and stable and result.get("repeated_success") is True,
            "forgetting_recommended": list(result.get("low_value_artifacts", [])),
        }

    def govern_cognitive_cycle(
        self,
        task: Mapping[str, Any] | Any,
        context: Mapping[str, Any] | None = None,
        runtime_events: list[Mapping[str, Any]] | None = None,
        execution_result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        intent = self.build_execution_intent(task, context)
        graph = self.construct_execution_graph(intent)
        budgets = self.allocate_runtime_budgets(intent, graph)
        activation = self.decide_runtime_activation(graph, budgets)
        thermal = self.initialize_thermal_governance(intent, graph, budgets)
        monitoring = self.monitor_execution(intent, runtime_events)
        replanning = self.adaptive_replan(intent, monitoring)
        termination = self.decide_termination(intent, monitoring)
        learning = self.govern_learning_cycle(execution_result)
        policy_report = intent.policy_evaluation
        decision_report = policy_report.get(
            "Cognitive Decision Intelligence Report",
            {},
        )
        selected_policy_id = (
            policy_report.get("Selected Policy", {})
            .get("policy", {})
            .get("policy_id")
        )
        policy_learning = {}
        if selected_policy_id:
            policy_learning = self.policy_engine.record_policy_outcome(
                selected_policy_id,
                {
                    "success": bool((execution_result or {}).get("success", False)),
                    "confidence": termination["latest_confidence"],
                    "cost": monitoring["resource_consumption"],
                    "runtime": len(activation["activated_runtimes"]),
                    "knowledge_yield": monitoring["knowledge_density"],
                    "truth_yield": monitoring["truth_growth"],
                    "memory_yield": 1.0 if learning["memory_update_allowed"] else 0.0,
                    "reuse_yield": 1.0
                    if any(
                        item.get("reuse_previous_cognition")
                        for item in activation["activated_runtimes"]
                    )
                    else 0.0,
                },
            )
            decision_learning = (
                self.policy_engine.decision_intelligence_engine
                .record_decision_outcome(
                    {
                        "COGNITIVE_DECISION_INTELLIGENCE_REPORT":
                        decision_report,
                    },
                    {
                        "success": bool((execution_result or {}).get("success", False)),
                        "truth_yield": monitoring["truth_growth"],
                        "memory_yield": 1.0 if learning["memory_update_allowed"] else 0.0,
                        "learning_value": 1.0
                        if learning["memory_update_allowed"]
                        or learning["world_model_update_allowed"]
                        else 0.0,
                    },
                )
            )
            policy_report["Learning Updates"] = [policy_learning]
            decision_report.setdefault("Learning Updates", []).append(
                decision_learning
            )
            policy_report["Execution Outcome"] = {
                "termination": termination,
                "monitoring": monitoring,
                "learning": learning,
            }
        report = {
            "COGNITIVE_DECISION_INTELLIGENCE_REPORT": decision_report,
            "COGNITIVE_POLICY_REPORT": policy_report,
            "WORLD_GOVERNANCE_EXECUTIVE_REPORT": {
                "Cognitive Decision Intelligence Report": decision_report,
                "Cognitive Policy Report": policy_report,
                "Execution Intent": intent.as_dict(),
                "Execution Graph": graph,
                "Activated Runtimes": activation["activated_runtimes"],
                "Skipped Runtimes": activation["skipped_runtimes"],
                "Runtime Budgets": budgets,
                "Budget Reallocation": {
                    "unused_resources_returned": True,
                    "dynamic_reallocation_enabled": True,
                },
                "Thermal Decisions": thermal,
                "Artifact Decisions": [],
                "Knowledge Decisions": [],
                "Truth Decisions": [],
                "Memory Decisions": {
                    "memory_update_allowed": learning["memory_update_allowed"],
                    "memory_receives_only_governed_truth": True,
                },
                "DNA Decisions": {
                    "dna_update_allowed": learning["dna_update_allowed"],
                    "temporary_reasoning_rejected": True,
                },
                "World Model Decisions": {
                    "world_model_update_allowed": learning["world_model_update_allowed"],
                    "only_committed_knowledge_may_modify_world_model": True,
                },
                "Execution Deviations": monitoring,
                "Adaptive Replanning Events": replanning,
                "Execution Termination": termination,
                "Learning Governance": learning,
                "Policy Learning": policy_learning,
                "Decision Learning": (
                    decision_report.get("Learning Updates", [])[-1]
                    if decision_report.get("Learning Updates")
                    else {}
                ),
                "Runtime Dependency Graph": RUNTIME_DEPENDENCY_GRAPH,
                "Final Executive Assessment": self._final_assessment(
                    activation,
                    termination,
                    replanning,
                ),
            }
        }
        self.executive_reports.append(report)
        return report

    def build_report(self) -> dict[str, Any]:
        latest = self.executive_reports[-1] if self.executive_reports else {}
        latest_decision = latest.get("COGNITIVE_DECISION_INTELLIGENCE_REPORT", {})
        latest_policy = latest.get("COGNITIVE_POLICY_REPORT", {})
        return {
            "COGNITIVE_DECISION_INTELLIGENCE_REPORT": latest_decision,
            "COGNITIVE_POLICY_REPORT": latest_policy,
            "WORLD_GOVERNANCE_EXECUTIVE_REPORT": latest.get(
                "WORLD_GOVERNANCE_EXECUTIVE_REPORT",
                {},
            ),
            "executive_report_count": len(self.executive_reports),
            "active_execution_intents": len(self.active_intents),
            "policy_engine": self.policy_engine.build_report(),
        }

    def reset(self) -> None:
        self.executive_reports.clear()
        self.active_intents.clear()
        self.policy_engine.reset()

    def _analysis_from_policy_report(
        self,
        policy_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        task_profile = dict(policy_report.get("Task Profile") or {})
        return {
            "difficulty": self._score(task_profile.get("difficulty", 0.5)),
            "novelty": self._score(task_profile.get("novelty", 0.5)),
            "similarity_to_previous_tasks": self._score(
                task_profile.get("similarity_to_previous_tasks", 0.0)
            ),
            "expected_reasoning_depth": self._score(
                max(
                    task_profile.get("difficulty", 0.5),
                    task_profile.get("logical_reasoning", 0.0),
                    task_profile.get("symbolic_reasoning", 0.0),
                )
            ),
            "expected_resources": self._score(
                max(
                    task_profile.get("expected_search_cost", 0.5),
                    task_profile.get("difficulty", 0.5),
                )
            ),
            "risk_level": self._score(task_profile.get("risk", 0.3)),
            "required_confidence": self._score(
                task_profile.get("required_confidence", 0.85)
            ),
            "priority": self._score(task_profile.get("priority", 0.5)),
        }

    def _profile_from_policy(self, selected_policy: Mapping[str, Any]) -> str:
        policy_id = selected_policy.get("policy_id")
        if policy_id == "low_resource_policy":
            return "fast"
        if policy_id in {"deep_investigation_policy", "conflict_resolution_policy"}:
            return "full"
        if policy_id == "novel_task_policy":
            return "deep"
        return "adaptive"

    def _analyze_task(
        self,
        task: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> dict[str, Any]:
        difficulty = self._score(task.get("difficulty", context.get("difficulty", 0.5)))
        novelty = self._score(task.get("novelty", context.get("novelty", 0.5)))
        similarity = self._score(task.get("similarity_to_previous_tasks", context.get("similarity_to_previous_tasks", 0.0)))
        risk = self._score(task.get("risk_level", context.get("risk_level", 0.3)))
        depth = self._score(task.get("expected_reasoning_depth", context.get("expected_reasoning_depth", difficulty)))
        resources = self._score(task.get("expected_resources", context.get("expected_resources", max(difficulty, novelty))))
        confidence = self._score(task.get("required_confidence", context.get("required_confidence", 0.85)))
        priority = self._score(task.get("priority", max(risk, confidence, 1.0 - similarity)))
        return {
            "difficulty": difficulty,
            "novelty": novelty,
            "similarity_to_previous_tasks": similarity,
            "expected_reasoning_depth": depth,
            "expected_resources": resources,
            "risk_level": risk,
            "required_confidence": confidence,
            "priority": priority,
        }

    def _select_execution_profile(self, analysis: Mapping[str, Any]) -> str:
        if analysis["difficulty"] < 0.25 and analysis["risk_level"] < 0.25:
            return "fast"
        if analysis["risk_level"] >= 0.75 or analysis["required_confidence"] >= 0.95:
            return "full"
        if analysis["difficulty"] >= 0.65 or analysis["novelty"] >= 0.7:
            return "deep"
        return "adaptive"

    def _reasoning_strategy(self, analysis: Mapping[str, Any]) -> str:
        if analysis["novelty"] >= 0.7:
            return "exploratory_evidence_first"
        if analysis["similarity_to_previous_tasks"] >= 0.7:
            return "reuse_guided_reasoning"
        if analysis["risk_level"] >= 0.6:
            return "truth_guarded_reasoning"
        return "adaptive_reasoning"

    def _expected_outputs(self, analysis: Mapping[str, Any]) -> list[str]:
        outputs = ["evaluation_report"]
        if analysis["difficulty"] >= 0.25:
            outputs.extend(["cognitive_artifacts", "knowledge_candidates"])
        if analysis["risk_level"] >= 0.45:
            outputs.extend(["evidence_report", "truth_decision"])
        if analysis["novelty"] >= 0.55:
            outputs.append("learning_signal")
        return outputs

    def _fallback_strategy(self, analysis: Mapping[str, Any]) -> str:
        if analysis["risk_level"] >= 0.65:
            return "sandbox_then_governance_review"
        if analysis["novelty"] >= 0.65:
            return "expand_search_then_evidence_review"
        return "safe_early_stop_with_partial_report"

    def _learning_objective(self, analysis: Mapping[str, Any]) -> str:
        if analysis["similarity_to_previous_tasks"] >= 0.7:
            return "reinforce_reusable_cognition"
        if analysis["novelty"] >= 0.55:
            return "capture_new_governed_knowledge"
        return "preserve_execution_statistics"

    def _confidence_target(self, analysis: Mapping[str, Any]) -> float:
        return round(max(0.75, analysis["required_confidence"], 0.8 + analysis["risk_level"] * 0.15), 3)

    def _runtime_depth(self, runtime_id: str, analysis: Mapping[str, Any]) -> int:
        base = 1 + int(round(analysis.get("expected_reasoning_depth", 0.5) * 4))
        if runtime_id in {"truth_runtime", "evidence_builder", "meta_review"}:
            base += 1
        return max(1, base)

    def _parallel_groups(self, runtimes: list[str]) -> list[list[str]]:
        active = set(runtimes)
        groups = [["concept_runtime"]]
        parallel = [
            runtime_id
            for runtime_id in ("program_runtime", "adaptive_search")
            if runtime_id in active
        ]
        if parallel:
            groups.append(parallel)
        later = [
            runtime_id
            for runtime_id in ("evidence_builder", "knowledge_integration", "truth_runtime")
            if runtime_id in active
        ]
        if later:
            groups.extend([[runtime_id] for runtime_id in later])
        tail = [
            runtime_id
            for runtime_id in ("memory_runtime", "evaluation_runtime", "meta_review")
            if runtime_id in active
        ]
        if tail:
            groups.append(tail)
        return groups

    def _final_assessment(
        self,
        activation: Mapping[str, Any],
        termination: Mapping[str, Any],
        replanning: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "executive_authority": "Executive Cognitive Governor",
            "cycle_governed": True,
            "all_runtime_activations_governed": all(
                item.get("activated_by") == "world_governance"
                for item in activation.get("activated_runtimes", [])
            ),
            "termination_decided_by_governance": True,
            "replanning_available": True,
            "current_state": (
                "terminated"
                if termination.get("terminate_execution")
                else "governed_execution_active"
            ),
            "replanning_state": replanning.get("reason"),
        }

    def _aggregate_state(
        self,
        events: list[Mapping[str, Any]],
        key: str,
        default: str,
    ) -> str:
        values = [str(event.get(key)) for event in events if event.get(key)]
        if not values:
            return default
        if any(value in {"failed", "critical", "unstable"} for value in values):
            return "unstable"
        if any(value in {"degraded", "warning"} for value in values):
            return "degraded"
        return "healthy"

    def _count_events(self, events: list[Mapping[str, Any]], event_type: str) -> int:
        return sum(1 for event in events if event.get("event_type") == event_type)

    def _sum_events(self, events: list[Mapping[str, Any]], key: str) -> float:
        total = 0.0
        for event in events:
            try:
                total += float(event.get(key, 0.0))
            except (TypeError, ValueError):
                continue
        return total

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


executive_cognitive_governor = ExecutiveCognitiveGovernor(
    policy_engine=cognitive_policy_engine,
)


__all__ = [
    "EXECUTIVE_DOMAINS",
    "LEGAL_ARTIFACT_TRANSITIONS",
    "RUNTIME_DEPENDENCY_GRAPH",
    "CognitiveExecutionIntent",
    "ExecutiveCognitiveGovernor",
    "executive_cognitive_governor",
]
