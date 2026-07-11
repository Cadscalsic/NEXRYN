from runtime.objects import CognitiveObjectRegistry, UnifiedCognitiveObjectLayer


def _layer(tmp_path):
    return UnifiedCognitiveObjectLayer(
        CognitiveObjectRegistry(tmp_path / "object_registry.json")
    )


def _artifact_lifecycle_report():
    return {
        "artifact_registry": {
            "concept:a": {
                "artifact_id": "concept:a",
                "artifact_type": "CONCEPT",
                "owner_runtime": "concept_formation_runtime",
                "origin_runtime": "concept_formation_runtime",
                "lifecycle_state": "PUBLISHED",
                "confidence": 0.82,
                "lineage": [],
            },
            "program:a": {
                "artifact_id": "program:a",
                "artifact_type": "PROGRAM",
                "owner_runtime": "program_synthesis_runtime",
                "origin_runtime": "program_synthesis_runtime",
                "lifecycle_state": "VALIDATED",
                "confidence": 0.78,
                "required_concepts": ["concept:a"],
                "lineage": ["concept:a"],
            },
            "evidence:a": {
                "artifact_id": "evidence:a",
                "artifact_type": "EVIDENCE",
                "owner_runtime": "evidence_builder_runtime",
                "origin_runtime": "evidence_builder_runtime",
                "lifecycle_state": "PROMOTED",
                "confidence": 0.86,
                "supporting_programs": ["program:a"],
                "evidence_references": ["concept:a"],
                "lineage": ["concept:a", "program:a"],
            },
            "truth:a": {
                "artifact_id": "truth:a",
                "artifact_type": "TRUTH",
                "owner_runtime": "truth_runtime",
                "origin_runtime": "truth_runtime",
                "lifecycle_state": "COMMITTED",
                "confidence": 0.9,
                "evidence_references": ["evidence:a"],
                "lineage": ["evidence:a"],
            },
        },
        "relationships": [
            {"source": "concept:a", "target": "program:a", "relationship": "supports"},
            {"source": "program:a", "target": "evidence:a", "relationship": "supports"},
            {"source": "evidence:a", "target": "truth:a", "relationship": "validated_by"},
        ],
    }


def _semantic_report():
    return {
        "SEMANTIC_INTEGRATION_REPORT": True,
        "discovered_domains": ["Geometry"],
        "canonical_concepts": [
            {
                "semantic_id": "semantic:spatial",
                "canonical_name": "Spatial Transformation",
                "domain": "Geometry",
                "confidence": 0.84,
                "supporting_concepts": ["concept:a"],
            }
        ],
    }


def _experience_report():
    return {
        "COGNITIVE_EXPERIENCE_REPORT": True,
        "experience": {
            "experience_id": "experience:one",
            "execution_id": "execution:one",
            "situation_id": "situation:one",
            "semantic_domains": ["Geometry"],
            "concepts": [{"concept_id": "concept:a", "confidence": 0.82}],
            "programs": [{"program_id": "program:a", "confidence": 0.78}],
            "evidence": [{"id": "evidence:a", "confidence": 0.86}],
            "truth": [{"truth_id": "truth:a", "confidence": 0.9}],
            "decisions_taken": [{"decision_id": "decision:a", "confidence": 0.75}],
            "policies_used": [{"policy_id": "policy:a", "confidence": 0.7}],
            "mental_model_updates": [
                {
                    "mental_model_id": "mental:spatial",
                    "domain": "Geometry",
                    "confidence": 0.8,
                }
            ],
        },
    }


def test_unified_cognitive_object_layer_normalizes_runtime_artifacts(tmp_path):
    report = _layer(tmp_path).build_report(
        artifact_lifecycle_report=_artifact_lifecycle_report(),
        semantic_report=_semantic_report(),
        experience_report=_experience_report(),
        situation_report={"situation_id": "situation:one", "confidence": 0.81},
        decision_report={"selected_decision": {"decision_id": "decision:a", "decision_confidence": 0.75}},
        policy_report={"selected_policy": {"policy_id": "policy:a", "confidence": 0.7}},
        world_model_report={"committed_updates": ["world:spatial"]},
        dna_report={"traits": {"Geometry": "spatial_bias"}},
        execution_id="execution:one",
    )

    object_types = {item["object_type"] for item in report["objects"]}
    identities = [item["object_id"] for item in report["objects"]]

    assert report["UNIFIED_COGNITIVE_OBJECT_REPORT"] is True
    assert {"CONCEPT", "PROGRAM", "EVIDENCE", "TRUTH", "SEMANTIC_ABSTRACTION", "EXPERIENCE", "SITUATION", "DECISION", "POLICY"}.issubset(object_types)
    assert all(identity.startswith("COG-") for identity in identities)
    assert len(set(identities)) == len(identities)
    assert report["identity_coverage"] == 1.0
    assert report["lifecycle_coverage"] == 1.0
    assert report["relationship_density"] > 0
    assert report["semantic_density"] > 0
    assert report["reuse_score"] > 0
    assert report["compression_ratio"] > 0
    assert report["object_evolution"]["objects_with_history"] == report["object_count"]
    assert report["lineage_statistics"]["lineage_completeness"] > 0
    assert report["world_model_references"]
    assert report["dna_references"]
    assert report["experience_references"] == ["experience:one"]
    assert report["semantic_integration"]["semantic_clusters_are_cognitive_object_collections"] is True
    assert report["experience_engine_integration"]["experiences_are_cognitive_object_collections"] is True
    assert report["world_model_integration"]["world_model_stores_cognitive_objects"] is True
    assert report["mental_model_integration"]["mental_models_emerge_from_object_subgraphs"] is True
    assert report["dna_integration"]["dna_evolves_from_object_histories"] is True
    assert report["decision_intelligence_integration"]["decisions_consume_cognitive_objects"] is True
    assert report["situation_awareness_integration"]["situations_are_cognitive_object_collections"] is True
    assert report["world_governance_integration"]["governs_object_flow"] is True
    assert report["meta_cognition"]["evaluates_object_quality"] is True
    assert report["object_governance"]["creation_governed"] is True
    assert report["runtime_alignment"]["removes_existing_runtime_artifacts"] is False


def test_cognitive_object_identity_is_permanent_across_evolution(tmp_path):
    layer = _layer(tmp_path)

    first = layer.build_report(
        artifact_lifecycle_report=_artifact_lifecycle_report(),
        semantic_report=_semantic_report(),
        experience_report=_experience_report(),
        execution_id="execution:one",
    )
    evolved = _artifact_lifecycle_report()
    evolved["artifact_registry"]["truth:a"]["lifecycle_state"] = "ARCHIVED"
    evolved["artifact_registry"]["truth:a"]["confidence"] = 0.92
    second = layer.build_report(
        artifact_lifecycle_report=evolved,
        semantic_report=_semantic_report(),
        experience_report=_experience_report(),
        execution_id="execution:one",
    )

    first_truth = next(item for item in first["objects"] if item["source_artifact_id"] == "truth:a")
    second_truth = next(item for item in second["objects"] if item["source_artifact_id"] == "truth:a")

    assert first_truth["object_id"] == second_truth["object_id"]
    assert first_truth["global_identity"] == second_truth["global_identity"]
    assert second_truth["lifecycle_state"] == "ARCHIVED"
    assert second["persistence"]["identity_count"] >= first["persistence"]["identity_count"]
    assert second["lifecycle_statistics"]["permanent_identity_preserved"] is True
