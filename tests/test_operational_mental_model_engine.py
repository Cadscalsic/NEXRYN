from runtime.mental_models import (
    Mechanism,
    MechanismDiscoveryEngine,
    MechanismLibrary,
    MentalModel,
    MentalModelConstructionEngine,
    MentalModelEngine,
    MentalModelValidationEngine,
)


def _semantic_memory_report():
    return {
        "SEMANTIC_MEMORY_REPORT": True,
        "Domains": ["Geometry", "Transformation", "Planning"],
        "Semantic Entities": [
            {"semantic_memory_id": "sem:rotation", "semantic_domain": "Geometry"},
            {"semantic_memory_id": "sem:transformation", "semantic_domain": "Transformation"},
            {"semantic_memory_id": "sem:planning", "semantic_domain": "Planning"},
        ],
    }


def _relation(relation_id, source, target, relation_type, confidence=0.82, strength=0.78):
    return {
        "relation_id": relation_id,
        "source_entity_id": source,
        "target_entity_id": target,
        "relation_type": relation_type,
        "relation_strength": strength,
        "relation_confidence": confidence,
        "relation_direction": "DIRECTED",
        "relation_stability": 0.76,
        "relation_origin": "SEMANTIC_MEMORY",
        "evidence_ids": ["evd:1"],
        "context_ids": ["ctx:1"],
        "relation_evidence": {"evidence_ids": ["evd:1"], "context_ids": ["ctx:1"]},
        "relation_scope": "CROSS_DOMAIN",
        "relation_temporality": "PERMANENT",
        "relation_causality": "PROCEDURAL",
        "provenance": {"source": "semantic_memory_relationship"},
        "validity_scope": {
            "source_domain": source.removeprefix("sem:").title(),
            "target_domain": target.removeprefix("sem:").title(),
            "cross_domain": True,
        },
        "lifecycle_state": "VALIDATED",
        "version": 1,
    }


def _knowledge_fabric_report():
    relationships = [
        _relation("FAB-REL-ROT-TRANS", "sem:rotation", "sem:transformation", "Generalizes", 0.86, 0.8),
        _relation("FAB-REL-TRANS-PLAN", "sem:transformation", "sem:planning", "Transfers", 0.82, 0.77),
    ]
    return {
        "KNOWLEDGE_FABRIC_FOUNDATION_REPORT": True,
        "Fabric Relationships": relationships,
        "Fabric Topology Intelligence": {
            "Critical Connections": [
                {
                    "relation_id": "FAB-REL-ROT-TRANS",
                    "source_entity_id": "sem:rotation",
                    "target_entity_id": "sem:transformation",
                    "criticality_score": 2.4,
                }
            ]
        },
    }


def _inference_fabric_report():
    return {
        "INFERENCE_FABRIC_REPORT": True,
        "Inference Paths": [
            {
                "inference_path_id": "INF-PATH-1",
                "source_entity_id": "sem:rotation",
                "target_entity_id": "sem:planning",
                "inference_goal": "mental_model_discovery",
                "entity_path": ["sem:rotation", "sem:transformation", "sem:planning"],
                "relation_path": ["FAB-REL-ROT-TRANS", "FAB-REL-TRANS-PLAN"],
                "relation_types": ["Generalizes", "Transfers"],
                "path_confidence": 0.84,
                "path_strength": 0.78,
                "path_depth": 2,
                "cross_domain_steps": 2,
            }
        ],
    }


def test_mental_models_are_executable_mechanisms_grounded_in_fabric():
    report = MentalModelEngine().discover(
        semantic_memory_report=_semantic_memory_report(),
        knowledge_fabric_report=_knowledge_fabric_report(),
        inference_fabric_report=_inference_fabric_report(),
    )

    assert report["MENTAL_MODEL_DISCOVERY_REPORT"] is True
    assert report["Integration Contracts"]["semantic_memory_owns_meaning"] is True
    assert report["Integration Contracts"]["knowledge_fabric_owns_relationships"] is True
    assert report["Integration Contracts"]["mental_models_own_executable_mechanisms"] is True
    assert report["Integration Contracts"]["does_not_duplicate_semantic_payloads"] is True
    assert report["Integration Contracts"]["stores_source_ids_and_subgraph_signatures"] is True
    assert report["Integration Contracts"]["mental_models_are_not_graphs"] is True
    assert report["Integration Contracts"]["mechanism_construction_replaces_global_pattern_mining"] is True
    assert report["Mechanism Construction"]["mental_models_are_executable_mechanisms"] is True
    assert report["Mechanism Construction"]["not_pattern_mining"] is True
    assert report["Mechanism Construction"]["not_graph_summary"] is True
    assert report["Mechanism Construction"]["does_not_consume_entire_fabric_at_once"] is True
    assert report["Mechanism Discovery Engine"]["MECHANISM_DISCOVERY_REPORT"] is True
    assert report["Mechanism Library"]["MECHANISM_LIBRARY_REPORT"] is True
    assert report["Mental Model Construction"]["MENTAL_MODEL_CONSTRUCTION_REPORT"] is True
    assert report["Mental Model Validation"]["MENTAL_MODEL_VALIDATION_REPORT"] is True
    assert report["Integration Contracts"]["mechanism_discovery_owns_mechanism_discovery"] is True
    assert report["Integration Contracts"]["mechanism_library_owns_reusable_mechanisms"] is True
    assert report["Integration Contracts"]["mental_model_construction_owns_model_composition"] is True
    assert report["Integration Contracts"]["mental_model_validation_owns_model_testing"] is True
    assert report["mental_model_count"] == 1

    model = report["Mental Models"][0]
    assert model["model_type"] in {
        "PROCEDURAL_MODEL",
        "STRUCTURAL_MODEL",
        "PLANNING_MODEL",
    }
    assert model["source_semantic_ids"] == ["sem:rotation", "sem:transformation", "sem:planning"]
    assert model["source_fabric_relation_ids"] == ["FAB-REL-ROT-TRANS", "FAB-REL-TRANS-PLAN"]
    assert model["input_schema"]
    assert model["state_representation"]
    assert model["mechanism"]
    assert model["mechanism"]["construction_mode"] == "mechanism_construction_not_pattern_mining"
    assert model["state_variables"]
    assert model["inputs"]
    assert model["outputs"]
    assert model["core_mechanism"]
    assert model["transition_function"]
    assert model["transition_rules"]
    assert model["invariants"]
    assert model["failure_modes"]
    assert model["predictions"]
    assert model["explanations"]
    assert model["prediction_function"] == "predict"
    assert model["explanation_function"] == "explain"
    assert model["simulation_function"] == "simulate"
    assert model["decision_support_function"] == "compare_alternatives"
    assert model["lifecycle_state"] in {
        "DISCOVERED",
        "PROVISIONAL",
        "SUPPORTED",
        "VALIDATED",
        "OPERATIONAL",
        "GENERALIZED",
        "CANONICAL",
    }
    assert "semantic_summary" not in model
    assert "truth_payload" not in model


def test_operational_mental_model_methods_execute_without_storing_meaning():
    engine = MentalModelEngine()
    engine.discover(
        semantic_memory_report=_semantic_memory_report(),
        knowledge_fabric_report=_knowledge_fabric_report(),
        inference_fabric_report=_inference_fabric_report(),
    )
    model = next(iter(engine.library.models.values()))

    prediction = model.predict({"object_state": "S", "transformation": "rotation"})
    explanation = model.explain({"object_state": "S"}, prediction["predicted_state"])
    simulation = model.simulate({"object_state": "S"}, {"operation": "rotate"})
    validation = model.validate({"object_state": "S_prime"})
    comparison = model.compare_alternatives([
        {"operation": "rotate"},
        {"operation": "translate"},
    ])
    confidence = model.estimate_confidence()

    assert prediction["predicted_state"]["applied_transition_rules"]
    assert prediction["predicted_state"]["transition_function"]
    assert explanation["source_semantic_ids"] == model.source_semantic_ids
    assert simulation["simulation_trace"]
    assert validation["validation_status"] in {"SUPPORTED", "UNVERIFIED"}
    assert comparison["ranked_alternatives"]
    assert confidence["confidence"] > 0


def test_mental_model_library_supports_selection_and_composition():
    engine = MentalModelEngine()
    engine.discover(
        semantic_memory_report=_semantic_memory_report(),
        knowledge_fabric_report=_knowledge_fabric_report(),
        inference_fabric_report=_inference_fabric_report(),
    )
    model_ids = list(engine.library.models)
    selected = engine.library.select(domains=["Geometry", "Planning"])
    composition = engine.library.compose(model_ids, composition_type="Model Ensemble")

    assert selected["selection_uses_operational_models"] is True
    assert selected["selected_mental_model"]
    assert composition["supports_model_ensemble"] is True
    assert composition["source_semantic_ids"]
    assert composition["source_fabric_relation_ids"]


def test_mental_model_discovery_limits_candidates_instead_of_mining_entire_fabric():
    inference = _inference_fabric_report()
    inference["Inference Paths"] = [
        {
            **inference["Inference Paths"][0],
            "inference_path_id": f"INF-PATH-{index}",
            "relation_path": ["FAB-REL-ROT-TRANS", "FAB-REL-TRANS-PLAN"],
            "path_confidence": 0.7 + index * 0.001,
        }
        for index in range(30)
    ]

    report = MentalModelEngine().discover(
        semantic_memory_report=_semantic_memory_report(),
        knowledge_fabric_report=_knowledge_fabric_report(),
        inference_fabric_report=inference,
    )

    assert report["mental_model_count"] <= report["Mechanism Construction"]["max_candidate_paths"]
    assert report["Mechanism Construction"]["does_not_consume_entire_fabric_at_once"] is True


def test_new_map_separates_mechanism_discovery_library_construction_and_validation():
    discovery = MechanismDiscoveryEngine().discover(
        semantic_memory_report=_semantic_memory_report(),
        knowledge_fabric_report=_knowledge_fabric_report(),
        inference_fabric_report=_inference_fabric_report(),
    )
    mechanism_library = MechanismLibrary()
    mechanisms = [
        mechanism_library.upsert(Mechanism(**item))
        for item in discovery["Mechanism Candidates"]
    ]
    construction = MentalModelConstructionEngine().construct(mechanisms)
    constructed = [
        MentalModel(**item)
        for item in construction["Constructed Mental Models"]
    ]
    validation = MentalModelValidationEngine().validate(constructed)

    assert discovery["MECHANISM_DISCOVERY_REPORT"] is True
    assert discovery["not_pattern_mining"] is True
    assert mechanism_library.report()["stores_reusable_mechanisms"] is True
    assert construction["constructs_from_mechanisms"] is True
    assert construction["does_not_discover_mechanisms"] is True
    assert validation["tests_invariants"] is True
    assert validation["promotes_only_valid_models"] is True
