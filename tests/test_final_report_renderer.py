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


def test_render_includes_cognitive_domain_ecosystem_report():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    governance_pos = report.index("COGNITIVE DOMAIN GOVERNANCE REPORT")
    ecosystem_pos = report.index("COGNITIVE DOMAIN ECOSYSTEM REPORT")
    compilation_pos = report.index("SEMANTIC COMPILATION")

    assert governance_pos < ecosystem_pos < compilation_pos
    assert "Total Domains:" in report
    assert "Capability Coverage:" in report
    assert "Cognitive Bottlenecks:" in report
    assert "Ecosystem Maturity:" in report


def test_render_includes_cognitive_capability_coverage_map():
    state = _report_state()
    state["PROGRAM_GENERATION_REPORT"] = {
        "generated_programs": 2,
        "eligible_concepts": 2,
        "generated_blueprints": 2,
        "missing_requirements": ["compiler_support"],
    }
    state["CANDIDATE_PROPOSAL_REPORT"] = {
        "proposal_phase_entered": True,
        "eligible_source_count": 1,
        "proposal_count": 1,
        "knowledge_investment_policy": "OPERATIONAL_VALUE_PRIORITIZED",
        "knowledge_investment_authority": "candidate_proposal_runtime",
        "high_value_knowledge_items": 1,
        "medium_value_knowledge_items": 0,
        "low_value_knowledge_items": 0,
        "deprioritized_knowledge_items": 0,
        "candidate_proposals": [
            {
                "source": "program_generation",
                "proposal_status": "PROPOSED",
                "operation": "construct_path",
                "operational_value_score": 0.82,
                "investment_tier": "HIGH_VALUE",
                "investment_reason": "concrete_task_execution_signal",
            }
        ],
        "sources_with_proposals": ["program_generation"],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "arena_state": "SINGLE_SOURCE_ONLY",
            "candidate_count": 1,
            "source_count": 1,
            "sources_entered": ["normalized_program_candidates"],
            "candidate_summary": [
                {
                    "source": "normalized_program_candidates",
                    "origin_source": "program_generation",
                    "origin_sources": ["program_generation"],
                    "normalized_source": "normalized_program_candidates",
                    "normalized_sources": ["normalized_program_candidates"],
                    "candidate_id": "semantic_program:path_finding",
                    "operation": "construct_path",
                    "entered_arena": True,
                }
            ],
            "selection_mode": "EVIDENCE_BASED_ARENA",
        }
    }
    state["OPERATIONAL_CAPABILITY_MATERIALIZATION_REPORT"] = {
        "materialized_operational_capabilities": 0,
        "known_operational_capability_count": 1,
        "known_operational_operations": ["replace_color"],
        "known_operational_domain_count": 1,
        "operational_experience_count": 4,
        "operational_experience_task_count": 4,
        "reuse_evidence_count": 3,
        "independent_reuse_success_count": 3,
        "capability_survival_rate": 0.0,
        "materialization_survival_rate": 0.0,
        "generated_survival_candidate_count": 3,
        "arena_simulated_survival_candidate_count": 2,
        "arena_quality_survival_candidate_count": 1,
        "incubating_operational_capability_count": 1,
        "operational_citizen_count": 0,
        "validation_bottleneck_inflation": 0.5,
        "validation_bottleneck_state": "VALIDATION_BOTTLENECK",
        "capability_survival_store_path": "runtime/test_survival.json",
        "capability_survival_state_distribution": {
            "GENERATED_CANDIDATE": 1,
            "ARENA_SIMULATED": 1,
            "INCUBATING_VALIDATION_GAP": 1,
            "SURVIVING_CAPABILITY": 0,
            "OPERATIONAL_CITIZEN": 0,
        },
        "top_incubating_capabilities": [
            {
                "capability_id": "operational_capability:topology:construct_path:path",
                "operation": "construct_path",
                "domain": "Topology",
                "lifecycle_state": "INCUBATING_VALIDATION_GAP",
                "distinct_task_count": 2,
                "arena_simulated_count": 2,
                "best_accuracy": 0.61,
                "average_accuracy": 0.55,
                "validation_attempts": 1,
                "improvement_trend": "IMPROVING",
                "next_required_evidence": "repeatable_validation_across_independent_task",
            }
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE CAPABILITY COVERAGE" in report
    assert "Overall Cognitive Capability Coverage:" in report
    assert "Architecture Freeze State:" in report
    assert "Execution Package Coverage Target:" in report
    assert "Compiler Runtime Coverage Target:" in report
    assert "Operational Capability Coverage Target:" in report
    assert "Compiler Runtime Activated Programs:" in report
    assert "Execution Package Coverage:" in report
    assert "Candidate Attrition Coverage:" in report
    assert "End-To-End Program Lifecycle:" in report
    assert "Operationalization Bottleneck:" in report
    assert "Secondary Operationalization Bottleneck:" in report
    assert "Current Run Materialization Gap:" in report
    assert "Compiler Success Rate:" in report
    assert "Validation Success Rate:" in report
    assert "Capability Materialization Rate:" in report
    assert "Operational Yield From Concepts:" in report
    assert "Operational Yield From Programs:" in report
    assert "Operational Yield From Candidates:" in report
    assert "Operational Yield From Arena:" in report
    assert "Knowledge Production Efficiency:" in report
    assert "Knowledge Operationalization Efficiency:" in report
    assert "Operational Knowledge Waste:" in report
    assert "Operational Yield Stability:" in report
    assert "Operational Yield Stability Basis:" in report
    assert "Operational Yield Health State:" in report
    assert "Knowledge Investment Policy:" in report
    assert "Knowledge Investment Authority:" in report
    assert "High Value Knowledge Items:" in report
    assert "Medium Value Knowledge Items:" in report
    assert "Low Value Knowledge Items:" in report
    assert "Deprioritized Knowledge Items:" in report
    assert "Operational Investment Accuracy:" in report
    assert "Operational Investment Accuracy State:" in report
    assert "High Value Operational False Positives:" in report
    assert "Validation Efficiency:" in report
    assert "Validation Bottleneck Inflation:" in report
    assert "Validation Bottleneck State:" in report
    assert "High Value Validation Yield:" in report
    assert "Operational Capability Acquisition Rate:" in report
    assert "Capability Acquisition Rate Per 100 Tasks:" in report
    assert "Capability Survival Rate:" in report
    assert "Materialization Survival Rate:" in report
    assert "Candidate Retention Rate:" in report
    assert "Incubation Conversion Rate:" in report
    assert "Surviving Capability Conversion Rate:" in report
    assert "Operational Citizen Conversion Rate:" in report
    assert "Generated Survival Candidates:" in report
    assert "Arena-Simulated Survival Candidates:" in report
    assert "Arena-Quality Survival Candidates:" in report
    assert "Incubating Operational Capabilities:" in report
    assert "Operational Citizens:" in report
    assert "Current Run Operational Citizens:" in report
    assert "Historical Operational Citizens:" in report
    assert "Operational Domain Citizenship Coverage:" in report
    assert "Historical Operational Domain Citizens:" in report
    assert "Expected Operational Domain Citizens:" in report
    assert "Surviving Capability Domain Count:" in report
    assert "Missing Operational Citizen Domains:" in report
    assert "Surviving Capabilities:" in report
    assert "Validation Gap Candidate Count:" in report
    assert "Capability Population Evolution Speed:" in report
    assert "Operational Experience Growth Speed:" in report
    assert "Capability Population Evolution Lag:" in report
    assert "Capability Population Evolution State:" in report
    assert "Expected Operational Capability Count:" in report
    assert "Capability Population Evolution Gap:" in report
    assert "Target Experience Per Capability:" in report
    assert "Materialized Operational Capabilities:" in report
    assert "Operational Confidence State:" in report
    assert "Authority Transfer State:" in report
    assert "Decision Trust State:" in report
    assert "Trusted For Decision:" in report
    assert "Known Operational Capabilities:" in report
    assert "Operational Capability Population Target:" in report
    assert "Known Operational Operations:" in report
    assert "Known Operational Domains:" in report
    assert "Operational Domain Population Target:" in report
    assert "Capability Population Diversification:" in report
    assert "Reuse Evidence Count:" in report
    assert "Operational Experience Store:" in report
    assert "Capability Survival Store:" in report
    assert "Capability Survival State Distribution:" in report
    assert "Top Incubating Capabilities:" in report
    assert "Operational Experience Task Count:" in report
    assert "Operational Experience Per Capability:" in report
    assert "Operational Specialization Pressure:" in report
    assert "Current Operational Exploration Rate:" in report
    assert "Current Operational Exploitation Rate:" in report
    assert "Known Operational Candidate Count:" in report
    assert "Novel Operational Candidate Count:" in report
    assert "Operational Exploration Target:" in report
    assert "Historical Exploitation Bias:" in report
    assert "Exploration Exploitation Balance State:" in report
    assert "Capability Monopoly Share:" in report
    assert "Capability Monopoly Pressure:" in report
    assert "Dominant Operational Capability:" in report
    assert "Dominant Capability Experience Count:" in report
    assert "Experienced Capability Count:" in report
    assert "Independent Reuse Capability Count:" in report
    assert "Domain Architecture State:" in report
    assert "Cognitive Domain Architecture:" in report
    assert "gap=" in report
    assert "Missing Compiler Requirements: compiler_support" in report
    assert "Origin Sources: program_generation" in report
    assert "Normalized Sources: normalized_program_candidates" in report
    assert "value=0.82 tier=HIGH_VALUE" in report
    assert "reason=concrete_task_execution_signal" in report
    assert (
        "raw=program_generation -> adapter=candidate_proposal_runtime -> "
        "normalized=normalized_program_candidates -> arena=normalized_program_candidates"
    ) in report


def test_render_includes_cognitive_domain_constitution_report():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    ecosystem_pos = report.index("COGNITIVE DOMAIN ECOSYSTEM REPORT")
    constitution_pos = report.index("COGNITIVE DOMAIN CONSTITUTION REPORT")
    compilation_pos = report.index("SEMANTIC COMPILATION")

    assert ecosystem_pos < constitution_pos < compilation_pos
    assert "Constitutional Status:" in report
    assert "Constitutional Integrity:" in report
    assert "Constitutional Violations:" in report
    assert "Domain Constitutional Health:" in report


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
    renderer = DeterministicFinalReportRenderer(console_budget_chars=100_000)
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
    assert "Semantic Intent Router Integration: ROUTER_DRIVEN" in report
    assert "Compiler Activation Source: semantic_intent_router" in report
    assert "Execution Intents: 1" in report
    assert "Compiler Triggered: TRUE" in report
    assert "Compiled Candidates: 1" in report
    assert "Selected Intent: path_construction" in report
    assert "Compiled Operation: construct_path" in report
    assert "Selected From Compiler: TRUE" in report
    assert "Compiler Advisory State: SELECTED_EXECUTABLE" in report
    assert "Compilation Status: SUCCESS" in report
    assert "Execution Status: SUCCESS" in report


def test_semantic_compilation_reports_fallback_bridge_when_router_fails():
    state = _report_state()
    compiler_report = state["TRANSFORMATION_SYNTHESIS_REPORT"][
        "semantic_to_transformation_compilation_report"
    ]
    compiler_report["semantic_intent_routing_report"] = {
        "semantic_intent_routing_success": False,
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Semantic Intent Router Success: FALSE" in report
    assert "Semantic Intent Router Integration: FALLBACK_BRIDGE_ACTIVE" in report
    assert "Compiler Activation Source: program_generation_activation_bridge" in report


def test_semantic_compilation_reports_exact_match_advisory_not_selected():
    state = _report_state()
    compiler_report = state["TRANSFORMATION_SYNTHESIS_REPORT"][
        "semantic_to_transformation_compilation_report"
    ]
    state["TRANSFORMATION_SYNTHESIS_REPORT"]["selected_program"] = {
        "steps": [{"operation": "preserve_grid", "parameters": {}}],
        "step_count": 1,
    }
    compiler_report["validation"] = {
        "accuracy": 1.0,
        "exact_match": True,
        "shape_match": True,
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Selected From Compiler: FALSE" in report
    assert "Compiler Advisory State: ADVISORY_EXACT_MATCH_NOT_SELECTED" in report
    assert "Execution Status: NOT_SELECTED" in report


def test_normal_report_exposes_unified_concept_lifecycle():
    state = _report_state()
    state["semantic_attribution_report"] = {
        "attributed_concepts": [
            "gravity",
            "falling",
        ],
    }
    state["semantic_memory_report"] = {
        "Semantic Entities": [
            {
                "concept": "gravity",
                "semantic_memory_id": "sem:gravity",
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "UNIFIED CONCEPT LIFECYCLE REPORT" in report
    assert report.index("UNIFIED CONCEPT LIFECYCLE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Concept: gravity" in report
    assert "Semantic Cluster: Physics" in report
    assert "Mental Model: Gravity Simulation" in report
    assert "Execution Package: FALSE" in report
    assert "Semantic Memory Integration: TRUE" in report
    assert "Lifecycle Status: DISCOVERED_BUT_NOT_EXECUTABLE" in report


def test_normal_report_exposes_program_generation_blueprints():
    state = _report_state()
    state["semantic_attribution_report"] = {
        "attributed_concepts": [
            "rotation",
            "gravity",
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "PROGRAM GENERATION REPORT" in report
    assert report.index("UNIFIED CONCEPT LIFECYCLE REPORT") < report.index("PROGRAM GENERATION REPORT")
    assert report.index("PROGRAM GENERATION REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Generated Blueprints:" in report
    assert "Program: Rotation Program" in report
    assert "Concept: rotation" in report
    assert "Generation Status: GENERATED" in report
    assert "Candidate Ready: FALSE" in report
    assert "Missing Requirements: candidate_proposal_support" in report


def test_normal_report_exposes_program_blueprint_intelligence():
    state = _report_state()
    state["PROGRAM_GENERATION_REPORT"] = {
        "program_blueprints": [
            {
                "program_id": "program_blueprint:gravity",
                "concept_name": "gravity",
                "semantic_cluster": "Physics",
                "program_type": "gravity_program",
                "compiler_supported": "TRUE",
                "generation_success": "FALSE",
                "generation_status": "BLOCKED",
                "execution_package_available": "FALSE",
                "candidate_ready": "FALSE",
                "missing_requirements": ["gravity_execution_package"],
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "PROGRAM BLUEPRINT INTELLIGENCE REPORT" in report
    assert report.index("PROGRAM GENERATION REPORT") < report.index("PROGRAM BLUEPRINT INTELLIGENCE REPORT")
    assert report.index("PROGRAM BLUEPRINT INTELLIGENCE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Program: Gravity Program" in report
    assert "Semantic Family: Physics" in report
    assert "Mental Model: Gravity Simulation" in report
    assert "Execution Readiness: MISSING_PACKAGE" in report
    assert "Candidate Readiness: WAITING_FOR_EXECUTION_PACKAGE" in report
    assert "Required Packages: gravity_execution_package" in report
    assert "Capability Status: WAITING_FOR_EXECUTION_PACKAGE" in report


def test_normal_report_exposes_cognitive_program_lifecycle():
    state = _report_state()
    state["PROGRAM_BLUEPRINT_INTELLIGENCE_REPORT"] = {
        "program_blueprint_intelligence": [
            {
                "blueprint_id": "program_intelligence:gravity_program",
                "program_type": "gravity_program",
                "semantic_family": "Physics",
                "mental_model": "Gravity Simulation",
                "supported_concepts": ["gravity", "falling"],
                "compiler_supported": "TRUE",
                "execution_ready": "MISSING_PACKAGE",
                "candidate_ready": "WAITING_FOR_EXECUTION_PACKAGE",
                "validation_ready": "FALSE",
                "required_packages": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                    "gravity_validation_support",
                ],
                "missing_requirements": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                    "gravity_validation_support",
                ],
                "capability_profile": {
                    "semantic_capabilities": ["gravity", "falling"],
                },
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE PROGRAM LIFECYCLE REPORT" in report
    assert report.index("PROGRAM BLUEPRINT INTELLIGENCE REPORT") < report.index("COGNITIVE PROGRAM LIFECYCLE REPORT")
    assert report.index("COGNITIVE PROGRAM LIFECYCLE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Program: Gravity Program" in report
    assert "Lifecycle Status: PACKAGE_REQUIREMENTS_IDENTIFIED" in report
    assert "Maturity Level: FOUNDATIONAL" in report
    assert "Execution Readiness: NOT_READY" in report
    assert "Candidate Readiness: NOT_READY" in report
    assert "Operational Readiness: NOT_READY" in report
    assert "Lifecycle Failures: EXECUTION_REQUIREMENTS_VALIDATED:NO_EXECUTION_PACKAGE" in report


def test_normal_report_exposes_cognitive_knowledge_domains():
    state = _report_state()
    state["semantic_attribution_report"] = {
        "attributed_concepts": [
            "gravity",
            "falling",
        ],
    }
    state["PROGRAM_BLUEPRINT_INTELLIGENCE_REPORT"] = {
        "program_blueprint_intelligence": [
            {
                "blueprint_id": "program_intelligence:gravity_program",
                "program_type": "gravity_program",
                "semantic_family": "Physics",
                "mental_model": "Gravity Simulation",
                "supported_concepts": ["gravity", "falling", "support"],
                "compiler_supported": "TRUE",
                "execution_ready": "MISSING_PACKAGE",
                "candidate_ready": "WAITING_FOR_EXECUTION_PACKAGE",
                "validation_ready": "FALSE",
                "required_packages": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                    "gravity_validation_support",
                ],
                "missing_requirements": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                    "gravity_validation_support",
                ],
                "capability_profile": {
                    "semantic_capabilities": ["gravity", "falling"],
                },
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE KNOWLEDGE DOMAINS REPORT" in report
    assert report.index("COGNITIVE PROGRAM LIFECYCLE REPORT") < report.index("COGNITIVE KNOWLEDGE DOMAINS REPORT")
    assert report.index("COGNITIVE KNOWLEDGE DOMAINS REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Domain: Physics Domain" in report
    assert "Semantic Families: Physics" in report
    assert "Mental Models: Gravity Simulation" in report
    assert "Program Blueprints: gravity_program" in report
    assert "Concept Count:" in report
    assert "Missing Capabilities:" in report
    assert "gravity_execution_package" in report
    assert "gravity_candidate_support" in report
    assert "gravity_validation_support" in report
    assert "Silent Domain Assignment Failures: FALSE" in report


def test_normal_report_exposes_cognitive_domain_intelligence():
    state = _report_state()
    state["COGNITIVE_KNOWLEDGE_DOMAINS_REPORT"] = {
        "domains": [
            {
                "domain_id": "domain:spatial",
                "domain_name": "Spatial Domain",
                "semantic_families": ["Spatial"],
                "semantic_concepts": ["relative_position"],
                "mental_models": ["Spatial Reasoning"],
            },
            {
                "domain_id": "domain:identity",
                "domain_name": "Identity Domain",
                "semantic_families": ["Identity"],
                "semantic_concepts": ["object_identity_preservation"],
                "mental_models": ["Object Identity"],
            },
            {
                "domain_id": "domain:topology",
                "domain_name": "Topology Domain",
                "semantic_families": ["Topology"],
                "mental_models": ["Topology Reasoning"],
                "program_blueprints": ["topology_program"],
                "semantic_concepts": ["bridge_creation", "topology_change"],
                "execution_packages": ["topology_execution_package"],
                "operational_capabilities": ["topology_execution"],
                "missing_capabilities": ["topology_candidate_support"],
                "maturity_level": "PARTIALLY_OPERATIONAL",
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE DOMAIN INTELLIGENCE REPORT" in report
    assert report.index("COGNITIVE KNOWLEDGE DOMAINS REPORT") < report.index("COGNITIVE DOMAIN INTELLIGENCE REPORT")
    assert report.index("COGNITIVE DOMAIN INTELLIGENCE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Domain Name: Topology Domain" in report
    assert "Semantic Capabilities: bridge_creation, topology_change" in report
    assert "Operational Capabilities: topology_execution" in report
    assert "Domain Dependencies: Spatial Domain, Identity Domain" in report
    assert "Mental Models: Topology Reasoning" in report
    assert "Program Blueprints: topology_program" in report
    assert "Execution Packages: topology_execution_package" in report
    assert "Missing Capabilities: topology_candidate_support" in report
    assert "Domain Readiness: PARTIALLY_OPERATIONAL" in report


def test_normal_report_exposes_cognitive_domain_lifecycle():
    state = _report_state()
    state["COGNITIVE_DOMAIN_INTELLIGENCE_REPORT"] = {
        "domain_intelligence": [
            {
                "domain_id": "domain:spatial",
                "domain_name": "Spatial Domain",
                "semantic_capabilities": ["relative_position"],
                "mental_models": ["Spatial Reasoning"],
            },
            {
                "domain_id": "domain:geometry",
                "domain_name": "Geometry Domain",
                "semantic_capabilities": ["shape_geometry"],
                "mental_models": ["Geometry Reasoning"],
            },
            {
                "domain_id": "domain:physics",
                "domain_name": "Physics Domain",
                "semantic_capabilities": ["gravity", "falling", "collision"],
                "mental_models": ["Gravity Simulation"],
                "program_blueprints": ["physics_program"],
                "missing_capabilities": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                ],
                "required_domains": ["Spatial Domain", "Geometry Domain"],
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE DOMAIN LIFECYCLE REPORT" in report
    assert report.index("COGNITIVE DOMAIN INTELLIGENCE REPORT") < report.index("COGNITIVE DOMAIN LIFECYCLE REPORT")
    assert report.index("COGNITIVE DOMAIN LIFECYCLE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Domain Name: Physics Domain" in report
    assert "Lifecycle Stage: PROGRAM_DEFINED" in report
    assert "Maturity Level: DEVELOPING" in report
    assert "Semantic=READY" in report
    assert "Mental Models=READY" in report
    assert "Programs=READY" in report
    assert "Execution=NOT_READY" in report
    assert "Candidate=NOT_READY" in report
    assert "Dependencies: Spatial Domain, Geometry Domain" in report
    assert "Missing Capabilities: gravity_execution_package, gravity_candidate_support" in report
    assert "Lifecycle Failures: EXECUTION_DEFINED:physics_execution_package_missing" in report


def test_normal_report_exposes_cognitive_domain_interaction():
    state = _report_state()
    state["COGNITIVE_DOMAIN_LIFECYCLE_REPORT"] = {
        "domain_registry": [
            {
                "domain_name": "Physics Domain",
                "semantic_capability_evolution": ["gravity"],
                "required_domains": ["Spatial Domain", "Geometry Domain"],
                "operational_capability_evolution": ["object_motion_reasoning"],
            },
            {
                "domain_name": "Spatial Domain",
                "semantic_capability_evolution": ["relative_position"],
            },
            {
                "domain_name": "Geometry Domain",
                "semantic_capability_evolution": ["object_shape"],
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE DOMAIN INTERACTION REPORT" in report
    assert report.index("COGNITIVE DOMAIN LIFECYCLE REPORT") < report.index("COGNITIVE DOMAIN INTERACTION REPORT")
    assert report.index("COGNITIVE DOMAIN INTERACTION REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Domain Name: Physics Domain" in report
    assert "Collaborating Domains: Spatial Domain, Geometry Domain" in report
    assert "Shared Capabilities: object_motion_reasoning" in report
    assert "Private Capabilities: collision_simulation" in report
    assert "Dependency Relationships: Spatial Domain, Geometry Domain" in report
    assert "Operational Capability Composition: Object Falling Simulation" in report
    assert "Cross-Domain Readiness:" in report
    assert "Operational Capability Lifecycle Count:" in report
    assert "Capability Promotion Candidates:" in report
    assert "Sandbox Operational Capabilities:" in report
    assert "Reusable Operational Capabilities:" in report
    assert "Capability Organisms:" in report
    assert "Emerging Capabilities:" in report
    assert "Capability Economy Watch:" in report
    assert "Capability Lifecycle:" in report
    assert "Capability Promotion:" in report
    assert "Capability Growth:" in report
    assert "Capability Identity:" in report
    assert "Capability Economy:" in report
    assert "Capability Resource Budget:" in report
    assert "Blocking Stage:" in report
    assert "Governance:" in report
    assert "Missing Collaborative Capabilities: Not Available" in report


def test_normal_report_exposes_cognitive_domain_governance():
    state = _report_state()
    state["COGNITIVE_DOMAIN_LIFECYCLE_REPORT"] = {
        "domain_registry": [
            {
                "domain_name": "Transformation Domain",
                "lifecycle_stage": "PROGRAM_DEFINED",
                "maturity_level": "DEVELOPING",
                "semantic_capability_evolution": ["rotation", "gravity"],
                "required_domains": ["Geometry Domain"],
            },
            {
                "domain_name": "Geometry Domain",
                "semantic_capability_evolution": ["object_shape"],
            },
        ],
    }
    state["COGNITIVE_DOMAIN_INTERACTION_REPORT"] = {
        "domain_interaction_reports": [],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE DOMAIN GOVERNANCE REPORT" in report
    assert report.index("COGNITIVE DOMAIN INTERACTION REPORT") < report.index("COGNITIVE DOMAIN GOVERNANCE REPORT")
    assert report.index("COGNITIVE DOMAIN GOVERNANCE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Domain Name: Transformation Domain" in report
    assert "Governance Status: BOUNDARY_VIOLATION" in report
    assert "Semantic Integrity:" in report
    assert "Ownership Integrity:" in report
    assert "Dependency Integrity:" in report
    assert "Domain Health Score:" in report
    assert "Boundary Violations:" in report


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
    assert "Source Diversity Bottleneck:" in report
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
    assert "Executable Concepts: 13" in report
    assert "Unsupported Concepts: 5" in report
    assert "Coverage Status: HIGH" in report
    assert "Unsupported Operations:" in report
    assert "preserve_shape" in report
    assert "density_modulation" in report


def test_report_marks_executable_coverage_not_measurable_without_concept_inputs():
    state = _report_state()
    state["generated_concepts"] = 18
    state["TRANSFORMATION_SYNTHESIS_REPORT"].pop(
        "detected_concepts",
        None,
    )
    state["TRANSFORMATION_SYNTHESIS_REPORT"].pop(
        "semantic_to_transformation_compilation_report",
    )

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Generated Concepts: 18" in report
    assert "Measured Concepts: 0" in report
    assert "Coverage State: NOT_MEASURABLE" in report
    assert "Coverage: Not Available" in report
    assert "Coverage Status: NOT_MEASURABLE" in report
    assert "Measurement Blocker: NO_UNIFIED_CONCEPT_INPUT" in report


def test_report_uses_lifecycle_concepts_for_executable_coverage():
    state = _report_state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"].pop(
        "detected_concepts",
        None,
    )
    state["TRANSFORMATION_SYNTHESIS_REPORT"].pop(
        "semantic_to_transformation_compilation_report",
    )
    state["concept_lifecycle_report"] = {
        "concepts": [
            {"concept": "component_splitting"},
            {"concept": "connectivity_change"},
            {"concept": "topology_change"},
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Measured Concepts: 3" in report
    assert "Executable Concepts: 2" in report
    assert "Unsupported Concepts: 1" in report
    assert "component_splitting" in report


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
