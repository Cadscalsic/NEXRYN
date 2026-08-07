from runtime.learning.training_report import build_training_report
import runtime.learning.training_report as training_report_module
from runtime.reporting.active_runtime_reachability_audit import (
    build_active_runtime_reachability_audit,
    mark_active_runtime_audit_attached_to_run,
    mark_active_runtime_audit_bound_to_canonical_report,
)
from runtime.reporting.final_report_renderer import final_report_renderer


def test_active_runtime_reachability_audit_detects_reported_gaps():
    report_state = {
        "run_id": "run_reachability",
        "task_id": "elite_cognitive_task_12",
        "reasoning_depth": 4,
        "active_routes": 12,
        "retry_allowed": True,
        "episode_completed": False,
        "repair_required": True,
        "repair_attempts": 0,
        "RUNTIME_BUDGET_ENFORCEMENT_REPORT": {
            "runtime_budget_state": "RUNTIME_BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE",
            "maximum_active_routes": 2,
            "peak_concurrent_active_route_count": 12,
            "maximum_reasoning_depth": 2,
            "maximum_entered_reasoning_depth": 4,
        },
        "VALIDATION_TASK_EXECUTION_REPORT": {
            "execution_state": "RAW_RESULT_CAPTURED",
            "raw_validation_result_id": "NOT_ISSUED",
        },
        "ENGINEERING_CONCLUSION": {
            "largest_success": "scheduled_validation_task_executed_and_raw_result_contained",
        },
    }

    audit = build_active_runtime_reachability_audit(report_state)

    assert audit["audit_state"] == "REACHABILITY_GAPS_DETECTED"
    assert "CANONICAL_EXECUTION_PLAN_NOT_BOUND" in audit["reachability_gaps"]
    assert "BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE" in audit["reachability_gaps"]
    assert "RUNTIME_BUDGET_EXCEEDED_UNREPORTED" in audit["reachability_gaps"]
    assert "RETRY_ALLOWED_REPAIR_NOT_ATTEMPTED" in audit["reachability_gaps"]
    assert "RAW_RESULT_CAPTURED_WITHOUT_IDENTITY" in audit["reachability_gaps"]
    assert audit["repair_reachability_state"] == "REPAIR_REACHABILITY_BLOCKED"
    assert audit["raw_result_identity_state"] == "RAW_RESULT_IDENTITY_MISSING"


def test_active_runtime_reachability_audit_reports_clear_state_for_bound_runtime():
    report_state = {
        "run_id": "run_clear",
        "task_id": "task_clear",
        "CANONICAL_EXECUTION_PLAN_REPORT": {
            "execution_plan_id": "execution_plan_run_clear_task_clear",
            "run_id": "run_clear",
            "task_id": "task_clear",
            "active_route_count": 2,
        },
        "RUNTIME_BUDGET_ENFORCEMENT_REPORT": {
            "runtime_budget_state": "RUNTIME_BUDGET_FINALIZED",
            "maximum_active_routes": 2,
            "peak_concurrent_active_route_count": 2,
            "maximum_reasoning_depth": 2,
            "maximum_entered_reasoning_depth": 2,
        },
        "VALIDATION_TASK_EXECUTION_REPORT": {
            "execution_state": "RAW_RESULT_CAPTURED",
            "raw_validation_result_id": "raw_validation_result_123",
        },
        "ENGINEERING_CONCLUSION": {"largest_success": "none"},
    }

    audit = build_active_runtime_reachability_audit(report_state)

    assert audit["audit_state"] == "REACHABILITY_CLEAR"
    assert audit["reachability_gaps"] == []
    assert audit["canonical_execution_plan_present"] is True
    assert audit["budget_exceeded_detected"] is False
    assert audit["raw_result_identity_state"] == "RAW_RESULT_IDENTITY_CLEAR"


def test_bound_plan_removes_only_canonical_binding_gap():
    report_state = {
        "run_id": "run_reachability",
        "task_id": "task_reachability",
        "CANONICAL_EXECUTION_PLAN_REPORT": {
            "execution_plan_id": "execution_plan_run_reachability_task_reachability",
            "run_id": "run_reachability",
            "task_id": "task_reachability",
        },
        "RUNTIME_BUDGET_ENFORCEMENT_REPORT": {
            "runtime_budget_state": "RUNTIME_BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE",
            "maximum_active_routes": 2,
            "peak_concurrent_active_route_count": 12,
        },
        "retry_allowed": True,
        "episode_completed": False,
        "repair_required": True,
        "repair_attempts": 0,
        "VALIDATION_TASK_EXECUTION_REPORT": {
            "execution_state": "RAW_RESULT_CAPTURED",
            "raw_validation_result_id": "NOT_ISSUED",
        },
    }

    audit = build_active_runtime_reachability_audit(report_state)

    assert "CANONICAL_EXECUTION_PLAN_NOT_BOUND" not in audit["reachability_gaps"]
    assert "RUNTIME_BUDGET_EXCEEDED_UNREPORTED" in audit["reachability_gaps"]
    assert "RETRY_ALLOWED_REPAIR_NOT_ATTEMPTED" in audit["reachability_gaps"]
    assert "RAW_RESULT_CAPTURED_WITHOUT_IDENTITY" in audit["reachability_gaps"]
    assert audit["execution_plan_id"] == "execution_plan_run_reachability_task_reachability"


def test_run_and_task_mismatched_plans_are_not_bound_as_current():
    run_mismatch = build_active_runtime_reachability_audit({
        "run_id": "current_run",
        "CANONICAL_EXECUTION_PLAN_REPORT": {
            "execution_plan_id": "execution_plan_old",
            "run_id": "old_run",
            "task_id": "task_a",
        },
    })
    task_mismatch = build_active_runtime_reachability_audit({
        "run_id": "current_run",
        "task_id": "current_task",
        "CANONICAL_EXECUTION_PLAN_REPORT": {
            "execution_plan_id": "execution_plan_other_task",
            "run_id": "current_run",
            "task_id": "other_task",
        },
    })

    assert run_mismatch["canonical_execution_plan_present"] is False
    assert run_mismatch["execution_plan_identity_state"] == "PLAN_RUN_ID_MISMATCH"
    assert "CANONICAL_EXECUTION_PLAN_RUN_ID_MISMATCH" in run_mismatch["reachability_gaps"]
    assert task_mismatch["canonical_execution_plan_present"] is False
    assert task_mismatch["execution_plan_identity_state"] == "PLAN_TASK_ID_MISMATCH"
    assert "CANONICAL_EXECUTION_PLAN_TASK_ID_MISMATCH" in task_mismatch["reachability_gaps"]


def test_task_runtime_telemetry_prevents_false_clear_and_zero_zero_budget():
    audit = build_active_runtime_reachability_audit(
        {"run_id": "run_task_telemetry"},
        task_results=[
            {
                "task": "elite_cognitive_task_12",
                "status": "failed",
                "result": {
                    "cognitive_budget_report": {
                        "max_active_routes": 2,
                        "max_reasoning_depth": 2,
                        "max_dependency_depth": 2,
                        "max_hypotheses": 0,
                    },
                    "evaluation_result": {
                        "retry_allowed": True,
                        "episode_completed": False,
                    },
                    "introspection_report": {
                        "latest_report": {
                            "reasoning_depth": 4,
                            "active_routes": 12,
                            "pipeline_activity": {
                                "route_count": 12,
                                "reasoning_depth": 4,
                            },
                        }
                    },
                    "evaluation_metrics": {"repair_attempts": 0},
                    "residual_analysis": {"residual_count": 3},
                },
            }
        ],
    )

    assert audit["task_runtime_telemetry_present"] is True
    assert audit["task_budget_snapshot_present"] is True
    assert audit["declared_max_active_routes"] == 2
    assert audit["declared_active_routes"] == 2
    assert audit["observed_active_routes"] == 12
    assert audit["declared_max_reasoning_depth"] == 2
    assert audit["declared_reasoning_depth"] == 2
    assert audit["observed_reasoning_depth"] == 4
    assert audit["budget_exceeded_detected"] is True
    assert "RUNTIME_BUDGET_EXCEEDED_UNREPORTED" in audit["reachability_gaps"]
    assert "RETRY_ALLOWED_REPAIR_NOT_ATTEMPTED" in audit["reachability_gaps"]
    assert audit["repair_reachability_state"] == "REPAIR_REACHABILITY_BLOCKED"
    assert audit["recommended_next_fix"] == "repair_canonical_execution_plan_active_runtime_binding"


def test_retry_allowed_without_repair_applicability_does_not_emit_repair_gap():
    audit = build_active_runtime_reachability_audit({
        "retry_allowed": True,
        "episode_completed": False,
        "repair_attempts": 0,
    })

    assert "RETRY_ALLOWED_REPAIR_NOT_ATTEMPTED" not in audit["reachability_gaps"]
    assert audit["repair_reachability_state"] == "REPAIR_REACHABILITY_CLEAR"


def test_raw_result_identity_missing_detected_from_main_results_lowercase_report():
    audit = build_active_runtime_reachability_audit({
        "validation_task_execution_report": {
            "execution_state": "RAW_RESULT_CAPTURED",
            "raw_validation_result_id": "RAW_VALIDATION_RESULT_ID_NOT_ISSUED",
        }
    })

    assert "RAW_RESULT_CAPTURED_WITHOUT_IDENTITY" in audit["reachability_gaps"]
    assert audit["raw_result_identity_state"] == "RAW_RESULT_IDENTITY_MISSING"


def test_issued_raw_result_identity_does_not_emit_missing_identity_gap():
    audit = build_active_runtime_reachability_audit({
        "validation_task_execution_report": {
            "execution_state": "RAW_RESULT_CAPTURED",
            "raw_validation_result_id": "raw_validation_result_abc123",
        }
    })

    assert "RAW_RESULT_CAPTURED_WITHOUT_IDENTITY" not in audit["reachability_gaps"]
    assert audit["raw_result_identity_state"] == "RAW_RESULT_IDENTITY_CLEAR"


def test_invalid_current_engineering_conclusion_emits_conflict():
    audit = build_active_runtime_reachability_audit({
        "ENGINEERING_CONCLUSION": {
            "integrity": "INVALID",
            "conclusion_is_current": True,
            "integrity_conflicts": [
                "failure_reason=none conflicts with non_none_root_cause"
            ],
        }
    })

    assert "ENGINEERING_CONCLUSION_CONFLICT" in audit["reachability_gaps"]
    assert audit["engineering_conclusion_state"] == "ENGINEERING_CONCLUSION_CONFLICT"


def test_valid_current_engineering_conclusion_does_not_emit_conflict():
    audit = build_active_runtime_reachability_audit({
        "ENGINEERING_CONCLUSION": {
            "integrity": "VALID",
            "conclusion_is_current": True,
            "integrity_conflicts": [],
        }
    })

    assert "ENGINEERING_CONCLUSION_CONFLICT" not in audit["reachability_gaps"]
    assert audit["engineering_conclusion_state"] == "ENGINEERING_CONCLUSION_NOT_CONFLICTING"


def test_audit_identity_and_lifecycle_are_stable():
    audit = build_active_runtime_reachability_audit({
        "ENGINEERING_CONCLUSION": {
            "conclusion_run_id": "run_20260807_013057",
            "conclusion_task_id": "task_31",
            "conclusion_source_timestamp": "2026-08-07T01:30:57",
        }
    })

    assert audit["audit_id"].startswith("active_runtime_reachability_audit_")
    assert audit["audit_schema_version"] == "1.0"
    assert audit["audit_run_id"] == "run_20260807_013057"
    assert audit["is_current_run"] is True
    transitions = audit["lifecycle_transitions"]
    assert [row["state"] for row in transitions] == [
        "ACTIVE_RUNTIME_AUDIT_BUILD_REQUESTED",
        "ACTIVE_RUNTIME_AUDIT_BUILD_COMPLETED",
    ]
    assert {row["audit_id"] for row in transitions} == {audit["audit_id"]}
    assert {row["run_id"] for row in transitions} == {"run_20260807_013057"}
    assert audit["audit_lifecycle_integrity_state"] == "AUDIT_LIFECYCLE_INCOMPLETE"


def test_audit_lifecycle_attach_and_bound_preserve_identity_and_order():
    built = build_active_runtime_reachability_audit({
        "ENGINEERING_CONCLUSION": {
            "conclusion_run_id": "run_lifecycle",
            "conclusion_task_id": "task_lifecycle",
            "conclusion_source_timestamp": "2026-08-07T02:09:42",
        }
    })
    attached = mark_active_runtime_audit_attached_to_run(built)
    bound = mark_active_runtime_audit_bound_to_canonical_report(attached)

    transitions = bound["lifecycle_transitions"]

    assert [row["transition_name"] for row in transitions] == [
        "ACTIVE_RUNTIME_AUDIT_BUILD_REQUESTED",
        "ACTIVE_RUNTIME_AUDIT_BUILD_COMPLETED",
        "ACTIVE_RUNTIME_AUDIT_ATTACHED_TO_RUN",
        "ACTIVE_RUNTIME_AUDIT_BOUND_TO_CANONICAL_REPORT",
    ]
    assert [row["sequence_index"] for row in transitions] == [1, 2, 3, 4]
    assert {row["audit_id"] for row in transitions} == {built["audit_id"]}
    assert {row["audit_schema_version"] for row in transitions} == {"1.0"}
    assert {row["run_id"] for row in transitions} == {"run_lifecycle"}
    assert bound["audit_id"] == built["audit_id"]
    assert bound["audit_lifecycle_integrity_state"] == "AUDIT_LIFECYCLE_COMPLETE"
    assert bound["audit_lifecycle_order_state"] == "AUDIT_LIFECYCLE_ORDER_VALID"
    assert bound["audit_lifecycle_identity_state"] == "AUDIT_LIFECYCLE_IDENTITY_STABLE"


def test_missing_or_out_of_order_lifecycle_is_not_reported_complete():
    built = build_active_runtime_reachability_audit({
        "ENGINEERING_CONCLUSION": {
            "conclusion_run_id": "run_lifecycle_bad",
        }
    })
    out_of_order = {
        **built,
        "lifecycle_transitions": [
            built["lifecycle_transitions"][1],
            built["lifecycle_transitions"][0],
        ],
    }
    checked = mark_active_runtime_audit_bound_to_canonical_report(out_of_order)

    assert built["audit_lifecycle_integrity_state"] == "AUDIT_LIFECYCLE_INCOMPLETE"
    assert checked["audit_lifecycle_integrity_state"] == "AUDIT_LIFECYCLE_INCOMPLETE"
    assert checked["audit_lifecycle_order_state"] == "AUDIT_LIFECYCLE_ORDER_INVALID"


def test_training_report_attaches_active_runtime_reachability_audit():
    report = build_training_report(
        training_batch={"selected_task_count": 1},
        multi_task_results=[
            {
                "task": "legacy_task.json",
                "status": "completed",
                "result": {},
            }
        ],
    )

    assert "ACTIVE_RUNTIME_REACHABILITY_AUDIT" in report
    assert report["active_runtime_reachability_audit"] == report[
        "ACTIVE_RUNTIME_REACHABILITY_AUDIT"
    ]


def test_training_report_invokes_active_runtime_audit_builder_once(monkeypatch):
    calls = []
    original = training_report_module.build_active_runtime_reachability_audit

    def counted(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(
        training_report_module,
        "build_active_runtime_reachability_audit",
        counted,
    )

    build_training_report(
        training_batch={"selected_task_count": 1},
        multi_task_results=[
            {
                "task": "elite_cognitive_task_12",
                "status": "failed",
                "result": {
                    "cognitive_budget_report": {
                        "max_active_routes": 2,
                        "max_reasoning_depth": 2,
                    },
                    "introspection_report": {
                        "latest_report": {
                            "active_routes": 12,
                            "reasoning_depth": 4,
                        }
                    },
                },
            }
        ],
    )

    assert len(calls) == 1


def test_training_report_materializes_active_runtime_plan_and_budget_from_telemetry():
    report = build_training_report(
        training_batch={"selected_task_count": 1},
        multi_task_results=[
            {
                "task": "elite_cognitive_task_12",
                "status": "failed",
                "result": {
                    "cognitive_budget_report": {
                        "max_active_routes": 2,
                        "max_reasoning_depth": 2,
                    },
                    "introspection_report": {
                        "latest_report": {
                            "active_routes": 12,
                            "reasoning_depth": 4,
                        }
                    },
                    "evaluation_result": {
                        "retry_allowed": True,
                        "episode_completed": False,
                    },
                    "evaluation_metrics": {"repair_attempts": 0},
                },
            }
        ],
    )

    audit = report["ACTIVE_RUNTIME_REACHABILITY_AUDIT"]

    assert report["canonical_execution_plan"]["execution_plan_id"].startswith(
        "execution_plan_active_runtime_"
    )
    assert report["RUNTIME_BUDGET_ENFORCEMENT_REPORT"][
        "runtime_budget_state"
    ] == "RUNTIME_BUDGET_INTEGRITY_FAILED"
    assert audit["canonical_execution_plan_present"] is True
    assert audit["budget_report_present"] is True
    assert "CANONICAL_EXECUTION_PLAN_NOT_BOUND" not in audit["reachability_gaps"]
    assert "BUDGET_ENFORCEMENT_REPORT_NOT_BOUND" not in audit["reachability_gaps"]
    assert "BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE" not in audit["reachability_gaps"]
    assert "RUNTIME_BUDGET_EXCEEDED_UNREPORTED" not in audit["reachability_gaps"]


def test_human_report_renders_active_runtime_reachability_section():
    rendered = final_report_renderer.render(
        {
            "runtime_status": "completed",
            "operation": "training_batch",
            "ACTIVE_RUNTIME_REACHABILITY_AUDIT": {
                "audit_state": "REACHABILITY_GAPS_DETECTED",
                "audit_id": "active_runtime_reachability_audit_test",
                "audit_schema_version": "1.0",
                "audit_run_id": "run_reachability",
                "source_stage": "active_runtime_reachability_audit",
                "source_timestamp": "now",
                "is_current_run": True,
                "canonical_execution_plan_present": False,
                "budget_report_present": True,
                "task_runtime_telemetry_present": True,
                "task_budget_snapshot_present": True,
                "budget_state": "RUNTIME_BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE",
                "budget_exceeded_detected": True,
                "declared_max_active_routes": 2,
                "observed_active_routes": 12,
                "declared_max_reasoning_depth": 2,
                "observed_reasoning_depth": 4,
                "repair_reachability_state": "REPAIR_REACHABILITY_BLOCKED",
                "raw_result_identity_state": "RAW_RESULT_IDENTITY_MISSING",
                "engineering_conclusion_state": "ENGINEERING_CONCLUSION_CONFLICT",
                "reachability_gap_count": 3,
                "reachability_gaps": [
                    "RUNTIME_BUDGET_EXCEEDED_UNREPORTED",
                    "RETRY_ALLOWED_REPAIR_NOT_ATTEMPTED",
                    "RAW_RESULT_CAPTURED_WITHOUT_IDENTITY",
                ],
                "recommended_next_fix": "repair_active_runtime_reachability_gaps",
            },
            "ENGINEERING_CONCLUSION": {"current_open_decision": "none"},
        },
        runtime_metadata={
            "execution_id": "run_reachability",
            "timestamp": "now",
            "mode": "test",
        },
    )

    assert "ACTIVE RUNTIME REACHABILITY" in rendered
    assert "Audit State: REACHABILITY_GAPS_DETECTED" in rendered
    assert "Audit Id: active_runtime_reachability_audit_test" in rendered
    assert "Declared/Observed Active Routes: 2/12" in rendered
    assert "Declared/Observed Reasoning Depth: 2/4" in rendered
    assert "Raw Result Identity State: RAW_RESULT_IDENTITY_CLEAR" in rendered
    assert "Task Runtime Telemetry Present: TRUE" in rendered
    assert "Audit Lifecycle Integrity State: AUDIT_LIFECYCLE_INCOMPLETE" in rendered
    assert "ACTIVE_RUNTIME_AUDIT_BOUND_TO_CANONICAL_REPORT" in rendered
    assert "RUNTIME_BUDGET_EXCEEDED_UNREPORTED" in rendered


def test_human_report_reads_reachability_audit_from_nested_training_report():
    rendered = final_report_renderer.render(
        {
            "runtime_status": "completed",
            "training_report": {
                "ACTIVE_RUNTIME_REACHABILITY_AUDIT": {
                    "audit_state": "REACHABILITY_CLEAR",
                    "execution_plan_id": "execution_plan_nested",
                    "execution_plan_identity_state": "PLAN_IDENTITY_CURRENT",
                    "canonical_execution_plan_present": True,
                    "budget_report_present": True,
                    "budget_state": "RUNTIME_BUDGET_FINALIZED",
                    "budget_exceeded_detected": False,
                    "repair_reachability_state": "REPAIR_REACHABILITY_CLEAR",
                    "raw_result_identity_state": "RAW_RESULT_IDENTITY_CLEAR",
                    "engineering_conclusion_state": "ENGINEERING_CONCLUSION_NOT_CONFLICTING",
                    "reachability_gap_count": 0,
                    "reachability_gaps": [],
                    "recommended_next_fix": "continue_with_next_governed_runtime_stage",
                }
            },
            "ENGINEERING_CONCLUSION": {"current_open_decision": "none"},
        },
        runtime_metadata={
            "execution_id": "run_nested",
            "timestamp": "now",
            "mode": "test",
        },
    )

    assert "Audit State: REACHABILITY_CLEAR" in rendered
    assert "Execution Plan Id: execution_plan_nested" in rendered
    assert "ACTIVE_RUNTIME_AUDIT_BOUND_TO_CANONICAL_REPORT" in rendered
    assert "AUDIT_NOT_PRODUCED" not in rendered


def test_renderer_binds_raw_identity_and_conclusion_lineage_after_audit_build():
    rendered = final_report_renderer.render(
        {
            "runtime_status": "completed",
            "validation_task_execution_report": {
                "execution_state": "RAW_RESULT_CAPTURED",
                "raw_validation_result_id": "RAW_VALIDATION_RESULT_ID_NOT_ISSUED",
            },
            "ACTIVE_RUNTIME_REACHABILITY_AUDIT": {
                "audit_state": "REACHABILITY_GAPS_DETECTED",
                "audit_id": "active_runtime_reachability_audit_late_binding",
                "audit_schema_version": "1.0",
                "audit_run_id": "RUN_ID_UNBOUND",
                "source_stage": "active_runtime_reachability_audit",
                "source_timestamp": "TIMESTAMP_UNBOUND",
                "is_current_run": True,
                "canonical_execution_plan_present": False,
                "budget_report_present": False,
                "task_runtime_telemetry_present": True,
                "task_budget_snapshot_present": True,
                "budget_state": "RUNTIME_BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE",
                "budget_exceeded_detected": True,
                "declared_active_routes": 2,
                "observed_active_routes": 12,
                "declared_reasoning_depth": 2,
                "observed_reasoning_depth": 4,
                "repair_reachability_state": "REPAIR_REACHABILITY_BLOCKED",
                "raw_result_identity_state": "RAW_RESULT_IDENTITY_CLEAR",
                "engineering_conclusion_state": "ENGINEERING_CONCLUSION_NOT_CONFLICTING",
                "reachability_gap_count": 5,
                "reachability_gaps": [
                    "CANONICAL_EXECUTION_PLAN_NOT_BOUND",
                    "BUDGET_ENFORCEMENT_REPORT_NOT_BOUND",
                    "BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE",
                    "RUNTIME_BUDGET_EXCEEDED_UNREPORTED",
                    "RETRY_ALLOWED_REPAIR_NOT_ATTEMPTED",
                ],
                "recommended_next_fix": "repair_canonical_execution_plan_active_runtime_binding",
            },
        },
        runtime_metadata={
            "timestamp": "2026-08-07 01:43:52.007136",
            "mode": "test",
        },
    )

    assert "Audit Run Id: RUN_ID_UNBOUND" not in rendered
    assert "Audit Source Timestamp: 2026-08-07 01:43:52.007136" in rendered
    assert "Raw Result State: RAW_RESULT_ENVELOPE_INCOMPLETE" in rendered
    assert "Raw Result Identity State: RAW_RESULT_IDENTITY_CLEAR" in rendered
    assert "RAW_RESULT_CAPTURED_WITHOUT_IDENTITY" not in rendered
    assert "Declared/Observed Active Routes: 2/12" in rendered
    assert "+1 more" not in rendered
