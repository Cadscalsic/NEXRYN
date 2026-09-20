import json
from pathlib import Path

from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
)
from runtime.validation.validation_task_execution_pipeline import (
    ValidationTaskExecutionPipeline,
)
from tests.test_evidence_plan_to_validation_schedule_boundary import (
    _chain_to_waiting_plan,
)


def _write_curriculum(path: Path):
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
                    "enabled": True,
                }
            ]
        }),
        encoding="utf-8",
    )


def _registry(path: Path):
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="elite_validation_academy",
        display_name="Elite Validation Academy",
        path=path,
        enabled=True,
    )
    return registry


def _chain_to_schedule(tmp_path):
    (
        need_engine,
        sponsor,
        request_engine,
        _store,
        scheduler,
        sponsorship_state,
        plan_report,
    ) = _chain_to_waiting_plan(tmp_path)
    schedule_report = scheduler.schedule_plan(plan_report["evidence_plan_id"])
    curriculum = tmp_path / "execution_curriculum.json"
    _write_curriculum(curriculum)
    pipeline = ValidationTaskExecutionPipeline(
        tmp_path / "plans",
        _registry(curriculum),
        need_authority=need_engine,
        sponsorship_authority=sponsor,
        request_authority=request_engine,
    )
    return need_engine, sponsor, pipeline, sponsorship_state, plan_report, schedule_report


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_current_validation_schedule_executes_to_raw_result_without_acceptance(tmp_path):
    _, _, pipeline, sponsorship_state, plan_report, schedule_report = (
        _chain_to_schedule(tmp_path)
    )

    report = pipeline.execute_schedule(schedule_report["schedule_id"])

    assert report["execution_admission_state"] == "ADMITTED"
    assert report["execution_invoked"] is True
    assert report["execution_state"] == "RAW_RESULT_CAPTURED"
    assert report["raw_result_captured"] is True
    assert report["raw_result_creation_result"] == "CREATED_NEW_RAW_RESULT"
    assert report["evidence_evaluation_invoked"] is False
    assert report["evidence_accepted"] is False
    assert report["truth_authority"] == "NONE"
    assert report["graduation_authority"] == "NONE"
    assert report["candidate_ranking_modified"] is False
    assert report["schedule_id"] == schedule_report["schedule_id"]
    assert report["plan_id"] == plan_report["evidence_plan_id"]

    raw = _read(
        tmp_path
        / "plans"
        / "raw_results"
        / f"{report['raw_result_id']}.json"
    )
    assert raw["schedule_id"] == schedule_report["schedule_id"]
    assert raw["plan_id"] == plan_report["evidence_plan_id"]
    assert raw["producer_operation_id"] == raw["execution_id"]
    assert raw["validation_attempt_id"].startswith("validation_attempt_")
    assert raw["claim_id"] == schedule_report.get("claim_id")
    assert raw["evidence_state"] == "NOT_EVALUATED"
    assert raw["origin_operation_id"] == raw["execution_id"]
    schedule_record = _read(
        tmp_path
        / "plans"
        / "schedules"
        / f"{schedule_report['schedule_id']}.json"
    )
    assert sponsorship_state["evidence_need_id"] == (
        schedule_record["schedule_admission_assessment"]["source_evidence_need_id"]
    )


def test_satisfied_need_blocks_execution_of_existing_schedule(tmp_path):
    need_engine, _, pipeline, sponsorship_state, _, schedule_report = (
        _chain_to_schedule(tmp_path)
    )
    need_engine.satisfy_need(
        sponsorship_state["evidence_need_id"],
        current_support_summary={
            "independent_source_count": 2,
            "required_independent_sources": 2,
        },
    )

    report = pipeline.execute_schedule(schedule_report["schedule_id"])

    assert report["execution_admission_state"] == "DENIED_SOURCE_NEED_NOT_CURRENT"
    assert report["execution_invoked"] is False
    assert report["raw_result_captured"] is False
    assert not list((tmp_path / "plans" / "raw_results").glob("*.json"))


def test_need_review_and_invalidated_need_block_execution(tmp_path):
    for transition in ("review", "invalidate"):
        need_engine, _, pipeline, sponsorship_state, _, schedule_report = (
            _chain_to_schedule(tmp_path / transition)
        )
        if transition == "review":
            need_engine.open_review(
                sponsorship_state["evidence_need_id"],
                review_reason="controlled_review",
            )
        else:
            need_engine.invalidate_need(
                sponsorship_state["evidence_need_id"],
                invalidation_reason="controlled_invalid",
            )

        report = pipeline.execute_schedule(schedule_report["schedule_id"])

        assert report["execution_admission_state"] == (
            "DENIED_SOURCE_NEED_NOT_CURRENT"
        )
        assert report["execution_invoked"] is False


def test_revoked_sponsorship_blocks_execution(tmp_path):
    _, sponsor, pipeline, sponsorship_state, _, schedule_report = _chain_to_schedule(
        tmp_path
    )
    sponsor.revoke_sponsorship(
        sponsorship_state["validation_sponsorship_id"],
        revocation_reason="controlled_revocation",
    )

    report = pipeline.execute_schedule(schedule_report["schedule_id"])

    assert report["execution_admission_state"] == (
        "DENIED_SOURCE_SPONSORSHIP_NOT_CURRENT"
    )
    assert report["execution_invoked"] is False
    assert report["raw_result_captured"] is False


def test_invalid_plan_blocks_execution(tmp_path):
    _, _, pipeline, _, plan_report, schedule_report = _chain_to_schedule(tmp_path)
    plan_path = (
        tmp_path / "plans" / "pending" / f"{plan_report['evidence_plan_id']}.json"
    )
    plan = _read(plan_path)
    plan["lifecycle_state"] = "INVALIDATED"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    report = pipeline.execute_schedule(schedule_report["schedule_id"])

    assert report["execution_admission_state"] == "DENIED_PLAN_NOT_EXECUTABLE"
    assert report["execution_invoked"] is False


def test_duplicate_execution_reuses_existing_raw_result_without_invocation(tmp_path):
    _, _, pipeline, _, _, schedule_report = _chain_to_schedule(tmp_path)

    first = pipeline.execute_schedule(schedule_report["schedule_id"])
    second = pipeline.execute_schedule(schedule_report["schedule_id"])

    assert first["raw_result_creation_result"] == "CREATED_NEW_RAW_RESULT"
    assert second["raw_result_creation_result"] == "REUSED_EXISTING_RAW_RESULT"
    assert second["execution_invoked"] is False
    assert first["raw_result_id"] == second["raw_result_id"]


def test_execution_start_persistence_failure_does_not_capture_raw_result(tmp_path, monkeypatch):
    _, _, pipeline, _, _, schedule_report = _chain_to_schedule(tmp_path)

    def fail_write(path, payload):
        raise OSError("simulated_execution_start_failure")

    monkeypatch.setattr(pipeline, "_atomic_write", fail_write)
    report = pipeline.execute_schedule(schedule_report["schedule_id"])

    assert report["execution_admission_state"] == (
        "BLOCKED_EXECUTION_STATE_PERSISTENCE_FAILURE"
    )
    assert report["execution_invoked"] is False
    assert report["raw_result_captured"] is False
    assert not list((tmp_path / "plans" / "raw_results").glob("*.json"))
