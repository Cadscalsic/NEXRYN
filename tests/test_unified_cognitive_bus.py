from runtime.knowledge import (
    CognitiveKnowledgeIntegrationLayer,
    CognitiveKnowledgeMemory,
    UnifiedCognitiveBus,
)


def _concept_report():
    return {
        "discovered_concepts": [
            {
                "concept_id": "concept:a",
                "concept_name": "spatial symmetry",
                "confidence": 0.82,
                "utility": 0.77,
                "lifecycle": "VALIDATED",
                "supporting_evidence": [{"source": "pattern"}],
            }
        ]
    }


def _program_report():
    return {
        "generated_program_objects": [
            {
                "program_id": "program:a",
                "program_name": "symmetry solver",
                "required_concepts": ["concept:a"],
                "confidence": 0.78,
                "utility": 0.72,
                "lifecycle": "VALIDATED",
            }
        ]
    }


def _route_report():
    return {
        "cognitive_routes": {
            "route:a": {
                "route_id": "route:a",
                "supporting_concepts": ["concept:a"],
                "supporting_programs": ["program:a"],
                "current_confidence": 0.74,
                "proposed_state": "VALIDATED",
            }
        }
    }


def _evidence_report():
    return {
        "evidence_objects": [
            {
                "id": "evidence:a",
                "supporting_concepts": ["concept:a"],
                "supporting_programs": ["program:a"],
                "confidence": 0.86,
                "reliability": 0.8,
                "lifecycle": "PUBLISHED",
            }
        ]
    }


def test_bus_transports_only_canonical_cognitive_objects():
    bus = UnifiedCognitiveBus()
    obj = bus.publish(
        "concept_formation_runtime",
        _concept_report()["discovered_concepts"][0],
        execution_id="exec:bus",
    )

    expected_fields = {
        "object_id",
        "execution_id",
        "runtime_origin",
        "creation_timestamp",
        "object_type",
        "object_family",
        "semantic_payload",
        "structural_payload",
        "evidence_payload",
        "causal_payload",
        "confidence",
        "importance",
        "priority",
        "relationships",
        "dependencies",
        "status",
        "lifecycle",
        "history",
        "version",
    }

    assert expected_fields.issubset(obj)
    assert obj["object_type"] == "CONCEPT"
    assert obj["runtime_origin"] == "concept_formation_runtime"
    assert obj["semantic_payload"]["concept_name"] == "spatial symmetry"
    assert obj["version"] == 1


def test_bus_contract_routing_ack_update_retire_and_replay():
    bus = UnifiedCognitiveBus()
    bus.subscribe("process_semantic_context_engine", ["CONCEPT"])
    obj = bus.publish(
        "concept_formation_runtime",
        _concept_report()["discovered_concepts"][0],
        execution_id="exec:bus",
    )
    route = bus.route(obj["object_id"])
    ack = bus.acknowledge("process_semantic_context_engine", obj["object_id"])
    updated = bus.update(
        obj["object_id"],
        {"confidence": 0.9, "lifecycle": "SUPPORTED"},
        author_runtime="truth_runtime",
        reason="truth_supported_object",
        supporting_evidence=["evidence:a"],
    )
    retired = bus.retire(
        obj["object_id"],
        author_runtime="memory_runtime",
        reason="archived_to_memory",
    )
    replay = bus.replay("meta_cognition", ["CONCEPT"])

    assert "process_semantic_context_engine" in route["delivered"]
    assert ack["acknowledged"] is True
    assert updated["version"] == 2
    assert updated["history"][-1]["author_runtime"] == "truth_runtime"
    assert retired["status"] == "RETIRED"
    assert retired["version"] == 3
    assert replay["replay_count"] == 1
    assert replay["deterministic_ordering"] is True


def test_parent_execution_aggregates_child_runtime_outputs():
    bus = UnifiedCognitiveBus()
    publication = bus.publish_many_from_runtime_reports(
        {
            "concept_formation_runtime": _concept_report(),
            "program_synthesis_runtime": _program_report(),
            "search_runtime": _route_report(),
            "evidence_builder_runtime": _evidence_report(),
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
            "reasoning_runtime": {
                "reasoning_artifacts": [
                    {"object_id": "reasoning:a", "confidence": 0.75}
                ]
            },
        },
        execution_id="exec:episode",
    )
    snapshot = publication["snapshot"]
    summary = snapshot["execution_summary"]

    assert snapshot["COGNITIVE_SNAPSHOT"] is True
    assert summary["generated_concepts"] == 1
    assert summary["generated_programs"] == 1
    assert summary["generated_truth_candidates"] == 1
    assert summary["generated_memory_entries"] == 1
    assert summary["search_routes"] == 1
    assert summary["reasoning_artifacts"] == 1
    assert summary["evidence_objects"] == 1
    assert summary["total_cognitive_objects"] == 7


def test_bus_report_tracks_telemetry_delivery_and_synchronization():
    bus = UnifiedCognitiveBus()
    obj = bus.publish(
        "evidence_builder_runtime",
        _evidence_report()["evidence_objects"][0],
        execution_id="exec:bus",
    )
    bus.route(obj["object_id"])
    report = bus.report()

    assert report["UNIFIED_COGNITIVE_BUS_REPORT"] is True
    assert report["published_objects"] == 1
    assert report["delivered_objects"] >= 1
    assert report["duplicate_deliveries"] == 0
    assert report["dropped_objects"] == 0
    assert report["canonical_coverage"] == 1.0
    assert report["synchronization_quality"]["deterministic_ordering"] is True
    assert report["synchronization_quality"]["idempotent_updates"] is True
    assert report["runtime_alignment"]["creates_new_runtime"] is False
    assert report["runtime_alignment"]["canonical_exchange_layer_inside_ckil"]


def test_ckil_exposes_unified_cognitive_bus_report(tmp_path):
    engine = CognitiveKnowledgeIntegrationLayer(
        memory=CognitiveKnowledgeMemory(tmp_path / "ckil_memory.json")
    )
    report = engine.build_unified_cognitive_bus_report(
        execution_id="exec:ckil",
        concept_formation_report=_concept_report(),
        program_synthesis_report=_program_report(),
        cognitive_route_intelligence_report=_route_report(),
        evidence_architecture_report=_evidence_report(),
        truth_report={"truth_candidates": [{"truth_id": "truth:a", "confidence": 0.9}]},
        memory_report={"memory_entries": [{"memory_id": "memory:a", "confidence": 0.8}]},
    )

    assert report["UNIFIED_COGNITIVE_BUS_REPORT"] is True
    assert report["parent_execution_aggregation"]["generated_concepts"] == 1
    assert report["parent_execution_aggregation"]["generated_programs"] == 1
    assert report["canonical_exchange_contract"]["publish"] is True
    assert report["future_subsystem_integration"][
        "process_semantic_context_consumes_cognitive_objects"
    ] is True
    assert report["future_subsystem_integration"][
        "world_model_stores_cognitive_objects"
    ] is True
