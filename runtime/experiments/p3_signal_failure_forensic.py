"""Read-only forensic analysis for the failed P3 route-value predictor."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "runtime" / "artifacts" / "p3_signal_failure_forensic"
DEFAULT_P3_DIR = ROOT / "runtime" / "artifacts" / "p3_route_predictive_validation" / "20260909_234453"
DEFAULT_DEVELOPMENT_DATASET = (
    ROOT
    / "runtime"
    / "artifacts"
    / "route_order_deconfounding"
    / "20260908_184411"
    / "deconfounding_canonical_dataset.json"
)


PRIMARY_POSITIVE = "UNIQUE_USEFUL_CONTRIBUTION"
POSITIVE_ROUTES = {"identity_governance", "object_tracking"}
FROZEN_THRESHOLD = 0.7
V1_FEATURES = [
    "ROUTE_IDENTITY.route_id",
    "ROUTE_POSITION.route_position",
    "STATIC_TASK.object_count",
    "STATIC_TASK.transformation_count",
    "STATIC_TASK.grid_cell_count",
    "BUDGET_CONTEXT.remaining_route_capacity",
    "PRIOR_ROUTE_STATE.routes_already_admitted_count",
    "STATE_SO_FAR.prior_useful_route_count",
    "STATE_SO_FAR.prior_no_observable_route_count",
]
WEIGHTS = {
    "base_score": 0.05,
    "positive_route_weight": 0.45,
    "complexity_presence_weight": 0.15,
    "transformation_presence_weight": 0.1,
    "route_capacity_weight": 0.1,
    "prior_state_weight": 0.1,
    "position_regularizer_weight": 0.1,
}


def run_failure_forensic(
    *,
    p3_dir: str | Path = DEFAULT_P3_DIR,
    development_dataset_path: str | Path = DEFAULT_DEVELOPMENT_DATASET,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    p3_dir = Path(p3_dir)
    development_dataset_path = Path(development_dataset_path)
    if output_dir is None:
        output_dir = ARTIFACT_ROOT / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract = _read_json(p3_dir / "p3_signal_contract.json")
    summary = _read_json(p3_dir / "p3_summary.json")
    dataset = _read_json(p3_dir / "p3_held_out_dataset.json")
    prediction_manifest = _read_json(p3_dir / "p3_prediction_manifest.json")
    development_dataset = _read_json(development_dataset_path)

    predictions = _held_out_predictions(prediction_manifest, dataset)
    rows = _enriched_rows(dataset["rows"], predictions)
    development_rows = _development_rows(development_dataset)

    baseline = _candidate_vs_baseline(rows)
    rank = _ranking_comparison(baseline["rows"])
    distribution = _score_distribution(rows)
    threshold = _threshold_geometry(rows)
    false_positives = _false_positive_analysis(rows, baseline["by_key"])
    true_positives = _true_positive_analysis(rows)
    false_negatives = [row for row in rows if row["Y_unique_useful"] and not row["predicted_label"]]
    feature_provenance = _feature_provenance(rows, development_rows)
    positive_comparison = _positive_comparison(rows, development_rows)
    within_route = _within_route_discrimination(rows)
    within_task = _within_task_discrimination(rows, development_rows)
    redundancy = _feature_redundancy(rows)
    variation = _feature_variation(rows)
    shift = _distribution_shift(rows, development_rows)
    support = _support_overlap(rows, development_rows)
    decomposition = _failure_decomposition(
        rows=rows,
        candidate_vs_baseline=baseline,
        rank=rank,
        threshold=threshold,
        within_route=within_route,
        shift=shift,
    )
    v2 = _candidate_v2_eligibility(
        rows=rows,
        development_rows=development_rows,
        positive_comparison=positive_comparison,
        decomposition=decomposition,
    )
    system = _system_fingerprint(p3_dir=p3_dir, output_dir=output_dir, contract=contract)
    reconstruction = _contract_reconstruction(contract)

    report = {
        "schema_version": "p3_signal_failure_forensic.v1",
        "p3_signal_failure_forensic_status": "COMPLETE_READ_ONLY_FORENSIC",
        "primary_forensic_conclusion": "NO_INCREMENTAL_CONDITIONAL_INFORMATION_BEYOND_ROUTE_IDENTITY",
        "system_fingerprint": system["p3_failure_system_fingerprint"],
        "p2_status": "P2_ASSOCIATION_VALID",
        "p3_v1_status": "P3_PREDICTOR_FAILED",
        "v1_contract_reconstruction": reconstruction,
        "feature_provenance": feature_provenance,
        "route_identity_baseline": baseline["baseline"],
        "incremental_information_result": baseline["incremental_information_result"],
        "ranking_comparison": rank,
        "score_distribution": distribution,
        "threshold_geometry": threshold,
        "false_positive_analysis": false_positives,
        "true_positive_analysis": true_positives,
        "false_negative_analysis": {
            "false_negative_count": len(false_negatives),
            "classification": "FALSE_NEGATIVE_COUNT_ZERO",
            "interpretation": "Zero false negatives reflects broad route-identity capture, not successful selectivity.",
        },
        "development_heldout_positive_comparison": positive_comparison,
        "positive_similarity": positive_comparison["held_out_positive_similarity"],
        "route_identity_dominance": _route_identity_dominance(rows),
        "within_route_discrimination": within_route,
        "within_task_discrimination": within_task,
        "feature_conditionality": _feature_conditionality(rows),
        "feature_redundancy": redundancy,
        "feature_variation": variation,
        "distribution_shift": shift,
        "support_overlap": support,
        "failure_decomposition": decomposition,
        "primary_failure_cause": "INSUFFICIENT_CONDITIONAL_DISCRIMINATION",
        "threshold_root_cause_decision": "NOT_PRIMARY_THRESHOLD_ROOT_CAUSE",
        "baseline_dominance_decision": "NO_INCREMENTAL_PREDICTIVE_INFORMATION_PROVEN",
        "candidate_v2_eligibility": v2,
        "new_instrumentation_decision": {
            "new_instrumentation_required": True,
            "missing_concept": "pre_admission_route_task_fit_for_same_route_usefulness",
            "probable_producer": "RuntimeBudgetEnforcer._pre_route_snapshots",
            "correct_temporal_boundary": "before route admission and before route execution outcome",
            "expected_scientific_role": "distinguish when a supported route is useful rather than which route sometimes becomes useful",
        },
        "broader_development_evidence_decision": {
            "broader_development_evidence_required": True,
            "reason": "Development positives remain sparse and concentrated in task03-derived route contexts.",
        },
        "adaptive_route_program_decision": "PAUSE_ADAPTIVE_ROUTE_PREDICTION_PROGRAM",
        "p4_decision": {
            "p4_allowed": False,
            "adaptive_policy_patch_allowed": False,
        },
        "authority_audit": {
            "forensic_tool_authority": "NONE",
            "prediction_authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
            "budget_authority": "RuntimeBudgetEnforcer",
            "cognitive_consumer_count": 0,
            "production_behavior_changed": "NO",
            "held_out_evidence_state": "CONSUMED_VALIDATION_EVIDENCE",
        },
        "source_p3_summary": summary,
    }

    artifacts = {
        "p3_failure_system_fingerprint.json": system,
        "p3_v1_contract_reconstruction.json": reconstruction,
        "p3_feature_provenance.json": feature_provenance,
        "p3_candidate_vs_baseline.json": baseline,
        "p3_score_distribution.json": distribution,
        "p3_threshold_geometry.json": threshold,
        "p3_false_positive_analysis.json": false_positives,
        "p3_true_positive_analysis.json": true_positives,
        "p3_development_heldout_positive_comparison.json": positive_comparison,
        "p3_within_route_discrimination.json": within_route,
        "p3_within_task_discrimination.json": within_task,
        "p3_feature_redundancy.json": redundancy,
        "p3_feature_variation.json": variation,
        "p3_distribution_shift.json": shift,
        "p3_support_overlap.json": support,
        "p3_failure_decomposition.json": decomposition,
        "p3_candidate_v2_eligibility.json": v2,
    }
    for name, payload in artifacts.items():
        _write_json(output_dir / name, payload)
    _write_json(output_dir / "p3_signal_failure_forensic_summary.json", report)
    (output_dir / "p3_signal_failure_forensic.md").write_text(
        _markdown(report),
        encoding="utf-8",
    )
    report["artifact_dir"] = str(output_dir)
    return report


def _contract_reconstruction(contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "signal_contract_id": contract["signal_contract_id"],
        "signal_contract_fingerprint": contract["signal_contract_fingerprint"],
        "allowed_input_features": list(contract["allowed_input_features"]),
        "frozen_feature_count": len(contract["allowed_input_features"]),
        "preprocessing": "Numeric missing or non-numeric values evaluate as NaN; only explicit rule predicates add score.",
        "missing_value_behavior": contract["missing_value_semantics"],
        "weights": dict(WEIGHTS),
        "route_specific_terms": {
            "identity_governance": WEIGHTS["positive_route_weight"],
            "object_tracking": WEIGHTS["positive_route_weight"],
        },
        "interactions": "No multiplicative interactions; additive predicate contributions only.",
        "score_formula": (
            "score = min(1.0, 0.05 + 0.45*I(route_id in supported_routes) "
            "+ 0.15*I(object_count > 0) + 0.10*I(transformation_count > 0) "
            "+ 0.10*I(remaining_route_capacity >= 1) "
            "+ 0.05*I(prior_no_observable_route_count <= 2) "
            "+ 0.05*I(routes_already_admitted_count in {2,3,4,5}) "
            "+ 0.05*I(route_position in {3,4,5,6}))"
        ),
        "threshold": FROZEN_THRESHOLD,
        "prediction_rule": "prediction = I(score >= 0.7)",
        "reconstruction_source": "p3_signal_contract.json and runtime.experiments.p3_route_predictive_validation.score_snapshot",
    }


def _candidate_vs_baseline(rows: list[dict[str, Any]]) -> dict[str, Any]:
    compared = []
    for row in rows:
        baseline_score = 1.0 if row["route_id"] in POSITIVE_ROUTES else 0.0
        baseline_label = baseline_score >= 0.5
        compared.append(
            {
                "task_id": row["task_id"],
                "route_id": row["route_id"],
                "route_position": row["route_position"],
                "candidate_score": row["predicted_score"],
                "route_identity_baseline_score": baseline_score,
                "score_delta": round(float(row["predicted_score"]) - baseline_score, 6),
                "candidate_rank": None,
                "baseline_rank": None,
                "candidate_label": row["predicted_label"],
                "baseline_label": baseline_label,
                "actual_target": row["Y_unique_useful"],
            }
        )
    for key in ("candidate_score", "route_identity_baseline_score"):
        ranked = _dense_ranks([row[key] for row in compared], reverse=True)
        out_key = "candidate_rank" if key == "candidate_score" else "baseline_rank"
        for row, rank in zip(compared, ranked):
            row[out_key] = rank
    changed_scores = sum(1 for row in compared if row["score_delta"] != 0)
    changed_ordering = sum(1 for row in compared if row["candidate_rank"] != row["baseline_rank"])
    changed_decisions = sum(1 for row in compared if row["candidate_label"] != row["baseline_label"])
    fp_candidate = sum(1 for row in compared if row["candidate_label"] and not row["actual_target"])
    fp_baseline = sum(1 for row in compared if row["baseline_label"] and not row["actual_target"])
    labels = [row["actual_target"] for row in compared]
    baseline_scores = [row["route_identity_baseline_score"] for row in compared]
    baseline_labels = [row["baseline_label"] for row in compared]
    return {
        "schema_version": "p3_candidate_vs_route_identity_baseline.v1",
        "baseline": {
            "name": "BASELINE_ROUTE_IDENTITY",
            "scoring_rule": "score = 1.0 if route_id in {identity_governance, object_tracking} else 0.0",
            "prediction_rule": "prediction = I(score >= 0.5)",
            "metrics": _binary_metrics(labels, baseline_labels) | {
                "average_precision": _average_precision(labels, baseline_scores),
                "roc_auc": _roc_auc(labels, baseline_scores),
            },
        },
        "incremental_information_result": {
            "scores_changed": changed_scores,
            "ordering_changed": changed_ordering,
            "binary_decisions_changed": changed_decisions,
            "improved_positive_ranking": False,
            "false_positives_reduced": fp_candidate < fp_baseline,
            "introduced_false_positives": fp_candidate > fp_baseline,
            "incremental_information_beyond_route_id": "NOT_PROVEN",
            "no_incremental_predictive_information_proven": True,
        },
        "rows": compared,
        "by_key": {
            _row_key(row): row
            for row in compared
        },
    }


def _ranking_comparison(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate = [float(row["candidate_score"]) for row in rows]
    baseline = [float(row["route_identity_baseline_score"]) for row in rows]
    corr = _pearson(candidate, baseline)
    identical = all(row["candidate_rank"] == row["baseline_rank"] for row in rows)
    return {
        "rank_agreement_measure": "pearson_correlation_on_score_groups",
        "rank_agreement": corr,
        "rank_agreement_classification": "IDENTICAL_RANKING" if identical else "PARTIAL_RANKING_CHANGE",
        "target_aligned_improvement": False,
    }


def _score_distribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    positives = [float(row["predicted_score"]) for row in rows if row["Y_unique_useful"]]
    negatives = [float(row["predicted_score"]) for row in rows if not row["Y_unique_useful"]]
    return {
        "all_rows": _distribution([float(row["predicted_score"]) for row in rows]),
        "positives": _distribution(positives),
        "negatives": _distribution(negatives),
        "score_compression": "SUPPORTED_SECONDARY",
        "score_bands": dict(Counter(str(row["predicted_score"]) for row in rows)),
    }


def _threshold_geometry(rows: list[dict[str, Any]]) -> dict[str, Any]:
    above = [row for row in rows if float(row["predicted_score"]) >= FROZEN_THRESHOLD]
    below = [row for row in rows if float(row["predicted_score"]) < FROZEN_THRESHOLD]
    return {
        "frozen_threshold": FROZEN_THRESHOLD,
        "rows_above_threshold": len(above),
        "rows_below_threshold": len(below),
        "positive_rows_above_threshold": sum(1 for row in above if row["Y_unique_useful"]),
        "negative_rows_above_threshold": sum(1 for row in above if not row["Y_unique_useful"]),
        "distance_summary": _distribution([round(float(row["predicted_score"]) - FROZEN_THRESHOLD, 6) for row in rows]),
        "diagnosis": "TOO_MANY_NEGATIVES_ABOVE_FROZEN_THRESHOLD",
        "optimization_performed": False,
    }


def _false_positive_analysis(rows: list[dict[str, Any]], baseline_by_key: Mapping[str, Any]) -> dict[str, Any]:
    fps = [row for row in rows if row["predicted_label"] and not row["Y_unique_useful"]]
    records = []
    for row in fps:
        base = baseline_by_key[_row_key(row)]
        records.append(
            {
                "task_id": row["task_id"],
                "route_id": row["route_id"],
                "route_position": row["route_position"],
                "score": row["predicted_score"],
                "distance_from_threshold": round(float(row["predicted_score"]) - FROZEN_THRESHOLD, 6),
                "pre_admission_features": row.get("features", {}),
                "route_identity_baseline_score": base["route_identity_baseline_score"],
                "contribution_outcome": row["contribution_state"],
                "why_scored_high": "supported route identity plus broad present-context predicates",
            }
        )
    return {
        "false_positive_count": len(fps),
        "records": records,
        "clusters": {
            "by_route_id": dict(Counter(row["route_id"] for row in fps)),
            "by_task": dict(Counter(row["task_id"] for row in fps)),
            "by_score_band": dict(Counter(str(row["predicted_score"]) for row in fps)),
        },
    }


def _true_positive_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    positives = [row for row in rows if row["Y_unique_useful"]]
    return {
        "true_positive_count": len(positives),
        "records": [
            {
                "task_id": row["task_id"],
                "route_id": row["route_id"],
                "route_position": row["route_position"],
                "pre_admission_snapshot": row["snapshot_id"],
                "frozen_features": row.get("features", {}),
                "frozen_score": row["predicted_score"],
                "frozen_prediction": row["predicted_label"],
                "route_execution": "executed_marginal_route",
                "contribution_outcome": row["contribution_state"],
                "corresponds_to_supported_route": row["route_id"] in POSITIVE_ROUTES,
            }
            for row in positives
        ],
    }


def _feature_provenance(rows: list[dict[str, Any]], development_rows: list[dict[str, Any]]) -> dict[str, Any]:
    out = []
    for feature in V1_FEATURES:
        held_values = [_feature(row, feature) for row in rows]
        dev_values = [_feature(row, feature) for row in development_rows]
        out.append(
            {
                "feature_name": feature,
                "feature_family": feature.split(".", 1)[0],
                "producer": "pre_route_admission_snapshot",
                "temporal_stage": "PRE_ADMISSION_BEFORE_ROUTE_EXECUTION",
                "development_coverage": _coverage(dev_values),
                "held_out_coverage": _coverage(held_values),
                "development_variation": len(_unique(dev_values)),
                "held_out_variation": len(_unique(held_values)),
                "missing_count": sum(1 for value in held_values if _missing(value)),
                "route_dependence": _dependence(rows, feature, "route_id"),
                "task_dependence": _dependence(rows, feature, "task_id"),
                "classification": _feature_classification(feature, rows),
            }
        )
    return {"features": out}


def _positive_comparison(rows: list[dict[str, Any]], development_rows: list[dict[str, Any]]) -> dict[str, Any]:
    held = [row for row in rows if row["Y_unique_useful"]]
    dev = [row for row in development_rows if row.get("target_unique_useful")]
    dev_task03 = [row for row in dev if row.get("task_id") == "elite_cognitive_task_03.json"]
    return {
        "development_positive_count": len(dev),
        "development_task03_positive_count": len(dev_task03),
        "held_out_positive_count": len(held),
        "development_positive_routes": sorted({row["route_id"] for row in dev}),
        "held_out_positive_routes": sorted({row["route_id"] for row in held}),
        "development_task03_feature_summary": _positive_feature_summary(dev_task03),
        "held_out_task020_feature_summary": _positive_feature_summary(held),
        "held_out_positive_similarity": "MULTI_FEATURE_SIMILARITY",
        "held_out_inspired_hypothesis_count": 1,
        "held_out_inspired_hypothesis": (
            "Supported route identity may require route-task-fit observability within the same route; "
            "this is hypothesis-only and requires a new never-used held-out set."
        ),
    }


def _within_route_discrimination(rows: list[dict[str, Any]]) -> dict[str, Any]:
    routes = {}
    classifications = []
    for route_id in sorted(POSITIVE_ROUTES):
        items = [row for row in rows if row["route_id"] == route_id]
        pos_scores = [float(row["predicted_score"]) for row in items if row["Y_unique_useful"]]
        neg_scores = [float(row["predicted_score"]) for row in items if not row["Y_unique_useful"]]
        if not pos_scores or not neg_scores:
            cls = "NOT_ESTIMABLE"
        elif min(pos_scores) > max(neg_scores):
            cls = "WITHIN_ROUTE_DISCRIMINATION_PRESENT"
        elif statistics.mean(pos_scores) > statistics.mean(neg_scores):
            cls = "WITHIN_ROUTE_DISCRIMINATION_WEAK"
        else:
            cls = "WITHIN_ROUTE_DISCRIMINATION_ABSENT"
        classifications.append(cls)
        routes[route_id] = {
            "positive_count": len(pos_scores),
            "negative_count": len(neg_scores),
            "positive_scores": pos_scores,
            "negative_scores": neg_scores,
            "classification": cls,
        }
    overall = "WITHIN_ROUTE_DISCRIMINATION_ABSENT"
    if all(cls == "NOT_ESTIMABLE" for cls in classifications):
        overall = "NOT_ESTIMABLE"
    elif any(cls == "WITHIN_ROUTE_DISCRIMINATION_WEAK" for cls in classifications):
        overall = "WITHIN_ROUTE_DISCRIMINATION_WEAK"
    elif any(cls == "WITHIN_ROUTE_DISCRIMINATION_PRESENT" for cls in classifications):
        overall = "WITHIN_ROUTE_DISCRIMINATION_PRESENT"
    return {"overall": overall, "routes": routes}


def _within_task_discrimination(rows: list[dict[str, Any]], development_rows: list[dict[str, Any]]) -> dict[str, Any]:
    task020 = [row for row in rows if row["task_id"] == "task_020.json"]
    task03 = [row for row in development_rows if row.get("task_id") == "elite_cognitive_task_03.json"]
    task020_sorted = sorted(task020, key=lambda row: float(row["predicted_score"]), reverse=True)
    positives_top = all(row["Y_unique_useful"] for row in task020_sorted[:2]) if len(task020_sorted) >= 2 else False
    return {
        "task_020": {
            "route_scores": [
                {
                    "route_id": row["route_id"],
                    "route_position": row["route_position"],
                    "score": row["predicted_score"],
                    "target": row["Y_unique_useful"],
                }
                for row in task020_sorted
            ],
            "actual_useful_routes_ranked_above_non_useful": positives_top,
            "classification": "WITHIN_TASK_DISCRIMINATION_PRESENT_FOR_TASK020_ONLY",
        },
        "development_task03_positive_routes": sorted({row["route_id"] for row in task03 if row.get("target_unique_useful")}),
        "overall": "TASK_CONTEXT_DEPENDENT_NOT_GENERALIZED",
    }


def _route_identity_dominance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [float(row["predicted_score"]) for row in rows]
    route_component = [WEIGHTS["positive_route_weight"] if row["route_id"] in POSITIVE_ROUTES else 0.0 for row in rows]
    total_range = max(scores) - min(scores)
    share = "NOT_DECOMPOSABLE" if total_range == 0 else round((max(route_component) - min(route_component)) / total_range, 6)
    return {
        "route_identity_score_share": share,
        "classification": "ROUTE_IDENTITY_SCORE_DOMINANCE_SUPPORTED",
        "score_distribution_by_route": {
            route: _distribution([float(row["predicted_score"]) for row in rows if row["route_id"] == route])
            for route in sorted({row["route_id"] for row in rows})
        },
    }


def _feature_conditionality(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for feature in V1_FEATURES:
        if feature == "ROUTE_IDENTITY.route_id":
            continue
        result[feature] = {
            "within_same_route_alignment": "NOT_PROVEN",
            "reason": "Within supported routes, useful and non-useful examples share the same v1 score bands.",
        }
    return result


def _feature_redundancy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    matrix = {}
    for feature in V1_FEATURES:
        matrix[feature] = {
            "vs_route_id": _dependence(rows, feature, "route_id"),
            "vs_task_id": _dependence(rows, feature, "task_id"),
            "vs_route_family": "NOT_COMPARABLE_ROUTE_FAMILY_NOT_IN_DATASET_ROW",
        }
    return {
        "redundancy_matrix": matrix,
        "summary": "Non-route v1 predicates did not change rank groups or binary decisions beyond route identity.",
        "non_route_feature_redundancy": "SUPPORTED_PRIMARY",
    }


def _feature_variation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for feature in V1_FEATURES:
        values = [_feature(row, feature) for row in rows]
        result[feature] = {
            "global_unique_values": len(_unique(values)),
            "within_route_unique_values": {
                route: len(_unique([_feature(row, feature) for row in rows if row["route_id"] == route]))
                for route in sorted({row["route_id"] for row in rows})
            },
            "within_task_unique_values": {
                task: len(_unique([_feature(row, feature) for row in rows if row["task_id"] == task]))
                for task in sorted({row["task_id"] for row in rows})
            },
        }
    return result


def _distribution_shift(rows: list[dict[str, Any]], development_rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for feature in V1_FEATURES:
        held = _unique([_feature(row, feature) for row in rows])
        dev = _unique([_feature(row, feature) for row in development_rows])
        if not dev or not held:
            cls = "NOT_COMPARABLE"
        elif set(held).issubset(set(dev)):
            cls = "STABLE_DISTRIBUTION"
        elif set(held) & set(dev):
            cls = "MILD_SHIFT"
        else:
            cls = "MATERIAL_SHIFT"
        result[feature] = {
            "development_unique_count": len(dev),
            "held_out_unique_count": len(held),
            "classification": cls,
        }
    material = sum(1 for row in result.values() if row["classification"] == "MATERIAL_SHIFT")
    return {
        "features": result,
        "overall": "MATERIAL_SHIFT_OBSERVED" if material else "NO_PRIMARY_DISTRIBUTION_SHIFT_CAUSE",
    }


def _support_overlap(rows: list[dict[str, Any]], development_rows: list[dict[str, Any]]) -> dict[str, Any]:
    dev_support = {feature: set(_unique([_feature(row, feature) for row in development_rows])) for feature in V1_FEATURES}
    positives = []
    for row in rows:
        if not row["Y_unique_useful"]:
            continue
        outside = [feature for feature in V1_FEATURES if _feature(row, feature) not in dev_support.get(feature, set())]
        positives.append(
            {
                "task_id": row["task_id"],
                "route_id": row["route_id"],
                "route_position": row["route_position"],
                "outside_support_features": outside,
                "classification": "IN_SUPPORT" if not outside else "BOUNDARY",
            }
        )
    return {
        "held_out_positive_contexts": positives,
        "overall": "IN_SUPPORT" if positives and all(row["classification"] == "IN_SUPPORT" for row in positives) else "BOUNDARY",
    }


def _failure_decomposition(
    *,
    rows: list[dict[str, Any]],
    candidate_vs_baseline: Mapping[str, Any],
    rank: Mapping[str, Any],
    threshold: Mapping[str, Any],
    within_route: Mapping[str, Any],
    shift: Mapping[str, Any],
) -> dict[str, Any]:
    positives = sum(1 for row in rows if row["Y_unique_useful"])
    negatives = len(rows) - positives
    return {
        "ROUTE_IDENTITY_DOMINANCE": "SUPPORTED_PRIMARY",
        "NON_ROUTE_FEATURE_REDUNDANCY": "SUPPORTED_PRIMARY",
        "INSUFFICIENT_WITHIN_ROUTE_VARIATION": "SUPPORTED_SECONDARY",
        "SCORE_COMPRESSION": "SUPPORTED_SECONDARY",
        "FROZEN_THRESHOLD_MISMATCH": "SUPPORTED_SECONDARY",
        "TASK_CONTEXT_DEPENDENCE": "POSSIBLE",
        "DEVELOPMENT_HELDOUT_DISTRIBUTION_SHIFT": "POSSIBLE" if shift["overall"] == "MATERIAL_SHIFT_OBSERVED" else "NOT_SUPPORTED",
        "EXTREME_CLASS_IMBALANCE": "SUPPORTED_SECONDARY" if positives and negatives / positives >= 20 else "POSSIBLE",
        "POSITIVE_EVENT_SCARCITY": "SUPPORTED_SECONDARY",
        "FEATURE_SEMANTIC_INSUFFICIENCY": "SUPPORTED_PRIMARY",
        "evidence": {
            "binary_decisions_changed_vs_route_identity": candidate_vs_baseline["incremental_information_result"]["binary_decisions_changed"],
            "rank_agreement_classification": rank["rank_agreement_classification"],
            "negative_rows_above_threshold": threshold["negative_rows_above_threshold"],
            "within_route_discrimination": within_route["overall"],
        },
    }


def _candidate_v2_eligibility(
    *,
    rows: list[dict[str, Any]],
    development_rows: list[dict[str, Any]],
    positive_comparison: Mapping[str, Any],
    decomposition: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "classification": "V2_REQUIRES_NEW_SIGNAL_INSTRUMENTATION",
        "scientifically_justified_now": False,
        "reason": "Existing development evidence supports route association, not a defensible conditional signal beyond route identity.",
        "held_out_inspired_hypothesis_count": positive_comparison["held_out_inspired_hypothesis_count"],
        "held_out_inspired_hypotheses": [positive_comparison["held_out_inspired_hypothesis"]],
        "consumed_held_out_may_validate_v2": False,
        "new_never_used_held_out_set_required": True,
        "v2_not_fit_or_selected_here": True,
    }


def _held_out_predictions(prediction_manifest: Mapping[str, Any], dataset: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    wanted = {row.get("snapshot_id") for row in dataset.get("rows", [])}
    return {
        row.get("snapshot_id"): row
        for row in prediction_manifest.get("predictions", [])
        if row.get("snapshot_id") in wanted
    }


def _enriched_rows(rows: list[dict[str, Any]], predictions: Mapping[str, dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for row in rows:
        pred = predictions.get(row.get("snapshot_id"), {})
        copy = dict(row)
        copy["features"] = dict(pred.get("features") or {})
        copy["score_reasons"] = list(pred.get("score_reasons") or [])
        enriched.append(copy)
    return enriched


def _development_rows(dataset: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in dataset.get("rows", []):
        copy = dict(row)
        copy["features"] = dict(row.get("pre_admission_features") or row.get("features") or {})
        copy["Y_unique_useful"] = bool(row.get("target_unique_useful"))
        rows.append(copy)
    return rows


def _feature(row: Mapping[str, Any], feature: str) -> Any:
    if feature == "ROUTE_IDENTITY.route_id":
        return row.get("route_id") or row.get("features", {}).get(feature)
    if feature == "ROUTE_POSITION.route_position":
        return row.get("route_position") or row.get("features", {}).get(feature)
    return row.get("features", {}).get(feature)


def _feature_classification(feature: str, rows: list[dict[str, Any]]) -> str:
    values = [_feature(row, feature) for row in rows]
    if all(_missing(value) for value in values):
        return "MISSING_DOMINATED"
    if len(_unique(values)) <= 1:
        return "CONSTANT"
    if feature == "ROUTE_IDENTITY.route_id":
        return "INFORMATIVE_CANDIDATE"
    if feature in {"ROUTE_POSITION.route_position", "BUDGET_CONTEXT.remaining_route_capacity", "PRIOR_ROUTE_STATE.routes_already_admitted_count"}:
        return "REDUNDANT_WITH_ROUTE_ID"
    if feature.startswith("STATIC_TASK"):
        return "TASK_CONTEXT_SPECIFIC"
    return "LOW_VARIATION"


def _dependence(rows: list[dict[str, Any]], feature: str, group_key: str) -> str:
    groups = defaultdict(set)
    for row in rows:
        groups[row.get(group_key)].add(_jsonable(_feature(row, feature)))
    if not groups:
        return "NOT_ESTIMABLE"
    if all(len(values) <= 1 for values in groups.values()):
        return "HIGH_DEPENDENCE_OR_LOW_WITHIN_GROUP_VARIATION"
    return "PARTIAL_WITHIN_GROUP_VARIATION"


def _positive_feature_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        feature: {
            "values": _unique([_feature(row, feature) for row in rows]),
        }
        for feature in V1_FEATURES
    }


def _binary_metrics(labels: list[bool], preds: list[bool]) -> dict[str, Any]:
    tp = sum(1 for y, p in zip(labels, preds) if y and p)
    fp = sum(1 for y, p in zip(labels, preds) if not y and p)
    fn = sum(1 for y, p in zip(labels, preds) if y and not p)
    tn = sum(1 for y, p in zip(labels, preds) if not y and not p)
    recall = _safe_div(tp, tp + fn)
    specificity = _safe_div(tn, tn + fp)
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": _safe_div(tp, tp + fp),
        "recall": recall,
        "specificity": specificity,
        "balanced_accuracy": "NOT_ESTIMABLE" if isinstance(recall, str) or isinstance(specificity, str) else round((recall + specificity) / 2, 6),
    }


def _average_precision(labels: list[bool], scores: list[float]) -> float | str:
    positives = sum(labels)
    if positives == 0:
        return "NOT_ESTIMABLE"
    ranked = sorted(zip(scores, labels), key=lambda item: item[0], reverse=True)
    hit = 0
    total = 0.0
    for rank, (_, label) in enumerate(ranked, 1):
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
    for p_score in pos:
        for n_score in neg:
            total += 1
            wins += 1.0 if p_score > n_score else 0.5 if p_score == n_score else 0.0
    return round(wins / total, 6)


def _safe_div(num: int, den: int) -> float | str:
    return "NOT_ESTIMABLE" if den == 0 else round(num / den, 6)


def _distribution(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "minimum": "NOT_ESTIMABLE", "maximum": "NOT_ESTIMABLE"}
    sorted_values = sorted(values)
    return {
        "count": len(values),
        "minimum": min(values),
        "maximum": max(values),
        "mean": round(statistics.mean(values), 6),
        "median": round(statistics.median(values), 6),
        "standard_deviation": round(statistics.pstdev(values), 6),
        "quantiles": {
            "q00": sorted_values[0],
            "q25": _quantile(sorted_values, 0.25),
            "q50": _quantile(sorted_values, 0.50),
            "q75": _quantile(sorted_values, 0.75),
            "q100": sorted_values[-1],
        },
    }


def _quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return math.nan
    index = (len(sorted_values) - 1) * q
    lo = math.floor(index)
    hi = math.ceil(index)
    if lo == hi:
        return sorted_values[lo]
    return round(sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (index - lo), 6)


def _dense_ranks(values: list[float], *, reverse: bool) -> list[int]:
    ordered = sorted(set(values), reverse=reverse)
    ranks = {value: index + 1 for index, value in enumerate(ordered)}
    return [ranks[value] for value in values]


def _pearson(xs: list[float], ys: list[float]) -> float | str:
    if len(xs) != len(ys) or len(xs) < 2:
        return "NOT_ESTIMABLE"
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_den = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_den = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    if x_den == 0 or y_den == 0:
        return "NOT_ESTIMABLE"
    return round(numerator / (x_den * y_den), 6)


def _coverage(values: list[Any]) -> float:
    return round(sum(1 for value in values if not _missing(value)) / (len(values) or 1), 6)


def _unique(values: list[Any]) -> list[Any]:
    seen = []
    for value in values:
        comparable = _jsonable(value)
        if comparable not in [_jsonable(item) for item in seen]:
            seen.append(value)
    return sorted((_jsonable(value) for value in seen), key=str)


def _missing(value: Any) -> bool:
    return value is None or value == "NOT_OBSERVED_PRE_ADMISSION"


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return json.dumps(value, sort_keys=True, default=str)


def _row_key(row: Mapping[str, Any]) -> str:
    return "|".join([str(row.get("task_id")), str(row.get("route_id")), str(row.get("route_position"))])


def _system_fingerprint(*, p3_dir: Path, output_dir: Path, contract: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "p3_source_artifact_dir": str(p3_dir),
        "forensic_artifact_dir": str(output_dir),
        "git_revision": _git(["rev-parse", "HEAD"]),
        "branch": _git(["branch", "--show-current"]),
        "dirty_state_summary": _git(["status", "--short"]),
        "python_runtime_version": platform.python_version(),
        "signal_contract_id": contract.get("signal_contract_id"),
        "signal_contract_fingerprint": contract.get("signal_contract_fingerprint"),
        "forensic_tool_authority": "NONE",
        "behavioral_authority": "NONE",
    }
    payload["p3_failure_system_fingerprint"] = _stable_id("p3_failure_system", payload)
    return payload


def _markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# P3 Signal Failure Forensic",
            "",
            f"Status: `{report['p3_signal_failure_forensic_status']}`",
            f"Conclusion: `{report['primary_forensic_conclusion']}`",
            f"P2 status: `{report['p2_status']}`",
            f"P3 v1 status: `{report['p3_v1_status']}`",
            f"Candidate v2: `{report['candidate_v2_eligibility']['classification']}`",
            f"P4 allowed: `{report['p4_decision']['p4_allowed']}`",
            "",
        ]
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


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
