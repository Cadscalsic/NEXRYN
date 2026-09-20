from runtime.memory.color_mapping_memory import ColorMappingMemory
from runtime.reasoning.color_mapping_engine import ColorMappingReasoningEngine
from runtime.reasoning.transformation_synthesis_engine import (
    TransformationSynthesisEngine,
)
from runtime.transforms.primitive_executor import PrimitiveExecutor


def test_color_mapping_engine_discovers_direct_mapping_program():
    report = ColorMappingReasoningEngine(
        memory=ColorMappingMemory(),
        executor=PrimitiveExecutor(),
    ).analyze(
        input_grid=[
            [1, 2, 3],
            [0, 0, 0],
        ],
        output_grid=[
            [5, 7, 8],
            [0, 0, 0],
        ],
    )

    color_report = report["COLOR_MAPPING_REPORT"]
    selected = color_report["selected_program"]["steps"][0]

    assert color_report["mapping_matrix"]["mapping"] == {
        "1": 5,
        "2": 7,
        "3": 8,
    }
    assert selected["operation"] == "recolor"
    assert selected["parameters"]["mapping"] == {
        "1": 5,
        "2": 7,
        "3": 8,
    }
    assert color_report["program_accuracy"] == 1.0
    assert color_report["mapping_confidence"] >= 0.9


def test_color_mapping_engine_supports_global_many_to_one_recolor():
    report = ColorMappingReasoningEngine(
        memory=ColorMappingMemory(),
        executor=PrimitiveExecutor(),
    ).analyze(
        input_grid=[
            [1, 2, 3],
        ],
        output_grid=[
            [9, 9, 9],
        ],
    )

    matrix = report["COLOR_MAPPING_REPORT"]["mapping_matrix"]

    assert matrix["mapping"] == {
        "1": 9,
        "2": 9,
        "3": 9,
    }
    assert matrix["mapping_type"] in {"direct", "many_to_one"}
    assert report["COLOR_MAPPING_REPORT"]["program_accuracy"] == 1.0


def test_color_mapping_engine_reports_object_specific_conditions():
    report = ColorMappingReasoningEngine(
        memory=ColorMappingMemory(),
        executor=PrimitiveExecutor(),
    ).analyze(
        input_grid=[
            [1, 0, 1],
        ],
        output_grid=[
            [5, 0, 8],
        ],
    )

    conditional_candidates = [
        candidate
        for candidate in report["candidate_mappings"]
        if candidate["mapping_matrix"]["conditional_mappings"]
    ]

    assert conditional_candidates
    assert {
        item["to"]
        for item in conditional_candidates[0]["mapping_matrix"]["conditional_mappings"]
    } == {5, 8}


def test_color_mapping_memory_reuses_successful_mapping():
    memory = ColorMappingMemory()
    matrix = {
        "mapping": {
            "1": 5,
        },
        "mapping_type": "direct",
        "scope": "global",
        "weighted_mappings": {
            "1": {
                "5": 1.0,
            }
        },
        "conditional_mappings": [],
        "object_color_relationships": [],
    }
    memory.remember(
        matrix,
        program={
            "steps": [
                {
                    "operation": "recolor",
                    "parameters": {
                        "mapping": {
                            "1": 5,
                        }
                    },
                }
            ],
            "step_count": 1,
        },
        accuracy=1.0,
        success=True,
    )

    report = ColorMappingReasoningEngine(
        memory=memory,
        executor=PrimitiveExecutor(),
    ).analyze(
        input_grid=[[1]],
        output_grid=[[5]],
    )

    assert report["COLOR_MAPPING_REPORT"]["reuse_hits"] >= 1
    assert report["COLOR_MAPPING_REPORT"]["selected_program"]["steps"][0][
        "parameters"
    ]["mapping"] == {"1": 5}


def test_transformation_synthesis_uses_color_mapping_engine():
    report = TransformationSynthesisEngine(
        memory=None,
        executor=PrimitiveExecutor(),
    ).synthesize(
        input_grid=[
            [1, 2, 3],
        ],
        output_grid=[
            [5, 7, 8],
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
