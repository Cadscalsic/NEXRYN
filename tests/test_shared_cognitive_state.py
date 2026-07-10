from runtime.state.shared_cognitive_state import (
    CognitiveKnowledgeBus,
    SharedCognitiveState,
)


def test_shared_cognitive_state_publishes_owned_stage_outputs(tmp_path):
    state = SharedCognitiveState.create(
        execution_profile={"execution_profile": "adaptive"},
        mode="adaptive",
    )

    state.publish(
        "concept_formation_runtime",
        {
            "generated_concepts": 2,
            "discovered_concepts": [
                {"id": "concept:a", "confidence": 0.8},
            ],
        },
        owner="concept_formation_runtime",
    )
    state.publish(
        "program_synthesis_runtime",
        {
            "generated_programs": 1,
            "generated_program_objects": [
                {
                    "id": "program:a",
                    "supporting_concepts": ["concept:a"],
                },
            ],
        },
        owner="program_synthesis_runtime",
    )
    state.snapshot("program_synthesis")

    report = state.build_report()

    assert report["SHARED_COGNITIVE_STATE_REPORT"] is True
    assert report["knowledge_availability"]["concept_count"] == 2
    assert report["knowledge_availability"]["program_count"] == 1
    assert state.ownership["concept:a"] == "concept_formation_runtime"
    assert state.ownership["program:a"] == "program_synthesis_runtime"
    assert report["missing_references"] == []


def test_deep_state_inherits_latest_adaptive_snapshot(tmp_path):
    path = tmp_path / "latest.json"
    adaptive = SharedCognitiveState.create(
        execution_profile={"execution_profile": "adaptive"},
        mode="adaptive",
    )
    adaptive.publish(
        "concept_formation_runtime",
        {"generated_concepts": 1},
        owner="concept_formation_runtime",
    )
    adaptive.publish(
        "truth_runtime",
        {"truth_candidates": [{"id": "truth:a"}]},
        owner="truth_runtime",
    )
    adaptive.snapshot("adaptive_complete")
    adaptive.save(path)

    deep = SharedCognitiveState.create(
        execution_profile={"execution_profile": "deep"},
        mode="deep",
        inherit_latest=True,
        path=path,
    )

    assert deep.inherited_from_snapshot is not None
    assert deep.counts()["concept_count"] == 1
    assert deep.counts()["truth_candidate_count"] == 1
    assert deep.execution_metadata["inherited_state"] is True


def test_truth_runtime_candidate_evaluations_publish_to_shared_state():
    state = SharedCognitiveState.create(mode="adaptive")

    state.publish(
        "truth_runtime",
        {
            "truth_candidate_evaluations": {
                "concept:a": {
                    "id": "truth:a",
                    "eligible_for_truth_candidate": True,
                },
            },
        },
        owner="truth_runtime",
    )

    assert state.counts()["truth_candidate_count"] == 1
    assert state.truth_candidates["truth:a"]["owner"] == "truth_runtime"


def test_deep_inheritance_report_explains_missing_snapshot(tmp_path):
    path = tmp_path / "missing.json"

    deep = SharedCognitiveState.create(
        execution_profile={"execution_profile": "deep"},
        mode="deep",
        inherit_latest=True,
        path=path,
    )
    report = deep.build_report()

    assert report["state_inheritance"]["inherit_requested"] is True
    assert report["state_inheritance"]["inherited_state"] is False
    assert report["state_inheritance"]["context_count_at_boot"] == 0
    assert (
        report["state_inheritance"]["context_zero_reason"]
        == "no_prior_shared_cognitive_state_snapshot"
    )
    assert any(
        warning["warning"] == "inherit_requested_without_snapshot"
        for warning in report["validation_warnings"]
    )


def test_context_validation_warns_without_rebuilding():
    state = SharedCognitiveState.create(mode="deep")

    report = state.validate_before(
        "program_synthesis_runtime",
        required=("concept_store",),
    )

    assert report["warnings"]
    assert state.counts()["concept_count"] == 0


def test_knowledge_bus_tracks_publish_consume_and_audit():
    state = SharedCognitiveState.create(mode="adaptive")
    bus = CognitiveKnowledgeBus(state)

    bus.publish(
        "concept_formation_runtime",
        {
            "discovered_concepts": [
                {
                    "id": "concept:a",
                    "confidence": 0.8,
                    "supporting_evidence": ["evidence:a"],
                },
            ],
            "context_objects": [{"id": "context:a", "kind": "semantic"}],
        },
        owner="concept_formation_runtime",
    )
    consumption = bus.consume(
        "program_synthesis_runtime",
        ("concept_store", "context_store", "evidence_store"),
        required=("concept_store", "context_store"),
    )
    report = bus.report()

    assert consumption["event"]["missing_required"] == []
    assert state.artifact_audit["concept:a"]["producer_runtime"] == (
        "concept_formation_runtime"
    )
    assert "program_synthesis_runtime" in state.artifact_audit["concept:a"]["consumers"]
    assert report["KNOWLEDGE_PROPAGATION_REPORT"] is True
    assert report["artifacts_published"]["by_store"]["concepts"] == 1
    assert report["artifacts_consumed"]["total"] >= 1


def test_truth_consume_requires_evidence_context_and_knowledge():
    state = SharedCognitiveState.create(mode="deep")
    bus = CognitiveKnowledgeBus(state)

    bus.consume(
        "truth_runtime",
        ("knowledge_objects", "evidence_store", "context_store"),
        required=("knowledge_objects", "evidence_store", "context_store"),
    )
    report = bus.report()

    assert report["propagation_failures"]
    assert any(
        warning["severity"] == "critical"
        for warning in report["propagation_failures"]
    )
