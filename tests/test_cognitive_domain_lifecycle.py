from runtime.knowledge import CognitiveDomainLifecycleRegistry


def test_cognitive_domain_lifecycle_tracks_physics_program_defined_stage():
    report = CognitiveDomainLifecycleRegistry().build({
        "domain_intelligence": [
            {
                "domain_id": "domain:spatial",
                "domain_name": "Spatial Domain",
                "semantic_capabilities": ["relative_position"],
                "mental_models": ["Spatial Reasoning"],
            },
            {
                "domain_id": "domain:geometry",
                "domain_name": "Geometry Domain",
                "semantic_capabilities": ["shape_geometry"],
                "mental_models": ["Geometry Reasoning"],
            },
            {
                "domain_id": "domain:physics",
                "domain_name": "Physics Domain",
                "semantic_capabilities": ["gravity", "falling", "collision"],
                "mental_models": ["Gravity Simulation"],
                "program_blueprints": ["physics_program"],
                "execution_packages": [],
                "operational_capabilities": [],
                "missing_capabilities": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                ],
                "required_domains": ["Spatial Domain", "Geometry Domain"],
            },
        ],
    })

    physics = {
        row["domain_name"]: row
        for row in report["domain_registry"]
    }["Physics Domain"]

    assert physics["lifecycle_stage"] == "PROGRAM_DEFINED"
    assert physics["maturity_level"] == "DEVELOPING"
    assert physics["semantic_readiness"] == "READY"
    assert physics["mental_model_readiness"] == "READY"
    assert physics["program_readiness"] == "READY"
    assert physics["execution_readiness"] == "NOT_READY"
    assert physics["candidate_readiness"] == "NOT_READY"
    assert physics["operational_readiness"] == "NOT_READY"
    assert physics["required_domains"] == ["Spatial Domain", "Geometry Domain"]
    assert physics["inherited_capabilities"]["Spatial Domain"] == ["relative_position"]
    assert physics["lifecycle_failures"][0]["failed_lifecycle_stage"] == "EXECUTION_DEFINED"
    assert physics["lifecycle_failures"][0]["reason"] == "physics_execution_package_missing"
    assert report["total_domains"] == 3
    assert report["foundational_domains"] == 0


def test_cognitive_domain_lifecycle_marks_independent_domain_fully_operational():
    report = CognitiveDomainLifecycleRegistry().build({
        "domain_intelligence": [
            {
                "domain_id": "domain:color",
                "domain_name": "Color Domain",
                "semantic_capabilities": ["color_mapping"],
                "mental_models": ["Color Mapping Mental Model"],
                "program_blueprints": ["color_mapping_program"],
                "execution_packages": ["color_execution_package"],
                "operational_capabilities": ["color_execution"],
                "missing_capabilities": [],
                "required_domains": [],
            },
        ],
    })

    color = report["domain_registry"][0]

    assert color["lifecycle_stage"] == "FULLY_OPERATIONAL"
    assert color["maturity_level"] == "FULLY_OPERATIONAL"
    assert color["candidate_readiness"] == "READY"
    assert color["operational_readiness"] == "READY"
    assert color["lifecycle_failures"] == []
    assert report["domain_readiness_distribution"] == {"FULLY_OPERATIONAL": 1}


def test_cognitive_domain_lifecycle_exposes_missing_program_failure():
    report = CognitiveDomainLifecycleRegistry().build({
        "domain_intelligence": [
            {
                "domain_id": "domain:growth",
                "domain_name": "Growth Domain",
                "semantic_capabilities": ["growth", "propagation"],
                "mental_models": ["Growth Mental Model"],
                "program_blueprints": [],
                "execution_packages": [],
                "operational_capabilities": [],
                "missing_capabilities": ["growth_program_missing"],
            },
        ],
    })

    growth = report["domain_registry"][0]

    assert growth["lifecycle_stage"] == "MENTAL_MODEL_DEFINED"
    assert growth["maturity_level"] == "EARLY_DEVELOPMENT"
    assert growth["program_readiness"] == "NOT_READY"
    assert growth["lifecycle_failures"][0]["failed_lifecycle_stage"] == "PROGRAM_DEFINED"
    assert growth["lifecycle_failures"][0]["missing_programs"] == ["program_blueprint"]
