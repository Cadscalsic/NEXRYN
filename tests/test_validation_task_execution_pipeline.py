import json
from pathlib import Path

from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
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


def _write_curriculum(
    path: Path,
    *,
    enabled_task=True,
    requires_target=False,
    unsupported=False,
):
    path.write_text(
        json.dumps({
            "tasks": [
                {
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
                    "expected_target_output": [[1]],
                    "required_ground_truth": [[1]],
                    "enabled": enabled_task,
                    "requires_target_for_prediction": requires_target,
                    "unsupported_task_type": unsupported,
                }
            ]
        }),
        encoding="utf-8",
    )


def _registry(curriculum_path, *, enabled=True):
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="elite_validation_academy",
        display_name="Elite Validation Academy",
        path=curriculum_path,
        enabled=enabled,
    )
    return registry


def _scheduled_plan(tmp_path, registry):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan())
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )
    schedule = ValidationTaskScheduler(tmp_path, registry).schedule_plan(
        persisted["evidence_plan_id"]
    )
    return persisted, schedule


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_scheduled_validation_task_executes_and_captures_raw_result(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    persisted, schedule = _scheduled_plan(tmp_path, _registry(curriculum))

    report = ValidationTaskExecutionPipeline(
        tmp_path,
        _registry(curriculum),
    ).execute_schedule(schedule["schedule_id"])

    assert report["execution_admission_state"] == "ADMITTED"
    assert report["execution_invoked"] is True
    assert report["execution_started"] is True
    assert report["execution_completed"] is True
    assert report["execution_state"] == "RAW_RESULT_CAPTURED"
    assert report["raw_result_captured"] is True
    assert report["raw_result_creation_result"] == "CREATED_NEW_RAW_RESULT"
    assert report["target_reference_forwarded_to_solver"] is False
    assert report["prediction_target_comparison_performed"] is False
    assert report["accuracy_calculated"] is False
    assert report["evidence_evaluation_invoked"] is False
    assert report["evidence_produced"] is False
    assert report["evidence_accepted"] is False
    assert report["arena_reentry_invoked"] is False
    assert report["candidate_ranking_modified"] is False
    assert report["candidate_execution_authority"] == "NONE"
    assert report["truth_authority"] == "NONE"
    assert report["trust_authority"] == "NONE"
    assert report["graduation_authority"] == "NONE"
    assert report["next_consumer"] == "VALIDATION_EVIDENCE_EVALUATOR"

    plan = _read_json(
        tmp_path / "pending" / f"{persisted['evidence_plan_id']}.json"
    )
    schedule_record = _read_json(
        tmp_path / "schedules" / f"{schedule['schedule_id']}.json"
    )
    raw_result = _read_json(
        tmp_path / "raw_results" / f"{report['raw_result_id']}.json"
    )
    assert plan["lifecycle_state"] == "RAW_RESULT_CAPTURED"
    assert plan["execution_state"] == "RAW_RESULT_CAPTURED"
    assert plan["raw_result_id"] == raw_result["raw_result_id"]
    assert schedule_record["execution_state"] == "RAW_RESULT_CAPTURED"
    assert schedule_record["raw_result_id"] == raw_result["raw_result_id"]
    assert raw_result["plan_id"] == plan["plan_id"]
    assert raw_result["schedule_id"] == schedule_record["schedule_id"]
    assert raw_result["raw_validation_result_schema_version"] == "1.0"
    assert raw_result["raw_validation_result_id"] == raw_result["raw_result_id"]
    envelope = raw_result["RAW_VALIDATION_RESULT_ENVELOPE"]
    assert envelope["raw_validation_result_id"] == raw_result["raw_result_id"]
    assert envelope["run_id"] == plan["source_run_id"]
    assert envelope["task_id"] == plan["source_task_id"]
    assert envelope["execution_plan_id"] == plan["plan_id"]
    assert envelope["executor_invocation_id"] == raw_result["execution_id"]
    assert envelope["validation_attempt_id"].startswith("validation_attempt_")
    assert envelope["expected_artifact_id"].startswith("expected_artifact_")
    assert envelope["captured_artifact_id"].startswith("captured_artifact_")
    assert envelope["artifact_state"] == "ARTIFACT_CAPTURED"
    assert envelope["payload_state"] == "PAYLOAD_CAPTURED"
    assert envelope["provenance_state"] == "RAW_RESULT_PROVENANCE_BOUND"
    assert envelope["binding_integrity_state"] == "BOUND"
    assert envelope["downstream_structural_eligibility"] == "STRUCTURALLY_ELIGIBLE"
    assert envelope["evidence_evaluation_invoked"] is False
    assert envelope["evidence_record_id"] is None
    assert raw_result["comparison_state"] == "NOT_COMPARED"
    assert raw_result["evidence_state"] == "NOT_EVALUATED"


def test_reprocessing_reuses_existing_raw_result_without_runner_invocation(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    _, schedule = _scheduled_plan(tmp_path, _registry(curriculum))

    class CountingPipeline(ValidationTaskExecutionPipeline):
        calls = 0

        def _run_task(self, task, schedule, plan):
            self.calls += 1
            return super()._run_task(task, schedule, plan)

    pipeline = CountingPipeline(tmp_path, _registry(curriculum))
    first = pipeline.execute_schedule(schedule["schedule_id"])
    second = pipeline.execute_schedule(schedule["schedule_id"])

    assert first["raw_result_creation_result"] == "CREATED_NEW_RAW_RESULT"
    assert second["raw_result_creation_result"] == "REUSED_EXISTING_RAW_RESULT"
    assert first["raw_result_id"] == second["raw_result_id"]
    assert second["execution_invoked"] is False
    assert pipeline.calls == 1
    assert len(list((tmp_path / "raw_results").glob("*.json"))) == 1


def test_raw_validation_result_identity_is_deterministic_and_not_random(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    _, schedule = _scheduled_plan(tmp_path, _registry(curriculum))

    pipeline = ValidationTaskExecutionPipeline(tmp_path, _registry(curriculum))
    first = pipeline.execute_schedule(schedule["schedule_id"])
    second = pipeline.execute_schedule(schedule["schedule_id"])

    assert first["raw_validation_result_id"] == second["raw_validation_result_id"]
    assert first["RAW_VALIDATION_RESULT_ENVELOPE"]["raw_validation_result_id"] == (
        second["RAW_VALIDATION_RESULT_ENVELOPE"]["raw_validation_result_id"]
    )
    assert first["raw_validation_result_id"].startswith("raw_validation_result_")


def test_missing_artifact_is_not_reported_as_captured_or_eligible(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    _, schedule = _scheduled_plan(tmp_path, _registry(curriculum))

    class MissingOutputPipeline(ValidationTaskExecutionPipeline):
        def _run_task(self, task, schedule, plan):
            return {}

    report = MissingOutputPipeline(tmp_path, _registry(curriculum)).execute_schedule(
        schedule["schedule_id"]
    )
    envelope = report["RAW_VALIDATION_RESULT_ENVELOPE"]

    assert report["execution_state"] == "RAW_RESULT_ARTIFACT_MISSING"
    assert report["raw_result_captured"] is False
    assert report["raw_validation_result_id"] is None
    assert report["raw_result_identity_state"] == (
        "APPLICABLE_ARTIFACT_MISSING_IDENTITY_NOT_ISSUABLE"
    )
    assert envelope["artifact_state"] == "ARTIFACT_MISSING"
    assert envelope["payload_state"] == "PAYLOAD_MISSING"
    assert envelope["captured_artifact_id"] is None
    assert envelope["downstream_structural_eligibility"] == "STRUCTURALLY_INELIGIBLE"
    assert envelope["structural_ineligibility_reason"] == "ARTIFACT_MISSING"
    assert report["next_consumer"] == "NONE"


def test_empty_valid_output_is_distinct_from_missing_artifact(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    _, schedule = _scheduled_plan(tmp_path, _registry(curriculum))

    class EmptyValidPipeline(ValidationTaskExecutionPipeline):
        def _run_task(self, task, schedule, plan):
            return {"empty_output_valid": True}

    report = EmptyValidPipeline(tmp_path, _registry(curriculum)).execute_schedule(
        schedule["schedule_id"]
    )
    envelope = report["RAW_VALIDATION_RESULT_ENVELOPE"]

    assert report["execution_state"] == "RAW_RESULT_EMPTY_VALID_OUTPUT_CAPTURED"
    assert report["raw_result_captured"] is True
    assert envelope["artifact_state"] == "ARTIFACT_EMPTY_VALID_OUTPUT"
    assert envelope["payload_state"] == "EMPTY_VALID_OUTPUT"
    assert envelope["downstream_structural_eligibility"] == "STRUCTURALLY_ELIGIBLE"


def test_source_label_is_not_silently_treated_as_task_identity(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    persisted, schedule = _scheduled_plan(
        tmp_path,
        _registry(curriculum),
    )
    plan_path = tmp_path / "pending" / f"{persisted['evidence_plan_id']}.json"
    schedule_path = tmp_path / "schedules" / f"{schedule['schedule_id']}.json"
    plan = _read_json(plan_path)
    schedule_record = _read_json(schedule_path)
    plan["source_task_id"] = "semantic_to_transformation_compiler_0"
    schedule_record["source_task_id"] = "semantic_to_transformation_compiler_0"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    schedule_path.write_text(json.dumps(schedule_record, indent=2), encoding="utf-8")

    report = ValidationTaskExecutionPipeline(
        tmp_path,
        _registry(curriculum),
    ).execute_schedule(schedule["schedule_id"])
    envelope = report["RAW_VALIDATION_RESULT_ENVELOPE"]

    assert envelope["task_id"] == "semantic_to_transformation_compiler_0"
    assert envelope["producer_component_id"] == "VALIDATION_TASK_EXECUTION_PIPELINE"
    assert envelope["binding_integrity_state"] == "CONFLICTED"
    assert envelope["raw_validation_result_identity_state"] == (
        "RAW_VALIDATION_IDENTITY_TYPE_CONFLICT"
    )
    assert envelope["downstream_structural_eligibility"] == "STRUCTURALLY_INELIGIBLE"


def test_three_batch_results_remain_task_local_and_distinct(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    reports = []
    for index in range(3):
        root = tmp_path / f"task_{index}"
        persisted, schedule = _scheduled_plan(
            root,
            _registry(curriculum),
        )
        plan_path = root / "pending" / f"{persisted['evidence_plan_id']}.json"
        schedule_path = root / "schedules" / f"{schedule['schedule_id']}.json"
        plan = _read_json(plan_path)
        schedule_record = _read_json(schedule_path)
        plan["source_task_id"] = f"task_{index}"
        schedule_record["source_task_id"] = f"task_{index}"
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        schedule_path.write_text(json.dumps(schedule_record, indent=2), encoding="utf-8")
        reports.append(
            ValidationTaskExecutionPipeline(root, _registry(curriculum))
            .execute_schedule(schedule["schedule_id"])
        )

    ids = {report["raw_validation_result_id"] for report in reports}
    tasks = {
        report["RAW_VALIDATION_RESULT_ENVELOPE"]["task_id"]
        for report in reports
    }
    assert len(ids) == 3
    assert tasks == {"task_0", "task_1", "task_2"}


def test_scheduler_alone_does_not_execute_task(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    _, schedule = _scheduled_plan(tmp_path, _registry(curriculum))

    assert schedule["task_scheduled"] is True
    assert schedule["execution_invoked"] is False
    assert schedule["execution_state"] == "NOT_STARTED"
    assert not (tmp_path / "raw_results").exists()


def test_plan_schedule_mismatch_blocks_execution(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    persisted, schedule = _scheduled_plan(tmp_path, _registry(curriculum))
    plan_path = tmp_path / "pending" / f"{persisted['evidence_plan_id']}.json"
    plan = _read_json(plan_path)
    plan["selected_validation_task_id"] = "other_task"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    report = ValidationTaskExecutionPipeline(
        tmp_path,
        _registry(curriculum),
    ).execute_schedule(schedule["schedule_id"])

    assert report["execution_admission_state"] == "BLOCKED_PLAN_SCHEDULE_MISMATCH"
    assert report["execution_invoked"] is False
    assert report["raw_result_captured"] is False


def test_disabled_task_and_target_leakage_block_execution(tmp_path):
    disabled_curriculum = tmp_path / "disabled.json"
    _write_curriculum(disabled_curriculum, enabled_task=True)
    _, disabled_schedule = _scheduled_plan(
        tmp_path / "disabled",
        _registry(disabled_curriculum),
    )
    _write_curriculum(disabled_curriculum, enabled_task=False)
    disabled_report = ValidationTaskExecutionPipeline(
        tmp_path / "disabled",
        _registry(disabled_curriculum),
    ).execute_schedule(disabled_schedule["schedule_id"])
    assert disabled_report["execution_admission_state"] == "BLOCKED_TASK_DISABLED"

    leakage_root = tmp_path / "leakage"
    leakage_curriculum = tmp_path / "leakage.json"
    _write_curriculum(leakage_curriculum, requires_target=True)
    _, leakage_schedule = _scheduled_plan(
        leakage_root,
        _registry(leakage_curriculum),
    )
    leakage_report = ValidationTaskExecutionPipeline(
        leakage_root,
        _registry(leakage_curriculum),
    ).execute_schedule(leakage_schedule["schedule_id"])
    assert leakage_report["execution_admission_state"] == (
        "BLOCKED_TARGET_LEAKAGE_RISK"
    )
    assert leakage_report["execution_invoked"] is False


def test_execution_start_persistence_failure_prevents_runner_invocation(
    tmp_path,
    monkeypatch,
):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    _, schedule = _scheduled_plan(tmp_path, _registry(curriculum))

    class CountingPipeline(ValidationTaskExecutionPipeline):
        calls = 0

        def _run_task(self, task, schedule, plan):
            self.calls += 1
            return super()._run_task(task, schedule, plan)

    pipeline = CountingPipeline(tmp_path, _registry(curriculum))

    def fail_write(path, payload):
        raise OSError("simulated_execution_start_failure")

    monkeypatch.setattr(pipeline, "_atomic_write", fail_write)
    report = pipeline.execute_schedule(schedule["schedule_id"])

    assert report["execution_admission_state"] == (
        "BLOCKED_EXECUTION_STATE_PERSISTENCE_FAILURE"
    )
    assert report["execution_invoked"] is False
    assert report["raw_result_captured"] is False
    assert pipeline.calls == 0
    assert list((tmp_path / "raw_results").glob("*.json")) == []


def test_runner_exception_records_failure_without_evidence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    _, schedule = _scheduled_plan(tmp_path, _registry(curriculum))

    class FailingPipeline(ValidationTaskExecutionPipeline):
        def _run_task(self, task, schedule, plan):
            raise RuntimeError("simulated_runner_failure")

    report = FailingPipeline(tmp_path, _registry(curriculum)).execute_schedule(
        schedule["schedule_id"]
    )

    assert report["execution_state"] == "EXECUTION_FAILED"
    assert report["execution_invoked"] is True
    assert report["execution_started"] is True
    assert report["execution_completed"] is False
    assert report["raw_result_captured"] is False
    assert report["evidence_state"] == "NOT_EVALUATED"
    assert report["evidence_accepted"] is False
    assert len(list((tmp_path / "raw_results").glob("*.json"))) == 0


def test_raw_result_captured_boots_to_evidence_evaluator(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    _, schedule = _scheduled_plan(tmp_path, _registry(curriculum))
    report = ValidationTaskExecutionPipeline(
        tmp_path,
        _registry(curriculum),
    ).execute_schedule(schedule["schedule_id"])

    loaded = EvidenceAcquisitionPlanStore(tmp_path).load_pending_plans()

    assert loaded["pending_evidence_acquisition_plans"] == []
    assert len(loaded["raw_result_captured_evidence_plans"]) == 1
    assert loaded["boot_recovery_route"] == (
        "RAW_RESULT_CAPTURED_TO_VALIDATION_EVIDENCE_EVALUATOR"
    )
    assert loaded["evidence_plan_lifecycle_state"] == "RAW_RESULT_CAPTURED"
    assert loaded["execution_state"] == "RAW_RESULT_CAPTURED"
    assert loaded["raw_result_id"] == report["raw_result_id"]
    assert loaded["evidence_state"] == "NOT_EVALUATED"
