"""Bounded runtime topology observation reports.

This module projects already-collected runtime execution trace data into an
observation-only artifact. It must not become an input to cognitive decisions.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"
REPORT_TYPE = "RUNTIME_TOPOLOGY_OBSERVATION_REPORT"
TRACE_SOURCE = "runtime.pipeline.legacy_pipeline.execution_trace"
DEFAULT_ARTIFACT_DIR = Path(
    "runtime/artifacts/runtime_data/topology_observation"
)
NOT_CONSUMABLE_AS_AUTHORITY = [
    "execution",
    "budget",
    "candidate",
    "repair",
    "evidence_acceptance",
    "truth",
    "identity",
    "learning",
    "task_selection",
]


def context_shape(context: Mapping[str, Any] | None) -> dict[str, str]:
    """Return passive, bounded structural summaries for context keys."""

    if not isinstance(context, Mapping):
        return {}
    return {
        str(key): _shape(value)
        for key, value in context.items()
    }


def context_delta(
    before: Mapping[str, Any] | None,
    after: Mapping[str, Any] | None,
) -> dict[str, Any]:
    before_shape = context_shape(before)
    after_shape = context_shape(after)
    before_keys = set(before_shape)
    after_keys = set(after_shape)
    shared = before_keys & after_keys
    return {
        "context_delta_status": "OBSERVED",
        "context_keys_before": sorted(before_keys),
        "context_keys_after": sorted(after_keys),
        "context_keys_added": sorted(after_keys - before_keys),
        "context_keys_removed": sorted(before_keys - after_keys),
        "context_keys_changed": sorted(
            key for key in shared if before_shape[key] != after_shape[key]
        ),
    }


def build_runtime_topology_observation_report(
    *,
    runtime_context: Mapping[str, Any] | None,
    execution_trace: list[Mapping[str, Any]] | None,
    pipeline_stages: list[Mapping[str, Any]] | None,
    execution_mode: str | None = None,
    report_level: str | None = None,
    expected_run_id: str | None = None,
) -> dict[str, Any]:
    started = perf_counter()
    context = runtime_context if isinstance(runtime_context, Mapping) else {}
    trace = execution_trace if isinstance(execution_trace, list) else []
    stages = pipeline_stages if isinstance(pipeline_stages, list) else []
    run_id = _first_text(
        context.get("run_id"),
        _mapping_get(context, "runtime_metrics", "run_id"),
        _mapping_get(context, "authoritative_execution_plan_reference", "run_id"),
        _mapping_get(context, "authoritative_execution_plan", "run_id"),
    )
    execution_plan_id = _first_text(
        _mapping_get(
            context,
            "authoritative_execution_plan_reference",
            "execution_plan_id",
        ),
        _mapping_get(context, "authoritative_execution_plan", "execution_plan_id"),
        context.get("execution_plan_id"),
    )
    task_id = _first_text(
        _context_value(context.get("task_id")),
        _context_value(context.get("task_file")),
        _context_value(context.get("task_path")),
    )
    binding = _current_run_binding(run_id, expected_run_id)
    stage_observations = _stage_observations(trace, stages)
    component_summary = _component_summary(context)
    serialization_started = perf_counter()
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        REPORT_TYPE: True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "execution_plan_id": execution_plan_id,
        "task_id": task_id,
        "execution_mode": _first_text(
            _mapping_get(context, "authoritative_execution_plan", "selected_mode"),
            _mapping_get(
                context,
                "authoritative_execution_plan_reference",
                "selected_mode",
            ),
            execution_mode,
            context.get("mode"),
        ),
        "report_level": _first_text(
            report_level,
            _mapping_get(context, "cognitive_budget_report", "report_level"),
        ),
        "authority": "OBSERVATION_ONLY",
        "behavioral_authority": "NONE",
        "not_consumable_as_authority": list(NOT_CONSUMABLE_AS_AUTHORITY),
        "cognitive_behavior_change": "NONE",
        "trace_source": TRACE_SOURCE,
        "trace_complete": bool(stage_observations),
        "trace_completeness_reason": (
            "EXECUTION_TRACE_PROJECTED"
            if stage_observations
            else "EXECUTION_TRACE_EMPTY_OR_UNAVAILABLE"
        ),
        "CURRENT_RUN_BINDING": binding["state"],
        "current_run_binding_reason": binding["reason"],
        "stage_count": len(stage_observations),
        "stage_observations": stage_observations,
        "stage_order": [row["stage_name"] for row in stage_observations],
        "component_reachability_summary": component_summary,
        "fast_minimal_survival": (
            "PROVEN"
            if _fast_minimal_return_observed(context)
            else "NOT_APPLICABLE_OR_NOT_OBSERVED"
        ),
        "topology_capture_time_seconds": 0.0,
        "topology_serialization_time_seconds": 0.0,
        "artifact_size_bytes": 0,
    }
    serialized = json.dumps(report, sort_keys=True, default=str)
    report["topology_capture_time_seconds"] = round(
        serialization_started - started,
        6,
    )
    report["topology_serialization_time_seconds"] = round(
        perf_counter() - serialization_started,
        6,
    )
    report["artifact_size_bytes"] = len(serialized.encode("utf-8"))
    return report


def persist_runtime_topology_observation_report(
    report: Mapping[str, Any],
    *,
    artifact_directory: str | Path | None = None,
) -> dict[str, Any]:
    started = perf_counter()
    directory = Path(artifact_directory or DEFAULT_ARTIFACT_DIR)
    try:
        directory.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            dict(report),
            indent=2,
            sort_keys=True,
            default=str,
        )
        run_id = _safe_filename(str(report.get("run_id") or "run_unbound"))
        report_path = directory / f"runtime_topology_observation_{run_id}.json"
        latest_path = directory / "latest.json"
        report_path.write_text(payload, encoding="utf-8")
        latest_path.write_text(payload, encoding="utf-8")
        return {
            "write_completed": True,
            "path": str(report_path),
            "latest_path": str(latest_path),
            "artifact_size_bytes": len(payload.encode("utf-8")),
            "topology_write_time_seconds": round(perf_counter() - started, 6),
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
        }
    except Exception as error:  # pragma: no cover - defensive persistence edge.
        return {
            "write_completed": False,
            "error": repr(error),
            "topology_write_time_seconds": round(perf_counter() - started, 6),
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
            "observation_failure_preserves_task_execution": True,
        }


def _stage_observations(
    trace: list[Mapping[str, Any]],
    stages: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    implementation_by_stage = {
        str(stage.get("stage_name")): str(
            stage.get("function_name")
            or getattr(stage.get("callable"), "__name__", "")
            or stage.get("implementation")
            or ""
        )
        for stage in stages
        if isinstance(stage, Mapping)
    }
    observations = []
    for index, item in enumerate(trace, start=1):
        if not isinstance(item, Mapping):
            continue
        stage_name = str(item.get("stage_name") or "")
        status = str(item.get("status") or "").lower()
        observations.append({
            "stage_name": stage_name,
            "stage_index": index,
            "implementation": implementation_by_stage.get(stage_name, ""),
            "entered": status not in {"initialized", "not_reached", ""},
            "completed": status == "completed",
            "skipped": status == "skipped",
            "skip_reason": item.get("reason") if status == "skipped" else None,
            "failed": status == "failed",
            "recovered": bool(item.get("recovered", False)),
            "fallback_used": bool(item.get("fallback_used", False)),
            "entry_sequence": item.get("entry_sequence", index),
            "exit_sequence": item.get("exit_sequence", index),
            "status": item.get("status"),
            "context_delta_status": item.get(
                "context_delta_status",
                "UNAVAILABLE",
            ),
            "context_keys_before": list(item.get("context_keys_before", []) or []),
            "context_keys_after": list(item.get("context_keys_after", []) or []),
            "context_keys_added": list(item.get("context_keys_added", []) or []),
            "context_keys_removed": list(item.get("context_keys_removed", []) or []),
            "context_keys_changed": list(item.get("context_keys_changed", []) or []),
            "emitted_artifact_types": list(
                item.get("emitted_artifact_types", []) or []
            ),
        })
    return observations


def _component_summary(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    components = [
        (
            "authoritative_execution_plan",
            "runtime/execution/execution_planner.py",
            "ExecutionPlanner",
            "PLANNING",
        ),
        (
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT",
            "runtime/budget/runtime_budget_enforcer.py",
            "RuntimeBudgetEnforcer",
            "BUDGET",
        ),
        (
            "CURRENT_CANDIDATE_ORIGIN_REPORT",
            "runtime/provenance/candidate_origin.py",
            "candidate_origin_report",
            "OBSERVATION",
        ),
        (
            "ACTIVE_RUNTIME_REACHABILITY_AUDIT",
            "runtime/reporting/active_runtime_reachability_audit.py",
            "build_active_runtime_reachability_audit",
            "OBSERVATION",
        ),
        (
            "runtime_finalization_report",
            "runtime/pipeline/legacy_pipeline.py",
            "finalize_runtime",
            "REPORTING",
        ),
    ]
    summary = []
    for key, file_name, symbol, authority in components:
        reached = key in context or key.lower() in context
        value = context.get(key, context.get(key.lower()))
        summary.append({
            "component": key,
            "file": file_name,
            "symbol": symbol,
            "reached": reached,
            "executed": reached,
            "state_effect_observed": bool(value),
            "authority_exercised": authority if reached else "NONE",
            "evidence_source": "runtime_context_key",
        })
    return summary


def _current_run_binding(
    run_id: str | None,
    expected_run_id: str | None,
) -> dict[str, str]:
    if not run_id:
        return {
            "state": "INVALID",
            "reason": "RUN_ID_MISSING",
        }
    if expected_run_id and str(run_id) != str(expected_run_id):
        return {
            "state": "INVALID",
            "reason": "RUN_ID_MISMATCH",
        }
    return {
        "state": "VALID",
        "reason": "RUN_ID_BOUND_TO_CURRENT_CONTEXT",
    }


def _fast_minimal_return_observed(context: Mapping[str, Any]) -> bool:
    fast_return = context.get("pipeline_fast_minimal_return")
    shutdown = context.get("post_success_shutdown")
    if isinstance(fast_return, Mapping) and fast_return.get("enabled") is True:
        return True
    return (
        isinstance(shutdown, Mapping)
        and shutdown.get("enabled") is True
        and str(shutdown.get("mode", "")).lower() == "fast"
    )


def _mapping_get(mapping: Mapping[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _first_text(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value)
        if text:
            return text
    return None


def _context_value(value: Any) -> Any:
    if isinstance(value, Mapping) and "value" in value:
        return value.get("value")
    return value


def _shape(value: Any) -> str:
    if isinstance(value, Mapping):
        return "dict:" + str(len(value))
    if isinstance(value, (list, tuple, set)):
        return type(value).__name__ + ":" + str(len(value))
    if isinstance(value, (str, int, float, bool)) or value is None:
        return type(value).__name__ + ":" + repr(value)[:96]
    return type(value).__name__


def _safe_filename(value: str) -> str:
    return "".join(
        char if char.isalnum() or char in {"_", "-", "."} else "_"
        for char in value
    )[:128]


__all__ = [
    "REPORT_TYPE",
    "SCHEMA_VERSION",
    "TRACE_SOURCE",
    "build_runtime_topology_observation_report",
    "context_delta",
    "context_shape",
    "persist_runtime_topology_observation_report",
]
