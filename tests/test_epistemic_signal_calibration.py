from copy import deepcopy

from runtime.learning.epistemic_signal_calibration import (
    derive_calibration_strategies,
    evaluate_calibration_strategies,
    rank_margin_rows,
    recommend_strategy,
    score_distribution,
    score_geometry_report,
)


def _rows():
    return [
        {
            "task_id": "task_exact",
            "task_file": "task_exact.json",
            "base_rank": 1,
            "base_score": 100.0,
            "evidence_match_class": "EXACT_MATCH",
            "epistemic_score": 1.0,
            "selected_in_base": True,
        },
        {
            "task_id": "task_unknown",
            "task_file": "task_unknown.json",
            "base_rank": 2,
            "base_score": 99.0,
            "evidence_match_class": "UNKNOWN",
            "epistemic_score": 0.0,
            "selected_in_base": True,
        },
        {
            "task_id": "task_strong",
            "task_file": "task_strong.json",
            "base_rank": 3,
            "base_score": 98.5,
            "evidence_match_class": "STRONG_MATCH",
            "epistemic_score": 0.82,
            "selected_in_base": False,
        },
        {
            "task_id": "task_no_match",
            "task_file": "task_no_match.json",
            "base_rank": 4,
            "base_score": 10.0,
            "evidence_match_class": "NO_MATCH",
            "epistemic_score": 0.0,
            "selected_in_base": False,
        },
    ]


def test_legacy_score_rows_remain_unchanged():
    rows = _rows()
    original = deepcopy(rows)

    geometry = score_geometry_report(rows, top_k=2)

    assert rows == original
    assert geometry["score_geometry_rows"][0]["base_score"] == 100.0


def test_calibration_evaluation_is_read_only():
    rows = _rows()
    original = deepcopy(rows)
    strategies = derive_calibration_strategies(rank_margin_rows(rows), top_k=2)

    evaluate_calibration_strategies(rows, strategies, selected_count=2)

    assert rows == original


def test_baseline_no_requirement_yields_zero_epistemic_effect():
    strategies = [{
        "strategy_id": "BASELINE",
        "strategy_family": "RAW_ADDITIVE",
        "derived_parameters": {"alpha": 0.0},
    }]

    result = evaluate_calibration_strategies(_rows(), strategies, selected_count=2)

    assert all(
        row["epistemic_effect"] == 0.0
        for row in result["calibration_matrix"]
    )


def test_unknown_remains_neutral():
    rows = _rows()
    strategies = [{
        "strategy_id": "SMALL_LOCAL_GAP_ADDITIVE",
        "strategy_family": "RAW_ADDITIVE",
        "derived_parameters": {"alpha": 10.0},
    }]

    result = evaluate_calibration_strategies(rows, strategies, selected_count=2)
    unknown = next(
        row for row in result["calibration_matrix"]
        if row["task_id"] == "task_unknown"
    )

    assert unknown["epistemic_effect"] == 0.0


def test_no_match_cannot_become_exact():
    rows = _rows()
    strategies = [{
        "strategy_id": "LARGE_BOUNDED_TOP_K_GAP_ADDITIVE",
        "strategy_family": "RAW_ADDITIVE",
        "derived_parameters": {"alpha": 1000.0},
    }]

    result = evaluate_calibration_strategies(rows, strategies, selected_count=2)
    no_match = next(
        row for row in result["calibration_matrix"]
        if row["task_id"] == "task_no_match"
    )

    assert no_match["evidence_match_class"] == "NO_MATCH"
    assert no_match["epistemic_effect"] == 0.0


def test_calibration_calculation_is_deterministic():
    rows = _rows()
    strategies = derive_calibration_strategies(rank_margin_rows(rows), top_k=2)

    first = evaluate_calibration_strategies(rows, strategies, selected_count=2)
    second = evaluate_calibration_strategies(rows, strategies, selected_count=2)

    assert first == second


def test_local_rank_margins_computed_correctly():
    margins = rank_margin_rows(_rows())

    assert margins[0]["previous_score_gap"] is None
    assert margins[0]["next_score_gap"] == 1.0
    assert margins[1]["previous_score_gap"] == 1.0
    assert margins[1]["next_score_gap"] == 0.5
    assert margins[2]["minimum_adjustment_to_move_up_one_rank"] == 0.5


def test_candidate_scaling_reports_sovereignty_risk():
    rows = _rows() + [{
        "task_id": "poor_exact",
        "task_file": "poor_exact.json",
        "base_rank": 60,
        "base_score": 0.0,
        "evidence_match_class": "EXACT_MATCH",
        "epistemic_score": 1.0,
    }]
    strategies = [{
        "strategy_id": "LARGE_BOUNDED_TOP_K_GAP_ADDITIVE",
        "strategy_family": "RAW_ADDITIVE",
        "derived_parameters": {"alpha": 50.0},
    }]

    result = evaluate_calibration_strategies(rows, strategies, selected_count=2)
    summary = result["strategy_summary"][0]

    assert summary["sovereignty_risk"] in {"MODERATE", "HIGH"}


def test_shadow_strategy_never_changes_production_selected_tasks():
    rows = _rows()
    strategies = derive_calibration_strategies(rank_margin_rows(rows), top_k=2)

    result = evaluate_calibration_strategies(rows, strategies, selected_count=2)

    assert {
        row["task_file"] for row in rows if row["selected_in_base"]
    } == {"task_exact.json", "task_unknown.json"}
    assert any(
        row["selected_shadow"] != row["selected_base"]
        for row in result["calibration_matrix"]
        if row["strategy_id"] != "BASELINE"
    )


def test_task_specific_ids_do_not_appear_in_calibration_rules():
    strategies = derive_calibration_strategies(rank_margin_rows(_rows()), top_k=2)
    strategy_text = repr([strategy["derived_parameters"] for strategy in strategies])

    assert "task_exact" not in strategy_text
    assert "task_strong" not in strategy_text
    assert "task_20" not in strategy_text


def test_validation_lane_contract_is_observation_only():
    strategies = derive_calibration_strategies(rank_margin_rows(_rows()), top_k=2)
    result = evaluate_calibration_strategies(_rows(), strategies, selected_count=2)

    assert result["authority"] == "OBSERVATION_ONLY"
    assert result["selection_authority"] == "NONE"
    assert result["truth_authority"] == "NONE"
    assert result["execution_authority"] == "NONE"


def test_strategy_recommendation_requires_responsiveness_and_safety():
    strategies = derive_calibration_strategies(rank_margin_rows(_rows()), top_k=2)
    result = evaluate_calibration_strategies(_rows(), strategies, selected_count=2)

    recommendation = recommend_strategy(result["strategy_summary"])

    assert recommendation["behavioral_rule_identified"] is True
    assert recommendation["behavioral_integration_justified"] == "NOT_YET"


def test_score_distribution_percentiles():
    distribution = score_distribution([1, 2, 3, 4, 5])

    assert distribution["min"] == 1.0
    assert distribution["max"] == 5.0
    assert distribution["median"] == 3.0
