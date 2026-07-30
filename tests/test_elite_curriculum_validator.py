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
    assert report["academy_task_count"] == 50
    assert report["academy_health"] >= 0.95
    assert report["academy_readiness"] == "READY"
    assert report["group_distribution"] == {
        "Advanced Multi-Concept Validation Tasks": 20,
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
    assert "localized_color_remap_cross_source_consensus" in (
        report["required_task_property_distribution"]
    )


def test_elite_validation_academy_expands_advanced_evidence_diversity():
    import json
    from pathlib import Path

    payload = json.loads(
        Path("data/curriculum/elite_validation_academy_v1.json").read_text(
            encoding="utf-8",
        )
    )
    tasks = payload["tasks"]
    advanced = [
        task for task in tasks
        if task["elite_group"] == "Advanced Multi-Concept Validation Tasks"
    ]
    evidence_categories = {
        task["required_validation_evidence"] for task in advanced
    } | {
        category
        for task in advanced
        for category in task["secondary_evidence_categories"]
    }

    assert len(advanced) == 20
    assert len({task["task_name"] for task in advanced}) == 20
    assert all(len(task["cross_domain_requirement"]) >= 3 for task in advanced)
    assert all(task["truth_authority"] == "NONE" for task in advanced)
    assert all(task["trust_authority"] == "NONE" for task in advanced)
    assert all(task["graduation_authority"] == "NONE" for task in advanced)
    assert {
        "cross_source_consensus_evidence",
        "object_grounding_evidence",
        "topology_preservation_evidence",
        "bridge_creation_evidence",
        "spatial_reasoning_evidence",
        "transformation_sequence_evidence",
        "identity_preservation_evidence",
        "dependency_reasoning_evidence",
        "causal_alignment_evidence",
        "semantic_consistency_evidence",
        "execution_generalization_evidence",
        "operational_reuse_evidence",
        "cross_domain_reasoning_evidence",
        "compositional_reasoning_evidence",
        "contextual_validation_evidence",
        "hierarchical_reasoning_evidence",
        "planning_evidence",
        "invariant_preservation_evidence",
        "capability_collaboration_evidence",
        "validation_stability_evidence",
    }.issubset(evidence_categories)
