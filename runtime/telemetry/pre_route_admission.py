"""Observation-only pre-route admission snapshots."""

from __future__ import annotations

import hashlib
import json
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "pre_route_admission_snapshot.v1"
AUTHORITY = "OBSERVATION_ONLY"
BEHAVIORAL_AUTHORITY = "NONE"
UNOBSERVED = "NOT_OBSERVED_PRE_ADMISSION"
TEMPORAL_INTEGRITY_VERIFIED = "PRE_ADMISSION_TEMPORAL_INTEGRITY_VERIFIED"

FORBIDDEN_FEATURE_FIELDS = {
    "admission_state",
    "admitted",
    "arena_participation",
    "contribution_state",
    "current_route_arena_participation",
    "current_route_candidate_generation_result",
    "current_route_contribution_state",
    "current_route_output_count",
    "current_route_program_generation_result",
    "current_route_validation_result",
    "final_task_accuracy",
    "final_task_score",
    "final_task_success",
    "future_route_states",
    "post_route_residual",
    "route_contribution_outcome",
}


class PreRouteAdmissionSnapshotObserver:
    """Create immutable, inert snapshots before route admission is decided."""

    system_name = "pre_route_admission_snapshot_observer"

    def create_snapshot(
        self,
        *,
        context: Mapping[str, Any] | None,
        budget: Mapping[str, Any] | None,
        execution_plan_id: str | None,
        route_record: Mapping[str, Any],
        route_position: int,
        selected_route_count: int,
        admitted_so_far: int,
        executed_so_far: int,
        admission_sequence_index: int,
        prior_route_states: list[Mapping[str, Any]] | None = None,
        persist: bool = True,
        artifact_root: str | Path = "runtime/artifacts/route_pre_admission",
    ) -> dict[str, Any]:
        started = time.perf_counter()
        context = context if isinstance(context, Mapping) else {}
        budget = budget if isinstance(budget, Mapping) else {}
        route = route_record if isinstance(route_record, Mapping) else {}
        run_id = _identity(
            context.get("run_id")
            or context.get("execution_id")
            or context.get("runtime_id")
            or "current_run"
        )
        task_id = _identity(context.get("task_id") or context.get("task") or "current_task")
        route_id = _identity(route.get("route_id") or route.get("id") or f"route_{route_position}")
        budget_context_id = _identity(
            budget.get("budget_snapshot_id")
            or budget.get("budget_id")
            or _stable_id("budget_context", dict(budget))
        )
        route_context = {
            "route_id": route_id,
            "route_position": route_position,
            "route_family": route.get("route_family")
            or route.get("family")
            or route.get("route_source")
            or route.get("source")
            or UNOBSERVED,
            "route_source": route.get("route_source") or route.get("source") or UNOBSERVED,
            "selected_route_count": selected_route_count,
            "current_route_budget": _int_or_unobserved(budget.get("max_active_routes")),
            "routes_already_admitted_count": admitted_so_far,
            "routes_already_executed_count": executed_so_far,
            "remaining_route_capacity": _remaining_capacity(
                budget.get("max_active_routes"),
                admitted_so_far,
            ),
        }
        state_so_far = _state_so_far(context, prior_route_states or [])
        feature_payload = {
            "task_features": _task_features(context),
            "route_context": route_context,
            "state_so_far": state_so_far,
        }
        leakage_fields = sorted(
            field for field in _deep_keys(feature_payload)
            if field in FORBIDDEN_FEATURE_FIELDS
        )
        snapshot_id = _stable_id(
            "pre_route_snapshot",
            {
                "run_id": run_id,
                "task_id": task_id,
                "route_id": route_id,
                "route_position": route_position,
                "execution_plan_id": execution_plan_id,
                "budget_context_id": budget_context_id,
                "admission_sequence_index": admission_sequence_index,
            },
        )
        captured_at = str(datetime.utcnow())
        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "system": self.system_name,
            "authority": AUTHORITY,
            "behavioral_authority": BEHAVIORAL_AUTHORITY,
            "snapshot_id": snapshot_id,
            "run_id": run_id,
            "task_id": task_id,
            "route_id": route_id,
            "route_position": route_position,
            "execution_plan_id": execution_plan_id,
            "budget_context_id": budget_context_id,
            "capture_stage": "runtime_budget_enforcer.pre_route_admission",
            "captured_at": captured_at,
            "admission_sequence_index": admission_sequence_index,
            "temporal_integrity_state": TEMPORAL_INTEGRITY_VERIFIED,
            **feature_payload,
            "leakage_state": "LEAKAGE_ABSENT" if not leakage_fields else "LEAKAGE_DETECTED",
            "leakage_fields": leakage_fields,
            "immutable": True,
            "telemetry_consumed_by_cognition": False,
        }
        fingerprint = snapshot_fingerprint(snapshot)
        snapshot["snapshot_fingerprint"] = fingerprint
        serialized = json.dumps(snapshot, sort_keys=True, default=str, separators=(",", ":"))
        elapsed = time.perf_counter() - started
        overhead = {
            "snapshot_serialization_time": round(elapsed, 6),
            "snapshot_bytes": len(serialized.encode("utf-8")),
        }
        path = None
        if persist:
            path = persist_snapshot(snapshot, artifact_root=artifact_root)
        return {
            "snapshot": snapshot,
            "linkage": {
                "snapshot_id": snapshot_id,
                "run_id": run_id,
                "task_id": task_id,
                "route_id": route_id,
                "route_position": route_position,
                "execution_plan_id": execution_plan_id,
                "budget_context_id": budget_context_id,
                "snapshot_fingerprint_before": fingerprint,
                "snapshot_fingerprint_after_route_execution": fingerprint,
                "snapshot_created_before_admission_decision": True,
                "temporal_integrity_state": TEMPORAL_INTEGRITY_VERIFIED,
                "feature_state": "PRE_ADMISSION_FEATURES",
                "admission_state": "PENDING_ADMISSION_DECISION",
                "contribution_outcome_state": "PENDING_ROUTE_CONTRIBUTION_OUTCOME",
                "artifact_path": str(path) if path else None,
            },
            "overhead": overhead,
        }

    def verify_snapshot(self, snapshot: Mapping[str, Any] | None) -> bool:
        if not isinstance(snapshot, Mapping):
            return False
        return snapshot.get("snapshot_fingerprint") == snapshot_fingerprint(snapshot)


def snapshot_fingerprint(snapshot: Mapping[str, Any]) -> str:
    payload = dict(snapshot)
    payload.pop("snapshot_fingerprint", None)
    return _stable_id("pre_route_snapshot_fingerprint", payload)


def persist_snapshot(
    snapshot: Mapping[str, Any],
    *,
    artifact_root: str | Path = "runtime/artifacts/route_pre_admission",
) -> Path:
    root = Path(artifact_root)
    run = _safe(snapshot.get("run_id"))
    task = _safe(_stable_id("task", snapshot.get("task_id")))
    route = _safe(snapshot.get("route_id"))
    path = root / run / task / f"{int(snapshot.get('route_position') or 0):03d}_{route}_{snapshot.get('snapshot_id')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return path


def leakage_audit(snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
    snapshot = snapshot if isinstance(snapshot, Mapping) else {}
    fields = sorted(field for field in _deep_keys(snapshot) if field in FORBIDDEN_FEATURE_FIELDS)
    return {
        "leakage_count": len(fields),
        "leakage_fields": fields,
        "leakage_state": "LEAKAGE_ABSENT" if not fields else "LEAKAGE_DETECTED",
    }


def _task_features(context: Mapping[str, Any]) -> dict[str, Any]:
    report = _first_mapping(
        context.get("task_complexity_report"),
        context.get("TASK_COMPLEXITY_REPORT"),
        context.get("task_complexity"),
        context.get("complexity_report"),
    )
    grid = _first_mapping(
        context.get("grid_dimension_analysis"),
        context.get("GRID_DIMENSION_ANALYSIS"),
        context.get("grid_analysis"),
    )
    task_signature = (
        context.get("task_signature")
        or report.get("task_signature")
        or context.get("task_id")
        or context.get("task")
        or UNOBSERVED
    )
    return {
        "task_signature": task_signature,
        "grid_dimensions": {
            "height": grid.get("height", UNOBSERVED),
            "width": grid.get("width", UNOBSERVED),
            "shape": grid.get("shape", UNOBSERVED),
            "total_cells": grid.get("total_cells", UNOBSERVED),
        },
        "object_count": report.get("object_count", grid.get("object_count", UNOBSERVED)),
        "transformation_count": report.get("transformation_count", UNOBSERVED),
        "spatial_complexity": report.get("spatial_complexity", UNOBSERVED),
        "process_complexity": report.get("process_complexity", UNOBSERVED),
        "temporal_complexity": report.get("temporal_complexity", UNOBSERVED),
        "estimated_cognitive_cost": report.get(
            "estimated_cognitive_cost",
            report.get("estimated_cost", UNOBSERVED),
        ),
    }


def _state_so_far(context: Mapping[str, Any], prior_route_states: list[Mapping[str, Any]]) -> dict[str, Any]:
    outputs = _list(context.get("route_output_lineage_records"))
    prior_ids = {_identity(row.get("route_id")) for row in prior_route_states}
    prior_outputs = [
        row for row in outputs
        if isinstance(row, Mapping)
        and (
            _identity(row.get("origin_route_id")) in prior_ids
            or any(_identity(item) in prior_ids for item in _list(row.get("origin_route_ids")))
        )
    ]
    candidate_ids = {
        _identity(row.get("candidate_id"))
        for row in prior_outputs
        if row.get("candidate_id")
    }
    program_ids = {
        _identity(row.get("program_id"))
        for row in prior_outputs
        if row.get("program_id")
    }
    contribution_counts = _prior_contribution_counts(prior_route_states)
    return {
        "residual_count_so_far": _first_present(context, "residual_count_so_far", "current_residual_count", default=UNOBSERVED),
        "residual_type_so_far": _first_present(context, "residual_type_so_far", "current_residual_type", default=UNOBSERVED),
        "candidate_count_so_far": len(candidate_ids) if candidate_ids else UNOBSERVED,
        "unique_candidate_count_so_far": len(candidate_ids) if candidate_ids else UNOBSERVED,
        "candidate_source_count_so_far": len({
            _identity(row.get("producer_component") or row.get("source"))
            for row in prior_outputs
            if row.get("producer_component") or row.get("source")
        }) or UNOBSERVED,
        "program_count_so_far": len(program_ids) if program_ids else UNOBSERVED,
        "successful_program_count_so_far": len([
            row for row in prior_outputs
            if row.get("program_id") and row.get("validation_state") in {"VALIDATED", "ACCEPTED"}
        ]) or UNOBSERVED,
        "arena_state_so_far": context.get("arena_state_so_far", UNOBSERVED),
        "arena_candidate_count_so_far": _first_present(context, "arena_candidate_count_so_far", default=UNOBSERVED),
        "arena_ambiguity_so_far": _first_present(context, "arena_ambiguity_so_far", default=UNOBSERVED),
        "route_useful_count_so_far": contribution_counts["useful"],
        "route_no_observable_count_so_far": contribution_counts["no_observable"],
        "route_duplicate_count_so_far": contribution_counts["duplicate"],
        "route_low_value_count_so_far": contribution_counts["low_value"],
        "route_saturation_so_far": _route_saturation(contribution_counts),
        "repair_attempt_count_so_far": _first_present(context, "repair_attempt_count_so_far", default=UNOBSERVED),
        "repair_success_count_so_far": _first_present(context, "repair_success_count_so_far", default=UNOBSERVED),
        "evidence_deficit_so_far": _first_present(context, "evidence_deficit_so_far", default=UNOBSERVED),
    }


def _prior_contribution_counts(prior_route_states: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = {"useful": 0, "no_observable": 0, "duplicate": 0, "low_value": 0}
    for row in prior_route_states:
        state = str(row.get("contribution_state") or "")
        if state == "UNIQUE_USEFUL_CONTRIBUTION":
            counts["useful"] += 1
        elif state == "NO_OBSERVABLE_CONTRIBUTION":
            counts["no_observable"] += 1
        elif state == "DUPLICATE_CONTRIBUTION":
            counts["duplicate"] += 1
        elif state == "LOW_VALUE_CONTRIBUTION":
            counts["low_value"] += 1
    return counts


def _route_saturation(counts: Mapping[str, int]) -> float | str:
    total = sum(int(value or 0) for value in counts.values())
    if total <= 0:
        return UNOBSERVED
    return round((counts.get("duplicate", 0) + counts.get("no_observable", 0)) / total, 4)


def _remaining_capacity(value: Any, admitted_so_far: int) -> int | str:
    limit = _int(value)
    if limit is None:
        return UNOBSERVED
    return max(limit - int(admitted_so_far or 0), 0)


def _int_or_unobserved(value: Any) -> int | str:
    parsed = _int(value)
    return parsed if parsed is not None else UNOBSERVED


def _int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _first_present(context: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in context and context.get(key) is not None:
            return context.get(key)
    return default


def _first_mapping(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _deep_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            keys.add(str(key))
            keys.update(_deep_keys(nested))
    elif isinstance(value, list):
        for item in value:
            keys.update(_deep_keys(item))
    return keys


def _stable_id(prefix: str, payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


def _identity(value: Any) -> str:
    text = str(value or "").strip()
    return text or "unidentified"


def _safe(value: Any) -> str:
    token = str(value or "current_run")
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in token)[:120]


pre_route_admission_snapshot_observer = PreRouteAdmissionSnapshotObserver()


__all__ = [
    "AUTHORITY",
    "BEHAVIORAL_AUTHORITY",
    "FORBIDDEN_FEATURE_FIELDS",
    "SCHEMA_VERSION",
    "TEMPORAL_INTEGRITY_VERIFIED",
    "UNOBSERVED",
    "PreRouteAdmissionSnapshotObserver",
    "leakage_audit",
    "persist_snapshot",
    "pre_route_admission_snapshot_observer",
    "snapshot_fingerprint",
]
