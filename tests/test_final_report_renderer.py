from runtime.reporting.final_report_renderer import (
    REPORT_BEGIN_MARKER,
    REPORT_END_MARKER,
    SECTION_ORDER,
    DeterministicFinalReportRenderer,
)


def _report_state():
    return {
        "runtime_status": "completed",
        "tasks_executed": 3,
        "successful_tasks": 3,
        "generated_concepts": 4,
        "generated_programs": 2,
        "truth_candidate_count": 1,
        "PROGRAM_SYNTHESIS_REPORT": {
            "average_program_confidence": 0.82,
            "highest_confidence": 0.91,
            "lowest_confidence": 0.64,
            "validation_distribution": {"VALID": 2},
        },
        "TRANSFORMATION_SYNTHESIS_REPORT": {
            "detected_concepts": ["path_finding", "route_completion"],
            "transformation_confidence": 1.0,
            "transformation_accuracy": 1.0,
            "selected_program": {
                "steps": [
                    {
                        "operation": "construct_path",
                        "parameters": {
                            "path_color": 1,
                            "path_cells": [[0, 1], [0, 2]],
                        },
                    }
                ],
                "step_count": 1,
            },
            "semantic_to_transformation_compilation_report": {
                "semantic_to_transformation_compilation_success": True,
                "detected_intents": ["path_finding", "route_completion"],
                "execution_intents": [
                    {
                        "intent": "path_construction",
                        "operation": "construct_path",
                        "source": "semantic_intent_router",
                    }
                ],
                "semantic_intent_routing_report": {
                    "semantic_intent_routing_success": True,
                    "execution_intent_count": 1,
                },
                "selected_intent": "path_construction",
                "candidate_count": 1,
                "compiled_program": {
                    "steps": [
                        {
                            "operation": "construct_path",
                            "parameters": {
                                "path_color": 1,
                                "path_cells": [[0, 1], [0, 2]],
                            },
                        }
                    ],
                    "step_count": 1,
                },
                "validation": {
                    "accuracy": 1.0,
                    "exact_match": True,
                    "shape_match": True,
                },
                "transformation_plan": {
                    "plan_type": "semantic_to_transformation",
                    "rationale": "semantic_path_delta_to_explicit_path_cells",
                },
                "transformation_graph": {
                    "node_count": 1,
                    "edge_count": 0,
                },
            },
        },
        "COGNITIVE_SEARCH_REPORT": {
            "overall_search_quality": 0.76,
            "search_efficiency": 0.81,
            "search_coverage": 0.69,
            "search_entropy": 0.33,
            "average_route_quality": 0.71,
            "route_count": 3,
        },
        "RUNTIME_LIFECYCLE_REPORT": {
            "total_executions": 3,
            "completed_executions": 3,
            "archived_executions": 3,
            "execution_coverage": 1.0,
            "snapshot_coverage": 1.0,
            "lifecycle_coverage": 1.0,
        },
        "EXECUTION_BINDING_REPORT": {
            "binding_status": "BOUND",
            "missing_execution_instances": 0,
            "missing_snapshot_runtimes": 0,
        },
        "RUNTIME_METRIC_SYNCHRONIZATION_REPORT": {
            "metric_validation_status": "VALID",
        },
        "RUNTIME_OBSERVABILITY_REPORT": {
            "observability_status": "HEALTHY",
        },
        "execution_timing": {
            "execution_timing_state": {
                "total_wall_time": 10.0,
                "cognitive_runtime_time": 6.0,
                "unattributed_time": 0.5,
                "timing_coverage": 0.95,
                "report_generation_time": 0.2,
                "finalization_time": 0.3,
            },
            "timing_records": [
                {
                    "timing_scope": "BOOT_TIME",
                    "timing_status": "OBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 0.5,
                    "inclusive_duration_seconds": 0.5,
                    "exclusive_duration_seconds": 0.5,
                    "cpu_duration_seconds": 0.0,
                    "measurement_source": "execution_timing_unification_engine",
                    "measurement_method": "external_scope_duration_or_zero_when_unobserved",
                },
                {
                    "timing_scope": "REPORT_GENERATION_TIME",
                    "timing_status": "OBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 0.2,
                    "inclusive_duration_seconds": 0.2,
                    "exclusive_duration_seconds": 0.2,
                    "cpu_duration_seconds": 0.0,
                    "measurement_source": "execution_timing_unification_engine",
                    "measurement_method": "external_scope_duration_or_zero_when_unobserved",
                },
            ],
        },
        "performance_report": {
            "total_runtime_seconds": 10.0,
            "active_compute_time_seconds": 8.0,
            "untracked_runtime_seconds": 0.5,
            "stage_metrics": [
                {
                    "stage_name": "grid_analysis",
                    "total_duration": 1.0,
                    "execution_count": 1,
                },
                {
                    "stage_name": "reasoning",
                    "total_duration": 3.0,
                    "execution_count": 1,
                },
                {
                    "stage_name": "search",
                    "total_duration": 2.0,
                    "execution_count": 1,
                },
                {
                    "stage_name": "evaluation",
                    "total_duration": 0.4,
                    "execution_count": 1,
                },
            ],
        },
        "compact_report": {
            "heavy_keys_removed": 1,
            "arrays_summarized": 1,
            "repeated_reports_collapsed": 1,
        },
        "raw_nested_report": {"nested": {"not": "printed"}},
    }


def _metadata():
    return {
        "system": "NEXRYN",
        "mode": "test",
        "profile": "unit",
        "report_level": "normal",
        "execution_id": "exec-1",
        "timestamp": "2026-07-15T00:00:00Z",
        "runtime_status": "completed",
        "execution_time": 1.25,
    }


def test_render_has_boundaries_and_stable_section_order():
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert report.startswith(REPORT_BEGIN_MARKER)
    assert report.rstrip().endswith(REPORT_END_MARKER)
    positions = [report.index(section) for section in SECTION_ORDER]
    assert positions == sorted(positions)
    assert renderer.report()["report_complete"] is True


def test_render_has_single_final_status_and_no_raw_dict_repr():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
    )

    assert report.count("NEXRYN :: FINAL STATUS") == 1
    assert "{'nested'" not in report
    assert "raw_nested_report" not in report


def test_render_does_not_begin_or_end_with_partial_structure():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
    )

    first_after_marker = report[len(REPORT_BEGIN_MARKER):].lstrip()
    assert first_after_marker.startswith("=")
    assert not report.rstrip().endswith(("{", "[", ":", ","))


def test_identical_inputs_render_identically():
    renderer = DeterministicFinalReportRenderer()

    first = renderer.render(_report_state(), runtime_metadata=_metadata())
    second = renderer.render(_report_state(), runtime_metadata=_metadata())

    assert first == second


def test_console_budget_fallback_remains_complete():
    state = _report_state()
    state["huge_diagnostic"] = "x" * 5000
    renderer = DeterministicFinalReportRenderer(console_budget_chars=200)

    report = renderer.render(state, runtime_metadata=_metadata())

    assert report.startswith(REPORT_BEGIN_MARKER)
    assert report.rstrip().endswith(REPORT_END_MARKER)
    assert "Console Appendix: omitted" in report
    assert renderer.report()["report_truncated"] is True
    assert renderer.report()["report_complete"] is True


def test_console_budget_writes_full_text_artifact(tmp_path):
    state = _report_state()
    state["huge_diagnostic"] = "x" * 5000
    renderer = DeterministicFinalReportRenderer(console_budget_chars=200)

    console_report = renderer.render(
        state,
        runtime_metadata=_metadata(),
        artifact_directory=tmp_path,
        write_artifact=True,
    )

    artifact_text = (tmp_path / "runtime_report.txt").read_text(
        encoding="utf-8",
    )
    assert "Console Appendix: omitted" in console_report
    assert "Console Appendix: omitted" not in artifact_text
    assert artifact_text.startswith(REPORT_BEGIN_MARKER)
    assert artifact_text.rstrip().endswith(REPORT_END_MARKER)


def test_text_artifact_matches_rendered_report(tmp_path):
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(
        _report_state(),
        runtime_metadata=_metadata(),
        artifact_directory=tmp_path,
        write_artifact=True,
    )

    artifact = tmp_path / "runtime_report.txt"
    assert artifact.read_text(encoding="utf-8") == report
    assert renderer.report()["report_artifact_written"] is True


def test_duplicate_section_detection():
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(_report_state(), runtime_metadata=_metadata())
    invalid_report = report.replace(
        "FINAL STATUS",
        "FINAL STATUS\nFINAL STATUS",
        1,
    )

    errors = renderer.validate(invalid_report)

    assert "duplicate_section:FINAL STATUS" in errors


def test_normal_report_restores_per_stage_timing_visibility():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE STAGE TIMING" in report
    assert "TIMING HIERARCHY SUMMARY" in report
    assert "RESOURCE CONSUMPTION RANKING" in report
    assert "stage_name" in report
    assert "Reasoning" in report
    assert "Search" in report
    assert "Grid Analysis" in report
    assert "percentage_of_active_compute" in report
    assert "Top Three Exclusive-Time Consumers" in report
    assert "ACTIVE_COMPUTE_TIME" in report
    assert "REPORTING TIMING SUMMARY" in report
    assert "Report Lifecycle Total Time:" in report


def test_normal_report_exposes_semantic_compilation_observability():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "SEMANTIC COMPILATION" in report
    assert "Semantic Intent Router Success: TRUE" in report
    assert "Execution Intents: 1" in report
    assert "Compiler Triggered: TRUE" in report
    assert "Compiled Candidates: 1" in report
    assert "Selected Intent: path_construction" in report
    assert "Compiled Operation: construct_path" in report
    assert "Selected From Compiler: TRUE" in report
    assert "Compilation Status: SUCCESS" in report
    assert "Execution Status: SUCCESS" in report


def test_normal_report_exposes_prediction_provenance_decision_owner():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "TRANSFORMATION DECISION" in report
    assert "Prediction Source: semantic_to_transformation_compiler" in report
    assert "Decision Owner: Semantic-to-Transformation Compiler" in report
    assert "Winning Candidate: construct_path" in report
    assert "Selected Operation: construct_path" in report
    assert "Compiler Participation: TRUE" in report
    assert "Program Validation: SUCCESS" in report
    assert "Generated Concepts Observed: 2.0" in report
    assert "Program Candidates: 1.0" in report
    assert "Decision Pipeline: Semantic Attribution -> Pattern Analysis -> Rule Analysis" in report


def test_prediction_provenance_reports_unresolved_when_success_source_is_missing():
    state = _report_state()
    state.pop("TRANSFORMATION_SYNTHESIS_REPORT")
    state["EVALUATION_REPORT"] = {
        "accuracy": 1.0,
        "success_state": "EXACT_SUCCESS",
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "TRANSFORMATION DECISION" in report
    assert "Prediction Source: Not Available" in report
    assert "Decision Owner: UNRESOLVED" in report
    assert "Program Validation: EXACT_SUCCESS" in report
    assert "Prediction Accuracy: 1" in report


def test_prediction_provenance_identifies_noncompiler_winning_program():
    state = _report_state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"][
        "semantic_to_transformation_compilation_report"
    ] = {
        "semantic_to_transformation_compilation_success": False,
        "detected_intents": ["inside_outside"],
        "compiled_program": {"steps": [], "step_count": 0},
        "candidate_count": 0,
        "failure_reason": "no_supported_semantic_delta",
        "validation": {"accuracy": 0.0, "exact_match": False},
    }
    state["TRANSFORMATION_SYNTHESIS_REPORT"]["transformation_accuracy"] = 1.0

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Compiler Participation: FALSE" in report
    assert "Prediction Source: transformation_synthesis" in report
    assert "Decision Owner: Transformation Synthesis Engine" in report
    assert "Selected Operation: construct_path" in report
    assert "Program Validation: SUCCESS" in report


def test_candidate_arena_reports_adaptive_reuse_single_source_dominance():
    state = _report_state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": ["bridge_creation", "component_connection"],
        "semantic_to_transformation_compilation_report": {
            "semantic_to_transformation_compilation_success": False,
            "detected_intents": ["bridge_creation", "component_connection"],
            "execution_intents": [],
            "semantic_intent_routing_report": {
                "semantic_intent_routing_success": False,
                "execution_intent_count": 0,
            },
            "candidate_count": 0,
            "compiled_program": {"steps": [], "step_count": 0},
            "failure_reason": "no_executable_semantic_intents",
        },
    }
    state["ADAPTIVE_REUSE_REPORT"] = {
        "reuse_success_rate": 1.0,
        "reused_programs": [
            {
                "steps": [
                    {
                        "operation": "inside_outside_reuse",
                        "parameters": {},
                    }
                ],
                "step_count": 1,
            }
        ],
    }
    state["PREDICTION_PROVENANCE_REPORT"] = {
        "prediction_source": "adaptive_reuse",
        "decision_owner": "Adaptive Reuse Layer",
        "winning_candidate": "adaptive_reuse_decision",
        "decision_confidence": 1.0,
        "program_validation": "SUCCESS",
        "prediction_accuracy": 1.0,
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE CANDIDATE ARENA" in report
    assert "Arena State: SINGLE_SOURCE_DOMINANCE" in report
    assert "Attempted Candidates: 2" in report
    assert "Explicit Rejections: 1" in report
    assert "Competitor Sources: adaptive_reuse" in report
    assert "Winner Takes All Detected: TRUE" in report
    assert "Dominance Source: adaptive_reuse" in report
    assert "Compiler Attempted: TRUE" in report
    assert "semantic_to_transformation_compiler: REJECTED reason=no_executable_semantic_intents" in report
    assert "Missing Competition Reason: Only one candidate source entered the arena." in report


def test_report_marks_selected_compiler_without_report_as_attempted_rejection():
    state = _report_state()
    state.pop("TRANSFORMATION_SYNTHESIS_REPORT")
    state["tool_selection_report"] = {
        "enabled_tools": ["semantic_to_transformation_compiler"],
    }
    state["ADAPTIVE_REUSE_REPORT"] = {
        "reuse_success_rate": 1.0,
        "reused_programs": [
            {
                "steps": [
                    {
                        "operation": "adaptive_reuse_program",
                        "parameters": {},
                    }
                ],
                "step_count": 1,
            }
        ],
    }
    state["PREDICTION_PROVENANCE_REPORT"] = {
        "prediction_source": "adaptive_reuse",
        "decision_owner": "Adaptive Reuse Layer",
        "winning_candidate": "adaptive_reuse_program",
        "program_validation": "SUCCESS",
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Compiler Triggered: TRUE" in report
    assert "Compilation Status: REQUIRED_REPORT_MISSING" in report
    assert "Compiler Attempted: TRUE" in report
    assert "CANDIDATE PROPOSAL PHASE" in report
    assert report.index("CANDIDATE PROPOSAL PHASE") < report.index("COGNITIVE CANDIDATE ARENA")
    assert "Proposal Phase Entered: TRUE" in report
    assert "Sources Rejected: semantic_to_transformation_compiler" in report
    assert "Attempted Candidates: 2" in report
    assert "Explicit Rejections: 1" in report
    assert "semantic_to_transformation_compiler: REJECTED reason=Semantic compiler selected but no compilation report was produced." in report


def test_report_exposes_executable_semantic_coverage():
    state = _report_state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"]["detected_concepts"] = [
        "density_increase",
        "symmetry_break",
        "relative_position",
        "spatial_relation",
        "transformation_sequence",
        "bridge_creation",
        "component_connection",
        "connectivity_change",
        "topology_change",
        "density_modulation",
        "growth",
        "propagation",
        "directional_motion",
        "position_preservation",
        "object_identity_preservation",
        "shape_preservation",
        "rotation",
        "reflection",
    ]
    state["TRANSFORMATION_SYNTHESIS_REPORT"].pop(
        "semantic_to_transformation_compilation_report",
    )

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "EXECUTABLE SEMANTIC COVERAGE" in report
    assert report.index("EXECUTABLE SEMANTIC COVERAGE") < report.index("TRANSFORMATION DECISION")
    assert "Generated Concepts: 18" in report
    assert "Executable Concepts: 7" in report
    assert "Unsupported Concepts: 11" in report
    assert "Coverage Status: LOW" in report
    assert "Unsupported Operations:" in report
    assert "density_modulation" in report


def test_candidate_arena_reports_competitive_sources_when_multiple_enter():
    state = _report_state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"]["ranked_candidates"] = [
        {
            "program": state["TRANSFORMATION_SYNTHESIS_REPORT"]["selected_program"],
            "score": 0.91,
            "prediction_accuracy": 1.0,
        },
        {
            "program": {
                "steps": [
                    {
                        "operation": "fill_region",
                        "parameters": {},
                    }
                ],
                "step_count": 1,
            },
            "score": 0.72,
            "prediction_accuracy": 0.75,
        },
    ]

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Arena State: COMPETITIVE" in report
    assert "semantic_to_transformation_compiler" in report
    assert "transformation_synthesis" in report
    assert "Winner Takes All Detected: FALSE" in report
    assert "Final Report Rendering Time: 0.2 s" in report
    assert "Report Generation Time:" not in report
    assert "Total Wall Time: 10 s" in report
    assert "Active Compute Time: 7.1 s" in report
    assert "Untracked Time: 0.5 s" in report


def test_minimal_report_keeps_top_timing_summary_without_full_stage_table():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="minimal",
    )

    assert "TIMING SUMMARY" in report
    assert "Total Wall Time: 10 s" in report
    assert "Active Compute Time: 7.1 s" in report
    assert "Top Three Exclusive-Time Consumers" in report
    assert "Overlap Detected:" in report
    assert "Report Lifecycle Total Time:" in report
    assert "Final Report Rendering Time: 0.2 s" in report
    assert "Report Timing Status:" in report
    assert "REPORTING TIMING SUMMARY" not in report
    assert "Report Generation Time:" not in report
    assert "COGNITIVE STAGE TIMING" not in report


def test_diagnostic_report_exposes_timing_detail_fields():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="diagnostic",
    )

    assert "DIAGNOSTIC TIMING DETAIL" in report
    assert "inclusive=" in report
    assert "exclusive=" in report
    assert "source=ExecutionTimingState" in report
    assert "Reporting Final Report Rendering Time" in report
    assert "Legacy Reporting Field report_generation_time" in report
