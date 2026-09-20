from runtime.knowledge import CognitiveDomainConstitutionRegistry


def test_cognitive_domain_constitution_reports_compliant_ecosystem():
    report = CognitiveDomainConstitutionRegistry().build(
        cognitive_domain_lifecycle_report={
            "domain_registry": [
                {
                    "domain_name": "Physics Domain",
                    "lifecycle_stage": "PROGRAM_DEFINED",
                    "maturity_level": "DEVELOPING",
                    "semantic_capability_evolution": ["gravity", "falling"],
                    "mental_model_evolution": ["Gravity Simulation"],
                    "program_blueprint_evolution": ["physics_program"],
                    "required_domains": ["Spatial Domain", "Geometry Domain"],
                },
                {
                    "domain_name": "Spatial Domain",
                    "lifecycle_stage": "OPERATIONAL",
                    "maturity_level": "OPERATIONAL",
                    "semantic_capability_evolution": ["relative_position"],
                    "mental_model_evolution": ["Spatial Reasoning"],
                    "program_blueprint_evolution": ["spatial_program"],
                    "operational_capability_evolution": ["relative_position_reasoning"],
                },
            ],
        },
        cognitive_domain_interaction_report={
            "domain_interaction_reports": [
                {
                    "domain_name": "Physics Domain",
                    "collaborating_domains": ["Spatial Domain", "Geometry Domain"],
                    "shared_capabilities": ["object_motion_reasoning"],
                },
            ],
        },
        cognitive_domain_governance_report={
            "domain_governance": [
                {
                    "domain_name": "Physics Domain",
                    "semantic_coherence_score": 1.0,
                    "governance_integrity_score": 1.0,
                },
                {
                    "domain_name": "Spatial Domain",
                    "semantic_coherence_score": 1.0,
                    "governance_integrity_score": 1.0,
                },
            ],
        },
        cognitive_domain_ecosystem_report={
            "ecosystem": {"architectural_coherence_score": 1.0},
            "ecosystem_health_metrics": {"architectural_coherence_score": 1.0},
        },
    )

    assert report["COGNITIVE_DOMAIN_CONSTITUTION_REPORT"] is True
    assert report["constitutional_violations"] == []
    assert report["ownership_compliance"] is True
    assert report["governance_compliance"] is True
    assert report["lifecycle_compliance"] is True
    assert report["constitutional_status"] in {
        "CONSTITUTIONALLY_COMPLIANT",
        "FULLY_CONSTITUTIONAL",
    }


def test_cognitive_domain_constitution_detects_boundary_and_ownership_violations():
    report = CognitiveDomainConstitutionRegistry().build(
        cognitive_domain_lifecycle_report={
            "domain_registry": [
                {
                    "domain_name": "Transformation Domain",
                    "lifecycle_stage": "PROGRAM_DEFINED",
                    "maturity_level": "DEVELOPING",
                    "semantic_capability_evolution": ["rotation", "gravity"],
                    "mental_model_evolution": ["Transformation Reasoning"],
                    "program_blueprint_evolution": ["transformation_program"],
                },
                {
                    "domain_name": "Physics Domain",
                    "lifecycle_stage": "PROGRAM_DEFINED",
                    "maturity_level": "DEVELOPING",
                    "semantic_capability_evolution": ["gravity"],
                    "mental_model_evolution": ["Gravity Simulation"],
                    "program_blueprint_evolution": ["physics_program"],
                },
            ],
        },
        cognitive_domain_interaction_report={"domain_interaction_reports": []},
        cognitive_domain_governance_report={
            "domain_governance": [
                {
                    "domain_name": "Transformation Domain",
                    "capability_conflicts": [
                        {
                            "capability": "gravity",
                            "expected_owner": "Physics Domain",
                            "actual_owner": "Transformation Domain",
                            "reason": "CANONICAL_OWNER_MISMATCH",
                        },
                    ],
                    "boundary_violations": [
                        {
                            "capability": "gravity",
                            "reason": "FORBIDDEN_CAPABILITY_TOKEN",
                        },
                    ],
                    "semantic_coherence_score": 0.5,
                    "governance_integrity_score": 0.5,
                },
                {
                    "domain_name": "Physics Domain",
                    "semantic_coherence_score": 1.0,
                    "governance_integrity_score": 1.0,
                },
            ],
        },
        cognitive_domain_ecosystem_report={
            "ecosystem": {"architectural_coherence_score": 0.8},
            "ecosystem_health_metrics": {"architectural_coherence_score": 0.8},
        },
    )

    violation_types = {
        violation["violation_type"]
        for violation in report["constitutional_violations"]
    }

    assert "SEMANTIC_BOUNDARY_BREACH" in violation_types
    assert "OWNERSHIP_CONFLICT" in violation_types
    assert report["ownership_compliance"] is False
    assert report["constitutional_status"] != "FULLY_CONSTITUTIONAL"


def test_cognitive_domain_constitution_exposes_domain_rights_and_responsibilities():
    report = CognitiveDomainConstitutionRegistry().build(
        cognitive_domain_lifecycle_report={
            "domain_registry": [
                {
                    "domain_name": "Color Domain",
                    "lifecycle_stage": "PROGRAM_DEFINED",
                    "maturity_level": "DEVELOPING",
                    "semantic_capability_evolution": ["color_mapping"],
                    "mental_model_evolution": ["Color Mapping"],
                    "program_blueprint_evolution": ["color_mapping_program"],
                },
            ],
        },
        cognitive_domain_interaction_report={"domain_interaction_reports": []},
        cognitive_domain_governance_report={
            "domain_governance": [
                {
                    "domain_name": "Color Domain",
                    "semantic_coherence_score": 1.0,
                    "governance_integrity_score": 1.0,
                },
            ],
        },
        cognitive_domain_ecosystem_report={
            "ecosystem": {"architectural_coherence_score": 1.0},
            "ecosystem_health_metrics": {"architectural_coherence_score": 1.0},
        },
    )

    health = report["domain_constitutional_health"][0]

    assert "semantic_boundary_protection" in health["rights"]
    assert "expose_governance_states" in health["responsibilities"]
    assert health["constitutional_status"] == "VALID"
