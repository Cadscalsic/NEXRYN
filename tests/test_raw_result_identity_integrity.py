import json
from copy import deepcopy

from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer
from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
)
from runtime.validation.raw_result_lifecycle_applicability import (
    APPLICABLE,
    NOT_APPLICABLE,
    UNDETERMINED,
    RawResultLifecycleApplicabilityEvaluator,
)
from runtime.validation.validation_task_execution_pipeline import (
    ValidationTaskExecutionPipeline,
)
from runtime.validation.validation_evidence_evaluator import ValidationEvidenceEvaluator
from runtime.validation.validation_task_scheduler import ValidationTaskScheduler


def _write_curriculum(path):
    path.write_text(
        json.dumps({
            "tasks": [
                {
                    "task_id": "elite_validation_task_31",
                    "task_name": "Cross Source Consensus",
                    "target_capability": "replace_color",
                    "target_domain": "Color",
                    "primary_evidence_category": "CROSS_SOURCE_CONSENSUS",
                    "secondary_evidence_categories": ["cross_source_consensus_evidence"],
                    "required_validation_evidence": "cross_source_consensus_evidence",
                    "required_grounding": ["cross_source_consensus"],
                    "expected_validation_contract": "localized_remap_consensus_contract",
                    "validation_objective": "observe consensus",
                    "expected_target_output": [[1]],
                    "required_ground_truth": [[1]],
                    "enabled": True,
                }
            ]
        }),
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


def _plan(run_id="run_identity", execution_plan_id="plan_identity", **overrides):
    plan = {
        "source_run_id": run_id,
        "source_task_id": "task-localized-remap",
        "source_candidate_id": "semantic_program:replace_color",
        "source_operation": "replace_color",
        "execution_plan_id": execution_plan_id,
        "evidence_acquisition_state": "EVIDENCE_ACQUISITION_PLAN_READY",
        "evidence_acquisition_trigger": "TIE_CONFIRMED_AFTER_ACCEPTED_SANDBOX_PROBE",
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
        "candidate_execution_authority": "NONE",
        "truth_authority": "NONE",
        "trust_authority": "NONE",
        "graduation_authority": "NONE",
        "execution_authority": "NONE",
    }
    plan.update(overrides)
    return plan


def _consumption_report(plan_id):
    return {
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


def _execute_validation(tmp_path, *, run_id="run_identity", execution_plan_id="plan_identity"):
    tmp_path.mkdir(parents=True, exist_ok=True)
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan(run_id, execution_plan_id))
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )
    schedule = ValidationTaskScheduler(tmp_path, registry).schedule_plan(
        persisted["evidence_plan_id"]
    )
    report = ValidationTaskExecutionPipeline(tmp_path, registry).execute_schedule(
        schedule["schedule_id"]
    )
    raw_path = tmp_path / "raw_results" / f"{report['raw_result_id']}.json"
    raw_result = json.loads(raw_path.read_text(encoding="utf-8"))
    return report, raw_result


def _raw_path(tmp_path, raw_result_id):
    return tmp_path / "raw_results" / f"{raw_result_id}.json"


def _applicability(report):
    return RawResultLifecycleApplicabilityEvaluator().evaluate(
        run_id=report["run_id"],
        execution_plan_id=report["execution_plan_id"],
        task_id=report["task_id"],
        validation_task_execution_report=report,
        source_timestamp="2026-08-08T00:00:00",
    )


def test_not_applicable_issues_no_raw_result_identity():
    applicability = RawResultLifecycleApplicabilityEvaluator().evaluate(
        run_id="run_identity",
        execution_plan_id="plan_identity",
        validation_task_execution_report={},
        source_timestamp="2026-08-08T00:00:00",
    )
    rendered = DeterministicFinalReportRenderer().render(
        {
            "runtime_status": "completed",
            "RAW_RESULT_APPLICABILITY_REPORT": applicability,
            "validation_task_execution_report": {},
        },
        runtime_metadata={
            "run_id": "run_identity",
            "timestamp": "2026-08-08T00:00:00",
            "mode": "adaptive",
            "runtime_status": "completed",
            "training_batch_size": 3,
        },
    )

    assert applicability["raw_result_applicability_state"] == NOT_APPLICABLE
    assert "Raw Result Identity State: NOT_EVALUATED_NOT_APPLICABLE" in rendered
    assert "Canonical Raw Result Id: Not expected at current lifecycle state" in rendered
    assert "RAW_RESULT_IDENTITY_INTACT" not in rendered


def test_applicable_materialized_raw_result_gets_one_source_identity(tmp_path):
    report, raw_result = _execute_validation(tmp_path)
    applicability = _applicability(report)

    assert applicability["raw_result_applicability_state"] == APPLICABLE
    assert report["raw_result_id"] == report["raw_validation_result_id"]
    assert report["canonical_raw_result_id"] == report["raw_validation_result_id"]
    assert report["raw_result_identity_issuance_count"] == 1
    assert report["raw_result_identity_state"] == "APPLICABLE_ARTIFACT_PRESENT_IDENTITY_BOUND"
    assert report["raw_result_identity_integrity_state"] == "RAW_RESULT_IDENTITY_INTACT"
    assert raw_result["raw_validation_result_id"] == report["raw_validation_result_id"]
    assert raw_result["immutable_identity_fingerprint"] == report["immutable_identity_fingerprint"]
    assert raw_result["run_id"] == "run_identity"
    assert raw_result["execution_plan_id"] == report["execution_plan_id"]
    assert raw_result["validation_attempt_id"] == report["validation_attempt_id"]
    assert raw_result["raw_validation_result_id"] != raw_result["raw_result_fingerprint"]
    assert raw_result["immutable_identity_fingerprint"] != raw_result["raw_result_fingerprint"]
    assert [
        event["transition_name"]
        for event in raw_result["raw_result_identity_lifecycle_transitions"]
    ] == [
        "RAW_RESULT_APPLICABILITY_FINALIZED",
        "PRODUCER_OBLIGATION_BOUNDARY_CROSSED",
        "RAW_RESULT_MATERIALIZED",
        "RAW_RESULT_IDENTITY_ISSUANCE_REQUESTED",
        "RAW_RESULT_IDENTITY_ISSUED",
        "RAW_RESULT_IDENTITY_BOUND_TO_ARTIFACT",
        "RAW_RESULT_IDENTITY_PROPAGATED",
        "RAW_RESULT_IDENTITY_INTEGRITY_EVALUATED",
    ]
    assert [
        event["sequence_index"]
        for event in raw_result["raw_result_identity_lifecycle_transitions"]
    ] == list(range(1, 9))
    assert raw_result["raw_result_applicability_state"] == APPLICABLE
    assert raw_result["raw_result_applicability_finalized"] is True
    assert raw_result["producer_obligation_boundary_crossed"] is True


def test_identity_survives_serialization_aggregation_and_rendering(tmp_path):
    report, raw_result = _execute_validation(tmp_path)
    applicability = _applicability(report)
    serialized = json.loads(json.dumps(report, sort_keys=True))
    renderer = DeterministicFinalReportRenderer()
    rendered_once = renderer.render(
        {
            "runtime_status": "completed",
            "RAW_RESULT_APPLICABILITY_REPORT": applicability,
            "validation_task_execution_report": serialized,
        },
        runtime_metadata={
            "run_id": report["run_id"],
            "timestamp": "2026-08-08T00:00:00",
            "mode": "adaptive",
            "runtime_status": "completed",
            "training_batch_size": 3,
        },
    )
    rendered_metrics = renderer.report()
    rendered_twice = DeterministicFinalReportRenderer().render(
        {
            "runtime_status": "completed",
            "RAW_RESULT_APPLICABILITY_REPORT": applicability,
            "validation_task_execution_report": serialized,
        },
        runtime_metadata={
            "run_id": report["run_id"],
            "timestamp": "2026-08-08T00:00:00",
            "mode": "adaptive",
            "runtime_status": "completed",
            "training_batch_size": 3,
        },
    )

    assert serialized["raw_validation_result_id"] == raw_result["raw_validation_result_id"]
    assert serialized["immutable_identity_fingerprint"] == raw_result["immutable_identity_fingerprint"]
    assert f"Canonical Raw Result Id: {report['raw_validation_result_id']}" in rendered_once
    assert f"Canonical Raw Result Id: {report['raw_validation_result_id']}" in rendered_twice
    assert "Raw Result Identity Issuance Count: 1" in rendered_once
    assert rendered_once.count(report["raw_validation_result_id"]) >= 1
    assert f"Canonical Raw Result Id: {report['raw_validation_result_id']}" in rendered_twice
    assert "Raw Result Identity Issuance Count: 1" in rendered_twice
    assert (
        rendered_metrics["raw_result_identity_lifecycle_transitions"][-1][
            "transition_name"
        ]
        == "RAW_RESULT_IDENTITY_BOUND_TO_CANONICAL_REPORT"
    )
    assert (
        rendered_metrics["raw_result_identity_lifecycle_transitions"][-1][
            "raw_result_id"
        ]
        == report["raw_validation_result_id"]
    )


def test_identical_payloads_from_distinct_attempts_do_not_collide(tmp_path):
    first, _ = _execute_validation(
        tmp_path / "first",
        run_id="run_identity_a",
        execution_plan_id="plan_identity_a",
    )
    second, _ = _execute_validation(
        tmp_path / "second",
        run_id="run_identity_b",
        execution_plan_id="plan_identity_b",
    )

    assert first["predicted_output_available"] is True
    assert second["predicted_output_available"] is True
    assert first["raw_validation_result_id"] != second["raw_validation_result_id"]
    assert first["immutable_identity_fingerprint"] != second["immutable_identity_fingerprint"]


def test_applicable_missing_artifact_does_not_receive_synthetic_identity(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan())
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )
    schedule = ValidationTaskScheduler(tmp_path, registry).schedule_plan(
        persisted["evidence_plan_id"]
    )

    class MissingOutputPipeline(ValidationTaskExecutionPipeline):
        def _run_task(self, task, schedule, plan):
            return {}

    report = MissingOutputPipeline(tmp_path, registry).execute_schedule(
        schedule["schedule_id"]
    )

    assert report["execution_state"] == "RAW_RESULT_ARTIFACT_MISSING"
    assert report["raw_result_captured"] is False
    assert report["raw_result_identity_issuance_count"] == 0
    assert report["raw_validation_result_id"] is None
    assert report["raw_result_identity_state"] == (
        "APPLICABLE_ARTIFACT_MISSING_IDENTITY_NOT_ISSUABLE"
    )
    assert report["raw_result_applicability_state"] == APPLICABLE
    assert report["raw_result_applicability_finalized"] is True
    assert report["producer_obligation_boundary_crossed"] is True


def test_undetermined_applicability_issues_no_identity():
    applicability = RawResultLifecycleApplicabilityEvaluator().evaluate(
        run_id="run_identity",
        execution_plan_id="plan_identity",
        validation_task_execution_report={
            "execution_admission_state": "ADMITTED",
            "execution_started": True,
            "execution_state": "EXECUTION_FAILED",
        },
        source_timestamp="2026-08-08T00:00:00",
    )

    assert applicability["raw_result_applicability_state"] == UNDETERMINED
    assert applicability["raw_result_required_count"] == 0


def test_empty_valid_output_gets_canonical_identity(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan())
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )
    schedule = ValidationTaskScheduler(tmp_path, registry).schedule_plan(
        persisted["evidence_plan_id"]
    )

    class EmptyValidPipeline(ValidationTaskExecutionPipeline):
        def _run_task(self, task, schedule, plan):
            return {"empty_output_valid": True, "case_outputs": []}

    report = EmptyValidPipeline(tmp_path, registry).execute_schedule(
        schedule["schedule_id"]
    )

    assert report["execution_state"] == "RAW_RESULT_EMPTY_VALID_OUTPUT_CAPTURED"
    assert report["raw_validation_result_id"].startswith("raw_validation_result_")
    assert report["raw_result_identity_issuance_count"] == 1
    assert report["raw_result_identity_state"] == "APPLICABLE_ARTIFACT_PRESENT_IDENTITY_BOUND"


def test_reobserving_same_artifact_preserves_existing_identity(tmp_path):
    report, _ = _execute_validation(tmp_path)

    second = ValidationTaskExecutionPipeline(
        tmp_path,
        _registry(tmp_path / "curriculum.json"),
    ).execute_schedule(report["schedule_id"])

    assert second["raw_result_creation_result"] == "REUSED_EXISTING_RAW_RESULT"
    assert second["raw_validation_result_id"] == report["raw_validation_result_id"]
    assert second["raw_result_identity_issuance_count"] == 1


def test_previous_run_plan_mismatch_collision_and_mutation_are_detected(tmp_path):
    report, raw_result = _execute_validation(tmp_path)
    pipeline = ValidationTaskExecutionPipeline(tmp_path, _registry(tmp_path / "curriculum.json"))

    previous = deepcopy(raw_result)
    previous["run_id"] = "previous_run"
    previous_check = pipeline.evaluate_raw_result_identity_integrity(
        previous,
        run_id=report["run_id"],
        execution_plan_id=report["execution_plan_id"],
    )
    assert previous_check["raw_result_identity_integrity_state"] == (
        "RAW_RESULT_IDENTITY_CONFLICT_DETECTED"
    )
    assert "previous_or_foreign_run_identity" in previous_check["raw_result_identity_conflicts"]

    plan_mismatch = deepcopy(raw_result)
    plan_mismatch["execution_plan_id"] = "different_plan"
    plan_check = pipeline.evaluate_raw_result_identity_integrity(
        plan_mismatch,
        run_id=report["run_id"],
        execution_plan_id=report["execution_plan_id"],
    )
    assert "execution_plan_identity_mismatch" in plan_check["raw_result_identity_conflicts"]

    collision = deepcopy(raw_result)
    collision["validation_attempt_id"] = "validation_attempt_other"
    collision_check = pipeline.evaluate_raw_result_identity_integrity(
        raw_result,
        run_id=report["run_id"],
        execution_plan_id=report["execution_plan_id"],
        observed_results=[collision],
    )
    assert "identity_collision_between_attempts" in collision_check["raw_result_identity_conflicts"]

    mutated = deepcopy(raw_result)
    mutated["RAW_VALIDATION_RESULT_ENVELOPE"]["task_id"] = "mutated_task"
    mutation_check = pipeline.evaluate_raw_result_identity_integrity(
        mutated,
        run_id=report["run_id"],
        execution_plan_id=report["execution_plan_id"],
    )
    assert "immutable_identity_fingerprint_mismatch" in mutation_check["raw_result_identity_conflicts"]
    assert mutation_check["identity_rewritten"] is False


def test_evidence_lifecycle_blocks_identity_missing_input(tmp_path):
    report, raw_result = _execute_validation(tmp_path)
    raw_result["raw_validation_result_id"] = None
    raw_result["raw_result_id"] = None
    raw_result["canonical_raw_result_id"] = None
    raw_result["RAW_VALIDATION_RESULT_ENVELOPE"] = {}
    raw_result["raw_validation_result_envelope"] = {}
    _raw_path(tmp_path, report["raw_result_id"]).write_text(
        json.dumps(raw_result),
        encoding="utf-8",
    )

    evaluation = ValidationEvidenceEvaluator(
        tmp_path,
        _registry(tmp_path / "curriculum.json"),
    ).evaluate_plan(report["plan_id"])

    assert evaluation["evaluation_admission_state"] == (
        "BLOCKED_RAW_VALIDATION_PROVENANCE_UNBOUND"
    )
    assert evaluation["recommended_action"] == (
        "repair_raw_validation_result_identity_without_evidence_evaluation"
    )
