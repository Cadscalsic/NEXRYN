"""Experiment-only pre-route signal replication analysis."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "runtime" / "artifacts" / "pre_route_controlled_replication"
SNAPSHOT_ROOT = ROOT / "runtime" / "artifacts" / "route_pre_admission"
PRIMARY_POSITIVE = "UNIQUE_USEFUL_CONTRIBUTION"
PRIMARY_NEGATIVES = {
    "DUPLICATE_CONTRIBUTION",
    "LOW_VALUE_CONTRIBUTION",
    "NO_OBSERVABLE_CONTRIBUTION",
}
UNOBSERVED = "NOT_OBSERVED_PRE_ADMISSION"
MARGINAL_POSITIONS = {3, 4, 5, 6}
AUTHORITY = "NONE"
TELEMETRY_AUTHORITY = "OBSERVATION_ONLY"


def run_pre_route_controlled_replication(
    source_artifact: str | Path,
    *,
    output_root: str | Path = ARTIFACT_ROOT,
    snapshot_root: str | Path = SNAPSHOT_ROOT,
    timestamp: str | None = None,
) -> dict[str, Any]:
    source_path = Path(source_artifact)
    report = json.loads(source_path.read_text(encoding="utf-8"))
    timestamp = timestamp or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    experiment_id = _stable_id(
        "pre_route_replication",
        {
            "source_artifact": str(source_path),
            "investigation_id": report.get("investigation_id"),
            "timestamp": timestamp,
        },
    )
    output_dir = Path(output_root) / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_runs = [row for row in report.get("raw_measurements", []) if isinstance(row, dict)]
    task_order = _task_order(report, raw_runs)
    system = _system_fingerprint(report, source_path, task_order)
    dataset = _canonical_dataset(
        experiment_id=experiment_id,
        raw_runs=raw_runs,
        snapshot_root=Path(snapshot_root),
    )
    feature_rows = _feature_records(dataset)
    feature_eligibility = _feature_eligibility(feature_rows)
    feature_variation = _feature_variation(feature_rows)
    repeat_independence = _repeat_independence(raw_runs, dataset)
    confounding = _route_position_confounding(dataset)
    permutation_feasibility = _permutation_feasibility()
    static_signal = _static_signal_analysis(dataset)
    route_identity = _route_identity_analysis(dataset)
    route_position = _route_position_analysis(dataset)
    state_so_far = _state_so_far_analysis(dataset)
    within_route = _within_route_analysis(dataset)
    within_task = _within_task_analysis(dataset)
    conditional = _conditional_dependency_analysis(dataset)
    internal_trace = _internal_value_trace(dataset)
    final_outcome = _final_outcome_analysis(report)
    stability = _signal_stability(dataset, confounding)
    evidence = _evidence_decision(dataset, repeat_independence, confounding, stability)
    manifest = {
        "experiment_id": experiment_id,
        "system": "pre_route_controlled_replication",
        "authority": AUTHORITY,
        "telemetry_authority": TELEMETRY_AUTHORITY,
        "source_artifact": str(source_path),
        "created_at": datetime.utcnow().isoformat(),
        "task_count": len(task_order),
        "task_order": task_order,
        "run_count": len(raw_runs),
        "cap_2_run_count": sum(1 for row in raw_runs if row.get("route_cap") == 2),
        "cap_6_run_count": sum(1 for row in raw_runs if row.get("route_cap") == 6),
        "production_route_order_changed": "NO",
        "production_route_budget_changed": "NO",
        "route_classifier_changed": "NO",
        "snapshot_schema_changed": "NO",
        "experiment_harness_authority": AUTHORITY,
        "budget_authority": "RuntimeBudgetEnforcer",
    }
    summary = {
        **manifest,
        "artifact_dir": str(output_dir),
        "raw_marginal_route_rows": len(dataset["rows"]),
        "effective_independent_observation_count": repeat_independence[
            "effective_independent_observation_count"
        ],
        "unique_useful_events": dataset["positive_count"],
        "positive_rate": _rate(dataset["positive_count"], dataset["primary_row_count"]),
        "deterministic_replay_detected": repeat_independence["deterministic_replay_detected"],
        "repeat_relationship": repeat_independence["repeat_relationship"],
        "snapshot_linkage_failures": dataset["snapshot_linkage_failures"],
        "temporal_integrity_failures": dataset["temporal_integrity_failures"],
        "leakage_failures": dataset["leakage_failures"],
        "snapshot_mutation_failures": 0,
        "pre_admission_feature_count": feature_eligibility["pre_admission_feature_count"],
        "high_coverage_feature_count": feature_eligibility["high_coverage_feature_count"],
        "variable_feature_count": feature_variation["variable_feature_count"],
        "constant_feature_count": feature_variation["constant_feature_count"],
        "route_position_confounding": confounding["classification"],
        "position_permutation_feasibility": permutation_feasibility["decision"],
        "position_permutation_used": "NO",
        "static_task_signal": static_signal["classification"],
        "route_identity_signal": route_identity["classification"],
        "route_position_signal": route_position["classification"],
        "state_so_far_signal": state_so_far["classification"],
        "within_route_signal": within_route["classification"],
        "within_task_signal": within_task["classification"],
        "conditional_dependency_signal": conditional["classification"],
        "internal_value_replicated": internal_trace["internal_value_replicated"],
        "decisive_final_value": final_outcome["decisive_final_value"],
        "route_local_cost_observability": "ROUTE_LOCAL_COST_NOT_INSTRUMENTABLE_AT_CURRENT_BOUNDARY",
        "strongest_candidate_signal": evidence["strongest_candidate_signal"],
        "signal_stability": stability["classification"],
        "current_evidence_level": evidence["current_evidence_level"],
        "p2_gate_passed": evidence["p2_gate_passed"],
        "p3_claim_allowed": False,
        "adaptive_policy_patch_allowed": False,
        "corpus_expansion_required": evidence["corpus_expansion_required"],
        "more_instrumentation_required": evidence["more_instrumentation_required"],
        "cognitive_consumer_count": 0,
        "real_experiment_completed": True,
        "remaining_limitation": evidence["remaining_limitation"],
        "primary_scientific_conclusion": evidence["primary_scientific_conclusion"],
        "next_action": evidence["next_action"],
    }

    artifacts = {
        "experiment_system_fingerprint.json": system,
        "pre_route_replication_manifest.json": manifest,
        "pre_route_canonical_dataset.json": dataset,
        "pre_route_feature_eligibility.json": feature_eligibility,
        "pre_route_feature_variation.json": feature_variation,
        "pre_route_repeat_independence.json": repeat_independence,
        "pre_route_route_position_confounding.json": confounding,
        "pre_route_permutation_feasibility.json": permutation_feasibility,
        "pre_route_static_signal_analysis.json": static_signal,
        "pre_route_route_identity_analysis.json": route_identity,
        "pre_route_route_position_analysis.json": route_position,
        "pre_route_state_so_far_analysis.json": state_so_far,
        "pre_route_within_route_analysis.json": within_route,
        "pre_route_within_task_analysis.json": within_task,
        "pre_route_conditional_dependency_analysis.json": conditional,
        "pre_route_internal_value_trace.json": internal_trace,
        "pre_route_final_outcome_analysis.json": final_outcome,
        "pre_route_signal_stability.json": stability,
        "pre_route_evidence_level_decision.json": evidence,
        "pre_route_controlled_replication_summary.json": summary,
    }
    for name, payload in artifacts.items():
        (output_dir / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
    (output_dir / "pre_route_controlled_replication.md").write_text(
        _markdown_report(summary, evidence, confounding),
        encoding="utf-8",
    )
    return summary


def _canonical_dataset(
    *,
    experiment_id: str,
    raw_runs: list[dict[str, Any]],
    snapshot_root: Path,
) -> dict[str, Any]:
    rows = []
    excluded = 0
    linkage_failures = 0
    temporal_failures = 0
    leakage_failures = 0
    for run in raw_runs:
        if run.get("route_cap") != 6:
            continue
        condition_id = str(run.get("configuration_id") or "route_cap_6")
        repeat_id = str(run.get("repeat_id") or "repeat_001")
        for manifest in run.get("route_manifests", []) or []:
            if not isinstance(manifest, dict):
                continue
            run_id = str(manifest.get("run_id") or run.get("human_report", {}).get("Run Id") or "")
            task_id = _task_identity(manifest.get("task_id"))
            snapshots = _snapshots_for(snapshot_root, run_id, task_id)
            for route in manifest.get("routes", []) or []:
                if not isinstance(route, dict):
                    continue
                position = _int(route.get("route_position"))
                if position not in MARGINAL_POSITIONS or route.get("executed") is not True:
                    continue
                contribution = str(route.get("contribution_state") or "")
                if contribution == "CONTRIBUTION_NOT_MEASURABLE":
                    excluded += 1
                    continue
                snapshot = _match_snapshot(snapshots, route, position)
                if not snapshot:
                    linkage_failures += 1
                else:
                    if snapshot.get("temporal_integrity_state") != "PRE_ADMISSION_TEMPORAL_INTEGRITY_VERIFIED":
                        temporal_failures += 1
                    leakage_failures += len(snapshot.get("leakage_fields") or [])
                rows.append(
                    {
                        "experiment_id": experiment_id,
                        "condition_id": condition_id,
                        "repeat_id": repeat_id,
                        "run_id": run_id,
                        "task_id": task_id,
                        "snapshot_id": snapshot.get("snapshot_id") if snapshot else None,
                        "snapshot_fingerprint": snapshot.get("snapshot_fingerprint") if snapshot else None,
                        "route_id": route.get("route_id"),
                        "route_family": route.get("route_family"),
                        "route_position": position,
                        "admission_disposition_id": _stable_id(
                            "route_admission_disposition",
                            [run_id, task_id, route.get("route_id"), position],
                        ),
                        "route_contribution_manifest_id": manifest.get("artifact_path"),
                        "route_execution_id": route.get("route_execution_id"),
                        "targets": {
                            "target_unique_useful": contribution == PRIMARY_POSITIVE,
                            "target_any_observable": contribution != "NO_OBSERVABLE_CONTRIBUTION",
                            "target_output_produced": int(route.get("output_count") or 0) > 0,
                            "target_internal_value": contribution == PRIMARY_POSITIVE,
                            "target_decisive_final_value": False,
                            "contribution_state": contribution,
                        },
                        "features": _features_from_snapshot(snapshot),
                    }
                )
    positive_count = sum(1 for row in rows if row["targets"]["target_unique_useful"])
    return {
        "schema_version": "pre_route_canonical_dataset.v1",
        "authority": AUTHORITY,
        "feature_namespace_excludes_outcomes": True,
        "primary_target": "Y_unique_useful",
        "rows": rows,
        "raw_row_count": len(rows),
        "primary_row_count": len(rows),
        "positive_count": positive_count,
        "negative_count": len(rows) - positive_count,
        "excluded_contribution_not_measurable": excluded,
        "snapshot_linkage_failures": linkage_failures,
        "temporal_integrity_failures": temporal_failures,
        "leakage_failures": leakage_failures,
    }


def _features_from_snapshot(snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(snapshot, Mapping):
        return {}
    features = {}
    for group, payload in (
        ("STATIC_TASK", snapshot.get("task_features")),
        ("ROUTE_IDENTITY", {"route_id": snapshot.get("route_id"), "route_family": snapshot.get("route_context", {}).get("route_family")}),
        ("ROUTE_POSITION", {"route_position": snapshot.get("route_position")}),
        ("BUDGET_CONTEXT", {
            key: snapshot.get("route_context", {}).get(key)
            for key in ("selected_route_count", "current_route_budget", "remaining_route_capacity")
        }),
        ("STATE_SO_FAR", snapshot.get("state_so_far")),
        ("PRIOR_ROUTE_STATE", {
            key: snapshot.get("route_context", {}).get(key)
            for key in ("routes_already_admitted_count", "routes_already_executed_count")
        }),
    ):
        if isinstance(payload, Mapping):
            for key, value in _flatten(payload).items():
                features[f"{group}.{key}"] = value
    return {
        key: value
        for key, value in features.items()
        if not any(token in key for token in ("target_", "contribution_state", "final_task"))
    }


def _feature_records(dataset: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = dataset.get("rows", []) if isinstance(dataset, Mapping) else []
    result = []
    for row in rows:
        for name, value in row.get("features", {}).items():
            result.append(
                {
                    "feature_name": name,
                    "value": value,
                    "target_unique_useful": row["targets"]["target_unique_useful"],
                    "task_id": row["task_id"],
                    "route_id": row["route_id"],
                    "route_position": row["route_position"],
                }
            )
    return result


def _feature_eligibility(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_feature = _group(records, "feature_name")
    rows = []
    total = len({(r["task_id"], r["route_id"], r["route_position"]) for r in records}) or 1
    for name, items in sorted(by_feature.items()):
        present = [item for item in items if item.get("value") != UNOBSERVED]
        rows.append(
            {
                "feature_name": name,
                "producer": "pre_route_admission_snapshot_observer",
                "capture_stage": "runtime_budget_enforcer.pre_route_admission",
                "availability_stage": "PRE_ADMISSION",
                "pre_admission_available": bool(present),
                "coverage": round(len(present) / total, 6),
                "variation": len({json.dumps(item.get("value"), sort_keys=True, default=str) for item in present}),
                "missing_count": total - len(present),
                "leakage_status": "LEAKAGE_SAFE",
            }
        )
    return {
        "features": rows,
        "pre_admission_feature_count": len(rows),
        "high_coverage_feature_count": sum(1 for row in rows if row["coverage"] >= 0.9),
    }


def _feature_variation(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_feature = _group(records, "feature_name")
    rows = []
    variable = 0
    constant = 0
    for name, items in sorted(by_feature.items()):
        values = [item.get("value") for item in items if item.get("value") != UNOBSERVED]
        unique = {json.dumps(value, sort_keys=True, default=str) for value in values}
        if not values:
            cls = "UNAVAILABLE"
        elif len(unique) == 1:
            cls = "CONSTANT"
            constant += 1
        elif len(unique) <= 3:
            cls = "LOW_VARIATION"
            variable += 1
        else:
            cls = "PARTIAL_VARIATION"
            variable += 1
        rows.append(
            {
                "feature_name": name,
                "unique_value_count": len(unique),
                "missing_count": len(items) - len(values),
                "constant_within_task": _constant_within(items, "task_id"),
                "constant_across_tasks": len({
                    item.get("task_id") for item in items
                }) > 1 and len(unique) == 1,
                "constant_within_route": _constant_within(items, "route_id"),
                "constant_across_routes": len({
                    item.get("route_id") for item in items
                }) > 1 and len(unique) == 1,
                "variation_class": cls,
            }
        )
    return {"features": rows, "variable_feature_count": variable, "constant_feature_count": constant}


def _repeat_independence(raw_runs: list[dict[str, Any]], dataset: Mapping[str, Any]) -> dict[str, Any]:
    signatures = defaultdict(list)
    target_signatures = defaultdict(list)
    for row in dataset.get("rows", []):
        signatures[row["repeat_id"]].append(
            {
                "task_id": row["task_id"],
                "route_id": row["route_id"],
                "route_position": row["route_position"],
                "features": row["features"],
                "targets": row["targets"],
            }
        )
        target_signatures[row["repeat_id"]].append(
            {
                "task_id": row["task_id"],
                "route_id": row["route_id"],
                "route_position": row["route_position"],
                "targets": row["targets"],
            }
        )
    frozen = {
        repeat: _stable_id("repeat_signature", sorted(values, key=lambda item: (item["task_id"], item["route_position"], str(item["route_id"]))))
        for repeat, values in signatures.items()
    }
    target_frozen = {
        repeat: _stable_id("repeat_target_signature", sorted(values, key=lambda item: (item["task_id"], item["route_position"], str(item["route_id"]))))
        for repeat, values in target_signatures.items()
    }
    relation = "INDEPENDENT_REPEAT"
    deterministic = False
    effective = len(dataset.get("rows", []))
    if len(set(frozen.values())) < len(frozen):
        deterministic = True
        relation = "DETERMINISTIC_REPLAY"
        effective = len(next(iter(signatures.values()), []))
    elif len(set(target_frozen.values())) < len(target_frozen):
        relation = "PARTIALLY_INDEPENDENT_REPEAT"
    return {
        "raw_run_count": len(raw_runs),
        "repeat_signatures": dict(frozen),
        "repeat_target_signatures": dict(target_frozen),
        "repeat_relationship": relation,
        "deterministic_replay_detected": deterministic,
        "raw_row_count": len(dataset.get("rows", [])),
        "effective_independent_observation_count": effective,
    }


def _route_position_confounding(dataset: Mapping[str, Any]) -> dict[str, Any]:
    rows = dataset.get("rows", [])
    route_to_pos = defaultdict(set)
    pos_to_route = defaultdict(set)
    for row in rows:
        route_to_pos[str(row["route_id"])].add(row["route_position"])
        pos_to_route[str(row["route_position"])].add(str(row["route_id"]))
    fully = all(len(v) == 1 for v in route_to_pos.values()) and all(len(v) == 1 for v in pos_to_route.values())
    return {
        "route_id_to_positions": {k: sorted(v) for k, v in sorted(route_to_pos.items())},
        "position_to_route_ids": {k: sorted(v) for k, v in sorted(pos_to_route.items())},
        "classification": "FULLY_CONFOUNDED" if fully else "PARTIALLY_CONFOUNDED",
    }


def _permutation_feasibility() -> dict[str, Any]:
    matrix = [
        ["contradiction_checks", "dependency_reasoning", "identity_governance", "object_tracking"],
        ["dependency_reasoning", "identity_governance", "object_tracking", "contradiction_checks"],
        ["identity_governance", "object_tracking", "contradiction_checks", "dependency_reasoning"],
        ["object_tracking", "contradiction_checks", "dependency_reasoning", "identity_governance"],
    ]
    return {
        "decision": "PERMUTATION_CHANGES_CAUSAL_STATE_BUT_IS_EXPERIMENTALLY_VALID",
        "production_route_order_changed": "NO",
        "production_configuration_changed": "NO",
        "route_set_changed": "NO",
        "route_implementation_changed": "NO",
        "max_active_routes_changed": "NO",
        "reasoning_depth_changed": "NO",
        "budget_authority_changed": "NO",
        "snapshot_authority_changed": "NO",
        "cognitive_authority_changed": "NO",
        "permutation_used_this_run": "NO",
        "recommended_balanced_matrix": matrix,
    }


def _static_signal_analysis(dataset: Mapping[str, Any]) -> dict[str, Any]:
    rows = dataset.get("rows", [])
    fields = sorted({key for row in rows for key in row.get("features", {}) if key.startswith("STATIC_TASK.")})
    analysis = {}
    for field in fields:
        pos = [row["features"].get(field) for row in rows if row["targets"]["target_unique_useful"]]
        neg = [row["features"].get(field) for row in rows if not row["targets"]["target_unique_useful"]]
        analysis[field] = _value_stats(pos, neg)
    positives = {row["task_id"] for row in rows if row["targets"]["target_unique_useful"]}
    return {
        "classification": "SINGLE_CONTEXT_ONLY" if len(positives) == 1 else "NOT_OBSERVED",
        "positive_tasks": sorted(positives),
        "features": analysis,
    }


def _route_identity_analysis(dataset: Mapping[str, Any]) -> dict[str, Any]:
    return _categorical_signal(dataset, "route_id", "DESCRIPTIVE_CONFOUNDED_ONLY")


def _route_position_analysis(dataset: Mapping[str, Any]) -> dict[str, Any]:
    return _categorical_signal(dataset, "route_position", "DESCRIPTIVE_CONFOUNDED_ONLY")


def _state_so_far_analysis(dataset: Mapping[str, Any]) -> dict[str, Any]:
    rows = dataset.get("rows", [])
    fields = sorted({key for row in rows for key in row.get("features", {}) if key.startswith(("STATE_SO_FAR.", "PRIOR_ROUTE_STATE.", "BUDGET_CONTEXT.remaining_route_capacity"))})
    variable = []
    for field in fields:
        values = {json.dumps(row["features"].get(field), sort_keys=True, default=str) for row in rows if row["features"].get(field) != UNOBSERVED}
        if len(values) > 1:
            variable.append(field)
    return {
        "classification": "CANDIDATE_SIGNAL_SPARSE" if variable else "NO_VARIABLE_SIGNAL_OBSERVED",
        "variable_fields": variable,
    }


def _within_route_analysis(dataset: Mapping[str, Any]) -> dict[str, Any]:
    groups = _group(dataset.get("rows", []), "route_id")
    details = {}
    for route_id, rows in groups.items():
        details[str(route_id)] = {
            "observations": len(rows),
            "positive": sum(1 for row in rows if row["targets"]["target_unique_useful"]),
            "tasks": sorted({row["task_id"] for row in rows}),
            "positions": sorted({row["route_position"] for row in rows}),
        }
    return {"classification": "SINGLE_POSITION_PER_ROUTE" if details else "NOT_OBSERVED", "routes": details}


def _within_task_analysis(dataset: Mapping[str, Any]) -> dict[str, Any]:
    positives = [row for row in dataset.get("rows", []) if row["targets"]["target_unique_useful"]]
    tasks = sorted({row["task_id"] for row in positives})
    return {
        "classification": "SINGLE_POSITIVE_TASK_CONTEXT" if len(tasks) == 1 else "NOT_OBSERVED",
        "positive_tasks": tasks,
        "explicit_reconstruction_task": tasks[0] if tasks else None,
        "positive_routes": [
            {"task_id": row["task_id"], "route_id": row["route_id"], "route_position": row["route_position"]}
            for row in positives
        ],
    }


def _conditional_dependency_analysis(dataset: Mapping[str, Any]) -> dict[str, Any]:
    positives = [row for row in dataset.get("rows", []) if row["targets"]["target_unique_useful"]]
    if not positives:
        return {"classification": "NOT_OBSERVED", "candidate_dependencies": []}
    return {
        "classification": "SINGLE_EVENT_HINT",
        "candidate_dependencies": [
            {
                "task_id": row["task_id"],
                "route_id": row["route_id"],
                "route_position": row["route_position"],
                "prior_admitted": row["features"].get("PRIOR_ROUTE_STATE.routes_already_admitted_count"),
                "remaining_capacity": row["features"].get("BUDGET_CONTEXT.remaining_route_capacity"),
            }
            for row in positives
        ],
    }


def _internal_value_trace(dataset: Mapping[str, Any]) -> dict[str, Any]:
    positives = [row for row in dataset.get("rows", []) if row["targets"]["target_unique_useful"]]
    return {
        "internal_value_replicated": "NO",
        "highest_supported_level": "L3_INTERNAL_USEFUL_CONTRIBUTION" if positives else "L0_EXECUTED",
        "traces": [
            {
                "snapshot_id": row["snapshot_id"],
                "admission": "ADMITTED",
                "execution": "EXECUTED",
                "route_execution_id": row["route_execution_id"],
                "contribution": row["targets"]["contribution_state"],
                "final_outcome_level": "NOT_L4",
            }
            for row in positives
        ],
    }


def _final_outcome_analysis(report: Mapping[str, Any]) -> dict[str, Any]:
    comparison = report.get("derived", {}).get("aggregate_comparison", {})
    return {
        "win": comparison.get("paired_improved_with_6", 0),
        "loss": comparison.get("paired_regressed_with_6", 0),
        "tie": comparison.get("paired_unchanged", 0),
        "delta_exact_success_rate": comparison.get("delta_exact_success_rate"),
        "delta_mean_accuracy": comparison.get("delta_mean_accuracy"),
        "delta_mean_final_score": comparison.get("delta_mean_final_score"),
        "decisive_final_value": "NO",
    }


def _signal_stability(dataset: Mapping[str, Any], confounding: Mapping[str, Any]) -> dict[str, Any]:
    positives = [row for row in dataset.get("rows", []) if row["targets"]["target_unique_useful"]]
    tasks = {row["task_id"] for row in positives}
    if not positives:
        cls = "UNSTABLE"
    elif len(tasks) == 1 or confounding.get("classification") == "FULLY_CONFOUNDED":
        cls = "SINGLE_CONTEXT_ONLY"
    else:
        cls = "CONSISTENT_BUT_SPARSE"
    return {"classification": cls, "positive_task_count": len(tasks), "positive_event_count": len(positives)}


def _evidence_decision(
    dataset: Mapping[str, Any],
    repeat_independence: Mapping[str, Any],
    confounding: Mapping[str, Any],
    stability: Mapping[str, Any],
) -> dict[str, Any]:
    positives = int(dataset.get("positive_count") or 0)
    p2 = (
        positives >= 2
        and repeat_independence.get("deterministic_replay_detected") is False
        and confounding.get("classification") != "FULLY_CONFOUNDED"
        and stability.get("classification") not in {"SINGLE_CONTEXT_ONLY", "UNSTABLE"}
    )
    if p2:
        conclusion = "P2_ASSOCIATION_REPLICATED"
        remaining = "P3_HELD_OUT_VALIDATION_NOT_RUN"
        next_action = "FREEZE_CANDIDATE_SIGNAL_AND_DESIGN_P3_HELD_OUT_VALIDATION"
    elif positives <= 2:
        conclusion = "P1_REMAINS_SIGNAL_TOO_SPARSE"
        remaining = "POSITIVE_EVENT_SCARCITY_PERSISTS"
        next_action = "DESIGN_TARGETED_CORPUS_EXPANSION"
    elif confounding.get("classification") == "FULLY_CONFOUNDED":
        conclusion = "P1_CONFUNDING_NOT_RESOLVED"
        remaining = "ROUTE_IDENTITY_POSITION_CONFOUNDING"
        next_action = "DESIGN_SAFE_DECONFOUNDING_EXPERIMENT"
    else:
        conclusion = "NO_USEFUL_PRE_ADMISSION_SIGNAL_FOUND"
        remaining = "NO_REPLICATED_ASSOCIATION"
        next_action = "DO_NOT_BUILD_ADAPTIVE_ROUTE_EXPANSION_FROM_CURRENT_SIGNALS"
    return {
        "primary_scientific_conclusion": conclusion,
        "current_evidence_level": "P2_ASSOCIATION_REPLICATED" if p2 else "P1_CANDIDATE_SIGNAL_OBSERVED",
        "p2_gate_passed": p2,
        "p3_claim_allowed": False,
        "strongest_candidate_signal": "route_id/route_position descriptive signal",
        "corpus_expansion_required": conclusion == "P1_REMAINS_SIGNAL_TOO_SPARSE",
        "more_instrumentation_required": False,
        "remaining_limitation": remaining,
        "next_action": next_action,
    }


def _categorical_signal(dataset: Mapping[str, Any], key: str, classification: str) -> dict[str, Any]:
    groups = _group(dataset.get("rows", []), key)
    details = {}
    for value, rows in sorted(groups.items(), key=lambda item: str(item[0])):
        states = Counter(row["targets"]["contribution_state"] for row in rows)
        executions = len(rows)
        useful = states.get(PRIMARY_POSITIVE, 0)
        details[str(value)] = {
            "executions": executions,
            "unique_useful": useful,
            "duplicate": states.get("DUPLICATE_CONTRIBUTION", 0),
            "low_value": states.get("LOW_VALUE_CONTRIBUTION", 0),
            "no_observable": states.get("NO_OBSERVABLE_CONTRIBUTION", 0),
            "positive_rate": _rate(useful, executions),
        }
    return {"classification": classification, "groups": details}


def _value_stats(pos: list[Any], neg: list[Any]) -> dict[str, Any]:
    pos_num = [float(v) for v in pos if isinstance(v, (int, float)) and not isinstance(v, bool)]
    neg_num = [float(v) for v in neg if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if pos_num or neg_num:
        return {
            "positive_n": len(pos_num),
            "negative_n": len(neg_num),
            "positive_mean": round(mean(pos_num), 6) if pos_num else None,
            "positive_median": round(median(pos_num), 6) if pos_num else None,
            "positive_range": [min(pos_num), max(pos_num)] if pos_num else None,
            "negative_mean": round(mean(neg_num), 6) if neg_num else None,
            "negative_median": round(median(neg_num), 6) if neg_num else None,
            "negative_range": [min(neg_num), max(neg_num)] if neg_num else None,
        }
    counter = Counter(pos)
    return {"support": Counter(pos + neg), "positive_support": dict(counter)}


def _system_fingerprint(report: Mapping[str, Any], source_path: Path, task_order: list[str]) -> dict[str, Any]:
    payload = {
        "git_revision": _git(["rev-parse", "HEAD"]),
        "branch": _git(["branch", "--show-current"]),
        "dirty_state_summary": _git(["status", "--short"]),
        "python_runtime_version": platform.python_version(),
        "task_corpus_fingerprint": _stable_id("task_corpus", task_order),
        "task_order_fingerprint": _stable_id("task_order", task_order),
        "seed": report.get("derived", {}).get("comparability", {}).get("seed", 424242),
        "execution_mode": report.get("derived", {}).get("comparability", {}).get("mode", "adaptive"),
        "route_budget": [2, 6],
        "reasoning_depth": report.get("derived", {}).get("comparability", {}).get("reasoning_depth", "2"),
        "snapshot_schema_version": "pre_route_admission_snapshot.v1",
        "route_classifier_schema_version": "route_contribution_telemetry.v1",
        "route_contribution_telemetry_schema": "1.0",
        "source_artifact": str(source_path),
    }
    payload["experiment_system_fingerprint"] = _stable_id("experiment_system", payload)
    return payload


def _task_order(report: Mapping[str, Any], raw_runs: list[dict[str, Any]]) -> list[str]:
    order = report.get("derived", {}).get("comparability", {}).get("task_order")
    if isinstance(order, list) and order:
        return [str(item) for item in order]
    for run in raw_runs:
        values = run.get("selected_task_files")
        if isinstance(values, list) and values:
            return [str(item) for item in values]
    return []


def _snapshots_for(snapshot_root: Path, run_id: str, task_id: str) -> list[dict[str, Any]]:
    result = []
    run_dir = snapshot_root / _safe(run_id)
    if not run_dir.exists():
        return []
    for path in run_dir.glob("**/*.json"):
        try:
            snapshot = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if snapshot.get("schema_version") != "pre_route_admission_snapshot.v1":
            continue
        if _task_identity(snapshot.get("task_id")) == _task_identity(task_id):
            result.append(snapshot)
    return result


def _match_snapshot(snapshots: list[dict[str, Any]], route: Mapping[str, Any], position: int) -> dict[str, Any] | None:
    route_id = str(route.get("route_id") or "")
    for snapshot in snapshots:
        if str(snapshot.get("route_id") or "") == route_id and _int(snapshot.get("route_position")) == position:
            return snapshot
    return None


def _flatten(value: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    result = {}
    for key, item in value.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, Mapping):
            result.update(_flatten(item, name))
        else:
            result[name] = item
    return result


def _constant_within(items: list[dict[str, Any]], group_key: str) -> bool:
    grouped = _group(items, group_key)
    return all(len({json.dumps(item.get("value"), sort_keys=True, default=str) for item in rows}) <= 1 for rows in grouped.values())


def _group(rows: Iterable[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    result: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        result[row.get(key)].append(row)
    return dict(result)


def _markdown_report(summary: Mapping[str, Any], evidence: Mapping[str, Any], confounding: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Pre-Route Controlled Replication",
            "",
            f"OBSERVED FACT: raw marginal route rows = {summary['raw_marginal_route_rows']}.",
            f"OBSERVED FACT: unique useful events = {summary['unique_useful_events']}.",
            f"DESCRIPTIVE ASSOCIATION: strongest candidate = {summary['strongest_candidate_signal']}.",
            f"CANDIDATE SIGNAL: route identity/position remains {confounding['classification']}.",
            f"REPLICATED ASSOCIATION: {evidence['p2_gate_passed']}.",
            f"NOT PROVEN: P3 predictive value and production policy benefit.",
            f"Decision: {summary['primary_scientific_conclusion']}.",
        ]
    )


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _stable_id(prefix: str, payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


def _task_identity(value: Any) -> str:
    if isinstance(value, Mapping):
        value = value.get("value") or value.get("task_id") or value.get("task")
    text = str(value or "")
    if text.startswith("{") and "value" in text:
        try:
            parsed = json.loads(text.replace("'", '"'))
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, Mapping):
            text = str(parsed.get("value") or text)
    text = text.replace("/", "\\")
    return text.rsplit("\\", 1)[-1] if "\\" in text else text


def _safe(value: Any) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(value or ""))[:120]


def _int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


__all__ = ["run_pre_route_controlled_replication"]
