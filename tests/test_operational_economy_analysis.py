from runtime.capability_intelligence.operational_economy_analysis import (
    OperationalEconomyAnalysis,
)


def test_operational_economy_measures_attrition_and_crisis_state():
    report = OperationalEconomyAnalysis().analyze(
        generated_concepts=100,
        generated_programs=50,
        candidate_count=30,
        arena_candidate_count=10,
        compiled_programs=2,
        validated_programs=1,
        materialized_operational_capabilities=0,
        operational_citizen_count=1,
        expected_operational_capability_count=13,
        known_operational_capability_count=2,
        operational_experience_count=78,
        candidate_attrition_summary={
            "rejected_before_arena": 5,
            "rejection_reasons": {
                "compiler_support_missing": 3,
                "execution_package_missing": 2,
            },
        },
        capability_ecology_report={
            "composite_capability_candidates": [
                {
                    "composite_name": "Topology Preserving Translation",
                    "required_capabilities": [
                        "translate",
                        "preserve_topology",
                        "preserve_colors",
                    ],
                    "present_capabilities": [
                        "translate",
                        "preserve_topology",
                        "preserve_colors",
                    ],
                    "missing_capabilities": [],
                    "participating_domains": ["Spatial", "Topology", "Color"],
                    "composition_readiness": 1.0,
                }
            ],
        },
        capability_population_evolution_lag=0.8462,
        crystallization_candidate_count=0,
        high_value_knowledge_items=10,
        medium_value_knowledge_items=15,
        low_value_knowledge_items=5,
    )

    assert report["knowledge_attrition_lifecycle"][0]["from_stage"] == (
        "generated_concepts"
    )
    assert report["operational_economy_bottleneck"] == (
        "validated_programs->materialized_operational_capabilities"
    )
    assert report["candidate_attrition_cost"] == 5
    assert report["capability_economy_crisis_state"] == "CAPABILITY_ECONOMY_CRISIS"
    assert report["operational_capability_clusters"][0]["cluster_state"] == (
        "OPERATIONAL_CLUSTER_READY"
    )
    assert report["operational_cluster_readiness"] == 1.0
    assert report["knowledge_to_citizen_efficiency"] == 0.01


def test_operational_economy_keeps_clusters_as_diagnostics_only():
    report = OperationalEconomyAnalysis().analyze(
        generated_concepts=10,
        generated_programs=8,
        candidate_count=6,
        arena_candidate_count=5,
        compiled_programs=4,
        validated_programs=3,
        materialized_operational_capabilities=2,
        operational_citizen_count=2,
        capability_ecology_report={
            "composite_capability_candidates": [
                {
                    "composite_name": "Identity Preserving Transformation",
                    "required_capabilities": ["preserve_grid", "translate"],
                    "present_capabilities": ["preserve_grid"],
                    "missing_capabilities": ["translate"],
                    "composition_readiness": 0.5,
                }
            ],
        },
    )

    assert report["operational_cluster_count"] == 1
    assert report["operational_capability_clusters"][0]["cluster_state"] == (
        "PARTIAL_OPERATIONAL_CLUSTER"
    )
    assert "capability_type" not in report["operational_capability_clusters"][0]
    assert report["knowledge_crystallization_efficiency"] is None
    assert report["operational_economy_health"] <= 1.0
