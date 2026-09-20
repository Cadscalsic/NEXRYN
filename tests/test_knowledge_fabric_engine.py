from runtime.knowledge import KnowledgeFabricEngine, KnowledgeFabricRegistry


REQUIRED_FABRIC_FIELDS = {
    "fabric_id",
    "fabric_identity",
    "fabric_type",
    "fabric_scope",
    "fabric_confidence",
    "fabric_strength",
    "fabric_density",
    "fabric_stability",
    "fabric_priority",
    "fabric_version",
    "fabric_history",
}

REQUIRED_RELATION_FIELDS = {
    "relation_id",
    "source_entity_id",
    "target_entity_id",
    "relation_type",
    "relation_strength",
    "relation_confidence",
    "relation_direction",
    "relation_stability",
    "relation_origin",
    "evidence_ids",
    "context_ids",
    "relation_evidence",
    "relation_scope",
    "relation_temporality",
    "relation_causality",
    "provenance",
    "validity_scope",
    "lifecycle_state",
    "version",
}


def _entity(entity_id, identity, domain, category, *, confidence=0.82, stability=0.72):
    return {
        "semantic_memory_id": entity_id,
        "semantic_identity": identity,
        "semantic_domain": domain,
        "semantic_category": category,
        "semantic_level": category,
        "semantic_summary": f"{identity} in {domain}",
        "semantic_confidence": confidence,
        "semantic_stability": stability,
        "semantic_importance": confidence,
        "indexes": {
            "meaning": identity.lower().split() + domain.lower().split(),
        },
    }


def _semantic_memory_report():
    return {
        "SEMANTIC_MEMORY_REPORT": True,
        "Semantic Entities": [
            _entity("sem:domain:geometry", "Geometry", "Geometry", "Domain"),
            _entity("sem:concept:symmetry", "spatial symmetry", "Geometry", "Concept"),
            _entity("sem:truth:symmetry", "symmetry reduces uncertainty", "Geometry", "Truth", confidence=0.9),
            _entity("sem:domain:planning", "Planning", "Planning", "Domain"),
            _entity("sem:strategy:planning", "symmetry planning strategy", "Planning", "Strategy"),
            _entity("sem:domain:reasoning", "Reasoning", "Reasoning", "Domain"),
            _entity("sem:principle:reasoning", "uncertainty reasoning principle", "Reasoning", "Principle"),
        ],
        "Domains": ["Geometry", "Planning", "Reasoning"],
        "Relationships": [
            {
                "source": "sem:concept:symmetry",
                "target": "sem:truth:symmetry",
                "relationship_type": "Supports",
                "confidence": 0.86,
            },
            {
                "source": "sem:truth:symmetry",
                "target": "sem:principle:reasoning",
                "relationship_type": "Explains",
                "confidence": 0.78,
            },
        ],
        "Semantic Knowledge Graph": {
            "node_count": 7,
            "edge_count": 2,
        },
    }


def test_knowledge_fabric_builds_unified_cross_domain_relationships():
    report = KnowledgeFabricEngine().integrate(
        semantic_memory_report=_semantic_memory_report()
    )

    assert report["KNOWLEDGE_FABRIC_FOUNDATION_REPORT"] is True
    assert report["Integration Contracts"]["creates_new_memory_system"] is False
    assert report["Integration Contracts"]["duplicates_semantic_memory"] is False
    assert report["Integration Contracts"]["duplicates_semantic_payloads"] is False
    assert report["Integration Contracts"]["accepts_orphan_relationships"] is False
    assert report["Integration Contracts"]["creates_new_truth"] is False
    assert report["Integration Contracts"]["stores_relationships_only"] is True
    assert report["Integration Contracts"]["semantic_memory_remains_canonical"] is True
    assert report["Integration Contracts"]["queries_return_ids_before_hydration"] is True
    assert set(report["Connected Domains"]) == {"Geometry", "Planning", "Reasoning"}
    assert report["Disconnected Domains"] == []
    assert report["Relationship Count"] >= 3
    assert report["Bridge Count"] >= 1
    assert report["Cross-Domain Links"]
    assert report["Relation Intelligence"]["relation_intelligence_enabled"] is True
    assert report["Relation Intelligence"]["relationship_count"] == report["Relationship Count"]
    assert report["Relation Intelligence"]["strong_links"] >= 1
    assert report["Relation Intelligence"]["permanent_links"] >= 1
    assert report["Relation Intelligence"]["temporary_links"] >= 1
    assert report["Relation Intelligence"]["semantic_links"] >= 1
    assert report["Relation Intelligence"]["procedural_links"] >= 1
    topology = report["Fabric Topology Intelligence"]
    assert topology["topology_intelligence_enabled"] is True
    assert topology["Central Concepts"]
    assert topology["Most Influential Domains"]
    assert topology["Bridge Concepts"]
    assert topology["Semantic Hubs"]
    assert topology["Critical Connections"]
    assert topology["Transfer Paths"]
    assert topology["Reasoning Corridors"]
    assert topology["Knowledge Communities"]
    assert topology["world_model_preparation"]["uses_ids_only"] is True
    assert report["Connectivity Metrics"]["cross_domain_coverage"] == 1.0
    assert report["Semantic Coverage"]["coverage_ratio"] == 1.0


def test_knowledge_fabric_registry_deduplicates_relationships_with_marker_index():
    registry = KnowledgeFabricRegistry()
    registry.allow_references(["sem:left", "sem:right"])
    relationship = {
        "source": "sem:left",
        "target": "sem:right",
        "relationship_type": "Supports",
        "confidence": 0.8,
    }

    registry.add_relationship(relationship)
    registry.add_relationship(relationship)

    assert len(registry.fabric_relationships) == 1
    assert registry.fabric_relationships[0]["source_entity_id"] == "sem:left"
    assert registry.fabric_relationships[0]["target_entity_id"] == "sem:right"
    assert len(registry._fabric_relationship_markers) == 1


def test_fabric_entities_and_relations_reference_semantic_ids_only():
    report = KnowledgeFabricEngine().integrate(
        semantic_memory_report=_semantic_memory_report()
    )

    assert report["Fabric Entities"]
    for entity in report["Fabric Entities"]:
        assert REQUIRED_FABRIC_FIELDS <= set(entity)
        assert entity["source_entity_ids"] or entity["target_entity_ids"]
        assert "semantic_identity" not in entity
        assert "semantic_summary" not in entity
        assert "semantic_domain" not in entity
        assert all(item.startswith("sem:") for item in entity["source_entity_ids"])
        assert all(item.startswith("sem:") for item in entity["target_entity_ids"])

    assert report["Fabric Relationships"]
    for relation in report["Fabric Relationships"]:
        assert REQUIRED_RELATION_FIELDS <= set(relation)
        assert relation["source_entity_id"].startswith("sem:")
        assert relation["target_entity_id"].startswith("sem:")
        assert "concept name" not in relation
        assert "semantic_summary" not in relation
        assert "truth_payload" not in relation
        assert relation["relation_direction"] in {
            "DIRECTED",
            "BIDIRECTIONAL",
            "REVERSE_DEPENDENCY",
        }
        assert 0.0 <= relation["relation_stability"] <= 1.0
        assert relation["relation_origin"] in {
            "SEMANTIC_MEMORY",
            "FABRIC_INFERENCE",
            "UNKNOWN",
        }
        assert relation["relation_scope"] in {
            "INTRA_DOMAIN",
            "CROSS_DOMAIN",
            "UNSCOPED",
        }
        assert relation["relation_temporality"] in {
            "PERMANENT",
            "TEMPORARY",
            "CONDITIONAL",
        }
        assert relation["relation_causality"] in {
            "CAUSAL",
            "STATISTICAL",
            "SEMANTIC",
            "PROCEDURAL",
        }
        assert relation["relation_evidence"]["provenance_support"] is not None
        assert relation["lifecycle_state"] in {
            "PROPOSED",
            "EVIDENCE_SUPPORTED",
            "VALIDATED",
            "STABLE",
        }

    inferred = [
        relation for relation in report["Fabric Relationships"]
        if relation["provenance"].get("source") == "fabric_relation_hypothesis"
    ]
    assert inferred
    assert all(relation["lifecycle_state"] == "PROPOSED" for relation in inferred)


def test_knowledge_fabric_detects_disconnected_domains():
    semantic_report = {
        "SEMANTIC_MEMORY_REPORT": True,
        "Semantic Entities": [
            _entity("sem:domain:geometry", "Geometry", "Geometry", "Domain"),
            _entity("sem:concept:symmetry", "spatial symmetry", "Geometry", "Concept"),
            _entity("sem:domain:counting", "Counting", "Counting", "Domain"),
            _entity("sem:concept:quantity", "quantity cardinality", "Counting", "Concept"),
            _entity("sem:domain:governance", "Governance", "Governance", "Domain"),
            _entity("sem:policy:boundary", "executive policy boundary", "Governance", "Policy", confidence=0.33, stability=0.31),
        ],
        "Domains": ["Geometry", "Counting", "Governance"],
        "Relationships": [
            {
                "source": "sem:concept:symmetry",
                "target": "sem:domain:geometry",
                "relationship_type": "Belongs To",
                "confidence": 0.8,
            },
            {
                "source": "sem:concept:quantity",
                "target": "sem:domain:counting",
                "relationship_type": "Belongs To",
                "confidence": 0.76,
            },
        ],
    }

    report = KnowledgeFabricEngine().integrate(semantic_memory_report=semantic_report)

    assert "Governance" in report["Disconnected Domains"]
    assert report["Connectivity Metrics"]["cross_domain_coverage"] < 1.0
    assert report["Weak Connections"]
    assert report["Semantic Coverage"]["semantic_memory_is_canonical"] is True


def test_knowledge_fabric_rejects_orphan_semantic_references():
    semantic_report = _semantic_memory_report()
    semantic_report["Relationships"] = [
        *semantic_report["Relationships"],
        {
            "source": "sem:concept:symmetry",
            "target": "sem:missing:target",
            "relationship_type": "Supports",
            "confidence": 0.99,
        },
    ]

    report = KnowledgeFabricEngine().integrate(semantic_memory_report=semantic_report)

    relation_targets = {
        relation["target_entity_id"]
        for relation in report["Fabric Relationships"]
    }
    assert "sem:missing:target" not in relation_targets


def test_knowledge_fabric_topology_intelligence_surfaces_world_model_signals():
    report = KnowledgeFabricEngine().integrate(
        semantic_memory_report=_semantic_memory_report()
    )
    topology = report["Fabric Topology Intelligence"]

    expected = {
        "Central Concepts",
        "Most Influential Domains",
        "Bridge Concepts",
        "Semantic Hubs",
        "Critical Connections",
        "Weak Regions",
        "Knowledge Bottlenecks",
        "Transfer Paths",
        "Reasoning Corridors",
        "Knowledge Communities",
    }
    assert expected <= set(topology)
    assert all("entity_id" in item for item in topology["Central Concepts"])
    assert all("domain" in item for item in topology["Most Influential Domains"])
    assert all("relation_id" in item for item in topology["Critical Connections"])
    assert all("entity_path" in item for item in topology["Transfer Paths"])
    assert all("entity_ids" in item for item in topology["Knowledge Communities"])
    assert "semantic_summary" not in topology["Central Concepts"][0]
    assert "semantic_payload" not in topology["Knowledge Communities"][0]
    assert topology["world_model_preparation"]["community_count"] >= 1
