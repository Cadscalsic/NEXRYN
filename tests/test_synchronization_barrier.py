import pytest

from runtime.kernel.cognitive_blackboard import (
    CognitiveBlackboard,
    StateSynchronizationFailure,
)


def test_blackboard_does_not_validate_transient_partial_state():
    blackboard = CognitiveBlackboard()

    with blackboard.transaction():
        blackboard.synchronize_from_graph_reasoning({
            "localized_prediction_ready": True,
            "placement_rules": [{
                "confidence": 1.0,
                "placement_vector": {
                    "delta_row": 2,
                    "delta_col": 0,
                },
            }],
        })
        blackboard.assert_synchronized()

    assert blackboard.barrier_report()["missing_stages"] == [
        "localization_engine",
        "program_synthesizer",
        "execution_plan_builder",
    ]


def test_blackboard_asserts_after_atomic_stage_commit():
    blackboard = CognitiveBlackboard()

    with blackboard.transaction():
        blackboard.synchronize_from_graph_reasoning({
            "localized_prediction_ready": True,
            "placement_rules": [{
                "confidence": 1.0,
                "placement_vector": {
                    "delta_row": 2,
                    "delta_col": 0,
                },
            }],
        })
        blackboard.synchronize_from_world_model({
            "transformation_localization": {
                "localization_ready": False,
                "localization_reports": [],
            },
            "localized_synthesized_program": {
                "steps": [{
                    "operation": "duplicate_object",
                    "parameters": {
                        "delta_row": 2,
                        "delta_col": 0,
                    },
                }],
            },
            "prediction_report": {
                "prediction_accuracy": 1.0,
            },
            "execution_accepted": True,
        })
        plan = blackboard.synchronize_execution_plan({
            "nodes": [{
                "operation": "duplicate_object",
                "parameters": {},
            }],
        })

    blackboard.assert_synchronized()

    assert blackboard.barrier_report()[
        "ready_for_synchronization_assertions"
    ] is True
    assert plan["localization_ready"] is True
    assert blackboard.execution_plan["localized_step_count"] == 1


def test_committed_complete_divergence_still_fails():
    blackboard = CognitiveBlackboard()

    with blackboard.transaction():
        blackboard.synchronize_from_graph_reasoning({
            "localized_prediction_ready": True,
            "placement_rules": [{
                "confidence": 1.0,
            }],
        })
        blackboard.synchronize_from_world_model({
            "transformation_localization": {
                "localization_ready": False,
            },
            "localized_synthesized_program": {
                "steps": [],
            },
        })
        blackboard.synchronize_execution_plan({
            "nodes": [],
        })

    with pytest.raises(
        StateSynchronizationFailure,
        match="localized_prediction_ready diverged from localization_ready",
    ):
        blackboard.assert_synchronized()
