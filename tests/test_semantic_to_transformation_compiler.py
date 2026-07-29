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


def test_compiles_translation_from_execution_operation_intent():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [0, 1, 0],
            [0, 0, 0],
            [0, 0, 0],
        ],
        output_grid=[
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ],
        detected_concepts=["spatial_reasoning"],
        execution_intents=[
            {
                "intent": "spatial_reasoning",
                "operation": "translate",
                "matched_concepts": ["directional_motion"],
            }
        ],
    )

    step = report["compiled_program"]["steps"][0]

    assert report["semantic_to_transformation_compilation_success"] is True
    assert report["selected_intent"] == "translation"
    assert step["operation"] == "translate"
    assert step["parameters"]["delta_row"] == 1
    assert step["parameters"]["delta_col"] == 0
    assert report["validation"]["exact_match"] is True


def test_compiles_color_replacement_from_execution_operation_intent():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 1],
            [0, 0],
        ],
        output_grid=[
            [2, 2],
            [0, 0],
        ],
        detected_concepts=["color_reasoning"],
        execution_intents=[
            {
                "intent": "color_reasoning",
                "operation": "replace_color",
                "matched_concepts": ["symbolic_remapping"],
            }
        ],
    )

    step = report["compiled_program"]["steps"][0]

    assert report["semantic_to_transformation_compilation_success"] is True
    assert step["operation"] == "replace_color"
    assert step["parameters"]["color_mapping"] == {1: 2}
    assert report["validation"]["exact_match"] is True


def test_reports_compiler_resolution_trace_for_unsupported_execution_intent():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[[1]],
        output_grid=[[1]],
        detected_concepts=["unsupported_semantic"],
        execution_intents=[
            {
                "intent": "unsupported_semantic",
                "operation": "density_modulation",
            }
        ],
    )

    trace = report["compiler_resolution_trace"][0]

    assert report["failure_reason"] == "no_supported_compiler_for_execution_intents"
    assert trace["semantic_intent"] == "unsupported_semantic"
    assert trace["operation"] == "density_modulation"
    assert trace["resolved_compiler"] == "NONE"
    assert trace["compiler_found"] is False
    assert trace["compilation_attempted"] is False
    assert trace["candidate_emitted"] is False
    assert trace["resolution_state"] == "RESOLVED_COMPILER_NOT_FOUND"


def test_reports_resolved_color_compiler_without_candidate_reason():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 1],
            [1, 0],
        ],
        output_grid=[
            [2, 3],
            [2, 0],
        ],
        detected_concepts=["symbolic_remapping"],
        execution_intents=[
            {
                "intent": "symbolic_remapping",
                "operation": "replace_color",
                "matched_concepts": ["replace_color_mapping"],
            }
        ],
    )

    trace = report["compiler_resolution_trace"][0]

    assert report["failure_reason"] == "AMBIGUOUS_COLOR_MAPPING"
    assert trace["resolved_compiler"] == "ColorRemapCompiler"
    assert trace["compiler_found"] is True
    assert trace["compilation_attempted"] is True
    assert trace["candidate_emitted"] is False
    assert trace["resolution_state"] == "RESOLVED_COMPILER_FOUND_NO_CANDIDATE"
    assert trace["candidate_rejection_reason"] == "AMBIGUOUS_COLOR_MAPPING"
    assert trace["compiler_entry_payload"]["operation"] == "replace_color"
    assert trace["compiler_entry_payload"]["input_grid_available"] is True
    assert trace["compiler_entry_payload"]["target_grid_available"] is True
    assert trace["compiler_entry_payload"]["source_color"] == 1
    assert trace["compiler_entry_payload"]["target_color"] == 3
    assert trace["compiler_entry_payload"]["mapping_count"] == 1
    assert trace["compiler_exit_payload"]["candidate_count"] == 0
    assert trace["compiler_exit_payload"]["rejected_candidate_count"] == 1
    assert trace["compiler_exit_payload"]["rejection_reason"] == (
        "AMBIGUOUS_COLOR_MAPPING"
    )
    op_diag = report["compiler_operation_diagnostics"][0]
    assert op_diag["operation"] == "replace_color"
    assert op_diag["composition_diagnostic_type"] == "color_remap"
    assert op_diag["mapping_extraction_state"] == "MAPPING_EXTRACTED"
    assert op_diag["source_color"] == 1
    assert op_diag["target_color"] == 3
    assert op_diag["mapping_count"] == 1
    assert op_diag["affected_cell_count"] == 3
    assert op_diag["rejection_reason"] == "AMBIGUOUS_COLOR_MAPPING"


def test_reports_missing_color_mapping_when_remap_has_no_delta():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 1],
            [0, 0],
        ],
        output_grid=[
            [1, 1],
            [0, 0],
        ],
        detected_concepts=["symbolic_remapping"],
        execution_intents=[
            {
                "intent": "symbolic_remapping",
                "operation": "replace_color",
                "matched_concepts": ["replace_color_mapping"],
            }
        ],
    )

    trace = report["compiler_resolution_trace"][0]

    assert report["failure_reason"] == "MISSING_COLOR_MAPPING"
    assert trace["resolved_compiler"] == "ColorRemapCompiler"
    assert trace["candidate_emitted"] is False
    assert trace["candidate_rejection_reason"] == "MISSING_COLOR_MAPPING"
    assert trace["compiler_entry_payload"]["mapping_count"] == 0
    assert trace["compiler_exit_payload"]["rejection_reason"] == (
        "MISSING_COLOR_MAPPING"
    )
    op_diag = report["compiler_operation_diagnostics"][0]
    assert op_diag["mapping_extraction_state"] == "MAPPING_NOT_EXTRACTED"
    assert op_diag["affected_cell_count"] == 0
    assert op_diag["rejection_reason"] == "MISSING_COLOR_MAPPING"


def test_color_remap_emits_localized_candidate_when_global_remap_has_collateral_loss():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [0, 0, 0],
            [1, 2, 2],
        ],
        output_grid=[
            [0, 6, 0],
            [3, 2, 2],
        ],
        detected_concepts=["symbolic_remapping"],
        execution_intents=[
            {
                "intent": "symbolic_remapping",
                "operation": "replace_color",
                "matched_concepts": ["replace_color_mapping"],
            }
        ],
    )

    trace = report["compiler_resolution_trace"][0]
    exit_payload = trace["compiler_exit_payload"]
    op_diag = report["compiler_operation_diagnostics"][0]
    step = report["compiled_program"]["steps"][0]
    parameters = step["parameters"]

    assert report["semantic_to_transformation_compilation_success"] is True
    assert "failure_reason" not in report
    assert trace["candidate_emitted"] is True
    assert trace["candidate_rejection_reason"] == "none"
    assert exit_payload["composition_step_count"] == 1
    assert exit_payload["candidate_schema_valid"] is True
    assert exit_payload["candidate_count"] == 1
    assert exit_payload["candidate_object_created"] is True
    assert exit_payload["candidate_registered"] is True
    assert exit_payload["candidate_count_incremented"] is True
    assert exit_payload["proposal_emission_ready"] is True
    assert exit_payload["materialization_outcome"] == "CANDIDATE_EMITTED"
    assert exit_payload["materialization_completion_stage"] == "candidate_registered"
    assert exit_payload["materialization_blocked_stage"] == "none"
    assert exit_payload["materialization_rejection_reason"] == "none"
    assert exit_payload["predicted_accuracy"] >= exit_payload["validation_threshold"]
    assert exit_payload["application_scope"] == "localized_changed_cells"
    assert exit_payload["affected_position_count"] == 2
    breakdown = exit_payload["predicted_accuracy_breakdown"]
    assert breakdown["estimator"] == "exact_grid_cell_match_after_global_color_remap"
    assert breakdown["accuracy_basis"] == "correct_cells / total_cells"
    assert breakdown["correct_cell_count"] == 4
    assert breakdown["total_cell_count"] == 6
    assert breakdown["collateral_remap_cell_count"] == 2
    assert breakdown["localized_accuracy"] == 1.0
    assert breakdown["localized_affected_position_count"] == 2
    assert breakdown["selected_execution_scope"] == "localized_changed_cells"
    assert breakdown["dominant_accuracy_loss_cause"] == (
        "GLOBAL_REMAP_COLLATERAL_MISMATCH"
    )
    assert exit_payload["accuracy_estimator"] == (
        "exact_grid_cell_match_after_global_color_remap"
    )
    assert exit_payload["correct_cell_count"] == 4
    assert exit_payload["incorrect_cell_count"] == 2
    assert exit_payload["total_cell_count"] == 6
    assert exit_payload["changed_target_cell_count"] == 2
    assert exit_payload["mapped_source_cell_count"] == 4
    assert exit_payload["collateral_remap_cell_count"] == 2
    assert parameters["application_scope"] == "localized_changed_cells"
    assert parameters["affected_positions"] == [[0, 1], [1, 0]]
    assert parameters["color_mapping"] == {0: 6, 1: 3}
    assert op_diag["mapping_extraction_state"] == "MAPPING_EXTRACTED"
    assert op_diag["mapping_count"] == 2
    assert op_diag["composition_step_count"] == 1
    assert op_diag["candidate_schema_valid"] is True
    assert op_diag["application_scope"] == "localized_changed_cells"
    assert op_diag["materialization_outcome"] == "CANDIDATE_EMITTED"
    assert op_diag["materialization_completion_stage"] == "candidate_registered"
    assert op_diag["materialization_blocked_stage"] == "none"
    assert op_diag["materialization_rejection_reason"] == "none"
    assert op_diag["dominant_accuracy_loss_cause"] == (
        "GLOBAL_REMAP_COLLATERAL_MISMATCH"
    )
    assert op_diag["composition_validation_state"] == "CANDIDATE_VALID"


def test_preservation_compiler_reports_target_changed_contract_failure():
    report = SemanticToTransformationCompiler().compile(
        input_grid=[
            [1, 0],
            [0, 1],
        ],
        output_grid=[
            [1, 2],
            [0, 1],
        ],
        detected_concepts=["symmetry_preservation"],
        execution_intents=[
            {
                "intent": "symmetry_reasoning",
                "operation": "preserve_symmetry",
                "matched_concepts": ["symmetry_preservation"],
            }
        ],
    )

    trace = report["compiler_resolution_trace"][0]
    exit_payload = trace["compiler_exit_payload"]
    op_diag = report["compiler_operation_diagnostics"][0]

    assert report["failure_reason"] == "operation_semantics_mismatch"
    assert trace["resolved_compiler"] == "PreservationCompiler"
    assert trace["candidate_emitted"] is False
    assert trace["candidate_rejection_reason"] == "operation_semantics_mismatch"
    assert exit_payload["preservation_contract_state"] == (
        "PRESERVATION_CONTRACT_FAILED_TARGET_CHANGED"
    )
    assert exit_payload["changed_cell_count"] == 1
    assert exit_payload["composition_step_count"] == 0
    assert exit_payload["candidate_schema_valid"] is False
    assert exit_payload["composition_validation_state"] == (
        "PRESERVATION_CONTRACT_FAILED_TARGET_CHANGED"
    )
    assert op_diag["composition_diagnostic_type"] == "preservation"
    assert op_diag["preservation_contract_state"] == (
        "PRESERVATION_CONTRACT_FAILED_TARGET_CHANGED"
    )


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


def test_compiler_reports_operational_grounding_requirements_when_grid_pair_missing():
    report = SemanticToTransformationCompiler().compile(
        input_grid=None,
        output_grid=None,
        detected_concepts=["translation"],
        execution_intents=[
            {
                "program_id": "semantic_program_translate",
                "intent": "directional_translation",
                "operation": "translate",
            }
        ],
    )

    diagnostics = report["compiler_failure_diagnostics"]
    row = diagnostics["grounding_requirement_rows"][0]

    assert diagnostics["failure_reason_counts"]["missing_grid_pair"] >= 1
    assert diagnostics["operational_grounding_failure_count"] >= 1
    assert diagnostics["operational_grounding_state"] == "GROUNDING_FAILURE_DOMINANT"
    assert diagnostics["grounding_required_for_operations"] == ["translate"]
    assert diagnostics["grounding_required_for_domains"]["Spatial"] == 1
    assert row["operation"] == "translate"
    assert row["domain"] == "Spatial"
    assert row["missing_grounding"] == "input_output_grid_pair"
    assert row["required_evidence"] == "exact_or_governed_validation_success"
    assert row["required_task_property"] == (
        "unambiguous_directional_translation_ground_truth"
    )
    assert row["grounding_stage"] == "compiler_input_grounding"
    assert row["action"] == "select_grounding_aligned_task"


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
    assert report["execution_package_inventory_state"] == (
        "PACKAGE_INVENTORY_AVAILABLE"
    )
    assert report["primitive_operation_inventory_state"] == (
        "PRIMITIVE_INVENTORY_AVAILABLE"
    )
    assert report["execution_package_inventory_count"] >= 1
    assert report["primitive_operation_inventory_count"] >= 1
    assert report["executable_package_count"] >= 1
    assert report["executable_primitive_count"] >= 1
    assert report["multi_step_program_support"] == 1.0
    assert report["compiler_primitive_success_rate"] == 1.0
    assert operations["density_modulation"]["canonical_operation"] == "expand_pattern"
    assert operations["density_modulation"]["executable"] is True
    assert operations["translate"]["compiler_can_emit"] is True


def test_compiler_infrastructure_reports_unused_executable_package_gaps():
    report = CompilerInfrastructureAnalyzer().build_report(
        compiler_report={
            "compiler_failure_diagnostics": {
                "failure_reason_counts": {
                    "missing_grid_pair": 3,
                    "execution_package_missing": 1,
                }
            }
        },
        expected_operations=["translate"],
    )

    gaps = {
        row["package"]: row
        for row in report["package_utilization_gap_rows"]
    }

    assert "object_execution_package" in report["unused_execution_packages"]
    assert "pattern_execution_package" in report["unused_execution_packages"]
    assert gaps["object_execution_package"]["utilization_gap_type"] == (
        "GROUNDING_BLOCKED_PACKAGE_UTILIZATION"
    )
    assert "remove_object" in gaps["object_execution_package"][
        "supported_operations"
    ]
    assert "expand_pattern" in gaps["pattern_execution_package"][
        "supported_operations"
    ]
    assert report["package_utilization_gap_state"] == (
        "UNUSED_EXECUTABLE_PACKAGES_PRESENT"
    )


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
