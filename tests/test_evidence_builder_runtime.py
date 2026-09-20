from runtime.evidence import EvidenceBuilderRuntime
from runtime.state.shared_cognitive_state import CognitiveKnowledgeBus, SharedCognitiveState


def test_evidence_builder_normalizes_correlates_and_reports():
    report = EvidenceBuilderRuntime().build_report(
        concept_formation_report={
            "discovered_concepts": [
                {"concept_id": "concept:replication", "confidence": 0.8}
            ]
        },
        program_synthesis_report={
            "generated_program_objects": [
                {
                    "program_id": "program:duplicate",
                    "required_concepts": ["concept:replication"],
                    "confidence": 0.75,
                }
            ]
        },
        cognitive_route_intelligence_report={
            "cognitive_routes": {
                "route:match": {
                    "route_id": "route:match",
                    "supporting_concepts": ["concept:replication"],
                    "supporting_programs": ["program:duplicate"],
                    "current_confidence": 0.7,
                }
            }
        },
        dependency_report={
            "dependency_edges": [
                {"source": "concept:replication", "target": "object_identity", "confidence": 0.9}
            ]
        },
    )

    assert report["EVIDENCE_ARCHITECTURE_REPORT"] is True
    assert report["runtime_alignment"]["performs_inference"] is False
    assert report["raw_observation_count"] >= 4
    assert report["normalized_observation_count"] >= 4
    assert report["evidence_objects"]
    assert report["evidence_confidence"]["average_confidence"] > 0.0
    assert report["evidence_lineage"]


def test_shared_state_accepts_canonical_evidence_not_raw_artifact_evidence():
    state = SharedCognitiveState.create(mode="adaptive")
    bus = CognitiveKnowledgeBus(state)

    bus.publish(
        "concept_formation_runtime",
        {
            "discovered_concepts": [
                {"id": "concept:a", "confidence": 0.8}
            ]
        },
        owner="concept_formation_runtime",
    )
    assert state.counts()["concept_count"] == 1
    assert state.counts()["evidence_count"] == 0

    report = EvidenceBuilderRuntime().build_report(
        shared_state=state.to_dict(),
    )
    bus.publish(
        "evidence_builder_runtime",
        report,
        owner="evidence_builder_runtime",
    )

    truth_inputs = bus.consume(
        "truth_runtime",
        ("knowledge_objects", "evidence_store", "context_store"),
        required=("evidence_store",),
    )

    assert state.counts()["evidence_count"] > 0
    assert truth_inputs["event"]["missing_required"] == []
    assert state.build_report()["cross_runtime_references"]["search_available_to_truth"] is False
