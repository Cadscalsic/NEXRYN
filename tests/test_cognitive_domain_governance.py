from runtime.knowledge import CognitiveDomainGovernanceRegistry


def test_cognitive_domain_governance_validates_canonical_ownership():
    report = CognitiveDomainGovernanceRegistry().build(
        cognitive_domain_lifecycle_report={
            "domain_registry": [
                {
                    "domain_name": "Physics Domain",
                    "lifecycle_stage": "PROGRAM_DEFINED",
                    "maturity_level": "DEVELOPING",
                    "semantic_capability_evolution": ["gravity", "falling"],
                    "operational_capability_evolution": [],
                    "required_domains": ["Spatial Domain", "Geometry Domain"],
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
        },
        cognitive_domain_interaction_report={
            "domain_interaction_reports": [
                {
                    "domain_name": "Physics Domain",
                    "shared_capabilities": ["object_motion_reasoning"],
                },
            ],
        },
    )

    physics = {
        row["domain_name"]: row
        for row in report["domain_governance"]
    }["Physics Domain"]

    assert physics["governance_status"] == "FULLY_GOVERNED"
    assert physics["semantic_coherence_score"] == 1.0
    assert physics["ownership_consistency_score"] == 1.0
    assert report["validation_success"] is True


def test_cognitive_domain_governance_detects_boundary_and_ownership_conflicts():
    report = CognitiveDomainGovernanceRegistry().build(
        cognitive_domain_lifecycle_report={
            "domain_registry": [
                {
                    "domain_name": "Transformation Domain",
                    "lifecycle_stage": "PROGRAM_DEFINED",
                    "maturity_level": "DEVELOPING",
                    "semantic_capability_evolution": ["rotation", "gravity"],
                    "required_domains": ["Geometry Domain"],
                },
                {
                    "domain_name": "Geometry Domain",
                    "semantic_capability_evolution": ["object_shape"],
                },
            ],
        },
        cognitive_domain_interaction_report={"domain_interaction_reports": []},
    )

    transformation = {
        row["domain_name"]: row
        for row in report["domain_governance"]
    }["Transformation Domain"]

    assert transformation["governance_status"] == "BOUNDARY_VIOLATION"
    assert transformation["boundary_violations"][0]["capability"] == "gravity"
    assert transformation["capability_conflicts"][0]["expected_owner"] == "Physics Domain"
    assert report["validation_success"] is False


def test_cognitive_domain_governance_records_capability_migration():
    report = CognitiveDomainGovernanceRegistry().build(
        cognitive_domain_lifecycle_report={
            "domain_registry": [
                {
                    "domain_name": "Growth Domain",
                    "semantic_capability_evolution": ["density_preservation"],
                },
            ],
        },
        cognitive_domain_interaction_report={"domain_interaction_reports": []},
    )

    growth = report["domain_governance"][0]

    assert growth["migration_history"][0]["capability"] == "density_preservation"
    assert growth["migration_history"][0]["previous_owner"] == "Transformation Domain"
    assert growth["migration_history"][0]["new_owner"] == "Growth Domain"
