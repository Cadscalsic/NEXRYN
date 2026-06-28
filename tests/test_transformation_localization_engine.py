from runtime.spatial import TransformationLocalizationEngine
from runtime.transforms.primitive_executor import PrimitiveExecutor
from runtime.world.world_model import WorldModelEngine
from core.scene_graph import GraphReasoner
from runtime.execution.execution_integrity_guard import ExecutionIntegrityGuard
from runtime.execution.world_model_gate import WorldModelGate
from runtime.transformation_localization import ExecutionReadinessCalibrator
from runtime.transformation_localization import localization_controller
from runtime.kernel.cognitive_blackboard import CognitiveBlackboard
from runtime.planning.planning_engine import PlanningEngine


def test_transformation_localization_engine_repairs_duplicate_offset():
    report = TransformationLocalizationEngine().localize_from_grids(
        [[1, 0, 0, 0, 0]],
        [[1, 0, 0, 1, 0]],
        operation="duplicate_object",
        position_rule={
            "operation": "duplicate_object",
            "source_object": "obj_1",
            "placement_vector": {"delta_row": 0, "delta_col": 2},
            "confidence": 0.72,
        },
    )

    assert report["anchor_object"] == "obj_1"
    assert report["relative_offset"] == [0, 3]
    assert report["placement_confidence"] >= 0.95
    assert report["localization_ready"] is True
    assert report["empty_region_compatible"] is True
    assert report["topology_preserved"] is True


def test_duplicate_object_uses_localized_relative_offset():
    output = PrimitiveExecutor().duplicate_object(
        [[1, 0, 0, 0, 0]],
        {
            "anchor_object": "obj_1",
            "relative_offset": [0, 3],
            "localization_ready": True,
        },
    )

    assert output.tolist() == [[1, 0, 0, 1, 0]]


def test_world_model_anticipation_localizes_before_acceptance():
    report = WorldModelEngine().anticipate_program(
        input_grid=[[1, 0, 0, 0, 0]],
        target_grid=[[1, 0, 0, 1, 0]],
        synthesized_program={
            "steps": [
                {
                    "operation": "duplicate_object",
                    "parameters": {},
                }
            ]
        },
    )

    localization = report["transformation_localization"]
    prediction = report["prediction_report"]

    assert localization["localization_ready"] is True
    assert localization["localization_reports"][0]["relative_offset"] == [0, 3]
    assert prediction["prediction_accuracy"] == 1.0
    assert report["residual_difference_count"] == 0
    assert report["execution_accepted"] is True


def test_localization_controller_calibrates_zero_confidence_with_fallback():
    calibrated = localization_controller.calibrate(
        {
            "localization_ready": False,
            "localization_confidence": 0.0,
            "localized_step_count": 0,
            "localization_reports": [{
                "anchor_object": "obj_1",
                "relative_offset": [1, 0],
                "topology_preserved": True,
                "spatial_constraints": [{
                    "type": "causal_dependency",
                    "confidence": 1.0,
                }],
                "causal_evidence": {"operation": "translate_down"},
            }],
        },
        synthesized_program={
            "step_count": 1,
            "steps": [{
                "operation": "translate_down",
                "parameters": {"delta_row": 1, "delta_col": 0},
            }],
        },
        hypothesis={
            "primitive": "translate_down",
            "confidence": 0.97,
            "semantic_support": 0.95,
            "causal_support": 0.95,
            "geometric_grounding": {"confidence": 0.90},
        },
        prediction_accuracy=0.95,
    )

    assert calibrated["localization_confidence"] >= 0.70
    assert calibrated["fallback_used"] in {
        "object_level_fallback",
        "global_translation_fallback",
    }
    assert calibrated["execution_ready"] is True
    assert calibrated["LOCALIZATION_REPORT"]["execution_authorized"] is True


def test_medium_localization_confidence_allows_probable_sandbox_execution():
    readiness = ExecutionReadinessCalibrator().evaluate(
        hypothesis_confidence=0.92,
        localization_confidence=0.748,
        prediction_accuracy=0.91,
        identity_confidence=0.95,
        dependency_support=0.94,
        arbitration_score=0.91,
        winning_hypothesis_stable=True,
        dependency_evidence_exists=True,
    )

    assert readiness["localization_confidence_band"] == "MEDIUM"
    assert readiness["readiness_class"] == "READINESS_HIGH"
    assert readiness["execution_governance_state"] == "EXECUTION_PROBABLE"
    assert readiness["execution_ready"] is True


def test_residual_guided_grounding_recovers_empty_target_objects_for_probation():
    calibrated = localization_controller.calibrate(
        {
            "localization_ready": False,
            "localization_confidence": 0.1675,
            "localized_step_count": 0,
            "target_objects": [],
            "localization_reports": [],
        },
        synthesized_program={
            "step_count": 1,
            "steps": [{
                "operation": "replace_color",
                "parameters": {},
            }],
        },
        hypothesis={
            "primitive": "replace_color",
            "confidence": 0.92,
        },
        prediction_accuracy=0.92,
        runtime_context={
            "prediction_accuracy": 0.92,
            "residual_locations": [(1, 2), (2, 2)],
            "WORLD GOVERNANCE INTROSPECTION REPORT": {
                "decision": "ALLOW_SANDBOX",
                "trust_score": 1.0,
                "risk_score": 0.0,
                "learning_credit_authorized": True,
            },
        },
    )

    report = calibrated["LOCALIZATION_REPORT"]
    readiness = calibrated["EXECUTION READINESS REPORT"]

    assert calibrated["target_objects"]
    assert report["object_detection"] > 0.0
    assert report["transformation_detection"] > 0.0
    assert report["candidate_object_regions"]
    assert report["localization_hints"]
    assert readiness["readiness_class"] == "EXECUTION_PROBATION"
    assert calibrated["execution_probation"] is True
    assert report["sandbox_execution_authorized"] is True


def test_color_mapping_localizes_to_object_level_executable_rule():
    input_grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 2, 0, 0],
        [0, 2, 1, 0, 0],
        [0, 0, 0, 3, 0],
        [0, 0, 0, 0, 0],
    ]
    output_grid = [
        [0, 0, 0, 0, 0],
        [0, 4, 7, 0, 0],
        [0, 7, 4, 0, 0],
        [0, 0, 0, 8, 0],
        [0, 0, 0, 0, 0],
    ]

    report = TransformationLocalizationEngine().localize_program(
        input_grid,
        output_grid,
        {
            "steps": [
                {
                    "operation": "symbolic_remapping",
                    "parameters": {},
                }
            ]
        },
    )

    localized_program = report["localized_program"]
    rule = report["localization_reports"][0]["localized_rules"][0]
    execution = PrimitiveExecutor().run_execution(
        input_grid=input_grid,
        primitives=[
            {
                "primitive": localized_program["steps"][0]["operation"],
                "parameters": localized_program["steps"][0]["parameters"],
            }
        ],
    )

    assert report["localization_ready"] is True
    assert report["localized_step_count"] == 1
    assert rule == {
        "mapping_type": "object_color_mapping",
        "localization_type": "color_mapping",
        "mapping": {"1": 4, "2": 7, "3": 8},
        "confidence": 0.95,
    }
    assert execution["output_grid"].tolist() == output_grid


def test_world_model_authorizes_localized_color_program():
    input_grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 2, 0, 0],
        [0, 2, 1, 0, 0],
        [0, 0, 0, 3, 0],
        [0, 0, 0, 0, 0],
    ]
    output_grid = [
        [0, 0, 0, 0, 0],
        [0, 4, 7, 0, 0],
        [0, 7, 4, 0, 0],
        [0, 0, 0, 8, 0],
        [0, 0, 0, 0, 0],
    ]

    anticipation = WorldModelEngine().anticipate_program(
        input_grid=input_grid,
        target_grid=output_grid,
        synthesized_program={
            "steps": [
                {
                    "operation": "symbolic_remapping",
                    "parameters": {},
                }
            ]
        },
    )
    gate_report = WorldModelGate().evaluate(anticipation)

    assert anticipation["transformation_localization"]["localization_ready"] is True
    assert anticipation["transformation_localization"]["localized_step_count"] == 1
    assert anticipation["prediction_report"]["prediction_accuracy"] > 0.95
    assert gate_report["execution_authorized"] is True
    assert gate_report["execution_aborted"] is False


def test_cognitive_blackboard_synchronizes_localization_to_execution():
    input_grid = [
        [0, 1, 0],
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]
    target_grid = [
        [0, 1, 0],
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]

    blackboard = CognitiveBlackboard()
    graph_reasoning = GraphReasoner().reason_about_placement(
        input_grid,
        target_grid,
        operation="duplicate_object",
    )
    blackboard.synchronize_from_graph_reasoning(graph_reasoning)

    synthesized_program = {
        "step_count": 1,
        "steps": [
            {
                "operation": "duplicate_object",
                "parameters": {"delta": 1},
            }
        ],
    }
    anticipation = WorldModelEngine().anticipate_program(
        input_grid=input_grid,
        target_grid=target_grid,
        synthesized_program=synthesized_program,
    )
    blackboard.synchronize_from_world_model(anticipation)
    localized_program = blackboard.synthesized_program
    execution_plan = blackboard.synchronize_execution_plan(
        PlanningEngine().build_plan(localized_program)
    )

    planned_primitives = ExecutionIntegrityGuard().primitives_from_plan(
        execution_plan
    )
    gate_report = WorldModelGate().evaluate(anticipation)
    execution_result = PrimitiveExecutor().run_execution(
        input_grid=input_grid,
        primitives=planned_primitives,
    )

    first_step = localized_program["steps"][0]["parameters"]

    assert graph_reasoning["localized_prediction_ready"] is True
    assert execution_plan["localization_ready"] is True
    assert execution_plan["localized_step_count"] == 1
    assert first_step["delta"] == 1
    assert first_step["delta_row"] == 2
    assert first_step["delta_col"] == 0
    assert first_step["anchor_object"] == "obj_1"
    assert first_step["placement_strategy"] == "vertical_down"
    assert gate_report["execution_authorized"] is True
    assert len(execution_result["execution_trace"]) == 1
    assert anticipation["prediction_report"]["prediction_accuracy"] >= 0.95
