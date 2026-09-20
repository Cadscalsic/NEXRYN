import json
from pathlib import Path

from runtime.evidence.training_outcome_validation_boundary import (
    TrainingOutcomeValidationBoundary,
)
from runtime.training.validation_curriculum_registry import ValidationCurriculumRegistry
from runtime.validation.validation_task_execution_pipeline import (
    ValidationTaskExecutionPipeline,
)
from runtime.validation.validation_task_scheduler import ValidationTaskScheduler


def _outcome(**overrides):
    payload = {
        "run_id": "run_current",
        "task_id": "elite_cognitive_task_04.json",
        "task_execution_id": "training_execution_current_04",
        "execution_plan_id": "execution_plan_current",
        "success_state": "EXACT_SUCCESS",
        "accuracy": 1.0,
        "final_score": 1.0,
        "residual_analysis": {
            "residual_type": "none",
            "residual_difference_count": 0,
        },
    }
    payload.update(overrides)
    return payload


def _need(**overrides):
    payload = {
        "evidence_need_state": "CURRENT",
        "capability_id": "capability_replace_color",
        "capability_identity_state": "CANONICAL_CAPABILITY_TARGET_RESOLVED",
        "claim_id": "claim_replace_color_cross_source",
        "claim_subject": {
            "subject_type": "candidate_operation",
            "target_candidate": "semantic_program:replace_color",
            "target_operation": "replace_color",
        },
        "qualification_evidence_need": True,
        "validation_sponsorship_reason": "qualification_evidence_need",
        "evidence_acquisition_state": "EVIDENCE_ACQUISITION_PLAN_READY",
        "evidence_acquisition_trigger": "TRAINING_OUTCOME_VALIDATION_REQUEST",
        "required_evidence_category": "CROSS_SOURCE_CONSENSUS",
        "required_evidence": "cross_source_consensus_evidence",
        "required_validation_task": "select_cross_source_tie_break_validation_task",
        "tie_break_strategy": "cross_source_consensus",
        "expected_tie_break_impact": "HIGH",
        "target_candidate": "semantic_program:replace_color",
        "target_operation": "replace_color",
        "governed_reentry_action": (
            "reenter_arena_after_required_evidence_without_truth_grant"
        ),
    }
    payload.update(overrides)
    return payload


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


def _registry(curriculum_path: Path):
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="elite_validation_academy",
        display_name="Elite Validation Academy",
        path=curriculum_path,
        enabled=True,
    )
    return registry


def test_success_alone_does_not_create_validation_request(tmp_path):
    boundary = TrainingOutcomeValidationBoundary(tmp_path / "requests")

    report = boundary.assess_outcome(_outcome())

    assert report["candidate_created"] is False
    assert report["validation_request_created"] is False
    assert report["evidence_candidate"]["candidate_state"] == "NOT_VALIDATION_WORTHY"
    assert report["validation_request"]["request_state"] == "REJECTED"
    assert report["direct_raw_evidence_created"] is False
    assert report["direct_accepted_evidence_created"] is False


def test_missing_target_fails_closed_without_fabricated_claim(tmp_path):
    boundary = TrainingOutcomeValidationBoundary(tmp_path / "requests")

    report = boundary.assess_outcome(
        _outcome(),
        evidence_need=_need(
            capability_id=None,
            capability_identity_state=None,
            claim_id=None,
            claim_subject=None,
        ),
        task_metadata={"target_concepts": ["replace_color"]},
    )

    assert report["candidate_created"] is False
    assert report["validation_request_created"] is False
    assert report["evidence_candidate"]["capability_resolution_state"] in {
        "CAPABILITY_TARGET_AMBIGUOUS",
        "CAPABILITY_TARGET_UNRESOLVED",
    }
    assert report["evidence_candidate"]["claim_resolution_state"] == (
        "CLAIM_TARGET_UNRESOLVED"
    )
    assert report["validation_request"]["request_admission_state"] == "REJECTED"


def test_current_qualification_need_creates_authority_free_request(tmp_path):
    boundary = TrainingOutcomeValidationBoundary(tmp_path / "requests")

    report = boundary.assess_outcome(
        _outcome(success_state="RECOVERABLE_FAILURE", accuracy=0.81),
        evidence_need=_need(novel_diagnostic_failure=True),
        selection_context={"selection_purpose": "CAPABILITY_EVIDENCE_ACQUISITION"},
    )

    candidate = report["evidence_candidate"]
    request = report["validation_request"]
    assert report["candidate_created"] is True
    assert report["validation_request_created"] is True
    assert candidate["authority"] == "NONE"
    assert request["authority"] == "NONE"
    assert request["raw_evidence_authority"] == "NONE"
    assert request["accepted_evidence_authority"] == "NONE"
    assert request["evidence_plan_authority"] == "NONE"


def test_duplicate_request_is_deduplicated(tmp_path):
    boundary = TrainingOutcomeValidationBoundary(tmp_path / "requests")
    first = boundary.assess_outcome(_outcome(), evidence_need=_need())
    second = boundary.assess_outcome(_outcome(), evidence_need=_need())

    assert first["validation_request"]["request_admission_state"] == "ADMITTED"
    assert second["validation_request"]["request_admission_state"] == "DEDUPLICATED"
    assert second["validation_request"]["request_admission_reason"] == (
        "VALIDATION_NEED_ALREADY_PENDING"
    )
    assert len(list((tmp_path / "requests" / "validation_requests").glob("*.json"))) == 1


def test_request_routes_to_existing_evidence_plan_lifecycle(tmp_path):
    root = tmp_path / "evidence_plans"
    request_root = tmp_path / "requests"
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    boundary = TrainingOutcomeValidationBoundary(request_root)

    report = boundary.assess_outcome(
        _outcome(),
        evidence_need=_need(),
    )
    # route explicitly into the tmp EvidencePlan store for this controlled test.
    plan_report = boundary.route_request_to_evidence_plan(
        report["validation_request"],
        evidence_plan_store=__import__(
            "runtime.evidence.evidence_plan_store",
            fromlist=["EvidenceAcquisitionPlanStore"],
        ).EvidenceAcquisitionPlanStore(root),
    )

    assert plan_report["request_consumed"] is True
    assert plan_report["request_is_not_evidence_plan"] is True
    plan_id = plan_report["evidence_plan_id"]
    store_path = root / "pending" / f"{plan_id}.json"
    plan = json.loads(store_path.read_text(encoding="utf-8"))
    assert plan["validation_request_id"] == report["validation_request"][
        "validation_request_id"
    ]
    assert plan["evidence_candidate_id"] == report["evidence_candidate"][
        "evidence_candidate_id"
    ]

    store = __import__(
        "runtime.evidence.evidence_plan_store",
        fromlist=["EvidenceAcquisitionPlanStore"],
    ).EvidenceAcquisitionPlanStore(root)
    store.mark_consumption_pending(plan_id)
    store.persist_selection_from_consumption_report({
        "current_plan_id": plan_id,
        "selection_state": "WAITING_EXECUTION",
        "selected_validation_task": "elite_validation_task_31",
        "best_matching_curriculum": "Elite Validation Academy",
        "current_required_evidence": "cross_source_consensus_evidence",
        "current_target_operation": "replace_color",
        "current_tie_break_strategy": "cross_source_consensus",
        "selected_validation_task_metadata": {
            "curriculum_id": "elite_validation_academy",
        },
    })
    schedule = ValidationTaskScheduler(root, registry).schedule_plan(plan_id)
    raw = ValidationTaskExecutionPipeline(root, registry).execute_schedule(
        schedule["schedule_id"]
    )

    assert schedule["scheduling_state"] == "SCHEDULED"
    assert raw["execution_state"] == "RAW_RESULT_CAPTURED"
    assert raw["raw_result_captured"] is True
    assert raw["evidence_produced"] is False
    assert raw["evidence_accepted"] is False


def test_direct_evidence_shortcuts_are_denied(tmp_path):
    boundary = TrainingOutcomeValidationBoundary(tmp_path / "requests")

    raw = boundary.deny_direct_raw_evidence(_outcome())
    accepted = boundary.deny_direct_accepted_evidence(_outcome())

    assert raw["admission_state"] == "DENIED"
    assert raw["raw_evidence_created"] is False
    assert accepted["admission_state"] == "DENIED"
    assert accepted["accepted_evidence_created"] is False


def test_cross_capability_and_cross_claim_requests_fail_closed(tmp_path):
    boundary = TrainingOutcomeValidationBoundary(tmp_path / "requests")

    cross_capability = boundary.assess_outcome(
        _outcome(),
        evidence_need=_need(
            capability_id=None,
            capability_identity_state="CAPABILITY_TARGET_AMBIGUOUS",
        ),
    )
    cross_claim = boundary.assess_outcome(
        _outcome(task_execution_id="training_execution_claim_attack"),
        evidence_need=_need(claim_id=None),
    )

    assert cross_capability["validation_request"]["request_state"] == "REJECTED"
    assert "missing_canonical_capability_id" in cross_capability[
        "validation_request"
    ]["request_admission_reason"]
    assert cross_claim["validation_request"]["request_state"] == "REJECTED"
    assert "missing_claim_id" in cross_claim["validation_request"][
        "request_admission_reason"
    ]
