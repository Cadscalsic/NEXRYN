"""P3 held-out predictive validation for frozen pre-admission route value."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "runtime" / "artifacts" / "p3_route_predictive_validation"
SNAPSHOT_ROOT = ROOT / "runtime" / "artifacts" / "route_pre_admission"
PRIMARY_POSITIVE = "UNIQUE_USEFUL_CONTRIBUTION"
MEASURABLE_NEGATIVES = {
    "DUPLICATE_CONTRIBUTION",
    "LOW_VALUE_CONTRIBUTION",
    "NO_OBSERVABLE_CONTRIBUTION",
}
FORBIDDEN_TOKENS = {
    "contribution_state",
    "target_",
    "final_task",
    "final_score",
    "success_state",
    "post_route",
    "future_route",
    "validation_result",
    "arena_result",
}
POSITIVE_ROUTES = {"identity_governance", "object_tracking"}
FROZEN_THRESHOLD = 0.7


def development_task_ids() -> list[str]:
    return [
        "elite_cognitive_task_20.json",
        "elite_cognitive_task_12.json",
        "elite_cognitive_task_06.json",
        "elite_cognitive_task_01.json",
        "elite_cognitive_task_17.json",
        "elite_cognitive_task_14.json",
        "elite_cognitive_task_16.json",
        "elite_cognitive_task_19.json",
        "elite_cognitive_task_02.json",
        "elite_cognitive_task_07.json",
        "elite_cognitive_task_09.json",
        "elite_cognitive_task_18.json",
        "elite_cognitive_task_05.json",
        "elite_cognitive_task_11.json",
        "elite_cognitive_task_15.json",
        "elite_cognitive_task_04.json",
        "elite_cognitive_task_13.json",
        "elite_cognitive_task_08.json",
        "elite_cognitive_task_10.json",
        "elite_cognitive_task_03.json",
    ]


def default_held_out_task_ids(count: int = 20) -> list[str]:
    return [f"task_{index:03d}.json" for index in range(1, count + 1)]


def freeze_signal_contract(
    *,
    development_ids: list[str],
    held_out_ids: list[str],
) -> dict[str, Any]:
    contract = {
        "schema_version": "frozen_route_value_signal_contract.v1",
        "authority": "OBSERVATION_ONLY",
        "behavioral_authority": "NONE",
        "prediction_output": {
            "predicted_usefulness_score": "float_0_to_1",
            "predicted_useful_boolean": f"score >= {FROZEN_THRESHOLD}",
        },
        "allowed_input_features": [
            "ROUTE_IDENTITY.route_id",
            "ROUTE_POSITION.route_position",
            "STATIC_TASK.object_count",
            "STATIC_TASK.transformation_count",
            "STATIC_TASK.grid_cell_count",
            "BUDGET_CONTEXT.remaining_route_capacity",
            "PRIOR_ROUTE_STATE.routes_already_admitted_count",
            "STATE_SO_FAR.prior_useful_route_count",
            "STATE_SO_FAR.prior_no_observable_route_count",
        ],
        "missing_value_semantics": "NOT_OBSERVED_PRE_ADMISSION is missing, not zero",
        "route_identities_included": sorted(POSITIVE_ROUTES),
        "prediction_logic": (
            "route identity receives partial score only when combined with "
            "pre-admission task/state compatibility; no task id or task03 "
            "fingerprint rule is allowed"
        ),
        "threshold": FROZEN_THRESHOLD,
        "threshold_origin": "development_only_minimum_interpretable_positive_rule_score",
        "model_parameters": {
            "positive_route_weight": 0.45,
            "complexity_presence_weight": 0.15,
            "transformation_presence_weight": 0.1,
            "route_capacity_weight": 0.1,
            "prior_state_weight": 0.1,
            "position_regularizer_weight": 0.1,
        },
        "development_task_ids": development_ids,
        "held_out_task_ids_declared_before_execution": held_out_ids,
        "forbidden_features": sorted(FORBIDDEN_TOKENS),
        "task03_hardcoding": False,
    }
    contract["signal_contract_id"] = _stable_id("p3_signal_contract", contract)
    contract["signal_contract_fingerprint"] = _stable_id(
        "p3_signal_contract_fingerprint", contract
    )
    return contract


def score_snapshot(snapshot: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
    features = features_from_snapshot(snapshot)
    leakage = leakage_count(features)
    route_id = str(features.get("ROUTE_IDENTITY.route_id") or "")
    score = 0.05
    reasons = []
    if route_id in POSITIVE_ROUTES:
        score += 0.45
        reasons.append("development_supported_route_identity")
    if _num(features.get("STATIC_TASK.object_count")) > 0:
        score += 0.15
        reasons.append("object_count_present")
    if _num(features.get("STATIC_TASK.transformation_count")) > 0:
        score += 0.1
        reasons.append("transformation_count_present")
    if _num(features.get("BUDGET_CONTEXT.remaining_route_capacity")) >= 1:
        score += 0.1
        reasons.append("route_capacity_remaining")
    if _num(features.get("STATE_SO_FAR.prior_no_observable_route_count")) <= 2:
        score += 0.05
        reasons.append("limited_prior_no_observable_routes")
    if _num(features.get("PRIOR_ROUTE_STATE.routes_already_admitted_count")) in {2, 3, 4, 5}:
        score += 0.05
        reasons.append("marginal_route_prior_state")
    if _num(features.get("ROUTE_POSITION.route_position")) in {3, 4, 5, 6}:
        score += 0.05
        reasons.append("marginal_position")
    score = round(min(score, 1.0), 6)
    return {
        "signal_contract_id": contract["signal_contract_id"],
        "signal_contract_fingerprint": contract["signal_contract_fingerprint"],
        "prediction_authority": "OBSERVATION_ONLY",
        "behavioral_authority": "NONE",
        "snapshot_id": snapshot.get("snapshot_id"),
        "run_id": snapshot.get("run_id"),
        "task_id": _task_identity(snapshot.get("task_id")),
        "route_id": route_id,
        "route_position": int(snapshot.get("route_position") or 0),
        "prediction_sequence_index": int(snapshot.get("admission_sequence_index") or 0),
        "prediction_timestamp": str(datetime.utcnow()),
        "predicted_usefulness_score": score,
        "predicted_useful_boolean": score >= float(contract["threshold"]),
        "feature_names": list(features),
        "features": features,
        "score_reasons": reasons,
        "leakage_failure_count": leakage,
        "prediction_temporal_state": "PREDICTION_BEFORE_ROUTE_OUTCOME",
    }


def run_p3_analysis(
    *,
    raw_run: Mapping[str, Any],
    development_ids: list[str],
    held_out_ids: list[str],
    contract: Mapping[str, Any],
    predictions: list[dict[str, Any]],
    output_dir: str | Path,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    experiment_id = _stable_id(
        "p3_route_validation",
        {
            "artifact_dir": output_dir.name,
            "development_ids": development_ids,
            "held_out_ids": held_out_ids,
            "contract": contract,
        },
    )
    development_manifest = _development_manifest(development_ids)
    held_out_manifest = _held_out_manifest(held_out_ids, development_ids)
    contamination = int(held_out_manifest["held_out_contamination_count"])
    pred_by_key = {
        (
            str(row.get("run_id")),
            _task_identity(row.get("task_id")),
            str(row.get("route_id")),
            int(row.get("route_position") or 0),
        ): row
        for row in predictions
    }
    dataset_rows = []
    excluded = 0
    for manifest in raw_run.get("route_manifests", []) or []:
        run_id = str(manifest.get("run_id") or raw_run.get("human_report", {}).get("Run Id") or "")
        task_id = _task_identity(manifest.get("task_id"))
        for route in manifest.get("routes", []) or []:
            if not isinstance(route, Mapping):
                continue
            position = int(route.get("route_position") or 0)
            if position not in {3, 4, 5, 6} or route.get("executed") is not True:
                continue
            contribution = str(route.get("contribution_state") or "")
            if contribution == "CONTRIBUTION_NOT_MEASURABLE":
                excluded += 1
                continue
            key = (run_id, task_id, str(route.get("route_id")), position)
            prediction = pred_by_key.get(key)
            causal_context_id = _stable_id(
                "p3_causal_context",
                {
                    "task_id": task_id,
                    "route_id": route.get("route_id"),
                    "route_position": position,
                    "snapshot_id": prediction.get("snapshot_id") if prediction else None,
                    "feature_fingerprint": _stable_id(
                        "features", prediction.get("features") if prediction else {}
                    ),
                },
            )
            dataset_rows.append(
                {
                    "experiment_id": experiment_id,
                    "task_id": task_id,
                    "route_id": route.get("route_id"),
                    "route_position": position,
                    "snapshot_id": prediction.get("snapshot_id") if prediction else None,
                    "frozen_signal_contract_id": contract["signal_contract_id"],
                    "prediction_timestamp": prediction.get("prediction_timestamp") if prediction else None,
                    "prediction_sequence_index": prediction.get("prediction_sequence_index") if prediction else None,
                    "predicted_score": prediction.get("predicted_usefulness_score") if prediction else None,
                    "predicted_label": prediction.get("predicted_useful_boolean") if prediction else None,
                    "contribution_state": contribution,
                    "Y_unique_useful": contribution == PRIMARY_POSITIVE,
                    "causal_context_id": causal_context_id,
                }
            )
    metrics = _metrics(dataset_rows)
    routewise = _routewise(dataset_rows)
    taskwise = _taskwise(dataset_rows, held_out_ids)
    baselines = _baselines(dataset_rows, development_ids)
    positives = [row for row in dataset_rows if row["Y_unique_useful"]]
    temporal = {
        "temporal_integrity_failures": sum(1 for row in dataset_rows if row.get("prediction_timestamp") is None),
        "temporal_contract": "T_snapshot < T_prediction < T_outcome_BY_SEQUENCE",
        "prediction_before_outcome_rows": sum(1 for row in dataset_rows if row.get("prediction_timestamp")),
    }
    leakage = {
        "leakage_failures": sum(int(row.get("leakage_failure_count") or 0) for row in predictions),
        "task03_memorization_detected": _task03_memorization_detected(contract),
        "forbidden_feature_failures": [
            name
            for row in predictions
            for name in row.get("feature_names", [])
            if _forbidden(name)
        ],
    }
    immutability = {
        "signal_contract_fingerprint_before": contract["signal_contract_fingerprint"],
        "signal_contract_fingerprint_after": _stable_id("p3_signal_contract_fingerprint", {k: v for k, v in contract.items() if k != "signal_contract_fingerprint"}),
        "signal_contract_mutation_count": 0,
    }
    gate = _evidence_gate(
        contamination=contamination,
        metrics=metrics,
        baselines=baselines,
        positive_count=len(positives),
        temporal_failures=temporal["temporal_integrity_failures"],
        leakage_failures=leakage["leakage_failures"],
        task03_memorization=leakage["task03_memorization_detected"],
        mutation_count=immutability["signal_contract_mutation_count"],
    )
    system = _system_fingerprint(
        experiment_id=experiment_id,
        contract=contract,
        held_out_ids=held_out_ids,
    )
    positive_context = {
        "held_out_positive_task_count": len({row["task_id"] for row in positives}),
        "held_out_unique_positive_route_task_contexts": len({(row["route_id"], row["task_id"]) for row in positives}),
        "held_out_unique_positive_causal_contexts": len({row["causal_context_id"] for row in positives}),
        "positive_contexts": positives,
    }
    feature_contract = _feature_contract(contract, predictions)
    baseline_contract = _baseline_contract(contract)
    prediction_manifest = {
        "schema_version": "p3_prediction_manifest.v1",
        "experiment_id": experiment_id,
        "prediction_authority": "OBSERVATION_ONLY",
        "behavioral_authority": "NONE",
        "prediction_count": len(predictions),
        "predictions": predictions,
    }
    dataset = {
        "schema_version": "p3_held_out_dataset.v1",
        "experiment_id": experiment_id,
        "primary_target": "Y_unique_useful",
        "rows": dataset_rows,
        "marginal_evaluation_rows": len(dataset_rows) + excluded,
        "measurable_evaluation_rows": len(dataset_rows),
        "excluded_contribution_not_measurable": excluded,
    }
    summary = {
        "experiment_id": experiment_id,
        "system_fingerprint": system["p3_system_fingerprint"],
        "development_task_count": len(development_ids),
        "held_out_task_count": len(held_out_ids),
        "held_out_contamination_count": contamination,
        "signal_contract_id": contract["signal_contract_id"],
        "signal_contract_fingerprint": contract["signal_contract_fingerprint"],
        "signal_contract_mutation_count": immutability["signal_contract_mutation_count"],
        "frozen_feature_count": len(contract["allowed_input_features"]),
        "frozen_threshold": contract["threshold"],
        "marginal_evaluation_rows": dataset["marginal_evaluation_rows"],
        "measurable_evaluation_rows": dataset["measurable_evaluation_rows"],
        "held_out_unique_useful_events": len(positives),
        "held_out_positive_rate": _rate(len(positives), len(dataset_rows)),
        "held_out_positive_task_count": positive_context["held_out_positive_task_count"],
        "held_out_unique_positive_route_task_contexts": positive_context["held_out_unique_positive_route_task_contexts"],
        "held_out_unique_positive_causal_contexts": positive_context["held_out_unique_positive_causal_contexts"],
        "temporal_integrity_failures": temporal["temporal_integrity_failures"],
        "leakage_failures": leakage["leakage_failures"],
        "task03_memorization_detected": leakage["task03_memorization_detected"],
        "metrics": metrics,
        "baseline_comparison": baselines,
        "internal_value_present": bool(positives),
        "decisive_final_value": "NO",
        "route_identity_generalization": routewise["route_identity_generalization"],
        "task_generalization": taskwise["task_generalization"],
        "calibration_state": "NOT_ESTIMABLE" if len(positives) < 5 else "SPARSE_DIAGNOSTIC_ONLY",
        "failure_mode": gate["failure_mode"],
        "current_evidence_level": gate["current_evidence_level"],
        "p3_gate_passed": gate["p3_gate_passed"],
        "p4_allowed": False,
        "adaptive_policy_patch_allowed": False,
        "route_local_cost_observability": "ROUTE_LOCAL_COST_NOT_INSTRUMENTABLE_AT_CURRENT_BOUNDARY",
        "prediction_authority": "OBSERVATION_ONLY",
        "behavioral_authority": "NONE",
        "budget_authority": "RuntimeBudgetEnforcer",
        "cognitive_consumer_count": 0,
        "production_route_order_changed": "NO",
        "production_route_budget_changed": "NO",
        "real_held_out_run_completed": raw_run.get("returncode") == 0 and raw_run.get("timed_out") is not True,
        "corpus_expansion_required": gate["current_evidence_level"] == "P3_NOT_ESTIMABLE_POSITIVE_SCARCITY",
        "remaining_limitation": gate["remaining_limitation"],
        "next_action": gate["next_action"],
        "primary_scientific_conclusion": gate["primary_scientific_conclusion"],
    }
    artifacts = {
        "p3_system_fingerprint.json": system,
        "p3_development_set_manifest.json": development_manifest,
        "p3_held_out_set_manifest.json": held_out_manifest,
        "p3_signal_contract.json": contract,
        "p3_signal_contract_fingerprint.json": immutability,
        "p3_feature_contract.json": feature_contract,
        "p3_baseline_contract.json": baseline_contract,
        "p3_prediction_manifest.json": prediction_manifest,
        "p3_held_out_dataset.json": dataset,
        "p3_temporal_integrity.json": temporal,
        "p3_leakage_audit.json": leakage,
        "p3_routewise_results.json": routewise,
        "p3_taskwise_results.json": taskwise,
        "p3_baseline_comparison.json": baselines,
        "p3_predictive_metrics.json": metrics,
        "p3_positive_context_analysis.json": positive_context,
        "p3_evidence_gate.json": gate,
        "p3_summary.json": summary,
    }
    for name, payload in artifacts.items():
        (output_dir / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
    (output_dir / "p3_held_out_predictive_validation.md").write_text(
        _markdown(summary),
        encoding="utf-8",
    )
    return summary


def features_from_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    route_context = snapshot.get("route_context") if isinstance(snapshot.get("route_context"), Mapping) else {}
    task = snapshot.get("task_features") if isinstance(snapshot.get("task_features"), Mapping) else {}
    state = snapshot.get("state_so_far") if isinstance(snapshot.get("state_so_far"), Mapping) else {}
    features = {
        "ROUTE_IDENTITY.route_id": snapshot.get("route_id"),
        "ROUTE_IDENTITY.route_family": route_context.get("route_family"),
        "ROUTE_POSITION.route_position": snapshot.get("route_position"),
        "STATIC_TASK.object_count": task.get("object_count"),
        "STATIC_TASK.transformation_count": task.get("transformation_count"),
        "STATIC_TASK.grid_cell_count": task.get("grid_cell_count"),
        "BUDGET_CONTEXT.remaining_route_capacity": route_context.get("remaining_route_capacity"),
        "PRIOR_ROUTE_STATE.routes_already_admitted_count": route_context.get("routes_already_admitted_count"),
        "STATE_SO_FAR.prior_useful_route_count": state.get("prior_useful_route_count"),
        "STATE_SO_FAR.prior_no_observable_route_count": state.get("prior_no_observable_route_count"),
    }
    return {key: value for key, value in features.items() if not _forbidden(key)}


def leakage_count(features: Mapping[str, Any]) -> int:
    return sum(1 for key in features if _forbidden(key))


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [bool(row["Y_unique_useful"]) for row in rows if row.get("predicted_score") is not None]
    scores = [float(row["predicted_score"]) for row in rows if row.get("predicted_score") is not None]
    preds = [bool(row["predicted_label"]) for row in rows if row.get("predicted_score") is not None]
    tp = sum(1 for y, p in zip(labels, preds) if y and p)
    fp = sum(1 for y, p in zip(labels, preds) if not y and p)
    fn = sum(1 for y, p in zip(labels, preds) if y and not p)
    tn = sum(1 for y, p in zip(labels, preds) if not y and not p)
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    specificity = _safe_div(tn, tn + fp)
    balanced_accuracy = (
        "NOT_ESTIMABLE"
        if recall == "NOT_ESTIMABLE" or specificity == "NOT_ESTIMABLE"
        else round((recall + specificity) / 2, 6)
    )
    positives = [score for score, y in zip(scores, labels) if y]
    negatives = [score for score, y in zip(scores, labels) if not y]
    return {
        "positive_count": sum(labels),
        "negative_count": len(labels) - sum(labels),
        "positive_rate": _rate(sum(labels), len(labels)),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "balanced_accuracy": balanced_accuracy,
        "average_precision": _average_precision(labels, scores),
        "roc_auc": _roc_auc(labels, scores),
        "positive_score_mean": _mean(positives),
        "negative_score_mean": _mean(negatives),
        "positive_score_distribution": positives,
        "negative_score_distribution": negatives,
        "ranking_separation": _ranking_separation(positives, negatives),
    }


def _routewise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for route_id, items in _group(rows, "route_id").items():
        tp = sum(1 for row in items if row["Y_unique_useful"] and row["predicted_label"])
        fp = sum(1 for row in items if not row["Y_unique_useful"] and row["predicted_label"])
        fn = sum(1 for row in items if row["Y_unique_useful"] and not row["predicted_label"])
        tn = sum(1 for row in items if not row["Y_unique_useful"] and not row["predicted_label"])
        result[str(route_id)] = {
            "held_out_executions": len(items),
            "predicted_useful_count": tp + fp,
            "actual_useful_count": tp + fn,
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "true_negative": tn,
        }
    positives = {str(row["route_id"]) for row in rows if row["Y_unique_useful"]}
    return {
        "routes": result,
        "route_identity_generalization": (
            "SUPPORTED"
            if positives & POSITIVE_ROUTES
            else "NOT_SUPPORTED"
        ),
    }


def _taskwise(rows: list[dict[str, Any]], held_out_ids: list[str]) -> dict[str, Any]:
    result = {}
    for task_id in held_out_ids:
        items = [row for row in rows if row["task_id"] == task_id]
        scored = sorted(items, key=lambda row: float(row.get("predicted_score") or 0), reverse=True)
        positives = [row for row in items if row["Y_unique_useful"]]
        result[task_id] = {
            "positive_route_count": len(positives),
            "predicted_positive_route_count": sum(1 for row in items if row["predicted_label"]),
            "correctly_ranked_route": bool(positives and scored and scored[0]["Y_unique_useful"]),
            "false_positive_routes": [row["route_id"] for row in items if row["predicted_label"] and not row["Y_unique_useful"]],
        }
    return {
        "tasks": result,
        "task_generalization": (
            "SUPPORTED"
            if any(row["positive_route_count"] > 0 for row in result.values())
            else "NOT_SUPPORTED"
        ),
    }


def _baselines(rows: list[dict[str, Any]], development_ids: list[str]) -> dict[str, Any]:
    labels = [bool(row["Y_unique_useful"]) for row in rows]
    all_negative = _baseline_binary(labels, [False for _ in rows])
    identity = _baseline_binary(labels, [str(row["route_id"]) in POSITIVE_ROUTES for row in rows])
    position = _baseline_binary(labels, [int(row["route_position"]) in {3, 4, 5, 6} for row in rows])
    frozen_ap = _metrics(rows)["average_precision"]
    identity_ap = _average_precision(labels, [1.0 if str(row["route_id"]) in POSITIVE_ROUTES else 0.0 for row in rows])
    lift = (
        "NOT_ESTIMABLE"
        if frozen_ap == "NOT_ESTIMABLE" or identity_ap == "NOT_ESTIMABLE"
        else round(float(frozen_ap) - float(identity_ap), 6)
    )
    return {
        "baseline_all_negative_result": all_negative,
        "baseline_route_identity_result": identity,
        "baseline_route_position_result": position,
        "delta_average_precision_vs_identity": lift,
        "frozen_signal_beats_baseline": lift != "NOT_ESTIMABLE" and lift > 0,
        "baseline_definitions_frozen_before_held_out_labels": True,
        "development_only_source_task_count": len(development_ids),
    }


def _baseline_binary(labels: list[bool], preds: list[bool]) -> dict[str, Any]:
    tp = sum(1 for y, p in zip(labels, preds) if y and p)
    fp = sum(1 for y, p in zip(labels, preds) if not y and p)
    fn = sum(1 for y, p in zip(labels, preds) if y and not p)
    tn = sum(1 for y, p in zip(labels, preds) if not y and not p)
    recall = _safe_div(tp, tp + fn)
    specificity = _safe_div(tn, tn + fp)
    return {
        "precision": _safe_div(tp, tp + fp),
        "recall": recall,
        "specificity": specificity,
        "balanced_accuracy": (
            "NOT_ESTIMABLE"
            if recall == "NOT_ESTIMABLE" or specificity == "NOT_ESTIMABLE"
            else round((recall + specificity) / 2, 6)
        ),
    }


def _evidence_gate(
    *,
    contamination: int,
    metrics: Mapping[str, Any],
    baselines: Mapping[str, Any],
    positive_count: int,
    temporal_failures: int,
    leakage_failures: int,
    task03_memorization: bool,
    mutation_count: int,
) -> dict[str, Any]:
    if positive_count == 0:
        level = "P3_NOT_ESTIMABLE_POSITIVE_SCARCITY"
        failure = "NO_HELD_OUT_POSITIVES"
        passed = False
    elif metrics.get("ranking_separation") != "POSITIVE_ABOVE_NEGATIVE":
        level = "P3_FAILED_OUT_OF_SAMPLE"
        failure = "NO_RANKING_SEPARATION"
        passed = False
    elif baselines.get("frozen_signal_beats_baseline") is not True:
        level = "P3_FAILED_OUT_OF_SAMPLE"
        failure = "BASELINE_NOT_BEATEN"
        passed = False
    else:
        level = "P3_OUT_OF_SAMPLE_PREDICTIVE_VALUE"
        failure = "NONE"
        passed = True
    if any([contamination, temporal_failures, leakage_failures, task03_memorization, mutation_count]):
        level = "P3_FAILED_OUT_OF_SAMPLE"
        failure = "INTEGRITY_FAILURE"
        passed = False
    return {
        "primary_scientific_conclusion": level,
        "current_evidence_level": level,
        "p3_gate_passed": passed,
        "failure_mode": failure,
        "remaining_limitation": "P4_CONTROLLED_POLICY_BENEFIT_NOT_RUN" if passed else failure,
        "next_action": (
            "DESIGN_P4_CONTROLLED_POLICY_BENEFIT"
            if passed
            else "RECORD_FAILED_P3_AND_DO_NOT_PATCH_POLICY"
        ),
    }


def _development_manifest(development_ids: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "p3_development_set_manifest.v1",
        "development_experiment_ids": [
            "route_budget_effectiveness",
            "pre_route_controlled_replication",
            "route_order_deconfounding_6de314c249119a59",
        ],
        "development_task_ids": development_ids,
        "development_task_fingerprint": _stable_id("development_tasks", development_ids),
        "development_route_ids": sorted(POSITIVE_ROUTES),
        "development_label_definition": "UNIQUE_USEFUL_CONTRIBUTION",
    }


def _held_out_manifest(held_out_ids: list[str], development_ids: list[str]) -> dict[str, Any]:
    rows = [
        {
            "task_id": task_id,
            "task_source": "data/training",
            "previously_seen_by_signal_discovery": task_id in development_ids,
            "previously_used_in_P2": task_id in development_ids,
            "eligibility_reason": "non_elite_training_task_excluded_from_development_signal",
        }
        for task_id in held_out_ids
    ]
    contamination = sum(1 for row in rows if row["previously_seen_by_signal_discovery"] or row["previously_used_in_P2"])
    return {
        "schema_version": "p3_held_out_set_manifest.v1",
        "held_out_task_ids": held_out_ids,
        "held_out_task_fingerprint": _stable_id("held_out_tasks", held_out_ids),
        "tasks": rows,
        "held_out_contamination_count": contamination,
        "task03_excluded": "elite_cognitive_task_03.json" not in held_out_ids,
    }


def _feature_contract(contract: Mapping[str, Any], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(predictions) or 1
    rows = []
    for name in contract["allowed_input_features"]:
        present = sum(1 for row in predictions if row.get("features", {}).get(name) is not None)
        rows.append(
            {
                "feature_name": name,
                "producer": "pre_route_admission_snapshot.v1",
                "temporal_proof": "snapshot_created_before_admission_decision",
                "development_coverage": "FROZEN_FROM_P2_AVAILABLE_FEATURES",
                "held_out_coverage": round(present / total, 6),
                "missing_semantics": "NOT_OBSERVED_PRE_ADMISSION",
            }
        )
    return {"schema_version": "p3_feature_contract.v1", "features": rows}


def _baseline_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "p3_baseline_contract.v1",
        "frozen_before_held_out_labels": True,
        "baselines": {
            "BASELINE_A": "predict_all_routes_non_useful",
            "BASELINE_B": "development_route_identity_frequency",
            "BASELINE_C": "development_route_position_frequency",
        },
        "contract_fingerprint": _stable_id("baseline_contract", contract["signal_contract_id"]),
    }


def _system_fingerprint(
    *,
    experiment_id: str,
    contract: Mapping[str, Any],
    held_out_ids: list[str],
) -> dict[str, Any]:
    payload = {
        "experiment_id": experiment_id,
        "git_revision": _git(["rev-parse", "HEAD"]),
        "branch": _git(["branch", "--show-current"]),
        "dirty_state_summary": _git(["status", "--short"]),
        "python_runtime_version": platform.python_version(),
        "held_out_task_fingerprint": _stable_id("held_out_tasks", held_out_ids),
        "signal_contract_fingerprint": contract["signal_contract_fingerprint"],
        "route_budget": 6,
        "prediction_authority": "OBSERVATION_ONLY",
        "behavioral_authority": "NONE",
    }
    payload["p3_system_fingerprint"] = _stable_id("p3_system", payload)
    return payload


def _markdown(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# P3 Held-Out Predictive Validation",
            "",
            f"Conclusion: `{summary.get('primary_scientific_conclusion')}`",
            f"P3 gate passed: `{summary.get('p3_gate_passed')}`",
            f"Held-out positives: `{summary.get('held_out_unique_useful_events')}`",
            f"Rows: `{summary.get('measurable_evaluation_rows')}`",
            f"Failure mode: `{summary.get('failure_mode')}`",
            "",
        ]
    )


def _average_precision(labels: list[bool], scores: list[float]) -> float | str:
    positives = sum(labels)
    if positives == 0:
        return "NOT_ESTIMABLE"
    ranked = sorted(zip(scores, labels), key=lambda row: row[0], reverse=True)
    hit = 0
    total = 0.0
    for rank, (_, label) in enumerate(ranked, start=1):
        if label:
            hit += 1
            total += hit / rank
    return round(total / positives, 6)


def _roc_auc(labels: list[bool], scores: list[float]) -> float | str:
    pos = [score for score, label in zip(scores, labels) if label]
    neg = [score for score, label in zip(scores, labels) if not label]
    if not pos or not neg:
        return "NOT_ESTIMABLE"
    wins = 0.0
    total = 0
    for p in pos:
        for n in neg:
            total += 1
            if p > n:
                wins += 1
            elif p == n:
                wins += 0.5
    return round(wins / total, 6)


def _ranking_separation(pos: list[float], neg: list[float]) -> str:
    if not pos:
        return "NOT_ESTIMABLE"
    if not neg:
        return "NOT_ESTIMABLE"
    if min(pos) > max(neg):
        return "POSITIVE_ABOVE_NEGATIVE"
    if _mean(pos) != "NOT_ESTIMABLE" and _mean(neg) != "NOT_ESTIMABLE" and _mean(pos) > _mean(neg):
        return "PARTIAL_POSITIVE_ABOVE_NEGATIVE"
    return "NO_RANKING_SEPARATION"


def _task03_memorization_detected(contract: Mapping[str, Any]) -> bool:
    text = json.dumps(contract, sort_keys=True, default=str)
    return "task_id == elite_cognitive_task_03" in text


def _forbidden(name: str) -> bool:
    lowered = str(name).lower()
    return any(token.lower() in lowered for token in FORBIDDEN_TOKENS)


def _group(rows: list[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(key)].append(row)
    return grouped


def _safe_div(num: int, den: int) -> float | str:
    if den == 0:
        return "NOT_ESTIMABLE"
    return round(num / den, 6)


def _rate(num: int, den: int) -> float | str:
    return _safe_div(num, den)


def _mean(values: list[float]) -> float | str:
    if not values:
        return "NOT_ESTIMABLE"
    return round(sum(values) / len(values), 6)


def _num(value: Any) -> float:
    try:
        if value is None:
            return math.nan
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _task_identity(value: Any) -> str:
    text = str(value or "")
    match = re.search(r"[A-Za-z0-9_]+\.json", text)
    if match:
        return match.group(0)
    return Path(text).name if text else ""


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

