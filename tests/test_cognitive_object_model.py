from runtime.knowledge import CognitiveKnowledgeIntegrationLayer, UnifiedCognitiveBus


def test_cognitive_object_identity_payload_lineage_and_versioning():
    bus = UnifiedCognitiveBus()
    obj = bus.publish(
        "concept_formation_runtime",
        {
            "concept_id": "concept:identity",
            "concept_name": "object permanence",
            "confidence": 0.81,
            "stability": 0.7,
            "complexity": 0.2,
            "generalization_score": 0.6,
            "supporting_evidence": [{"id": "evidence:1"}],
            "supporting_concepts": ["concept:base"],
            "required_concepts": ["concept:precondition"],
        },
        execution_id="exec:object-model",
    )

    assert obj["object_uuid"]
    assert obj["object_status"] == "CREATED"
    assert obj["object_confidence"] == 0.81
    assert obj["object_version"] == 1
    assert obj["canonical_payload"]["semantic_payload"]["concept_name"] == "object permanence"
    assert obj["canonical_payload"]["evidence_payload"]["supporting_evidence"]
    assert obj["canonical_payload"]["metadata_payload"]["source_id"] == "concept:identity"
    assert obj["required_objects"] == ["concept:precondition"]
    assert obj["supporting_objects"] == ["concept:base"]
    assert obj["lineage"]["created_by"] == ["concept_formation_runtime"]
    assert obj["lineage"]["supported_by"] == ["evidence:1"]

    updated = bus.update(
        obj["object_id"],
        {"confidence": 0.9, "lifecycle": "SUPPORTED"},
        author_runtime="truth_runtime",
        reason="truth_supported_object",
        supporting_evidence=["evidence:1"],
    )

    assert updated["object_id"] == obj["object_id"]
    assert updated["object_uuid"] == obj["object_uuid"]
    assert updated["object_version"] == 2
    assert updated["object_status"] == "SUPPORTED"
    assert updated["history"][-1]["previous_version"] == 1
    assert updated["history"][-1]["change_reason"] == "truth_supported_object"
    assert "truth_runtime" in updated["lineage"]["supported_by"]
    assert "truth_runtime" in updated["lineage"]["validated_by"]


def test_cognitive_object_graph_snapshot_and_report():
    bus = UnifiedCognitiveBus()
    concept = bus.publish(
        "concept_formation_runtime",
        {"concept_id": "concept:a", "concept_name": "symmetry", "confidence": 0.8},
        execution_id="exec:graph",
    )
    program = bus.publish(
        "program_synthesis_runtime",
        {
            "program_id": "program:a",
            "program_name": "symmetry solver",
            "required_concepts": [concept["object_id"]],
            "confidence": 0.78,
            "reuse_score": 0.4,
        },
        execution_id="exec:graph",
    )
    bus.route(program["object_id"])

    snapshot = bus.snapshot("exec:graph")
    model_report = bus.cognitive_object_model_report()

    assert snapshot["COGNITIVE_SNAPSHOT"] is True
    assert snapshot["object_graph"]["node_count"] == 2
    assert snapshot["object_graph"]["dependency_edge_count"] >= 1
    assert snapshot["semantic_distribution"]["Knowledge"] == 1
    assert snapshot["semantic_distribution"]["Execution"] == 1
    assert model_report["COGNITIVE_OBJECT_MODEL_REPORT"] is True
    assert model_report["objects_created"] == 2
    assert model_report["object_graph_metrics"]["node_count"] == 2
    assert model_report["identity_consistency"]["identity_survives_version_updates"] is True
    assert model_report["canonical_coverage"] == 1.0
    assert model_report["integration_health"]["duplicates_storage_layer"] is False


def test_ckil_exposes_cognitive_object_model_report(tmp_path):
    engine = CognitiveKnowledgeIntegrationLayer()
    report = engine.build_unified_cognitive_bus_report(
        execution_id="exec:ckil-object-model",
        runtime_reports={
            "truth_runtime": {
                "truth_candidates": [
                    {"truth_id": "truth:a", "confidence": 0.91}
                ]
            },
        },
    )

    model_report = report["cognitive_object_model"]
    assert model_report["COGNITIVE_OBJECT_MODEL_REPORT"] is True
    assert model_report["object_types"]["TRUTH"] == 1
    assert report["cognitive_snapshot"]["all_cognitive_objects"][0]["object_type"] == "TRUTH"
    assert report["future_subsystem_integration"]["world_model_stores_cognitive_objects"] is True
