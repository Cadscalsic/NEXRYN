from runtime.memory.transformation_memory import TransformationMemory
from runtime.reasoning.transformation_synthesis_engine import TransformationSynthesisEngine
from runtime.transformation_compilation import SemanticToTransformationCompiler
from runtime.transformation_compilation.compiler_infrastructure import (
    CompilerInfrastructureAnalyzer,
)
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
    infrastructure = report["compiler_infrastructure_report"]
    assert infrastructure["execution_package_health_score"] > 0.5
    assert infrastructure["primitive_operation_coverage"] > 0.5
    assert infrastructure["compiler_infrastructure_readiness"] in {"PARTIAL", "READY"}
    assert "topology_execution_package" in infrastructure["existing_execution_packages"]


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


def test_compiler_reports_failure_diagnostics_by_reason_and_domain():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 0],
            [0, 0],
        ],
        output_grid=[
            [1, 2],
            [0, 0],
        ],
        detected_concepts=["object_identity_preservation", "position_preservation"],
        execution_intents=[
            {
                "intent": "object_identity_preservation",
                "operation": "preserve_grid",
            }
        ],
    )

    diagnostics = report["compiler_failure_diagnostics"]

    assert report["semantic_to_transformation_compilation_success"] is False
    assert diagnostics["failure_reason_counts"]["operation_semantics_mismatch"] == 1
    assert diagnostics["failure_domain_distribution"]["Spatial"] == 1
    assert diagnostics["failure_rows"][0]["operation"] == "preserve_grid"
    assert diagnostics["failure_rows"][0]["domain"] == "Spatial"
    assert diagnostics["failure_rows"][0]["program"] == "semantic_program_preserve_grid"
    assert diagnostics["failure_rows"][0]["semantic_intent"] == "object_identity_preservation"
    assert diagnostics["failure_rows"][0]["expected_operation"] == "preserve_grid"
    assert diagnostics["failure_rows"][0]["resolved_operation"] == "preserve_grid"
    assert diagnostics["failure_rows"][0]["failure_stage"] == "semantic_operation_resolution"
    assert diagnostics["failure_rows"][0]["compiler_rule"] == "RULE_GRID_PRESERVATION_01"
    assert diagnostics["failure_rows"][0]["failed_primitive"] == "preserve_grid"
    assert diagnostics["failure_rows"][0]["execution_package"] == "spatial_execution_package"
    assert diagnostics["failure_rows"][0]["semantic_mapping_failure"] == (
        "SEMANTIC_OPERATION_MISMATCH"
    )
    assert diagnostics["failure_rows"][0]["failure_detail_depth"] == (
        "PRIMITIVE_PACKAGE_PARAMETER_TRACE"
    )


def test_compiler_infrastructure_analyzer_reports_packages_primitives_and_multistep():
    analyzer = CompilerInfrastructureAnalyzer()
    report = analyzer.build_report(
        compiler_report={},
        expected_operations=["translate", "replace_color", "density_modulation"],
        candidate_programs=[
            {
                "program_id": "program:multi",
                "compiled_program": {
                    "steps": [
                        {"operation": "translate", "parameters": {"translation": [0, 1]}},
                        {"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}},
                    ],
                },
                "validation": {"exact_match": True, "accuracy": 1.0},
            }
        ],
    )

    operations = {
        row["operation"]: row
        for row in report["primitive_operation_inventory"]
    }

    assert report["missing_execution_packages"] == []
    assert report["multi_step_program_support"] == 1.0
    assert report["compiler_primitive_success_rate"] == 1.0
    assert operations["density_modulation"]["canonical_operation"] == "expand_pattern"
    assert operations["density_modulation"]["executable"] is True
    assert operations["translate"]["compiler_can_emit"] is True


def test_primitive_executor_supports_compiler_infrastructure_aliases():
    executor = PrimitiveExecutor()
    grid = [[1, 0], [0, 0]]

    preserve = executor.execute_primitive(
        grid,
        {"primitive": "preserve_size", "parameters": {}},
    )
    bridge = executor.execute_primitive(
        grid,
        {
            "primitive": "bridge_creation",
            "parameters": {"path_cells": [[0, 1]], "path_color": 1},
        },
    )

    assert preserve.tolist() == grid
    assert bridge.tolist() == [[1, 1], [0, 0]]


def test_compiler_reports_traceable_semantic_drift_failures():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 0],
            [0, 0],
        ],
        output_grid=[
            [1, 2],
            [0, 0],
        ],
        detected_concepts=["topology_preservation"],
        execution_intents=[
            {
                "program_id": "semantic_program_preserve_topology",
                "intent": "preserve_topology",
                "operation": "translate",
                "matched_concepts": ["topology_preservation"],
            }
        ],
    )

    diagnostics = report["compiler_failure_diagnostics"]
    row = diagnostics["failure_rows"][0]

    assert report["semantic_to_transformation_compilation_success"] is False
    assert diagnostics["failure_reason_counts"]["operation_semantics_mismatch"] == 1
    assert row["trace_id"] == (
        "compiler_trace:semantic_program_preserve_topology:"
        "preserve_topology:preserve_topology"
    )
    assert row["program"] == "semantic_program_preserve_topology"
    assert row["semantic_intent"] == "preserve_topology"
    assert row["expected_operation"] == "preserve_topology"
    assert row["resolved_operation"] == "translate"
    assert row["failure_stage"] == "semantic_operation_resolution"
    assert row["reason"] == "operation_semantics_mismatch"
    assert row["compiler_rule"] == "RULE_TOPOLOGY_PRESERVATION_01"


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
