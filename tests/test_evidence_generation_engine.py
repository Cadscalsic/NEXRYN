import json

from runtime.evidence_generation.evidence_generation_engine import (
    EvidenceGenerationEngine,
)


def _cross_source_plan():
    return {
        "evidence_acquisition_state": "EVIDENCE_ACQUISITION_PLAN_READY",
        "evidence_acquisition_required_evidence": (
            "cross_source_consensus_evidence"
        ),
        "evidence_acquisition_required_category": "CROSS_SOURCE_CONSENSUS",
        "evidence_acquisition_validation_task": (
            "select_cross_source_tie_break_validation_task"
        ),
        "evidence_acquisition_tie_break_strategy": "cross_source_consensus",
        "evidence_acquisition_target_operation": "replace_color",
        "evidence_acquisition_target_candidate": "semantic_program:replace_color",
    }


def test_evidence_generation_engine_generates_governed_validation_opportunity(
    tmp_path,
):
    engine = EvidenceGenerationEngine(tmp_path / "generated_curriculum")

    report = engine.generate_for_plan(
        _cross_source_plan(),
        existing_tasks_found=False,
    )

    assert report["generation_required"] is True
    assert report["generation_status"] == "GENERATED_VALIDATION_OPPORTUNITY"
    assert report["generated_tasks"] == 1
    assert report["training_assistant_queue_updated"] is True
    assert report["future_execution_ready"] is True
    assert report["evidence_produced"] is False
    assert report["truth_authority"] == "NONE"
    assert report["trust_authority"] == "NONE"
    assert report["graduation_authority"] == "NONE"

    task_path = tmp_path / "generated_curriculum" / (
        report["generated_task_files"][0].split("\\")[-1].split("/")[-1]
    )
    task = json.loads(task_path.read_text(encoding="utf-8"))
    metadata = task["nexryn_metadata"]
    assert metadata["generated_by"] == "EvidenceGenerationEngine"
    assert metadata["evidence_produced"] is False
    assert metadata["consumed_by_training_assistant"] is False
    assert metadata["governance_state"] == (
        "POTENTIAL_VALIDATION_OPPORTUNITY_ONLY"
    )
    assert metadata["truth_authority"] == "NONE"
    assert metadata["trust_authority"] == "NONE"
    assert metadata["graduation_authority"] == "NONE"
    assert "cross_source_consensus_evidence" in metadata["required_evidence"]
    assert (
        "select_cross_source_tie_break_validation_task"
        in metadata["task_properties"]
    )


def test_evidence_generation_engine_does_not_generate_when_existing_task_found(
    tmp_path,
):
    engine = EvidenceGenerationEngine(tmp_path / "generated_curriculum")

    report = engine.generate_for_plan(
        _cross_source_plan(),
        existing_tasks_found=True,
    )

    assert report["generation_required"] is False
    assert report["existing_tasks_found"] is True
    assert report["generated_tasks"] == 0
    assert report["training_assistant_queue_updated"] is False
    assert not (tmp_path / "generated_curriculum").exists()
