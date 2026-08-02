import json
from pathlib import Path

from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
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


def _write_curriculum(path, *, enabled_task=True, evidence=None):
    path.write_text(
        json.dumps({
            "tasks": [
                {
                    "task_id": "elite_validation_task_31",
                    "task_name": "Cross Source Consensus",
                    "target_capability": "replace_color",
                    "target_domain": "Color",
                    "primary_evidence_category": (
                        evidence or "CROSS_SOURCE_CONSENSUS"
                    ),
                    "secondary_evidence_categories": [
                        evidence or "cross_source_consensus_evidence"
                    ],
                    "required_validation_evidence": (
                        evidence or "cross_source_consensus_evidence"
                    ),
                    "required_grounding": [
                        "cross_source_consensus",
                        "select_cross_source_tie_break_validation_task",
                    ],
                    "expected_validation_contract": (
                        "select_cross_source_tie_break_validation_task"
                    ),
                    "enabled": enabled_task,
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


def _waiting_execution_plan(tmp_path):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan())
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )
    return persisted


def test_valid_waiting_execution_plan_creates_one_durable_schedule(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    persisted = _waiting_execution_plan(tmp_path)

    scheduler = ValidationTaskScheduler(tmp_path, _registry(curriculum))
    report = scheduler.schedule_plan(persisted["evidence_plan_id"])

    assert report["scheduling_admission_state"] == "ADMITTED"
    assert report["scheduling_state"] == "SCHEDULED"
    assert report["schedule_creation_result"] == "CREATED_NEW_SCHEDULE"
    assert report["task_selected"] is True
    assert report["task_scheduled"] is True
    assert report["task_execution_started"] is False
    assert report["task_execution_completed"] is False
    assert report["execution_state"] == "NOT_STARTED"
    assert report["execution_invoked"] is False
    assert report["execution_authority"] == "NONE"
    assert report["attempt_count"] == 0

    schedules = list((tmp_path / "schedules").glob("*.json"))
    assert len(schedules) == 1
    schedule = json.loads(schedules[0].read_text(encoding="utf-8"))
    plan = json.loads(
        (tmp_path / "pending" / f"{persisted['evidence_plan_id']}.json")
        .read_text(encoding="utf-8")
    )
    assert plan["lifecycle_state"] == "SCHEDULED"
    assert plan["schedule_id"] == schedule["schedule_id"]
    assert schedule["plan_id"] == plan["plan_id"]
    assert schedule["selected_validation_task_id"] == (
        plan["selected_validation_task_id"]
    )
    assert schedule["execution_state"] == "NOT_STARTED"
    assert schedule["execution_invoked"] is False


def test_duplicate_scheduler_calls_reuse_existing_schedule(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    persisted = _waiting_execution_plan(tmp_path)
    scheduler = ValidationTaskScheduler(tmp_path, _registry(curriculum))

    first = scheduler.schedule_plan(persisted["evidence_plan_id"])
    second = scheduler.schedule_plan(persisted["evidence_plan_id"])

    assert first["schedule_id"] == second["schedule_id"]
    assert second["schedule_creation_result"] == "REUSED_EXISTING_SCHEDULE"
    assert len(list((tmp_path / "schedules").glob("*.json"))) == 1


def test_scheduled_plan_boots_to_execution_pipeline_not_matching(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    persisted = _waiting_execution_plan(tmp_path)
    ValidationTaskScheduler(tmp_path, _registry(curriculum)).schedule_plan(
        persisted["evidence_plan_id"]
    )

    loaded = EvidenceAcquisitionPlanStore(tmp_path).load_pending_plans()

    assert loaded["pending_evidence_acquisition_plans"] == []
    assert len(loaded["scheduled_evidence_plans"]) == 1
    assert loaded["boot_recovery_route"] == (
        "SCHEDULED_TO_VALIDATION_EXECUTION_PIPELINE"
    )
    assert loaded["evidence_plan_lifecycle_state"] == "SCHEDULED"
    assert loaded["execution_state"] == "NOT_STARTED"


def test_invalid_state_and_missing_task_block_scheduling(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan())
    scheduler = ValidationTaskScheduler(tmp_path, _registry(curriculum))

    invalid_state = scheduler.schedule_plan(persisted["evidence_plan_id"])
    assert invalid_state["scheduling_admission_state"] == (
        "BLOCKED_INVALID_PLAN_STATE"
    )
    assert invalid_state["task_scheduled"] is False

    delivery = store.mark_consumption_pending(persisted["evidence_plan_id"])
    plan_path = Path(delivery["evidence_plan_storage_path"])
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["lifecycle_state"] = "WAITING_EXECUTION"
    plan["consumption_state"] = "MATCHING_COMPLETED"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    missing_task = scheduler.schedule_plan(persisted["evidence_plan_id"])
    assert missing_task["scheduling_admission_state"] == (
        "BLOCKED_MISSING_SELECTED_TASK"
    )


def test_disabled_or_incompatible_task_blocks_scheduling(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    persisted = _waiting_execution_plan(tmp_path)

    disabled = ValidationTaskScheduler(
        tmp_path,
        _registry(curriculum, enabled=False),
    ).schedule_plan(persisted["evidence_plan_id"])
    assert disabled["scheduling_admission_state"] == "BLOCKED_TASK_DISABLED"

    incompatible = tmp_path / "incompatible.json"
    _write_curriculum(incompatible, evidence="identity_preservation_evidence")
    mismatch = ValidationTaskScheduler(
        tmp_path,
        _registry(incompatible),
    ).schedule_plan(persisted["evidence_plan_id"])
    assert mismatch["scheduling_admission_state"] == "BLOCKED_EVIDENCE_MISMATCH"


def test_persistence_failure_does_not_claim_scheduled(tmp_path, monkeypatch):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    persisted = _waiting_execution_plan(tmp_path)
    scheduler = ValidationTaskScheduler(tmp_path, _registry(curriculum))

    def fail_write(path, payload):
        raise OSError("simulated_schedule_write_failure")

    monkeypatch.setattr(scheduler, "_atomic_write", fail_write)
    report = scheduler.schedule_plan(persisted["evidence_plan_id"])

    assert report["scheduling_admission_state"] == (
        "BLOCKED_SCHEDULING_PERSISTENCE_FAILURE"
    )
    assert report["schedule_creation_result"] == "SCHEDULE_PERSISTENCE_FAILED"
    assert report["scheduling_state"] == "NOT_SCHEDULED"
    assert report["task_scheduled"] is False
    plan = json.loads(
        (tmp_path / "pending" / f"{persisted['evidence_plan_id']}.json")
        .read_text(encoding="utf-8")
    )
    assert plan["lifecycle_state"] == "WAITING_EXECUTION"
