from runtime.reasoning.mechanistic_reasoning_engine import MechanisticReasoningEngine
from runtime.reasoning.transformation_synthesis_engine import TransformationSynthesisEngine
from runtime.memory.transformation_memory import TransformationMemory
from runtime.transforms.primitive_executor import PrimitiveExecutor


def test_gravity_concepts_build_executable_mechanism_graph():
    report = MechanisticReasoningEngine().reason(
        concepts=[
            "gravity",
            "falling",
            "support",
            "collision",
            "rest_state",
            "downward_motion",
        ],
        input_grid=[
            [0],
            [2],
            [0],
        ],
        output_grid=[
            [0],
            [0],
            [2],
        ],
    )

    graph = report["mechanism_graphs"][0]

    assert report["MECHANISTIC_REASONING_REPORT"] is True
    assert graph["family"] == "gravity"
    assert "downward_trajectory_simulation" in graph["candidate_mechanisms"]
    assert "translate" in graph["candidate_operations"]
    assert graph["causal_validation"]["validated"] is True
    assert report["unknown_sequence_resolved"] is True


def test_rotation_mechanism_infers_angle_center_and_preservation():
    report = MechanisticReasoningEngine().reason(
        concepts=["rotation_reflection", "rotation", "orientation_change"],
        input_grid=[
            [1, 0],
            [2, 0],
        ],
        output_grid=[
            [0, 0],
            [1, 2],
        ],
    )

    graph = report["mechanism_graphs"][0]
    angle = [
        node for node in graph["nodes"]
        if node["mechanism"] == "rotation_angle_inference"
    ][0]

    assert graph["family"] == "rotation"
    assert angle["evidence"]["degrees"] == 90
    assert "grid_center" in graph["reference_frames"]
    assert "rotate" in graph["candidate_operations"]


def test_counting_mechanism_extracts_cardinality_and_quantity_delta():
    report = MechanisticReasoningEngine().reason(
        concepts=[
            "object_counting",
            "cardinality",
            "quantity_transformation",
            "set_reasoning",
        ],
        input_grid=[
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 2],
        ],
        output_grid=[
            [1, 0, 3],
            [0, 0, 0],
            [0, 0, 2],
        ],
    )

    graph = report["mechanism_graphs"][0]
    cardinality = [
        node for node in graph["nodes"]
        if node["mechanism"] == "cardinality_extraction"
    ][0]
    quantity = [
        node for node in graph["nodes"]
        if node["mechanism"] == "quantity_transformation"
    ][0]

    assert graph["family"] == "object_counting"
    assert cardinality["evidence"]["input_object_count"] == 2
    assert cardinality["evidence"]["output_object_count"] == 3
    assert quantity["evidence"]["count_delta"] == 1
    assert graph["candidate_operations"] == ["duplicate"]


def test_transformation_synthesis_surfaces_mechanistic_report_for_sequence():
    report = TransformationSynthesisEngine(
        memory=TransformationMemory(),
        executor=PrimitiveExecutor(),
    ).synthesize(
        input_grid=[
            [0],
            [2],
            [0],
        ],
        output_grid=[
            [0],
            [0],
            [2],
        ],
        detected_concepts=[
            "gravity",
            "falling",
            "transformation_sequence",
        ],
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]
    mechanism = synthesis["mechanistic_reasoning_report"]
    selected = synthesis["selected_program"]["steps"][0]

    assert mechanism["mechanism_families"] == ["gravity"]
    assert mechanism["unknown_sequence_resolved"] is True
    assert selected["operation"] == "translate"
    assert selected["parameters"]["mechanism_family"] == "gravity"
    assert synthesis["transformation_accuracy"] == 1.0
