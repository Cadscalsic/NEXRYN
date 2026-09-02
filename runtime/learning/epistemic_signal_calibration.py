from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Mapping
from statistics import mean, median, pstdev
from typing import Any


AUTHORITY = {
    "authority": "OBSERVATION_ONLY",
    "behavioral_authority": "NONE",
    "selection_authority": "NONE",
    "truth_authority": "NONE",
    "execution_authority": "NONE",
    "evidence_acceptance_authority": "NONE",
}


MATCH_VALUE = {
    "EXACT_MATCH": 1.0,
    "STRONG_MATCH": 0.82,
    "PARTIAL_MATCH": 0.55,
    "NO_MATCH": 0.0,
    "UNKNOWN": 0.0,
}


def score_distribution(values: Iterable[float]) -> dict[str, float | int | None]:
    scores = sorted(float(value) for value in values)
    if not scores:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "p10": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "p99": None,
        }
    return {
        "count": len(scores),
        "min": round(scores[0], 6),
        "max": round(scores[-1], 6),
        "mean": round(mean(scores), 6),
        "median": round(median(scores), 6),
        "std": round(pstdev(scores), 6) if len(scores) > 1 else 0.0,
        "p10": round(_percentile(scores, 10), 6),
        "p25": round(_percentile(scores, 25), 6),
        "p50": round(_percentile(scores, 50), 6),
        "p75": round(_percentile(scores, 75), 6),
        "p90": round(_percentile(scores, 90), 6),
        "p95": round(_percentile(scores, 95), 6),
        "p99": round(_percentile(scores, 99), 6),
    }


def rank_margin_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        [dict(row) for row in rows],
        key=lambda item: (
            int(item.get("base_rank") or 0),
            str(item.get("task_file") or item.get("task_id") or ""),
        ),
    )
    result = []
    for index, row in enumerate(ordered):
        score = float(row.get("base_score") or 0.0)
        previous_score = (
            float(ordered[index - 1].get("base_score") or 0.0)
            if index > 0
            else None
        )
        next_score = (
            float(ordered[index + 1].get("base_score") or 0.0)
            if index + 1 < len(ordered)
            else None
        )
        previous_gap = (
            round(previous_score - score, 6)
            if previous_score is not None
            else None
        )
        next_gap = (
            round(score - next_score, 6)
            if next_score is not None
            else None
        )
        result.append({
            **row,
            "previous_score_gap": previous_gap,
            "next_score_gap": next_gap,
            "minimum_adjustment_to_move_up_one_rank": (
                None if previous_gap is None else round(max(previous_gap, 0.0), 6)
            ),
            "minimum_adjustment_to_resist_next_rank": (
                None if next_gap is None else round(max(next_gap, 0.0), 6)
            ),
        })
    return result


def derive_calibration_strategies(
    margin_rows: Iterable[Mapping[str, Any]],
    *,
    top_k: int,
) -> list[dict[str, Any]]:
    rows = list(margin_rows)
    positive_gaps = [
        float(row["next_score_gap"])
        for row in rows[: max(top_k, 1)]
        if row.get("next_score_gap") is not None
        and float(row.get("next_score_gap") or 0.0) > 0
    ]
    all_positive_gaps = [
        float(row["next_score_gap"])
        for row in rows
        if row.get("next_score_gap") is not None
        and float(row.get("next_score_gap") or 0.0) > 0
    ]
    lower_gap = _percentile(positive_gaps, 25) if positive_gaps else 0.0
    median_gap = _percentile(positive_gaps, 50) if positive_gaps else 0.0
    high_gap = _percentile(positive_gaps, 90) if positive_gaps else 0.0
    epsilon = _percentile(all_positive_gaps, 25) if all_positive_gaps else 0.0
    return [
        {
            "strategy_id": "BASELINE",
            "strategy_family": "RAW_ADDITIVE",
            "derived_parameters": {"alpha": 0.0, "source": "zero_control"},
        },
        {
            "strategy_id": "SMALL_LOCAL_GAP_ADDITIVE",
            "strategy_family": "RAW_ADDITIVE",
            "derived_parameters": {
                "alpha": round(lower_gap, 6),
                "source": "p25_positive_top_k_adjacent_gap",
            },
        },
        {
            "strategy_id": "MEDIAN_TOP_K_GAP_ADDITIVE",
            "strategy_family": "RAW_ADDITIVE",
            "derived_parameters": {
                "alpha": round(median_gap, 6),
                "source": "p50_positive_top_k_adjacent_gap",
            },
        },
        {
            "strategy_id": "LARGE_BOUNDED_TOP_K_GAP_ADDITIVE",
            "strategy_family": "RAW_ADDITIVE",
            "derived_parameters": {
                "alpha": round(high_gap, 6),
                "source": "p90_positive_top_k_adjacent_gap",
            },
        },
        {
            "strategy_id": "LOCAL_GAP_TIE_BREAK",
            "strategy_family": "LEXICOGRAPHIC_TIE_BREAK",
            "derived_parameters": {
                "epsilon": round(epsilon, 6),
                "source": "p25_positive_all_adjacent_gap",
            },
        },
        {
            "strategy_id": "NORMALIZED_MULTI_OBJECTIVE_SHADOW",
            "strategy_family": "NORMALIZED_MULTI_OBJECTIVE",
            "derived_parameters": {
                "operational_weight": 0.9,
                "epistemic_weight": 0.1,
                "source": "bounded_axis_probe",
            },
        },
    ]


def evaluate_calibration_strategies(
    rows: Iterable[Mapping[str, Any]],
    strategies: Iterable[Mapping[str, Any]],
    *,
    selected_count: int,
) -> dict[str, Any]:
    base_rows = rank_margin_rows(rows)
    base_by_file = {str(row.get("task_file")): row for row in base_rows}
    base_selected = {
        str(row.get("task_file"))
        for row in base_rows[:selected_count]
        if row.get("task_file")
    }
    matrix = []
    summaries = []
    for strategy in strategies:
        strategy_rows = _apply_strategy(base_rows, strategy)
        shadow_selected = {
            str(row.get("task_file"))
            for row in strategy_rows[:selected_count]
            if row.get("task_file")
        }
        for rank, row in enumerate(strategy_rows, start=1):
            task_file = str(row.get("task_file"))
            base_row = base_by_file[task_file]
            row["calibrated_shadow_rank"] = rank
            row["rank_delta"] = int(base_row.get("base_rank") or 0) - rank
            row["selected_base"] = task_file in base_selected
            row["selected_shadow"] = task_file in shadow_selected
            matrix.append(_matrix_row(strategy, row))
        summaries.append(
            _strategy_summary(
                strategy,
                [
                    row for row in matrix
                    if row["strategy_id"] == strategy.get("strategy_id")
                ],
                selected_count=selected_count,
            )
        )
    return {
        "score_geometry_rows": base_rows,
        "calibration_matrix": matrix,
        "strategy_summary": summaries,
        **AUTHORITY,
    }


def score_geometry_report(rows: Iterable[Mapping[str, Any]], *, top_k: int) -> dict[str, Any]:
    margin_rows = rank_margin_rows(rows)
    scores = [float(row.get("base_score") or 0.0) for row in margin_rows]
    gaps = [
        float(row.get("next_score_gap") or 0.0)
        for row in margin_rows
        if row.get("next_score_gap") is not None
    ]
    return {
        "selector_score_geometry": "PROVEN",
        "base_score_distribution": score_distribution(scores),
        "adjacent_gap_distribution": score_distribution(gaps),
        "top_k_local_margin_distribution": score_distribution([
            float(row.get("next_score_gap") or 0.0)
            for row in margin_rows[:top_k]
            if row.get("next_score_gap") is not None
        ]),
        "score_geometry_rows": margin_rows,
        **AUTHORITY,
    }


def _apply_strategy(
    rows: list[Mapping[str, Any]],
    strategy: Mapping[str, Any],
) -> list[dict[str, Any]]:
    strategy_id = strategy.get("strategy_id")
    params = strategy.get("derived_parameters") or {}
    scores = [float(row.get("base_score") or 0.0) for row in rows]
    min_score = min(scores) if scores else 0.0
    max_score = max(scores) if scores else 0.0
    span = max(max_score - min_score, 1.0)
    adjusted = []
    for row in rows:
        base_score = float(row.get("base_score") or 0.0)
        compatibility = _compatibility(row)
        match_class = str(row.get("evidence_match_class") or "UNKNOWN")
        if strategy_id == "BASELINE":
            effect = 0.0
            final = base_score
        elif strategy.get("strategy_family") == "RAW_ADDITIVE":
            alpha = float(params.get("alpha") or 0.0)
            effect = alpha * compatibility
            final = base_score + effect
        elif strategy_id == "LOCAL_GAP_TIE_BREAK":
            epsilon = float(params.get("epsilon") or 0.0)
            effect = epsilon * compatibility
            final = base_score + effect
        elif strategy_id == "NORMALIZED_MULTI_OBJECTIVE_SHADOW":
            operational_weight = float(params.get("operational_weight") or 0.9)
            epistemic_weight = float(params.get("epistemic_weight") or 0.1)
            normalized_base = (base_score - min_score) / span
            effect = epistemic_weight * compatibility
            final = (operational_weight * normalized_base) + effect
        else:
            effect = 0.0
            final = base_score
        adjusted.append({
            **dict(row),
            "calibrated_score": round(final, 8),
            "epistemic_effect": round(effect, 8),
            "compatibility": compatibility,
            "sovereignty_risk": _row_sovereignty_risk(
                row,
                effect=effect,
                score_span=span,
                match_class=match_class,
            ),
        })
    return sorted(
        adjusted,
        key=lambda item: (
            -float(item["calibrated_score"]),
            int(item.get("base_rank") or 0),
            str(item.get("task_file") or ""),
        ),
    )


def _matrix_row(strategy: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "strategy_id": strategy.get("strategy_id"),
        "strategy_family": strategy.get("strategy_family"),
        "derived_parameters": strategy.get("derived_parameters"),
        "task_id": row.get("task_id"),
        "task_file": row.get("task_file"),
        "base_rank": row.get("base_rank"),
        "calibrated_shadow_rank": row.get("calibrated_shadow_rank"),
        "rank_delta": row.get("rank_delta"),
        "base_score": row.get("base_score"),
        "epistemic_effect": row.get("epistemic_effect"),
        "compatibility": row.get("compatibility"),
        "evidence_match_class": row.get("evidence_match_class"),
        "sovereignty_risk": row.get("sovereignty_risk"),
        "selected_base": row.get("selected_base"),
        "selected_shadow": row.get("selected_shadow"),
        **AUTHORITY,
    }


def _strategy_summary(
    strategy: Mapping[str, Any],
    rows: list[Mapping[str, Any]],
    *,
    selected_count: int,
) -> dict[str, Any]:
    changed = [row for row in rows if row["rank_delta"]]
    selected_changed = [
        row for row in rows
        if bool(row["selected_base"]) != bool(row["selected_shadow"])
    ]
    selected_shadow = [row for row in rows if row["selected_shadow"]]
    promotion_counts = Counter(
        row["evidence_match_class"]
        for row in changed
        if int(row["rank_delta"] or 0) > 0
    )
    rank_deltas = [abs(int(row["rank_delta"] or 0)) for row in rows]
    compatible_selected = [
        row for row in selected_shadow
        if row["evidence_match_class"] in {
            "EXACT_MATCH",
            "STRONG_MATCH",
            "PARTIAL_MATCH",
        }
    ]
    override_rate = (
        len(selected_changed) / selected_count
        if selected_count else 0.0
    )
    responsiveness = (
        sum(1 for row in changed if float(row.get("compatibility") or 0.0) > 0.0)
        / max(1, sum(1 for row in rows if float(row.get("compatibility") or 0.0) > 0.0))
    )
    risks = {str(row.get("sovereignty_risk")) for row in rows}
    sovereignty = (
        "HIGH" if "HIGH" in risks else "MODERATE" if "MODERATE" in risks else "LOW"
    )
    return {
        "strategy_id": strategy.get("strategy_id"),
        "strategy_family": strategy.get("strategy_family"),
        "parameter_derivation": strategy.get("derived_parameters"),
        "top_k_changes": len(selected_changed),
        "mean_rank_delta": round(mean(rank_deltas), 6) if rank_deltas else 0.0,
        "max_rank_delta": max(rank_deltas) if rank_deltas else 0,
        "exact_match_promotion_count": int(promotion_counts.get("EXACT_MATCH", 0)),
        "strong_match_promotion_count": int(promotion_counts.get("STRONG_MATCH", 0)),
        "no_match_promotion_count": int(promotion_counts.get("NO_MATCH", 0)),
        "unknown_promotion_count": int(promotion_counts.get("UNKNOWN", 0)),
        "compatible_task_promotion_rate": round(
            len(compatible_selected) / max(1, len(selected_shadow)),
            6,
        ),
        "no_match_promotion_rate": round(
            promotion_counts.get("NO_MATCH", 0) / max(1, len(changed)),
            6,
        ),
        "unknown_task_effect": "NEUTRAL"
        if all(
            float(row.get("epistemic_effect") or 0.0) == 0.0
            for row in rows
            if row.get("evidence_match_class") == "UNKNOWN"
        )
        else "NON_NEUTRAL",
        "policy_override_rate": round(override_rate, 6),
        "epistemic_responsiveness": round(responsiveness, 6),
        "sovereignty_risk": sovereignty,
        "deterministic": True,
        "recommended": False,
        "rejection_reason": "not_evaluated",
        **AUTHORITY,
    }


def recommend_strategy(summaries: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    candidates = [
        dict(summary)
        for summary in summaries
        if float(summary.get("epistemic_responsiveness") or 0.0) > 0.0
        and summary.get("sovereignty_risk") in {"LOW", "MODERATE"}
        and summary.get("unknown_task_effect") == "NEUTRAL"
        and float(summary.get("no_match_promotion_rate") or 0.0) == 0.0
    ]
    if not candidates:
        return {
            "best_strategy": "NONE",
            "behavioral_rule_identified": False,
            "behavioral_integration_justified": "NO",
            "decision": "NO_SAFE_BEHAVIORAL_RULE_YET",
            **AUTHORITY,
        }
    candidates.sort(
        key=lambda item: (
            item["sovereignty_risk"] != "LOW",
            abs(float(item.get("policy_override_rate") or 0.0) - 0.2),
            -float(item.get("epistemic_responsiveness") or 0.0),
            str(item.get("strategy_id")),
        )
    )
    best = candidates[0]
    return {
        "best_strategy": best["strategy_id"],
        "behavioral_rule_identified": True,
        "behavioral_integration_justified": "NOT_YET",
        "decision": _decision_for(best),
        **AUTHORITY,
    }


def _decision_for(summary: Mapping[str, Any]) -> str:
    family = summary.get("strategy_family")
    if family == "LEXICOGRAPHIC_TIE_BREAK":
        return "LOCAL_TIE_BREAK_JUSTIFIED"
    if family == "NORMALIZED_MULTI_OBJECTIVE":
        return "MULTI_OBJECTIVE_DESIGN_PREFERRED"
    if family == "RAW_ADDITIVE":
        return "ADDITIVE_CALIBRATION_JUSTIFIED"
    return "NO_SAFE_BEHAVIORAL_RULE_YET"


def _row_sovereignty_risk(
    row: Mapping[str, Any],
    *,
    effect: float,
    score_span: float,
    match_class: str,
) -> str:
    base_rank = int(row.get("base_rank") or 0)
    if match_class == "EXACT_MATCH" and base_rank > 50 and effect > score_span * 0.1:
        return "HIGH"
    if effect > score_span * 0.02:
        return "MODERATE"
    return "LOW"


def _compatibility(row: Mapping[str, Any]) -> float:
    value = row.get("epistemic_score")
    if value is None:
        value = MATCH_VALUE.get(str(row.get("evidence_match_class")), 0.0)
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * (percentile / 100.0)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    lower_value = ordered[lower]
    upper_value = ordered[upper]
    return lower_value + (upper_value - lower_value) * (position - lower)


__all__ = [
    "AUTHORITY",
    "MATCH_VALUE",
    "derive_calibration_strategies",
    "evaluate_calibration_strategies",
    "rank_margin_rows",
    "recommend_strategy",
    "score_distribution",
    "score_geometry_report",
]
