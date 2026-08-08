from runtime.reporting.active_runtime_reachability_audit import (
    build_active_runtime_reachability_audit,
)
from runtime.reporting.engineering_conclusion_integrity import (
    engineering_conclusion_integrity_evaluator,
)
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def test_engineering_conclusion_binding_preserves_canonical_fingerprint():
    state = {
        "run_id": "run_20260808_020000",
        "CANONICAL_EXECUTION_PLAN": {
            "execution_plan_id": "execution_plan_run_20260808_020000",
        },
        "ENGINEERING_CONCLUSION": {
            "largest_success": "scheduled_validation_task_executed",
            "largest_regression": "none",
            "root_cause": "raw_result_not_applicable",
            "next_task": "continue_with_next_governed_runtime_stage",
            "conclusion_task_id": "semantic_to_transformation_compiler_0",
            "conclusion_is_current": True,
        },
    }

    ensured = engineering_conclusion_integrity_evaluator.ensure_authoritative_conclusion(
        state,
        runtime_metadata={"execution_id": "run_20260808_020000"},
    )
    conclusion = ensured["ENGINEERING_CONCLUSION"]

    assert conclusion["engineering_conclusion_state"] == (
        "AUTHORITATIVE_ENGINEERING_CONCLUSION_FINALIZED"
    )
    assert conclusion["engineering_conclusion_integrity_state"] == (
        "ENGINEERING_CONCLUSION_INTEGRITY_VERIFIED"
    )
    assert conclusion["authoritative_run_id"] == "run_20260808_020000"
    assert conclusion["authoritative_execution_plan_id"] == (
        "execution_plan_run_20260808_020000"
    )
    assert conclusion["pre_reconciliation_fingerprint"] == (
        conclusion["post_reconciliation_fingerprint"]
    )


def test_human_report_exposes_authoritative_engineering_conclusion_fields():
    state = {
        "runtime_status": "completed",
        "run_id": "run_20260808_020001",
        "CANONICAL_EXECUTION_PLAN": {
            "execution_plan_id": "execution_plan_run_20260808_020001",
        },
        "ENGINEERING_CONCLUSION": {
            "largest_success": "scheduled_validation_task_executed",
            "largest_regression": "none",
            "current_open_decision": "none",
            "next_decision_gate": "continue_with_next_governed_runtime_stage",
            "root_cause": "raw_result_not_applicable",
            "responsible_component": "VALIDATION_EXECUTION_PIPELINE",
            "next_task": "continue_with_next_governed_runtime_stage",
            "conclusion_task_id": "semantic_to_transformation_compiler_0",
            "conclusion_is_current": True,
        },
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata={
            "execution_id": "run_20260808_020001",
            "timestamp": "2026-08-08T02:00:01",
            "mode": "adaptive",
            "training_batch_size": 3,
        },
    )

    assert "Engineering Conclusion State: AUTHORITATIVE_ENGINEERING_CONCLUSION_FINALIZED" in report
    assert "Engineering Conclusion Integrity State: ENGINEERING_CONCLUSION_INTEGRITY_VERIFIED" in report
    assert "Conclusion Evaluation Source: engineering_conclusion_integrity_evaluator" in report
    assert "Authoritative Run Id: run_20260808_020001" in report
    assert "Authoritative Execution Plan Id: execution_plan_run_20260808_020001" in report
    assert "Persistence Applicability: PERSISTENCE_NOT_APPLICABLE" in report
    assert "Conclusion Conflict Count: 0" in report


def test_active_runtime_audit_uses_canonical_engineering_conclusion_integrity():
    audit = build_active_runtime_reachability_audit({
        "ENGINEERING_CONCLUSION": {
            "integrity": "INVALID",
            "conclusion_is_current": True,
            "integrity_conflicts": ["explicit_integrity_failure"],
        }
    })

    assert "ENGINEERING_CONCLUSION_CONFLICT" in audit["reachability_gaps"]
    assert audit["engineering_conclusion_state"] == "ENGINEERING_CONCLUSION_CONFLICT"
