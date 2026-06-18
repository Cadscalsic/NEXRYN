from runtime.process import (
    ProcessSemanticContext,
    ProcessSemanticContextEngine,
    ProcessTransitionGraph,
)


PROCESS_CONCEPTS = [
    "growth",
    "propagation",
    "replication",
    "directional_motion",
    "topological_growth",
]


def test_process_semantic_context_model_exposes_state_transition_state():
    context = ProcessSemanticContext(
        concept="growth",
        preconditions=["object_identity_exists"],
        transition_steps=["object_area_increases"],
        postconditions=["identity_preserved"],
        invariants=["topology_preserved"],
        temporal_constraints=["temporal_reasoning_disabled"],
        context_strength=0.91,
    )

    report = context.as_dict()
    graph = ProcessTransitionGraph().build(context)

    assert report["concept"] == "growth"
    assert report["preconditions"] == ["object_identity_exists"]
    assert report["transition_steps"] == ["object_area_increases"]
    assert report["postconditions"] == ["identity_preserved"]
    assert report["invariants"] == ["topology_preserved"]
    assert report["process_context_strength"] == 0.91
    assert report["temporal_reasoning_enabled"] is False
    assert graph["model"] == "STATE_TRANSITION_STATE"
    assert graph["initial_state"]["node_type"] == "state"
    assert graph["transition_steps"] == ["object_area_increases"]
    assert graph["final_state"]["node_type"] == "state"


def test_alpha13_discovers_required_process_semantic_contexts():
    engine = ProcessSemanticContextEngine()
    report = engine.discover_all()

    assert report["process_context_count"] == 5
    assert report["process_context_coverage"] == 1.0
    assert report["process_context_registration_rate"] == 1.0
    assert report["average_process_context_strength"] > 0.8
    assert report["truth_candidate_blocked_by_context"] is False

    for concept in PROCESS_CONCEPTS:
        assert report[f"{concept}_context_discovered"] is True

    assert set(report["discovered_contexts"]) == {
        f"{concept}_context" for concept in PROCESS_CONCEPTS
    }


def test_alpha13_process_reports_clear_context_block_for_each_process():
    engine = ProcessSemanticContextEngine()

    for concept in PROCESS_CONCEPTS:
        report = engine.synthesize(concept)

        assert report["context_name"] == f"{concept}_context"
        assert report["process_semantic_context_synthesized"] is True
        assert report["process_context_generated"] is True
        assert report["process_context_strength"] > 0.8
        assert report["truth_candidate_blocked_by_context"] is False
        assert report["state_transition_graph"]["model"] == (
            "STATE_TRANSITION_STATE"
        )
        assert report["state_transition_graph"][
            "temporal_reasoning_enabled"
        ] is False
        assert report["preconditions"]
        assert report["transition_steps"]
        assert report["postconditions"]
        assert report["invariants"]
        assert "temporal_reasoning_disabled" in report[
            "temporal_constraints"
        ]
