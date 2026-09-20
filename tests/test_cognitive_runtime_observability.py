from runtime.observability import OBSERVABILITY_CONTRACT
from runtime.state.shared_cognitive_state import CognitiveKnowledgeBus, SharedCognitiveState


def _build_observable_state():
    state = SharedCognitiveState.create(mode="adaptive")
    bus = CognitiveKnowledgeBus(state)

    bus.publish(
        "concept_formation_runtime",
        {"discovered_concepts": [{"id": "concept:a", "confidence": 0.82}]},
        owner="concept_formation_runtime",
    )
    bus.consume("program_synthesis_runtime", ("concept_store",), required=("concept_store",))
    bus.publish(
        "program_synthesis_runtime",
        {
            "generated_program_objects": [
                {
                    "id": "program:a",
                    "supporting_concepts": ["concept:a"],
                    "confidence": 0.78,
                }
            ]
        },
        owner="program_synthesis_runtime",
    )
    bus.consume("adaptive_search_intelligence_runtime", ("program_store",), required=("program_store",))
    bus.publish(
        "adaptive_search_intelligence_runtime",
        {
            "search_routes": [
                {
                    "id": "route:a",
                    "supporting_programs": ["program:a"],
                    "confidence": 0.8,
                }
            ]
        },
        owner="adaptive_search_intelligence_runtime",
    )
    bus.consume(
        "evidence_builder_runtime",
        ("concept_store", "program_store", "search_routes"),
        required=("concept_store", "program_store", "search_routes"),
    )
    bus.publish(
        "evidence_builder_runtime",
        {
            "evidence_objects": [
                {
                    "id": "evidence:a",
                    "supporting_concepts": ["concept:a"],
                    "supporting_programs": ["program:a"],
                    "supporting_routes": ["route:a"],
                    "confidence": 0.84,
                }
            ]
        },
        owner="evidence_builder_runtime",
    )
    bus.consume("knowledge_integration_runtime", ("evidence_store",), required=("evidence_store",))
    bus.publish(
        "knowledge_integration_runtime",
        {
            "knowledge_objects": [
                {
                    "id": "knowledge:a",
                    "evidence_references": ["evidence:a"],
                    "confidence": 0.86,
                }
            ],
            "knowledge_graph": {"nodes": ["knowledge:a"], "edges": []},
        },
        owner="knowledge_integration_runtime",
    )
    bus.consume(
        "truth_runtime",
        ("evidence_store", "knowledge_objects", "context_store"),
        required=("evidence_store", "knowledge_objects"),
    )
    bus.publish(
        "truth_runtime",
        {
            "truth_candidates": [
                {
                    "id": "truth:a",
                    "supporting_evidence": ["evidence:a"],
                    "evidence_references": ["evidence:a"],
                    "lineage": ["knowledge:a"],
                    "confidence": 0.92,
                    "reliability": 0.9,
                    "validated": True,
                }
            ],
            "validated_truths": [
                {
                    "id": "validated_truth:a",
                    "supporting_evidence": ["evidence:a"],
                    "confidence": 0.91,
                }
            ],
        },
        owner="truth_runtime",
    )
    bus.consume(
        "memory_runtime",
        ("truth_candidates", "validated_truths", "knowledge_objects", "evidence_store"),
        required=("truth_candidates", "knowledge_objects", "evidence_store"),
    )
    bus.publish(
        "memory_runtime",
        {
            "memory_entries": [
                {
                    "id": "memory:a",
                    "truth_references": ["truth:a"],
                    "confidence": 0.88,
                }
            ]
        },
        owner="memory_runtime",
    )
    bus.consume("evaluation_runtime", ("memory_entries", "validated_truths"), required=("memory_entries",))
    bus.publish(
        "evaluation_runtime",
        {
            "contexts": [
                {
                    "id": "context:evaluation:a",
                    "context_type": "evaluation",
                    "confidence": 0.8,
                }
            ],
            "metrics": {"accuracy": 1.0},
        },
        owner="evaluation_runtime",
    )
    state.run_artifact_governance()
    return state


def test_cognitive_runtime_observability_report_exposes_level_5_runtime_contract():
    state = _build_observable_state()

    report = state.build_cognitive_observability_report()

    assert report["COGNITIVE_OBSERVABILITY_REPORT"] is True
    assert report["observability_contract"] == list(OBSERVABILITY_CONTRACT)
    assert report["coverage"]["every_runtime_level_5"] is True
    assert report["coverage"]["level_5_coverage"] == 1.0
    for runtime_id, runtime_report in report["runtime_reports"].items():
        assert runtime_report["observability_level"] == 5, runtime_id
        assert runtime_report["snapshot_count"] >= 1
        assert runtime_report["health_score"] >= 0.9
        snapshot = runtime_report["snapshots"][-1]
        assert snapshot["purpose"]
        assert snapshot["owner_runtime"] == runtime_id
        assert snapshot["timestamp"]
        assert snapshot["execution_id"]
        assert "artifact_references" in snapshot
        assert "processing_duration_seconds" in snapshot
        assert "failures" in snapshot
        assert "warnings" in snapshot
        assert "summary" in snapshot


def test_cognitive_runtime_observability_tracks_artifact_flow_gaps_world_and_dna():
    state = _build_observable_state()

    report = state.build_cognitive_observability_report()
    flow = report["artifact_flow_observability"]
    gaps = report["observability_gap_detection"]

    assert flow["truth_runtime"]["consumed_artifacts"]
    assert flow["truth_runtime"]["published_artifacts"]
    assert flow["memory_runtime"]["consumed_artifacts"]
    assert flow["evaluation_runtime"]["produced_artifacts"]
    assert report["cognitive_timeline"][0]["runtime_id"] == "concept_formation_runtime"
    assert gaps["missing_snapshots"] == []
    assert gaps["missing_telemetry"] == []
    assert state.world_model["fully_observable_cognition"]["runtime_count"] >= 8
    assert state.world_model["opaque_cognition_excluded"] is True
    assert state.dna_state["observable_behavior_statistics"][
        "learns_only_from_explainable_behavior"
    ] is True
