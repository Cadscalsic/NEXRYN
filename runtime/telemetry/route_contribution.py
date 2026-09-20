"""Observation-only route contribution telemetry."""

from __future__ import annotations

import hashlib
import json
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"
AUTHORITY = "OBSERVATION_ONLY"
BEHAVIORAL_AUTHORITY = "NONE"

ACTIVE_STATES = {"ACTIVE_ROUTE", "ROUTE_ACTIVATION_STARTED", "EXECUTING", "ACTIVE"}
ADMITTED_STATES = {"ROUTE_ADMITTED", "ADMITTED_ROUTE"}
COMPLETED_STATES = {"COMPLETED_ROUTE", "RELEASED_ROUTE", "COMPLETED", "RELEASED"}
FAILED_STATES = {"FAILED_ROUTE", "CANCELLED_ROUTE", "TIMED_OUT_ROUTE", "FAILED", "TIMEOUT"}
DEFERRED_STATES = {"DEFERRED_BY_BUDGET"}
REJECTED_STATES = {"REJECTED_BY_BUDGET", "BLOCKED_ROUTE"}

USEFUL_STATES = {
    "QUALIFIED",
    "VALIDATED",
    "ACCEPTED",
    "EVIDENCE_USED_IN_DECISION",
    "EVIDENCE_DECISIVE",
    "WINNER",
    "ROUTE_CONTRIBUTED_TO_ARENA",
    "ROUTE_OUTPUT_USED_IN_SUCCESSFUL_PATH",
    "ROUTE_CONTRIBUTED_TO_RESIDUAL_REDUCTION",
}
LOW_VALUE_STATES = {
    "REJECTED",
    "FAILED_VALIDATION",
    "FAILED_QUALIFICATION",
    "DOMINATED",
    "REJECTED_BY_SCORE",
    "REJECTED_BY_SIMULATION",
    "BLOCKED_BY_GOVERNANCE",
}

ROUTE_LINEAGE_FIELDS = (
    "route_origin_lineage",
    "origin_route_execution_id",
    "origin_route_execution_ids",
    "origin_route_id",
    "origin_route_ids",
    "route_lineage_origin_type",
    "route_lineage_scope_state",
)

SOURCE_ROUTE_ALIASES = {
    "adaptive_reuse": {"adaptive_reuse"},
    "causal": {"causal_validation"},
    "causal_validation": {"causal_validation"},
    "color": {"color_mapping"},
    "color_mapping": {"color_mapping"},
    "contradiction": {"contradiction_checks"},
    "contradiction_checks": {"contradiction_checks"},
    "dependency": {"dependency_reasoning"},
    "dependency_reasoning": {"dependency_reasoning"},
    "identity": {"identity_governance"},
    "identity_governance": {"identity_governance"},
    "object": {"object_tracking"},
    "object_tracking": {"object_tracking"},
    "program_generation": {"transformation_compilation"},
    "semantic_compiler": {"semantic_to_transformation_compiler"},
    "semantic_to_transformation_compiler": {"semantic_to_transformation_compiler"},
    "spatial": {"spatial_reasoning"},
    "spatial_reasoning": {"spatial_reasoning"},
    "transformation": {"transformation_compilation"},
    "transformation_compilation": {"transformation_compilation"},
    "transformation_execution": {"transformation_execution"},
    "truth": {"truth_governance"},
    "truth_governance": {"truth_governance"},
}


def route_origin_lineage_from_record(
    manifest: Mapping[str, Any] | None,
    *,
    source_name: Any = None,
    record: Mapping[str, Any] | None = None,
    produced_at_stage: str | None = None,
    producer_component: str | None = None,
) -> dict[str, Any]:
    """Return validated observation-only route origin lineage for one artifact.

    This helper never guesses from proposal order. It accepts an existing
    route-origin payload or a source descriptor that can be matched to a
    current-run executed route.
    """

    manifest = manifest if isinstance(manifest, Mapping) else {}
    record = record if isinstance(record, Mapping) else {}
    existing = record.get("route_origin_lineage")
    if isinstance(existing, Mapping):
        lineage = deepcopy(dict(existing))
        lineage.setdefault("route_lineage_origin_type", "DIRECT_LINEAGE")
    else:
        matched = _route_for_source_descriptor(
            manifest,
            [
                source_name,
                record.get("source"),
                record.get("origin_source"),
                record.get("normalized_source"),
                record.get("route_id"),
                record.get("origin_route_id"),
                _record_metadata_value(record, "source_domain"),
                _record_metadata_value(record, "concept"),
                record.get("intent"),
                record.get("operation"),
            ],
        )
        if not matched:
            return {
                "route_lineage_scope_state": "ROUTE_ORIGIN_NOT_OBSERVABLE",
                "route_lineage_origin_type": "UNBOUND",
                "authority": AUTHORITY,
                "behavioral_authority": BEHAVIORAL_AUTHORITY,
            }
        lineage = {
            "schema_version": "route_origin_lineage.v1",
            "run_id": manifest.get("run_id"),
            "task_id": manifest.get("task_id"),
            "route_execution_id": matched.get("route_execution_id"),
            "route_execution_ids": [matched.get("route_execution_id")],
            "route_id": matched.get("route_id"),
            "route_ids": [matched.get("route_id")],
            "route_position": matched.get("route_position"),
            "route_family": matched.get("route_family"),
            "route_source": matched.get("route_source"),
            "route_lineage_origin_type": "DIRECT_SOURCE_DESCRIPTOR",
            "producer_component": producer_component or source_name or record.get("source"),
            "produced_at_stage": produced_at_stage,
            "authority": AUTHORITY,
            "behavioral_authority": BEHAVIORAL_AUTHORITY,
        }
    lineage["route_lineage_scope_state"] = _validate_route_origin_lineage(
        manifest,
        lineage,
    )
    lineage.setdefault("authority", AUTHORITY)
    lineage.setdefault("behavioral_authority", BEHAVIORAL_AUTHORITY)
    return lineage


def attach_route_origin_lineage(
    record: Mapping[str, Any] | None,
    lineage: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Attach route origin lineage as inert metadata to a copied record."""

    copied = deepcopy(dict(record)) if isinstance(record, Mapping) else {}
    lineage = deepcopy(dict(lineage)) if isinstance(lineage, Mapping) else {}
    if lineage.get("route_lineage_scope_state") != "ROUTE_ORIGIN_CURRENT":
        return copied
    route_execution_ids = [
        item for item in lineage.get("route_execution_ids", []) if item
    ]
    if lineage.get("route_execution_id") and lineage.get("route_execution_id") not in route_execution_ids:
        route_execution_ids.insert(0, lineage.get("route_execution_id"))
    route_ids = [item for item in lineage.get("route_ids", []) if item]
    if lineage.get("route_id") and lineage.get("route_id") not in route_ids:
        route_ids.insert(0, lineage.get("route_id"))
    copied["route_origin_lineage"] = lineage
    copied["origin_route_execution_id"] = lineage.get("route_execution_id")
    copied["origin_route_execution_ids"] = route_execution_ids
    copied["origin_route_id"] = lineage.get("route_id")
    copied["origin_route_ids"] = route_ids
    copied["route_lineage_origin_type"] = lineage.get("route_lineage_origin_type")
    copied["route_lineage_scope_state"] = lineage.get("route_lineage_scope_state")
    metadata = copied.get("metadata")
    metadata = dict(metadata) if isinstance(metadata, Mapping) else {}
    for field in ROUTE_LINEAGE_FIELDS:
        if copied.get(field) is not None:
            metadata[field] = deepcopy(copied.get(field))
    metadata.setdefault("route_lineage_authority", AUTHORITY)
    metadata.setdefault("route_lineage_behavioral_authority", BEHAVIORAL_AUTHORITY)
    copied["metadata"] = metadata
    return copied


def route_lineage_record_from_artifact(
    artifact: Mapping[str, Any] | None,
    *,
    output_type: str,
    produced_at_stage: str,
    producer_component: str,
    validation_state: Any = None,
    qualification_state: Any = None,
    arena_state: Any = None,
    repair_state: Any = None,
) -> dict[str, Any] | None:
    artifact = artifact if isinstance(artifact, Mapping) else {}
    lineage = artifact.get("route_origin_lineage")
    if not isinstance(lineage, Mapping):
        return None
    if artifact.get("route_lineage_scope_state") != "ROUTE_ORIGIN_CURRENT":
        return None
    output_id = (
        artifact.get("candidate_id")
        or artifact.get("program_id")
        or artifact.get("evidence_id")
        or artifact.get("proposal_id")
        or artifact.get("output_id")
    )
    record = {
        "run_id": lineage.get("run_id"),
        "task_id": lineage.get("task_id"),
        "origin_route_execution_id": artifact.get("origin_route_execution_id"),
        "origin_route_execution_ids": list(artifact.get("origin_route_execution_ids") or []),
        "origin_route_id": artifact.get("origin_route_id"),
        "origin_route_ids": list(artifact.get("origin_route_ids") or []),
        "route_lineage_origin_type": artifact.get("route_lineage_origin_type"),
        "route_lineage_scope_state": artifact.get("route_lineage_scope_state"),
        "output_type": output_type,
        "output_id": output_id,
        "candidate_id": artifact.get("candidate_id"),
        "program_id": artifact.get("program_id") or artifact.get("candidate_id"),
        "evidence_id": artifact.get("evidence_id"),
        "output_fingerprint": (
            artifact.get("program_signature")
            or artifact.get("output_fingerprint")
            or artifact.get("candidate_fingerprint")
        ),
        "operation": artifact.get("operation"),
        "program": artifact.get("program"),
        "producer_component": producer_component,
        "produced_at_stage": produced_at_stage,
        "validation_state": validation_state or artifact.get("validation_state") or artifact.get("validation_status"),
        "qualification_state": qualification_state or artifact.get("qualification_state"),
        "arena_state": arena_state or artifact.get("arena_state") or artifact.get("status"),
        "repair_state": repair_state or artifact.get("repair_state"),
        "downstream_consumers": list(artifact.get("downstream_consumers") or []),
    }
    if not record["origin_route_execution_ids"] and record["origin_route_execution_id"]:
        record["origin_route_execution_ids"] = [record["origin_route_execution_id"]]
    if not record["origin_route_ids"] and record["origin_route_id"]:
        record["origin_route_ids"] = [record["origin_route_id"]]
    return record


def build_route_contribution_manifest(
    *,
    context: Mapping[str, Any] | None,
    route_records: list[dict[str, Any]] | None = None,
    route_lifecycle_records: list[dict[str, Any]] | None = None,
    budget_report: Mapping[str, Any] | None = None,
    persist: bool = False,
    artifact_root: str | Path = "runtime/artifacts/route_contribution",
) -> dict[str, Any]:
    """Build a bounded, current-run route contribution manifest.

    The manifest is deliberately observational. It reads already-produced
    route/candidate/program/evidence/arena/repair records and never returns
    routing, ranking, budget, Arena, repair, truth, or execution decisions.
    """

    started = time.perf_counter()
    context = context if isinstance(context, Mapping) else {}
    budget_report = budget_report if isinstance(budget_report, Mapping) else {}
    run_id = _identity(
        context.get("run_id")
        or budget_report.get("run_id")
        or context.get("execution_id")
        or "current_run"
    )
    task_id = _identity(
        context.get("task_id")
        or budget_report.get("task_id")
        or context.get("task_path")
        or "current_task"
    )
    routes = _route_records(context, route_records)
    lifecycle = _list(route_lifecycle_records or context.get("route_lifecycle_records"))
    route_cap = _int(
        budget_report.get("maximum_active_routes")
        or budget_report.get("max_active_routes")
        or getattr(context.get("current_reasoning_budget"), "max_active_routes", None)
    )

    identity_state, identity_breaks = _validate_route_inputs(routes, lifecycle, run_id, task_id)
    identity_by_route_id = _route_identity_map(routes, run_id, task_id)
    lifecycle_by_route_id = _lifecycle_by_route(lifecycle)
    output_records = _scoped_outputs(context, identity_by_route_id, run_id, task_id)
    output_groups = _outputs_by_route(output_records)
    arena_records = _scoped_records(context, "route_arena_lineage_records", run_id, task_id)
    repair_records = _scoped_records(context, "route_repair_lineage_records", run_id, task_id)

    routes_out = []
    earlier_fingerprints: dict[str, str] = {}
    for route in sorted(routes, key=lambda row: (_int(row.get("route_rank")) or 10**9, str(row.get("route_id")))):
        route_id = _identity(route.get("route_id"))
        identity = identity_by_route_id[route_id]
        events = lifecycle_by_route_id.get(route_id, [])
        outputs = output_groups.get(identity["route_execution_id"], [])
        contribution = _classify_route(
            identity=identity,
            lifecycle=events,
            outputs=outputs,
            arena_records=arena_records,
            repair_records=repair_records,
            earlier_fingerprints=earlier_fingerprints,
        )
        for output in outputs:
            fingerprint = output.get("output_fingerprint")
            if fingerprint and fingerprint not in earlier_fingerprints:
                earlier_fingerprints[fingerprint] = identity["route_execution_id"]
        routes_out.append({
            **identity,
            "lifecycle_state": contribution["lifecycle_state"],
            "execution_state": contribution["execution_state"],
            "lineage_state": contribution["lineage_state"],
            "contribution_measurability_state": contribution[
                "contribution_measurability_state"
            ],
            "downstream_lineage_state": contribution["downstream_lineage_state"],
            "unmeasurable_reasons": contribution["unmeasurable_reasons"],
            "selected": True,
            "admitted": contribution["admitted"],
            "executed": contribution["executed"],
            "completed": contribution["completed"],
            "failed": contribution["failed"],
            "outputs": outputs,
            "candidate_ids": _ids(outputs, "candidate"),
            "program_ids": _ids(outputs, "program"),
            "evidence_ids": _ids(outputs, "evidence"),
            "arena_participation": contribution["arena_participation"],
            "repair_participation": contribution["repair_participation"],
            "output_count": len(outputs),
            "unique_output_count": contribution["unique_output_count"],
            "duplicate_output_count": contribution["duplicate_output_count"],
            "qualified_candidate_count": contribution["qualified_candidate_count"],
            "arena_candidate_count": contribution["arena_candidate_count"],
            "accepted_evidence_count": contribution["accepted_evidence_count"],
            "repair_contribution_count": contribution["repair_contribution_count"],
            "contribution_state": contribution["contribution_state"],
            "contribution_evidence": contribution["evidence"],
            "limitations": contribution["limitations"],
        })

    aggregate = _aggregate(routes_out, route_cap)
    continuity_state, continuity_breaks = _lineage_continuity(
        routes_out,
        output_records,
        identity_breaks,
    )
    completeness_state = _completeness_state(identity_state, continuity_state, routes_out)
    elapsed = round(time.perf_counter() - started, 6)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "system": "route_contribution_telemetry",
        "authority": AUTHORITY,
        "behavioral_authority": BEHAVIORAL_AUTHORITY,
        "telemetry_consumed_by_cognition": False,
        "run_id": run_id,
        "task_id": task_id,
        "route_cap": route_cap,
        "selected_routes": len(routes_out),
        "admitted_routes": aggregate["admitted_routes"],
        "executed_routes": aggregate["executed_routes"],
        "completed_routes": aggregate["completed_routes"],
        "routes": routes_out,
        "aggregate_summary": aggregate,
        "attribution_completeness_state": completeness_state,
        "lineage_continuity_state": continuity_state,
        "lineage_breaks": continuity_breaks,
        "identity_validation_state": identity_state,
        "identity_breaks": identity_breaks,
        "base_routes_definition": "route_position in 1..2",
        "marginal_routes_definition": "route_position in 3..6",
        "collection_cost": {
            "collection_time_seconds": elapsed,
            "manifest_size_bytes": 0,
            "record_count": len(routes_out) + len(output_records) + len(lifecycle),
        },
        "limitations": _limitations(routes_out, continuity_breaks),
        "created_at": str(datetime.utcnow()),
    }
    manifest["collection_cost"]["manifest_size_bytes"] = len(
        json.dumps(manifest, sort_keys=True, default=str)
    )
    if persist:
        manifest["artifact_path"] = str(_persist_manifest(manifest, artifact_root))
    return manifest


def compact_route_contribution_summary(manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    manifest = manifest if isinstance(manifest, Mapping) else {}
    aggregate = manifest.get("aggregate_summary") if isinstance(manifest.get("aggregate_summary"), Mapping) else {}
    return {
        "schema_version": manifest.get("schema_version", SCHEMA_VERSION),
        "authority": manifest.get("authority", AUTHORITY),
        "behavioral_authority": manifest.get("behavioral_authority", BEHAVIORAL_AUTHORITY),
        "attribution_state": manifest.get("attribution_completeness_state", "ROUTE_ATTRIBUTION_INSUFFICIENT"),
        "executed_route_attribution_state": manifest.get("attribution_completeness_state", "ROUTE_ATTRIBUTION_INSUFFICIENT"),
        "executed_route_attribution_scope": aggregate.get("executed_route_attribution_scope", "EXECUTED_ROUTES"),
        "lineage_state": manifest.get("lineage_continuity_state", "ROUTE_LINEAGE_BROKEN"),
        "selected_routes": aggregate.get("selected_routes", 0),
        "executed_routes": aggregate.get("executed_routes", 0),
        "unique_useful_routes": aggregate.get("routes_with_unique_useful_contribution", 0),
        "duplicate_routes": aggregate.get("routes_with_duplicate_contribution", 0),
        "low_value_routes": aggregate.get("routes_with_low_value_contribution", 0),
        "no_observable_routes": aggregate.get("routes_with_no_observable_contribution", 0),
        "unmeasurable_routes": aggregate.get("routes_with_unmeasurable_contribution", 0),
        "unmeasurable_routes_scope": aggregate.get("routes_with_unmeasurable_contribution_scope", "SELECTED_ROUTES"),
        "selected_routes_with_measurable_contribution": aggregate.get("selected_routes_with_measurable_contribution", 0),
        "selected_routes_with_unmeasurable_contribution": aggregate.get("selected_routes_with_unmeasurable_contribution", 0),
        "executed_routes_with_measurable_contribution": aggregate.get("executed_routes_with_measurable_contribution", 0),
        "executed_routes_with_unmeasurable_contribution": aggregate.get("executed_routes_with_unmeasurable_contribution", 0),
        "unmeasurable_because_not_executed": aggregate.get("unmeasurable_because_not_executed", 0),
        "unmeasurable_because_lineage_error": aggregate.get("unmeasurable_because_lineage_error", 0),
        "unmeasurable_because_insufficient_downstream_lineage": aggregate.get("unmeasurable_because_insufficient_downstream_lineage", 0),
        "unmeasurable_because_other": aggregate.get("unmeasurable_because_other", 0),
        "selected_route_partition_delta": aggregate.get("selected_route_partition_delta", 0),
        "selected_route_partition_integrity": aggregate.get("selected_route_partition_integrity", "PARTITION_INTEGRITY_FAILED"),
        "executed_route_partition_delta": aggregate.get("executed_route_partition_delta", 0),
        "executed_route_partition_integrity": aggregate.get("executed_route_partition_integrity", "PARTITION_INTEGRITY_FAILED"),
        "marginal_routes_executed": aggregate.get("marginal_routes_executed", 0),
        "marginal_routes_measurable": aggregate.get("marginal_routes_measurable", 0),
        "marginal_routes_unmeasurable": aggregate.get("marginal_routes_unmeasurable", 0),
        "marginal_useful_routes": aggregate.get("marginal_routes_useful_count", 0),
        "marginal_duplicate_routes": aggregate.get("marginal_duplicate_routes", 0),
        "marginal_low_value_routes": aggregate.get("marginal_low_value_routes", 0),
        "marginal_no_observable_routes": aggregate.get("marginal_no_observable_routes", 0),
        "marginal_unique_contribution_rate": aggregate.get("marginal_unique_contribution_rate", "NOT_MEASURABLE"),
        "marginal_redundancy_rate": aggregate.get("marginal_redundancy_rate", "NOT_MEASURABLE"),
        "artifact_path": manifest.get("artifact_path"),
        "telemetry_consumed_by_cognition": False,
    }


def _route_records(context: Mapping[str, Any], explicit: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if explicit:
        return [dict(row) for row in explicit if isinstance(row, Mapping)]
    report = context.get("route_selection_report")
    if isinstance(report, Mapping):
        routes = report.get("active_routes") or report.get("candidate_routes") or report.get("available_routes")
        if isinstance(routes, list):
            return [
                {
                    "route_id": row.get("route_id") or row.get("id") or f"route_{index}",
                    "route_rank": row.get("route_rank") or row.get("rank") or index,
                    "route_score": row.get("route_score") or row.get("score"),
                    "route_source": row.get("route_source") or row.get("source"),
                    "route_family": row.get("route_family") or row.get("family"),
                }
                for index, row in enumerate(routes, start=1)
                if isinstance(row, Mapping)
            ]
    return []


def _validate_route_inputs(
    routes: list[dict[str, Any]],
    lifecycle: list[dict[str, Any]],
    run_id: str,
    task_id: str,
) -> tuple[str, list[dict[str, Any]]]:
    breaks = []
    seen = set()
    for route in routes:
        route_id = _identity(route.get("route_id"))
        if route_id in seen:
            breaks.append({"break_type": "duplicate_route_id", "route_id": route_id})
        seen.add(route_id)
        if route.get("run_id") is not None and _identity(route.get("run_id")) != run_id:
            breaks.append({"break_type": "stale_previous_run_route_id", "route_id": route_id})
        if route.get("task_id") is not None and _identity(route.get("task_id")) != task_id:
            breaks.append({"break_type": "cross_task_route_attribution", "route_id": route_id})
    for row in lifecycle:
        route_id = _identity(row.get("route_id") or row.get("id"))
        if route_id and route_id not in seen:
            breaks.append({"break_type": "lifecycle_route_not_selected", "route_id": route_id})
        if row.get("run_id") is not None and _identity(row.get("run_id")) != run_id:
            breaks.append({"break_type": "stale_previous_run_route_id", "route_id": route_id})
        if row.get("task_id") is not None and _identity(row.get("task_id")) != task_id:
            breaks.append({"break_type": "cross_task_route_attribution", "route_id": route_id})
    return ("ROUTE_IDENTITY_CONFLICT" if breaks else "ROUTE_IDENTITY_VERIFIED", breaks)


def _route_identity_map(routes: list[dict[str, Any]], run_id: str, task_id: str) -> dict[str, dict[str, Any]]:
    identities = {}
    for index, route in enumerate(
        sorted(routes, key=lambda row: (_int(row.get("route_rank")) or 10**9, str(row.get("route_id")))),
        start=1,
    ):
        route_id = _identity(route.get("route_id") or f"route_{index}")
        family = _identity(route.get("route_family") or route.get("family") or route.get("route_source") or "unknown_route_family")
        source = _identity(route.get("route_source") or route.get("source") or "unknown_route_source")
        semantic_payload = {
            "route_id": route_id,
            "route_family": family,
            "route_source": source,
            "route_score": route.get("route_score"),
            "route_rank": route.get("route_rank"),
        }
        route_fingerprint = _stable_id("route_fingerprint", semantic_payload)
        identities[route_id] = {
            "route_execution_id": route.get("route_execution_id") or _stable_id(
                "route_execution",
                {
                    "run_id": run_id,
                    "task_id": task_id,
                    "route_id": route_id,
                    "route_position": _int(route.get("route_rank")) or index,
                    "route_fingerprint": route_fingerprint,
                },
            ),
            "run_id": run_id,
            "task_id": task_id,
            "route_id": route_id,
            "route_position": _int(route.get("route_rank")) or index,
            "route_family": family,
            "route_source": source,
            "route_fingerprint": route_fingerprint,
        }
    return identities


def _lifecycle_by_route(lifecycle: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in lifecycle:
        if not isinstance(row, Mapping):
            continue
        route_id = _identity(row.get("route_id") or row.get("id"))
        if route_id:
            grouped.setdefault(route_id, []).append(dict(row))
    return grouped


def _scoped_outputs(
    context: Mapping[str, Any],
    identity_by_route_id: Mapping[str, Mapping[str, Any]],
    run_id: str,
    task_id: str,
) -> list[dict[str, Any]]:
    records = []
    for key in (
        "route_output_lineage_records",
        "candidate_lineage_records",
        "program_lineage_records",
        "evidence_lineage_records",
    ):
        for row in _scoped_records(context, key, run_id, task_id):
            output = _output_record(row, identity_by_route_id, run_id, task_id, key)
            records.append(output)
    return records


def _scoped_records(context: Mapping[str, Any], key: str, run_id: str, task_id: str) -> list[dict[str, Any]]:
    records = []
    for row in _list(context.get(key)):
        if not isinstance(row, Mapping):
            continue
        copied = deepcopy(dict(row))
        if copied.get("run_id") is not None and _identity(copied.get("run_id")) != run_id:
            copied["lineage_error"] = "STALE_PREVIOUS_RUN_LINEAGE"
        if copied.get("task_id") is not None and _identity(copied.get("task_id")) != task_id:
            copied["lineage_error"] = "CROSS_TASK_LINEAGE"
        copied.setdefault("run_id", run_id)
        copied.setdefault("task_id", task_id)
        records.append(copied)
    return records


def _output_record(
    row: Mapping[str, Any],
    identity_by_route_id: Mapping[str, Mapping[str, Any]],
    run_id: str,
    task_id: str,
    source_key: str,
) -> dict[str, Any]:
    route_ids = row.get("origin_route_execution_ids")
    if not isinstance(route_ids, list):
        route_ids = []
    route_execution_id = row.get("origin_route_execution_id") or row.get("route_execution_id")
    route_id = row.get("origin_route_id") or row.get("route_id")
    if not route_execution_id and route_id in identity_by_route_id:
        route_execution_id = identity_by_route_id[str(route_id)]["route_execution_id"]
    if route_execution_id and route_execution_id not in route_ids:
        route_ids.insert(0, route_execution_id)
    output_type = _output_type(row, source_key)
    output_id = (
        row.get("output_id")
        or row.get("candidate_id")
        or row.get("program_id")
        or row.get("evidence_id")
        or row.get("accepted_evidence_id")
        or _stable_id("route_output", dict(row))
    )
    fingerprint = row.get("output_fingerprint") or row.get("candidate_fingerprint") or row.get("program_fingerprint")
    if not fingerprint:
        fingerprint = _stable_id(
            f"{output_type}_fingerprint",
            {
                "type": output_type,
                "id": output_id,
                "operation": row.get("operation"),
                "program": row.get("program"),
                "signature": row.get("program_signature") or row.get("signature"),
                "evidence_type": row.get("evidence_type"),
            },
        )
    return {
        "route_execution_id": route_execution_id,
        "origin_route_execution_ids": route_ids,
        "run_id": run_id,
        "task_id": task_id,
        "output_type": output_type,
        "output_id": str(output_id),
        "output_fingerprint": str(fingerprint),
        "producer_component": row.get("producer_component") or row.get("source") or source_key,
        "produced_at_stage": row.get("produced_at_stage") or source_key,
        "downstream_consumers": list(row.get("downstream_consumers") or []),
        "candidate_id": row.get("candidate_id"),
        "program_id": row.get("program_id"),
        "evidence_id": row.get("evidence_id") or row.get("accepted_evidence_id"),
        "validation_state": row.get("validation_state") or row.get("validation_status"),
        "qualification_state": row.get("qualification_state"),
        "arena_state": row.get("arena_state") or row.get("arena_status"),
        "repair_state": row.get("repair_state"),
        "residual_reduction": _float(row.get("residual_reduction")),
        "lineage_error": row.get("lineage_error"),
        "raw_lineage_record": deepcopy(dict(row)),
    }


def _classify_route(
    *,
    identity: Mapping[str, Any],
    lifecycle: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
    arena_records: list[dict[str, Any]],
    repair_records: list[dict[str, Any]],
    earlier_fingerprints: dict[str, str],
) -> dict[str, Any]:
    states = {str(row.get("state") or row.get("lifecycle_state") or "") for row in lifecycle}
    admitted = bool(states & (ADMITTED_STATES | ACTIVE_STATES | COMPLETED_STATES | FAILED_STATES)) or bool(outputs)
    executed = bool(states & ACTIVE_STATES) or bool(outputs)
    completed = bool(states & COMPLETED_STATES)
    failed = bool(states & FAILED_STATES)
    deferred = bool(states & DEFERRED_STATES)
    rejected = bool(states & REJECTED_STATES)
    if failed:
        lifecycle_state = "ROUTE_FAILED"
    elif completed:
        lifecycle_state = "ROUTE_COMPLETED"
    elif executed:
        lifecycle_state = "ROUTE_EXECUTED"
    elif admitted:
        lifecycle_state = "ROUTE_ADMITTED"
    elif deferred:
        lifecycle_state = "ROUTE_DEFERRED"
    elif rejected:
        lifecycle_state = "ROUTE_REJECTED"
    else:
        lifecycle_state = "ROUTE_SELECTED"

    current_outputs = [row for row in outputs if row.get("route_execution_id") == identity["route_execution_id"] or identity["route_execution_id"] in row.get("origin_route_execution_ids", [])]
    duplicate_outputs = [
        row for row in current_outputs
        if row.get("output_fingerprint") in earlier_fingerprints
        and len(row.get("origin_route_execution_ids") or []) <= 1
    ]
    unique_outputs = [
        row for row in current_outputs
        if row.get("output_fingerprint") not in earlier_fingerprints
        or len(row.get("origin_route_execution_ids") or []) > 1
    ]
    useful = [row for row in unique_outputs if _output_useful(row)]
    low_value = [row for row in unique_outputs if _output_low_value(row)]
    lineage_errors = [row.get("lineage_error") for row in current_outputs if row.get("lineage_error")]
    route_arena = [
        row for row in arena_records
        if _route_match(row, identity["route_execution_id"])
    ]
    route_repair = [
        row for row in repair_records
        if _route_match(row, identity["route_execution_id"])
    ]
    repair_contrib = [
        row for row in route_repair
        if _float(row.get("residual_reduction")) > 0
    ]

    limitations = []
    evidence = []
    unmeasurable_reasons = []
    if lineage_errors:
        limitations.extend(str(item) for item in lineage_errors)
    if not executed and (deferred or rejected):
        contribution_state = "CONTRIBUTION_NOT_MEASURABLE"
        limitations.append("route_not_executed")
        unmeasurable_reasons.append("route_not_executed")
    elif lineage_errors:
        contribution_state = "CONTRIBUTION_NOT_MEASURABLE"
        unmeasurable_reasons.append("lineage_error")
    elif useful or repair_contrib:
        contribution_state = "UNIQUE_USEFUL_CONTRIBUTION"
        evidence.append("distinct_output_used_downstream")
    elif current_outputs and len(duplicate_outputs) == len(current_outputs):
        contribution_state = "DUPLICATE_CONTRIBUTION"
        evidence.append("all_meaningful_outputs_match_earlier_fingerprints")
    elif low_value:
        contribution_state = "LOW_VALUE_CONTRIBUTION"
        evidence.append("distinct_output_rejected_or_dominated")
    elif executed and not current_outputs:
        contribution_state = "NO_OBSERVABLE_CONTRIBUTION"
        evidence.append("route_executed_without_linked_output")
    else:
        contribution_state = "CONTRIBUTION_NOT_MEASURABLE"
        limitations.append("insufficient_downstream_lineage")
        unmeasurable_reasons.append("insufficient_downstream_lineage")

    contribution_measurable = contribution_state != "CONTRIBUTION_NOT_MEASURABLE"
    downstream_lineage_sufficient = (
        contribution_measurable or contribution_state == "NO_OBSERVABLE_CONTRIBUTION"
    )

    return {
        "lifecycle_state": lifecycle_state,
        "execution_state": "EXECUTED" if executed else "NOT_EXECUTED",
        "lineage_state": "LINEAGE_ERROR" if lineage_errors else "LINEAGE_VERIFIED",
        "contribution_measurability_state": (
            "CONTRIBUTION_MEASURABLE"
            if contribution_measurable
            else "CONTRIBUTION_NOT_MEASURABLE"
        ),
        "downstream_lineage_state": (
            "DOWNSTREAM_LINEAGE_SUFFICIENT"
            if downstream_lineage_sufficient
            else "DOWNSTREAM_LINEAGE_INSUFFICIENT"
        ),
        "unmeasurable_reasons": sorted(set(unmeasurable_reasons)),
        "admitted": admitted,
        "executed": executed,
        "completed": completed,
        "failed": failed,
        "arena_participation": bool(route_arena or any(_arena_participates(row) for row in current_outputs)),
        "repair_participation": bool(route_repair or any(_repair_participates(row) for row in current_outputs)),
        "unique_output_count": len(unique_outputs),
        "duplicate_output_count": len(duplicate_outputs),
        "qualified_candidate_count": len([
            row for row in current_outputs
            if row.get("output_type") == "candidate"
            and row.get("qualification_state") == "QUALIFIED"
        ]),
        "arena_candidate_count": len([
            row for row in current_outputs
            if row.get("output_type") == "candidate" and _arena_participates(row)
        ]),
        "accepted_evidence_count": len([
            row for row in current_outputs
            if row.get("output_type") == "evidence"
            and row.get("validation_state") in {"ACCEPTED", "EVIDENCE_USED_IN_DECISION", "EVIDENCE_DECISIVE"}
        ]),
        "repair_contribution_count": len(repair_contrib),
        "contribution_state": contribution_state,
        "evidence": evidence,
        "limitations": sorted(set(limitations)),
    }


def _aggregate(routes: list[dict[str, Any]], route_cap: int | None) -> dict[str, Any]:
    executed = [row for row in routes if row.get("executed")]
    marginal = [row for row in executed if 3 <= int(row.get("route_position") or 0) <= 6]
    useful = [row for row in routes if row.get("contribution_state") == "UNIQUE_USEFUL_CONTRIBUTION"]
    duplicate = [row for row in routes if row.get("contribution_state") == "DUPLICATE_CONTRIBUTION"]
    low_value = [row for row in routes if row.get("contribution_state") == "LOW_VALUE_CONTRIBUTION"]
    no_observable = [row for row in routes if row.get("contribution_state") == "NO_OBSERVABLE_CONTRIBUTION"]
    unmeasurable = [row for row in routes if row.get("contribution_state") == "CONTRIBUTION_NOT_MEASURABLE"]
    executed_useful = [row for row in executed if row.get("contribution_state") == "UNIQUE_USEFUL_CONTRIBUTION"]
    executed_duplicate = [row for row in executed if row.get("contribution_state") == "DUPLICATE_CONTRIBUTION"]
    executed_low_value = [row for row in executed if row.get("contribution_state") == "LOW_VALUE_CONTRIBUTION"]
    executed_no_observable = [row for row in executed if row.get("contribution_state") == "NO_OBSERVABLE_CONTRIBUTION"]
    executed_unmeasurable = [row for row in executed if row.get("contribution_state") == "CONTRIBUTION_NOT_MEASURABLE"]
    marginal_useful = [row for row in marginal if row.get("contribution_state") == "UNIQUE_USEFUL_CONTRIBUTION"]
    marginal_duplicate = [row for row in marginal if row.get("contribution_state") == "DUPLICATE_CONTRIBUTION"]
    marginal_low_value = [row for row in marginal if row.get("contribution_state") == "LOW_VALUE_CONTRIBUTION"]
    marginal_no_observable = [row for row in marginal if row.get("contribution_state") == "NO_OBSERVABLE_CONTRIBUTION"]
    marginal_unmeasurable = [row for row in marginal if row.get("contribution_state") == "CONTRIBUTION_NOT_MEASURABLE"]
    selected_partition_total = (
        len(useful) + len(duplicate) + len(low_value) + len(no_observable)
        + len(unmeasurable)
    )
    executed_partition_total = (
        len(executed_useful) + len(executed_duplicate) + len(executed_low_value)
        + len(executed_no_observable) + len(executed_unmeasurable)
    )
    reason_counts = _unmeasurable_reason_counts(unmeasurable)
    return {
        "selected_routes": len(routes),
        "admitted_routes": len([row for row in routes if row.get("admitted")]),
        "executed_routes": len(executed),
        "completed_routes": len([row for row in routes if row.get("completed")]),
        "routes_with_unique_useful_contribution": len(useful),
        "routes_with_duplicate_contribution": len(duplicate),
        "routes_with_low_value_contribution": len(low_value),
        "routes_with_no_observable_contribution": len(no_observable),
        "routes_with_unmeasurable_contribution": len(unmeasurable),
        "routes_with_unmeasurable_contribution_scope": "SELECTED_ROUTES",
        "selected_routes_with_measurable_contribution": len(routes) - len(unmeasurable),
        "selected_routes_with_unmeasurable_contribution": len(unmeasurable),
        "executed_routes_with_measurable_contribution": len(executed) - len(executed_unmeasurable),
        "executed_routes_with_unmeasurable_contribution": len(executed_unmeasurable),
        "unmeasurable_because_not_executed": reason_counts["route_not_executed"],
        "unmeasurable_because_lineage_error": reason_counts["lineage_error"],
        "unmeasurable_because_insufficient_downstream_lineage": reason_counts["insufficient_downstream_lineage"],
        "unmeasurable_because_other": reason_counts["other"],
        "selected_route_partition_delta": len(routes) - selected_partition_total,
        "selected_route_partition_integrity": (
            "VERIFIED"
            if len(routes) == selected_partition_total
            else "PARTITION_INTEGRITY_FAILED"
        ),
        "executed_route_partition_delta": len(executed) - executed_partition_total,
        "executed_route_partition_integrity": (
            "VERIFIED"
            if len(executed) == executed_partition_total
            else "PARTITION_INTEGRITY_FAILED"
        ),
        "executed_route_attribution_scope": "EXECUTED_ROUTES",
        "base_routes_useful_count": len([
            row for row in useful if int(row.get("route_position") or 0) <= 2
        ]),
        "marginal_routes_useful_count": len(marginal_useful),
        "marginal_routes_admitted": len([
            row for row in routes
            if row.get("admitted") and 3 <= int(row.get("route_position") or 0) <= 6
        ]),
        "marginal_routes_executed": len(marginal),
        "marginal_unique_outputs": sum(int(row.get("unique_output_count") or 0) for row in marginal),
        "marginal_duplicate_outputs": sum(int(row.get("duplicate_output_count") or 0) for row in marginal),
        "marginal_routes_measurable": len(marginal) - len(marginal_unmeasurable),
        "marginal_routes_unmeasurable": len(marginal_unmeasurable),
        "marginal_unique_useful_routes": len(marginal_useful),
        "marginal_duplicate_routes": len(marginal_duplicate),
        "marginal_low_value_routes": len(marginal_low_value),
        "marginal_no_observable_routes": len(marginal_no_observable),
        "marginal_useful_contributions": len(marginal_useful),
        "marginal_duplicate_route_count": len(marginal_duplicate),
        "marginal_low_value_contributions": len(marginal_low_value),
        "marginal_unmeasurable_contributions": len(marginal_unmeasurable),
        "unique_contribution_rate": _rate(len(useful), len(executed)),
        "marginal_unique_contribution_rate": _rate(len(marginal_useful), len(marginal)),
        "route_redundancy_rate": _rate(len(duplicate), len(executed)),
        "marginal_redundancy_rate": _rate(len(marginal_duplicate), len(marginal)),
        "arena_candidates_from_base_routes": sum(
            int(row.get("arena_candidate_count") or 0)
            for row in routes
            if int(row.get("route_position") or 0) <= 2
        ),
        "arena_candidates_from_marginal_routes": sum(
            int(row.get("arena_candidate_count") or 0)
            for row in marginal
        ),
        "repair_contributions_from_base_routes": sum(
            int(row.get("repair_contribution_count") or 0)
            for row in routes
            if int(row.get("route_position") or 0) <= 2
        ),
        "repair_contributions_from_marginal_routes": sum(
            int(row.get("repair_contribution_count") or 0)
            for row in marginal
        ),
        "route_cap": route_cap,
    }


def _unmeasurable_reason_counts(routes: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "route_not_executed": 0,
        "lineage_error": 0,
        "insufficient_downstream_lineage": 0,
        "other": 0,
    }
    for route in routes:
        reasons = [
            str(reason)
            for reason in route.get("unmeasurable_reasons", [])
            if reason
        ]
        matched = False
        for reason in reasons:
            if reason in counts and reason != "other":
                counts[reason] += 1
                matched = True
        if not matched:
            counts["other"] += 1
    return counts


def _lineage_continuity(
    routes: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
    identity_breaks: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    breaks = list(identity_breaks)
    route_ids = {row["route_execution_id"] for row in routes}
    for output in outputs:
        origins = [
            item for item in output.get("origin_route_execution_ids", [])
            if item
        ]
        if not origins:
            breaks.append({
                "break_type": "candidate_with_no_route_lineage"
                if output.get("output_type") == "candidate"
                else "output_with_no_route_lineage",
                "output_id": output.get("output_id"),
                "missing_identity_field": "origin_route_execution_id",
            })
        for origin in origins:
            if origin not in route_ids:
                breaks.append({
                    "break_type": "candidate_attributed_to_wrong_route",
                    "output_id": output.get("output_id"),
                    "route_execution_id": origin,
                })
    if not routes:
        return "ROUTE_LINEAGE_BROKEN", breaks
    if not breaks:
        return "ROUTE_LINEAGE_CONTINUITY_VERIFIED", []
    if breaks and outputs:
        return "ROUTE_LINEAGE_PARTIAL", breaks
    return "ROUTE_LINEAGE_BROKEN", breaks


def _completeness_state(identity_state: str, continuity_state: str, routes: list[dict[str, Any]]) -> str:
    if identity_state != "ROUTE_IDENTITY_VERIFIED":
        return "ROUTE_ATTRIBUTION_INSUFFICIENT"
    if continuity_state == "ROUTE_LINEAGE_CONTINUITY_VERIFIED" and all(
        row.get("contribution_state") != "CONTRIBUTION_NOT_MEASURABLE"
        for row in routes
        if row.get("executed")
    ):
        return "ROUTE_ATTRIBUTION_COMPLETE"
    if routes:
        return "ROUTE_ATTRIBUTION_PARTIAL"
    return "ROUTE_ATTRIBUTION_INSUFFICIENT"


def _limitations(routes: list[dict[str, Any]], breaks: list[dict[str, Any]]) -> list[str]:
    values = []
    if breaks:
        values.append("lineage_continuity_breaks_present")
    if any(row.get("contribution_state") == "CONTRIBUTION_NOT_MEASURABLE" for row in routes):
        values.append("some_route_contribution_not_measurable")
    return values


def _persist_manifest(manifest: Mapping[str, Any], artifact_root: str | Path) -> Path:
    root = Path(artifact_root)
    root.mkdir(parents=True, exist_ok=True)
    run = _safe(manifest.get("run_id"))
    task = _stable_id("task", manifest.get("task_id"))
    path = root / f"{run}_{task}_route_contribution_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return path


def _outputs_by_route(outputs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for output in outputs:
        origins = output.get("origin_route_execution_ids") or []
        for origin in origins:
            if origin:
                grouped.setdefault(str(origin), []).append(output)
    return grouped


def _output_type(row: Mapping[str, Any], source_key: str) -> str:
    if row.get("output_type"):
        return str(row.get("output_type"))
    if "candidate" in source_key or row.get("candidate_id"):
        return "candidate"
    if "program" in source_key or row.get("program_id"):
        return "program"
    if "evidence" in source_key or row.get("evidence_id") or row.get("accepted_evidence_id"):
        return "evidence"
    return "cognitive_artifact"


def _output_useful(row: Mapping[str, Any]) -> bool:
    values = {
        str(row.get("validation_state") or ""),
        str(row.get("qualification_state") or ""),
        str(row.get("arena_state") or ""),
        str(row.get("repair_state") or ""),
    }
    if values & USEFUL_STATES:
        return True
    if _float(row.get("residual_reduction")) > 0:
        return True
    return False


def _output_low_value(row: Mapping[str, Any]) -> bool:
    values = {
        str(row.get("validation_state") or ""),
        str(row.get("qualification_state") or ""),
        str(row.get("arena_state") or ""),
        str(row.get("repair_state") or ""),
    }
    return bool(values & LOW_VALUE_STATES)


def _arena_participates(row: Mapping[str, Any]) -> bool:
    return str(row.get("arena_state") or "") in USEFUL_STATES | LOW_VALUE_STATES | {"EVALUATED", "RUNNER_UP", "TIE_PARTICIPANT"}


def _repair_participates(row: Mapping[str, Any]) -> bool:
    return bool(row.get("repair_state") or _float(row.get("residual_reduction")) > 0)


def _route_match(row: Mapping[str, Any], route_execution_id: str) -> bool:
    return (
        row.get("route_execution_id") == route_execution_id
        or row.get("origin_route_execution_id") == route_execution_id
        or route_execution_id in (row.get("origin_route_execution_ids") or [])
    )


def _validate_route_origin_lineage(
    manifest: Mapping[str, Any],
    lineage: Mapping[str, Any],
) -> str:
    run_id = _identity(manifest.get("run_id"))
    task_id = _identity(manifest.get("task_id"))
    if _identity(lineage.get("run_id")) != run_id:
        return "STALE_PREVIOUS_RUN_LINEAGE"
    if _identity(lineage.get("task_id")) != task_id:
        return "CROSS_TASK_LINEAGE"
    route_execution_id = _identity(lineage.get("route_execution_id"))
    if not route_execution_id:
        return "ROUTE_ORIGIN_NOT_OBSERVABLE"
    for route in _list(manifest.get("routes")):
        if not isinstance(route, Mapping):
            continue
        if _identity(route.get("route_execution_id")) != route_execution_id:
            continue
        if route.get("admitted") is not True:
            return "ROUTE_ORIGIN_NOT_ADMITTED"
        if route.get("executed") is not True:
            return "ROUTE_ORIGIN_NOT_EXECUTED"
        return "ROUTE_ORIGIN_CURRENT"
    return "ROUTE_ORIGIN_UNKNOWN"


def _route_for_source_descriptor(
    manifest: Mapping[str, Any],
    descriptors: list[Any],
) -> dict[str, Any] | None:
    routes = [row for row in _list(manifest.get("routes")) if isinstance(row, Mapping)]
    if not routes:
        return None
    route_by_id = {
        _runtime_token(row.get("route_id")): row
        for row in routes
        if row.get("route_id")
    }
    for descriptor in descriptors:
        tokens = _descriptor_tokens(descriptor)
        for token in tokens:
            candidates = [token]
            candidates.extend(sorted(SOURCE_ROUTE_ALIASES.get(token, set())))
            for candidate in candidates:
                route = route_by_id.get(candidate)
                if (
                    isinstance(route, Mapping)
                    and route.get("admitted") is True
                    and route.get("executed") is True
                ):
                    return dict(route)
    return None


def _descriptor_tokens(value: Any) -> list[str]:
    raw = _runtime_token(value)
    if not raw:
        return []
    tokens = {raw}
    for part in raw.replace(":", "_").replace(".", "_").split("_"):
        if part:
            tokens.add(part)
    if "color" in raw:
        tokens.add("color")
    if "identity" in raw or "preserve" in raw:
        tokens.add("identity")
    if "object" in raw:
        tokens.add("object")
    if "dependency" in raw:
        tokens.add("dependency")
    if "causal" in raw:
        tokens.add("causal")
    if "contradiction" in raw:
        tokens.add("contradiction")
    if "spatial" in raw:
        tokens.add("spatial")
    if "semantic" in raw and "compiler" in raw:
        tokens.add("semantic_to_transformation_compiler")
    if "transformation" in raw:
        tokens.add("transformation")
    return sorted(tokens)


def _record_metadata_value(record: Mapping[str, Any], key: str) -> Any:
    metadata = record.get("metadata")
    if isinstance(metadata, Mapping):
        return metadata.get(key)
    return None


def _runtime_token(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _ids(outputs: list[dict[str, Any]], output_type: str) -> list[str]:
    values = []
    key = f"{output_type}_id"
    for output in outputs:
        if output.get("output_type") == output_type and output.get(key):
            values.append(str(output[key]))
    return sorted(set(values))


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _identity(value: Any) -> str:
    return str(value or "").strip()


def _int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float:
    if value is None or isinstance(value, bool):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _rate(numerator: int, denominator: int) -> float | str:
    if denominator <= 0:
        return "NOT_MEASURABLE"
    return round(numerator / denominator, 4)


def _stable_id(prefix: str, payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


def _safe(value: Any) -> str:
    token = str(value or "current_run")
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in token)[:120]


__all__ = [
    "ROUTE_LINEAGE_FIELDS",
    "attach_route_origin_lineage",
    "build_route_contribution_manifest",
    "compact_route_contribution_summary",
    "route_lineage_record_from_artifact",
    "route_origin_lineage_from_record",
]
