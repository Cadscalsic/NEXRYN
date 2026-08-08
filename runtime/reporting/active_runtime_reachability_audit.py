"""Read-only audit for active runtime reachability in canonical reports."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from runtime.reporting.engineering_conclusion_integrity import (
    engineering_conclusion_integrity_evaluator,
)

_MISSING_VALUES = {None, "", "Not Available", "NOT_AVAILABLE", "NOT_PRODUCED"}
_RAW_RESULT_IDENTITY_NOT_ISSUED = {
    None,
    "",
    "NOT_ISSUED",
    "RAW_VALIDATION_RESULT_ID_NOT_ISSUED",
    "RAW_RESULT_ID_NOT_ISSUED",
    "NOT_PRODUCED",
    "NOT_AVAILABLE",
    "Not Available",
}
_SCHEMA_VERSION = "1.0"
_LIFECYCLE_ORDER = [
    "ACTIVE_RUNTIME_AUDIT_BUILD_REQUESTED",
    "ACTIVE_RUNTIME_AUDIT_BUILD_COMPLETED",
    "ACTIVE_RUNTIME_AUDIT_ATTACHED_TO_RUN",
    "ACTIVE_RUNTIME_AUDIT_BOUND_TO_CANONICAL_REPORT",
]


def _first_dict(mapping: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _first_meaningful(*values: Any, default: Any = None) -> Any:
    for value in values:
        if value not in _MISSING_VALUES and value != {} and value != []:
            return value
    return default


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        upper = value.strip().upper()
        if upper == "TRUE":
            return True
        if upper == "FALSE":
            return False
    return None


def _raw_result_identity_missing(
    validation_report: dict[str, Any],
    evaluation_report: dict[str, Any],
    report_state: dict[str, Any],
) -> bool:
    raw_envelope = _first_dict(
        validation_report,
        "RAW_VALIDATION_RESULT_ENVELOPE",
        "raw_validation_result_envelope",
    )
    raw_state = str(
        _first_meaningful(
            raw_envelope.get("raw_validation_result_state"),
            validation_report.get("execution_state"),
            validation_report.get("validation_execution_lifecycle_state"),
            evaluation_report.get("raw_validation_result_state"),
            report_state.get("raw_result_state"),
            default="",
        )
    ).upper()
    raw_id = _first_meaningful(
        raw_envelope.get("raw_validation_result_id"),
        validation_report.get("raw_validation_result_id"),
        validation_report.get("raw_result_id"),
        evaluation_report.get("raw_validation_result_id"),
        report_state.get("raw_validation_result_id"),
        default=None,
    )
    raw_id_state = str(raw_id).strip().upper() if raw_id is not None else None
    return raw_state == "RAW_RESULT_CAPTURED" and (
        raw_id in _RAW_RESULT_IDENTITY_NOT_ISSUED
        or raw_id_state in _RAW_RESULT_IDENTITY_NOT_ISSUED
    )


def _engineering_conclusion_conflict(engineering: dict[str, Any]) -> bool:
    if _to_bool(engineering.get("conclusion_is_current")) is False:
        return False
    return engineering_conclusion_integrity_evaluator.has_conflict(engineering)


def _stable_id(prefix: str, payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


def _transition(
    audit: dict[str, Any],
    transition_name: str,
    *,
    sequence_index: int,
) -> dict[str, Any]:
    return {
        "transition_name": transition_name,
        "state": transition_name,
        "audit_id": audit.get("audit_id"),
        "audit_schema_version": audit.get("audit_schema_version", _SCHEMA_VERSION),
        "run_id": audit.get("audit_run_id") or audit.get("run_id"),
        "source_stage": audit.get("source_stage", "active_runtime_reachability_audit"),
        "source_timestamp": audit.get("source_timestamp", "TIMESTAMP_UNBOUND"),
        "sequence_index": sequence_index,
        "is_current_run": bool(audit.get("is_current_run", True)),
    }


def _transition_name(row: Any) -> str:
    if not isinstance(row, dict):
        return ""
    return str(row.get("transition_name") or row.get("state") or "")


def _lifecycle_integrity(audit: dict[str, Any]) -> dict[str, Any]:
    transitions = audit.get("lifecycle_transitions")
    transitions = transitions if isinstance(transitions, list) else []
    names = [_transition_name(row) for row in transitions]
    missing = [name for name in _LIFECYCLE_ORDER if name not in names]
    observed_order = [name for name in names if name in _LIFECYCLE_ORDER]
    expected_prefix = _LIFECYCLE_ORDER[: len(observed_order)]
    out_of_order = observed_order != expected_prefix
    ids = {
        row.get("audit_id")
        for row in transitions
        if isinstance(row, dict) and row.get("audit_id")
    }
    schemas = {
        row.get("audit_schema_version")
        for row in transitions
        if isinstance(row, dict) and row.get("audit_schema_version")
    }
    run_ids = {
        row.get("run_id")
        for row in transitions
        if isinstance(row, dict) and row.get("run_id")
    }
    identity_consistent = (
        len(ids) <= 1
        and len(schemas) <= 1
        and len(run_ids) <= 1
        and (not ids or audit.get("audit_id") in ids)
        and (not run_ids or (audit.get("audit_run_id") or audit.get("run_id")) in run_ids)
    )
    complete = not missing and not out_of_order and identity_consistent
    return {
        "audit_lifecycle_integrity_state": (
            "AUDIT_LIFECYCLE_COMPLETE" if complete else "AUDIT_LIFECYCLE_INCOMPLETE"
        ),
        "audit_lifecycle_transition_count": len(transitions),
        "audit_lifecycle_missing_transitions": missing,
        "audit_lifecycle_order_state": (
            "AUDIT_LIFECYCLE_ORDER_VALID"
            if not out_of_order
            else "AUDIT_LIFECYCLE_ORDER_INVALID"
        ),
        "audit_lifecycle_identity_state": (
            "AUDIT_LIFECYCLE_IDENTITY_STABLE"
            if identity_consistent
            else "AUDIT_LIFECYCLE_IDENTITY_CONFLICT"
        ),
    }


def _with_lifecycle_transition(
    audit: dict[str, Any] | None,
    transition_name: str,
) -> dict[str, Any]:
    current = dict(audit or {})
    transitions = [
        dict(row)
        for row in current.get("lifecycle_transitions", [])
        if isinstance(row, dict)
    ]
    if transition_name not in {_transition_name(row) for row in transitions}:
        transitions.append(
            _transition(
                current,
                transition_name,
                sequence_index=_LIFECYCLE_ORDER.index(transition_name) + 1,
            )
        )
    integrity_source = {**current, "lifecycle_transitions": list(transitions)}
    transitions.sort(
        key=lambda row: _LIFECYCLE_ORDER.index(_transition_name(row))
        if _transition_name(row) in _LIFECYCLE_ORDER
        else 10**6
    )
    current["lifecycle_transitions"] = transitions
    current.update(_lifecycle_integrity(integrity_source))
    return current


def mark_active_runtime_audit_attached_to_run(
    audit: dict[str, Any] | None,
) -> dict[str, Any]:
    return _with_lifecycle_transition(
        audit,
        "ACTIVE_RUNTIME_AUDIT_ATTACHED_TO_RUN",
    )


def mark_active_runtime_audit_bound_to_canonical_report(
    audit: dict[str, Any] | None,
) -> dict[str, Any]:
    return _with_lifecycle_transition(
        audit,
        "ACTIVE_RUNTIME_AUDIT_BOUND_TO_CANONICAL_REPORT",
    )


def _iter_dicts(value: Any, *, max_depth: int = 5, _depth: int = 0):
    if _depth > max_depth:
        return
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _iter_dicts(nested, max_depth=max_depth, _depth=_depth + 1)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_dicts(item, max_depth=max_depth, _depth=_depth + 1)


def _task_runtime_summary(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    declared_routes: list[int] = []
    declared_depths: list[int] = []
    declared_dependency_depths: list[int] = []
    declared_hypotheses: list[int] = []
    observed_routes: list[int] = []
    observed_peak_routes: list[int] = []
    selected_routes: list[int] = []
    observed_depths: list[int] = []
    observed_entered_depths: list[int] = []
    observed_completed_depths: list[int] = []
    requested_depths: list[int] = []
    depth_block_counts: list[int] = []
    depth_admission_counts: list[int] = []
    retry_allowed_seen = False
    incomplete_episode_seen = False
    repair_applicable_seen = False
    repair_not_applicable_seen = False
    repair_attempt_values: list[int] = []
    telemetry_present = False

    for item in task_results:
        result = item.get("result") if isinstance(item, dict) else None
        if not isinstance(result, dict):
            continue
        for row in _iter_dicts(result):
            if any(key in row for key in ("max_active_routes", "max_reasoning_depth", "active_routes", "route_count", "reasoning_depth")):
                telemetry_present = True
            peak = _to_int(row.get("peak_concurrent_active_route_count"))
            if peak is not None:
                observed_peak_routes.append(peak)
                telemetry_present = True
            selected = _to_int(row.get("selected_route_count"))
            if selected is not None:
                selected_routes.append(selected)
            entered = _to_int(row.get("maximum_entered_reasoning_depth"))
            if entered is not None:
                observed_entered_depths.append(entered)
                telemetry_present = True
            completed = _to_int(row.get("maximum_completed_reasoning_depth"))
            if completed is not None:
                observed_completed_depths.append(completed)
            requested = _to_int(
                _first_meaningful(
                    row.get("maximum_requested_reasoning_depth"),
                    row.get("attempted_reasoning_depth"),
                    default=None,
                )
            )
            if requested is not None:
                requested_depths.append(requested)
            block_count = _to_int(row.get("depth_block_count"))
            if block_count is not None:
                depth_block_counts.append(block_count)
            admission_count = _to_int(row.get("depth_admission_count"))
            if admission_count is not None:
                depth_admission_counts.append(admission_count)
            for key, target in (
                ("max_active_routes", declared_routes),
                ("maximum_active_routes", declared_routes),
                ("max_reasoning_depth", declared_depths),
                ("maximum_reasoning_depth", declared_depths),
                ("max_dependency_depth", declared_dependency_depths),
                ("maximum_dependency_depth", declared_dependency_depths),
                ("max_hypotheses", declared_hypotheses),
                ("maximum_hypotheses", declared_hypotheses),
                ("active_routes", observed_routes),
                ("route_count", observed_routes),
                ("peak_concurrent_active_route_count", observed_routes),
                ("reasoning_depth", observed_depths),
                ("maximum_entered_reasoning_depth", observed_depths),
            ):
                number = _to_int(row.get(key))
                if number is not None:
                    target.append(number)
            if _to_bool(row.get("retry_allowed")) is True:
                retry_allowed_seen = True
            if _to_bool(row.get("episode_completed")) is False:
                incomplete_episode_seen = True
            if _to_bool(row.get("repair_required")) is True:
                repair_applicable_seen = True
            if _to_bool(row.get("repair_applicable")) is True:
                repair_applicable_seen = True
            if _to_bool(row.get("repair_applicable")) is False:
                repair_not_applicable_seen = True
            residual_count = _to_int(
                _first_meaningful(
                    row.get("residual_difference_count"),
                    row.get("residual_count"),
                    row.get("difference_count"),
                    default=None,
                )
            )
            residual_type = str(row.get("residual_type") or "").lower()
            if residual_count is not None and residual_count > 0:
                repair_applicable_seen = True
            if residual_type and residual_type not in {"none", "not_applicable"}:
                repair_applicable_seen = True
            attempts = _to_int(row.get("repair_attempts"))
            if attempts is not None:
                repair_attempt_values.append(attempts)

    return {
        "task_runtime_telemetry_present": telemetry_present,
        "task_budget_snapshot_present": bool(declared_routes or declared_depths),
        "declared_max_active_routes": min(declared_routes) if declared_routes else None,
        "declared_max_reasoning_depth": min(declared_depths) if declared_depths else None,
        "declared_max_dependency_depth": min(declared_dependency_depths) if declared_dependency_depths else None,
        "declared_max_hypotheses": min(declared_hypotheses) if declared_hypotheses else None,
        "selected_route_count": max(selected_routes) if selected_routes else None,
        "observed_active_routes": (
            max(observed_peak_routes)
            if observed_peak_routes
            else max(observed_routes)
            if observed_routes
            else None
        ),
        "observed_reasoning_depth": (
            max(observed_entered_depths)
            if observed_entered_depths
            else max(observed_depths)
            if observed_depths
            else None
        ),
        "observed_completed_reasoning_depth": (
            max(observed_completed_depths)
            if observed_completed_depths
            else None
        ),
        "maximum_requested_reasoning_depth": (
            max(requested_depths)
            if requested_depths
            else None
        ),
        "depth_block_count": max(depth_block_counts) if depth_block_counts else None,
        "depth_admission_count": max(depth_admission_counts) if depth_admission_counts else None,
        "retry_allowed": True if retry_allowed_seen else None,
        "episode_completed": False if incomplete_episode_seen else None,
        "repair_applicable": (
            True
            if repair_applicable_seen and not repair_not_applicable_seen
            else False
            if repair_not_applicable_seen
            else None
        ),
        "repair_attempts": min(repair_attempt_values) if repair_attempt_values else None,
    }


def build_active_runtime_telemetry_summary(
    task_results: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    return _task_runtime_summary(list(task_results or []))


def build_active_runtime_reachability_audit(
    report_state: dict[str, Any] | None,
    *,
    task_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic read-only audit of whether active runtime state is bound.

    This module does not execute, repair, schedule, evaluate, or mutate any NEXRYN
    runtime state. It only classifies whether the final report has enough current
    runtime facts to support the claims it renders.
    """

    state = report_state if isinstance(report_state, dict) else {}
    source_task_results = list(task_results or [])
    if not source_task_results and isinstance(state.get("multi_task_results"), list):
        source_task_results = [
            item for item in state.get("multi_task_results", []) if isinstance(item, dict)
        ]
    task_summary = _task_runtime_summary(source_task_results)
    execution_report = _first_dict(
        state,
        "EXECUTION_PLAN_REPORT",
        "execution_plan_report",
        "CANONICAL_EXECUTION_PLAN_REPORT",
        "canonical_execution_plan",
    )
    canonical_plan = _first_dict(
        state,
        "CANONICAL_EXECUTION_PLAN_REPORT",
        "canonical_execution_plan",
    ) or _first_dict(execution_report, "CANONICAL_EXECUTION_PLAN_REPORT", "canonical_execution_plan")
    budget_report = _first_dict(
        state,
        "RUNTIME_BUDGET_ENFORCEMENT_REPORT",
        "runtime_budget_enforcement_report",
    ) or _first_dict(
        execution_report,
        "RUNTIME_BUDGET_ENFORCEMENT_REPORT",
        "runtime_budget_enforcement_report",
    )
    validation_report = _first_dict(
        state,
        "VALIDATION_TASK_EXECUTION_REPORT",
        "validation_task_execution_report",
    )
    raw_applicability = _first_dict(
        state,
        "RAW_RESULT_APPLICABILITY_REPORT",
        "raw_result_applicability_report",
    )
    raw_applicability_state = str(
        raw_applicability.get("raw_result_applicability_state") or ""
    ).upper()
    evaluation_report = _first_dict(
        state,
        "VALIDATION_EVIDENCE_EVALUATION_REPORT",
        "validation_evidence_evaluation_report",
    )
    repair_report = _first_dict(
        state,
        "FINAL_REPAIR_REPORT",
        "REPAIR_REPORT",
        "repair_report",
        "execution_repair_report",
    )
    engineering = _first_dict(state, "ENGINEERING_CONCLUSION", "engineering_conclusion")
    source_timestamp = _first_meaningful(
        engineering.get("conclusion_source_timestamp"),
        state.get("timestamp"),
        state.get("source_timestamp"),
        default="TIMESTAMP_UNBOUND",
    )
    expected_run_id = _first_meaningful(
        state.get("run_id"),
        engineering.get("conclusion_run_id"),
        default=None,
    )
    expected_task_id = _first_meaningful(
        state.get("task_id"),
        engineering.get("conclusion_task_id"),
        default=None,
    )
    plan_run_id = _first_meaningful(canonical_plan.get("run_id"), default=None)
    plan_task_id = _first_meaningful(canonical_plan.get("task_id"), default=None)
    plan_authority = _first_meaningful(
        canonical_plan.get("planning_authority"),
        canonical_plan.get("temporal_authority_state"),
        default=None,
    )
    authoritative_plan_state = "AUTHORITATIVE_PLAN_UNAVAILABLE"
    retrospective_reconstruction_state = "RETROSPECTIVE_RECONSTRUCTION_ABSENT"
    if canonical_plan and plan_authority == "AUTHORITATIVE":
        authoritative_plan_state = "AUTHORITATIVE_PRE_EXECUTION_PLAN_PRESENT"
    elif canonical_plan and canonical_plan.get("plan_origin") == (
        "POST_EXECUTION_TELEMETRY_RECONSTRUCTION"
    ):
        retrospective_reconstruction_state = "RETROSPECTIVE_RECONSTRUCTION_PRESENT"
    retrospective_plan = _first_dict(
        execution_report,
        "retrospective_execution_plan",
    )
    if retrospective_plan:
        retrospective_reconstruction_state = "RETROSPECTIVE_RECONSTRUCTION_PRESENT"
    plan_identity_state = "PLAN_IDENTITY_CURRENT"
    if not canonical_plan:
        plan_identity_state = "PLAN_IDENTITY_UNBOUND"
    elif expected_run_id is not None and plan_run_id != expected_run_id:
        plan_identity_state = "PLAN_RUN_ID_MISMATCH"
        canonical_plan = {}
    elif expected_task_id is not None and plan_task_id not in {expected_task_id, None}:
        plan_identity_state = "PLAN_TASK_ID_MISMATCH"
        canonical_plan = {}

    max_routes = _to_int(
        _first_meaningful(
            budget_report.get("maximum_active_routes"),
            budget_report.get("max_active_routes"),
            task_summary.get("declared_max_active_routes"),
            default=None,
        )
    )
    observed_routes = _to_int(
        _first_meaningful(
            budget_report.get("peak_concurrent_active_route_count"),
            budget_report.get("selected_route_count"),
            execution_report.get("active_route_count"),
            canonical_plan.get("active_route_count"),
            state.get("active_routes"),
            task_summary.get("observed_active_routes"),
            default=None,
        )
    )
    if (
        task_summary.get("observed_active_routes") is not None
        and (observed_routes in {None, 0})
        and not canonical_plan
    ):
        observed_routes = task_summary["observed_active_routes"]
    max_depth = _to_int(
        _first_meaningful(
            budget_report.get("maximum_reasoning_depth"),
            budget_report.get("max_reasoning_depth"),
            task_summary.get("declared_max_reasoning_depth"),
            default=None,
        )
    )
    observed_depth = _to_int(
        _first_meaningful(
            budget_report.get("maximum_entered_reasoning_depth"),
            budget_report.get("maximum_completed_reasoning_depth"),
            state.get("reasoning_depth"),
            task_summary.get("observed_reasoning_depth"),
            default=None,
        )
    )
    if (
        task_summary.get("observed_reasoning_depth") is not None
        and (observed_depth in {None, 0})
        and not canonical_plan
    ):
        observed_depth = task_summary["observed_reasoning_depth"]
    budget_exceeded_detected = (
        (max_routes is not None and observed_routes is not None and observed_routes > max_routes)
        or (max_depth is not None and observed_depth is not None and observed_depth > max_depth)
    )
    budget_state = _first_meaningful(
        budget_report.get("runtime_budget_state"),
        default="RUNTIME_BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE",
    )

    retry_allowed = _to_bool(
        _first_meaningful(
            state.get("retry_allowed"),
            repair_report.get("retry_allowed"),
            task_summary.get("retry_allowed"),
            default=None,
        )
    )
    episode_completed = _to_bool(
        _first_meaningful(
            state.get("episode_completed"),
            task_summary.get("episode_completed"),
            default=None,
        )
    )
    repair_attempts = _to_int(
        _first_meaningful(
            repair_report.get("repair_attempts"),
            state.get("repair_attempts"),
            task_summary.get("repair_attempts"),
            default=0,
        )
    ) or 0
    repair_applicable = _to_bool(
        _first_meaningful(
            state.get("repair_required"),
            repair_report.get("repair_required"),
            task_summary.get("repair_applicable"),
            default=None,
        )
    )

    gaps: list[str] = []
    if not canonical_plan:
        gaps.append("CANONICAL_EXECUTION_PLAN_NOT_BOUND")
    if plan_identity_state == "PLAN_RUN_ID_MISMATCH":
        gaps.append("CANONICAL_EXECUTION_PLAN_RUN_ID_MISMATCH")
    if plan_identity_state == "PLAN_TASK_ID_MISMATCH":
        gaps.append("CANONICAL_EXECUTION_PLAN_TASK_ID_MISMATCH")
    if not budget_report:
        gaps.append("BUDGET_ENFORCEMENT_REPORT_NOT_BOUND")
    if budget_state == "RUNTIME_BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE":
        gaps.append("BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE")
    if budget_exceeded_detected and budget_state not in {
        "RUNTIME_BUDGET_INTEGRITY_FAILED",
        "AUTHORITATIVE_RUNTIME_BUDGET_EXCEEDED",
    }:
        gaps.append("RUNTIME_BUDGET_EXCEEDED_UNREPORTED")
    if (
        retry_allowed is True
        and episode_completed is False
        and repair_applicable is True
        and repair_attempts == 0
    ):
        gaps.append("RETRY_ALLOWED_REPAIR_NOT_ATTEMPTED")
    if (
        raw_applicability_state != "RAW_RESULT_NOT_APPLICABLE"
        and _raw_result_identity_missing(validation_report, evaluation_report, state)
    ):
        gaps.append("RAW_RESULT_CAPTURED_WITHOUT_IDENTITY")
    if _engineering_conclusion_conflict(engineering):
        gaps.append("ENGINEERING_CONCLUSION_CONFLICT")
    if (
        validation_report.get("execution_state") in {"NOT_PRODUCED", "Not produced"}
        and engineering.get("largest_success")
        == "scheduled_validation_task_executed_and_raw_result_contained"
    ):
        gaps.append("ENGINEERING_CONCLUSION_CONFLICT")

    run_id = _first_meaningful(
        state.get("run_id"),
        engineering.get("conclusion_run_id"),
        canonical_plan.get("run_id"),
        default="RUN_ID_UNBOUND",
    )
    task_id = _first_meaningful(
        state.get("task_id"),
        engineering.get("conclusion_task_id"),
        canonical_plan.get("task_id"),
        default="TASK_ID_UNBOUND",
    )
    audit_id = _stable_id(
        "active_runtime_reachability_audit",
        {
            "schema_version": _SCHEMA_VERSION,
            "run_id": run_id,
            "task_id": task_id,
            "source_timestamp": source_timestamp,
            "source_stage": "active_runtime_reachability_audit",
        },
    )
    lifecycle_transitions = [
        _transition(
            {
                "audit_id": audit_id,
                "audit_schema_version": _SCHEMA_VERSION,
                "audit_run_id": run_id,
                "run_id": run_id,
                "source_stage": "active_runtime_reachability_audit",
                "source_timestamp": source_timestamp,
                "is_current_run": True,
            },
            "ACTIVE_RUNTIME_AUDIT_BUILD_REQUESTED",
            sequence_index=1,
        ),
        _transition(
            {
                "audit_id": audit_id,
                "audit_schema_version": _SCHEMA_VERSION,
                "audit_run_id": run_id,
                "run_id": run_id,
                "source_stage": "active_runtime_reachability_audit",
                "source_timestamp": source_timestamp,
                "is_current_run": True,
            },
            "ACTIVE_RUNTIME_AUDIT_BUILD_COMPLETED",
            sequence_index=2,
        ),
    ]
    audit = {
        "audit_schema_version": _SCHEMA_VERSION,
        "audit_id": audit_id,
        "audit_state": "REACHABILITY_GAPS_DETECTED" if gaps else "REACHABILITY_CLEAR",
        "audit_run_id": run_id,
        "run_id": run_id,
        "task_id": task_id,
        "source_stage": "active_runtime_reachability_audit",
        "source_timestamp": source_timestamp,
        "is_current_run": True,
        "lifecycle_transitions": lifecycle_transitions,
        "execution_plan_id": _first_meaningful(
            canonical_plan.get("execution_plan_id"),
            default="EXECUTION_PLAN_ID_UNBOUND",
        ),
        "execution_plan_identity_state": plan_identity_state,
        "canonical_execution_plan_present": bool(canonical_plan),
        "authoritative_plan_state": authoritative_plan_state,
        "retrospective_reconstruction_state": retrospective_reconstruction_state,
        "temporal_authority_state": _first_meaningful(
            canonical_plan.get("temporal_authority_state"),
            default="AUTHORITATIVE_PLAN_UNAVAILABLE",
        ),
        "execution_plan_report_present": bool(execution_report),
        "budget_report_present": bool(budget_report),
        "task_runtime_telemetry_present": bool(task_summary["task_runtime_telemetry_present"]),
        "task_budget_snapshot_present": bool(task_summary["task_budget_snapshot_present"]),
        "budget_state": budget_state,
        "budget_exceeded_detected": bool(budget_exceeded_detected),
        "declared_active_routes": max_routes,
        "declared_max_active_routes": max_routes,
        "observed_active_routes": observed_routes,
        "declared_reasoning_depth": max_depth,
        "declared_max_reasoning_depth": max_depth,
        "observed_reasoning_depth": observed_depth,
        "retry_allowed": retry_allowed,
        "episode_completed": episode_completed,
        "repair_attempts": repair_attempts,
        "repair_applicable": repair_applicable,
        "raw_result_applicability_state": raw_applicability.get(
            "raw_result_applicability_state",
            "RAW_RESULT_APPLICABILITY_UNDETERMINED",
        ),
        "raw_result_applicability_reason": raw_applicability.get(
            "raw_result_applicability_reason",
            "RAW_RESULT_PRODUCER_PROVENANCE_UNDETERMINED",
        ),
        "raw_result_producer_obligation_count": raw_applicability.get(
            "raw_result_producer_obligation_count",
            0,
        ),
        "applicable_raw_result_missing_count": raw_applicability.get(
            "applicable_raw_result_missing_count",
            0,
        ),
        "repair_reachability_state": (
            "REPAIR_REACHABILITY_BLOCKED"
            if "RETRY_ALLOWED_REPAIR_NOT_ATTEMPTED" in gaps
            else "REPAIR_REACHABILITY_CLEAR"
        ),
        "raw_result_identity_state": (
            "RAW_RESULT_IDENTITY_MISSING"
            if "RAW_RESULT_CAPTURED_WITHOUT_IDENTITY" in gaps
            else "RAW_RESULT_IDENTITY_CLEAR"
        ),
        "engineering_conclusion_state": (
            "ENGINEERING_CONCLUSION_CONFLICT"
            if "ENGINEERING_CONCLUSION_CONFLICT" in gaps
            else "ENGINEERING_CONCLUSION_NOT_CONFLICTING"
        ),
        "reachability_gap_count": len(gaps),
        "reachability_gaps": gaps,
        "recommended_next_fix": (
            "repair_canonical_execution_plan_active_runtime_binding"
            if gaps
            else "continue_with_next_governed_runtime_stage"
        ),
    }
    audit.update(_lifecycle_integrity(audit))
    return audit
