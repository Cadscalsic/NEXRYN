import json

from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
)


def _write_curriculum(path, tasks):
    path.write_text(
        json.dumps({"academy": "test", "tasks": tasks}, indent=2),
        encoding="utf-8",
    )


def _plan(**overrides):
    plan = {
        "plan_id": "plan-cross-source",
        "required_evidence_category": "CROSS_SOURCE_CONSENSUS",
        "required_evidence": "cross_source_consensus_evidence",
        "required_validation_task": "select_cross_source_tie_break_validation_task",
        "tie_break_strategy": "cross_source_consensus",
        "target_operation": "replace_color",
    }
    plan.update(overrides)
    return plan


def test_registry_searches_multiple_enabled_curricula_and_ranks_metadata(tmp_path):
    weak = tmp_path / "weak.json"
    strong = tmp_path / "strong.json"
    disabled = tmp_path / "disabled.json"
    _write_curriculum(weak, [
        {
            "task_id": "weak-consensus",
            "task_name": "Weak Consensus",
            "target_capability": "replace_color",
            "target_domain": "Color",
            "required_validation_evidence": "cross_source_consensus_evidence",
            "required_task_property": "generic_consensus",
        }
    ])
    _write_curriculum(strong, [
        {
            "task_id": "strong-consensus",
            "task_name": "Strong Consensus",
            "target_capability": "replace_color",
            "target_domain": "Color",
            "primary_evidence_category": "CROSS_SOURCE_CONSENSUS",
            "secondary_evidence_categories": [
                "cross_source_consensus_evidence",
            ],
            "required_validation_evidence": "cross_source_consensus_evidence",
            "required_grounding": [
                "cross_source_consensus",
                "select_cross_source_tie_break_validation_task",
            ],
            "expected_validation_contract": (
                "select_cross_source_tie_break_validation_task"
            ),
            "cross_domain_participation": ["Color", "Identity"],
            "operational_reuse_potential": "high",
        }
    ])
    _write_curriculum(disabled, [
        {
            "task_id": "disabled-best",
            "primary_evidence_category": "CROSS_SOURCE_CONSENSUS",
            "required_validation_evidence": "cross_source_consensus_evidence",
            "target_capability": "replace_color",
        }
    ])
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="weak",
        display_name="Weak Academy",
        path=weak,
        priority=10,
    )
    registry.register_curriculum(
        identifier="strong",
        display_name="Strong Academy",
        path=strong,
        priority=20,
    )
    registry.register_curriculum(
        identifier="disabled",
        display_name="Disabled Academy",
        path=disabled,
        enabled=False,
        priority=100,
    )

    report = registry.search(_plan())

    assert report["registered_curricula"] == 3
    assert report["enabled_curricula"] == 2
    assert report["disabled_curricula"] == 1
    assert report["curricula_searched"] == 2
    assert report["total_validation_tasks"] == 2
    assert report["matching_tasks"] == 2
    assert report["best_matching_task"] == "strong-consensus"
    assert report["best_matching_curriculum"] == "Strong Academy"
    assert report["selection_state"] == "WAITING_EXECUTION"
    assert report["waiting_execution"] is True
    assert report["generation_invoked"] is False
    assert report["truth_authority"] == "NONE"


def test_registry_reports_no_match_without_invoking_generation(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum, [
        {
            "task_id": "identity-only",
            "target_capability": "preserve_grid",
            "target_domain": "Identity",
            "required_validation_evidence": "identity_preservation_evidence",
        }
    ])
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="identity",
        display_name="Identity Academy",
        path=curriculum,
    )

    report = registry.search(_plan(
        required_evidence="bridge_creation_evidence",
        required_evidence_category="BRIDGE_CREATION",
        target_operation="bridge_creation",
    ))

    assert report["matching_tasks"] == 0
    assert report["selection_state"] == "NO_MATCH"
    assert report["generation_eligible"] is True
    assert report["generation_invoked"] is False
    assert report["waiting_generator"] is True
