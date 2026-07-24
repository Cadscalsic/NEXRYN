from runtime.training.elite_curriculum_validator import (
    validate_elite_curriculum,
    validate_elite_validation_academy,
)


def test_elite_curriculum_validator_reports_v1_training_value():
    report = validate_elite_curriculum()

    assert report["curriculum"] == "nexryn_elite_training_curriculum_v1"
    assert report["elite_task_count"] == 20
    assert report["elite_curriculum_health"] >= 0.9
    assert report["elite_task_difficulty"] == "very_high"
    assert report["capability_graduation_coverage"] == 1.0
    assert report["domain_expansion_coverage"] == 1.0
    assert report["composite_capability_coverage"] == 1.0
    assert report["adaptive_reuse_coverage"] == 1.0
    assert report["operationalization_coverage"] == 1.0
    assert report["elite_task_utilization"] == 1.0
    assert report["tier_distribution"] == {
        "Tier 1": 5,
        "Tier 2": 5,
        "Tier 3": 5,
        "Tier 4": 5,
    }
    assert report["invalid_elite_tasks"] == []


def test_elite_validation_academy_reports_governed_validation_task_design():
    report = validate_elite_validation_academy()

    assert report["academy"] == "nexryn_elite_validation_academy_v1"
    assert report["academy_task_count"] == 30
    assert report["academy_health"] >= 0.95
    assert report["academy_readiness"] == "READY"
    assert report["group_distribution"] == {
        "Capability Graduation Tasks": 5,
        "Capability Validation Tasks": 10,
        "Composite Capability Validation Tasks": 5,
        "Cross Domain Validation Tasks": 5,
        "Trust Formation Tasks": 5,
    }
    assert report["invalid_validation_tasks"] == []
    assert "unambiguous_directional_translation_ground_truth" in (
        report["required_task_property_distribution"]
    )
    assert "paired_symbolic_object_replication_ground_truth" in (
        report["required_task_property_distribution"]
    )
    assert "Topology Preserving Translation" in (
        report["target_cluster_distribution"]
    )
