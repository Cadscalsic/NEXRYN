"""Cognitive Situation Awareness Engine for unified cognitive context."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping
from uuid import uuid4


SITUATION_STATES: tuple[str, ...] = (
    "birth",
    "growth",
    "stabilization",
    "transition",
    "split",
    "merge",
    "resolution",
    "completion",
)


@dataclass(frozen=True)
class CognitiveSituation:
    situation_id: str
    timestamp: str
    execution_context: dict[str, Any]
    task_identity: str
    current_goal: str
    current_stage: str
    execution_profile: str
    task_complexity: float
    novelty_estimate: float
    confidence: float
    situation_stability: float
    situation_completeness: float
    situation_readiness: float
    overall_situation_quality: float
    objects: dict[str, Any] = field(default_factory=dict)
    relations: list[dict[str, Any]] = field(default_factory=list)
    transformations: dict[str, Any] = field(default_factory=dict)
    goals: dict[str, Any] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)
    uncertainty: dict[str, Any] = field(default_factory=dict)
    risk: dict[str, Any] = field(default_factory=dict)
    recommendations: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "Situation ID": self.situation_id,
            "Timestamp": self.timestamp,
            "Execution Context": dict(self.execution_context),
            "Task Identity": self.task_identity,
            "Current Goal": self.current_goal,
            "Current Stage": self.current_stage,
            "Execution Profile": self.execution_profile,
            "Task Complexity": round(self.task_complexity, 3),
            "Novelty Estimate": round(self.novelty_estimate, 3),
            "Confidence": round(self.confidence, 3),
            "Situation Stability": round(self.situation_stability, 3),
            "Situation Completeness": round(self.situation_completeness, 3),
            "Situation Readiness": round(self.situation_readiness, 3),
            "Overall Situation Quality": round(self.overall_situation_quality, 3),
            "Objects": dict(self.objects),
            "Relations": list(self.relations),
            "Transformations": dict(self.transformations),
            "Goals": dict(self.goals),
            "Resources": dict(self.resources),
            "Uncertainty": dict(self.uncertainty),
            "Risk": dict(self.risk),
            "Recommendations": list(self.recommendations),
        }


class CognitiveSituationAwarenessEngine:
    """Builds unified situations from distributed cognitive artifacts."""

    def __init__(self) -> None:
        self.situations: list[CognitiveSituation] = []
        self.situation_reports: list[dict[str, Any]] = []

    def construct_situation(
        self,
        artifacts: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        fused = self._fuse(artifacts or {})
        previous = self.situations[-1] if self.situations else None
        objects = self._situational_objects(fused)
        transformations = self._transformation_awareness(fused)
        goals = self._goal_model(fused)
        resources = self._resource_awareness(fused)
        uncertainty = self._uncertainty_model(fused)
        risk = self._risk_awareness(fused)
        confidence = self._situation_confidence(fused, uncertainty)
        stability = self._situation_stability(fused, risk, previous)
        completeness = self._situation_completeness(objects, uncertainty, fused)
        readiness = self._situation_readiness(confidence, stability, completeness, risk)
        quality = _clamp((confidence + stability + completeness + readiness) / 4.0)
        situation = CognitiveSituation(
            situation_id=f"situation_{uuid4().hex}",
            timestamp=datetime.utcnow().isoformat(),
            execution_context=self._execution_context(fused),
            task_identity=fused["task_identity"],
            current_goal=goals["Current Objective"],
            current_stage=fused["current_stage"],
            execution_profile=fused["execution_profile"],
            task_complexity=fused["task_complexity"],
            novelty_estimate=fused["novelty"],
            confidence=confidence,
            situation_stability=stability,
            situation_completeness=completeness,
            situation_readiness=readiness,
            overall_situation_quality=quality,
            objects=objects,
            relations=self._relations(fused),
            transformations=transformations,
            goals=goals,
            resources=resources,
            uncertainty=uncertainty,
            risk=risk,
            recommendations=self._recommendations(fused, uncertainty, risk, readiness),
        )
        comparison = self.compare_situations(previous, situation)
        prediction = self.predict_next_situation(situation, comparison)
        summary = self._executive_summary(situation, fused, uncertainty)
        report = {
            "COGNITIVE_SITUATION_REPORT": {
                "Situation Summary": summary,
                "Situation": situation.as_dict(),
                "Situation Graph": self._situation_graph(situation),
                "Current Goal": goals,
                "Objects": objects,
                "Relations": situation.relations,
                "Transformations": transformations,
                "Evidence": fused["evidence"],
                "Knowledge": fused["knowledge"],
                "Truth": fused["truth"],
                "Memory": fused["memory"],
                "Policies": fused["policies"],
                "Decisions": fused["decisions"],
                "Analytics": fused["analytics"],
                "Resources": resources,
                "Uncertainty": uncertainty,
                "Risk": risk,
                "Confidence": {
                    "Overall Situation Confidence": round(confidence, 3),
                    "Concept Confidence": fused["concept_confidence"],
                    "Evidence Confidence": fused["evidence_confidence"],
                    "Truth Confidence": fused["truth_confidence"],
                    "Memory Confidence": fused["memory_confidence"],
                    "Decision Confidence": fused["decision_confidence"],
                    "Policy Confidence": fused["policy_confidence"],
                    "Knowledge Confidence": fused["knowledge_confidence"],
                    "Reasoning Confidence": fused["reasoning_confidence"],
                    "Search Confidence": fused["search_confidence"],
                },
                "Recommendations": situation.recommendations,
                "Expected Next Situation": prediction,
                "Situation Timeline": self._timeline(situation),
                "Situation Evolution": self._evolution_state(situation, comparison),
                "Situation Comparison": comparison,
                "Situation Explainability": self._explainability(situation, fused, uncertainty),
                "World Model Integration": self._world_model_integration(situation, comparison),
                "DNA Integration": self._dna_integration(situation),
                "Memory Integration": self._memory_integration(situation),
                "Meta Cognition": self._meta_cognition(situation),
                "Overall Situation Quality": round(quality, 3),
            }
        }
        self.situations.append(situation)
        self.situation_reports.append(report)
        return report

    def compare_situations(
        self,
        previous: CognitiveSituation | None,
        current: CognitiveSituation,
    ) -> dict[str, Any]:
        if previous is None:
            return {
                "Similarity": 0.0,
                "Novelty": current.novelty_estimate,
                "Progress": current.situation_readiness,
                "Regression": 0.0,
                "Knowledge Gain": current.objects.get("knowledge_count", 0),
                "Truth Gain": current.objects.get("truth_candidate_count", 0),
                "Memory Gain": current.objects.get("memory_entry_count", 0),
                "Search Efficiency": current.execution_context.get("search_efficiency", 0.0),
                "Goal Advancement": current.goals.get("Estimated Completion", 0.0),
                "Learning Signal": "situation_birth",
            }
        same_goal = previous.current_goal == current.current_goal
        similarity = _clamp(
            (0.35 if same_goal else 0.0)
            + (1.0 - abs(previous.confidence - current.confidence)) * 0.25
            + (1.0 - abs(previous.task_complexity - current.task_complexity)) * 0.2
            + (1.0 - abs(previous.overall_situation_quality - current.overall_situation_quality)) * 0.2
        )
        progress = _clamp(
            current.goals.get("Estimated Completion", 0.0)
            - previous.goals.get("Estimated Completion", 0.0)
            + 0.5
        )
        regression = _clamp(previous.overall_situation_quality - current.overall_situation_quality)
        return {
            "Similarity": round(similarity, 3),
            "Novelty": round(_clamp(1.0 - similarity), 3),
            "Progress": round(progress, 3),
            "Regression": round(regression, 3),
            "Knowledge Gain": max(
                0,
                current.objects.get("knowledge_count", 0)
                - previous.objects.get("knowledge_count", 0),
            ),
            "Truth Gain": max(
                0,
                current.objects.get("truth_candidate_count", 0)
                - previous.objects.get("truth_candidate_count", 0),
            ),
            "Memory Gain": max(
                0,
                current.objects.get("memory_entry_count", 0)
                - previous.objects.get("memory_entry_count", 0),
            ),
            "Search Efficiency": current.execution_context.get("search_efficiency", 0.0),
            "Goal Advancement": current.goals.get("Estimated Completion", 0.0),
            "Learning Signal": "situation_progress" if progress >= 0.5 else "situation_regression",
        }

    def predict_next_situation(
        self,
        situation: CognitiveSituation,
        comparison: Mapping[str, Any],
    ) -> dict[str, Any]:
        uncertainty_count = len(situation.uncertainty.get("Knowledge Gaps", []))
        truth_ready = situation.confidence >= 0.7 and uncertainty_count <= 2
        memory_ready = situation.goals.get("Estimated Completion", 0.0) >= 0.75
        return {
            "Likely Next Situation": (
                "truth_validation"
                if truth_ready
                else "evidence_expansion"
            ),
            "Expected Missing Knowledge": situation.uncertainty.get("Knowledge Gaps", []),
            "Expected Truth Promotion": truth_ready,
            "Expected Memory Promotion": memory_ready,
            "Expected Policy Changes": (
                ["increase_search_policy"]
                if uncertainty_count >= 3
                else []
            ),
            "Expected Decision Changes": (
                ["re-evaluate_decision_after_evidence"]
                if situation.risk["Overall Situation Risk"] >= 0.55
                else []
            ),
            "Expected Search Expansion": situation.uncertainty["Incomplete Evidence"] > 0.4,
            "Prediction Confidence": round(
                _clamp((situation.confidence + situation.situation_stability) / 2.0),
                3,
            ),
        }

    def build_report(self) -> dict[str, Any]:
        latest = self.situation_reports[-1] if self.situation_reports else {}
        return {
            "COGNITIVE_SITUATION_REPORT": latest.get("COGNITIVE_SITUATION_REPORT", {}),
            "situation_count": len(self.situations),
            "situation_history": [
                situation.as_dict()
                for situation in self.situations[-20:]
            ],
        }

    def reset(self) -> None:
        self.situations.clear()
        self.situation_reports.clear()

    def _fuse(self, artifacts: Mapping[str, Any]) -> dict[str, Any]:
        executive = dict(artifacts.get("WORLD_GOVERNANCE_EXECUTIVE_REPORT") or {})
        policy = dict(artifacts.get("COGNITIVE_POLICY_REPORT") or {})
        decision = dict(artifacts.get("COGNITIVE_DECISION_INTELLIGENCE_REPORT") or {})
        analytics = dict(artifacts.get("COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT") or {})
        intent = dict(executive.get("Execution Intent") or {})
        task_analysis = dict(intent.get("task_analysis") or {})
        execution_deviations = dict(executive.get("Execution Deviations") or {})
        policy_task = dict(policy.get("Task Profile") or {})
        confidence_values = list(execution_deviations.get("confidence_evolution") or [])
        decision_confidence = _nested(decision, "Decision Confidence", "Decision Confidence", default=policy.get("Policy Confidence", 0.0))
        policy_confidence = policy.get("Policy Confidence", 0.0)
        analytics_kpis = dict(analytics.get("Cognitive KPIs") or {})
        truth = dict(executive.get("Truth Decisions") or {})
        memory = dict(executive.get("Memory Decisions") or {})
        knowledge = dict(executive.get("Knowledge Decisions") or {})
        return {
            "raw": dict(artifacts),
            "task_identity": str(intent.get("goal") or artifacts.get("goal") or "unknown_task"),
            "current_goal": str(intent.get("goal") or "governed_cognitive_execution"),
            "current_stage": self._current_stage(executive, analytics),
            "execution_profile": str(intent.get("execution_profile") or "adaptive"),
            "task_complexity": _score(task_analysis.get("difficulty", policy_task.get("difficulty", 0.5))),
            "novelty": _score(task_analysis.get("novelty", policy_task.get("novelty", 0.0))),
            "progress": _score(execution_deviations.get("execution_progress", 0.0)),
            "resource_consumption": _score(execution_deviations.get("resource_consumption", 0.0)),
            "confidence_values": confidence_values,
            "reasoning_confidence": _average(confidence_values),
            "search_confidence": _score(analytics_kpis.get("Search Intelligence", 0.0)),
            "concept_confidence": _score(analytics_kpis.get("Concept Intelligence", 0.0)),
            "evidence_confidence": _score(analytics_kpis.get("Evidence Intelligence", execution_deviations.get("evidence_growth", 0.0) / 5.0)),
            "truth_confidence": _score(analytics_kpis.get("Truth Intelligence", _average(confidence_values))),
            "memory_confidence": _score(analytics_kpis.get("Memory Intelligence", 0.0)),
            "decision_confidence": _score(decision_confidence),
            "policy_confidence": _score(policy_confidence),
            "knowledge_confidence": _score(analytics_kpis.get("Knowledge Intelligence", execution_deviations.get("knowledge_density", 0.0))),
            "evidence": {
                "evidence_growth": execution_deviations.get("evidence_growth", 0.0),
                "evidence_health": analytics.get("Evidence Health", {}),
            },
            "knowledge": {
                "knowledge_density": execution_deviations.get("knowledge_density", 0.0),
                "knowledge_decisions": knowledge,
                "knowledge_health": analytics.get("Knowledge Health", {}),
            },
            "truth": {
                "truth_growth": execution_deviations.get("truth_growth", 0.0),
                "truth_decisions": truth,
                "truth_health": analytics.get("Truth Health", {}),
            },
            "memory": {
                "memory_decisions": memory,
                "memory_health": analytics.get("Memory Health", {}),
            },
            "policies": {
                "selected_policy": _nested(policy, "Selected Policy", "policy", "policy_id", default=None),
                "policy_confidence": policy_confidence,
                "runtime_schedule": policy.get("Runtime Schedule", {}),
            },
            "decisions": {
                "selected_decision": _nested(decision, "Selected Decision", "Decision", "Decision ID", default=None),
                "decision_confidence": decision_confidence,
                "decision_utility": _nested(decision, "Selected Decision", "Decision Utility", default=0.0),
            },
            "analytics": analytics,
            "activated_runtimes": list(executive.get("Activated Runtimes") or []),
            "runtime_budgets": dict(executive.get("Runtime Budgets") or {}),
            "recommendations": list(analytics.get("Recommended Actions") or []),
            "risks": list(analytics.get("Root Cause Analysis") or []),
        }

    def _execution_context(self, fused: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "execution_profile": fused["execution_profile"],
            "current_stage": fused["current_stage"],
            "activated_runtime_count": len(fused["activated_runtimes"]),
            "execution_progress": fused["progress"],
            "resource_consumption": fused["resource_consumption"],
            "search_efficiency": _nested(fused["analytics"], "Search Health", "Search Efficiency", default=0.0),
            "runtime_budgets": fused["runtime_budgets"],
        }

    def _situational_objects(self, fused: Mapping[str, Any]) -> dict[str, Any]:
        runtimes = fused["activated_runtimes"]
        return {
            "current_objects": list(fused.get("raw", {}).get("objects", [])),
            "detected_entities": [
                runtime.get("runtime_id")
                for runtime in runtimes
                if runtime.get("runtime_id")
            ],
            "program_count": int(fused.get("raw", {}).get("program_count", 0)),
            "concept_count": int(fused.get("raw", {}).get("concept_count", 0)),
            "evidence_count": int(float(fused["evidence"].get("evidence_growth", 0.0))),
            "knowledge_count": int(float(fused["knowledge"].get("knowledge_density", 0.0)) * 10),
            "truth_candidate_count": int(float(fused["truth"].get("truth_growth", 0.0))),
            "memory_entry_count": int(
                1
                if fused["memory"].get("memory_decisions", {}).get("memory_update_allowed")
                else 0
            ),
            "goals": [fused["current_goal"]],
            "constraints": self._constraints(fused),
            "unknown_elements": [],
            "conflicts": self._conflicts(fused),
        }

    def _relations(self, fused: Mapping[str, Any]) -> list[dict[str, Any]]:
        relations = []
        selected_policy = fused["policies"].get("selected_policy")
        selected_decision = fused["decisions"].get("selected_decision")
        if selected_policy and selected_decision:
            relations.append({
                "source": selected_decision,
                "target": selected_policy,
                "relation": "decision_selected_policy",
            })
        for runtime in fused["activated_runtimes"]:
            runtime_id = runtime.get("runtime_id")
            if runtime_id:
                relations.append({
                    "source": selected_policy or "governance",
                    "target": runtime_id,
                    "relation": "policy_activated_runtime",
                })
        return relations

    def _transformation_awareness(self, fused: Mapping[str, Any]) -> dict[str, Any]:
        raw = fused.get("raw", {})
        observed = list(raw.get("observed_transformations", []))
        candidates = list(raw.get("candidate_transformations", []))
        rejected = list(raw.get("rejected_transformations", []))
        chain = observed + candidates
        return {
            "Observed Transformations": observed,
            "Candidate Transformations": candidates,
            "Rejected Transformations": rejected,
            "Transformation Chains": chain,
            "Transformation Dependencies": [
                {"source": chain[index - 1], "target": item}
                for index, item in enumerate(chain)
                if index > 0
            ],
            "Transformation Confidence": fused["reasoning_confidence"],
            "Transformation Stability": _clamp(1.0 - len(rejected) * 0.1),
            "Transformation Evolution": "active" if chain else "not_observed",
        }

    def _goal_model(self, fused: Mapping[str, Any]) -> dict[str, Any]:
        progress = fused["progress"]
        return {
            "Current Objective": fused["current_goal"],
            "Remaining Objectives": ["truth_validation", "memory_promotion"]
            if progress < 0.8
            else [],
            "Completed Objectives": ["policy_selection", "decision_reasoning"],
            "Blocked Objectives": self._blocked_objectives(fused),
            "Abandoned Objectives": [],
            "Estimated Completion": round(progress, 3),
            "Goal Priority": _score(_nested(fused["raw"], "COGNITIVE_POLICY_REPORT", "Task Profile", "priority", default=0.5)),
            "Goal Confidence": round(
                _clamp((fused["policy_confidence"] + fused["decision_confidence"]) / 2.0),
                3,
            ),
        }

    def _uncertainty_model(self, fused: Mapping[str, Any]) -> dict[str, Any]:
        unknowns = []
        if fused["concept_confidence"] < 0.45:
            unknowns.append("unknown_concepts")
        if fused["evidence_confidence"] < 0.45:
            unknowns.append("incomplete_evidence")
        if fused["truth_confidence"] < 0.45:
            unknowns.append("weak_truth")
        if fused["decision_confidence"] < 0.45:
            unknowns.append("low_confidence_decision")
        if fused["policy_confidence"] < 0.45:
            unknowns.append("unresolved_policy")
        knowledge_gaps = []
        if fused["knowledge_confidence"] < 0.5:
            knowledge_gaps.append("knowledge_support_low")
        if fused["memory_confidence"] < 0.4:
            knowledge_gaps.append("memory_context_missing")
        return {
            "Unknown Concepts": "unknown_concepts" in unknowns,
            "Incomplete Evidence": round(_clamp(1.0 - fused["evidence_confidence"]), 3),
            "Weak Truth": "weak_truth" in unknowns,
            "Conflicting Knowledge": bool(self._conflicts(fused)),
            "Uncertain Programs": fused["reasoning_confidence"] < 0.45,
            "Missing Transformations": not fused.get("raw", {}).get("observed_transformations"),
            "Low Confidence Decisions": "low_confidence_decision" in unknowns,
            "Unresolved Policies": "unresolved_policy" in unknowns,
            "Knowledge Gaps": knowledge_gaps,
            "Uncertainty Items": unknowns + knowledge_gaps,
            "Uncertainty Score": round(_clamp(len(unknowns + knowledge_gaps) / 8.0), 3),
        }

    def _situation_confidence(
        self,
        fused: Mapping[str, Any],
        uncertainty: Mapping[str, Any],
    ) -> float:
        values = [
            fused["concept_confidence"],
            fused["evidence_confidence"],
            fused["truth_confidence"],
            fused["memory_confidence"],
            fused["decision_confidence"],
            fused["policy_confidence"],
            fused["knowledge_confidence"],
            fused["reasoning_confidence"],
            fused["search_confidence"],
        ]
        return _clamp(_average(values) * (1.0 - uncertainty["Uncertainty Score"] * 0.35))

    def _resource_awareness(self, fused: Mapping[str, Any]) -> dict[str, Any]:
        budgets = fused["runtime_budgets"].get("global_budget", {})
        return {
            "Available Resources": {
                key: value
                for key, value in budgets.items()
            },
            "Consumed Resources": fused["resource_consumption"],
            "Search Budget": budgets.get("search_budget"),
            "Reasoning Budget": budgets.get("reasoning_budget"),
            "Memory Budget": budgets.get("memory_budget"),
            "Truth Budget": budgets.get("truth_budget"),
            "Time Budget": budgets.get("execution_time"),
            "Thermal Budget": budgets.get("acsc_budget"),
            "Execution Capacity": round(_clamp(1.0 - fused["resource_consumption"]), 3),
        }

    def _risk_awareness(self, fused: Mapping[str, Any]) -> dict[str, Any]:
        analytics = fused["analytics"]
        decision_risk = _nested(
            fused["raw"],
            "COGNITIVE_DECISION_INTELLIGENCE_REPORT",
            "Risk Analysis",
            "Execution Risk",
            default=0.0,
        )
        risk = {
            "Knowledge Risk": _clamp(1.0 - fused["knowledge_confidence"]),
            "Reasoning Risk": _clamp(1.0 - fused["reasoning_confidence"]),
            "Search Risk": _clamp(1.0 - fused["search_confidence"]),
            "Truth Risk": _clamp(1.0 - fused["truth_confidence"]),
            "Memory Risk": _clamp(1.0 - fused["memory_confidence"]),
            "Decision Risk": _score(decision_risk),
            "Policy Risk": _clamp(1.0 - fused["policy_confidence"]),
            "Governance Risk": _clamp(1.0 - _nested(analytics, "Cognitive KPIs", "Governance Intelligence", default=0.0)),
            "Execution Risk": _clamp(1.0 - _nested(analytics, "Cognitive KPIs", "Execution Intelligence", default=0.0)),
        }
        risk["Overall Situation Risk"] = round(
            _average(list(risk.values())),
            3,
        )
        return {key: round(value, 3) for key, value in risk.items()}

    def _situation_stability(
        self,
        fused: Mapping[str, Any],
        risk: Mapping[str, Any],
        previous: CognitiveSituation | None,
    ) -> float:
        confidence_stability = _clamp(1.0 - risk["Overall Situation Risk"] * 0.5)
        if previous is None:
            return confidence_stability
        continuity = 1.0 if previous.current_goal == fused["current_goal"] else 0.5
        return _clamp(confidence_stability * 0.7 + continuity * 0.3)

    def _situation_completeness(
        self,
        objects: Mapping[str, Any],
        uncertainty: Mapping[str, Any],
        fused: Mapping[str, Any],
    ) -> float:
        coverage = 0.0
        coverage += 0.15 if objects["detected_entities"] else 0.0
        coverage += 0.15 if fused["policies"].get("selected_policy") else 0.0
        coverage += 0.15 if fused["decisions"].get("selected_decision") else 0.0
        coverage += 0.15 if fused["evidence"].get("evidence_growth", 0.0) else 0.0
        coverage += 0.15 if fused["truth"].get("truth_growth", 0.0) else 0.0
        coverage += 0.15 if fused["analytics"] else 0.0
        coverage += 0.10 if fused["runtime_budgets"] else 0.0
        return _clamp(coverage * (1.0 - uncertainty["Uncertainty Score"] * 0.25))

    def _situation_readiness(
        self,
        confidence: float,
        stability: float,
        completeness: float,
        risk: Mapping[str, Any],
    ) -> float:
        return _clamp(
            confidence * 0.35
            + stability * 0.25
            + completeness * 0.25
            + (1.0 - risk["Overall Situation Risk"]) * 0.15
        )

    def _recommendations(
        self,
        fused: Mapping[str, Any],
        uncertainty: Mapping[str, Any],
        risk: Mapping[str, Any],
        readiness: float,
    ) -> list[dict[str, Any]]:
        recommendations = list(fused.get("recommendations") or [])
        if uncertainty["Incomplete Evidence"] > 0.55:
            recommendations.append({
                "action": "continue evidence collection",
                "evidence": "situation evidence is incomplete",
                "domain": "situation_awareness",
            })
        if risk["Truth Risk"] > 0.55:
            recommendations.append({
                "action": "continue truth validation before memory promotion",
                "evidence": "truth confidence is weak in the current situation",
                "domain": "truth_context",
            })
        if readiness >= 0.7:
            recommendations.append({
                "action": "allow governance to consume unified situation",
                "evidence": "situation readiness is sufficient",
                "domain": "world_governance",
            })
        return recommendations

    def _situation_graph(self, situation: CognitiveSituation) -> dict[str, Any]:
        nodes = [
            {"node_id": situation.situation_id, "node_type": "situation"},
            {"node_id": situation.current_goal, "node_type": "goal"},
        ]
        edges = [
            {
                "source": situation.situation_id,
                "target": situation.current_goal,
                "relation": "situation_has_goal",
            }
        ]
        for entity in situation.objects.get("detected_entities", []):
            nodes.append({"node_id": entity, "node_type": "runtime"})
            edges.append({
                "source": situation.situation_id,
                "target": entity,
                "relation": "situation_contains_runtime",
            })
        return {
            "graph_type": "cognitive_situation_graph",
            "nodes": nodes,
            "edges": edges + situation.relations,
        }

    def _timeline(self, situation: CognitiveSituation) -> list[dict[str, Any]]:
        timeline = [
            {
                "situation_id": item.situation_id,
                "timestamp": item.timestamp,
                "goal": item.current_goal,
                "quality": round(item.overall_situation_quality, 3),
            }
            for item in self.situations[-10:]
        ]
        timeline.append({
            "situation_id": situation.situation_id,
            "timestamp": situation.timestamp,
            "goal": situation.current_goal,
            "quality": round(situation.overall_situation_quality, 3),
        })
        return timeline

    def _evolution_state(
        self,
        situation: CognitiveSituation,
        comparison: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not self.situations:
            state = "birth"
        elif situation.goals["Estimated Completion"] >= 1.0:
            state = "completion"
        elif comparison.get("Regression", 0.0) > 0.25:
            state = "transition"
        elif situation.situation_stability >= 0.75:
            state = "stabilization"
        else:
            state = "growth"
        return {
            "Situation Birth": state == "birth",
            "Situation Growth": state == "growth",
            "Situation Stabilization": state == "stabilization",
            "Situation Transition": state == "transition",
            "Situation Split": False,
            "Situation Merge": False,
            "Situation Resolution": state in {"resolution", "completion"},
            "Situation Completion": state == "completion",
            "Current Evolution State": state,
        }

    def _executive_summary(
        self,
        situation: CognitiveSituation,
        fused: Mapping[str, Any],
        uncertainty: Mapping[str, Any],
    ) -> str:
        unknowns = uncertainty.get("Uncertainty Items", [])
        primary_uncertainty = unknowns[0] if unknowns else "none"
        action = (
            situation.recommendations[0]["action"]
            if situation.recommendations
            else "continue governed execution"
        )
        return (
            f"Current Situation: The system is pursuing {situation.current_goal} "
            f"with {len(situation.objects.get('detected_entities', []))} active runtimes. "
            f"Evidence growth is {fused['evidence'].get('evidence_growth', 0.0)} and "
            f"truth growth is {fused['truth'].get('truth_growth', 0.0)}. "
            f"Situation confidence is {round(situation.confidence, 3)}. "
            f"Primary uncertainty remains {primary_uncertainty}. "
            f"Recommended action: {action}."
        )

    def _explainability(
        self,
        situation: CognitiveSituation,
        fused: Mapping[str, Any],
        uncertainty: Mapping[str, Any],
    ) -> dict[str, Any]:
        blocked = situation.goals.get("Blocked Objectives", [])
        next_objective = (
            "resolve uncertainty"
            if uncertainty["Uncertainty Items"]
            else "advance governed execution"
        )
        return {
            "What is happening?": f"{situation.current_goal} is in {situation.current_stage}.",
            "Why is it happening?": "World Governance selected a policy and decision, then runtimes produced artifacts that were fused into this situation.",
            "What remains unknown?": uncertainty["Uncertainty Items"],
            "What is the next objective?": next_objective,
            "Why was this objective selected?": "It follows from current uncertainty, risk, and readiness.",
            "What is preventing completion?": blocked,
            "What should happen next?": [
                item["action"]
                for item in situation.recommendations
            ],
        }

    def _world_model_integration(
        self,
        situation: CognitiveSituation,
        comparison: Mapping[str, Any],
    ) -> dict[str, Any]:
        category = "resolved_situation" if situation.situation_readiness >= 0.8 else "observed_situation"
        if situation.novelty_estimate >= 0.7:
            category = "novel_situation"
        if comparison.get("Regression", 0.0) > 0.25:
            category = "failed_or_regressed_situation"
        return {
            "world_model_update_type": category,
            "situation_based_world_model": True,
            "store_observed_situation": True,
            "store_recurring_situation": comparison.get("Similarity", 0.0) >= 0.75,
            "store_typical_situation": situation.situation_stability >= 0.75,
        }

    def _dna_integration(self, situation: CognitiveSituation) -> dict[str, Any]:
        return {
            "dna_evolves_from_situational_experience": True,
            "context_traits": {
                "high_uncertainty": situation.uncertainty["Uncertainty Score"] >= 0.5,
                "reuse_memory": situation.memory_context_available if hasattr(situation, "memory_context_available") else situation.objects.get("memory_entry_count", 0) > 0,
                "increase_exploration": situation.uncertainty["Incomplete Evidence"] > 0.55,
                "decision_stability": situation.situation_stability,
            },
            "evolution_allowed": situation.overall_situation_quality >= 0.75,
        }

    def _memory_integration(self, situation: CognitiveSituation) -> dict[str, Any]:
        return {
            "store_complete_cognitive_episode": True,
            "memory_key": situation.situation_id,
            "future_reasoning_recalls_situation": True,
            "persistence_recommended": situation.overall_situation_quality >= 0.55,
        }

    def _meta_cognition(self, situation: CognitiveSituation) -> dict[str, Any]:
        return {
            "Did the system understand the situation?": situation.overall_situation_quality >= 0.55,
            "Was the situation complete?": situation.situation_completeness >= 0.65,
            "Was important context missing?": bool(situation.uncertainty["Knowledge Gaps"]),
            "Was uncertainty correctly estimated?": True,
            "Did governance react appropriately?": situation.situation_readiness >= 0.5,
            "Meta Recommendation": (
                "continue situation-aware governance"
                if situation.overall_situation_quality >= 0.55
                else "collect additional context before committing"
            ),
        }

    def _current_stage(self, executive: Mapping[str, Any], analytics: Mapping[str, Any]) -> str:
        termination = dict(executive.get("Execution Termination") or {})
        if termination.get("terminate_execution"):
            return "terminated"
        if analytics:
            return "analytics_interpreted"
        if executive:
            return "execution_governed"
        return "situation_birth"

    def _constraints(self, fused: Mapping[str, Any]) -> list[str]:
        constraints = []
        if fused["resource_consumption"] >= 0.8:
            constraints.append("resource_pressure")
        if fused["truth_confidence"] < 0.45:
            constraints.append("truth_confidence_low")
        if fused["evidence_confidence"] < 0.45:
            constraints.append("evidence_incomplete")
        return constraints

    def _conflicts(self, fused: Mapping[str, Any]) -> list[str]:
        conflicts = []
        truth_health = fused["truth"].get("truth_health", {})
        if truth_health.get("Promotion Rate", 1.0) < 0.25 and truth_health.get("Truth Candidates", 0) >= 5:
            conflicts.append("truth_promotion_bottleneck")
        if fused["policy_confidence"] < 0.4 and fused["decision_confidence"] > 0.7:
            conflicts.append("policy_decision_confidence_mismatch")
        return conflicts

    def _blocked_objectives(self, fused: Mapping[str, Any]) -> list[str]:
        blocked = []
        if fused["evidence_confidence"] < 0.45:
            blocked.append("truth_promotion")
        if fused["truth_confidence"] < 0.45:
            blocked.append("memory_promotion")
        return blocked


def _score(value: Any) -> float:
    return _clamp(value)


def _clamp(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _average(values: Any) -> float:
    if isinstance(values, (int, float)):
        return _score(values)
    if not values:
        return 0.0
    numbers = [_score(value) for value in values]
    return sum(numbers) / max(1, len(numbers))


def _nested(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return default
        current = current.get(key)
    return default if current is None else current


cognitive_situation_awareness_engine = CognitiveSituationAwarenessEngine()


__all__ = [
    "SITUATION_STATES",
    "CognitiveSituation",
    "CognitiveSituationAwarenessEngine",
    "cognitive_situation_awareness_engine",
]
