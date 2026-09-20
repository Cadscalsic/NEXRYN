from runtime.knowledge import CognitiveDomainIntelligenceLayer


def test_cognitive_domain_intelligence_describes_topology_capabilities():
    report = CognitiveDomainIntelligenceLayer().analyze({
        "domains": [
            {
                "domain_id": "domain:spatial",
                "domain_name": "Spatial Domain",
                "semantic_families": ["Spatial"],
                "semantic_concepts": ["relative_position"],
                "mental_models": ["Spatial Reasoning"],
            },
            {
                "domain_id": "domain:identity",
                "domain_name": "Identity Domain",
                "semantic_families": ["Identity"],
                "semantic_concepts": ["object_identity_preservation"],
                "mental_models": ["Object Identity"],
            },
            {
                "domain_id": "domain:topology",
                "domain_name": "Topology Domain",
                "semantic_families": ["Topology"],
                "mental_models": ["Topology Reasoning"],
                "program_blueprints": ["topology_program"],
                "semantic_concepts": [
                    "bridge_creation",
                    "topology_change",
                    "component_connection",
                ],
                "execution_packages": ["topology_execution_package"],
                "operational_capabilities": ["topology_execution"],
                "missing_capabilities": ["topology_candidate_support"],
                "maturity_level": "PARTIALLY_OPERATIONAL",
            },
        ],
    })

    topology = {
        domain["domain_name"]: domain
        for domain in report["domain_intelligence"]
    }["Topology Domain"]

    assert report["validation_success"] is True
    assert topology["semantic_capabilities"] == [
        "bridge_creation",
        "topology_change",
        "component_connection",
    ]
    assert topology["operational_capabilities"] == ["topology_execution"]
    assert topology["required_domains"] == ["Spatial Domain", "Identity Domain"]
    assert topology["mental_model_count"] == 1
    assert topology["program_blueprint_count"] == 1
    assert topology["execution_package_count"] == 1
    assert topology["operational_capability_count"] == 1
    assert topology["readiness_state"] == "PARTIALLY_OPERATIONAL"


def test_cognitive_domain_intelligence_detects_domain_pollution():
    report = CognitiveDomainIntelligenceLayer().analyze({
        "domains": [
            {
                "domain_id": "domain:transformation",
                "domain_name": "Transformation Domain",
                "semantic_families": ["Transformation"],
                "mental_models": ["Object Transformation Mental Model"],
                "program_blueprints": ["transformation_program"],
                "semantic_concepts": ["rotation", "gravity"],
            },
            {
                "domain_id": "domain:geometry",
                "domain_name": "Geometry Domain",
                "semantic_families": ["Geometry"],
            },
        ],
    })

    transformation = {
        domain["domain_name"]: domain
        for domain in report["domain_intelligence"]
    }["Transformation Domain"]

    assert report["validation_success"] is False
    assert transformation["readiness_state"] == "NOT_READY"
    assert report["validation"]["domain_pollution"][0]["item"] == "gravity"
    assert report["validation"]["invalid_concept_assignments"][0]["reason"] == (
        "DOMAIN_BOUNDARY_VIOLATION"
    )


def test_cognitive_domain_intelligence_supports_independent_domains():
    report = CognitiveDomainIntelligenceLayer().analyze({
        "domains": [
            {
                "domain_id": "domain:color",
                "domain_name": "Color Domain",
                "semantic_families": ["Color"],
                "mental_models": ["Color Mapping Mental Model"],
                "program_blueprints": ["color_mapping_program"],
                "semantic_concepts": ["color_mapping"],
                "execution_packages": ["color_execution_package"],
                "operational_capabilities": ["color_execution"],
                "missing_capabilities": [],
                "maturity_level": "FULLY_OPERATIONAL",
            },
        ],
    })

    color = report["domain_intelligence"][0]

    assert color["required_domains"] == []
    assert color["independent_capabilities"] == ["color_mapping"]
    assert color["readiness_state"] == "FULLY_OPERATIONAL"
    assert report["readiness_distribution"] == {"FULLY_OPERATIONAL": 1}
