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


def test_authoritative_creator_produces_required_substantive_categories():
    base = {
        "run_id": "run_current",
        "CANONICAL_EXECUTION_PLAN": {"execution_plan_id": "plan_current"},
    }

    no_failure = engineering_conclusion_integrity_evaluator.create_authoritative_conclusion(
        {
            **base,
            "VALIDATION_EVIDENCE_EVALUATION_REPORT": {
                "evidence_acceptance_state": "ACCEPTED",
            },
        },
        runtime_metadata={"execution_id": "run_current"},
    )
    real_failure = engineering_conclusion_integrity_evaluator.create_authoritative_conclusion(
        {
            **base,
            "failure_summary": {
                "latest_failure": {
                    "failure_detected": True,
                    "failure_causes": ["routing_overload"],
                },
            },
        },
        runtime_metadata={"execution_id": "run_current"},
    )
    pending = engineering_conclusion_integrity_evaluator.create_authoritative_conclusion(
        {
            **base,
            "VALIDATION_TASK_EXECUTION_REPORT": {
                "execution_state": "RAW_RESULT_CAPTURED",
                "raw_validation_result_id": "raw_result_current",
            },
        },
        runtime_metadata={"execution_id": "run_current"},
    )
    not_applicable = engineering_conclusion_integrity_evaluator.create_authoritative_conclusion(
        {
            **base,
            "RAW_RESULT_APPLICABILITY_REPORT": {
                "raw_result_applicability_state": "RAW_RESULT_NOT_APPLICABLE",
            },
        },
        runtime_metadata={"execution_id": "run_current"},
    )
    conflicting = engineering_conclusion_integrity_evaluator.normalize({
        "conclusion_state": "NO_FAILURE",
        "failure_reason": "none",
        "root_cause": "unexpected_root",
        "conclusion_run_id": "run_current",
        "authoritative_execution_plan_id": "plan_current",
    })

    assert no_failure["conclusion_state"] == "NO_FAILURE"
    assert real_failure["conclusion_state"] == "FAILURE"
    assert real_failure["failure_reason"] == "routing_overload"
    assert real_failure["root_cause"] == "routing_overload"
    assert pending["conclusion_state"] == "UNDETERMINED"
    assert not_applicable["conclusion_state"] == "NOT_APPLICABLE"
    assert conflicting["engineering_conclusion_integrity_state"] == (
        "ENGINEERING_CONCLUSION_CONFLICT"
    )


def test_renderer_is_projection_only_when_conclusion_missing():
    report = DeterministicFinalReportRenderer().render(
        {"runtime_status": "completed"},
        runtime_metadata={"execution_id": "run_projection_only"},
    )

    assert "Engineering Conclusion State: ENGINEERING_CONCLUSION_NOT_PRODUCED" in report
    assert "AUTHORITATIVE_ENGINEERING_CONCLUSION_FINALIZED" not in report
    assert "Root Cause: raw_validation_result_not_yet_evaluated" not in report


def test_persistence_emission_parity_and_mismatch_detection(tmp_path):
    conclusion = engineering_conclusion_integrity_evaluator.create_authoritative_conclusion(
        {
            "run_id": "run_parity",
            "CANONICAL_EXECUTION_PLAN": {"execution_plan_id": "plan_parity"},
            "VALIDATION_EVIDENCE_EVALUATION_REPORT": {
                "evidence_acceptance_state": "ACCEPTED",
            },
        },
        runtime_metadata={"execution_id": "run_parity"},
    )
    artifact = tmp_path / "engineering_conclusion.json"

    persisted = engineering_conclusion_integrity_evaluator.persist_conclusion(
        conclusion,
        artifact,
    )
    readback = engineering_conclusion_integrity_evaluator.read_persisted_conclusion(
        artifact,
    )
    parity = engineering_conclusion_integrity_evaluator.persistence_emission_parity(
        readback,
        conclusion,
    )
    mutated = {**readback, "root_cause": "default_substituted_value"}
    mutated_parity = (
        engineering_conclusion_integrity_evaluator.persistence_emission_parity(
            mutated,
            conclusion,
        )
    )
    formatting_only = {
        **readback,
        "recommended_action": "continue_with_next_governed_runtime_stage\n",
    }
    formatting_parity = (
        engineering_conclusion_integrity_evaluator.persistence_emission_parity(
            formatting_only,
            conclusion,
        )
    )

    assert persisted["persistence_integrity"] == "VERIFIED"
    assert parity["emission_integrity"] == "VERIFIED"
    assert parity["persistence_matches_emission"] is True
    assert mutated_parity["persistence_matches_emission"] is False
    assert any(
        row["field"] == "root_cause"
        for row in mutated_parity["mismatches"]
    )
    assert formatting_parity["persistence_matches_emission"] is True


def test_previous_run_and_plan_mismatched_conclusions_are_rejected():
    previous_run = engineering_conclusion_integrity_evaluator.normalize(
        {
            "conclusion_state": "NO_FAILURE",
            "failure_reason": "none",
            "root_cause": "none",
            "conclusion_run_id": "run_previous",
            "authoritative_execution_plan_id": "plan_current",
        },
        report_state={
            "run_id": "run_current",
            "CANONICAL_EXECUTION_PLAN": {"execution_plan_id": "plan_current"},
        },
        runtime_metadata={"execution_id": "run_current"},
    )
    plan_mismatch = engineering_conclusion_integrity_evaluator.normalize(
        {
            "conclusion_state": "NO_FAILURE",
            "failure_reason": "none",
            "root_cause": "none",
            "conclusion_run_id": "run_current",
            "authoritative_execution_plan_id": "plan_previous",
        },
        report_state={
            "run_id": "run_current",
            "CANONICAL_EXECUTION_PLAN": {"execution_plan_id": "plan_current"},
        },
        runtime_metadata={"execution_id": "run_current"},
    )

    assert previous_run["current_run_binding_state"] == "PREVIOUS_RUN_REJECTED"
    assert previous_run["engineering_conclusion_integrity_state"] == (
        "ENGINEERING_CONCLUSION_CONFLICT"
    )
    assert plan_mismatch["current_run_binding_state"] == (
        "EXECUTION_PLAN_MISMATCH_REJECTED"
    )
    assert "execution_plan_id_mismatch_rejected" in plan_mismatch["integrity_conflicts"]


def test_human_report_conflict_attribution_excludes_engineering_conclusion():
    report = DeterministicFinalReportRenderer().render(
        {
            "runtime_status": "completed",
            "run_id": "run_conflicting_state",
            "ENGINEERING_CONCLUSION": {
                "conclusion_state": "NO_FAILURE",
                "failure_reason": "none",
                "root_cause": "none",
                "conclusion_run_id": "run_runtime",
            },
        },
        runtime_metadata={
            "execution_id": "run_runtime",
            "timestamp": "2026-08-08T02:00:01",
            "mode": "adaptive",
        },
    )

    assert "Human Report Canonical Binding Integrity: CONFLICTED" in report
    assert "Engineering Conclusion Binding Conflict Count: 0" in report
    assert "Engineering Conclusion Projection Divergence Count: 0" in report
    assert "engineering_conclusion_related=FALSE" in report
