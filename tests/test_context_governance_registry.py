from core.context.context_strength_engine import ContextStrengthEngine
from core.dependency.process_dependency_memory import ProcessDependencyMemory
from core.truth.truth_candidate_engine import TruthCandidatePromotionEngine
from runtime.context.context_governance_registry import (
    ContextGovernanceRegistry,
)
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


def temporal_context(concept):
    process_memory = ProcessDependencyMemory(
        seed_defaults=True,
    ).resolve_chain(concept)
    return TemporalProcessContextEngine().evaluate(
        concept,
        dependency_chain=process_memory,
        transformational_identity={
            "integration_safe": True,
            "identity_continuity": 0.84,
        },
    )


def test_governance_registry_registers_all_valid_process_contexts():
    contexts = [temporal_context(concept) for concept in PROCESS_CONCEPTS]

    report = ContextGovernanceRegistry().register_runtime_contexts(
        contexts=contexts,
    )

    assert report["runtime_context_count"] == 5
    assert report["governance_context_count"] >= report["runtime_context_count"]
    assert report["context_registration_gap"] == 0
    assert report["registration_coverage"] == 1.0
    assert report["hidden_contexts"] == []
    assert report["unregistered_contexts"] == []
    assert set(report["visible_context_ids"]) == {
        "growth_context",
        "propagation_context",
        "replication_context",
        "directional_motion_context",
        "topological_growth_context",
    }
    for context in report["visible_contexts"]:
        assert context["semantic_validation"] is True
        assert context["identity_compatible"] is True
        assert context["governance_visible"] is True
        assert context["context_type"] == "PROCESS_CONTEXT"


def test_governance_registry_hides_invalid_contexts():
    report = ContextGovernanceRegistry().register_runtime_contexts(
        contexts=[
            {
                "context_name": "invalid_growth_context",
                "concept": "growth",
                "semantic_validation": False,
                "identity_compatible": True,
                "context_confidence": 0.96,
            },
            {
                "context_name": "identity_leaking_context",
                "concept": "replication",
                "semantic_validation": True,
                "identity_compatible": False,
                "context_confidence": 0.96,
            },
        ],
    )

    assert report["runtime_context_count"] == 0
    assert report["governance_context_count"] == 0
    assert report["hidden_contexts"] == []
    assert report["visible_contexts"] == []


def test_context_strength_consumes_governance_visible_process_context():
    governance_report = ContextGovernanceRegistry().register_runtime_contexts(
        contexts=[temporal_context("replication")],
    )

    strength = ContextStrengthEngine().consume_math_reasoning(
        0.50,
        math_reasoning_report={
            "math_reasoning_signature": {
                "typed_dependencies_generated": True,
                "transformations_detected": True,
            },
        },
        process_context_report={},
        dependency_semantics_report={},
        runtime_context={
            "concept": "replication",
            "context_governance_report": governance_report,
        },
    )

    assert strength["final_context_strength"] > 0.90
    assert strength["rejection_reasons"] == []
    assert "process_transition_sequence" in strength["evidence_used"]
    assert "temporal_state_sequence" in strength["evidence_used"]


def test_truth_candidate_promotion_exposes_context_governance_report():
    promotion = TruthCandidatePromotionEngine().evaluate(
        mature_ledger("growth", context_strength=0.50),
        {"evaluations": [runtime_evaluation("growth")]},
    )

    governance_report = promotion["context_governance_report"]
    assert governance_report["context_registration_gap"] == 0
    assert "growth_context" in governance_report["visible_context_ids"]
    assert promotion["readiness_gates"]["context_strength"] is True
    assert "promotion_gate_blocked:context_strength" not in (
        promotion["dependency_promotion_blockers"]
    )
    assert promotion["candidate_ready"] is True
