"""Experimental realized-resource telemetry collection helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from runtime.budget.budget_ablation_experiment import UNAVAILABLE
from runtime.budget.experimental_budget_authority import EXPERIMENTAL_BUDGET_SOURCE


def collect_realized_resource_telemetry(
    *,
    runtime_context: Mapping[str, Any] | None,
    result: Mapping[str, Any] | None = None,
    wall_time: float | None = None,
) -> dict[str, Any]:
    """Collect realized resource usage without substituting budget ceilings."""

    context = runtime_context if isinstance(runtime_context, Mapping) else {}
    result = result if isinstance(result, Mapping) else {}
    receipt = _first_mapping(
        context.get("RUNTIME_BUDGET_ENFORCEMENT_REPORT"),
        context.get("runtime_budget_enforcement_report"),
        _mapping_path(result, ("RUNTIME_BUDGET_ENFORCEMENT_REPORT",)),
        _mapping_path(result, ("runtime_budget_enforcement_report",)),
        _mapping_path(result, ("training_report", "RUNTIME_BUDGET_ENFORCEMENT_REPORT")),
        _mapping_path(result, ("training_report", "runtime_budget_enforcement_report")),
    )
    active_audit = _first_mapping(
        context.get("active_runtime_reachability_audit"),
        context.get("ACTIVE_RUNTIME_REACHABILITY_AUDIT"),
        _mapping_path(result, ("active_runtime_reachability_audit",)),
        _mapping_path(result, ("ACTIVE_RUNTIME_REACHABILITY_AUDIT",)),
        _mapping_path(result, ("training_report", "active_runtime_reachability_audit")),
        _mapping_path(result, ("training_report", "ACTIVE_RUNTIME_REACHABILITY_AUDIT")),
    )
    performance = _first_mapping(
        context.get("performance_report"),
        context.get("PERFORMANCE_REPORT"),
        _mapping_path(result, ("performance_report",)),
        _mapping_path(result, ("PERFORMANCE_REPORT",)),
        _mapping_path(result, ("training_report", "performance_report")),
        _mapping_path(result, ("training_report", "PERFORMANCE_REPORT")),
    )
    runtime_summary = _first_mapping(
        context.get("runtime_summary"),
        _mapping_path(result, ("runtime_summary",)),
        _mapping_path(result, ("training_report", "runtime_summary")),
    )
    execution_timing = _first_mapping(
        context.get("execution_timing_state"),
        _mapping_path(result, ("execution_timing_state",)),
        _mapping_path(result, ("training_report", "execution_timing_state")),
    )

    return {
        "requested_routes": _metric(
            receipt,
            "selected_route_count",
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT.selected_route_count",
        ),
        "admitted_routes": _metric(
            receipt,
            "admitted_route_count",
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT.admitted_route_count",
        ),
        "peak_active_routes": _metric(
            receipt,
            "peak_concurrent_active_route_count",
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT.peak_concurrent_active_route_count",
        ),
        "requested_reasoning_depth": _metric(
            receipt,
            "maximum_requested_reasoning_depth",
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT.maximum_requested_reasoning_depth",
        ),
        "entered_reasoning_depth": _metric(
            receipt,
            "maximum_entered_reasoning_depth",
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT.maximum_entered_reasoning_depth",
        ),
        "completed_reasoning_depth": _metric(
            receipt,
            "maximum_completed_reasoning_depth",
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT.maximum_completed_reasoning_depth",
        ),
        "realized_overrun": _metric(
            receipt,
            "realized_overrun_state",
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT.realized_overrun_state",
        ),
        "prevented_overrun": _metric(
            receipt,
            "prevented_overrun_state",
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT.prevented_overrun_state",
        ),
        "attempted_overrun": _metric(
            receipt,
            "attempted_overrun_state",
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT.attempted_overrun_state",
        ),
        "reachability_gap_count": _metric(
            active_audit,
            "reachability_gap_count",
            "active_runtime_reachability_audit.reachability_gap_count",
        ),
        "aggregate_active_compute_time": _active_compute_metric(
            performance,
            runtime_summary,
            execution_timing,
        ),
        "wall_time": {
            "value": wall_time if isinstance(wall_time, (int, float)) else UNAVAILABLE,
            "source": "collector_perf_counter_wall_time"
            if isinstance(wall_time, (int, float))
            else "NOT_AVAILABLE",
        },
    }


def flatten_realized_resource_telemetry(
    telemetry: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    return {
        key: value.get("value", UNAVAILABLE) if isinstance(value, Mapping) else UNAVAILABLE
        for key, value in telemetry.items()
    }


def validate_realized_usage_within_effective_ceiling(
    *,
    realized: Mapping[str, Any],
    effective_max_active_routes: int,
    effective_max_reasoning_depth: int,
) -> list[str]:
    failures: list[str] = []
    for key in ("admitted_routes", "peak_active_routes"):
        value = realized.get(key)
        if _numeric(value) and value > effective_max_active_routes:
            failures.append(f"{key.upper()}_EXCEEDS_EFFECTIVE_CEILING")
    for key in ("entered_reasoning_depth", "completed_reasoning_depth"):
        value = realized.get(key)
        if _numeric(value) and value > effective_max_reasoning_depth:
            failures.append(f"{key.upper()}_EXCEEDS_EFFECTIVE_CEILING")
    return failures


def observe_runtime_budget_authority(
    *,
    runtime_context: Mapping[str, Any] | None,
    result: Mapping[str, Any] | None = None,
    expected_authority_source: str = EXPERIMENTAL_BUDGET_SOURCE,
    expected_binding_state: str = "EXPERIMENTAL_BUDGET_GRANT_ACCEPTED",
) -> dict[str, Any]:
    """Observe runtime budget authority from runtime-produced reports only."""

    context = runtime_context if isinstance(runtime_context, Mapping) else {}
    result = result if isinstance(result, Mapping) else {}
    report = _first_mapping(
        context.get("cognitive_budget_report"),
        context.get("COGNITIVE_BUDGET_REPORT"),
        _mapping_path(result, ("cognitive_budget_report",)),
        _mapping_path(result, ("COGNITIVE_BUDGET_REPORT",)),
        _mapping_path(result, ("training_report", "cognitive_budget_report")),
        _mapping_path(result, ("training_report", "COGNITIVE_BUDGET_REPORT")),
    )
    binding = _first_mapping(
        context.get("runtime_budget_binding"),
        context.get("RUNTIME_BUDGET_BINDING"),
        _mapping_path(result, ("runtime_budget_binding",)),
        _mapping_path(result, ("RUNTIME_BUDGET_BINDING",)),
        _mapping_path(result, ("training_report", "runtime_budget_binding")),
        _mapping_path(result, ("training_report", "RUNTIME_BUDGET_BINDING")),
    )
    observed_authority = (
        report.get("runtime_budget_source")
        or report.get("budget_source")
        or binding.get("budget_source")
        or UNAVAILABLE
    )
    observed_binding = (
        report.get("runtime_budget_binding_state")
        or binding.get("binding_state")
        or UNAVAILABLE
    )
    valid = (
        observed_authority == expected_authority_source
        and observed_binding == expected_binding_state
    )
    return {
        "expected_authority_source": expected_authority_source,
        "observed_authority_source": observed_authority,
        "expected_binding_state": expected_binding_state,
        "observed_binding_state": observed_binding,
        "measurement_authority_valid": valid,
        "observed_authority_source_provenance": (
            "cognitive_budget_report.runtime_budget_source"
            if report.get("runtime_budget_source") is not None
            else "runtime_budget_binding.budget_source"
            if binding.get("budget_source") is not None
            else "NOT_AVAILABLE"
        ),
        "observed_binding_state_provenance": (
            "cognitive_budget_report.runtime_budget_binding_state"
            if report.get("runtime_budget_binding_state") is not None
            else "runtime_budget_binding.binding_state"
            if binding.get("binding_state") is not None
            else "NOT_AVAILABLE"
        ),
    }


def canonical_task_set_fingerprint(task_paths: Iterable[str | Path]) -> dict[str, Any]:
    tasks = []
    for task_path in task_paths:
        path = Path(task_path)
        tasks.append({
            "task_id": path.name,
            "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    canonical = sorted(tasks, key=lambda item: item["task_id"])
    return {
        "task_set_fingerprint": "task_set_sha256_" + _sha_json(canonical),
        "canonical_task_set_identity": canonical,
    }


def state_surface_fingerprint(
    *,
    root: str | Path,
    surfaces: Iterable[str | Path],
) -> dict[str, Any]:
    root_path = Path(root)
    entries = []
    for surface in sorted(str(item).replace("\\", "/") for item in surfaces):
        path = root_path / surface
        if not path.exists():
            entries.append({"path": surface, "kind": "missing", "sha256": None})
            continue
        files = [path] if path.is_file() else sorted(
            (item for item in path.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(root_path).as_posix(),
        )
        for file_path in files:
            relative = file_path.relative_to(root_path).as_posix()
            entries.append({
                "path": relative,
                "kind": "file",
                "sha256": hashlib.sha256(file_path.read_bytes()).hexdigest(),
            })
    return {
        "state_fingerprint": "state_sha256_" + _sha_json(entries),
        "state_identity_entries": entries,
        "file_count": len(entries),
    }


def _metric(source: Mapping[str, Any], key: str, source_name: str) -> dict[str, Any]:
    if not isinstance(source, Mapping) or key not in source or source.get(key) is None:
        return {"value": UNAVAILABLE, "source": "NOT_AVAILABLE"}
    return {"value": source.get(key), "source": source_name}


def _active_compute_metric(
    performance: Mapping[str, Any],
    runtime_summary: Mapping[str, Any],
    execution_timing: Mapping[str, Any],
) -> dict[str, Any]:
    candidates = (
        (performance, "active_compute_time_seconds", "performance_report.active_compute_time_seconds"),
        (runtime_summary, "active_compute_time_seconds", "runtime_summary.active_compute_time_seconds"),
        (execution_timing, "active_compute_time", "execution_timing_state.active_compute_time"),
    )
    for source, key, source_name in candidates:
        value = source.get(key) if isinstance(source, Mapping) else None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return {"value": value, "source": source_name}
    return {"value": UNAVAILABLE, "source": "NOT_AVAILABLE"}


def _first_mapping(*items: Any) -> Mapping[str, Any]:
    for item in items:
        if isinstance(item, Mapping):
            return item
    return {}


def _mapping_path(source: Mapping[str, Any], path: tuple[str, ...]) -> Mapping[str, Any]:
    current: Any = source
    for key in path:
        if not isinstance(current, Mapping):
            return {}
        current = current.get(key)
    return current if isinstance(current, Mapping) else {}


def _numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _sha_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


__all__ = [
    "canonical_task_set_fingerprint",
    "collect_realized_resource_telemetry",
    "flatten_realized_resource_telemetry",
    "observe_runtime_budget_authority",
    "state_surface_fingerprint",
    "validate_realized_usage_within_effective_ceiling",
]
