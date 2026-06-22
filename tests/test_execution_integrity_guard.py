import numpy as np

from runtime.execution.execution_integrity_guard import (
    ExecutionIntegrityGuard,
)
from runtime.execution.world_model_gate import WorldModelGate
from runtime.stages.transformation import transformation_stage


def execution_plan(operation="translate_down"):
    return {
        "node_count": 1,
        "nodes": [{
            "execution_index": 0,
            "operation": operation,
            "parameters": {"translation": (1, 1)},
        }],
    }


def test_execution_integrity_guard_detects_unauthorized_operation():
    report = ExecutionIntegrityGuard().evaluate(
        execution_plan(),
        [
            {"primitive": "translate_down", "status": "completed"},
            {"primitive": "mirror_object", "status": "completed"},
        ],
    )

    assert report["integrity_preserved"] is False
    assert report["execution_drift_detected"] is True
    assert report["unauthorized_ops"] == ["mirror_object"]


def test_world_model_gate_requires_explicit_execution_acceptance():
    rejected = WorldModelGate().evaluate({
        "execution_accepted": False,
        "acceptance_state": "SEARCH_CANDIDATE_ONLY",
    })
    accepted = WorldModelGate().evaluate({
        "execution_accepted": True,
        "acceptance_state": "EXECUTION_ACCEPTED",
    })

    assert rejected["execution_authorized"] is False
    assert rejected["execution_aborted"] is True
    assert accepted["execution_authorized"] is True


def test_world_model_gate_routes_soft_execution_to_isolated_sandbox():
    report = WorldModelGate().evaluate({
        "execution_accepted": False,
        "sandbox_execution_accepted": True,
        "acceptance_state": "SOFT_EXECUTION_ZONE",
    })

    assert report["execution_authorized"] is False
    assert report["sandbox_execution_authorized"] is True
    assert report["gate_state"] == "EXECUTION_ROUTED_TO_SANDBOX"


def localized_color_anticipation(operation="replace_color"):
    return {
        "execution_accepted": False,
        "sandbox_execution_accepted": True,
        "acceptance_state": "SOFT_EXECUTION_ZONE",
        "residual_difference_count": 1,
        "prediction_report": {
            "prediction_accuracy": 0.9796,
            "partial_success": True,
            "success_state": "PARTIAL_SUCCESS",
        },
        "transformation_localization": {
            "localization_ready": True,
            "localization_confidence": 0.9775,
            "localized_step_count": 1,
            "localized_program": {
                "step_count": 1,
                "steps": [{
                    "operation": operation,
                    "parameters": {
                        "localization_type": "color_mapping",
                        "mapping": {"2": 8},
                    },
                }],
            },
            "localization_reports": [{
                "localization_ready": True,
                "localization_confidence": 0.9775,
                "localized_rules": [{
                    "mapping_type": "object_color_mapping",
                    "localization_type": "color_mapping",
                    "mapping": {"2": 8},
                    "confidence": 0.95,
                }],
                "object_matches": [{
                    "identity_confidence": 1.0,
                    "topology_preserved": True,
                    "shape_similarity": 1.0,
                }],
            }],
        },
        "localized_synthesized_program": {
            "step_count": 1,
            "steps": [{
                "operation": operation,
                "parameters": {
                    "localization_type": "color_mapping",
                    "mapping": {"2": 8},
                },
            }],
        },
        "execution_integrity_report": {
            "integrity_preserved": True,
        },
    }


def test_world_model_gate_authorizes_localization_confirmed_color_execution():
    report = WorldModelGate().evaluate(localized_color_anticipation())

    assert report["execution_authorized"] is True
    assert report["execution_aborted"] is False
    assert report["sandbox_execution_authorized"] is False
    assert report["gate_state"] == "LOCALIZATION_CONFIRMED_EXECUTION"
    assert report["acceptance_state"] == "EXECUTION_ACCEPTED"
    assert report["localization_confirmed"] is True


def test_world_model_gate_authorizes_ready_spatial_localization():
    report = WorldModelGate().evaluate(
        localized_color_anticipation(operation="duplicate_object")
    )

    assert report["execution_authorized"] is True
    assert report["execution_aborted"] is False
    assert report["gate_state"] == "LOCALIZATION_CONFIRMED_EXECUTION"
    assert report["localization_confirmed"] is True


def test_world_model_gate_requires_integrity_for_localization_execution():
    anticipation = localized_color_anticipation()
    anticipation["execution_integrity_report"] = {
        "integrity_preserved": False,
    }

    report = WorldModelGate().evaluate(anticipation)

    assert report["execution_authorized"] is False
    assert report["gate_state"] == "EXECUTION_ROUTED_TO_SANDBOX"
    assert report["localization_confirmed"] is False


def test_world_model_gate_authorizes_high_confidence_fallback_localization():
    report = WorldModelGate().evaluate({
        "execution_accepted": False,
        "acceptance_state": "SEARCH_CANDIDATE_ONLY",
        "residual_difference_count": 0,
        "winner_hypothesis": {
            "primitive": "translate_down",
            "confidence": 0.97,
            "semantic_support": 0.95,
            "causal_support": 0.95,
            "geometric_grounding": {"confidence": 0.90},
        },
        "prediction_report": {
            "prediction_accuracy": 0.95,
        },
        "transformation_localization": {
            "localization_ready": False,
            "localization_confidence": 0.0,
            "localized_step_count": 0,
            "shape_similarity": 0.0,
            "topology_preserved": True,
            "localization_reports": [{
                "anchor_object": "obj_1",
                "relative_offset": [1, 0],
                "placement_confidence": 0.0,
                "topology_preserved": True,
                "spatial_constraints": [{
                    "type": "causal_dependency",
                    "confidence": 1.0,
                }],
                "causal_evidence": {
                    "operation": "translate_down",
                },
            }],
            "localized_program": {
                "step_count": 1,
                "steps": [{
                    "operation": "translate_down",
                    "parameters": {"delta_row": 1, "delta_col": 0},
                }],
            },
        },
        "localized_synthesized_program": {
            "step_count": 1,
            "steps": [{
                "operation": "translate_down",
                "parameters": {"delta_row": 1, "delta_col": 0},
            }],
        },
        "execution_integrity_report": {
            "integrity_preserved": True,
        },
    })

    assert report["execution_authorized"] is True
    assert report["execution_aborted"] is False
    assert report["localization_execution_ready"] is True
    assert report["execution_readiness"] >= 0.75
    assert report["LOCALIZATION_REPORT"]["fallback_used"] in {
        "object_level_fallback",
        "global_translation_fallback",
    }


def test_transformation_executes_only_planned_operations():
    input_grid = np.array([
        [0, 1, 0],
        [0, 0, 0],
        [0, 0, 0],
    ])
    context = transformation_stage({
        "input_grid": input_grid,
        "output_grid": np.array([
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]),
        "synthesized_program": {
            "steps": [{
                "operation": "translate_down",
                "parameters": {"translation": (1, 1)},
            }],
        },
        "execution_plan": execution_plan(),
        "ranked_primitives": [
            {"primitive": "translate_down"},
            {"primitive": "mirror_object"},
        ],
        "world_model_anticipation": {
            "execution_accepted": True,
            "acceptance_state": "EXECUTION_ACCEPTED",
        },
    })

    trace = context["transformation_execution_trace"]
    assert [event["primitive"] for event in trace] == ["translate_down"]
    assert context["execution_integrity_report"]["integrity_preserved"] is True


def test_transformation_aborts_when_world_model_rejects_plan():
    input_grid = np.array([
        [0, 1, 0],
        [0, 0, 0],
        [0, 0, 0],
    ])
    context = transformation_stage({
        "input_grid": input_grid,
        "output_grid": np.array([
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]),
        "synthesized_program": {
            "steps": [{
                "operation": "translate_down",
                "parameters": {"translation": (1, 1)},
            }],
        },
        "execution_plan": execution_plan(),
        "ranked_primitives": [
            {"primitive": "translate_down"},
            {"primitive": "mirror_object"},
        ],
        "world_model_anticipation": {
            "execution_accepted": False,
            "acceptance_state": "SEARCH_CANDIDATE_ONLY",
        },
    })

    assert context["transformation_execution_trace"] == []
    assert context["transformation_report"]["execution_aborted"] is True
    assert np.array_equal(context["predicted_output"], input_grid)


def test_transformation_evaluates_soft_execution_inside_sandbox():
    input_grid = np.array([
        [0, 1, 0],
        [0, 0, 0],
        [0, 0, 0],
    ])
    context = transformation_stage({
        "input_grid": input_grid,
        "output_grid": np.array([
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]),
        "synthesized_program": {
            "steps": [{
                "operation": "translate_down",
                "parameters": {"translation": (1, 1)},
            }],
        },
        "execution_plan": execution_plan(),
        "world_model_anticipation": {
            "execution_accepted": False,
            "sandbox_execution_accepted": True,
            "acceptance_state": "SOFT_EXECUTION_ZONE",
        },
    })

    sandbox = context["sandbox_execution_result"]
    assert context["transformation_execution_trace"] == []
    assert context["transformation_report"]["execution_aborted"] is True
    assert sandbox["execution_mode"] == "isolated_world_model_sandbox"
    assert sandbox["persistent_effects_forbidden"] is True
    assert np.array_equal(context["predicted_output"], sandbox["output_grid"])
