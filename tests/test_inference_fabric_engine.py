from runtime.knowledge import InferenceFabricEngine


def _fabric_report():
    return {
        "KNOWLEDGE_FABRIC_FOUNDATION_REPORT": True,
        "Fabric Entities": [
            {
                "fabric_id": "fabric:global",
                "source_entity_ids": [
                    "sem:domain:geometry",
                    "sem:domain:transformation",
                    "sem:domain:planning",
                    "sem:domain:prediction",
                ],
                "target_entity_ids": [
                    "sem:domain:geometry",
                    "sem:domain:transformation",
                    "sem:domain:planning",
                    "sem:domain:prediction",
                ],
            }
        ],
        "Fabric Relationships": [
            _relation(
                "FAB-REL-001",
                "sem:domain:geometry",
                "sem:domain:transformation",
                "Bridges",
                0.88,
                0.82,
            ),
            _relation(
                "FAB-REL-002",
                "sem:domain:transformation",
                "sem:domain:planning",
                "Transfers",
                0.84,
                0.78,
            ),
            _relation(
                "FAB-REL-003",
                "sem:domain:planning",
                "sem:domain:prediction",
                "Predicts",
                0.8,
                0.74,
            ),
            _relation(
                "FAB-REL-004",
                "sem:domain:geometry",
                "sem:domain:prediction",
                "Complements",
                0.45,
                0.35,
            ),
        ],
    }


def _relation(relation_id, source, target, relation_type, confidence, strength):
    return {
        "relation_id": relation_id,
        "source_entity_id": source,
        "target_entity_id": target,
        "relation_type": relation_type,
        "relation_confidence": confidence,
        "relation_strength": strength,
        "evidence_ids": [],
        "context_ids": [],
        "provenance": {"source": "knowledge_fabric"},
        "validity_scope": {
            "source_domain": source.removeprefix("sem:domain:").title(),
            "target_domain": target.removeprefix("sem:domain:").title(),
            "cross_domain": source != target,
        },
        "lifecycle_state": "VALIDATED",
        "version": 1,
    }


def test_inference_fabric_builds_dynamic_paths_over_knowledge_fabric():
    report = InferenceFabricEngine().build_report(
        knowledge_fabric_report=_fabric_report(),
        source_entity_id="sem:domain:geometry",
        target_entity_id="sem:domain:prediction",
        inference_goal="prediction",
        max_depth=3,
    )

    assert report["INFERENCE_FABRIC_REPORT"] is True
    assert report["Integration Contracts"]["stores_relationships"] is False
    assert report["Integration Contracts"]["duplicates_knowledge_fabric"] is False
    assert report["Integration Contracts"]["creates_new_truth"] is False
    assert report["Integration Contracts"]["returns_dynamic_inference_paths"] is True
    assert report["Integration Contracts"]["returns_ids_for_later_hydration"] is True
    assert report["path_count"] >= 1

    best = report["Inference Paths"][0]
    assert best["source_entity_id"] == "sem:domain:geometry"
    assert best["target_entity_id"] == "sem:domain:prediction"
    assert best["dynamic"] is True
    assert best["entity_path"] == [
        "sem:domain:geometry",
        "sem:domain:transformation",
        "sem:domain:planning",
        "sem:domain:prediction",
    ]
    assert best["relation_path"] == ["FAB-REL-001", "FAB-REL-002", "FAB-REL-003"]
    assert best["cross_domain_steps"] == 3
    assert "semantic_summary" not in best
    assert "concept_payload" not in best


def test_inference_fabric_prepares_mental_models_without_mutating_fabric():
    fabric = _fabric_report()
    before_relationships = list(fabric["Fabric Relationships"])

    report = InferenceFabricEngine().build_report(
        knowledge_fabric_report=fabric,
        inference_goal="mental_model_discovery",
        max_depth=2,
        top_k=5,
    )

    assert fabric["Fabric Relationships"] == before_relationships
    assert report["Mental Model Preparation"]["ready"] is True
    assert report["Mental Model Preparation"]["entity_paths"]
    assert report["Integration Contracts"]["mutates_knowledge_fabric"] is False
    assert report["Integration Contracts"]["mutates_semantic_memory"] is False
    assert report["Dynamic Path Statistics"]["average_depth"] > 0
