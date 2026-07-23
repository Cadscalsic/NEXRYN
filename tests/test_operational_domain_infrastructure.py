from runtime.capability_intelligence.operational_domain_infrastructure import (
    OperationalDomainInfrastructure,
)


def test_operational_domain_infrastructure_identifies_domain_gaps_and_roadmap():
    report = OperationalDomainInfrastructure().analyze(
        domain_architecture={
            "domain_count": 3,
            "domain_rows": [
                {
                    "domain_name": "Identity Cognitive Domain",
                    "semantic_concept_count": 5,
                    "execution_package_count": 5,
                    "program_blueprint_count": 5,
                    "candidate_count": 0,
                    "arena_candidate_count": 0,
                    "validated_program_count": 0,
                    "domain_operational_readiness": 0.5,
                    "operationalization_gap": "candidate_generation_gap",
                },
                {
                    "domain_name": "Topology Cognitive Domain",
                    "semantic_concept_count": 2,
                    "execution_package_count": 2,
                    "program_blueprint_count": 2,
                    "candidate_count": 2,
                    "arena_candidate_count": 0,
                    "validated_program_count": 0,
                    "domain_operational_readiness": 0.6,
                    "operationalization_gap": "arena_entry_gap",
                },
                {
                    "domain_name": "Color Cognitive Domain",
                    "semantic_concept_count": 2,
                    "execution_package_count": 2,
                    "program_blueprint_count": 2,
                    "candidate_count": 2,
                    "arena_candidate_count": 2,
                    "validated_program_count": 1,
                    "domain_operational_readiness": 0.8,
                    "operationalization_gap": "none",
                },
            ],
        },
        operational_distribution={"Color": 2},
        survival_rows=[
            {
                "domain": "Color",
                "lifecycle_state": "OPERATIONAL_CITIZEN",
            }
        ],
        target_domain_count=5,
    )

    gaps = {
        row["domain_label"]: row["domain_operationalization_bottleneck"]
        for row in report["domain_diagnostics"]
    }

    assert report["operational_domain_population"] == 1
    assert report["operational_domain_coverage"] == 0.2
    assert report["domain_population_balance"] == "IMBALANCED"
    assert gaps["Identity"] == "candidate_generation_gap"
    assert gaps["Topology"] == "arena_entry_gap"
    assert report["domain_expansion_roadmap"][0]["domain_label"] == "Identity"
    assert report["domain_operational_targets"][0]["target"]
    assert report["domain_collaboration_rows"]
