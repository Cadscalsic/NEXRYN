from core.concept_lifecycle.concept_maturity import ConceptMaturityTracker
from core.context.context_strength_engine import ContextStrengthEngine
from core.context.process_context_generation import ProcessContextGenerationEngine
from core.dependency.dependency_graph_engine import DependencyGraphEngine
from core.dependency.process_dependency_memory import ProcessDependencyMemory
from core.math_reasoning import MathematicalReasoningLayer
from runtime.context.context_surface_engine import ContextSurfaceEngine


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


def test_context_surface_engine_identifies_missing_replication_contexts():
    report = ContextSurfaceEngine().evaluate(
        "replication",
        task_metadata={
            "directions": ["right"],
            "object_types": ["single_cell"],
            "colors": [1],
            "topologies": ["split"],
            "sizes": [1],
            "spatial_patterns": ["offset"],
        },
        track_history=False,
    )

    assert report["concept"] == "replication"
    assert report["promotion_readiness"] is False
    assert "cross_axis_replication" in report["missing_contexts"]
    assert "multi_color_replication" in report["missing_contexts"]
    assert report["repetition_rewarded"] is False


def test_context_surface_engine_saturates_unique_process_contexts():
    memory = ProcessDependencyMemory(seed_defaults=True)
    reasoning = MathematicalReasoningLayer().analyze_dependency_chain(
        "replication",
        process_dependency_memory=memory.resolve_chain("replication"),
    )

    report = ContextSurfaceEngine().evaluate(
        "replication",
        dependency_chain=reasoning["process_dependency_chain"],
        process_signature=reasoning["process_signature_report"],
        task_metadata=saturated_surface_evidence(),
        track_history=False,
    )

    assert report["context_surface_score"] >= 0.74
    assert report["context_strength_estimate"] >= 0.74
    assert report["context_saturation"] >= 0.90
    assert report["missing_contexts"] == []
    assert report["promotion_readiness"] is True


def test_context_strength_consumes_context_surface_additively():
    memory = ProcessDependencyMemory(seed_defaults=True)
    reasoning = MathematicalReasoningLayer().analyze_dependency_chain(
        "growth",
        process_dependency_memory=memory.resolve_chain("growth"),
    )
    surface = ContextSurfaceEngine().evaluate(
        "growth",
        dependency_chain=reasoning["process_dependency_chain"],
        process_signature=reasoning["process_signature_report"],
        task_metadata=saturated_surface_evidence(),
        track_history=False,
    )
    process_report = ProcessContextGenerationEngine().generate(
        "growth",
        reasoning,
        context={"context_surface_report": surface},
    )
    strength = ContextStrengthEngine().consume_math_reasoning(
        0.35,
        math_reasoning_report=reasoning,
        process_context_report=process_report,
        dependency_semantics_report=reasoning["dependency_semantics_report"],
        runtime_context={"context_surface_report": surface},
    )

    assert "context_surface" in strength["evidence_used"]
    assert strength["process_context_strength"] > 0.30
    assert strength["final_context_strength"] >= 0.69


def test_context_surface_saturation_promotes_process_concepts_naturally(tmp_path):
    concepts = [
        "growth",
        "propagation",
        "replication",
        "topological_growth",
        "directional_motion",
    ]
    memory = ProcessDependencyMemory(seed_defaults=True)
    evaluations = []
    for concept in concepts:
        process_memory = memory.resolve_chain(concept)
        reasoning = MathematicalReasoningLayer().analyze_dependency_chain(
            concept,
            process_dependency_memory=process_memory,
        )
        evaluations.append({
            "concept": concept,
            "process_dependency_memory": process_memory,
            "math_reasoning_report": reasoning,
            "dependency_semantics_report": reasoning[
                "dependency_semantics_report"
            ],
            "context_surface_evidence": saturated_surface_evidence(),
            "causal_validation": {
                "promotion_dependency_score": 0.92,
                "dependency_promotion_evidence": process_memory,
            },
            "identity_safe_truth_integration": {
                "identity_continuity": 0.75,
            },
        })

    lifecycle = ConceptMaturityTracker().evaluate(
        {
            "concepts": [
                mature_concept(
                    concept,
                    contradiction_score=(
                        0.12 if concept == "directional_motion" else 0.05
                    ),
                )
                for concept in concepts
            ],
        },
        {"evaluations": evaluations},
    )
    coherence = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
        dependency_chain_ledger_path=tmp_path / "dependency_chain_ledger.json",
        process_dependency_memory_path=tmp_path / "process_dependency_memory.json",
    ).ingest_process_dependency_memory(concepts)

    assert coherence["dependency_coherence_average"] > 0.90
    for item in lifecycle["concepts"]:
        promotion = item["truth_candidate_promotion"]
        assert item["state"] != "BOUNDARY_REFINEMENT"
        assert promotion["readiness_gates"]["context_strength"] is True
        assert promotion["context_surface_promotion_readiness"] is True
        assert "promotion_gate_blocked:context_strength" not in (
            promotion["dependency_promotion_blockers"]
        )
        if item["concept"] == "directional_motion":
            assert promotion["readiness_gates"]["contradiction_governance"] is True
