from runtime.knowledge import CognitiveDomainEcosystemRegistry


def _lifecycle_report():
    return {
        "domain_registry": [
            {
                "domain_name": "Physics Domain",
                "maturity_level": "DEVELOPING",
                "semantic_capability_evolution": ["gravity", "falling"],
                "mental_model_evolution": ["Gravity Simulation"],
                "program_blueprint_evolution": ["physics_program"],
                "execution_capability_evolution": [],
                "candidate_capability_evolution": [],
                "operational_capability_evolution": [],
                "semantic_readiness": "READY",
                "mental_model_readiness": "READY",
                "program_readiness": "READY",
                "execution_readiness": "NOT_READY",
                "candidate_readiness": "NOT_READY",
                "operational_readiness": "NOT_READY",
                "required_domains": ["Spatial Domain", "Geometry Domain"],
                "missing_capabilities": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                ],
            },
            {
                "domain_name": "Spatial Domain",
                "maturity_level": "OPERATIONAL",
                "semantic_capability_evolution": ["relative_position"],
                "mental_model_evolution": ["Spatial Reasoning"],
                "program_blueprint_evolution": ["spatial_program"],
                "execution_capability_evolution": ["spatial_execution_package"],
                "candidate_capability_evolution": ["spatial_candidate_support"],
                "operational_capability_evolution": ["relative_position_reasoning"],
                "semantic_readiness": "READY",
                "mental_model_readiness": "READY",
                "program_readiness": "READY",
                "execution_readiness": "READY",
                "candidate_readiness": "READY",
                "operational_readiness": "READY",
                "missing_capabilities": [],
            },
            {
                "domain_name": "Geometry Domain",
                "maturity_level": "FOUNDATIONAL",
                "semantic_capability_evolution": ["object_shape"],
                "mental_model_evolution": [],
                "program_blueprint_evolution": [],
                "execution_capability_evolution": [],
                "candidate_capability_evolution": [],
                "operational_capability_evolution": [],
                "semantic_readiness": "READY",
                "program_readiness": "NOT_READY",
                "execution_readiness": "NOT_READY",
                "candidate_readiness": "NOT_READY",
                "operational_readiness": "NOT_READY",
                "missing_capabilities": ["geometry_program_missing"],
            },
        ],
    }


def _interaction_report():
    return {
        "dependency_graph": {
            "Physics Domain": ["Spatial Domain", "Geometry Domain"],
        },
        "domain_interaction_reports": [
            {
                "domain_name": "Physics Domain",
                "collaborating_domains": ["Spatial Domain", "Geometry Domain"],
            },
            {
                "domain_name": "Spatial Domain",
                "collaborating_domains": ["Physics Domain"],
            },
        ],
        "operational_capability_compositions": [
            {
                "composition_name": "Object Falling Simulation",
                "participating_domains": [
                    "Physics Domain",
                    "Spatial Domain",
                    "Geometry Domain",
                ],
            },
        ],
    }


def _governance_report():
    return {
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
        "missing_governance_requirements": ["ecosystem_candidate_governance"],
    }


def test_cognitive_domain_ecosystem_aggregates_global_coverage():
    report = CognitiveDomainEcosystemRegistry().build(
        cognitive_domain_lifecycle_report=_lifecycle_report(),
        cognitive_domain_interaction_report=_interaction_report(),
        cognitive_domain_governance_report=_governance_report(),
    )

    ecosystem = report["ecosystem"]

    assert report["COGNITIVE_DOMAIN_ECOSYSTEM_REPORT"] is True
    assert report["global_cognitive_coverage"]["domains"] == 3
    assert report["global_cognitive_coverage"]["semantic_concepts"] == 4
    assert report["global_cognitive_coverage"]["mental_models"] == 2
    assert ecosystem["dependency_graph"]["Physics Domain"] == [
        "Spatial Domain",
        "Geometry Domain",
    ]
    assert "Temporal Domain" in ecosystem["missing_domains"]
    assert "gravity_execution_package" in report["missing_ecosystem_capabilities"]
    assert "ecosystem_candidate_governance" in report["missing_ecosystem_capabilities"]


def test_cognitive_domain_ecosystem_detects_bottlenecks_and_imbalances():
    lifecycle = _lifecycle_report()
    lifecycle["domain_registry"][0]["semantic_capability_evolution"].extend(
        ["collision", "support", "rest_state", "downward_motion"]
    )

    report = CognitiveDomainEcosystemRegistry().build(
        cognitive_domain_lifecycle_report=lifecycle,
        cognitive_domain_interaction_report=_interaction_report(),
        cognitive_domain_governance_report=_governance_report(),
    )

    bottleneck_types = {
        row["bottleneck_type"]
        for row in report["cognitive_bottlenecks"]
    }
    imbalance_types = {
        row["imbalance_type"]
        for row in report["cognitive_imbalances"]
    }

    assert "execution_package_coverage" in bottleneck_types
    assert "candidate_proposal_support" in bottleneck_types
    assert "program_to_execution_gap" in bottleneck_types
    assert "capability_concentration" in imbalance_types


def test_cognitive_domain_ecosystem_marks_operational_domains_as_covered():
    report = CognitiveDomainEcosystemRegistry().build(
        cognitive_domain_lifecycle_report=_lifecycle_report(),
        cognitive_domain_interaction_report=_interaction_report(),
        cognitive_domain_governance_report=_governance_report(),
    )

    ecosystem = report["ecosystem"]

    assert "Spatial Domain" in ecosystem["covered_domains"]
    assert "Physics Domain" in ecosystem["partially_covered_domains"]
    assert report["ecosystem_maturity"] in {
        "FOUNDATIONAL",
        "DEVELOPING",
        "PARTIALLY_OPERATIONAL",
        "OPERATIONAL",
        "ADVANCED",
        "FULLY_OPERATIONAL",
    }
