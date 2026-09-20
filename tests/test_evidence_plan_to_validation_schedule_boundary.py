import json
from pathlib import Path

from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.evidence.validation_request import ValidationRequestAuthorityEngine
from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
)
from runtime.validation.validation_task_scheduler import ValidationTaskScheduler
from tests.test_validation_request_authority import _active_sponsorship


def _write_curriculum(path: Path, *, enabled=True):
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
                    "enabled": enabled,
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


def _chain_to_waiting_plan(tmp_path):
    need_engine, sponsor, sponsorship_state = _active_sponsorship(tmp_path)
    request_engine = ValidationRequestAuthorityEngine(
        tmp_path / "requests",
        sponsorship_authority=sponsor,
    )
    request_candidate = request_engine.candidate_from_current_sponsorship(
        sponsorship_state["validation_sponsorship_id"]
    )
    request_state = request_engine.decide_request(request_candidate)["current_state"]
    store = EvidenceAcquisitionPlanStore(tmp_path / "plans")
    plan_report = store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=request_engine,
    )
    store.mark_consumption_pending(plan_report["evidence_plan_id"])
    store.persist_selection_from_consumption_report({
        "current_plan_id": plan_report["evidence_plan_id"],
        "selection_state": "WAITING_EXECUTION",
        "selected_validation_task": "elite_validation_task_31",
        "best_matching_curriculum": "Elite Validation Academy",
        "current_required_evidence": "cross_source_consensus_evidence",
        "current_target_operation": "SOURCE_INDEPENDENCE_REQUIRED",
        "current_tie_break_strategy": "cross_source_consensus",
        "selected_validation_task_metadata": {
            "curriculum_id": "elite_validation_academy",
        },
    })
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    scheduler = ValidationTaskScheduler(
        tmp_path / "plans",
        _registry(curriculum),
        need_authority=need_engine,
        sponsorship_authority=sponsor,
        request_authority=request_engine,
    )
    return need_engine, sponsor, request_engine, store, scheduler, sponsorship_state, plan_report


def test_current_plan_schedules_after_preschedule_currentness_revalidation(tmp_path):
    _, _, _, _, scheduler, sponsorship_state, plan_report = _chain_to_waiting_plan(
        tmp_path
    )

    report = scheduler.schedule_plan(plan_report["evidence_plan_id"])

    assert report["scheduling_admission_state"] == "ADMITTED"
    assert report["scheduling_state"] == "SCHEDULED"
    assert report["task_scheduled"] is True
    assert report["task_execution_started"] is False
    assert report["execution_invoked"] is False
    assert report["execution_authority"] == "NONE"
    schedule_path = tmp_path / "plans" / "schedules" / f"{report['schedule_id']}.json"
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    assert schedule["plan_id"] == plan_report["evidence_plan_id"]
    assert schedule["source_validation_request_id"] == (
        plan_report["source_validation_request_id"]
    )
    assert schedule["source_validation_sponsorship_id"] == (
        sponsorship_state["validation_sponsorship_id"]
    )
    assert schedule["source_evidence_need_id"] == sponsorship_state["evidence_need_id"]
    assert schedule["capability_id"] != "Not Available"
    assert schedule["validation_scope"] == "SOURCE_INDEPENDENCE"
    assert schedule["schedule_id"] != plan_report["evidence_plan_id"]


def test_satisfied_need_blocks_existing_plan_before_schedule(tmp_path):
    need_engine, _, _, _, scheduler, sponsorship_state, plan_report = (
        _chain_to_waiting_plan(tmp_path)
    )
    need_engine.satisfy_need(
        sponsorship_state["evidence_need_id"],
        current_support_summary={
            "independent_source_count": 2,
            "required_independent_sources": 2,
        },
    )

    report = scheduler.schedule_plan(plan_report["evidence_plan_id"])

    assert report["scheduling_admission_state"] == "DENIED_SOURCE_NEED_NOT_CURRENT"
    assert report["task_scheduled"] is False
    assert report["execution_invoked"] is False
    assert not list((tmp_path / "plans" / "schedules").glob("*.json"))


def test_reviewed_invalidated_and_superseded_need_block_schedule(tmp_path):
    for transition in ("review", "invalidate", "supersede"):
        need_engine, _, _, _, scheduler, sponsorship_state, plan_report = (
            _chain_to_waiting_plan(tmp_path / transition)
        )
        if transition == "review":
            need_engine.open_review(
                sponsorship_state["evidence_need_id"],
                review_reason="controlled_review",
            )
        elif transition == "invalidate":
            need_engine.invalidate_need(
                sponsorship_state["evidence_need_id"],
                invalidation_reason="controlled_invalid",
            )
        else:
            need_engine.supersede_need(
                sponsorship_state["evidence_need_id"],
                replacement_evidence_need_id="replacement_need",
                supersession_reason="controlled_supersession",
            )

        report = scheduler.schedule_plan(plan_report["evidence_plan_id"])

        assert report["scheduling_admission_state"] == (
            "DENIED_SOURCE_NEED_NOT_CURRENT"
        )
        assert report["task_scheduled"] is False


def test_revoked_and_expired_sponsorship_block_schedule(tmp_path):
    for transition in ("revoked", "expired"):
        _, sponsor, _, _, scheduler, sponsorship_state, plan_report = (
            _chain_to_waiting_plan(tmp_path / transition)
        )
        if transition == "revoked":
            sponsor.revoke_sponsorship(
                sponsorship_state["validation_sponsorship_id"],
                revocation_reason="controlled_revocation",
            )
        else:
            sponsor.expire_sponsorship(
                sponsorship_state["validation_sponsorship_id"],
                expiration_reason="controlled_expiration",
            )

        report = scheduler.schedule_plan(plan_report["evidence_plan_id"])

        assert report["scheduling_admission_state"] == (
            "DENIED_SOURCE_SPONSORSHIP_NOT_CURRENT"
        )
        assert report["task_scheduled"] is False


def test_duplicate_schedule_reuses_one_current_schedule(tmp_path):
    _, _, _, _, scheduler, _, plan_report = _chain_to_waiting_plan(tmp_path)

    first = scheduler.schedule_plan(plan_report["evidence_plan_id"])
    second = scheduler.schedule_plan(plan_report["evidence_plan_id"])

    assert first["schedule_id"] == second["schedule_id"]
    assert second["schedule_creation_result"] == "REUSED_EXISTING_SCHEDULE"
    assert len(list((tmp_path / "plans" / "schedules").glob("*.json"))) == 1


def test_schedule_persistence_failure_does_not_mark_plan_scheduled(tmp_path, monkeypatch):
    _, _, _, _, scheduler, _, plan_report = _chain_to_waiting_plan(tmp_path)

    def fail_write(path, payload):
        raise OSError("simulated_schedule_write_failure")

    monkeypatch.setattr(scheduler, "_atomic_write", fail_write)
    report = scheduler.schedule_plan(plan_report["evidence_plan_id"])
    plan_path = (
        tmp_path / "plans" / "pending" / f"{plan_report['evidence_plan_id']}.json"
    )
    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    assert report["scheduling_admission_state"] == (
        "BLOCKED_SCHEDULING_PERSISTENCE_FAILURE"
    )
    assert report["task_scheduled"] is False
    assert plan["lifecycle_state"] == "WAITING_EXECUTION"
    assert not list((tmp_path / "plans" / "schedules").glob("*.json"))
