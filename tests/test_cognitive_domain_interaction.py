from runtime.knowledge import CognitiveDomainInteractionRegistry


def test_cognitive_domain_interaction_builds_dependency_and_composition():
    report = CognitiveDomainInteractionRegistry().build({
        "domain_registry": [
            {
                "domain_name": "Physics Domain",
                "semantic_capability_evolution": ["gravity"],
                "required_domains": ["Spatial Domain", "Geometry Domain"],
                "operational_capability_evolution": ["object_motion_reasoning"],
            },
            {
                "domain_name": "Spatial Domain",
                "semantic_capability_evolution": ["relative_position"],
            },
            {
                "domain_name": "Geometry Domain",
                "semantic_capability_evolution": ["object_shape"],
            },
        ],
    })

    physics = {
        row["domain_name"]: row
        for row in report["domain_interaction_reports"]
    }["Physics Domain"]
    gravity = {
        row["composition_name"]: row
        for row in report["operational_capability_compositions"]
    }["Object Falling Simulation"]

    assert report["validation_success"] is False
    assert "Spatial Domain" in physics["collaborating_domains"]
    assert "Geometry Domain" in physics["dependency_relationships"]
    assert "object_motion_reasoning" in physics["shared_capabilities"]
    assert "collision_simulation" in physics["private_capabilities"]
    assert gravity["composition_status"] == "READY"
    assert report["dependency_graph"]["Physics Domain"] == [
        "Spatial Domain",
        "Geometry Domain",
    ]


def test_cognitive_domain_interaction_marks_missing_composition_capabilities():
    report = CognitiveDomainInteractionRegistry().build({
        "domain_registry": [
            {
                "domain_name": "Pattern Completion Domain",
                "semantic_capability_evolution": ["pattern_inference"],
                "required_domains": ["Transformation Domain"],
            },
            {
                "domain_name": "Transformation Domain",
                "semantic_capability_evolution": ["transformation_detection"],
            },
        ],
    })

    pattern = {
        row["composition_name"]: row
        for row in report["operational_capability_compositions"]
    }["Pattern Completion Capability"]

    assert pattern["composition_status"] == "BLOCKED"
    assert "Color Domain" in pattern["missing_domains"]
    assert "color_mapping" in pattern["missing_capabilities"]
    assert report["validation"]["invalid_capability_composition"]


def test_cognitive_domain_interaction_exposes_optional_collaboration():
    report = CognitiveDomainInteractionRegistry().build({
        "domain_registry": [
            {
                "domain_name": "Topology Domain",
                "semantic_capability_evolution": ["bridge_creation"],
                "required_domains": ["Spatial Domain"],
                "optional_domains": ["Geometry Domain"],
            },
            {
                "domain_name": "Spatial Domain",
                "semantic_capability_evolution": ["relative_position"],
            },
            {
                "domain_name": "Geometry Domain",
                "semantic_capability_evolution": ["object_shape"],
            },
        ],
    })

    optional = [
        row for row in report["domain_interactions"]
        if row["interaction_type"] == "OPTIONAL_SUPPORT"
    ][0]

    assert optional["source_domain"] == "Topology Domain"
    assert optional["target_domain"] == "Geometry Domain"
    assert optional["interaction_status"] == "READY"
