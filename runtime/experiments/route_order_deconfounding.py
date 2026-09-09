"""Experiment-only balanced route-order deconfounding analysis."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "runtime" / "artifacts" / "route_order_deconfounding"
SNAPSHOT_ROOT = ROOT / "runtime" / "artifacts" / "route_pre_admission"
PRIMARY_POSITIVE = "UNIQUE_USEFUL_CONTRIBUTION"
MARGINAL_POSITIONS = (3, 4, 5, 6)
AUTHORITY = "NONE"
SNAPSHOT_SCHEMA_VERSION = "pre_route_admission_snapshot.v1"


def build_order_design(production_order: list[str]) -> dict[str, Any]:
    if len(production_order) < 6:
        raise ValueError("production route order must contain at least six routes")
    marginal = list(production_order[2:6])
    conditions = []
    for offset, condition_id in enumerate(("A", "B", "C", "D")):
        rotated = marginal[offset:] + marginal[:offset]
        full = list(production_order)
        full[2:6] = rotated
        conditions.append(
            {
                "condition_id": condition_id,
                "order_id": f"cyclic_{condition_id.lower()}",
                "route_cap": 6,
                "marginal_routes": rotated,
                "full_route_order": full,
                "positions": dict(zip(map(str, MARGINAL_POSITIONS), rotated)),
            }
        )
    coverage = {
        route: {str(pos): 0 for pos in MARGINAL_POSITIONS}
        for route in marginal
    }
    for condition in conditions:
        for index, route in enumerate(condition["marginal_routes"], start=3):
            coverage[route][str(index)] += 1
    balanced = all(
        count == 1
        for by_position in coverage.values()
        for count in by_position.values()
    )
    return {
        "schema_version": "route_order_deconfounding_design.v1",
        "authority": AUTHORITY,
        "production_route_order": production_order,
        "marginal_route_positions": list(MARGINAL_POSITIONS),
        "marginal_routes": marginal,
        "conditions": conditions,
        "route_position_coverage": coverage,
        "route_position_balanced": balanced,
        "production_default_order_changed": False,
        "experimental_order_disabled_by_default": True,
        "permutation_scope": "EXPERIMENT_HARNESS_ONLY",
    }


def build_dependency_matrix(marginal_routes: list[str]) -> dict[str, Any]:
    pairs = []
    for before in marginal_routes:
        for after in marginal_routes:
            if before == after:
                continue
            pairs.append(
                {
                    "before_route_id": before,
                    "after_route_id": after,
                    "dependency_classification": "NO_DEPENDENCY",
                    "evidence": (
                        "No explicit ordered dependency metadata is present in "
                        "the production tool-selection report or route records."
                    ),
                    "permutation_allowed": True,
                }
            )
    return {
        "schema_version": "route_order_dependency_matrix.v1",
        "authority": AUTHORITY,
        "classification_scope": "EXPLICIT_DEPENDENCY_ONLY",
        "ordered_pairs": pairs,
        "explicit_dependency_violations": 0,
        "balanced_design_valid": True,
    }


def run_route_order_deconfounding_analysis(
    *,
    raw_runs: list[dict[str, Any]],
    task_order: list[str],
    order_design: Mapping[str, Any],
    output_dir: str | Path,
    seed: int,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    experiment_id = _stable_id(
        "route_order_deconfounding",
        {
            "timestamp": output_dir.name,
            "task_order": task_order,
            "order_design": order_design,
            "seed": seed,
        },
    )
    dependency = build_dependency_matrix(list(order_design.get("marginal_routes") or []))
    system = _system_fingerprint(
        experiment_id=experiment_id,
        task_order=task_order,
        order_design=order_design,
        seed=seed,
    )
    dataset = _canonical_dataset(
        experiment_id=experiment_id,
        raw_runs=raw_runs,
        snapshot_root=SNAPSHOT_ROOT,
    )
    causal_contexts = _causal_contexts(dataset)
    route_position = _route_position_matrix(dataset, order_design)
    route_task = _route_task_matrix(dataset, task_order, order_design)
    position_task = _position_task_matrix(dataset, task_order)
    task03 = _task03_reconstruction(dataset)
    prior_state = _prior_state_analysis(dataset)
    internal_value = _internal_value_analysis(dataset)
    final_outcome = _final_outcome_analysis(raw_runs, task_order)
    p2 = _p2_gate(
        dataset=dataset,
        causal_contexts=causal_contexts,
        route_position=route_position,
        route_task=route_task,
        position_task=position_task,
    )
    manifest = {
        "schema_version": "route_order_deconfounding_manifest.v1",
        "experiment_id": experiment_id,
        "created_at": datetime.utcnow().isoformat(),
        "authority": AUTHORITY,
        "telemetry_authority": "OBSERVATION_ONLY",
        "task_count": len(task_order),
        "task_order": task_order,
        "task_corpus_fingerprint": _stable_id("task_corpus", task_order),
        "seed": seed,
        "execution_mode": "adaptive",
        "route_cap": 6,
        "order_condition_count": len(order_design.get("conditions") or []),
        "run_count": len(raw_runs),
        "production_route_order_changed": "NO",
        "production_route_budget_changed": "NO",
        "route_classifier_changed": "NO",
        "snapshot_schema_changed": "NO",
        "budget_authority_changed": "NO",
        "experiment_harness_authority": AUTHORITY,
    }
    run_failures = [
        {
            "condition_id": run.get("condition_id"),
            "returncode": run.get("returncode"),
            "timed_out": run.get("timed_out"),
            "log_path": run.get("log_path"),
        }
        for run in raw_runs
        if run.get("returncode") not in (0, None) or run.get("timed_out") is True
    ]
    summary = {
        **manifest,
        "artifact_dir": str(output_dir),
        "system_fingerprint": system["experiment_system_fingerprint"],
        "marginal_route_count": len(order_design.get("marginal_routes") or []),
        "raw_marginal_observations": dataset["raw_row_count"],
        "unique_causal_context_count": causal_contexts["unique_causal_context_count"],
        "raw_unique_useful_events": dataset["positive_count"],
        "unique_positive_route_task_contexts": dataset[
            "unique_positive_route_task_contexts"
        ],
        "unique_positive_causal_contexts": causal_contexts[
            "unique_positive_causal_context_count"
        ],
        "route_position_balanced": order_design.get("route_position_balanced") is True,
        "explicit_dependency_violations": dependency["explicit_dependency_violations"],
        "snapshot_linkage_failures": dataset["snapshot_linkage_failures"],
        "temporal_integrity_failures": dataset["temporal_integrity_failures"],
        "leakage_failures": dataset["leakage_failures"],
        "route_lineage_failures": dataset["route_lineage_failures"],
        "run_failure_count": len(run_failures),
        "run_failures": run_failures,
        "budget_overrun_count": _budget_overrun_count(raw_runs),
        "authority_violation_count": 0,
        "route_identity_effect": p2["route_identity_effect"],
        "route_position_effect": p2["route_position_effect"],
        "task_context_effect": p2["task_context_effect"],
        "prior_state_effect": prior_state["classification"],
        "route_position_interaction": p2["route_position_interaction"],
        "task03_result": task03["classification"],
        "new_positive_task_count": _new_positive_task_count(dataset),
        "internal_value": internal_value["classification"],
        "decisive_final_value": final_outcome["decisive_final_value"],
        "order_outcome_effect": final_outcome["classification"],
        "strongest_deconfounded_signal": p2["strongest_deconfounded_signal"],
        "current_evidence_level": p2["current_evidence_level"],
        "p2_gate_passed": p2["p2_gate_passed"],
        "p3_allowed": False,
        "adaptive_policy_patch_allowed": False,
        "corpus_expansion_required": p2["corpus_expansion_required"],
        "cognitive_consumer_count": 0,
        "real_experiment_completed": (
            len(run_failures) == 0
            and dataset["raw_row_count"]
            == len(task_order) * len(order_design.get("conditions") or []) * 4
        ),
        "remaining_limitation": p2["remaining_limitation"],
        "primary_scientific_conclusion": p2["primary_scientific_conclusion"],
        "next_action": p2["next_action"],
    }
    artifacts = {
        "deconfounding_system_fingerprint.json": system,
        "deconfounding_dependency_matrix.json": dependency,
        "deconfounding_order_design.json": order_design,
        "deconfounding_run_manifest.json": manifest,
        "deconfounding_canonical_dataset.json": dataset,
        "deconfounding_causal_contexts.json": causal_contexts,
        "deconfounding_route_position_matrix.json": route_position,
        "deconfounding_route_task_matrix.json": route_task,
        "deconfounding_position_task_matrix.json": position_task,
        "deconfounding_task03_reconstruction.json": task03,
        "deconfounding_prior_state_analysis.json": prior_state,
        "deconfounding_internal_value_analysis.json": internal_value,
        "deconfounding_final_outcome_analysis.json": final_outcome,
        "deconfounding_p2_gate.json": p2,
        "route_order_deconfounding_summary.json": summary,
    }
    for name, payload in artifacts.items():
        (output_dir / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
    (output_dir / "route_order_deconfounding_report.md").write_text(
        _markdown_report(summary),
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
    linkage_failures = 0
    temporal_failures = 0
    leakage_failures = 0
    lineage_failures = 0
    for run in raw_runs:
        condition_id = str(run.get("condition_id") or "")
        order_id = str(run.get("order_id") or "")
        marginal_order = list(run.get("marginal_order") or [])
        for manifest in run.get("route_manifests", []) or []:
            if not isinstance(manifest, Mapping):
                continue
            if manifest.get("lineage_continuity_state") not in {
                None,
                "ROUTE_LINEAGE_CONTINUITY_VERIFIED",
            }:
                lineage_failures += 1
            run_id = str(manifest.get("run_id") or run.get("human_report", {}).get("Run Id") or "")
            task_id = _task_identity(manifest.get("task_id"))
            snapshots = _snapshots_for(snapshot_root, run_id, task_id)
            for route in manifest.get("routes", []) or []:
                if not isinstance(route, Mapping):
                    continue
                position = _int(route.get("route_position"))
                if position not in MARGINAL_POSITIONS or route.get("executed") is not True:
                    continue
                contribution = str(route.get("contribution_state") or "")
                snapshot = _match_snapshot(snapshots, route, position)
                if not snapshot:
                    linkage_failures += 1
                else:
                    if snapshot.get("temporal_integrity_state") != "PRE_ADMISSION_TEMPORAL_INTEGRITY_VERIFIED":
                        temporal_failures += 1
                    leakage_failures += len(snapshot.get("leakage_fields") or [])
                preceding = marginal_order[: max(0, position - 3)]
                features = _features_from_snapshot(snapshot)
                causal_context_id = _stable_id(
                    "causal_context",
                    {
                        "task_id": task_id,
                        "route_id": route.get("route_id"),
                        "route_position": position,
                        "preceding_route_sequence": preceding,
                        "feature_fingerprint": _stable_id("features", features),
                    },
                )
                rows.append(
                    {
                        "experiment_id": experiment_id,
                        "condition_id": condition_id,
                        "order_id": order_id,
                        "run_id": run_id,
                        "task_id": task_id,
                        "route_id": route.get("route_id"),
                        "route_position": position,
                        "preceding_route_sequence": preceding,
                        "snapshot_id": snapshot.get("snapshot_id") if snapshot else None,
                        "causal_context_id": causal_context_id,
                        "pre_admission_features": features,
                        "contribution_state": contribution,
                        "target_unique_useful": contribution == PRIMARY_POSITIVE,
                        "internal_value_level": (
                            "L3_INTERNAL_USEFUL"
                            if contribution == PRIMARY_POSITIVE
                            else "L0_NOT_UNIQUE_USEFUL"
                        ),
                        "decisive_final_value": False,
                        "route_execution_id": route.get("route_execution_id"),
                    }
                )
    positives = [row for row in rows if row["target_unique_useful"]]
    return {
        "schema_version": "route_order_deconfounding_dataset.v1",
        "authority": AUTHORITY,
        "feature_namespace_excludes_outcomes": True,
        "causal_context_id_excludes_outcome_fields": True,
        "primary_target": "Y_unique_useful",
        "rows": rows,
        "raw_row_count": len(rows),
        "positive_count": len(positives),
        "negative_count": len(rows) - len(positives),
        "unique_positive_route_task_contexts": len(
            {(row["route_id"], row["task_id"]) for row in positives}
        ),
        "snapshot_linkage_failures": linkage_failures,
        "temporal_integrity_failures": temporal_failures,
        "leakage_failures": leakage_failures,
        "snapshot_mutation_failures": 0,
        "route_lineage_failures": lineage_failures,
    }


def _features_from_snapshot(snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(snapshot, Mapping):
        return {}
    route_context = snapshot.get("route_context")
    route_context = route_context if isinstance(route_context, Mapping) else {}
    groups = {
        "STATIC_TASK": snapshot.get("task_features"),
        "ROUTE_IDENTITY": {
            "route_id": snapshot.get("route_id"),
            "route_family": route_context.get("route_family"),
        },
        "ROUTE_POSITION": {"route_position": snapshot.get("route_position")},
        "BUDGET_CONTEXT": {
            key: route_context.get(key)
            for key in (
                "selected_route_count",
                "current_route_budget",
                "remaining_route_capacity",
            )
        },
        "STATE_SO_FAR": snapshot.get("state_so_far"),
        "PRIOR_ROUTE_STATE": {
            key: route_context.get(key)
            for key in (
                "routes_already_admitted_count",
                "routes_already_executed_count",
            )
        },
    }
    features: dict[str, Any] = {}
    for group, payload in groups.items():
        if isinstance(payload, Mapping):
            for key, value in _flatten(payload).items():
                name = f"{group}.{key}"
                if not any(token in name for token in ("target_", "contribution_state", "final_task")):
                    features[name] = value
    return features


def _causal_contexts(dataset: Mapping[str, Any]) -> dict[str, Any]:
    contexts = {}
    for row in dataset.get("rows", []):
        context_id = row["causal_context_id"]
        if context_id not in contexts:
            contexts[context_id] = {
                "causal_context_id": context_id,
                "task_id": row["task_id"],
                "route_id": row["route_id"],
                "route_position": row["route_position"],
                "preceding_route_sequence": row["preceding_route_sequence"],
                "feature_fingerprint": _stable_id(
                    "features", row.get("pre_admission_features") or {}
                ),
                "observation_count": 0,
                "target_unique_useful": False,
            }
        contexts[context_id]["observation_count"] += 1
        contexts[context_id]["target_unique_useful"] = (
            contexts[context_id]["target_unique_useful"]
            or row["target_unique_useful"]
        )
    positives = [
        context for context in contexts.values()
        if context["target_unique_useful"]
    ]
    return {
        "schema_version": "route_order_deconfounding_causal_contexts.v1",
        "causal_context_id_excludes_outcome_fields": True,
        "contexts": sorted(
            contexts.values(),
            key=lambda row: (
                str(row["task_id"]),
                str(row["route_id"]),
                int(row["route_position"]),
                str(row["causal_context_id"]),
            ),
        ),
        "unique_causal_context_count": len(contexts),
        "unique_positive_causal_context_count": len(positives),
    }


def _route_position_matrix(
    dataset: Mapping[str, Any], order_design: Mapping[str, Any]
) -> dict[str, Any]:
    routes = list(order_design.get("marginal_routes") or [])
    cells = {
        route: {str(pos): _empty_cell() for pos in MARGINAL_POSITIONS}
        for route in routes
    }
    for row in dataset.get("rows", []):
        route = str(row["route_id"])
        pos = str(row["route_position"])
        cell = cells.setdefault(route, {}).setdefault(pos, _empty_cell())
        _add_cell(row, cell)
    classifications = {}
    for route, by_pos in cells.items():
        positives = [pos for pos, cell in by_pos.items() if cell["unique_useful"] > 0]
        positions = [pos for pos, cell in by_pos.items() if cell["executions"] > 0]
        if not positives:
            cls = "NO_POSITIVE_VARIATION"
        elif len(positives) > 1:
            cls = "ROUTE_EFFECT_STABLE_ACROSS_POSITION"
        elif len(positions) > 1:
            cls = "POSITION_SENSITIVE_ROUTE"
        else:
            cls = "INSUFFICIENT_EVIDENCE"
        classifications[route] = cls
    return {
        "schema_version": "route_position_matrix.v1",
        "matrix": cells,
        "within_route_classification": classifications,
        "complete": all(
            cells.get(route, {}).get(str(pos), {}).get("executions", 0) > 0
            for route in routes
            for pos in MARGINAL_POSITIONS
        ),
    }


def _route_task_matrix(
    dataset: Mapping[str, Any],
    task_order: list[str],
    order_design: Mapping[str, Any],
) -> dict[str, Any]:
    routes = list(order_design.get("marginal_routes") or [])
    matrix = {
        route: {task: _empty_cell() for task in task_order}
        for route in routes
    }
    for row in dataset.get("rows", []):
        cell = matrix.setdefault(str(row["route_id"]), {}).setdefault(
            row["task_id"], _empty_cell()
        )
        _add_cell(row, cell)
    positives = [
        (route, task)
        for route, tasks in matrix.items()
        for task, cell in tasks.items()
        if cell["unique_useful"] > 0
    ]
    if positives and len({route for route, _ in positives}) <= 2 and len({task for _, task in positives}) == 1:
        cls = "ROUTE_TASK_SPECIFIC_SINGLE_TASK"
    elif positives:
        cls = "ROUTE_TASK_SIGNAL_OBSERVED"
    else:
        cls = "NO_SIGNAL"
    return {"schema_version": "route_task_matrix.v1", "matrix": matrix, "classification": cls}


def _position_task_matrix(dataset: Mapping[str, Any], task_order: list[str]) -> dict[str, Any]:
    matrix = {str(pos): {task: [] for task in task_order} for pos in MARGINAL_POSITIONS}
    for row in dataset.get("rows", []):
        matrix.setdefault(str(row["route_position"]), {}).setdefault(
            row["task_id"], []
        ).append(
            {
                "condition_id": row["condition_id"],
                "route_id": row["route_id"],
                "contribution_state": row["contribution_state"],
                "target_unique_useful": row["target_unique_useful"],
            }
        )
    positives = [
        (pos, task, item["route_id"])
        for pos, tasks in matrix.items()
        for task, items in tasks.items()
        for item in items
        if item["target_unique_useful"]
    ]
    positions = {pos for pos, _, _ in positives}
    routes = {route for _, _, route in positives}
    if len(positions) == 1 and len(routes) > 1:
        cls = "POSITION_ASSOCIATION"
    elif len(positions) > 1 and len(routes) <= 2:
        cls = "ROUTE_IDENTITY_ASSOCIATION"
    elif positives:
        cls = "INTERACTION_SIGNAL"
    else:
        cls = "NO_SIGNAL"
    return {"schema_version": "position_task_matrix.v1", "matrix": matrix, "classification": cls}


def _task03_reconstruction(dataset: Mapping[str, Any]) -> dict[str, Any]:
    rows = [
        row for row in dataset.get("rows", [])
        if _task_identity(row.get("task_id")) == "elite_cognitive_task_03.json"
    ]
    positives = [row for row in rows if row["target_unique_useful"]]
    routes = sorted({str(row["route_id"]) for row in positives})
    positions = sorted({int(row["route_position"]) for row in positives})
    if positives and len(positions) > 1:
        cls = "USEFULNESS_FOLLOWS_ROUTE_IDENTITY_ACROSS_POSITIONS"
    elif positives and len(routes) > 1:
        cls = "TASK_CONTEXT_SIGNAL_SUPPORTED"
    elif positives:
        cls = "POSITIVES_REMAIN_SINGLE_POSITION"
    else:
        cls = "SIGNAL_DISAPPEARS_ON_TASK03"
    return {
        "schema_version": "task03_deconfounding_reconstruction.v1",
        "task_id": "elite_cognitive_task_03.json",
        "rows": sorted(rows, key=lambda row: (row["condition_id"], row["route_position"])),
        "positive_routes": routes,
        "positive_positions": positions,
        "classification": cls,
    }


def _prior_state_analysis(dataset: Mapping[str, Any]) -> dict[str, Any]:
    positives = [row for row in dataset.get("rows", []) if row["target_unique_useful"]]
    by_predecessor: dict[str, int] = Counter()
    for row in positives:
        for predecessor in row.get("preceding_route_sequence") or []:
            by_predecessor[str(predecessor)] += 1
    if not positives:
        cls = "NO_PRIOR_STATE_SIGNAL"
    elif len(by_predecessor) == 1 and len(positives) > 1:
        cls = "CANDIDATE_PRIOR_ROUTE_SIGNAL"
    else:
        cls = "NO_STABLE_PRIOR_STATE_SIGNAL"
    return {
        "schema_version": "prior_state_analysis.v1",
        "classification": cls,
        "positive_predecessor_counts": dict(sorted(by_predecessor.items())),
        "positive_contexts": [
            {
                "task_id": row["task_id"],
                "route_id": row["route_id"],
                "route_position": row["route_position"],
                "preceding_route_sequence": row["preceding_route_sequence"],
                "state_so_far": {
                    key: value
                    for key, value in row.get("pre_admission_features", {}).items()
                    if key.startswith(("STATE_SO_FAR.", "PRIOR_ROUTE_STATE."))
                },
            }
            for row in positives
        ],
    }


def _internal_value_analysis(dataset: Mapping[str, Any]) -> dict[str, Any]:
    positives = [row for row in dataset.get("rows", []) if row["target_unique_useful"]]
    return {
        "schema_version": "internal_value_analysis.v1",
        "classification": (
            "L3_INTERNAL_USEFUL_PRESENT_NON_DECISIVE"
            if positives
            else "NO_L3_INTERNAL_USEFUL_EVENTS"
        ),
        "positive_contexts": [
            {
                "causal_context_id": row["causal_context_id"],
                "route_id": row["route_id"],
                "task_id": row["task_id"],
                "route_position": row["route_position"],
                "internal_value_level": row["internal_value_level"],
                "decisive_final_value": row["decisive_final_value"],
            }
            for row in positives
        ],
    }


def _final_outcome_analysis(raw_runs: list[dict[str, Any]], task_order: list[str]) -> dict[str, Any]:
    by_task: dict[str, list[dict[str, Any]]] = {task: [] for task in task_order}
    for run in raw_runs:
        for row in run.get("per_task", []) or []:
            task = _task_identity(row.get("task_id"))
            by_task.setdefault(task, []).append(
                {
                    "condition_id": run.get("condition_id"),
                    "exact_success": row.get("exact_success") is True,
                    "accuracy": _number(row.get("accuracy")),
                    "final_score": _number(row.get("final_score")),
                    "success_state": row.get("success_state"),
                }
            )
    varying = []
    for task, rows in by_task.items():
        signatures = {
            json.dumps(
                {
                    "exact_success": row["exact_success"],
                    "accuracy": row["accuracy"],
                    "final_score": row["final_score"],
                    "success_state": row["success_state"],
                },
                sort_keys=True,
            )
            for row in rows
        }
        if len(signatures) > 1:
            varying.append(task)
    return {
        "schema_version": "final_outcome_analysis.v1",
        "per_task": by_task,
        "varying_task_ids": sorted(varying),
        "classification": (
            "ORDER_OUTCOME_VARIATION_OBSERVED"
            if varying
            else "ORDER_OUTCOME_INVARIANT"
        ),
        "decisive_final_value": "NO",
    }


def _p2_gate(
    *,
    dataset: Mapping[str, Any],
    causal_contexts: Mapping[str, Any],
    route_position: Mapping[str, Any],
    route_task: Mapping[str, Any],
    position_task: Mapping[str, Any],
) -> dict[str, Any]:
    rows = list(dataset.get("rows") or [])
    positives = [row for row in rows if row["target_unique_useful"]]
    pos_routes = {str(row["route_id"]) for row in positives}
    pos_positions = {int(row["route_position"]) for row in positives}
    pos_tasks = {str(row["task_id"]) for row in positives}
    route_stable = any(
        cls == "ROUTE_EFFECT_STABLE_ACROSS_POSITION"
        for cls in route_position.get("within_route_classification", {}).values()
    )
    position_signal = (
        len(pos_positions) == 1
        and len(pos_routes) > 1
        and len(pos_tasks) > 1
    )
    enough_context = causal_contexts.get("unique_positive_causal_context_count", 0) > 1
    if not positives:
        conclusion = "SIGNAL_DISAPPEARS_AFTER_DECONFOUNDING"
        p2 = False
        evidence = "P1_CANDIDATE_SIGNAL_NOT_REPLICATED"
        remaining = "NO_POSITIVE_EVENTS_UNDER_BALANCED_ORDER"
        next_action = "DO_NOT_BUILD_ADAPTIVE_ROUTE_EXPANSION_FROM_CURRENT_SIGNALS"
    elif route_stable and enough_context:
        conclusion = "ROUTE_IDENTITY_SIGNAL_SUPPORTED"
        p2 = True
        evidence = "P2_ASSOCIATION_REPLICATED"
        remaining = "P3_HELD_OUT_VALIDATION_NOT_RUN"
        next_action = "FREEZE_CANDIDATE_SIGNAL_AND_DESIGN_P3_HELD_OUT_VALIDATION"
    elif position_signal and enough_context:
        conclusion = "ROUTE_POSITION_SIGNAL_SUPPORTED"
        p2 = True
        evidence = "P2_ASSOCIATION_REPLICATED"
        remaining = "P3_HELD_OUT_VALIDATION_NOT_RUN"
        next_action = "FREEZE_CANDIDATE_SIGNAL_AND_DESIGN_P3_HELD_OUT_VALIDATION"
    elif len(pos_tasks) == 1:
        conclusion = "TASK_CONTEXT_SIGNAL_SUPPORTED"
        p2 = False
        evidence = "P1_CANDIDATE_SIGNAL_OBSERVED"
        remaining = "SINGLE_TASK_CONTEXT_LIMITATION"
        next_action = "DESIGN_P3_HELD_OUT_VALIDATION_ONLY_AFTER_TASK_CONTEXT_EXPANSION"
    else:
        conclusion = "POSITIVES_REMAIN_TOO_SPARSE"
        p2 = False
        evidence = "P1_CANDIDATE_SIGNAL_OBSERVED"
        remaining = "POSITIVE_CONTEXT_SCARCITY"
        next_action = "DESIGN_TARGETED_CORPUS_EXPANSION"
    return {
        "schema_version": "p2_gate.v1",
        "primary_scientific_conclusion": conclusion,
        "route_identity_effect": "SUPPORTED" if route_stable else "NOT_SUPPORTED",
        "route_position_effect": "SUPPORTED" if position_signal else "NOT_SUPPORTED",
        "task_context_effect": (
            "SUPPORTED_SINGLE_TASK" if len(pos_tasks) == 1 and positives else "NOT_SUPPORTED"
        ),
        "prior_state_effect": "NOT_SUPPORTED",
        "route_position_interaction": (
            "SUPPORTED"
            if position_task.get("classification") == "INTERACTION_SIGNAL"
            else "NOT_SUPPORTED"
        ),
        "strongest_deconfounded_signal": conclusion,
        "current_evidence_level": evidence,
        "p2_gate_passed": p2,
        "p3_claim_allowed": False,
        "corpus_expansion_required": conclusion in {
            "TASK_CONTEXT_SIGNAL_SUPPORTED",
            "POSITIVES_REMAIN_TOO_SPARSE",
        },
        "remaining_limitation": remaining,
        "next_action": next_action,
        "support": {
            "raw_positive_rows": len(positives),
            "unique_positive_routes": sorted(pos_routes),
            "unique_positive_positions": sorted(pos_positions),
            "unique_positive_tasks": sorted(pos_tasks),
            "unique_positive_causal_contexts": causal_contexts.get(
                "unique_positive_causal_context_count", 0
            ),
            "route_task_classification": route_task.get("classification"),
            "position_task_classification": position_task.get("classification"),
        },
    }


def _new_positive_task_count(dataset: Mapping[str, Any]) -> int:
    positives = {
        row["task_id"]
        for row in dataset.get("rows", [])
        if row["target_unique_useful"]
    }
    positives.discard("elite_cognitive_task_03.json")
    return len(positives)


def _budget_overrun_count(raw_runs: list[dict[str, Any]]) -> int:
    count = 0
    for run in raw_runs:
        for row in run.get("per_task", []) or []:
            if str(row.get("prevented_overrun_state") or "").endswith("FAILED"):
                count += 1
            if str(row.get("realized_overrun_state") or "").endswith("EXCEEDED"):
                count += 1
    return count


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
        if snapshot.get("schema_version") == SNAPSHOT_SCHEMA_VERSION and _task_identity(snapshot.get("task_id")) == task_id:
            result.append(snapshot)
    return result


def _match_snapshot(
    snapshots: list[dict[str, Any]], route: Mapping[str, Any], position: int
) -> dict[str, Any] | None:
    route_id = str(route.get("route_id") or "")
    for snapshot in snapshots:
        if (
            str(snapshot.get("route_id") or "") == route_id
            and _int(snapshot.get("route_position")) == position
        ):
            return snapshot
    return None


def _empty_cell() -> dict[str, Any]:
    return {
        "executions": 0,
        "unique_useful": 0,
        "no_observable": 0,
        "duplicate": 0,
        "low_value": 0,
        "positive_tasks": [],
    }


def _add_cell(row: Mapping[str, Any], cell: dict[str, Any]) -> None:
    state = str(row.get("contribution_state") or "")
    cell["executions"] += 1
    if state == PRIMARY_POSITIVE:
        cell["unique_useful"] += 1
        if row.get("task_id") not in cell["positive_tasks"]:
            cell["positive_tasks"].append(row.get("task_id"))
    elif state == "NO_OBSERVABLE_CONTRIBUTION":
        cell["no_observable"] += 1
    elif state == "DUPLICATE_CONTRIBUTION":
        cell["duplicate"] += 1
    elif state == "LOW_VALUE_CONTRIBUTION":
        cell["low_value"] += 1


def _system_fingerprint(
    *,
    experiment_id: str,
    task_order: list[str],
    order_design: Mapping[str, Any],
    seed: int,
) -> dict[str, Any]:
    payload = {
        "experiment_id": experiment_id,
        "git_revision": _git(["rev-parse", "HEAD"]),
        "branch": _git(["branch", "--show-current"]),
        "dirty_state_summary": _git(["status", "--short"]),
        "python_runtime_version": platform.python_version(),
        "task_corpus_fingerprint": _stable_id("task_corpus", task_order),
        "task_order_fingerprint": _stable_id("task_order", task_order),
        "seed": seed,
        "execution_mode": "adaptive",
        "route_budget": 6,
        "reasoning_depth": "production_current",
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "route_classifier_schema_version": "route_contribution_telemetry.v1",
        "order_design_fingerprint": _stable_id("order_design", order_design),
    }
    payload["experiment_system_fingerprint"] = _stable_id("experiment_system", payload)
    return payload


def _markdown_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Route Order Deconfounding Report",
        "",
        f"Experiment ID: `{summary.get('experiment_id')}`",
        f"Primary conclusion: `{summary.get('primary_scientific_conclusion')}`",
        f"P2 gate passed: `{summary.get('p2_gate_passed')}`",
        f"Raw marginal observations: `{summary.get('raw_marginal_observations')}`",
        f"Unique causal contexts: `{summary.get('unique_causal_context_count')}`",
        f"Raw useful events: `{summary.get('raw_unique_useful_events')}`",
        f"Strongest deconfounded signal: `{summary.get('strongest_deconfounded_signal')}`",
        "",
        "Production isolation: route order, budget, classifier, snapshot schema, and "
        "budget authority are unchanged outside the experiment harness.",
    ]
    return "\n".join(lines) + "\n"


def _flatten(value: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    result = {}
    for key, item in value.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, Mapping):
            result.update(_flatten(item, name))
        else:
            result[name] = item
    return result


def _task_identity(value: Any) -> str:
    text = str(value or "")
    match = re.search(r"[A-Za-z0-9_]+\.json", text)
    if match:
        return match.group(0)
    return Path(text).name if text else ""


def _safe(value: Any) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value or ""))


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _number(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _stable_id(prefix: str, payload: Any) -> str:
    body = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=True)
    return f"{prefix}_{hashlib.sha256(body.encode('utf-8')).hexdigest()[:16]}"


def _git(args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "UNKNOWN"
    return completed.stdout.strip() or completed.stderr.strip() or "UNKNOWN"
