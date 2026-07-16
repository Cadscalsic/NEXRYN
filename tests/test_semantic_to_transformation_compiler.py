from runtime.memory.transformation_memory import TransformationMemory
from runtime.reasoning.transformation_synthesis_engine import TransformationSynthesisEngine
from runtime.transformation_compilation import SemanticToTransformationCompiler
from runtime.transforms.primitive_executor import PrimitiveExecutor


def test_compiles_path_construction_into_explicit_path_cells():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 0, 0, 1],
        ],
        output_grid=[
            [1, 1, 1, 1],
        ],
        detected_concepts=["path_finding", "route_completion"],
    )

    assert report["semantic_to_transformation_compilation_success"] is True
    assert report["selected_intent"] == "path_construction"
    assert report["compiled_program"]["steps"][0]["operation"] == "construct_path"
    assert report["compiled_program"]["steps"][0]["parameters"]["path_cells"] == [[0, 1], [0, 2]]
    assert report["validation"]["exact_match"] is True


def test_compiles_scaling_into_cell_repeat_program():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 2],
            [3, 4],
        ],
        output_grid=[
            [1, 1, 2, 2],
            [1, 1, 2, 2],
            [3, 3, 4, 4],
            [3, 3, 4, 4],
        ],
        detected_concepts=["scaling", "scale_transformation"],
    )

    step = report["compiled_program"]["steps"][0]

    assert report["semantic_to_transformation_compilation_success"] is True
    assert report["selected_intent"] == "scaling"
    assert step["operation"] == "scale_up"
    assert step["parameters"]["scale_mode"] == "cell_repeat"
    assert step["parameters"]["scale_factor"] == 2
    assert report["validation"]["exact_match"] is True


def test_compiles_noise_removal_into_explicit_filter_program():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [0, 0, 0],
            [0, 5, 0],
            [0, 9, 0],
        ],
        output_grid=[
            [0, 0, 0],
            [0, 5, 0],
            [0, 0, 0],
        ],
        detected_concepts=["noise_removal", "artifact_filtering"],
    )

    step = report["compiled_program"]["steps"][0]

    assert report["semantic_to_transformation_compilation_success"] is True
    assert report["selected_intent"] == "noise_or_artifact_filtering"
    assert step["operation"] == "remove_object"
    assert step["parameters"]["cells_to_clear"] == [[2, 1]]
    assert report["validation"]["exact_match"] is True


def test_compiler_is_stable_for_identical_inputs():
    compiler = SemanticToTransformationCompiler()
    kwargs = {
        "input_grid": [[1, 0, 1]],
        "output_grid": [[1, 1, 1]],
        "detected_concepts": ["path_finding"],
    }

    first = compiler.compile(**kwargs)
    second = compiler.compile(**kwargs)

    assert first["compiled_program"] == second["compiled_program"]
    assert first["transformation_graph"] == second["transformation_graph"]


def test_synthesis_selects_semantic_compiler_for_scaling_execution_gap():
    report = TransformationSynthesisEngine(
        memory=TransformationMemory(),
        executor=PrimitiveExecutor(),
    ).synthesize(
        input_grid=[
            [1, 2],
            [3, 4],
        ],
        output_grid=[
            [1, 1, 2, 2],
            [1, 1, 2, 2],
            [3, 3, 4, 4],
            [3, 3, 4, 4],
        ],
        detected_concepts=["scaling", "density_increase"],
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]
    selected = synthesis["selected_program"]["steps"][0]

    assert selected["operation"] == "scale_up"
    assert selected["parameters"]["scale_mode"] == "cell_repeat"
    assert synthesis["transformation_accuracy"] == 1.0
    assert (
        synthesis["semantic_to_transformation_compilation_report"][
            "semantic_to_transformation_compilation_success"
        ]
        is True
    )


def test_synthesis_selects_semantic_compiler_for_path_execution_gap():
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
        detected_concepts=["path_finding", "route_completion"],
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]
    selected = synthesis["selected_program"]["steps"][0]

    assert selected["operation"] == "construct_path"
    assert selected["parameters"]["path_cells"] == [[0, 1], [0, 2]]
    assert synthesis["transformation_accuracy"] == 1.0
