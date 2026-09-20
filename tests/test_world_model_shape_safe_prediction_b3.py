import numpy as np

from runtime.engines.program_synthesis import ProgramSynthesisEngine
from runtime.reasoning.hypothesis_arbitration_engine import (
    HypothesisArbitrationEngine,
)
from runtime.world.world_model import WorldModelEngine


def test_world_model_shape_mismatch_returns_fail_closed_diagnostic_15_by_7():
    report = WorldModelEngine().evaluate_prediction(
        np.zeros((15, 15), dtype=int),
        np.zeros((15, 7), dtype=int),
    )

    assert report["success"] is False
    assert report["exact_success"] is False
    assert report["partial_success"] is False
    assert report["prediction_accuracy"] == 0.0
    assert report["correct_cells"] == 0
    assert report["total_cells"] == 105
    assert report["comparable"] is False
    assert report["failure_reason"] == "SHAPE_MISMATCH"
    assert report["predicted_shape"] == [15, 15]
    assert report["target_shape"] == [15, 7]


def test_world_model_shape_mismatch_returns_fail_closed_diagnostic_19_by_7():
    report = WorldModelEngine().evaluate_prediction(
        np.zeros((19, 19), dtype=int),
        np.zeros((19, 7), dtype=int),
    )

    assert report["success"] is False
    assert report["exact_success"] is False
    assert report["prediction_accuracy"] == 0.0
    assert report["comparable"] is False
    assert report["failure_reason"] == "SHAPE_MISMATCH"
    assert report["predicted_shape"] == [19, 19]
    assert report["target_shape"] == [19, 7]


def test_world_model_same_shape_prediction_contract_remains_unchanged():
    report = WorldModelEngine().evaluate_prediction(
        np.array([[1, 2], [3, 4]]),
        np.array([[1, 0], [3, 4]]),
    )

    assert report["success"] is False
    assert report["exact_success"] is False
    assert report["prediction_accuracy"] == 0.75
    assert report["correct_cells"] == 3
    assert report["total_cells"] == 4
    assert "comparable" not in report
    assert "failure_reason" not in report


def test_arbitration_shape_changing_train_pair_does_not_raise_broadcast_error():
    report = HypothesisArbitrationEngine().arbitrate_execution_candidates(
        hypotheses=[
            {
                "type": "color_transformation",
                "primitive": "replace_color",
                "parameters": {"source": [1], "target": [2]},
                "confidence": 0.8,
                "search_final_score": 0.8,
                "explanatory_power": 0.8,
                "residual_reduction": 0.8,
                "transformation_salience": 0.8,
                "geometric_grounding": {"confidence": 0.8},
            }
        ],
        input_grid=np.zeros((15, 15), dtype=int),
        target_grid=np.zeros((15, 7), dtype=int),
        world_model_engine=WorldModelEngine(),
        program_synthesis_engine=ProgramSynthesisEngine(),
    )

    assert report["candidate_count"] == 1
    candidate = report["ranked_candidates"][0]
    prediction_report = candidate["anticipation"]["prediction_report"]
    assert prediction_report["failure_reason"] == "SHAPE_MISMATCH"
    assert prediction_report["prediction_accuracy"] == 0.0
    assert candidate["hypothesis"]["world_model_fit"] == 0.0
    assert candidate["anticipation"]["accepted"] is False
