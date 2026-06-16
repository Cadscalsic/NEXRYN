from runtime.spatial import TransformationLocalizationEngine
from runtime.transforms.primitive_executor import PrimitiveExecutor
from runtime.world.world_model import WorldModelEngine
from core.scene_graph import GraphReasoner
from runtime.execution.execution_integrity_guard import ExecutionIntegrityGuard
from runtime.execution.world_model_gate import WorldModelGate
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
