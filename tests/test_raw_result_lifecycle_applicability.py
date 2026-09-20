from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer
from runtime.validation.raw_result_lifecycle_applicability import (
    APPLICABLE,
    NOT_APPLICABLE,
    UNDETERMINED,
    RawResultLifecycleApplicabilityEvaluator,
)


def _evaluate(**overrides):
    base = {
        "run_id": "run_app",
        "execution_plan_id": "plan_app",
        "task_id": "task_app",
        "validation_task_execution_report": {},
        "validation_scheduling_report": {},
        "route_lifecycle_records": [],
        "reasoning_depth_lifecycle_records": [],
        "source_timestamp": "2026-08-08T00:00:00",
    }
    base.update(overrides)
    return RawResultLifecycleApplicabilityEvaluator().evaluate(**base)


def test_no_qualifying_producer_is_not_applicable_before_lifecycle_checks():
    report = _evaluate()

    assert report["raw_result_applicability_state"] == NOT_APPLICABLE
    assert report["raw_result_producer_obligation_count"] == 0
    assert report["applicable_raw_result_missing_count"] == 0
    assert report["raw_result_lifecycle_completeness_state"] == "NOT_EVALUATED_NOT_APPLICABLE"
    transition_names = [
        row["transition_name"] for row in report["lifecycle_transitions"]
    ]
    assert transition_names.index("RAW_RESULT_APPLICABILITY_FINALIZED") < 3


def test_admitted_started_validation_is_applicable_with_present_raw_result():
    report = _evaluate(
        validation_task_execution_report={
            "run_id": "run_app",
            "execution_plan_id": "plan_app",
            "execution_id": "validation_execution_1",
            "execution_admission_state": "ADMITTED",
            "execution_started": True,
            "execution_state": "RAW_RESULT_CAPTURED",
            "raw_validation_result_id": "raw_validation_result_1",
            "validation_attempt_id": "validation_attempt_1",
        }
    )
    decision = report["operation_applicability_decisions"][0]

    assert report["raw_result_applicability_state"] == APPLICABLE
    assert report["raw_result_required_count"] == 1
    assert report["applicable_raw_result_present_count"] == 1
    assert report["applicable_raw_result_missing_count"] == 0
    assert decision["producer_contract"] == "VALIDATION_TASK_EXECUTION_PIPELINE_RAW_RESULT_CAPTURE"


def test_applicable_missing_raw_result_remains_applicable_and_visible():
    report = _evaluate(
        validation_task_execution_report={
            "run_id": "run_app",
            "execution_plan_id": "plan_app",
            "execution_id": "validation_execution_2",
            "execution_admission_state": "ADMITTED",
            "execution_started": True,
            "execution_state": "RAW_RESULT_ARTIFACT_MISSING",
            "raw_validation_result_id": "raw_validation_result_2",
        }
    )

    assert report["raw_result_applicability_state"] == APPLICABLE
    assert report["applicable_raw_result_missing_count"] == 1
    assert report["raw_result_lifecycle_completeness_state"] == (
        "RAW_RESULT_LIFECYCLE_APPLICABLE_RESULT_MISSING"
    )


def test_artifact_absence_alone_does_not_create_not_applicable_when_boundary_crossed():
    report = _evaluate(
        validation_task_execution_report={
            "run_id": "run_app",
            "execution_plan_id": "plan_app",
            "execution_admission_state": "ADMITTED",
            "execution_started": True,
            "execution_state": "EXECUTION_FAILED",
        }
    )

    assert report["raw_result_applicability_state"] == APPLICABLE
    assert report["raw_result_required_count"] == 1


def test_artifact_presence_without_current_run_lineage_is_undetermined():
    report = _evaluate(
        validation_task_execution_report={
            "run_id": "previous_run",
            "execution_plan_id": "previous_plan",
            "execution_state": "RAW_RESULT_CAPTURED",
            "raw_validation_result_id": "raw_validation_result_previous",
        }
    )

    assert report["raw_result_applicability_state"] == NOT_APPLICABLE
    assert report["raw_result_required_count"] == 0
    assert report["operation_applicability_decisions"][0]["raw_result_required"] is False


def test_started_producer_with_missing_current_run_provenance_is_undetermined():
    report = _evaluate(
        validation_task_execution_report={
            "execution_admission_state": "ADMITTED",
            "execution_started": True,
            "execution_state": "EXECUTION_FAILED",
        }
    )

    assert report["raw_result_applicability_state"] == UNDETERMINED
    assert report["undetermined_operation_count"] == 1


def test_pre_obligation_stops_do_not_create_raw_result_obligations():
    report = _evaluate(
        route_lifecycle_records=[
            {"route_id": "route_3", "state": "DEFERRED_BY_BUDGET"},
            {"route_id": "route_4", "state": "REJECTED_BY_BUDGET"},
        ],
        reasoning_depth_lifecycle_records=[
            {"depth": 3, "state": "DEPTH_ENTRY_BLOCKED_BY_BUDGET"},
        ],
    )

    assert report["raw_result_applicability_state"] == NOT_APPLICABLE
    assert report["pre_obligation_deferred_count"] == 1
    assert report["pre_obligation_blocked_count"] == 2
    assert report["raw_result_producer_obligation_count"] == 0


def test_diagnostic_probe_and_solver_output_are_not_canonical_raw_results():
    report = _evaluate(
        validation_scheduling_report={
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
            "validation_probe_candidate_id": "probe_1",
        },
        validation_task_execution_report={
            "evaluation_result": {"accuracy": 0.9},
            "predicted_output": [[1]],
        },
    )

    assert report["raw_result_applicability_state"] == NOT_APPLICABLE
    assert report["raw_result_required_count"] == 0


def test_applicability_decision_preserves_run_and_plan_identity():
    report = _evaluate()

    assert report["run_id"] == "run_app"
    assert report["execution_plan_id"] == "plan_app"
    assert report["authoritative_execution_plan_id"] == "plan_app"
    for decision in report["operation_applicability_decisions"]:
        assert decision["run_id"] == "run_app"
        assert decision["execution_plan_id"] == "plan_app"


def test_human_report_renders_applicability_before_raw_result_state():
    applicability = _evaluate()
    rendered = DeterministicFinalReportRenderer().render(
        {
            "runtime_status": "completed",
            "RAW_RESULT_APPLICABILITY_REPORT": applicability,
            "validation_task_execution_report": {},
            "ENGINEERING_CONCLUSION": {},
        },
        runtime_metadata={
            "run_id": "run_app",
            "timestamp": "2026-08-08T00:00:00",
            "mode": "adaptive",
            "runtime_status": "completed",
            "training_batch_size": 3,
        },
    )

    assert rendered.index("Raw Result Applicability State") < rendered.index("Raw Result State")
    assert "Raw Result Applicability State: RAW_RESULT_NOT_APPLICABLE" in rendered
    assert "Raw Result Producer Obligation Count: 0" in rendered
    assert "Applicable Raw Result Missing Count: 0" in rendered
    assert "Raw Result Lifecycle Completeness: NOT_EVALUATED_NOT_APPLICABLE" in rendered
    assert "Raw Result State: RAW_RESULT_NOT_APPLICABLE" in rendered
    assert "Raw Validation Result Id: RAW_VALIDATION_RESULT_ID_NOT_ISSUED" not in rendered
    assert "RAW_RESULT_ENVELOPE_INCOMPLETE" not in rendered


def test_bound_applicability_report_records_canonical_binding_transition():
    evaluator = RawResultLifecycleApplicabilityEvaluator()
    report = _evaluate()
    bound = evaluator.bind_to_canonical_report(report)

    assert bound["canonical_binding_state"] == "RAW_RESULT_APPLICABILITY_BOUND_TO_CANONICAL_REPORT"
    assert bound["lifecycle_transitions"][-1]["transition_name"] == (
        "RAW_RESULT_APPLICABILITY_BOUND_TO_CANONICAL_REPORT"
    )
