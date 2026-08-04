import json
from pathlib import Path

from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
)
from runtime.validation.validation_evidence_evaluator import (
    ValidationEvidenceEvaluator,
)
from runtime.validation.validation_task_execution_pipeline import (
    ValidationTaskExecutionPipeline,
)
from runtime.validation.validation_task_scheduler import ValidationTaskScheduler


def _plan(**overrides):
    plan = {
        "source_run_id": "run_20260730_074151",
        "source_task_id": "task-localized-remap",
        "source_candidate_id": "semantic_program:replace_color",
        "source_operation": "replace_color",
        "evidence_acquisition_state": "EVIDENCE_ACQUISITION_PLAN_READY",
        "evidence_acquisition_trigger": (
            "TIE_CONFIRMED_AFTER_ACCEPTED_SANDBOX_PROBE"
        ),
        "required_evidence_category": "CROSS_SOURCE_CONSENSUS",
        "required_evidence": "cross_source_consensus_evidence",
        "required_validation_task": (
            "select_cross_source_tie_break_validation_task"
        ),
        "tie_break_strategy": "cross_source_consensus",
        "expected_tie_break_impact": "HIGH",
        "target_candidate": "semantic_program:replace_color",
        "target_operation": "replace_color",
        "governed_reentry_action": (
            "reenter_arena_after_required_evidence_without_truth_grant"
        ),
    }
    plan.update(overrides)
    return plan


def _consumption_report(plan_id, **overrides):
    report = {
        "current_plan_id": plan_id,
        "selection_state": "WAITING_EXECUTION",
        "consumption_state": "MATCHING_COMPLETED",
        "selected_validation_task": "elite_validation_task_31",
        "best_matching_curriculum": "Elite Validation Academy",
        "matching_score": 118.0,
        "matching_explanation": "primary_required_evidence_match",
        "current_required_evidence": "cross_source_consensus_evidence",
        "current_target_operation": "replace_color",
        "current_tie_break_strategy": "cross_source_consensus",
        "selected_validation_task_metadata": {
            "curriculum_id": "elite_validation_academy",
        },
    }
    report.update(overrides)
    return report


def _expected_output():
    return {
        "task_id": "elite_validation_task_31",
        "execution_scope": "SCHEDULED_VALIDATION_TASK_ONLY",
        "reference_visible_to_runner": False,
    }


def _write_curriculum(
    path: Path,
    *,
    comparator_id="manifest_observation_comparison",
    exact_required=True,
    expected=None,
    include_evaluation_contract=True,
):
    task = {
        "task_id": "elite_validation_task_31",
        "task_name": "Cross Source Consensus",
        "target_capability": "replace_color",
        "target_domain": "Color",
        "primary_evidence_category": "CROSS_SOURCE_CONSENSUS",
        "secondary_evidence_categories": [
            "cross_source_consensus_evidence"
        ],
        "required_validation_evidence": (
            "cross_source_consensus_evidence"
        ),
        "required_grounding": [
            "cross_source_consensus",
            "select_cross_source_tie_break_validation_task",
        ],
        "expected_validation_contract": (
            "select_cross_source_tie_break_validation_task"
        ),
        "validation_objective": (
            "observe cross-source consensus without evaluator target"
        ),
        "expected_target_output": expected
        if expected is not None else _expected_output(),
        "enabled": True,
    }
    if include_evaluation_contract:
        task["evaluation_contract"] = {
            "comparator_id": comparator_id,
            "comparator_version": "1.0",
            "minimum_case_coverage": 1.0,
            "exact_match_required": exact_required,
        }
    path.write_text(
        json.dumps({"tasks": [task]}),
        encoding="utf-8",
    )


def _registry(curriculum_path):
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="elite_validation_academy",
        display_name="Elite Validation Academy",
        path=curriculum_path,
        enabled=True,
    )
    return registry


def _captured_result(tmp_path, registry):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan())
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )
    schedule = ValidationTaskScheduler(tmp_path, registry).schedule_plan(
        persisted["evidence_plan_id"]
    )
    raw = ValidationTaskExecutionPipeline(tmp_path, registry).execute_schedule(
        schedule["schedule_id"]
    )
    return persisted, schedule, raw


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_raw_result_captured_evaluates_to_accepted_without_arena_authority(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, raw = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evaluation_admission_state"] == (
        "ADMITTED_TO_VALIDATION_EVIDENCE_EVALUATION"
    )
    assert report["evaluation_contract_id"].startswith(
        "validation_evidence_evaluation_contract_"
    )
    assert report["sealed_reference_resolved"] is True
    assert report["target_reference_forwarded_to_solver"] is False
    assert report["sealed_reference_opened_by_evaluator"] is True
    assert report["sealed_reference_forwarded_to_solver"] is False
    assert report["comparison_state"] == "COMPARISON_COMPLETED"
    assert report["comparable_result_available"] is True
    assert report["exact_match_rate"] == 1.0
    assert report["evidence_admissibility_state"] == "ADMISSIBLE"
    assert report["evidence_sufficiency_state"] == "SUFFICIENT"
    assert report["evidence_direction"] == "SUPPORTING"
    assert report["evidence_acceptance_state"] == "ACCEPTED"
    assert report["evidence_accepted"] is True
    assert report["accepted_evidence_artifact_created"] is True
    assert report["arena_evidence_admission_invoked"] is False
    assert report["arena_reentry_invoked"] is False
    assert report["candidate_score_changed"] is False
    assert report["candidate_ranking_changed"] is False
    assert report["tie_resolved"] is False
    assert report["winner_selected"] is False
    assert report["truth_authority"] == "NONE"
    assert report["trust_authority"] == "NONE"
    assert report["graduation_authority"] == "NONE"
    assert report["candidate_execution_authority"] == "NONE"
    assert report["next_consumer"] == "FUTURE_ARENA_EVIDENCE_ADMISSION_GATE"

    plan = _read_json(
        tmp_path / "pending" / f"{persisted['evidence_plan_id']}.json"
    )
    comparable = _read_json(
        tmp_path / "comparable_results" / f"{report['comparable_result_id']}.json"
    )
    decision = _read_json(
        tmp_path / "evidence_decisions" / f"{report['evidence_decision_id']}.json"
    )
    accepted = _read_json(
        tmp_path / "accepted_evidence" / f"{report['accepted_evidence_id']}.json"
    )
    assert plan["lifecycle_state"] == "EVIDENCE_ACCEPTED"
    assert plan["boot_recovery_route"] == (
        "EVIDENCE_ACCEPTED_TO_ARENA_EVIDENCE_ADMISSION_GATE"
    )
    assert comparable["raw_result_id"] == raw["raw_result_id"]
    assert "candidate_score_delta" not in comparable
    assert decision["evidence_acceptance_state"] == "ACCEPTED"
    assert accepted["evidence_state"] == "EVIDENCE_ACCEPTED"


def test_reprocessing_reuses_comparable_decision_and_accepted_evidence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, _ = _captured_result(tmp_path, registry)
    evaluator = ValidationEvidenceEvaluator(tmp_path, registry)

    first = evaluator.evaluate_plan(persisted["evidence_plan_id"])
    second = evaluator.evaluate_plan(persisted["evidence_plan_id"])

    assert second["comparable_result_creation_result"] == (
        "REUSED_EXISTING_COMPARABLE_RESULT"
    )
    assert second["evidence_decision_creation_result"] == (
        "REUSED_EXISTING_EVIDENCE_DECISION"
    )
    assert second["accepted_evidence_creation_result"] == (
        "REUSED_EXISTING_ACCEPTED_EVIDENCE"
    )
    assert first["comparable_result_id"] == second["comparable_result_id"]
    assert first["evidence_decision_id"] == second["evidence_decision_id"]
    assert len(list((tmp_path / "comparable_results").glob("*.json"))) == 1
    assert len(list((tmp_path / "evidence_decisions").glob("*.json"))) == 1
    assert len(list((tmp_path / "accepted_evidence").glob("*.json"))) == 1


def test_wrong_prediction_is_accepted_as_contradicting_evidence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum, exact_required=False, expected={"different": True})
    registry = _registry(curriculum)
    persisted, _, _ = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evidence_acceptance_state"] == "ACCEPTED"
    assert report["evidence_direction"] == "CONTRADICTING"
    assert report["evidence_accepted"] is True


def test_valid_but_incomplete_evidence_becomes_insufficient(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(
        curriculum,
        expected=[{"output": _expected_output()}, {"output": {"case": 2}}],
    )
    registry = _registry(curriculum)
    persisted, _, _ = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evidence_acceptance_state"] == "INSUFFICIENT"
    assert report["evidence_admissibility_state"] == "ADMISSIBLE"
    assert report["evidence_sufficiency_state"] == "INSUFFICIENT"
    assert report["accepted_evidence_artifact_created"] is False
    assert report["evidence_accepted"] is False
    assert list((tmp_path / "accepted_evidence").glob("*.json")) == []


def test_target_leakage_rejects_evidence_without_arena_penalty(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, raw = _captured_result(tmp_path, registry)
    raw_path = tmp_path / "raw_results" / f"{raw['raw_result_id']}.json"
    raw_record = _read_json(raw_path)
    raw_record["runner_trace_reference"]["target_reference_forwarded_to_solver"] = True
    raw_path.write_text(json.dumps(raw_record, indent=2), encoding="utf-8")

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evaluation_admission_state"] == "BLOCKED_TARGET_LEAKAGE_RISK"
    assert report["comparison_invoked"] is False
    assert report["evidence_accepted"] is False
    assert report["arena_reentry_invoked"] is False


def test_missing_contract_or_unsupported_comparator_blocks_evaluation(tmp_path):
    unsupported = tmp_path / "unsupported.json"
    _write_curriculum(unsupported, comparator_id="subjective_llm_judge")
    registry = _registry(unsupported)
    persisted, _, _ = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evaluation_admission_state"] == "BLOCKED_UNSUPPORTED_COMPARATOR"
    assert report["comparison_invoked"] is False
    assert report["evidence_accepted"] is False


def test_manifest_task_without_explicit_contract_derives_safe_contract(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum, include_evaluation_contract=False)
    registry = _registry(curriculum)
    persisted, _, _ = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evaluation_admission_state"] == (
        "ADMITTED_TO_VALIDATION_EVIDENCE_EVALUATION"
    )
    assert report["comparison_state"] == "COMPARISON_COMPLETED"
    assert report["evidence_acceptance_state"] == "ACCEPTED"
    comparable = _read_json(
        tmp_path / "comparable_results" / f"{report['comparable_result_id']}.json"
    )
    assert comparable["evaluation_contract_source"] == (
        "derived_from_expected_target_output"
    )


def test_boot_recovery_routes_terminal_evidence_to_future_consumer(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, _ = _captured_result(tmp_path, registry)
    ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    loaded = EvidenceAcquisitionPlanStore(tmp_path).load_pending_plans()

    assert loaded["pending_evidence_acquisition_plans"] == []
    assert len(loaded["terminal_evidence_plans"]) == 1
    assert loaded["boot_recovery_route"] == (
        "EVIDENCE_ACCEPTED_TO_ARENA_EVIDENCE_ADMISSION_GATE"
    )
    assert loaded["evidence_plan_lifecycle_state"] == "EVIDENCE_ACCEPTED"
