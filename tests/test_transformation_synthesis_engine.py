from runtime.memory.transformation_memory import TransformationMemory
from runtime.reasoning.transformation_synthesis_engine import (
    TransformationSynthesisEngine,
)
from runtime.transforms.primitive_executor import PrimitiveExecutor


def test_synthesizes_translation_from_centroid_shift():
    report = TransformationSynthesisEngine(
        memory=TransformationMemory(),
        executor=PrimitiveExecutor(),
    ).synthesize(
        input_grid=[
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ],
        output_grid=[
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 1],
        ],
        detected_concepts=[
            "relative_position",
            "spatial_relation",
            "transformation_sequence",
        ],
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]
    selected = synthesis["selected_program"]["steps"][0]

    assert selected["operation"] == "translate"
    assert selected["parameters"]["delta_row"] == 2
    assert selected["parameters"]["delta_col"] == 2
    assert synthesis["transformation_accuracy"] == 1.0


def test_synthesizes_recolor_mapping_from_symbolic_remapping():
    report = TransformationSynthesisEngine(
        memory=TransformationMemory(),
        executor=PrimitiveExecutor(),
    ).synthesize(
        input_grid=[
            [1, 2, 3],
            [0, 0, 0],
        ],
        output_grid=[
            [5, 7, 8],
            [0, 0, 0],
        ],
        detected_concepts=[
            "symbolic_remapping",
            "color_mapping",
        ],
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]
    selected = synthesis["selected_program"]["steps"][0]

    assert selected["operation"] == "recolor"
    assert selected["parameters"]["mapping"] == {
        "1": 5,
        "2": 7,
        "3": 8,
    }
    assert synthesis["transformation_accuracy"] == 1.0


def test_synthesizes_path_construction_from_route_completion():
    report = TransformationSynthesisEngine(
        memory=TransformationMemory(),
        executor=PrimitiveExecutor(),
    ).synthesize(
        input_grid=[
            [1, 0, 0, 1],
        ],
        output_grid=[
            [1, 1, 1, 1],
        ],
        detected_concepts=[
            "path_finding",
            "route_completion",
        ],
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]
    operations = [
        step["operation"]
        for candidate in report["ranked_candidates"]
        for step in candidate["program"]["steps"]
    ]

    assert "construct_path" in operations
    assert synthesis["candidate_count"] > 0


def test_transformation_memory_reuses_successful_programs():
    memory = TransformationMemory()
    memory.remember(
        {
            "steps": [
                {
                    "operation": "translate",
                    "parameters": {
                        "delta_row": 1,
                        "delta_col": 0,
                        "translation": [1, 0],
                    },
                }
            ],
            "step_count": 1,
        },
        concepts=["relative_position"],
        accuracy=1.0,
        success=True,
    )

    report = TransformationSynthesisEngine(
        memory=memory,
        executor=PrimitiveExecutor(),
    ).synthesize(
        detected_concepts=["relative_position"],
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]

    assert synthesis["program_reuse"] is True
    assert synthesis["selected_program"]["steps"][0]["operation"] == "translate"
