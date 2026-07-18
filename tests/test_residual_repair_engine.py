import numpy as np

from runtime.reasoning.counterfactual_repair_engine import (
    CounterfactualRepairEngine,
)
from runtime.reasoning.object_residual_repair import ObjectResidualRepair
from runtime.reasoning.residual_reasoning_engine import ResidualReasoningEngine
from runtime.reasoning.spatial_residual_repair import SpatialResidualRepair
from runtime.stages.evaluation import evaluation_stage


def test_residual_reasoning_activates_localized_repair_mode():
    predicted = np.zeros((5, 5), dtype=int)
    target = predicted.copy()
    target[2, 2] = 8

    report = ResidualReasoningEngine().analyze(
        predicted,
        target,
        runtime_context={"active_concepts": ["inside_outside"]},
        evaluation_result={"accuracy": 0.96, "difference_count": 1},
    )

    assert report["repair_mode"] == "LOCALIZED_REPAIR_MODE"
    assert report["residual_count"] == 1
    assert report["residual_locations"] == [[2, 2]]
    assert report["residual_type"] == "containment_residual"
    assert report["repair_candidates"][0]["candidate_value"] == 8


def test_counterfactual_repair_accepts_only_improving_candidate():
    predicted = np.zeros((5, 5), dtype=int)
    target = predicted.copy()
    target[2, 2] = 8
    residual_report = ResidualReasoningEngine().analyze(
        predicted,
        target,
        evaluation_result={"accuracy": 0.96, "difference_count": 1},
    )
    spatial_report = SpatialResidualRepair().propose(
        predicted,
        residual_report,
        runtime_context={},
    )
    object_report = ObjectResidualRepair().propose(
        predicted,
        residual_report,
        runtime_context={},
    )

    report = CounterfactualRepairEngine().repair(
        predicted,
        target,
        [residual_report, spatial_report, object_report],
    )

    assert report["repair_accepted"] is True
    assert report["before_difference_count"] == 1
    assert report["after_difference_count"] == 0
    assert report["cells_corrected"] == 1
    assert report["after_accuracy"] == 1.0


def test_evaluation_stage_repairs_near_perfect_prediction_before_success():
    predicted = np.zeros((5, 5), dtype=int)
    target = predicted.copy()
    target[2, 2] = 8

    result = evaluation_stage({
        "predicted_output": predicted,
        "output_grid": target,
        "cognitive_cycle": {"task_id": "localized_residual"},
        "active_concepts": ["inside_outside"],
    })

    assert result["pre_repair_evaluation_result"]["difference_count"] == 1
    assert result["FINAL_REPAIR_REPORT"]["repair_accepted"] is True
    assert result["evaluation_result"]["difference_count"] == 0
    assert result["evaluation_result"]["exact_success"] is True
    assert result["success_state"] in {"SUCCESS", "EXACT_SUCCESS"}
    assert np.array_equal(result["predicted_output"], target)


def test_high_value_partial_residual_starts_repair_attempts():
    predicted = np.zeros((5, 7), dtype=int)
    target = predicted.copy()
    target[0, 0] = 8
    target[0, 1] = 8

    result = evaluation_stage({
        "predicted_output": predicted,
        "output_grid": target,
        "cognitive_cycle": {"task_id": "high_value_two_cell_residual"},
        "active_concepts": ["containment", "relative_position"],
    })

    assert result["pre_repair_evaluation_result"]["accuracy"] == 0.9429
    assert result["pre_repair_evaluation_result"]["difference_count"] == 2
    assert result["pre_repair_evaluation_result"][
        "high_value_partial_success"
    ] is True
    assert result["LOCALIZED_REPAIR_REPORT"]["activated"] is True
    assert result["residual_reasoning_report"]["repair_activation_reason"] == (
        "high_value_partial_residual"
    )
    assert result["FINAL_REPAIR_REPORT"]["repair_attempts"] > 0
    assert result["FINAL_REPAIR_REPORT"]["localized_repairs"] > 0
    assert result["FINAL_REPAIR_REPORT"]["counterfactual_repairs"] > 0


def test_recoverable_four_cell_residual_starts_repair_attempts():
    predicted = np.zeros((5, 5), dtype=int)
    target = predicted.copy()
    target[1, 1] = 7
    target[1, 2] = 7
    target[2, 1] = 7
    target[2, 2] = 7

    result = evaluation_stage({
        "predicted_output": predicted,
        "output_grid": target,
        "cognitive_cycle": {"task_id": "four_cell_localized_residual"},
        "active_concepts": ["artifact_filtering", "symbolic_remapping"],
    })

    assert result["pre_repair_evaluation_result"]["accuracy"] == 0.84
    assert result["pre_repair_evaluation_result"]["difference_count"] == 4
    assert result["residual_reasoning_report"]["repair_mode"] == (
        "LOCALIZED_REPAIR_MODE"
    )
    assert result["FINAL_REPAIR_REPORT"]["repair_attempts"] >= 4
    assert result["FINAL_REPAIR_REPORT"]["repair_accepted"] is True
    assert result["evaluation_result"]["difference_count"] == 0
