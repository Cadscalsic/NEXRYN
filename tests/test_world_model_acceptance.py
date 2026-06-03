from runtime.world.acceptance_calibrator import (
    WorldModelAcceptanceCalibrator,
)
from runtime.world.world_model import WorldModelEngine


def test_world_model_acceptance_separates_search_candidate_from_execution():
    report = WorldModelAcceptanceCalibrator().evaluate(
        {
            "prediction_accuracy": 0.84,
            "success": False,
        },
        {
            "simulation_uncertainty": 0.18,
        },
    )

    assert report["search_candidate_accepted"] is True
    assert report["execution_accepted"] is False
    assert report["accepted"] is False
    assert report["acceptance_state"] == "SEARCH_CANDIDATE_ONLY"


def test_world_model_acceptance_requires_prediction_success():
    report = WorldModelAcceptanceCalibrator().evaluate(
        {
            "prediction_accuracy": 1.0,
            "success": True,
        },
        {
            "simulation_uncertainty": 0.15,
        },
    )

    assert report["accepted"] is True
    assert report["acceptance_state"] == "EXECUTION_ACCEPTED"


def test_world_model_acceptance_routes_one_cell_partial_success_to_sandbox():
    report = WorldModelAcceptanceCalibrator().evaluate(
        {
            "prediction_accuracy": 0.96,
            "correct_cells": 24,
            "total_cells": 25,
            "success": False,
            "partial_success": True,
        },
        {
            "simulation_uncertainty": 0.166,
        },
    )

    assert report["execution_accepted"] is False
    assert report["sandbox_execution_accepted"] is True
    assert report["acceptance_state"] == "SOFT_EXECUTION_ZONE"


def test_world_model_acceptance_routes_ninety_two_percent_one_cell_to_sandbox():
    report = WorldModelAcceptanceCalibrator().evaluate(
        {
            "prediction_accuracy": 0.92,
            "correct_cells": 24,
            "total_cells": 25,
            "success": False,
            "partial_success": True,
        },
        {
            "simulation_uncertainty": 0.12,
        },
    )

    assert report["execution_accepted"] is False
    assert report["sandbox_execution_accepted"] is True
    assert report["acceptance_state"] == "SOFT_EXECUTION_ZONE"


def test_world_model_acceptance_rejects_multi_cell_partial_success_from_sandbox():
    report = WorldModelAcceptanceCalibrator().evaluate(
        {
            "prediction_accuracy": 0.98,
            "correct_cells": 98,
            "total_cells": 100,
            "success": False,
            "partial_success": True,
        },
        {
            "simulation_uncertainty": 0.158,
        },
    )

    assert report["sandbox_execution_accepted"] is False
    assert report["acceptance_state"] == "SEARCH_CANDIDATE_ONLY"


def test_world_model_acceptance_recognizes_success_state_partial_success():
    report = WorldModelAcceptanceCalibrator().evaluate(
        {
            "prediction_accuracy": 0.92,
            "correct_cells": 24,
            "total_cells": 25,
            "success": False,
            "success_state": "PARTIAL_SUCCESS",
        },
        {
            "simulation_uncertainty": 0.12,
        },
    )

    assert report["execution_accepted"] is False
    assert report["sandbox_execution_accepted"] is True
    assert report["acceptance_state"] == "SOFT_EXECUTION_ZONE"


def test_world_model_confidence_is_calibrated_to_observed_accuracy():
    report = WorldModelEngine().estimate_simulation_uncertainty(
        synthesized_program={"steps": [{"operation": "translate_right"}]},
        simulation_trace=[{"operation": "translate_right"}],
        prediction_report={"prediction_accuracy": 0.92},
    )

    assert report["uncalibrated_prediction_confidence"] == 0.818
    assert report["prediction_confidence"] == 0.818
    assert report["confidence_calibration_gap"] == 0.0


def test_world_model_confidence_does_not_exceed_observed_accuracy():
    report = WorldModelEngine().estimate_simulation_uncertainty(
        synthesized_program={"steps": [
            {"operation": "preserve_size"},
            {"operation": "translate_right"},
        ]},
        simulation_trace=[
            {"operation": "preserve_size"},
            {"operation": "translate_right"},
        ],
        prediction_report={"prediction_accuracy": 0.92},
    )

    assert report["uncalibrated_prediction_confidence"] == 0.968
    assert report["prediction_confidence"] == 0.92
    assert report["confidence_calibration_gap"] == 0.048


def test_world_model_reports_partial_success_without_exact_acceptance():
    import numpy as np

    predicted = np.zeros((5, 5), dtype=int)
    target = np.zeros((5, 5), dtype=int)
    target[0, 0] = 1

    report = WorldModelEngine().evaluate_prediction(predicted, target)

    assert report["prediction_accuracy"] == 0.96
    assert report["success"] is False
    assert report["partial_success"] is True
    assert report["success_state"] == "PARTIAL_SUCCESS"
