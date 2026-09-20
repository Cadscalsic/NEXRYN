from runtime.process import (
    CognitiveArtifactSemanticContextEngine,
    ProcessSemanticContextEngine,
    SemanticContextRegistry,
)


def symmetry_artifact():
    return {
        "object_id": "concept:symmetry_reasoning",
        "execution_id": "exec:semantic:001",
        "runtime_origin": "concept_formation_runtime",
        "concept": "symmetry_reasoning",
        "semantic_role_hint": "concept transformation",
        "evidence": [
            "geometry",
            "shape",
            "symmetry",
            "reflection",
            "mirror",
            "spatial",
            "pattern",
        ],
        "preconditions": ["object_identity_exists", "shape_known"],
        "invariants": ["topology_preserved", "identity_preserved"],
        "related_objects": ["mirror", "rotation", "flip"],
        "confidence": 0.88,
    }


def test_artifact_receives_complete_semantic_context_without_mutation():
    artifact = symmetry_artifact()
    original = dict(artifact)

    report = CognitiveArtifactSemanticContextEngine().contextualize(artifact)
    context = report["semantic_context"]

    assert artifact == original
    assert report["semantic_context_registered"] is True
    assert context["object_id"] == "concept:symmetry_reasoning"
    assert context["execution_id"] == "exec:semantic:001"
    assert context["runtime_origin"] == "concept_formation_runtime"
    assert context["primary_domain"] == "Geometry & Shape"
    assert "Spatial Reasoning" in context["secondary_domains"]
    assert context["semantic_role"] in {"Concept", "Transformation"}
    assert context["operation_family"]
    assert context["reasoning_family"]
    assert context["concept_family"]
    assert context["task_family"]
    assert context["object_family"]
    assert context["causal_family"]
    assert context["transformation_family"] == "reflection"
    assert context["context_confidence"] >= 0.88
    assert context["context_stability"] > 0.0
    assert context["context_version"] == 1


def test_context_models_boundaries_neighborhoods_distance_and_hierarchy():
    context = CognitiveArtifactSemanticContextEngine().contextualize(
        symmetry_artifact(),
        runtime_context={
            "environment_constraints": ["grid_world"],
            "generalization_limits": ["requires_shape_evidence"],
        },
    )["semantic_context"]

    boundary = context["boundary"]

    assert boundary["valid_conditions"] == [
        "object_identity_exists",
        "shape_known",
    ]
    assert boundary["required_prerequisites"] == [
        "object_identity_exists",
        "shape_known",
    ]
    assert boundary["environment_constraints"] == ["grid_world"]
    assert boundary["transformation_constraints"] == [
        "topology_preserved",
        "identity_preserved",
    ]
    assert "confidence_is_not_truth" in boundary["confidence_limits"]
    assert boundary["generalization_limits"] == ["requires_shape_evidence"]

    assert "reflection" in context["semantic_neighbors"]
    assert "geometry_and_shape" in context["parent_abstractions"]
    assert "symmetry_reasoning" in context["child_specializations"]
    assert "reflection" in context["child_specializations"]
    assert "geometry_and_shape" in context["semantic_distance"]
    assert context["semantic_distance"]["geometry_and_shape"] < 1.0


def test_relationship_discovery_and_registry_versioning_are_explicit():
    registry = SemanticContextRegistry()
    engine = CognitiveArtifactSemanticContextEngine(registry=registry)
    artifact = {
        "object_id": "evidence:growth_support",
        "runtime_origin": "evidence_builder_runtime",
        "evidence": [
            "supports",
            "depends",
            "causal",
            "growth",
            "transition",
            "object",
        ],
        "related_objects": ["concept:growth", "truth:growth_candidate"],
        "support_score": 0.91,
    }

    first = engine.contextualize(artifact)["semantic_context"]
    second = engine.contextualize(artifact)["semantic_context"]
    relationships = {
        edge["relationship"] for edge in second["semantic_edges"]
    }

    assert first["context_id"] == second["context_id"]
    assert second["context_version"] == 2
    assert {"Depends On", "Supports"}.issubset(relationships)
    assert registry.get_by_object("evidence:growth_support")["context_id"] == (
        first["context_id"]
    )
    assert registry.report()["semantic_backbone_ready"] is True


def test_process_semantic_context_engine_exposes_artifact_contextualization():
    engine = ProcessSemanticContextEngine()
    report = engine.contextualize_artifact(symmetry_artifact())

    assert report["semantic_context_required"] is True
    assert report["semantic_context"]["primary_domain"] == "Geometry & Shape"
    assert engine.semantic_registry_report()["semantic_context_count"] == 1


def residual_artifact(index):
    return {
        "object_id": f"observation:downward_propagation_{index}",
        "execution_id": f"exec:residual:{index}",
        "runtime_origin": "evidence_builder_runtime",
        "observed_behavior": [
            "downward",
            "propagation",
            "collision",
            "stopping",
            "spatial",
            "motion",
        ],
    }


def test_low_confidence_assignments_become_semantic_residuals_and_clusters():
    engine = CognitiveArtifactSemanticContextEngine(assignment_threshold=0.72)

    reports = [
        engine.contextualize(residual_artifact(index))
        for index in range(3)
    ]
    registry = engine.registry_report()

    assert all(report["semantic_residual_created"] for report in reports)
    assert all(
        report["truth_candidate_blocked_by_semantic_context"]
        for report in reports
    )
    assert registry["residual_count"] == 3
    assert len(registry["residual_clusters"]) == 1
    assert registry["residual_clusters"][0]["status"] == "CANDIDATE_CONCEPT"
    assert registry["candidate_concepts"] == [
        "candidate_concept:gravity_simulation"
    ]
    assert registry["unknown_regions"]
    assert registry["unknown_regions"][0]["density_score"] >= 0.5


def test_context_evolution_versions_lifecycle_and_confidence_history():
    engine = CognitiveArtifactSemanticContextEngine()
    report = engine.contextualize(symmetry_artifact())
    context_id = report["semantic_context_id"]

    evolved = engine.evolve_context(
        context_id,
        change_reason="truth_runtime_supported_context",
        supporting_evidence=["validated_trial", "boundary_retest"],
        author_runtime="truth_runtime",
        target_stage="VALIDATED",
        confidence_updates={
            "assignment_confidence": 0.94,
            "boundary_confidence": 0.91,
            "relationship_confidence": 0.88,
            "domain_confidence": 0.95,
            "role_confidence": 0.90,
            "generalization_confidence": 0.82,
            "overall_context_confidence": 0.92,
        },
    )
    registry = engine.registry_report()
    version_event = registry["version_history"][context_id][-1]

    assert evolved["context_version"] == 2
    assert evolved["lifecycle_stage"] == "VALIDATED"
    assert evolved["overall_context_confidence"] == 0.92
    assert version_event["previous_version"] == 1
    assert version_event["new_version"] == 2
    assert version_event["change_reason"] == "truth_runtime_supported_context"
    assert version_event["historical_snapshot"]["context_version"] == 1


def test_ontology_gaps_prediction_errors_and_semantic_report_are_measurable():
    engine = CognitiveArtifactSemanticContextEngine()
    context = engine.contextualize(symmetry_artifact())["semantic_context"]
    engine.record_prediction_error(
        context["context_id"],
        predicted="mirror_reflection",
        observed="rotation_like_change",
        error_score=0.64,
        runtime_origin="world_model",
    )

    report = engine.process_semantic_context_report()

    assert report["PROCESS_SEMANTIC_CONTEXT_REPORT"] is True
    assert report["semantic_contexts_created"] == 1
    assert report["semantic_graph_statistics"]["node_count"] >= 1
    assert report["prediction_errors"][0]["prediction_error"] == 0.64
    assert report["ontology_gaps"]
    assert report["context_confidence_distribution"]["medium"] >= 1
    assert report["integration_health"]["world_model_semantic_context_ready"]


def test_runtime_integration_packet_feeds_world_model_dna_meta_and_governance():
    engine = ProcessSemanticContextEngine()
    context = engine.contextualize_artifact(symmetry_artifact())[
        "semantic_context"
    ]
    packet = engine.runtime_integration_packet()

    world_entity = packet["world_model_entities"][0]
    dna_experience = packet["dna_semantic_experiences"][0]
    meta = packet["meta_cognition"]
    governance = packet["executive_world_governance"]

    assert world_entity["entity_id"] == context["object_id"]
    assert world_entity["meaning"]["context_id"] == context["context_id"]
    assert world_entity["boundaries"]
    assert "Geometry & Shape" in world_entity["domains"]
    assert dna_experience["semantic_domain"] == "Geometry & Shape"
    assert meta["context_quality"] > 0.0
    assert governance["runtime_steering"] == "semantic_context_aware"
