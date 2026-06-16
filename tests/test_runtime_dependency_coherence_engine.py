from core.concept_lifecycle.concept_maturity import ConceptMaturityTracker
from core.context.context_strength_engine import ContextStrengthEngine
from core.context.process_context_generation import ProcessContextGenerationEngine
from core.dependency.process_dependency_memory import ProcessDependencyMemory
from core.math_reasoning import MathematicalReasoningLayer
from runtime.context.context_surface_engine import ContextSurfaceEngine
from runtime.dependency.dependency_coherence_engine import (
    DependencyCoherenceEngine,
)


def saturated_surface_evidence():
    return {
        "directions": ["up", "down", "left", "right", "diagonal"],
        "object_types": ["line", "block", "compound"],
        "colors": [1, 2, 3],
        "topologies": ["split", "hole", "branch", "nested"],
        "sizes": [1, 4, 9],
        "spatial_patterns": ["offset", "cross_axis", "nested", "gap"],
    }


def mature_concept(concept, contradiction_score=0.05):
    return {
        "concept": concept,
        "used_task_count": 8,
        "cross_task_support": 0.84,
        "records": [
            {
                "success": True,
                "contradiction_score": contradiction_score,
                "causal_alignment": 0.82,
            }
            for _ in range(8)
        ],
        "identity_strength": 0.75,
        "context_strength": 0.35,
    }


def process_evidence(concept):
    memory = ProcessDependencyMemory(seed_defaults=True)
    process_memory = memory.resolve_chain(concept)
    reasoning = MathematicalReasoningLayer().analyze_dependency_chain(
        concept,
        process_dependency_memory=process_memory,
    )
    surface = ContextSurfaceEngine().evaluate(
        concept,
        dependency_chain=reasoning["process_dependency_chain"],
        process_signature=reasoning["process_signature_report"],
        task_metadata=saturated_surface_evidence(),
        track_history=False,
    )
    coherence = DependencyCoherenceEngine().evaluate(
        concept,
        dependency_chain=process_memory,
        task_metadata=saturated_surface_evidence(),
        transformation_traces=[
            {"success": True, "prediction_accuracy": 1.0},
            {"success": True, "prediction_accuracy": 0.98},
        ],
        process_signature=reasoning["process_signature_report"],
        runtime_context={
            "process_dependency_memory": process_memory,
            "context_surface_report": surface,
            "prediction_accuracy": 1.0,
        },
    )
    return process_memory, reasoning, surface, coherence


def test_dependency_coherence_engine_scores_stable_contexts_above_point_nine():
    _, _, _, report = process_evidence("replication")

    assert report["concept"] == "replication"
    assert report["dependency_coherence"] > 0.90
    assert report["causal_reliability"] > 0.90
    assert report["contextual_variance"] < 0.10
    assert report["stable_dependencies"]
    assert report["fragile_dependencies"] == []
    assert report["hidden_contradictions"] == []


def test_dependency_coherence_engine_detects_hidden_contradictions():
    process_memory, reasoning, surface, _ = process_evidence("propagation")

    report = DependencyCoherenceEngine().evaluate(
        "propagation",
        dependency_chain=process_memory,
        task_metadata=saturated_surface_evidence(),
        contextual_truth_reports=[
            {
                "dependency": "directional_motion",
                "contradiction": True,
                "reason": "anti_directional_motion in matched context",
            }
        ],
        process_signature=reasoning["process_signature_report"],
        runtime_context={
            "process_dependency_memory": process_memory,
            "context_surface_report": surface,
        },
    )

    assert report["dependency_coherence"] < 0.90
    assert report["hidden_contradictions"]
    assert "directional_motion" in report["fragile_dependencies"]


def test_context_strength_depends_on_surface_and_dependency_coherence():
    process_memory, reasoning, surface, coherence = process_evidence("growth")
    process_report = ProcessContextGenerationEngine().generate(
        "growth",
        reasoning,
        context={
            "context_surface_report": surface,
            "dependency_coherence_report": coherence,
        },
    )

    strong = ContextStrengthEngine().consume_math_reasoning(
        0.35,
        math_reasoning_report=reasoning,
        process_context_report=process_report,
        dependency_semantics_report=reasoning["dependency_semantics_report"],
        runtime_context={
            "process_dependency_memory": process_memory,
            "context_surface_report": surface,
            "dependency_coherence_report": coherence,
        },
    )
    fragile = ContextStrengthEngine().consume_math_reasoning(
        0.35,
        math_reasoning_report=reasoning,
        process_context_report=process_report,
        dependency_semantics_report=reasoning["dependency_semantics_report"],
        runtime_context={
            "process_dependency_memory": process_memory,
            "context_surface_report": surface,
            "dependency_coherence_report": {
                "dependency_coherence": 0.42,
                "hidden_contradictions": [
                    {"dependency": "identity_persistence"},
                ],
                "stable_dependencies": [],
            },
        },
    )

    assert "context_surface" in strong["evidence_used"]
    assert "dependency_coherence" in strong["evidence_used"]
    assert strong["final_context_strength"] >= 0.69
    assert "dependency_coherence" not in fragile["evidence_used"]
    assert strong["final_context_strength"] > fragile["final_context_strength"]


def test_dependency_coherence_promotes_process_concepts_naturally():
    concepts = [
        "growth",
        "replication",
        "propagation",
        "topological_growth",
    ]
    evaluations = []
    coherence_values = []
    for concept in concepts:
        process_memory, reasoning, surface, coherence = process_evidence(concept)
        coherence_values.append(coherence["dependency_coherence"])
        evaluations.append({
            "concept": concept,
            "process_dependency_memory": process_memory,
            "math_reasoning_report": reasoning,
            "dependency_semantics_report": reasoning[
                "dependency_semantics_report"
            ],
            "context_surface_report": surface,
            "dependency_coherence_report": coherence,
            "causal_validation": {
                "promotion_dependency_score": 0.92,
                "dependency_promotion_evidence": process_memory,
            },
            "identity_safe_truth_integration": {
                "identity_continuity": 0.75,
            },
            "identity_runtime_ready": True,
        })

    lifecycle = ConceptMaturityTracker().evaluate(
        {
            "concepts": [
                mature_concept(concept)
                for concept in concepts
            ],
            "identity_runtime_ready": True,
        },
        {"evaluations": evaluations},
    )

    assert sum(coherence_values) / len(coherence_values) > 0.90
    assert lifecycle.get("identity_runtime_ready", True) is True
    for item in lifecycle["concepts"]:
        promotion = item["truth_candidate_promotion"]
        assert item["state"] != "BOUNDARY_REFINEMENT"
        assert promotion["readiness_gates"]["context_strength"] is True
        assert "promotion_gate_blocked:context_strength" not in (
            promotion["dependency_promotion_blockers"]
        )
