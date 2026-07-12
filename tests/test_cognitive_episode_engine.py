from runtime.knowledge import CognitiveKnowledgeIntegrationLayer, UnifiedCognitiveBus


def _runtime_reports():
    return {
        "reasoning_runtime": {
            "reasoning_artifacts": [
                {"object_id": "reasoning:a", "confidence": 0.75}
            ]
        },
        "search_runtime": {
            "cognitive_routes": {
                "route:a": {
                    "route_id": "route:a",
                    "supporting_concepts": ["concept:a"],
                    "current_confidence": 0.74,
                }
            }
        },
        "concept_formation_runtime": {
            "discovered_concepts": [
                {
                    "concept_id": "concept:a",
                    "concept_name": "spatial symmetry",
                    "confidence": 0.82,
                    "supporting_evidence": [{"id": "evidence:a"}],
                }
            ]
        },
        "program_synthesis_runtime": {
            "generated_program_objects": [
                {
                    "program_id": "program:a",
                    "program_name": "symmetry solver",
                    "required_concepts": ["concept:a"],
                    "confidence": 0.78,
                }
            ]
        },
        "evidence_builder_runtime": {
            "evidence_objects": [
                {
                    "id": "evidence:a",
                    "supporting_concepts": ["concept:a"],
                    "confidence": 0.86,
                    "reliability": 0.8,
                }
            ]
        },
        "truth_runtime": {
            "truth_candidates": [
                {"truth_id": "truth:a", "confidence": 0.91}
            ]
        },
        "memory_runtime": {
            "memory_entries": [
                {"memory_id": "memory:a", "confidence": 0.84}
            ]
        },
    }


def test_every_execution_cycle_creates_one_primary_episode():
    bus = UnifiedCognitiveBus()
    publication = bus.publish_many_from_runtime_reports(
        _runtime_reports(),
        execution_id="exec:episode-engine",
    )

    episode = publication["episode"]
    snapshot = publication["snapshot"]

    assert episode["episode_id"] == snapshot["primary_episode"]["episode_id"]
    assert episode["episode_uuid"]
    assert episode["execution_id"] == "exec:episode-engine"
    assert episode["episode_type"] == "PRIMARY_REASONING_EPISODE"
    assert episode["episode_outcome"] == "SUCCESS"
    assert episode["statistics"]["object_count"] == 7
    assert episode["statistics"]["concept_count"] == 1
    assert episode["statistics"]["program_count"] == 1
    assert episode["statistics"]["truth_count"] == 1
    assert episode["statistics"]["reasoning_count"] == 1
    assert episode["statistics"]["search_count"] == 1
    assert snapshot["execution_summary"]["episode_id"] == episode["episode_id"]
    assert snapshot["execution_summary"]["parent_execution_summarizes_episode"] is True


def test_episode_tracks_membership_stages_timeline_graph_and_replay():
    bus = UnifiedCognitiveBus()
    publication = bus.publish_many_from_runtime_reports(
        _runtime_reports(),
        execution_id="exec:episode-replay",
    )
    episode = publication["snapshot"]["primary_episode"]
    objects = publication["snapshot"]["all_cognitive_objects"]
    replay = bus.replay_episode(episode["episode_id"])

    assert all(episode["episode_id"] in obj["episode_ids"] for obj in objects)
    assert episode["stages"]["Reasoning"]["observed"] is True
    assert episode["stages"]["Search"]["observed"] is True
    assert episode["stages"]["Concept Formation"]["observed"] is True
    assert episode["stages"]["Truth Validation"]["observed"] is True
    assert episode["timeline"]
    assert episode["episode_graph"]["node_count"] == 7
    assert episode["episode_graph"]["edge_count"] >= 1
    assert episode["lineage"]["concept"]
    assert episode["lineage"]["truth"]
    assert replay["replay_available"] is True
    assert replay["deterministic_ordering"] is True
    assert replay["object_ids"] == episode["object_ids"]


def test_cognitive_episode_report_and_ckil_integration():
    engine = CognitiveKnowledgeIntegrationLayer()
    report = engine.build_unified_cognitive_bus_report(
        execution_id="exec:ckil-episode",
        runtime_reports=_runtime_reports(),
    )

    episode_report = report["cognitive_episode_report"]
    primary = report["primary_cognitive_episode"]

    assert episode_report["COGNITIVE_EPISODE_REPORT"] is True
    assert episode_report["episodes_created"] == 1
    assert episode_report["episode_outcomes"]["SUCCESS"] == 1
    assert episode_report["concept_statistics"]["total"] == 1
    assert episode_report["program_statistics"]["total"] == 1
    assert episode_report["truth_statistics"]["total"] == 1
    assert episode_report["replay_availability"]["available"] is True
    assert episode_report["integration_health"]["duplicates_object_registry"] is False
    assert report["parent_execution_aggregation"]["episode_id"] == primary["episode_id"]
    assert report["future_subsystem_integration"]["process_semantic_context_consumes_episodes"] is True
    assert report["future_subsystem_integration"]["experience_engine_transforms_successful_episodes"] is True
