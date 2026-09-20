"""Reflection Engine for completed Cognitive Episodes.

The engine does not execute cognition. It analyzes a closed episode and turns
the episode record into reflective understanding before the episode can be
treated as experience-ready knowledge.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


REFLECTION_DIMENSIONS = (
    "Reasoning",
    "Search",
    "Concept Formation",
    "Program Synthesis",
    "Evidence",
    "Truth",
    "Decision Making",
    "Resource Allocation",
    "Execution Strategy",
    "Governance Decisions",
    "Learning Behavior",
)

REFLECTION_QUESTIONS = (
    "What happened?",
    "Why did it happen?",
    "Which reasoning path was chosen?",
    "Which alternatives were rejected?",
    "Which assumptions proved correct?",
    "Which assumptions failed?",
    "Which evidence mattered most?",
    "Which concepts were unnecessary?",
    "Which search paths were inefficient?",
    "Which transformations produced value?",
    "Which decisions reduced uncertainty?",
    "Which decisions increased uncertainty?",
    "What should be repeated?",
    "What should never be repeated?",
)


@dataclass(frozen=True)
class ReflectionObject:
    reflection_id: str
    episode_id: str
    execution_id: str
    reflection_timestamp: str
    reflection_version: int
    reflection_confidence: float
    reflection_quality: float
    reflection_summary: str
    reflection_status: str
    dimensions: dict[str, dict[str, Any]] = field(default_factory=dict)
    answers: dict[str, Any] = field(default_factory=dict)
    second_order_cognition: dict[str, Any] = field(default_factory=dict)
    causal_analysis: dict[str, Any] = field(default_factory=dict)
    strategy_analysis: dict[str, Any] = field(default_factory=dict)
    learning_value: dict[str, Any] = field(default_factory=dict)
    self_improvement_report: dict[str, Any] = field(default_factory=dict)
    reflection_memory_update: dict[str, Any] = field(default_factory=dict)
    reflective_synthesis_report: dict[str, Any] = field(default_factory=dict)
    abstraction_registry_update: dict[str, Any] = field(default_factory=dict)
    reflection_intelligence_report: dict[str, Any] = field(default_factory=dict)
    reflection_knowledge_graph: dict[str, Any] = field(default_factory=dict)
    reflection_report: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReflectionRegistry:
    """In-memory reflection registry keyed by episode and reflection identity."""

    def __init__(self) -> None:
        self.reflections: dict[str, ReflectionObject] = {}
        self.episode_reflection_index: dict[str, str] = {}

    def upsert(self, reflection: ReflectionObject) -> ReflectionObject:
        self.reflections[reflection.reflection_id] = reflection
        self.episode_reflection_index[reflection.episode_id] = reflection.reflection_id
        return reflection

    def get(self, reflection_id: str) -> ReflectionObject | None:
        return self.reflections.get(str(reflection_id))

    def for_episode(self, episode_id: str) -> ReflectionObject | None:
        reflection_id = self.episode_reflection_index.get(str(episode_id))
        return self.reflections.get(reflection_id) if reflection_id else None


class ReflectionEngine:
    """Analyze completed cognition and produce mandatory reflection records."""

    system_name = "reflection_engine"

    def __init__(self, registry: ReflectionRegistry | None = None) -> None:
        self.registry = registry or ReflectionRegistry()

    def reflect(
        self,
        *,
        episode: Mapping[str, Any],
        objects: Iterable[Mapping[str, Any]] | None = None,
    ) -> ReflectionObject:
        episode = dict(episode or {})
        object_list = [dict(obj) for obj in (objects or [])]
        episode_id = str(episode.get("episode_id") or "episode:unknown")
        execution_id = str(episode.get("execution_id") or "execution:unknown")
        existing = self.registry.for_episode(episode_id)
        reflection_id = (
            existing.reflection_id
            if existing is not None
            else f"reflection:{uuid5(NAMESPACE_URL, episode_id).hex[:16]}"
        )
        dimensions = _dimension_analysis(episode, object_list)
        answers = _answers(episode, object_list, dimensions)
        second_order = _second_order_cognition(episode, object_list, dimensions, answers)
        causal = _causal_analysis(episode, object_list, dimensions)
        strategy = _strategy_analysis(episode, object_list, dimensions, causal)
        learning_value = _learning_value(episode, dimensions, strategy, causal, second_order)
        historical_reflections = [
            reflection
            for reflection in self.registry.reflections.values()
            if reflection.episode_id != episode_id
        ]
        self_improvement = _self_improvement_report(
            episode,
            object_list,
            dimensions,
            second_order,
            causal,
            strategy,
            learning_value,
            historical_reflections,
        )
        synthesis = _reflective_synthesis_report(
            episode,
            object_list,
            dimensions,
            answers,
            second_order,
            causal,
            strategy,
            learning_value,
            self_improvement,
            historical_reflections,
        )
        intelligence = _reflection_intelligence_report(
            episode,
            dimensions,
            second_order,
            causal,
            strategy,
            learning_value,
            self_improvement,
            synthesis,
            historical_reflections,
        )
        report = _reflection_report(
            episode,
            dimensions,
            answers,
            second_order,
            causal,
            strategy,
            learning_value,
            self_improvement,
            synthesis,
            intelligence,
        )
        confidence = _reflection_confidence(episode, dimensions)
        quality = _reflection_quality(episode, dimensions, answers)
        status = "COMPLETED" if episode.get("episode_status") != "EMPTY" else "EMPTY"
        reflection = ReflectionObject(
            reflection_id=reflection_id,
            episode_id=episode_id,
            execution_id=execution_id,
            reflection_timestamp=datetime.now(timezone.utc).isoformat(),
            reflection_version=(existing.reflection_version + 1) if existing else 1,
            reflection_confidence=confidence,
            reflection_quality=quality,
            reflection_summary=_summary(episode, dimensions, answers),
            reflection_status=status,
            dimensions=dimensions,
            answers=answers,
            second_order_cognition=second_order,
            causal_analysis=causal,
            strategy_analysis=strategy,
            learning_value=learning_value,
            self_improvement_report=self_improvement,
            reflection_memory_update=self_improvement.get("Reflection Memory Updates", {}),
            reflective_synthesis_report=synthesis,
            abstraction_registry_update=synthesis.get("Reflection Abstraction Registry", {}),
            reflection_intelligence_report=intelligence,
            reflection_knowledge_graph=intelligence.get("Reflection Knowledge Graph", {}),
            reflection_report=report,
        )
        return self.registry.upsert(reflection)

    def report(self) -> dict[str, Any]:
        reflections = list(self.registry.reflections.values())
        return {
            "REFLECTION_ENGINE_REPORT": True,
            "system": self.system_name,
            "reflections_created": len(reflections),
            "episodes_reflected": len(self.registry.episode_reflection_index),
            "mandatory_reflection_enforced": True,
            "experience_requires_reflection": True,
            "average_reflection_confidence": _average(
                reflection.reflection_confidence for reflection in reflections
            ),
            "average_reflection_quality": _average(
                reflection.reflection_quality for reflection in reflections
            ),
            "reflection_statuses": _distribution(
                reflection.reflection_status for reflection in reflections
            ),
            "dimension_coverage": {
                dimension: sum(
                    1
                    for reflection in reflections
                    if reflection.dimensions.get(dimension, {}).get("evaluated")
                )
                for dimension in REFLECTION_DIMENSIONS
            },
            "second_order_cognition_available": any(
                bool(reflection.second_order_cognition) for reflection in reflections
            ),
            "causal_analysis_available": any(
                bool(reflection.causal_analysis) for reflection in reflections
            ),
            "average_learning_value": _average(
                reflection.learning_value.get("learning_value_score", 0.0)
                for reflection in reflections
            ),
            "reusable_strategies_detected": sum(
                1
                for reflection in reflections
                if reflection.strategy_analysis.get("strategy_reuse", 0.0) > 0
            ),
            "self_improvement_reports_created": sum(
                1 for reflection in reflections
                if reflection.self_improvement_report.get("SELF_IMPROVEMENT_REPORT")
            ),
            "adaptive_learning_signals_created": sum(
                len(reflection.self_improvement_report.get("Learning Signals", []))
                for reflection in reflections
            ),
            "reflection_memory_size": len(reflections),
            "reflection_memory_available": bool(reflections),
            "average_actionability": _average(
                reflection.self_improvement_report
                .get("Reflection Quality Metrics", {})
                .get("actionability", 0.0)
                for reflection in reflections
            ),
            "reflective_synthesis_reports_created": sum(
                1 for reflection in reflections
                if reflection.reflective_synthesis_report.get("REFLECTIVE_SYNTHESIS_REPORT")
            ),
            "experience_candidates_created": sum(
                len(reflection.reflective_synthesis_report.get("Experience Candidates", []))
                for reflection in reflections
            ),
            "abstractions_created": sum(
                len(reflection.reflective_synthesis_report.get("Abstractions Created", []))
                for reflection in reflections
            ),
            "lessons_extracted": sum(
                len(reflection.reflective_synthesis_report.get("Lessons Extracted", []))
                for reflection in reflections
            ),
            "reflection_intelligence_reports_created": sum(
                1 for reflection in reflections
                if reflection.reflection_intelligence_report.get("REFLECTION_INTELLIGENCE_REPORT")
            ),
            "executive_recommendations_created": sum(
                len(reflection.reflection_intelligence_report.get("Executive Recommendations", []))
                for reflection in reflections
            ),
            "adaptive_signals_created": sum(
                len(reflection.reflection_intelligence_report.get("Adaptive Signals", []))
                for reflection in reflections
            ),
            "reflection_knowledge_graph_nodes": sum(
                reflection.reflection_knowledge_graph.get("node_count", 0)
                for reflection in reflections
            ),
        }


def _dimension_analysis(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    stats = dict(episode.get("statistics") or {})
    quality = dict(episode.get("quality") or {})
    graph = dict(episode.get("episode_graph") or {})
    timeline = list(episode.get("timeline") or [])
    stages = dict(episode.get("stages") or {})
    object_types = [str(obj.get("object_type", "UNKNOWN")) for obj in objects]
    confidence_values = [obj.get("object_confidence", obj.get("confidence", 0.0)) for obj in objects]
    evidence_quality = quality.get("evidence_quality", 0.0)
    truth_quality = quality.get("truth_quality", 0.0)
    reasoning_count = stats.get("reasoning_count", 0)
    search_count = stats.get("search_count", 0)
    concept_count = stats.get("concept_count", 0)
    program_count = stats.get("program_count", 0)
    evidence_count = stats.get("evidence_count", 0)
    truth_count = stats.get("truth_count", 0)
    decision_count = stats.get("decision_count", 0)
    object_count = max(stats.get("object_count", len(objects)), 1)
    edge_count = graph.get("edge_count", 0)
    duration = float(episode.get("episode_duration", 0.0) or 0.0)
    complexity = float(episode.get("episode_complexity", quality.get("episode_complexity", 0.0)) or 0.0)
    resource_load = clamp((duration / max(object_count, 1)) + (complexity * 0.5))
    confidence = _average(confidence_values)
    dimensions = {
        "Reasoning": {
            "evaluated": True,
            "depth": reasoning_count,
            "efficiency": clamp(1.0 - (reasoning_count / max(object_count * 2, 1))),
            "continuity": clamp(graph.get("temporal_flow_edges", 0) / max(len(timeline), 1)),
            "branching": graph.get("reasoning_dependency_edges", 0),
            "convergence": clamp(truth_count / max(reasoning_count, 1)),
            "stability": confidence,
            "novelty": quality.get("novelty", 0.0),
        },
        "Search": {
            "evaluated": True,
            "route_quality": clamp(search_count / max(search_count + stats.get("failure_count", 0), 1)),
            "exploration": search_count,
            "pruning": clamp(1.0 - (search_count / max(object_count, 1))),
            "diversity": _ratio({"SEARCH_ROUTE"}, object_types),
            "dead_ends": stats.get("failure_count", 0),
            "convergence": clamp(evidence_count / max(search_count, 1)),
        },
        "Concept Formation": {
            "evaluated": True,
            "useful_concepts": concept_count,
            "unused_concepts": max(concept_count - program_count - truth_count, 0),
            "repeated_concepts": _repeated(objects, "CONCEPT"),
            "novel_concepts": _novel(objects, "CONCEPT"),
            "generalized_concepts": sum(
                1 for obj in objects
                if obj.get("object_type") == "CONCEPT" and obj.get("generalization_score", 0.0)
            ),
            "concept_redundancy": clamp(max(concept_count - edge_count, 0) / max(concept_count, 1)),
        },
        "Program Synthesis": {
            "evaluated": True,
            "program_usefulness": clamp(program_count / max(program_count + stats.get("failure_count", 0), 1)),
            "program_reuse": sum(1 for obj in objects if obj.get("object_type") == "PROGRAM" and obj.get("reuse_score", 0.0)),
            "program_complexity": _average(
                obj.get("object_complexity", 0.0)
                for obj in objects
                if obj.get("object_type") == "PROGRAM"
            ),
            "program_correctness": clamp(truth_count / max(program_count, 1)),
            "program_generality": _average(
                obj.get("generalization_score", 0.0)
                for obj in objects
                if obj.get("object_type") == "PROGRAM"
            ),
        },
        "Evidence": {
            "evaluated": True,
            "quality": evidence_quality,
            "sufficiency": clamp(evidence_count / max(truth_count, 1)),
            "diversity": _ratio({"EVIDENCE"}, object_types),
            "conflicts": sum(1 for obj in objects for rel in obj.get("relationships", []) if rel.get("relationship_type") == "CONTRADICTS"),
            "redundancy": clamp(max(evidence_count - truth_count, 0) / max(evidence_count, 1)),
            "gaps": max(truth_count - evidence_count, 0),
            "reliability": _average(
                obj.get("evidence_payload", {}).get("reliability", obj.get("object_confidence", 0.0))
                for obj in objects
                if obj.get("object_type") == "EVIDENCE"
            ),
        },
        "Truth": {
            "evaluated": True,
            "stability": truth_quality,
            "confidence": _average(
                obj.get("object_confidence", 0.0)
                for obj in objects
                if obj.get("object_type") in {"TRUTH", "TRUTH_CANDIDATE"}
            ),
            "promotion": truth_count,
            "rejection": sum(1 for obj in objects if obj.get("object_status") == "RETIRED"),
            "uncertainty": clamp(1.0 - truth_quality),
            "dependency": graph.get("truth_dependency_edges", 0),
            "consistency": clamp(1.0 - stats.get("failure_count", 0) / max(object_count, 1)),
        },
        "Decision Making": {
            "evaluated": True,
            "correct_decisions": truth_count if decision_count else 0,
            "incorrect_decisions": stats.get("failure_count", 0),
            "late_decisions": max(len(timeline) - object_count, 0),
            "early_decisions": decision_count if decision_count and evidence_count == 0 else 0,
            "risky_decisions": sum(1 for obj in objects if obj.get("object_confidence", 1.0) < 0.5),
            "safe_decisions": sum(1 for obj in objects if obj.get("object_confidence", 0.0) >= 0.75),
            "decision_chains": graph.get("decision_flow_edges", 0),
        },
        "Resource Allocation": {
            "evaluated": True,
            "execution_time": duration,
            "search_budget": search_count,
            "reasoning_budget": reasoning_count,
            "memory_usage": stats.get("memory_count", 0),
            "cpu_utilization": resource_load,
            "concept_cost": concept_count,
            "search_cost": search_count,
            "efficiency_score": quality.get("efficiency", clamp(1.0 - resource_load)),
            "resource_limitation_detected": resource_load > 0.75,
            "reasoning_limitation_detected": reasoning_count > 0 and confidence < 0.5,
        },
        "Execution Strategy": {
            "evaluated": True,
            "strategy_value": quality.get("episode_quality", 0.0),
            "transformations_produced_value": program_count + truth_count + evidence_count,
            "repeatable": episode.get("episode_outcome") in {"SUCCESS", "PARTIAL_SUCCESS"},
            "avoid_repetition": episode.get("episode_outcome") in {"FAILURE", "INTERRUPTED"},
        },
        "Governance Decisions": {
            "evaluated": True,
            "policy_objects": len(stages.get("Goal", {}).get("object_ids", []) or []),
            "uncertainty_reduced": truth_count + evidence_count,
            "uncertainty_increased": stats.get("failure_count", 0),
            "governance_pressure": clamp(stats.get("failure_count", 0) / max(object_count, 1)),
        },
        "Learning Behavior": {
            "evaluated": True,
            "reusable_strategy_detected": episode.get("episode_outcome") == "SUCCESS",
            "adaptive_knowledge_created": bool(truth_count or evidence_count or concept_count),
            "experience_candidate": episode.get("episode_outcome") in {"SUCCESS", "PARTIAL_SUCCESS"},
            "reflection_required_before_experience": True,
        },
    }
    return dimensions


def _answers(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    stats = dict(episode.get("statistics") or {})
    outcome = str(episode.get("episode_outcome") or "UNRESOLVED")
    most_confident = sorted(
        objects,
        key=lambda item: item.get("object_confidence", item.get("confidence", 0.0)),
        reverse=True,
    )
    weak = [
        obj.get("object_id")
        for obj in objects
        if obj.get("object_confidence", obj.get("confidence", 0.0)) < 0.5
    ]
    repeat = []
    avoid = []
    if outcome in {"SUCCESS", "PARTIAL_SUCCESS"}:
        repeat.extend(["evidence_backed_reasoning", "truth_validated_episode_closure"])
    if outcome in {"FAILURE", "INTERRUPTED"}:
        avoid.extend(["unresolved_episode_promotion", "experience_without_reflection"])
    if dimensions["Resource Allocation"]["resource_limitation_detected"]:
        avoid.append("resource_unbounded_search")
    return {
        "What happened?": episode.get("episode_summary", ""),
        "Why did it happen?": _why(episode, dimensions),
        "Which reasoning path was chosen?": list(episode.get("content", {}).get("reasoning_objects", [])),
        "Which alternatives were rejected?": list(episode.get("content", {}).get("failure_objects", [])),
        "Which assumptions proved correct?": list(episode.get("content", {}).get("truth_objects", [])),
        "Which assumptions failed?": weak,
        "Which evidence mattered most?": [
            obj.get("object_id")
            for obj in most_confident
            if obj.get("object_type") == "EVIDENCE"
        ][:5],
        "Which concepts were unnecessary?": dimensions["Concept Formation"]["unused_concepts"],
        "Which search paths were inefficient?": dimensions["Search"]["dead_ends"],
        "Which transformations produced value?": dimensions["Execution Strategy"]["transformations_produced_value"],
        "Which decisions reduced uncertainty?": dimensions["Governance Decisions"]["uncertainty_reduced"],
        "Which decisions increased uncertainty?": dimensions["Governance Decisions"]["uncertainty_increased"],
        "What should be repeated?": repeat or ["maintain_current_cognitive_route"],
        "What should never be repeated?": avoid or ["promote_episode_without_reflection"],
        "statistics_considered": stats,
    }


def _second_order_cognition(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
    answers: Mapping[str, Any],
) -> dict[str, Any]:
    current_path = _causal_chain(episode, objects)
    alternatives = _alternative_strategies(episode, objects, dimensions)
    counterfactuals = _counterfactual_review(episode, dimensions, alternatives)
    assumptions = _assumption_analysis(objects, dimensions)
    uncertainty = _uncertainty_analysis(episode, objects, dimensions)
    decisions = _decision_justifications(episode, objects, dimensions)
    bias = _bias_detection(episode, dimensions)
    return {
        "second_order_cognition": True,
        "reflection_is_replay": False,
        "historical_execution_modified": False,
        "reasoning_about_reasoning": True,
        "selected_reasoning_path": current_path,
        "why_path_selected": answers.get("Why did it happen?", ""),
        "alternative_reasoning_paths": alternatives,
        "counterfactual_review": counterfactuals,
        "assumption_analysis": assumptions,
        "uncertainty_analysis": uncertainty,
        "decision_justifications": decisions,
        "bias_detection": bias,
    }


def _causal_analysis(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    outcome = str(episode.get("episode_outcome") or "UNRESOLVED")
    chain = _causal_chain(episode, objects)
    root_causes = []
    contributing_causes = []
    supporting_causes = []
    blocking_causes = []
    unexpected_causes = []
    hidden_causes = []
    if outcome == "SUCCESS":
        root_causes.append("truth_validation_converged")
        supporting_causes.extend([
            "evidence_sufficient_for_truth_analysis"
            if dimensions["Evidence"]["sufficiency"] >= 1.0
            else "truth_reached_with_limited_evidence",
            "reasoning_path_preserved_episode_continuity",
        ])
    elif outcome == "PARTIAL_SUCCESS":
        root_causes.append("partial_cognitive_progress_without_full_truth_convergence")
        blocking_causes.append("truth_validation_incomplete")
    elif outcome == "FAILURE":
        root_causes.append("episode_failed_before_reusable_truth_or_experience")
        blocking_causes.extend(_failure_lessons(dimensions))
    else:
        root_causes.append("episode_did_not_resolve_to_a_stable_outcome")
    if dimensions["Resource Allocation"]["resource_limitation_detected"]:
        contributing_causes.append("resource_pressure")
    if dimensions["Truth"]["uncertainty"] > 0.5:
        contributing_causes.append("truth_uncertainty_high")
    if dimensions["Evidence"]["conflicts"]:
        unexpected_causes.append("conflicting_evidence_relationships")
    if dimensions["Concept Formation"]["unused_concepts"]:
        hidden_causes.append("unused_concepts_increased_cognitive_surface_area")
    return {
        "root_causes": root_causes,
        "contributing_causes": contributing_causes,
        "supporting_causes": supporting_causes,
        "blocking_causes": blocking_causes,
        "unexpected_causes": unexpected_causes,
        "hidden_causes": hidden_causes,
        "secondary_effects": _secondary_effects(episode, dimensions),
        "long_term_consequences": _long_term_consequences(episode, dimensions),
        "causal_chain_reconstruction": chain,
        "causal_confidence": _causal_confidence(dimensions),
    }


def _strategy_analysis(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
    causal: Mapping[str, Any],
) -> dict[str, Any]:
    alternatives = _alternative_strategies(episode, objects, dimensions)
    episode_quality = float(episode.get("episode_quality", 0.0) or 0.0)
    efficiency = float(dimensions["Resource Allocation"].get("efficiency_score", 0.0) or 0.0)
    robustness = _average([
        dimensions["Reasoning"]["stability"],
        dimensions["Truth"]["consistency"],
        dimensions["Evidence"]["reliability"],
    ])
    adaptability = _average([
        dimensions["Learning Behavior"]["adaptive_knowledge_created"],
        dimensions["Concept Formation"]["generalized_concepts"] > 0,
        dimensions["Program Synthesis"]["program_generality"],
    ])
    complexity = float(episode.get("episode_complexity", 0.0) or 0.0)
    risk = _average([
        dimensions["Decision Making"]["risky_decisions"] / max(len(objects), 1),
        dimensions["Truth"]["uncertainty"],
        dimensions["Governance Decisions"]["governance_pressure"],
    ])
    reuse = _average([
        episode.get("episode_outcome") == "SUCCESS",
        dimensions["Execution Strategy"]["repeatable"],
        dimensions["Program Synthesis"]["program_reuse"] > 0,
    ])
    transfer = _transfer_potential(dimensions, robustness, adaptability)
    return {
        "strategy_efficiency": efficiency,
        "strategy_robustness": robustness,
        "strategy_adaptability": adaptability,
        "strategy_complexity": complexity,
        "strategy_reuse": reuse,
        "strategy_stability": dimensions["Reasoning"]["stability"],
        "strategy_novelty": dimensions["Reasoning"]["novelty"],
        "strategy_risk": risk,
        "strategy_quality": _average([episode_quality, efficiency, robustness, adaptability, 1.0 - risk]),
        "alternative_strategies": alternatives,
        "best_available_strategy": _best_strategy(alternatives, efficiency, reuse),
        "success_analysis": _success_analysis(episode, dimensions, causal),
        "failure_analysis": _failure_analysis(episode, dimensions, causal),
        "generalization_opportunities": _generalization_opportunities(dimensions),
        "transfer_opportunities": transfer,
    }


def _learning_value(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    strategy: Mapping[str, Any],
    causal: Mapping[str, Any],
    second_order: Mapping[str, Any],
) -> dict[str, Any]:
    novelty = float(dimensions["Reasoning"].get("novelty", 0.0) or 0.0)
    difficulty = clamp(float(episode.get("episode_complexity", 0.0) or 0.0) + dimensions["Truth"]["uncertainty"] * 0.5)
    generalization = _average([
        len(strategy.get("generalization_opportunities", [])) / 5.0,
        dimensions["Program Synthesis"]["program_generality"],
        dimensions["Concept Formation"]["generalized_concepts"] / max(dimensions["Concept Formation"]["useful_concepts"], 1),
    ])
    reflection_depth = _average([
        bool(second_order.get("alternative_reasoning_paths")),
        bool(second_order.get("counterfactual_review")),
        bool(causal.get("causal_chain_reconstruction")),
        bool(second_order.get("decision_justifications")),
    ])
    concept_richness = clamp(dimensions["Concept Formation"]["useful_concepts"] / 4.0)
    evidence_richness = clamp(dimensions["Evidence"]["sufficiency"])
    transfer = _average(
        item.get("transfer_score", 0.0)
        for item in strategy.get("transfer_opportunities", [])
    )
    score = _average([
        novelty,
        difficulty,
        generalization,
        reflection_depth,
        concept_richness,
        evidence_richness,
        transfer,
    ])
    return {
        "learning_value_score": score,
        "novelty": novelty,
        "difficulty": difficulty,
        "generalization": generalization,
        "reflection_depth": reflection_depth,
        "concept_richness": concept_richness,
        "evidence_richness": evidence_richness,
        "transfer_potential": transfer,
        "long_term_importance": "high" if score >= 0.7 else "medium" if score >= 0.4 else "low",
    }


def _self_improvement_report(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
    second_order: Mapping[str, Any],
    causal: Mapping[str, Any],
    strategy: Mapping[str, Any],
    learning_value: Mapping[str, Any],
    historical_reflections: list[ReflectionObject],
) -> dict[str, Any]:
    strengths = _cognitive_strengths(episode, objects, dimensions, strategy)
    weaknesses = _cognitive_weaknesses(dimensions, strategy, causal)
    recurring = _recurring_patterns(episode, dimensions, strategy, historical_reflections)
    promotions = _knowledge_promotions(objects, dimensions, strategy)
    demotions = _knowledge_demotions(objects, dimensions, causal)
    conflicts = _detected_conflicts(objects, dimensions, second_order)
    consistency = _consistency_analysis(dimensions, conflicts)
    learning_signals = _learning_signals(
        strengths,
        weaknesses,
        promotions,
        demotions,
        conflicts,
        strategy,
        learning_value,
    )
    priorities = _improvement_priorities(learning_signals)
    plan = _improvement_plan(learning_signals, causal, priorities)
    evolution = _evolution_metrics(dimensions, strategy, learning_value, historical_reflections)
    memory_update = _reflection_memory_update(
        episode,
        strengths,
        weaknesses,
        recurring,
        plan,
        learning_value,
        historical_reflections,
    )
    quality_metrics = _reflection_quality_metrics(
        dimensions,
        second_order,
        causal,
        strategy,
        learning_value,
        plan,
        conflicts,
    )
    return {
        "SELF_IMPROVEMENT_REPORT": True,
        "reflection_proposes_improvements_only": True,
        "cognitive_objects_mutated": False,
        "historical_execution_mutated": False,
        "Strengths": strengths,
        "Weaknesses": weaknesses,
        "Recurring Patterns": recurring,
        "Knowledge Promotions": promotions,
        "Knowledge Demotions": demotions,
        "Detected Conflicts": conflicts,
        "Consistency Analysis": consistency,
        "Learning Signals": learning_signals,
        "Improvement Priorities": priorities,
        "Improvement Plan": plan,
        "Evolution Metrics": evolution,
        "Reflection Memory Updates": memory_update,
        "Reflection Quality Metrics": quality_metrics,
        "Self Assessment": _self_assessment(quality_metrics, causal, plan),
        "What should improve?": [item["recommended_action"] for item in plan],
        "What should remain unchanged?": [item["asset"] for item in strengths],
        "What should be strengthened?": [
            item["target"] for item in learning_signals
            if item["category"] in {"Concept Improvement", "Strategy Improvement", "Truth Improvement"}
        ],
        "What should be simplified?": [
            item["target"] for item in learning_signals
            if item["category"] in {"Search Improvement", "Reasoning Improvement"}
        ],
        "What should be forgotten?": [
            item["knowledge_id"] for item in demotions
            if item["recommended_level"] in {"Deprecated Strategy", "Retired Knowledge"}
        ],
        "What should be explored next?": [
            item["recommended_action"] for item in plan
            if item["priority"] in {"HIGH", "CRITICAL"}
        ],
    }


def _reflective_synthesis_report(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
    answers: Mapping[str, Any],
    second_order: Mapping[str, Any],
    causal: Mapping[str, Any],
    strategy: Mapping[str, Any],
    learning_value: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
    historical_reflections: list[ReflectionObject],
) -> dict[str, Any]:
    lessons = _lessons_extracted(episode, objects, answers, second_order, causal, strategy, self_improvement)
    integrated = _synthesized_knowledge_structures(episode, objects, dimensions, lessons)
    abstractions = _abstractions_created(episode, objects, dimensions, strategy, lessons, historical_reflections)
    principles = _general_principles(dimensions, strategy, lessons)
    exceptions = _exceptions_discovered(dimensions, strategy, causal, second_order)
    transfer = _synthesis_transfer_opportunities(strategy, learning_value, principles)
    compression = _compression_statistics(objects, lessons, abstractions, strategy)
    merged = _merged_knowledge(objects, lessons, abstractions)
    separated = _separated_knowledge(objects, causal, self_improvement)
    reuse = _reuse_opportunities(objects, lessons, strategy, abstractions)
    candidates = _experience_candidates(
        episode,
        lessons,
        strategy,
        learning_value,
        abstractions,
        transfer,
        dimensions,
    )
    registry = _abstraction_registry_update(
        episode,
        abstractions,
        principles,
        lessons,
        exceptions,
        strategy,
        transfer,
        compression,
    )
    quality = _synthesis_quality(episode, dimensions, learning_value, lessons, abstractions, candidates)
    return {
        "REFLECTIVE_SYNTHESIS_REPORT": True,
        "reflection_constructs_reusable_knowledge": True,
        "writes_permanent_memory": False,
        "modifies_world_model": False,
        "updates_dna_directly": False,
        "experience_engine_retains_promotion_authority": True,
        "Experience Candidates": candidates,
        "Lessons Extracted": lessons,
        "Integrated Knowledge Structures": integrated,
        "Abstractions Created": abstractions,
        "General Principles": principles,
        "Exceptions": exceptions,
        "Transfer Opportunities": transfer,
        "Compression Statistics": compression,
        "Merged Knowledge": merged,
        "Separated Knowledge": separated,
        "Reuse Opportunities": reuse,
        "Knowledge Quality": quality["knowledge_quality"],
        "Knowledge Novelty": quality["knowledge_novelty"],
        "Reflection Contribution": quality["reflection_contribution"],
        "Reflection Abstraction Registry": registry,
    }


def _reflection_report(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    answers: Mapping[str, Any],
    second_order: Mapping[str, Any],
    causal: Mapping[str, Any],
    strategy: Mapping[str, Any],
    learning_value: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
    synthesis: Mapping[str, Any],
    intelligence: Mapping[str, Any],
) -> dict[str, Any]:
    weaknesses = []
    if dimensions["Evidence"]["gaps"]:
        weaknesses.append("evidence_gaps_detected")
    if dimensions["Truth"]["uncertainty"] > 0.5:
        weaknesses.append("truth_uncertainty_high")
    if dimensions["Resource Allocation"]["reasoning_limitation_detected"]:
        weaknesses.append("reasoning_limitation_detected")
    improvements = []
    if dimensions["Search"]["dead_ends"]:
        improvements.append("prune_failed_search_routes")
    if dimensions["Concept Formation"]["unused_concepts"]:
        improvements.append("retire_or_merge_unused_concepts")
    if dimensions["Evidence"]["gaps"]:
        improvements.append("collect_more_evidence_before_truth_promotion")
    return {
        "REFLECTION_REPORT": True,
        "Episode Summary": episode.get("episode_summary", ""),
        "Reasoning Review": dimensions["Reasoning"],
        "Search Review": dimensions["Search"],
        "Concept Review": dimensions["Concept Formation"],
        "Program Review": dimensions["Program Synthesis"],
        "Evidence Review": dimensions["Evidence"],
        "Truth Review": dimensions["Truth"],
        "Decision Review": dimensions["Decision Making"],
        "Resource Review": dimensions["Resource Allocation"],
        "Major Successes": _major_successes(episode, dimensions),
        "Major Weaknesses": weaknesses or ["no_major_reflective_weakness_detected"],
        "Improvement Candidates": improvements or ["preserve_successful_strategy_for_experience"],
        "Reflection Confidence": _reflection_confidence(episode, dimensions),
        "Root Cause Report": causal,
        "Success Analysis": strategy.get("success_analysis", {}),
        "Failure Analysis": strategy.get("failure_analysis", {}),
        "Alternative Strategies": strategy.get("alternative_strategies", []),
        "Counterfactual Review": second_order.get("counterfactual_review", []),
        "Assumption Analysis": second_order.get("assumption_analysis", {}),
        "Uncertainty Analysis": second_order.get("uncertainty_analysis", {}),
        "Decision Justifications": second_order.get("decision_justifications", []),
        "Bias Detection": second_order.get("bias_detection", {}),
        "Strategy Analysis": strategy,
        "Transfer Opportunities": strategy.get("transfer_opportunities", []),
        "Generalization Opportunities": strategy.get("generalization_opportunities", []),
        "Learning Value": learning_value,
        "Reflection Recommendations": _reflection_recommendations(dimensions, strategy, learning_value),
        "SELF_IMPROVEMENT_REPORT": self_improvement,
        "REFLECTIVE_SYNTHESIS_REPORT": synthesis,
        "REFLECTION_INTELLIGENCE_REPORT": intelligence,
        "reflection_answers": dict(answers),
    }


def _reflection_intelligence_report(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    second_order: Mapping[str, Any],
    causal: Mapping[str, Any],
    strategy: Mapping[str, Any],
    learning_value: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
    synthesis: Mapping[str, Any],
    historical_reflections: list[ReflectionObject],
) -> dict[str, Any]:
    recommendation_validation = _recommendation_validation(self_improvement, historical_reflections)
    maturity = _cognitive_maturity(dimensions, synthesis, self_improvement, learning_value)
    trends = _long_term_trends(dimensions, learning_value, self_improvement, historical_reflections)
    behavioral = _behavioral_evolution(strategy, self_improvement, historical_reflections)
    trajectories = _learning_trajectories(episode, synthesis, historical_reflections)
    preservation = _knowledge_preservation_candidates(synthesis, self_improvement)
    forgetting = _knowledge_forgetting_candidates(synthesis, self_improvement)
    adaptive = _adaptive_signals(dimensions, strategy, self_improvement, synthesis)
    executive = _executive_recommendations(
        self_improvement,
        synthesis,
        adaptive,
        preservation,
        forgetting,
    )
    world_model = _world_model_preparation(synthesis)
    dna = _dna_preparation(adaptive, behavioral, maturity)
    meta = _meta_cognitive_feedback(
        self_improvement,
        synthesis,
        maturity,
        behavioral,
        recommendation_validation,
    )
    graph = _reflection_knowledge_graph(
        episode,
        self_improvement,
        synthesis,
        trajectories,
        executive,
        historical_reflections,
    )
    confidence = _reflection_confidence_evolution(
        episode,
        learning_value,
        recommendation_validation,
        historical_reflections,
    )
    return {
        "REFLECTION_INTELLIGENCE_REPORT": True,
        "reflection_is_permanent_cycle_stage": True,
        "reflection_advises_governance_only": True,
        "does_not_bypass_executive_governance": True,
        "does_not_perform_architectural_evolution": True,
        "Reflection Summary": episode.get("episode_summary", ""),
        "Reflection Quality": self_improvement.get("Reflection Quality Metrics", {}),
        "Recommendation Statistics": _recommendation_statistics(self_improvement, executive),
        "Recommendation Validation": recommendation_validation,
        "Learning Trajectories": trajectories,
        "Knowledge Preservation Candidates": preservation,
        "Knowledge Forgetting Candidates": forgetting,
        "Behavioral Evolution": behavioral,
        "Cognitive Maturity": maturity,
        "Reflection Confidence": confidence,
        "Trend Analysis": trends,
        "Adaptive Signals": adaptive,
        "Executive Recommendations": executive,
        "World Model Preparation": world_model,
        "DNA Preparation": dna,
        "Meta-Cognitive Feedback": meta,
        "Reflection Knowledge Graph": graph,
        "Reflection Knowledge Graph Statistics": {
            "node_count": graph["node_count"],
            "edge_count": graph["edge_count"],
            "node_types": graph["node_types"],
            "edge_types": graph["edge_types"],
        },
        "Executive Feedback": {
            "Strength Reports": self_improvement.get("Strengths", []),
            "Weakness Reports": self_improvement.get("Weaknesses", []),
            "Risk Reports": adaptive,
            "Improvement Opportunities": self_improvement.get("Improvement Plan", []),
            "Generalization Opportunities": synthesis.get("General Principles", []),
            "Knowledge Gaps": _knowledge_gaps(dimensions, causal),
            "Search Improvements": [
                item for item in self_improvement.get("Learning Signals", [])
                if item.get("category") == "Search Improvement"
            ],
            "Reasoning Improvements": [
                item for item in self_improvement.get("Learning Signals", [])
                if item.get("category") == "Reasoning Improvement"
            ],
            "Resource Recommendations": [
                item for item in self_improvement.get("Improvement Plan", [])
                if "resource" in item.get("recommended_action", "")
            ],
        },
    }


def _major_successes(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    successes = []
    if episode.get("episode_outcome") == "SUCCESS":
        successes.append("episode_reached_truth_validated_success")
    if dimensions["Evidence"]["sufficiency"] >= 1.0:
        successes.append("evidence_sufficient_for_truth_analysis")
    if dimensions["Resource Allocation"]["efficiency_score"] >= 0.5:
        successes.append("resource_use_remained_within_reasonable_bounds")
    if dimensions["Learning Behavior"]["adaptive_knowledge_created"]:
        successes.append("episode_created_adaptive_knowledge")
    return successes or ["episode_preserved_for_learning_analysis"]


def _lessons_extracted(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    answers: Mapping[str, Any],
    second_order: Mapping[str, Any],
    causal: Mapping[str, Any],
    strategy: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
) -> list[dict[str, Any]]:
    lesson_specs = []
    for item in answers.get("What should be repeated?", []):
        lesson_specs.append(("Successful Strategy", item, "repeatable_behavior"))
    for item in answers.get("What should never be repeated?", []):
        lesson_specs.append(("Avoidable Mistake", item, "negative_boundary"))
    for evidence_id in answers.get("Which evidence mattered most?", []):
        lesson_specs.append(("Critical Evidence", evidence_id, "decisive_evidence"))
    for concept_id in episode.get("content", {}).get("concept_objects", []):
        lesson_specs.append(("Useful Concept", concept_id, "conceptual_asset"))
    for decision in second_order.get("decision_justifications", []):
        lesson_specs.append(("Reusable Reasoning", decision.get("decision"), "decision_chain"))
    for cause in causal.get("blocking_causes", []):
        lesson_specs.append(("Failure Indicator", cause, "causal_blocker"))
    for plan in self_improvement.get("Improvement Plan", [])[:5]:
        lesson_specs.append(("Optimization Opportunity", plan.get("recommended_action"), "improvement_plan"))
    if strategy.get("success_analysis", {}).get("reproducible_success"):
        lesson_specs.append(("Boundary Condition", "evidence_sufficiency_and_truth_confidence_required", "success_boundary"))
    lessons = []
    for index, (lesson_type, content, source) in enumerate(lesson_specs):
        if not content:
            continue
        lesson_id = _stable_id("lesson", episode.get("episode_id"), lesson_type, content, index)
        lessons.append({
            "lesson_id": lesson_id,
            "lesson_type": lesson_type,
            "lesson": str(content),
            "source": source,
            "origin_episode": episode.get("episode_id"),
            "supporting_objects": _supporting_object_ids(objects, str(content)),
            "lineage": {
                "episode_id": [str(episode.get("episode_id"))],
                "object_ids": _supporting_object_ids(objects, str(content)),
            },
            "confidence": _lesson_confidence(lesson_type, strategy),
            "first_class_cognitive_object": True,
        })
    return _dedupe_by_key(lessons, "lesson")


def _synthesized_knowledge_structures(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
    lessons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    content = dict(episode.get("content") or {})
    structures = []
    groups = {
        "concept_evidence_truth_cluster": (
            content.get("concept_objects", [])
            + content.get("evidence_objects", [])
            + content.get("truth_objects", [])
        ),
        "reasoning_search_decision_cluster": (
            content.get("reasoning_objects", [])
            + content.get("search_objects", [])
            + content.get("decision_objects", [])
        ),
        "strategy_outcome_lesson_cluster": (
            content.get("program_objects", [])
            + content.get("failure_objects", [])
            + [lesson["lesson_id"] for lesson in lessons]
        ),
    }
    for name, ids in groups.items():
        ids = [str(item) for item in ids if item]
        if not ids:
            continue
        structures.append({
            "knowledge_structure_id": _stable_id("knowledge_structure", episode.get("episode_id"), name, ids),
            "structure_type": name,
            "member_ids": ids,
            "coherence": _structure_coherence(name, dimensions),
            "lineage": {"episode_id": [str(episode.get("episode_id"))], "member_ids": ids},
            "semantic_consistency": True,
            "duplicates_cognitive_objects": False,
        })
    return structures


def _experience_candidates(
    episode: Mapping[str, Any],
    lessons: list[dict[str, Any]],
    strategy: Mapping[str, Any],
    learning_value: Mapping[str, Any],
    abstractions: list[dict[str, Any]],
    transfer: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    depth = learning_value.get("reflection_depth", 0.0)
    score = _experience_candidate_score(episode, learning_value, strategy, transfer)
    qualifies = (
        depth >= 0.5
        and learning_value.get("learning_value_score", 0.0) >= 0.25
        and _average(item.get("transfer_score", 0.0) for item in transfer) >= 0.2
        and episode.get("episode_outcome") in {"SUCCESS", "PARTIAL_SUCCESS", "FAILURE", "UNRESOLVED"}
    )
    if not lessons:
        qualifies = False
    candidate = {
        "experience_candidate_id": _stable_id("experience_candidate", episode.get("episode_id"), score),
        "origin_episode": episode.get("episode_id"),
        "reflection_summary": episode.get("reflection", {}).get("reflection_summary")
        or episode.get("episode_summary", ""),
        "lessons": [lesson["lesson_id"] for lesson in lessons],
        "strategies": [
            strategy.get("best_available_strategy", {}).get("strategy", "current_reasoning_strategy")
        ],
        "generalizations": [item["abstraction_id"] for item in abstractions],
        "transfer_opportunities": transfer,
        "confidence": _average([
            episode.get("episode_confidence", 0.0),
            strategy.get("strategy_quality", 0.0),
            learning_value.get("learning_value_score", 0.0),
        ]),
        "quality": score,
        "qualified": qualifies,
        "qualification_reasons": _experience_qualification_reasons(episode, learning_value, strategy, dimensions, lessons),
        "governance_required": True,
        "experience_engine_decides_promotion": True,
        "writes_memory": False,
        "lineage": {
            "episode_id": [str(episode.get("episode_id"))],
            "lesson_ids": [lesson["lesson_id"] for lesson in lessons],
            "abstraction_ids": [item["abstraction_id"] for item in abstractions],
        },
    }
    return [candidate]


def _abstractions_created(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
    strategy: Mapping[str, Any],
    lessons: list[dict[str, Any]],
    historical_reflections: list[ReflectionObject],
) -> list[dict[str, Any]]:
    levels = [
        ("Episode", "episode_specific_understanding", 0.2),
        ("Experience", "validated_episode_lesson_bundle", 0.35),
        ("General Pattern", "recurring_reasoning_evidence_truth_pattern", 0.5),
        ("Strategy", strategy.get("best_available_strategy", {}).get("strategy", "current_reasoning_strategy"), 0.65),
        ("Mental Principle", "evidence_backed_reasoning_improves_transfer", 0.8),
        ("Cognitive Law", "reflection_required_before_experience_promotion", 0.9),
    ]
    abstractions = []
    for level, name, transferability in levels:
        confidence = _average([
            strategy.get("strategy_quality", 0.0),
            dimensions["Truth"]["confidence"],
            len(lessons) / 8.0,
            min(len(historical_reflections) + 1, 5) / 5.0,
        ])
        abstractions.append({
            "abstraction_id": _stable_id("abstraction", episode.get("episode_id"), level, name),
            "abstraction_level": level,
            "abstraction": str(name),
            "transferability": clamp(transferability),
            "confidence": confidence,
            "supporting_lessons": [lesson["lesson_id"] for lesson in lessons[:6]],
            "supporting_objects": [str(obj.get("object_id")) for obj in objects if obj.get("object_id")][:12],
            "lineage": {
                "episode_id": [str(episode.get("episode_id"))],
                "historical_reflections": [reflection.reflection_id for reflection in historical_reflections[-5:]],
            },
        })
    return abstractions


def _general_principles(
    dimensions: Mapping[str, Mapping[str, Any]],
    strategy: Mapping[str, Any],
    lessons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    principles = []
    if dimensions["Reasoning"]["stability"] >= 0.5:
        principles.append(_principle("Reliable Reasoning Principle", "preserve_continuous_reasoning_paths", dimensions["Reasoning"]["stability"]))
    if dimensions["Search"]["route_quality"] >= 0.5:
        principles.append(_principle("Search Principle", "prefer_routes_that_converge_to_evidence", dimensions["Search"]["route_quality"]))
    if dimensions["Program Synthesis"]["program_usefulness"] > 0:
        principles.append(_principle("Transformation Principle", "reuse_programs_supported_by_concepts_and_truth", dimensions["Program Synthesis"]["program_usefulness"]))
    if dimensions["Evidence"]["sufficiency"] >= 1.0:
        principles.append(_principle("Evidence Principle", "promote_truth_only_when_evidence_is_sufficient", dimensions["Evidence"]["sufficiency"]))
    if dimensions["Truth"]["confidence"] >= 0.5:
        principles.append(_principle("Truth Principle", "truth_confidence_requires_traceable_evidence", dimensions["Truth"]["confidence"]))
    if strategy.get("strategy_quality", 0.0) >= 0.4:
        principles.append(_principle("Planning Principle", "rank_strategies_by_quality_risk_and_transfer", strategy["strategy_quality"]))
    if lessons:
        principles.append(_principle("Reflection Principle", "lessons_become_reusable_only_after_lineage_preserving_synthesis", len(lessons) / 8.0))
    return principles


def _exceptions_discovered(
    dimensions: Mapping[str, Mapping[str, Any]],
    strategy: Mapping[str, Any],
    causal: Mapping[str, Any],
    second_order: Mapping[str, Any],
) -> list[dict[str, Any]]:
    exceptions = []
    if strategy.get("success_analysis", {}).get("success_detected") and not strategy.get("success_analysis", {}).get("reproducible_success"):
        exceptions.append(_exception("Exception", "success_without_full_reproducibility", "requires_additional_evidence"))
    if dimensions["Evidence"]["conflicts"]:
        exceptions.append(_exception("Contradictory Situation", "conflicting_evidence", "resolve_before_merging"))
    if causal.get("blocking_causes"):
        exceptions.append(_exception("Failure Condition", ",".join(causal["blocking_causes"][:3]), "avoid_or_revalidate"))
    if second_order.get("bias_detection", {}).get("biases_detected"):
        exceptions.append(_exception("Context Limitation", ",".join(second_order["bias_detection"]["biases_detected"]), "bias_mitigation_required"))
    if dimensions["Truth"]["uncertainty"] > 0.5:
        exceptions.append(_exception("Boundary Case", "high_truth_uncertainty", "do_not_overgeneralize"))
    return exceptions


def _synthesis_transfer_opportunities(
    strategy: Mapping[str, Any],
    learning_value: Mapping[str, Any],
    principles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    opportunities = []
    for transfer in strategy.get("transfer_opportunities", []):
        opportunities.append({
            **transfer,
            "recommended_reuse_scope": _transfer_scope(transfer.get("transfer_type", "")),
            "supports_experience_candidate": transfer.get("transfer_score", 0.0) >= 0.25,
        })
    if principles:
        opportunities.append({
            "transfer_type": "principle_transfer",
            "transfer_score": clamp(len(principles) / 8.0 + learning_value.get("generalization", 0.0) * 0.5),
            "recommended_reuse_scope": "strategies",
            "supports_experience_candidate": True,
        })
    return opportunities


def _compression_statistics(
    objects: list[dict[str, Any]],
    lessons: list[dict[str, Any]],
    abstractions: list[dict[str, Any]],
    strategy: Mapping[str, Any],
) -> dict[str, Any]:
    concept_ids = [obj.get("object_id") for obj in objects if obj.get("object_type") == "CONCEPT"]
    strategy_names = [
        strategy.get("best_available_strategy", {}).get("strategy"),
        *[item.get("strategy") for item in strategy.get("alternative_strategies", [])],
    ]
    equivalent_lessons = len(lessons) - len({lesson["lesson"] for lesson in lessons})
    before = len(objects) + len(lessons) + len(strategy_names)
    after = len(set(concept_ids)) + len({lesson["lesson"] for lesson in lessons}) + len({item for item in strategy_names if item}) + len(abstractions)
    return {
        "equivalent_concepts_found": len(concept_ids) - len(set(concept_ids)),
        "equivalent_strategies_found": len(strategy_names) - len({item for item in strategy_names if item}),
        "equivalent_lessons_found": max(equivalent_lessons, 0),
        "equivalent_experiences_found": 0,
        "equivalent_abstractions_found": len(abstractions) - len({item["abstraction"] for item in abstractions}),
        "items_before_compression": before,
        "items_after_compression": after,
        "compression_ratio": round(clamp(1.0 - (after / max(before, 1))), 4),
        "meaning_preserved": True,
    }


def _merged_knowledge(
    objects: list[dict[str, Any]],
    lessons: list[dict[str, Any]],
    abstractions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merges = []
    by_type: dict[str, list[str]] = {}
    for obj in objects:
        by_type.setdefault(str(obj.get("object_type")), []).append(str(obj.get("object_id")))
    for object_type, ids in by_type.items():
        if len(ids) > 1 and object_type in {"CONCEPT", "EVIDENCE", "TRUTH", "SEARCH_ROUTE"}:
            merges.append({
                "merge_id": _stable_id("merge", object_type, ids),
                "merge_type": object_type,
                "member_ids": ids,
                "semantic_compatibility": True,
                "evidence_supports_merging": object_type in {"EVIDENCE", "TRUTH"} or bool(lessons),
                "contradiction_exists": False,
                "identity_integrity_preserved": True,
                "lineage": {"member_ids": ids, "abstraction_ids": [item["abstraction_id"] for item in abstractions]},
            })
    return merges


def _separated_knowledge(
    objects: list[dict[str, Any]],
    causal: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
) -> list[dict[str, Any]]:
    separated = []
    for demotion in self_improvement.get("Knowledge Demotions", []):
        separated.append({
            "separation_id": _stable_id("separation", demotion.get("knowledge_id"), demotion.get("recommended_level")),
            "source": demotion.get("knowledge_id"),
            "reason": "avoid_false_generalization",
            "separated_as": demotion.get("recommended_level"),
            "lineage": {"evidence": demotion.get("evidence", [])},
        })
    for cause in causal.get("blocking_causes", []):
        separated.append({
            "separation_id": _stable_id("separation", cause),
            "source": str(cause),
            "reason": "different_cause_or_boundary_condition",
            "separated_as": "Failure Condition",
            "lineage": {"causal_analysis": [str(cause)]},
        })
    return separated


def _reuse_opportunities(
    objects: list[dict[str, Any]],
    lessons: list[dict[str, Any]],
    strategy: Mapping[str, Any],
    abstractions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    opportunities = []
    for obj in objects:
        object_type = str(obj.get("object_type"))
        if object_type in {"CONCEPT", "PROGRAM", "EVIDENCE", "SEARCH_ROUTE", "REASONING_STEP"}:
            opportunities.append({
                "reuse_id": _stable_id("reuse", object_type, obj.get("object_id")),
                "reuse_type": object_type,
                "source_id": obj.get("object_id"),
                "immediate_reuse": obj.get("object_confidence", 0.0) >= 0.7,
                "reuse_confidence": obj.get("object_confidence", 0.0),
            })
    for lesson in lessons:
        opportunities.append({
            "reuse_id": _stable_id("reuse", "lesson", lesson["lesson_id"]),
            "reuse_type": "LESSON",
            "source_id": lesson["lesson_id"],
            "immediate_reuse": lesson["confidence"] >= 0.5,
            "reuse_confidence": lesson["confidence"],
        })
    for abstraction in abstractions:
        opportunities.append({
            "reuse_id": _stable_id("reuse", "abstraction", abstraction["abstraction_id"]),
            "reuse_type": "ABSTRACTION",
            "source_id": abstraction["abstraction_id"],
            "immediate_reuse": abstraction["transferability"] >= 0.5,
            "reuse_confidence": abstraction["confidence"],
        })
    opportunities.append({
        "reuse_id": _stable_id("reuse", "strategy", strategy.get("best_available_strategy", {}).get("strategy")),
        "reuse_type": "STRATEGY",
        "source_id": strategy.get("best_available_strategy", {}).get("strategy"),
        "immediate_reuse": strategy.get("strategy_reuse", 0.0) >= 0.5,
        "reuse_confidence": strategy.get("strategy_quality", 0.0),
    })
    return opportunities


def _abstraction_registry_update(
    episode: Mapping[str, Any],
    abstractions: list[dict[str, Any]],
    principles: list[dict[str, Any]],
    lessons: list[dict[str, Any]],
    exceptions: list[dict[str, Any]],
    strategy: Mapping[str, Any],
    transfer: list[dict[str, Any]],
    compression: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "registry_enabled": True,
        "stores_permanent_memory": False,
        "abstractions": abstractions,
        "general_principles": principles,
        "lessons": lessons,
        "exceptions": exceptions,
        "strategies": [strategy.get("best_available_strategy", {})],
        "transfer_rules": transfer,
        "knowledge_compression_results": dict(compression),
        "complete_lineage_preserved": True,
        "lineage": {
            "episode_id": [str(episode.get("episode_id"))],
            "abstraction_ids": [item["abstraction_id"] for item in abstractions],
            "lesson_ids": [item["lesson_id"] for item in lessons],
        },
    }


def _synthesis_quality(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    learning_value: Mapping[str, Any],
    lessons: list[dict[str, Any]],
    abstractions: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> dict[str, float]:
    lesson_quality = _average(lesson.get("confidence", 0.0) for lesson in lessons)
    abstraction_quality = _average(item.get("confidence", 0.0) for item in abstractions)
    candidate_quality = _average(item.get("quality", 0.0) for item in candidates)
    knowledge_quality = _average([
        dimensions["Truth"]["confidence"],
        dimensions["Evidence"]["reliability"],
        lesson_quality,
        abstraction_quality,
        candidate_quality,
    ])
    return {
        "knowledge_quality": knowledge_quality,
        "knowledge_novelty": learning_value.get("novelty", 0.0),
        "reflection_contribution": _average([
            learning_value.get("reflection_depth", 0.0),
            len(lessons) / 8.0,
            len(abstractions) / 6.0,
            bool(candidates and candidates[0].get("qualified")),
        ]),
    }


def _causal_chain(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    content = dict(episode.get("content") or {})
    object_lookup = {str(obj.get("object_id")): obj for obj in objects}
    links = (
        ("Observation", content.get("other_objects", []) + content.get("semantic_objects", [])),
        ("Reasoning", content.get("reasoning_objects", [])),
        ("Hypothesis", content.get("truth_objects", [])[:1]),
        ("Decision", content.get("decision_objects", [])),
        ("Action", content.get("program_objects", [])),
        ("Evidence", content.get("evidence_objects", [])),
        ("Truth", content.get("truth_objects", [])),
        ("Outcome", content.get("failure_objects", []) or content.get("memory_objects", [])),
        ("Reflection", [episode.get("reflection_id")] if episode.get("reflection_id") else []),
    )
    chain = []
    previous = ""
    for stage, ids in links:
        ids = [str(item) for item in ids if item]
        chain.append({
            "stage": stage,
            "object_ids": ids,
            "observable": bool(ids) or stage in {"Outcome", "Reflection"},
            "source_stage": previous,
            "confidence": _average(
                object_lookup.get(object_id, {}).get("object_confidence", 0.0)
                for object_id in ids
            ) if ids else 0.0,
        })
        previous = stage
    return chain


def _alternative_strategies(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    base_efficiency = float(dimensions["Resource Allocation"].get("efficiency_score", 0.0) or 0.0)
    base_confidence = float(episode.get("episode_confidence", 0.0) or 0.0)
    complexity = float(episode.get("episode_complexity", 0.0) or 0.0)
    alternatives = [
        {
            "strategy_id": "alternative:a:evidence_first",
            "strategy": "prioritize_evidence_before_truth_promotion",
            "expected_efficiency": clamp(base_efficiency + 0.05),
            "expected_confidence": clamp(base_confidence + 0.08),
            "expected_resource_cost": clamp(complexity + 0.1),
            "potential_generalization": clamp(dimensions["Evidence"]["sufficiency"] * 0.8 + 0.1),
            "reason": "More decisive evidence can reduce truth uncertainty before closure.",
        },
        {
            "strategy_id": "alternative:b:search_pruning",
            "strategy": "prune_low_confidence_search_routes_earlier",
            "expected_efficiency": clamp(base_efficiency + 0.12),
            "expected_confidence": clamp(base_confidence + 0.02),
            "expected_resource_cost": clamp(max(complexity - 0.1, 0.0)),
            "potential_generalization": clamp(dimensions["Search"]["convergence"]),
            "reason": "Earlier pruning can reduce dead ends and resource pressure.",
        },
        {
            "strategy_id": "alternative:c:concept_minimization",
            "strategy": "minimize_unused_concepts_before_program_synthesis",
            "expected_efficiency": clamp(base_efficiency + 0.08),
            "expected_confidence": clamp(base_confidence + 0.04),
            "expected_resource_cost": clamp(max(complexity - 0.05, 0.0)),
            "potential_generalization": clamp(1.0 - dimensions["Concept Formation"]["concept_redundancy"]),
            "reason": "Reducing concept redundancy can make reasoning easier to reuse.",
        },
    ]
    if not any(obj.get("object_type") == "SEARCH_ROUTE" for obj in objects):
        alternatives.append({
            "strategy_id": "alternative:d:explicit_search",
            "strategy": "generate_explicit_search_route_before_decision",
            "expected_efficiency": clamp(base_efficiency),
            "expected_confidence": clamp(base_confidence + 0.06),
            "expected_resource_cost": clamp(complexity + 0.15),
            "potential_generalization": 0.55,
            "reason": "Explicit search gives reflection more observable alternatives.",
        })
    return alternatives


def _counterfactual_review(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    alternatives: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    outcome = str(episode.get("episode_outcome") or "UNRESOLVED")
    return [
        {
            "counterfactual": "What if a different search route had been selected?",
            "expected_outcome": "lower_resource_cost"
            if dimensions["Search"]["dead_ends"]
            else "similar_outcome_with_comparable_cost",
            "confidence": clamp(dimensions["Search"]["route_quality"]),
        },
        {
            "counterfactual": "What if more evidence had been required before truth validation?",
            "expected_outcome": "higher_truth_confidence"
            if dimensions["Evidence"]["gaps"] or dimensions["Truth"]["uncertainty"] > 0.4
            else outcome,
            "confidence": clamp(dimensions["Evidence"]["sufficiency"]),
        },
        {
            "counterfactual": "What if the best alternative strategy had been used?",
            "expected_outcome": alternatives[0]["strategy"] if alternatives else "no_alternative_available",
            "confidence": alternatives[0]["expected_confidence"] if alternatives else 0.0,
        },
    ]


def _assumption_analysis(
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> dict[str, list[str]]:
    correct = []
    incorrect = []
    unverified = []
    unsupported = []
    risky = []
    necessary = []
    optional = []
    hidden = []
    for obj in objects:
        object_id = str(obj.get("object_id"))
        object_type = str(obj.get("object_type"))
        confidence = float(obj.get("object_confidence", obj.get("confidence", 0.0)) or 0.0)
        if object_type in {"TRUTH", "EVIDENCE"} and confidence >= 0.75:
            correct.append(object_id)
        elif confidence < 0.5:
            risky.append(object_id)
        if object_type in {"CONCEPT", "PROGRAM"}:
            necessary.append(object_id)
        if object_type in {"OBSERVATION", "SEMANTIC_CONTEXT"}:
            optional.append(object_id)
        if not obj.get("supporting_objects") and object_type in {"TRUTH", "PROGRAM"}:
            unsupported.append(object_id)
        if not obj.get("relationships") and object_type in {"CONCEPT", "REASONING_STEP"}:
            hidden.append(object_id)
    if dimensions["Truth"]["uncertainty"] > 0.5:
        unverified.append("truth_outcome_requires_additional_validation")
    if dimensions["Evidence"]["conflicts"]:
        incorrect.append("conflicting_evidence_assumption")
    return {
        "correct": correct,
        "incorrect": incorrect,
        "unverified": unverified,
        "unsupported": unsupported,
        "risky": risky,
        "necessary": necessary,
        "optional": optional,
        "hidden": hidden,
    }


def _uncertainty_analysis(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    low_confidence = [
        str(obj.get("object_id"))
        for obj in objects
        if float(obj.get("object_confidence", obj.get("confidence", 0.0)) or 0.0) < 0.5
    ]
    sources = []
    if dimensions["Evidence"]["gaps"]:
        sources.append("evidence_gap")
    if dimensions["Truth"]["uncertainty"] > 0.4:
        sources.append("truth_uncertainty")
    if low_confidence:
        sources.append("low_confidence_objects")
    if episode.get("episode_outcome") in {"UNRESOLVED", "PARTIAL_SUCCESS"}:
        sources.append("incomplete_episode_resolution")
    return {
        "uncertainty_sources": sources or ["no_major_uncertainty_source_detected"],
        "uncertainty_propagation": _causal_chain(episode, objects),
        "confidence_collapse": len(low_confidence) > max(len(objects) // 2, 0),
        "evidence_ambiguity": dimensions["Evidence"]["conflicts"] > 0,
        "competing_hypotheses": max(dimensions["Reasoning"]["branching"], 0),
        "decision_ambiguity": dimensions["Decision Making"]["risky_decisions"] > 0,
        "unknown_knowledge": dimensions["Evidence"]["gaps"],
        "certainty": clamp(1.0 - dimensions["Truth"]["uncertainty"]),
        "confidence": float(episode.get("episode_confidence", 0.0) or 0.0),
    }


def _decision_justifications(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    decision_objects = [obj for obj in objects if obj.get("object_type") == "DECISION"]
    if not decision_objects:
        return [{
            "decision": "implicit_episode_strategy",
            "reason": "No explicit decision object was published; reflection inferred the decision chain from episode structure.",
            "evidence": list(episode.get("content", {}).get("evidence_objects", [])),
            "alternatives": ["evidence_first", "search_pruning", "concept_minimization"],
            "expected_outcome": episode.get("episode_outcome"),
            "observed_outcome": episode.get("episode_outcome"),
            "justification_confidence": _average([
                dimensions["Reasoning"]["stability"],
                dimensions["Evidence"]["sufficiency"],
                dimensions["Truth"]["confidence"],
            ]),
        }]
    return [
        {
            "decision": obj.get("object_id"),
            "reason": obj.get("behavior_payload", {}).get("decision", "decision_published_by_runtime"),
            "evidence": obj.get("supporting_objects", []),
            "alternatives": obj.get("optional_objects", []),
            "expected_outcome": obj.get("behavior_payload", {}).get("expected_outcome"),
            "observed_outcome": episode.get("episode_outcome"),
            "justification_confidence": obj.get("object_confidence", 0.0),
        }
        for obj in decision_objects
    ]


def _bias_detection(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    signals = []
    if dimensions["Search"]["exploration"] <= 1 and dimensions["Truth"]["promotion"] > 0:
        signals.append("premature_convergence")
    if dimensions["Search"]["dead_ends"] > 0:
        signals.append("search_fixation")
    if dimensions["Evidence"]["redundancy"] > 0.5:
        signals.append("confirmation_bias")
    if dimensions["Evidence"]["diversity"] < 0.1 and dimensions["Truth"]["promotion"] > 0:
        signals.append("evidence_imbalance")
    if dimensions["Concept Formation"]["concept_redundancy"] > 0.4:
        signals.append("concept_fixation")
    if episode.get("episode_outcome") == "SUCCESS" and dimensions["Evidence"]["sufficiency"] < 1.0:
        signals.append("accidental_success_risk")
    return {
        "biases_detected": signals,
        "bias_count": len(signals),
        "bias_risk": "high" if len(signals) >= 3 else "medium" if signals else "low",
        "automatic_detection": True,
    }


def _success_analysis(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    causal: Mapping[str, Any],
) -> dict[str, Any]:
    if episode.get("episode_outcome") != "SUCCESS":
        return {"success_detected": False, "reason": "episode_outcome_not_success"}
    return {
        "success_detected": True,
        "why_success_occurred": causal.get("root_causes", []),
        "reasoning_strategy_contribution": dimensions["Reasoning"]["convergence"],
        "valuable_concepts": dimensions["Concept Formation"]["useful_concepts"],
        "decisive_evidence": dimensions["Evidence"]["sufficiency"],
        "optimal_search_path": dimensions["Search"]["route_quality"],
        "convergence_accelerating_decisions": dimensions["Governance Decisions"]["uncertainty_reduced"],
        "resource_efficiency": dimensions["Resource Allocation"]["efficiency_score"],
        "reproducible_success": dimensions["Evidence"]["sufficiency"] >= 1.0
        and dimensions["Truth"]["confidence"] >= 0.75,
    }


def _failure_analysis(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    causal: Mapping[str, Any],
) -> dict[str, Any]:
    failed = episode.get("episode_outcome") in {"FAILURE", "UNRESOLVED", "INTERRUPTED"}
    lessons = _failure_lessons(dimensions)
    return {
        "failure_detected": failed,
        "lessons_extracted": lessons,
        "missing_concepts": dimensions["Concept Formation"]["useful_concepts"] == 0,
        "weak_evidence": dimensions["Evidence"]["sufficiency"] < 1.0,
        "incorrect_assumptions": causal.get("blocking_causes", []),
        "invalid_reasoning": dimensions["Reasoning"]["stability"] < 0.5,
        "poor_search_strategy": dimensions["Search"]["route_quality"] < 0.5,
        "premature_decisions": dimensions["Decision Making"]["early_decisions"],
        "late_decisions": dimensions["Decision Making"]["late_decisions"],
        "boundary_violations": dimensions["Governance Decisions"]["governance_pressure"] > 0.5,
        "resource_exhaustion": dimensions["Resource Allocation"]["resource_limitation_detected"],
    }


def _failure_lessons(dimensions: Mapping[str, Mapping[str, Any]]) -> list[str]:
    lessons = []
    if dimensions["Concept Formation"]["useful_concepts"] == 0:
        lessons.append("introduce_missing_concepts_before_program_synthesis")
    if dimensions["Evidence"]["sufficiency"] < 1.0:
        lessons.append("strengthen_evidence_before_truth_promotion")
    if dimensions["Reasoning"]["stability"] < 0.5:
        lessons.append("stabilize_reasoning_before_decision")
    if dimensions["Search"]["route_quality"] < 0.5:
        lessons.append("improve_search_strategy")
    if dimensions["Resource Allocation"]["resource_limitation_detected"]:
        lessons.append("separate_resource_limitations_from_reasoning_limitations")
    return lessons or ["preserve_failure_as_negative_training_signal"]


def _secondary_effects(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    effects = []
    if dimensions["Learning Behavior"]["adaptive_knowledge_created"]:
        effects.append("future_reasoning_can_reuse_episode_knowledge")
    if episode.get("episode_outcome") == "SUCCESS":
        effects.append("strategy_candidate_for_experience_engine")
    if dimensions["Concept Formation"]["unused_concepts"]:
        effects.append("concept_library_requires_pruning_review")
    return effects


def _long_term_consequences(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    consequences = []
    if episode.get("episode_outcome") == "SUCCESS":
        consequences.append("success_pattern_can_be_promoted_to_reusable_strategy")
    if dimensions["Truth"]["uncertainty"] > 0.5:
        consequences.append("truth_model_should_delay_high_confidence_promotion")
    if dimensions["Resource Allocation"]["reasoning_limitation_detected"]:
        consequences.append("meta_cognition_should_monitor_low_confidence_reasoning")
    return consequences or ["episode_remains_available_for_future_reflective_comparison"]


def _causal_confidence(dimensions: Mapping[str, Mapping[str, Any]]) -> float:
    return _average([
        dimensions["Reasoning"]["continuity"],
        dimensions["Evidence"]["sufficiency"],
        dimensions["Truth"]["confidence"],
        dimensions["Resource Allocation"]["efficiency_score"],
    ])


def _best_strategy(
    alternatives: list[dict[str, Any]],
    current_efficiency: float,
    current_reuse: float,
) -> dict[str, Any]:
    current = {
        "strategy_id": "current",
        "strategy": "current_reasoning_strategy",
        "expected_efficiency": current_efficiency,
        "expected_confidence": current_reuse,
        "expected_resource_cost": 1.0 - current_efficiency,
        "potential_generalization": current_reuse,
    }
    candidates = [current, *alternatives]
    return max(
        candidates,
        key=lambda item: (
            item.get("expected_efficiency", 0.0)
            + item.get("expected_confidence", 0.0)
            + item.get("potential_generalization", 0.0)
            - item.get("expected_resource_cost", 0.0)
        ),
    )


def _generalization_opportunities(dimensions: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    opportunities = []
    if dimensions["Concept Formation"]["useful_concepts"]:
        opportunities.append({
            "opportunity": "concept_generalization",
            "score": clamp(dimensions["Concept Formation"]["generalized_concepts"] / max(dimensions["Concept Formation"]["useful_concepts"], 1)),
        })
    if dimensions["Program Synthesis"]["program_usefulness"] > 0:
        opportunities.append({
            "opportunity": "program_strategy_reuse",
            "score": dimensions["Program Synthesis"]["program_correctness"],
        })
    if dimensions["Evidence"]["sufficiency"] >= 1.0:
        opportunities.append({
            "opportunity": "evidence_pattern_transfer",
            "score": dimensions["Evidence"]["reliability"],
        })
    return opportunities


def _transfer_potential(
    dimensions: Mapping[str, Mapping[str, Any]],
    robustness: float,
    adaptability: float,
) -> list[dict[str, Any]]:
    base = _average([robustness, adaptability, dimensions["Resource Allocation"]["efficiency_score"]])
    return [
        {"transfer_type": "near_transfer", "transfer_score": clamp(base + 0.1)},
        {"transfer_type": "far_transfer", "transfer_score": clamp(base * 0.65)},
        {"transfer_type": "cross_domain_transfer", "transfer_score": clamp(dimensions["Concept Formation"]["generalized_concepts"] / 4.0)},
        {"transfer_type": "cross_task_transfer", "transfer_score": clamp(base * 0.75)},
        {"transfer_type": "cross_strategy_transfer", "transfer_score": clamp(dimensions["Program Synthesis"]["program_generality"] + 0.2)},
        {"transfer_type": "cross_context_transfer", "transfer_score": clamp(adaptability)},
    ]


def _reflection_recommendations(
    dimensions: Mapping[str, Mapping[str, Any]],
    strategy: Mapping[str, Any],
    learning_value: Mapping[str, Any],
) -> list[str]:
    recommendations = []
    if strategy.get("success_analysis", {}).get("reproducible_success"):
        recommendations.append("promote_strategy_candidate_to_experience_engine")
    if strategy.get("failure_analysis", {}).get("lessons_extracted"):
        recommendations.extend(strategy["failure_analysis"]["lessons_extracted"][:3])
    if learning_value.get("learning_value_score", 0.0) >= 0.7:
        recommendations.append("assign_high_long_term_memory_priority")
    if dimensions["Resource Allocation"]["resource_limitation_detected"]:
        recommendations.append("lower_future_resource_pressure_for_similar_tasks")
    return recommendations or ["retain_reflection_for_future_strategy_comparison"]


def _stable_id(prefix: str, *values: Any) -> str:
    digest = uuid5(NAMESPACE_URL, "|".join(str(value) for value in values)).hex[:16]
    return f"{prefix}:{digest}"


def _recommendation_validation(
    self_improvement: Mapping[str, Any],
    historical_reflections: list[ReflectionObject],
) -> dict[str, Any]:
    current = self_improvement.get("Improvement Plan", [])
    historical_plans = [
        plan
        for reflection in historical_reflections
        for plan in reflection.self_improvement_report.get("Improvement Plan", [])
    ]
    accepted = [plan for plan in historical_plans if plan.get("priority") in {"CRITICAL", "HIGH"}]
    rejected = [plan for plan in historical_plans if plan.get("priority") in {"LOW", "OPTIONAL"}]
    implemented = [
        plan for plan in historical_plans
        if plan.get("recommended_action") in str(self_improvement.get("Strengths", []))
    ]
    successful = [
        plan for plan in implemented
        if plan.get("confidence", 0.0) >= 0.5
    ]
    failed = [
        plan for plan in implemented
        if plan.get("confidence", 0.0) < 0.5
    ]
    return {
        "recommendations_tracked": len(current) + len(historical_plans),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "implemented": len(implemented),
        "successful": len(successful),
        "failed": len(failed),
        "partially_successful": max(len(implemented) - len(successful) - len(failed), 0),
        "validation_confidence": _average([
            len(successful) / max(len(implemented), 1),
            len(historical_reflections) / max(len(historical_reflections) + 1, 1),
            bool(current),
        ]),
    }


def _cognitive_maturity(
    dimensions: Mapping[str, Mapping[str, Any]],
    synthesis: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
    learning_value: Mapping[str, Any],
) -> dict[str, Any]:
    maturity = {
        "reasoning_maturity": dimensions["Reasoning"]["stability"],
        "search_maturity": dimensions["Search"]["route_quality"],
        "concept_maturity": clamp(dimensions["Concept Formation"]["useful_concepts"] / 4.0),
        "evidence_maturity": dimensions["Evidence"]["sufficiency"],
        "truth_maturity": dimensions["Truth"]["confidence"],
        "experience_maturity": _average(
            candidate.get("quality", 0.0)
            for candidate in synthesis.get("Experience Candidates", [])
        ),
        "generalization_maturity": learning_value.get("generalization", 0.0),
        "reflection_maturity": self_improvement.get("Reflection Quality Metrics", {}).get("confidence", 0.0),
    }
    maturity["overall_cognitive_maturity"] = _average(maturity.values())
    maturity["maturity_level"] = (
        "advanced" if maturity["overall_cognitive_maturity"] >= 0.75
        else "developing" if maturity["overall_cognitive_maturity"] >= 0.45
        else "early"
    )
    return maturity


def _long_term_trends(
    dimensions: Mapping[str, Mapping[str, Any]],
    learning_value: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
    historical_reflections: list[ReflectionObject],
) -> dict[str, Any]:
    previous_learning = [
        reflection.learning_value.get("learning_value_score", 0.0)
        for reflection in historical_reflections
    ]
    previous_quality = [
        reflection.self_improvement_report.get("Reflection Quality Metrics", {}).get("confidence", 0.0)
        for reflection in historical_reflections
    ]
    current_learning = learning_value.get("learning_value_score", 0.0)
    current_quality = self_improvement.get("Reflection Quality Metrics", {}).get("confidence", 0.0)
    return {
        "learning_speed": _trend_delta(current_learning, previous_learning),
        "knowledge_growth": len(self_improvement.get("Knowledge Promotions", [])),
        "reasoning_improvement": dimensions["Reasoning"]["stability"],
        "search_optimization": dimensions["Search"]["route_quality"],
        "generalization_growth": learning_value.get("generalization", 0.0),
        "transfer_growth": learning_value.get("transfer_potential", 0.0),
        "reflection_quality": current_quality,
        "reflection_quality_delta": _trend_delta(current_quality, previous_quality),
        "executive_decision_quality": _average(
            item.get("confidence", 0.0)
            for item in self_improvement.get("Improvement Plan", [])
        ),
        "trend_basis": "lifelong_reflection_memory",
    }


def _behavioral_evolution(
    strategy: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
    historical_reflections: list[ReflectionObject],
) -> dict[str, Any]:
    previous_best = [
        reflection.strategy_analysis.get("best_available_strategy", {}).get("strategy")
        for reflection in historical_reflections
    ]
    current = strategy.get("best_available_strategy", {}).get("strategy")
    stable = [current] if current and current in previous_best else []
    emerging = [current] if current and current not in previous_best else []
    changing = self_improvement.get("Recurring Patterns", {}).get("behavioral_trend") == "Unexpectedly Changing"
    return {
        "stable_behaviors": stable,
        "emerging_behaviors": emerging,
        "changing_behaviors": [current] if changing and current else [],
        "regressing_behaviors": [
            item["target"] for item in self_improvement.get("Weaknesses", [])
            if item.get("severity", 0.0) >= 0.6
        ],
        "unexpected_behaviors": self_improvement.get("Detected Conflicts", []),
        "adaptive_behaviors": [
            signal["recommended_action"]
            for signal in self_improvement.get("Learning Signals", [])
            if signal.get("priority") in {"HIGH", "CRITICAL"}
        ],
        "behavioral_trend": self_improvement.get("Recurring Patterns", {}).get("behavioral_trend", "Stable"),
    }


def _learning_trajectories(
    episode: Mapping[str, Any],
    synthesis: Mapping[str, Any],
    historical_reflections: list[ReflectionObject],
) -> list[dict[str, Any]]:
    trajectories = []
    for candidate in synthesis.get("Experience Candidates", []):
        trajectory = [
            {"stage": "Episode", "id": episode.get("episode_id"), "status": "observed"},
            {"stage": "Reflection", "id": episode.get("reflection_id"), "status": "completed"},
            {"stage": "Experience Candidate", "id": candidate.get("experience_candidate_id"), "status": "candidate"},
            {"stage": "Experience", "id": None, "status": "requires_experience_engine"},
            {"stage": "Generalization", "id": candidate.get("generalizations", []), "status": "prepared"},
            {"stage": "Mental Model", "id": None, "status": "requires_future_discovery"},
            {"stage": "World Model", "id": None, "status": "prepared_not_written"},
            {"stage": "DNA Adaptation", "id": None, "status": "governance_required"},
        ]
        trajectories.append({
            "trajectory_id": _stable_id("trajectory", episode.get("episode_id"), candidate.get("experience_candidate_id")),
            "trajectory": trajectory,
            "historical_reflections_considered": len(historical_reflections),
            "reveals_intelligence_evolution": True,
        })
    return trajectories


def _knowledge_preservation_candidates(
    synthesis: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
) -> list[dict[str, Any]]:
    candidates = []
    for principle in synthesis.get("General Principles", []):
        if principle.get("confidence", 0.0) >= 0.5:
            candidates.append(_preservation("Core Reasoning Principle", principle["principle_id"], principle["confidence"]))
    for abstraction in synthesis.get("Abstractions Created", []):
        if abstraction.get("confidence", 0.0) >= 0.4:
            candidates.append(_preservation("Stable Abstraction", abstraction["abstraction_id"], abstraction["confidence"]))
    for promotion in self_improvement.get("Knowledge Promotions", []):
        candidates.append(_preservation("Canonical Strategy", promotion["knowledge_id"], promotion.get("promotion_confidence", 0.0)))
    for lesson in synthesis.get("Lessons Extracted", []):
        if lesson.get("confidence", 0.0) >= 0.6:
            candidates.append(_preservation("Fundamental Lesson", lesson["lesson_id"], lesson["confidence"]))
    for candidate in synthesis.get("Experience Candidates", []):
        if candidate.get("quality", 0.0) >= 0.4:
            candidates.append(_preservation("High-Value Experience", candidate["experience_candidate_id"], candidate["quality"]))
    return candidates


def _knowledge_forgetting_candidates(
    synthesis: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
) -> list[dict[str, Any]]:
    candidates = []
    for demotion in self_improvement.get("Knowledge Demotions", []):
        candidates.append({
            "forgetting_candidate_id": _stable_id("forget", demotion.get("knowledge_id")),
            "candidate_type": demotion.get("recommended_level", "Weak Knowledge"),
            "source_id": demotion.get("knowledge_id"),
            "reason": "future_preference_demote_not_history_deletion",
            "delete_history": False,
            "governance_required": True,
            "confidence": demotion.get("demotion_confidence", 0.0),
        })
    for separated in synthesis.get("Separated Knowledge", []):
        candidates.append({
            "forgetting_candidate_id": _stable_id("forget", separated.get("separation_id")),
            "candidate_type": "Temporary Heuristic",
            "source_id": separated.get("source"),
            "reason": separated.get("reason"),
            "delete_history": False,
            "governance_required": True,
            "confidence": 0.5,
        })
    return candidates


def _adaptive_signals(
    dimensions: Mapping[str, Mapping[str, Any]],
    strategy: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
    synthesis: Mapping[str, Any],
) -> list[dict[str, Any]]:
    signals = [
        _adaptive_signal("Behavioral Signal", "strategy_reuse", strategy.get("strategy_reuse", 0.0)),
        _adaptive_signal("Adaptive Signal", "learning_priority", len(self_improvement.get("Learning Signals", [])) / 8.0),
        _adaptive_signal("Stability Signal", "truth_consistency", dimensions["Truth"]["consistency"]),
        _adaptive_signal("Curiosity Signal", "explore_transfer_opportunities", len(synthesis.get("Transfer Opportunities", [])) / 8.0),
        _adaptive_signal("Risk Signal", "strategy_risk", strategy.get("strategy_risk", 0.0)),
    ]
    return signals


def _executive_recommendations(
    self_improvement: Mapping[str, Any],
    synthesis: Mapping[str, Any],
    adaptive: list[dict[str, Any]],
    preservation: list[dict[str, Any]],
    forgetting: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    recommendations = []
    for plan in self_improvement.get("Improvement Plan", [])[:8]:
        recommendations.append({
            "recommendation_id": _stable_id("executive_recommendation", plan.get("plan_id"), plan.get("recommended_action")),
            "recommendation_type": "Improvement Opportunity",
            "recommendation": plan.get("recommended_action"),
            "priority": plan.get("priority"),
            "confidence": plan.get("confidence", 0.0),
            "executive_governance_decides": True,
        })
    for candidate in synthesis.get("Experience Candidates", []):
        recommendations.append({
            "recommendation_id": _stable_id("executive_recommendation", candidate.get("experience_candidate_id")),
            "recommendation_type": "Experience Candidate Review",
            "recommendation": "evaluate_experience_candidate_for_promotion",
            "priority": "HIGH" if candidate.get("qualified") else "MEDIUM",
            "confidence": candidate.get("confidence", 0.0),
            "executive_governance_decides": True,
        })
    for item in preservation[:5]:
        recommendations.append({
            "recommendation_id": _stable_id("executive_recommendation", item.get("source_id"), "preserve"),
            "recommendation_type": "Knowledge Preservation",
            "recommendation": "preserve_high_value_reflective_knowledge",
            "priority": "HIGH",
            "confidence": item.get("confidence", 0.0),
            "executive_governance_decides": True,
        })
    for item in forgetting[:5]:
        recommendations.append({
            "recommendation_id": _stable_id("executive_recommendation", item.get("source_id"), "forget"),
            "recommendation_type": "Governed Forgetting",
            "recommendation": "reduce_future_preference_without_deleting_history",
            "priority": "MEDIUM",
            "confidence": item.get("confidence", 0.0),
            "executive_governance_decides": True,
        })
    for signal in adaptive:
        if signal["priority"] in {"HIGH", "CRITICAL"}:
            recommendations.append({
                "recommendation_id": _stable_id("executive_recommendation", signal.get("signal_type"), signal.get("target")),
                "recommendation_type": "Adaptive Evolution",
                "recommendation": signal.get("recommended_action"),
                "priority": signal.get("priority"),
                "confidence": signal.get("confidence"),
                "executive_governance_decides": True,
            })
    return recommendations


def _world_model_preparation(synthesis: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "forwards_raw_episodes": False,
        "experience_candidates": synthesis.get("Experience Candidates", []),
        "general_principles": synthesis.get("General Principles", []),
        "stable_abstractions": synthesis.get("Abstractions Created", []),
        "transfer_rules": synthesis.get("Transfer Opportunities", []),
        "boundary_conditions": synthesis.get("Exceptions", []),
        "semantic_refinement_complete": True,
        "world_model_write_authorized": False,
    }


def _dna_preparation(
    adaptive: list[dict[str, Any]],
    behavioral: Mapping[str, Any],
    maturity: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "modifies_dna_directly": False,
        "behavioral_signals": [item for item in adaptive if item["signal_type"] == "Behavioral Signal"],
        "adaptive_signals": [item for item in adaptive if item["signal_type"] == "Adaptive Signal"],
        "stability_signals": [item for item in adaptive if item["signal_type"] == "Stability Signal"],
        "curiosity_signals": [item for item in adaptive if item["signal_type"] == "Curiosity Signal"],
        "risk_signals": [item for item in adaptive if item["signal_type"] == "Risk Signal"],
        "behavioral_evolution": dict(behavioral),
        "cognitive_maturity": maturity.get("overall_cognitive_maturity", 0.0),
        "executive_governance_and_dna_decide": True,
    }


def _meta_cognitive_feedback(
    self_improvement: Mapping[str, Any],
    synthesis: Mapping[str, Any],
    maturity: Mapping[str, Any],
    behavioral: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "reflection_quality": self_improvement.get("Reflection Quality Metrics", {}),
        "recommendation_quality": validation,
        "learning_trajectory_count": len(synthesis.get("Experience Candidates", [])),
        "cognitive_maturity": maturity,
        "behavioral_evolution": behavioral,
        "recursive_improvement": self_improvement.get("Self Assessment", {}),
        "meta_cognition_should_evaluate": True,
    }


def _reflection_knowledge_graph(
    episode: Mapping[str, Any],
    self_improvement: Mapping[str, Any],
    synthesis: Mapping[str, Any],
    trajectories: list[dict[str, Any]],
    executive: list[dict[str, Any]],
    historical_reflections: list[ReflectionObject],
) -> dict[str, Any]:
    nodes = []
    edges = []

    def add_node(node_id: Any, node_type: str, **payload: Any) -> None:
        if not node_id:
            return
        nodes.append({"id": str(node_id), "type": node_type, **payload})

    def add_edge(source: Any, target: Any, relation: str) -> None:
        if source and target and source != target:
            edges.append({"source": str(source), "target": str(target), "relation": relation})

    reflection_id = episode.get("reflection_id") or _stable_id("reflection", episode.get("episode_id"))
    add_node(reflection_id, "Reflection", episode_id=episode.get("episode_id"))
    for historical in historical_reflections[-10:]:
        add_node(historical.reflection_id, "Reflection")
        add_edge(historical.reflection_id, reflection_id, "SUPPORTS")
    for lesson in synthesis.get("Lessons Extracted", []):
        add_node(lesson["lesson_id"], "Lesson", lesson_type=lesson.get("lesson_type"))
        add_edge(reflection_id, lesson["lesson_id"], "DERIVED_FROM")
    for abstraction in synthesis.get("Abstractions Created", []):
        add_node(abstraction["abstraction_id"], "General Principle" if abstraction["abstraction_level"] in {"Mental Principle", "Cognitive Law"} else "Abstraction")
        add_edge(reflection_id, abstraction["abstraction_id"], "GENERALIZES")
    for principle in synthesis.get("General Principles", []):
        add_node(principle["principle_id"], "General Principle")
        add_edge(reflection_id, principle["principle_id"], "EXPLAINS")
    for candidate in synthesis.get("Experience Candidates", []):
        add_node(candidate["experience_candidate_id"], "Experience Candidate")
        add_edge(reflection_id, candidate["experience_candidate_id"], "IMPROVES")
    for recommendation in executive:
        add_node(recommendation["recommendation_id"], "Recommendation")
        add_edge(reflection_id, recommendation["recommendation_id"], "IMPROVES")
    for pattern, value in self_improvement.get("Recurring Patterns", {}).items():
        node_id = _stable_id("behavioral_pattern", pattern, value)
        add_node(node_id, "Behavioral Pattern", pattern=pattern, value=value)
        add_edge(reflection_id, node_id, "EXPLAINS")
    for trajectory in trajectories:
        add_node(trajectory["trajectory_id"], "Learning Trajectory")
        add_edge(reflection_id, trajectory["trajectory_id"], "DERIVED_FROM")
    for conflict in self_improvement.get("Detected Conflicts", []):
        node_id = _stable_id("conflict", conflict.get("source"), conflict.get("target"))
        add_node(node_id, "Conflict")
        add_edge(reflection_id, node_id, "CONTRADICTS")
    edges = _dedupe_edges_generic(edges)
    nodes = _dedupe_nodes(nodes)
    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_types": _distribution(node["type"] for node in nodes),
        "edge_types": _distribution(edge["relation"] for edge in edges),
        "architectural_memory_of_reflective_intelligence": True,
    }


def _reflection_confidence_evolution(
    episode: Mapping[str, Any],
    learning_value: Mapping[str, Any],
    validation: Mapping[str, Any],
    historical_reflections: list[ReflectionObject],
) -> dict[str, Any]:
    prior = _average(reflection.reflection_confidence for reflection in historical_reflections)
    current = float(episode.get("episode_confidence", 0.0) or 0.0)
    success_factor = validation.get("validation_confidence", 0.0)
    generalization = learning_value.get("generalization", 0.0)
    evolved = _average([current, success_factor, generalization, learning_value.get("learning_value_score", 0.0)])
    return {
        "analysis_confidence": current,
        "causal_confidence": success_factor,
        "decision_confidence": validation.get("validation_confidence", 0.0),
        "generalization_confidence": generalization,
        "transfer_confidence": learning_value.get("transfer_potential", 0.0),
        "overall_reflection_confidence": evolved,
        "previous_average_confidence": prior,
        "confidence_delta": round(evolved - prior, 4) if historical_reflections else 0.0,
        "trust_direction": "increasing" if historical_reflections and evolved > prior else "decreasing" if historical_reflections and evolved < prior else "initial",
    }


def _recommendation_statistics(
    self_improvement: Mapping[str, Any],
    executive: list[dict[str, Any]],
) -> dict[str, Any]:
    priorities = _distribution(item.get("priority") for item in executive)
    return {
        "self_improvement_recommendations": len(self_improvement.get("Improvement Plan", [])),
        "executive_recommendations": len(executive),
        "priority_distribution": priorities,
        "average_confidence": _average(item.get("confidence", 0.0) for item in executive),
    }


def _knowledge_gaps(
    dimensions: Mapping[str, Mapping[str, Any]],
    causal: Mapping[str, Any],
) -> list[str]:
    gaps = []
    if dimensions["Evidence"]["gaps"]:
        gaps.append("evidence_gap")
    if dimensions["Concept Formation"]["useful_concepts"] == 0:
        gaps.append("concept_gap")
    if dimensions["Truth"]["uncertainty"] > 0.5:
        gaps.append("truth_uncertainty_gap")
    gaps.extend(str(item) for item in causal.get("hidden_causes", []))
    return gaps or ["no_major_knowledge_gap_detected"]



def _supporting_object_ids(objects: list[dict[str, Any]], marker: str) -> list[str]:
    refs = []
    for obj in objects:
        object_id = str(obj.get("object_id"))
        if not object_id:
            continue
        payload = repr(obj)
        if marker in object_id or marker in payload:
            refs.append(object_id)
    return refs[:8]


def _lesson_confidence(lesson_type: str, strategy: Mapping[str, Any]) -> float:
    base = {
        "Successful Strategy": strategy.get("strategy_quality", 0.5),
        "Avoidable Mistake": strategy.get("strategy_risk", 0.5),
        "Critical Evidence": strategy.get("success_analysis", {}).get("decisive_evidence", 0.5),
        "Useful Concept": 0.65,
        "Reusable Reasoning": strategy.get("strategy_reuse", 0.5),
        "Boundary Condition": 0.75,
        "Failure Indicator": 0.7,
        "Optimization Opportunity": 0.6,
    }.get(lesson_type, 0.5)
    return round(clamp(base), 4)


def _dedupe_by_key(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    deduped = {}
    for item in items:
        marker = str(item.get(key) or item)
        deduped[marker] = item
    return list(deduped.values())


def _structure_coherence(
    name: str,
    dimensions: Mapping[str, Mapping[str, Any]],
) -> float:
    if "concept" in name:
        return _average([dimensions["Concept Formation"]["useful_concepts"] > 0, dimensions["Evidence"]["sufficiency"], dimensions["Truth"]["confidence"]])
    if "reasoning" in name:
        return _average([dimensions["Reasoning"]["stability"], dimensions["Search"]["route_quality"], dimensions["Decision Making"]["safe_decisions"] > 0])
    return _average([dimensions["Execution Strategy"]["strategy_value"], dimensions["Learning Behavior"]["adaptive_knowledge_created"]])


def _experience_candidate_score(
    episode: Mapping[str, Any],
    learning_value: Mapping[str, Any],
    strategy: Mapping[str, Any],
    transfer: list[dict[str, Any]],
) -> float:
    outcome_quality = {
        "SUCCESS": 1.0,
        "PARTIAL_SUCCESS": 0.65,
        "FAILURE": 0.35,
        "UNRESOLVED": 0.25,
        "INTERRUPTED": 0.1,
    }.get(str(episode.get("episode_outcome")), 0.2)
    return _average([
        learning_value.get("reflection_depth", 0.0),
        learning_value.get("learning_value_score", 0.0),
        learning_value.get("novelty", 0.0),
        _average(item.get("transfer_score", 0.0) for item in transfer),
        learning_value.get("generalization", 0.0),
        outcome_quality,
        strategy.get("strategy_quality", 0.0),
        episode.get("episode_confidence", 0.0),
    ])


def _experience_qualification_reasons(
    episode: Mapping[str, Any],
    learning_value: Mapping[str, Any],
    strategy: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    lessons: list[dict[str, Any]],
) -> list[str]:
    reasons = []
    if learning_value.get("reflection_depth", 0.0) >= 0.5:
        reasons.append("reflection_depth_sufficient")
    if lessons:
        reasons.append("lessons_extracted")
    if strategy.get("transfer_opportunities"):
        reasons.append("transfer_opportunities_available")
    if learning_value.get("generalization", 0.0) > 0:
        reasons.append("generalization_detected")
    if episode.get("episode_outcome") == "SUCCESS":
        reasons.append("successful_outcome")
    elif dimensions["Learning Behavior"]["adaptive_knowledge_created"]:
        reasons.append("adaptive_knowledge_created")
    return reasons


def _principle(principle_type: str, principle: str, confidence: float) -> dict[str, Any]:
    return {
        "principle_id": _stable_id("principle", principle_type, principle),
        "principle_type": principle_type,
        "principle": principle,
        "confidence": round(clamp(confidence), 4),
        "reusable_cognitive_asset": True,
    }


def _exception(exception_type: str, condition: str, handling: str) -> dict[str, Any]:
    return {
        "exception_id": _stable_id("exception", exception_type, condition),
        "exception_type": exception_type,
        "condition": condition,
        "handling": handling,
        "prevents_overgeneralization": True,
    }


def _transfer_scope(transfer_type: str) -> str:
    mapping = {
        "near_transfer": "tasks",
        "far_transfer": "problems",
        "cross_domain_transfer": "domains",
        "cross_task_transfer": "tasks",
        "cross_strategy_transfer": "strategies",
        "cross_context_transfer": "situations",
    }
    return mapping.get(str(transfer_type), "problems")


def _trend_delta(current: float, previous: list[float]) -> dict[str, Any]:
    baseline = _average(previous)
    delta = round(float(current or 0.0) - baseline, 4) if previous else 0.0
    return {
        "current": round(float(current or 0.0), 4),
        "previous_average": baseline,
        "delta": delta,
        "trend": "Improving" if delta > 0.05 else "Regressing" if delta < -0.05 else "Stable" if previous else "Initial",
    }


def _preservation(candidate_type: str, source_id: str, confidence: float) -> dict[str, Any]:
    return {
        "preservation_candidate_id": _stable_id("preserve", candidate_type, source_id),
        "candidate_type": candidate_type,
        "source_id": source_id,
        "confidence": round(clamp(confidence), 4),
        "forward_to_experience_engine": True,
        "forward_to_executive_governance": True,
        "requires_governance_approval": True,
    }


def _adaptive_signal(signal_type: str, target: str, confidence: float) -> dict[str, Any]:
    confidence = clamp(confidence)
    priority = "CRITICAL" if confidence >= 0.9 else "HIGH" if confidence >= 0.65 else "MEDIUM" if confidence >= 0.35 else "LOW"
    action = {
        "Behavioral Signal": "review_behavioral_strategy_bias",
        "Adaptive Signal": "adjust_learning_priorities",
        "Stability Signal": "preserve_stable_cognitive_pattern",
        "Curiosity Signal": "increase_guided_exploration",
        "Risk Signal": "reduce_or_guard_risky_strategy",
    }.get(signal_type, "review_adaptive_signal")
    return {
        "signal_id": _stable_id("adaptive_signal", signal_type, target),
        "signal_type": signal_type,
        "target": target,
        "confidence": round(confidence, 4),
        "priority": priority,
        "recommended_action": action,
        "dna_may_evaluate": True,
        "reflection_modifies_dna": False,
    }


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = {}
    for node in nodes:
        deduped[str(node.get("id"))] = node
    return list(deduped.values())


def _dedupe_edges_generic(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for edge in edges:
        marker = (edge.get("source"), edge.get("target"), edge.get("relation"))
        if marker in seen:
            continue
        seen.add(marker)
        output.append(edge)
    return output


def _cognitive_strengths(
    episode: Mapping[str, Any],
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
    strategy: Mapping[str, Any],
) -> list[dict[str, Any]]:
    strengths = []
    if dimensions["Reasoning"]["stability"] >= 0.7:
        strengths.append(_strength("reliable_reasoning_pattern", "reasoning", dimensions["Reasoning"]["stability"]))
    stable_concepts = [
        obj.get("object_id")
        for obj in objects
        if obj.get("object_type") == "CONCEPT" and obj.get("object_confidence", 0.0) >= 0.75
    ]
    for concept_id in stable_concepts[:5]:
        strengths.append(_strength("stable_concept", str(concept_id), 0.8))
    if strategy.get("strategy_reuse", 0.0) >= 0.5:
        strengths.append(_strength("highly_reusable_strategy", "current_strategy", strategy["strategy_reuse"]))
    if dimensions["Search"]["route_quality"] >= 0.75:
        strengths.append(_strength("efficient_search_behavior", "search", dimensions["Search"]["route_quality"]))
    if dimensions["Evidence"]["sufficiency"] >= 1.0:
        strengths.append(_strength("strong_evidence_generation", "evidence", dimensions["Evidence"]["sufficiency"]))
    if dimensions["Truth"]["confidence"] >= 0.75:
        strengths.append(_strength("accurate_truth_validation", "truth", dimensions["Truth"]["confidence"]))
    if dimensions["Decision Making"]["safe_decisions"] > 0:
        strengths.append(_strength("high_confidence_decisions", "decisions", clamp(dimensions["Decision Making"]["safe_decisions"] / max(len(objects), 1))))
    if strategy.get("generalization_opportunities"):
        strengths.append(_strength("successful_generalization", "generalization", len(strategy["generalization_opportunities"]) / 3.0))
    if not strengths and episode.get("episode_outcome") == "SUCCESS":
        strengths.append(_strength("successful_episode_completion", "episode", 0.6))
    return strengths


def _cognitive_weaknesses(
    dimensions: Mapping[str, Mapping[str, Any]],
    strategy: Mapping[str, Any],
    causal: Mapping[str, Any],
) -> list[dict[str, Any]]:
    weaknesses = []
    if dimensions["Reasoning"]["stability"] < 0.5:
        weaknesses.append(_weakness("repeated_reasoning_failure_risk", "reasoning", "stabilize_reasoning_before_decision"))
    if dimensions["Concept Formation"]["useful_concepts"] == 0:
        weaknesses.append(_weakness("weak_concept_formation", "concepts", "explore_alternative_concepts"))
    if dimensions["Evidence"]["sufficiency"] < 1.0:
        weaknesses.append(_weakness("evidence_shortage", "evidence", "increase_evidence_gathering"))
    if dimensions["Truth"]["uncertainty"] > 0.5:
        weaknesses.append(_weakness("unstable_truth_candidates", "truth", "strengthen_validation"))
    if dimensions["Search"]["route_quality"] < 0.75 or dimensions["Search"]["dead_ends"]:
        weaknesses.append(_weakness("search_inefficiency", "search", "reduce_search_redundancy"))
    if strategy.get("strategy_risk", 0.0) > 0.5:
        weaknesses.append(_weakness("poor_strategy_selection_risk", "strategy", "adjust_reasoning_priority"))
    if _average(item.get("transfer_score", 0.0) for item in strategy.get("transfer_opportunities", [])) < 0.4:
        weaknesses.append(_weakness("low_transferability", "transfer", "improve_abstraction_quality"))
    if dimensions["Resource Allocation"]["resource_limitation_detected"]:
        weaknesses.append(_weakness("resource_waste", "resources", "simplify_resource_usage"))
    for cause in causal.get("blocking_causes", [])[:3]:
        weaknesses.append(_weakness(str(cause), "causal_blocker", "resolve_blocking_cause"))
    return weaknesses


def _recurring_patterns(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    strategy: Mapping[str, Any],
    historical_reflections: list[ReflectionObject],
) -> dict[str, Any]:
    current_outcome = str(episode.get("episode_outcome") or "UNRESOLVED")
    previous_outcomes = [
        str(reflection.reflection_report.get("Episode Summary", ""))
        for reflection in historical_reflections
    ]
    previous_strategy_ids = [
        reflection.strategy_analysis.get("best_available_strategy", {}).get("strategy")
        for reflection in historical_reflections
        if reflection.strategy_analysis
    ]
    current_strategy = strategy.get("best_available_strategy", {}).get("strategy")
    repeated_strategy = bool(current_strategy and current_strategy in previous_strategy_ids)
    return {
        "previous_reflections_considered": len(historical_reflections),
        "repeated_successes": sum(1 for item in previous_outcomes if "SUCCESS" in item) + (1 if current_outcome == "SUCCESS" else 0),
        "repeated_failures": sum(1 for item in previous_outcomes if "FAILURE" in item) + (1 if current_outcome == "FAILURE" else 0),
        "repeated_mistakes": sum(
            1 for reflection in historical_reflections
            if reflection.self_improvement_report.get("Weaknesses")
        ) + (1 if _cognitive_weaknesses(dimensions, strategy, {}) else 0),
        "repeated_reasoning_paths": dimensions["Reasoning"]["depth"] > 0 and len(historical_reflections) > 0,
        "repeated_search_strategies": repeated_strategy,
        "repeated_concept_evolution": dimensions["Concept Formation"]["generalized_concepts"] > 0,
        "repeated_execution_bottlenecks": dimensions["Resource Allocation"]["resource_limitation_detected"],
        "behavioral_trend": _behavioral_trend(current_outcome, historical_reflections),
    }


def _knowledge_promotions(
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
    strategy: Mapping[str, Any],
) -> list[dict[str, Any]]:
    promotions = []
    for obj in objects:
        object_type = str(obj.get("object_type"))
        confidence = float(obj.get("object_confidence", obj.get("confidence", 0.0)) or 0.0)
        if object_type == "CONCEPT" and confidence >= 0.75:
            promotions.append(_promotion(obj, "Validated Concept", "confidence_and_evidence"))
        elif object_type == "TRUTH" and confidence >= 0.8:
            promotions.append(_promotion(obj, "Stable Knowledge", "truth_confidence"))
        elif object_type == "EVIDENCE" and dimensions["Evidence"]["reliability"] >= 0.75:
            promotions.append(_promotion(obj, "Reliable Evidence Pattern", "evidence_reliability"))
        elif object_type == "PROGRAM" and strategy.get("strategy_reuse", 0.0) >= 0.5:
            promotions.append(_promotion(obj, "Validated Reasoning Strategy", "strategy_reuse"))
    if strategy.get("success_analysis", {}).get("reproducible_success"):
        promotions.append({
            "knowledge_id": "current_episode_strategy",
            "current_level": "Candidate Strategy",
            "recommended_level": "Canonical Knowledge",
            "evidence": ["reproducible_success", "truth_validation", "evidence_sufficiency"],
            "promotion_confidence": strategy.get("strategy_quality", 0.0),
        })
    return promotions


def _knowledge_demotions(
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
    causal: Mapping[str, Any],
) -> list[dict[str, Any]]:
    demotions = []
    for obj in objects:
        object_type = str(obj.get("object_type"))
        confidence = float(obj.get("object_confidence", obj.get("confidence", 0.0)) or 0.0)
        if confidence < 0.4 and object_type in {"CONCEPT", "TRUTH", "PROGRAM", "SEARCH_ROUTE"}:
            level = "Retired Knowledge" if object_type in {"TRUTH", "PROGRAM"} else "Unsupported Hypothesis"
            demotions.append(_demotion(obj, level, "low_confidence"))
        if obj.get("object_status") == "RETIRED":
            demotions.append(_demotion(obj, "Retired Knowledge", "object_retired"))
    if dimensions["Concept Formation"]["unused_concepts"]:
        demotions.append({
            "knowledge_id": "unused_concepts",
            "current_level": "Candidate Concept",
            "recommended_level": "Weak Concept",
            "evidence": ["unused_concepts_detected"],
            "demotion_confidence": clamp(dimensions["Concept Formation"]["unused_concepts"] / 5.0),
        })
    for cause in causal.get("blocking_causes", [])[:2]:
        demotions.append({
            "knowledge_id": str(cause),
            "current_level": "Strategy Assumption",
            "recommended_level": "Deprecated Strategy",
            "evidence": [str(cause)],
            "demotion_confidence": 0.65,
        })
    return demotions


def _detected_conflicts(
    objects: list[dict[str, Any]],
    dimensions: Mapping[str, Mapping[str, Any]],
    second_order: Mapping[str, Any],
) -> list[dict[str, Any]]:
    conflicts = []
    for obj in objects:
        for relationship in obj.get("relationships", []) or []:
            if relationship.get("relationship_type") == "CONTRADICTS":
                conflicts.append({
                    "conflict_type": "Evidence",
                    "source": obj.get("object_id"),
                    "target": relationship.get("target"),
                    "classification": "Resolvable",
                    "confidence": obj.get("object_confidence", 0.0),
                })
    if dimensions["Truth"]["uncertainty"] > 0.5:
        conflicts.append({
            "conflict_type": "Truth",
            "source": "truth_uncertainty",
            "target": "episode_outcome",
            "classification": "Temporary",
            "confidence": dimensions["Truth"]["uncertainty"],
        })
    if second_order.get("bias_detection", {}).get("biases_detected"):
        conflicts.append({
            "conflict_type": "Mental Assumption",
            "source": "bias_detection",
            "target": ",".join(second_order["bias_detection"]["biases_detected"]),
            "classification": "Unknown",
            "confidence": clamp(second_order["bias_detection"]["bias_count"] / 5.0),
        })
    return conflicts


def _consistency_analysis(
    dimensions: Mapping[str, Mapping[str, Any]],
    conflicts: list[dict[str, Any]],
) -> dict[str, Any]:
    conflict_penalty = clamp(len(conflicts) / 5.0)
    return {
        "logical_consistency": clamp(dimensions["Truth"]["consistency"] - conflict_penalty * 0.2),
        "semantic_consistency": clamp(1.0 - dimensions["Concept Formation"]["concept_redundancy"]),
        "behavioral_consistency": dimensions["Reasoning"]["stability"],
        "strategic_consistency": clamp(1.0 - dimensions["Execution Strategy"]["avoid_repetition"] * 0.5),
        "knowledge_consistency": clamp(dimensions["Evidence"]["sufficiency"] - conflict_penalty * 0.1),
        "truth_consistency": dimensions["Truth"]["consistency"],
        "cognitive_drift_detected": conflict_penalty > 0.4 or dimensions["Truth"]["uncertainty"] > 0.6,
    }


def _learning_signals(
    strengths: list[dict[str, Any]],
    weaknesses: list[dict[str, Any]],
    promotions: list[dict[str, Any]],
    demotions: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    strategy: Mapping[str, Any],
    learning_value: Mapping[str, Any],
) -> list[dict[str, Any]]:
    signals = []
    for weakness in weaknesses:
        category = {
            "reasoning": "Reasoning Improvement",
            "concepts": "Concept Improvement",
            "evidence": "Evidence Improvement",
            "truth": "Truth Improvement",
            "search": "Search Improvement",
            "strategy": "Strategy Improvement",
            "transfer": "Generalization Improvement",
            "resources": "Governance Improvement",
        }.get(weakness["domain"], "Strategy Improvement")
        signals.append(_learning_signal(category, weakness["target"], weakness["recommendation"], weakness["severity"], learning_value))
    for promotion in promotions:
        signals.append(_learning_signal("Strategy Improvement", promotion["knowledge_id"], "protect_and_reuse_promoted_knowledge", promotion["promotion_confidence"], learning_value))
    for demotion in demotions:
        signals.append(_learning_signal("Truth Improvement", demotion["knowledge_id"], "downgrade_or_revalidate_weak_knowledge", demotion["demotion_confidence"], learning_value))
    for conflict in conflicts:
        signals.append(_learning_signal("Governance Improvement", conflict["source"], "resolve_detected_conflict", conflict["confidence"], learning_value))
    if strengths and not weaknesses:
        signals.append(_learning_signal("Strategy Improvement", "current_strategy", "preserve_successful_cognitive_asset", strategy.get("strategy_quality", 0.0), learning_value))
    return signals


def _improvement_priorities(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "signal_id": signal["signal_id"],
            "target": signal["target"],
            "priority": signal["priority"],
            "impact": signal["impact"],
            "frequency": signal["frequency"],
            "risk": signal["risk"],
            "generalization_value": signal["generalization_value"],
            "future_usefulness": signal["future_usefulness"],
        }
        for signal in signals
    ]


def _improvement_plan(
    signals: list[dict[str, Any]],
    causal: Mapping[str, Any],
    priorities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    priority_by_signal = {item["signal_id"]: item["priority"] for item in priorities}
    plans = []
    for index, signal in enumerate(signals):
        plans.append({
            "plan_id": f"improvement:{index + 1}",
            "current_limitation": signal["target"],
            "observed_evidence": signal["evidence"],
            "root_cause": causal.get("root_causes", ["unknown"])[0],
            "recommended_action": signal["recommended_action"],
            "expected_improvement": signal["expected_improvement"],
            "confidence": signal["confidence"],
            "priority": priority_by_signal.get(signal["signal_id"], signal["priority"]),
            "estimated_cost": signal["estimated_cost"],
            "dependencies": signal["dependencies"],
            "advisory_only": True,
            "execution_decides_adoption": True,
        })
    return plans


def _evolution_metrics(
    dimensions: Mapping[str, Mapping[str, Any]],
    strategy: Mapping[str, Any],
    learning_value: Mapping[str, Any],
    historical_reflections: list[ReflectionObject],
) -> dict[str, Any]:
    previous_learning = _average(
        reflection.learning_value.get("learning_value_score", 0.0)
        for reflection in historical_reflections
    )
    current_learning = learning_value.get("learning_value_score", 0.0)
    delta = round(current_learning - previous_learning, 4) if historical_reflections else 0.0
    return {
        "reasoning_evolution": dimensions["Reasoning"]["stability"],
        "concept_evolution": clamp(dimensions["Concept Formation"]["generalized_concepts"] / max(dimensions["Concept Formation"]["useful_concepts"], 1)),
        "strategy_evolution": strategy.get("strategy_quality", 0.0),
        "evidence_evolution": dimensions["Evidence"]["sufficiency"],
        "truth_evolution": dimensions["Truth"]["confidence"],
        "reflection_evolution": current_learning,
        "generalization_evolution": learning_value.get("generalization", 0.0),
        "adaptation_evolution": learning_value.get("transfer_potential", 0.0),
        "historical_reflections_considered": len(historical_reflections),
        "learning_value_delta": delta,
        "trajectory": "Improving" if delta > 0.05 else "Regressing" if delta < -0.05 else "Stable" if historical_reflections else "Unexpectedly Changing",
    }


def _reflection_memory_update(
    episode: Mapping[str, Any],
    strengths: list[dict[str, Any]],
    weaknesses: list[dict[str, Any]],
    recurring: Mapping[str, Any],
    plan: list[dict[str, Any]],
    learning_value: Mapping[str, Any],
    historical_reflections: list[ReflectionObject],
) -> dict[str, Any]:
    successful = [item for item in plan if item["priority"] in {"LOW", "OPTIONAL"}]
    rejected = [item for item in plan if item["estimated_cost"] == "high" and item["confidence"] < 0.5]
    return {
        "reflection_memory_enabled": True,
        "duplicates_episodic_memory": False,
        "memory_size_after_update": len(historical_reflections) + 1,
        "lessons_learned": [item["recommended_action"] for item in plan],
        "successful_improvements": [item["recommended_action"] for item in successful],
        "rejected_improvements": [item["recommended_action"] for item in rejected],
        "recurring_failures": recurring.get("repeated_failures", 0),
        "optimization_history": [item["plan_id"] for item in plan],
        "reflection_history": [reflection.reflection_id for reflection in historical_reflections[-10:]],
        "current_episode_id": episode.get("episode_id"),
        "protected_assets": [item["asset"] for item in strengths],
        "active_improvement_targets": [item["target"] for item in weaknesses],
        "long_term_importance": learning_value.get("long_term_importance", "low"),
    }


def _reflection_quality_metrics(
    dimensions: Mapping[str, Mapping[str, Any]],
    second_order: Mapping[str, Any],
    causal: Mapping[str, Any],
    strategy: Mapping[str, Any],
    learning_value: Mapping[str, Any],
    plan: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
) -> dict[str, float]:
    depth = _average([
        bool(second_order.get("alternative_reasoning_paths")),
        bool(second_order.get("counterfactual_review")),
        bool(causal.get("causal_chain_reconstruction")),
        bool(plan),
    ])
    completeness = _average([
        dimensions[key].get("evaluated", False)
        for key in REFLECTION_DIMENSIONS
    ])
    accuracy = _average([
        causal.get("causal_confidence", 0.0),
        dimensions["Truth"]["confidence"],
        dimensions["Evidence"]["reliability"],
    ])
    novelty = learning_value.get("novelty", 0.0)
    consistency = clamp(1.0 - len(conflicts) / 10.0)
    usefulness = learning_value.get("learning_value_score", 0.0)
    transferability = learning_value.get("transfer_potential", 0.0)
    actionability = clamp(len(plan) / 5.0)
    confidence = _average([accuracy, usefulness, actionability])
    return {
        "depth": depth,
        "completeness": completeness,
        "accuracy": accuracy,
        "novelty": novelty,
        "consistency": consistency,
        "usefulness": usefulness,
        "transferability": transferability,
        "actionability": actionability,
        "confidence": confidence,
    }


def _self_assessment(
    quality_metrics: Mapping[str, float],
    causal: Mapping[str, Any],
    plan: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "reflection_sufficiently_deep": quality_metrics.get("depth", 0.0) >= 0.75,
        "causal_explanations_complete": bool(causal.get("root_causes")) and bool(causal.get("causal_chain_reconstruction")),
        "recommendations_actionable": bool(plan) and quality_metrics.get("actionability", 0.0) > 0.0,
        "important_patterns_missed": False,
        "uncertainty_acknowledged": True,
        "self_improvement_quality": quality_metrics.get("confidence", 0.0),
    }


def _strength(kind: str, asset: str, confidence: float) -> dict[str, Any]:
    return {
        "strength": kind,
        "asset": asset,
        "confidence": round(clamp(confidence), 4),
        "protected_cognitive_asset": True,
    }


def _weakness(kind: str, domain: str, recommendation: str) -> dict[str, Any]:
    return {
        "weakness": kind,
        "domain": domain,
        "target": kind,
        "severity": 0.65,
        "recommendation": recommendation,
        "improvement_target": True,
    }


def _promotion(obj: Mapping[str, Any], level: str, evidence: str) -> dict[str, Any]:
    return {
        "knowledge_id": str(obj.get("object_id")),
        "current_level": str(obj.get("object_status") or "Observation"),
        "recommended_level": level,
        "evidence": [evidence],
        "promotion_confidence": round(clamp(obj.get("object_confidence", 0.0)), 4),
    }


def _demotion(obj: Mapping[str, Any], level: str, evidence: str) -> dict[str, Any]:
    return {
        "knowledge_id": str(obj.get("object_id")),
        "current_level": str(obj.get("object_status") or "Candidate"),
        "recommended_level": level,
        "evidence": [evidence],
        "demotion_confidence": round(clamp(1.0 - float(obj.get("object_confidence", 0.0) or 0.0)), 4),
    }


def _learning_signal(
    category: str,
    target: str,
    action: str,
    severity: float,
    learning_value: Mapping[str, Any],
) -> dict[str, Any]:
    severity = clamp(severity)
    generalization = clamp(learning_value.get("generalization", 0.0))
    usefulness = clamp(learning_value.get("transfer_potential", 0.0))
    risk = severity
    impact = _average([severity, learning_value.get("learning_value_score", 0.0), generalization])
    priority = _priority(impact, frequency=0.5, risk=risk, generalization=generalization, usefulness=usefulness)
    signal_id = uuid5(NAMESPACE_URL, f"{category}:{target}:{action}").hex[:12]
    return {
        "signal_id": f"learning_signal:{category.lower().replace(' ', '_')}:{signal_id}",
        "category": category,
        "target": str(target),
        "recommended_action": action,
        "evidence": [str(target), category],
        "impact": impact,
        "frequency": 0.5,
        "risk": risk,
        "generalization_value": generalization,
        "future_usefulness": usefulness,
        "priority": priority,
        "confidence": _average([impact, usefulness, 1.0 - risk * 0.25]),
        "expected_improvement": f"{category} through {action}",
        "estimated_cost": "high" if severity > 0.75 else "medium" if severity > 0.4 else "low",
        "dependencies": [],
    }


def _priority(
    impact: float,
    *,
    frequency: float,
    risk: float,
    generalization: float,
    usefulness: float,
) -> str:
    score = _average([impact, frequency, risk, generalization, usefulness])
    if score >= 0.85 or risk >= 0.9:
        return "CRITICAL"
    if score >= 0.65:
        return "HIGH"
    if score >= 0.45:
        return "MEDIUM"
    if score >= 0.25:
        return "LOW"
    return "OPTIONAL"


def _behavioral_trend(
    current_outcome: str,
    historical_reflections: list[ReflectionObject],
) -> str:
    if not historical_reflections:
        return "Unexpectedly Changing"
    previous_successes = sum(
        1 for reflection in historical_reflections
        if "SUCCESS" in str(reflection.reflection_report.get("Episode Summary", ""))
    )
    previous_failures = sum(
        1 for reflection in historical_reflections
        if "FAILURE" in str(reflection.reflection_report.get("Episode Summary", ""))
    )
    if current_outcome == "SUCCESS" and previous_failures > previous_successes:
        return "Improving"
    if current_outcome == "FAILURE" and previous_successes > previous_failures:
        return "Regressing"
    return "Stable"


def _why(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> str:
    outcome = episode.get("episode_outcome")
    if outcome == "SUCCESS":
        return "Truth validation and evidence-backed cognition converged."
    if outcome == "PARTIAL_SUCCESS":
        return "Some concepts or evidence emerged, but full truth validation did not converge."
    if dimensions["Resource Allocation"]["resource_limitation_detected"]:
        return "Resource pressure limited cognitive efficiency."
    if dimensions["Resource Allocation"]["reasoning_limitation_detected"]:
        return "Reasoning confidence stayed low despite cognitive activity."
    return "The episode preserved cognition but did not produce enough validated knowledge."


def _summary(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    answers: Mapping[str, Any],
) -> str:
    return (
        f"{episode.get('episode_outcome', 'UNRESOLVED')} reflection: "
        f"{answers.get('Why did it happen?', '')} "
        f"Repeat {', '.join(answers.get('What should be repeated?', [])[:2])}; "
        f"avoid {', '.join(answers.get('What should never be repeated?', [])[:2])}."
    )


def _reflection_confidence(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
) -> float:
    coverage = sum(1 for item in dimensions.values() if item.get("evaluated")) / max(len(REFLECTION_DIMENSIONS), 1)
    episode_confidence = float(episode.get("episode_confidence", 0.0) or 0.0)
    return round(clamp((coverage * 0.6) + (episode_confidence * 0.4)), 4)


def _reflection_quality(
    episode: Mapping[str, Any],
    dimensions: Mapping[str, Mapping[str, Any]],
    answers: Mapping[str, Any],
) -> float:
    report_coverage = len([question for question in REFLECTION_QUESTIONS if question in answers]) / len(REFLECTION_QUESTIONS)
    dimension_coverage = sum(1 for item in dimensions.values() if item.get("evaluated")) / max(len(REFLECTION_DIMENSIONS), 1)
    episode_quality = float(episode.get("episode_quality", 0.0) or 0.0)
    return round(clamp((report_coverage * 0.4) + (dimension_coverage * 0.4) + (episode_quality * 0.2)), 4)


def _ratio(selected: set[str], object_types: list[str]) -> float:
    return round(clamp(sum(1 for item in object_types if item in selected) / max(len(object_types), 1)), 4)


def _repeated(objects: list[dict[str, Any]], object_type: str) -> int:
    seen = set()
    repeated = 0
    for obj in objects:
        if obj.get("object_type") != object_type:
            continue
        signature = repr(sorted((obj.get("semantic_payload") or obj.get("canonical_payload") or {}).items()))
        if signature in seen:
            repeated += 1
        seen.add(signature)
    return repeated


def _novel(objects: list[dict[str, Any]], object_type: str) -> int:
    return sum(
        1
        for obj in objects
        if obj.get("object_type") == object_type and obj.get("object_novelty", 0.0) > 0
    )


def _distribution(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "Unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _average(values: Iterable[Any]) -> float:
    items = [float(value) for value in values]
    return round(sum(items) / len(items), 4) if items else 0.0


__all__ = [
    "REFLECTION_DIMENSIONS",
    "REFLECTION_QUESTIONS",
    "ReflectionEngine",
    "ReflectionObject",
    "ReflectionRegistry",
]
