from core.truth.truth_candidate_engine import TruthCandidatePromotionEngine
from runtime.causal.causal_alignment_engine import RuntimeCausalAlignmentEngine
from runtime.context.context_governance_registry import ContextGovernanceRegistry
from runtime.process import (
    ProcessContextRegistry,
    ProcessSemanticEngine,
    TypedProcessDependencyMemory,
)


PROCESS_CONCEPTS = {
    "growth",
    "propagation",
    "replication",
    "directional_motion",
    "topological_growth",
    "object_counting",
    "cardinality",
    "quantity_preservation",
    "quantity_transformation",
    "numerical_reasoning",
    "set_reasoning",
}


def mature_ledger(concept):
    return {
        "concept": concept,
        "used_task_count": 5,
        "successful_task_count": 5,
        "counterexample_task_count": 0,
        "cross_task_support": 0.95,
        "average_contradiction_score": 0.02,
        "context_strength": 0.50,
        "identity_strength": 0.95,
    }


def test_process_semantic_engine_builds_required_state_transition_models():
    report = ProcessSemanticEngine().synthesize_all()
    models = report["process_semantic_models"]

    assert set(models) == PROCESS_CONCEPTS
    assert report["average_process_context_strength"] > 0.8
    assert report["truth_candidate_blocked_by_context"] is False

    growth = models["growth"]
    assert growth["preconditions"] == ["object_identity_exists"]
    assert growth["transition_steps"] == ["area_increases"]
    assert growth["postconditions"] == ["identity_preserved"]
    assert growth["invariants"] == [
        "identity_preserved",
        "topology_preserved",
    ]
    assert growth["process_context_strength"] > 0.8
    assert growth["state_graph"]["model"] == "STATE_TRANSITION_STATE"
    assert growth["PROCESS SEMANTIC REPORT"] == {
        "preconditions": ["object_identity_exists"],
        "transition_steps": ["area_increases"],
        "postconditions": ["identity_preserved"],
        "invariants": ["identity_preserved", "topology_preserved"],
        "process_context_strength": growth["process_context_strength"],
    }


def test_process_semantic_models_feed_context_governance_and_causal_alignment():
    semantic_report = ProcessSemanticEngine().synthesize_all()
    models = semantic_report["process_semantic_models"]

    governance = ContextGovernanceRegistry().register_runtime_contexts({
        "process_semantic_models": models,
    })

    assert "growth_context" in governance["visible_context_ids"]

    causal = RuntimeCausalAlignmentEngine().build_explicit_causal_alignment(
        "growth",
        context={
            "process_semantic_models": models,
            "dependency_coherence_report": {
                "dependency_coherence": 0.86,
            },
            "causal_validation": {
                "validation_score": 0.90,
            },
        },
    )

    assert "area_increases" not in causal["causal_gaps"]
    assert causal["causal_alignment"] > 0.0


def test_truth_governance_consumes_process_semantic_models():
    models = ProcessSemanticEngine().synthesize_all()["process_semantic_models"]

    promotion = TruthCandidatePromotionEngine().evaluate(
        mature_ledger("growth"),
        {
            "evaluations": [{
                "concept": "growth",
                "process_semantic_models": models,
                "causal_validation": {
                    "dependency_promotion_evidence": {
                        "dependency_chain_depth": 4,
                        "dependency_chain_coverage": 0.9,
                        "dependency_confidence": 0.9,
                        "missing_dependencies": [],
                    },
                    "promotion_dependency_score": 0.92,
                },
            }]
        },
    )

    assert promotion["context_strength"] > 0.8
    assert promotion["readiness_gates"]["context_strength"] is True


def test_dependency_completeness_audit_generates_missing_definitions():
    audit = ProcessSemanticEngine().dependency_completeness_audit()
    incomplete = set(audit["incomplete_concepts"])

    assert {
        "size_preservation",
        "symbolic_remapping",
        "density_preservation",
    }.issubset(incomplete)

    for item in audit["audit"]:
        assert item["chain_depth"] == 0
        assert item["coherence"] > 0
        assert item["generated_dependency_definitions"]

    memory = TypedProcessDependencyMemory(seed_defaults=True)
    for concept in [
        "size_preservation",
        "symbolic_remapping",
        "density_preservation",
    ]:
        resolution = memory.resolve(concept)
        assert resolution["dependency_chain_depth"] > 0
        assert resolution["process_dependency_links_used"] > 0


def test_process_context_registry_registers_semantic_models():
    model = ProcessSemanticEngine().synthesize("replication")
    registered = ProcessContextRegistry().register_semantic_model(model)

    assert registered["context_name"] == "replication_context"
    assert registered["process_semantic_model"] is True
    assert registered["transition_steps"] == ["object_instance_copied"]
