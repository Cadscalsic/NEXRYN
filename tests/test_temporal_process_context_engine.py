from core.concept_lifecycle.concept_maturity import ConceptMaturityTracker
from core.context.context_strength_engine import ContextStrengthEngine
from core.dependency.process_dependency_memory import ProcessDependencyMemory
from core.truth.truth_candidate_engine import TruthCandidatePromotionEngine
from runtime.context.temporal_process_context_engine import (
    TemporalProcessContextEngine,
)


PROCESS_CONCEPTS = [
    "growth",
    "propagation",
    "replication",
    "directional_motion",
    "topological_growth",
]


def mature_ledger(concept, context_strength=0.50):
    return {
        "concept": concept,
        "used_task_count": 8,
        "cross_task_support": 0.84,
        "records": [
            {
                "success": True,
                "contradiction_score": 0.05,
                "causal_alignment": 0.82,
            }
            for _ in range(8)
        ],
        "context_strength": context_strength,
        "identity_strength": 0.75,
    }


def runtime_evaluation(concept):
    process_memory = ProcessDependencyMemory(
        seed_defaults=True,
    ).resolve_chain(concept)
    return {
        "concept": concept,
        "process_dependency_memory": process_memory,
        "causal_validation": {
            "promotion_dependency_score": 0.92,
            "dependency_promotion_evidence": process_memory,
        },
        "identity_safe_truth_integration": {
            "integration_safe": True,
            "identity_continuity": 0.82,
        },
    }


def test_temporal_process_context_engine_models_state_transition_state():
    process_memory = ProcessDependencyMemory(
        seed_defaults=True,
    ).resolve_chain("growth")

    report = TemporalProcessContextEngine().evaluate(
        "growth",
        dependency_chain=process_memory,
        transformational_identity={
            "integration_safe": True,
            "identity_continuity": 0.84,
        },
    )

    assert report["concept"] == "growth"
    assert report["initial_state"]
    assert report["transitions"]
    assert report["final_state"]
    assert report["temporal_consistency"] > 0.90
    assert report["process_context_strength"] > 0.90
    assert report["process_context_ready"] is True


def test_context_strength_consumes_temporal_state_sequence():
    process_memory = ProcessDependencyMemory(
        seed_defaults=True,
    ).resolve_chain("directional_motion")
    process_report = TemporalProcessContextEngine().evaluate(
        "directional_motion",
        dependency_chain=process_memory,
        transformational_identity={
            "integration_safe": True,
            "identity_continuity": 0.82,
        },
    )
    dependency_report = (
        TemporalProcessContextEngine().dependency_semantics_report(
            process_report,
        )
    )

    strength = ContextStrengthEngine().consume_math_reasoning(
        0.50,
        math_reasoning_report={
            "math_reasoning_signature": {
                "typed_dependencies_generated": True,
            },
        },
        process_context_report=process_report,
        dependency_semantics_report=dependency_report,
        runtime_context={},
    )

    assert strength["final_context_strength"] > 0.90
    assert "temporal_state_sequence" in strength["evidence_used"]
    assert "temporal_final_state" in strength["evidence_used"]


def test_temporal_context_unblocks_growth_promotion_gate():
    promotion = TruthCandidatePromotionEngine().evaluate(
        mature_ledger("growth", context_strength=0.50),
        {"evaluations": [runtime_evaluation("growth")]},
    )

    assert promotion["temporal_process_context_report"][
        "temporal_consistency"
    ] > 0.90
    assert promotion["context_strength"] > 0.90
    assert promotion["failed_gates"] == []
    assert promotion["dependency_promotion_blockers"] == []
    assert promotion["candidate_ready"] is True


def test_temporal_context_makes_all_process_concepts_candidate_ready():
    report = ConceptMaturityTracker().evaluate(
        {
            "concepts": [
                mature_ledger(concept, context_strength=0.50)
                for concept in PROCESS_CONCEPTS
            ],
        },
        {
            "evaluations": [
                runtime_evaluation(concept)
                for concept in PROCESS_CONCEPTS
            ],
        },
    )

    for concept in report["concepts"]:
        promotion = concept["truth_candidate_promotion"]
        assert concept["state"] == "TRUTH_CANDIDATE"
        assert promotion["context_strength"] > 0.90
        assert promotion["failed_gates"] == []
        assert promotion["dependency_promotion_blockers"] == []
