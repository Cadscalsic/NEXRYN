from runtime.reporting.canonical_report_binding_engine import (
    BindingState,
    CanonicalReportBindingEngine,
    ReportFieldBinding,
)
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def _state():
    return {
        "runtime_status": "completed",
        "tasks_executed": 3,
        "successful_tasks": 3,
        "generated_concepts": 4,
        "generated_programs": 21,
        "truth_candidate_count": 2,
        "metric_attribution_state": {
            "metric_ownership_map": {"generated_programs": "Program Runtime"},
        },
        "runtime_snapshots": {
            "latest_snapshot_payload": {"payload_size": 12},
        },
        "PROGRAM_SYNTHESIS_REPORT": {
            "average_program_confidence": 0.6148,
            "highest_confidence": 0.91,
            "lowest_confidence": 0.42,
            "validation_distribution": {"VALID": 21},
        },
        "COGNITIVE_SEARCH_REPORT": {
            "overall_search_quality": 0.499,
            "search_efficiency": 0.5,
            "search_coverage": 0.7,
            "search_entropy": 0.33,
            "route_count": 5,
        },
        "RUNTIME_LIFECYCLE_REPORT": {
            "total_executions": 3,
            "completed_executions": 3,
            "execution_coverage": 1.0,
            "snapshot_coverage": 1.0,
            "lifecycle_coverage": 1.0,
        },
        "execution_timing": {
            "execution_timing_state": {
                "total_wall_time": 20.0,
                "cognitive_runtime_time": 15.0,
                "unattributed_time": 1.0,
                "timing_coverage": 0.95,
                "report_generation_time": 0.4,
                "finalization_time": 0.6,
            },
            "timing_records": [
                {
                    "execution_id": "old-exec",
                    "timing_scope": "SEARCH_TIME",
                    "timing_status": "OBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 99.0,
                },
                {
                    "timing_scope": "TASK_SELECTION_TIME",
                    "timing_status": "OBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 1.0,
                },
                {
                    "timing_scope": "GOVERNANCE_TIME",
                    "timing_status": "UNOBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 0.0,
                },
            ],
        },
        "performance_report": {
            "total_runtime_seconds": 20.0,
            "active_compute_time_seconds": 17.0,
            "untracked_runtime_seconds": 1.0,
            "stage_metrics": [
                {"stage_name": "program_synthesis", "total_duration": 3.0},
                {"stage_name": "evaluation", "total_duration": 0.5},
            ],
        },
    }


def _metadata():
    return {
        "system": "NEXRYN",
        "mode": "test",
        "profile": "unit",
        "execution_id": "exec-1",
        "timestamp": "2026-07-15T00:00:00Z",
        "execution_time": 1.25,
    }


def test_canonical_source_discovery_registers_known_sources():
    engine = CanonicalReportBindingEngine()

    sources = engine.discover_sources(_state(), runtime_metadata=_metadata())

    assert "execution_registry" in sources
    assert "metric_attribution_state" in sources
    assert "runtime_snapshots" in sources
    assert sources["program_registry"].payload["average_program_confidence"] == 0.6148


def test_field_binding_resolves_visible_values():
    result = CanonicalReportBindingEngine().bind(
        _state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert result["field_values"]["generated_programs"] == "21"
    assert result["field_values"]["overall_search_quality"] == "0.499"
    assert result["field_values"]["average_program_confidence"] == "0.6148"
    assert result["field_values"]["execution_coverage"] == "100%"


def test_generated_outputs_bind_from_semantic_synthesis_when_top_level_missing():
    state = _state()
    state.pop("generated_concepts")
    state.pop("generated_programs")
    state["semantic_concept_count"] = 8
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": [
            "bridge_creation",
            "component_connection",
            "connectivity_change",
            "topology_change",
        ],
        "candidate_count": 3,
        "generated_transformations": [
            {"steps": [{"operation": "connect_components"}]},
            {"steps": [{"operation": "construct_path"}]},
            {"steps": [{"operation": "repair_topology"}]},
        ],
        "semantic_to_transformation_compilation_report": {
            "semantic_to_transformation_compilation_success": False,
            "detected_intents": [
                "bridge_creation",
                "component_connection",
                "connectivity_change",
                "topology_change",
            ],
            "execution_intents": [
                {
                    "intent": "component_connection",
                    "operation": "connect_components",
                }
            ],
            "candidate_count": 0,
        },
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    semantic_summary = result["field_bindings"]["semantic_compilation_summary"]["value"]

    assert result["field_values"]["generated_concepts"] == "8"
    assert result["field_values"]["generated_programs"] == "3"
    assert semantic_summary["generated_concepts"] == 8
    assert semantic_summary["generated_programs"] == 3
    assert semantic_summary["execution_intent_count"] == 1


def test_duplicate_owner_and_conflicting_binding_detection():
    bindings = [
        ReportFieldBinding(
            "generated_programs",
            "Program Runtime",
            "report_state",
            ("NORMAL",),
            source_fields=("generated_programs",),
        ),
        ReportFieldBinding(
            "generated_programs",
            "Search Runtime",
            "search_metrics",
            ("NORMAL",),
            source_fields=("generated_programs",),
        ),
    ]

    errors = CanonicalReportBindingEngine(bindings).validate_field_registry()

    assert "conflicting_binding:generated_programs" in errors
    assert "duplicate_owner:generated_programs" in errors
    assert "conflicting_source:generated_programs" in errors


def test_visibility_validation_and_hidden_policy_state():
    bindings = [
        ReportFieldBinding(
            "metric_ownership_map",
            "Metric Attribution",
            "metric_attribution_state",
            ("DIAGNOSTIC",),
            source_fields=("metric_ownership_map",),
            representation_type="map",
        ),
        ReportFieldBinding(
            "bad_visibility",
            "Representation",
            "report_state",
            ("SIDEWAYS",),
        ),
    ]
    engine = CanonicalReportBindingEngine(bindings)

    result = engine.bind(_state(), report_level="normal")

    hidden = result["field_bindings"]["metric_ownership_map"]
    assert hidden["binding_status"] == BindingState.HIDDEN.value
    assert hidden["display_value"] == "Hidden by Report Policy"
    assert "invalid_visibility_policy:bad_visibility" in (
        result["binding_diagnostics"]["validation_errors"]
    )


def test_compression_and_externalization_states():
    result = CanonicalReportBindingEngine().bind(
        _state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    compressed = result["field_bindings"]["validation_distribution"]
    externalized = result["field_bindings"]["metric_ownership_map"]

    assert compressed["binding_status"] == BindingState.COMPRESSED.value
    assert compressed["display_value"] == "Compressed Summary: 1 fields"
    assert externalized["binding_status"] == BindingState.EXTERNALIZED.value
    assert externalized["display_value"] == "Externalized to Technical Appendix"


def test_required_field_validation_and_invalid_representation_type():
    bindings = [
        ReportFieldBinding(
            "generated_programs",
            "Program Runtime",
            "report_state",
            ("NORMAL",),
            representation_type="count",
            source_fields=("missing_program_count",),
            required=True,
        ),
        ReportFieldBinding(
            "bad_representation",
            "Representation",
            "report_state",
            ("NORMAL",),
            representation_type="mystery",
        ),
    ]

    result = CanonicalReportBindingEngine(bindings).bind(
        _state(),
        report_level="normal",
    )
    errors = result["binding_diagnostics"]["validation_errors"]

    assert result["field_bindings"]["generated_programs"]["binding_status"] == (
        BindingState.NOT_AVAILABLE.value
    )
    assert "required_field_not_bound:generated_programs" in errors
    assert "invalid_representation_type:bad_representation" in errors


def test_report_level_compatibility_and_deterministic_resolution():
    engine = CanonicalReportBindingEngine()

    first = engine.bind(_state(), runtime_metadata=_metadata(), report_level="normal")
    second = engine.bind(_state(), runtime_metadata=_metadata(), report_level="normal")

    assert first["field_values"] == second["field_values"]
    assert {
        name: field["binding_state"]
        for name, field in first["report_field_registry"].items()
    } == {
        name: field["binding_state"]
        for name, field in second["report_field_registry"].items()
    }
    assert first["field_bindings"]["snapshot_payload"]["binding_status"] == (
        BindingState.EXTERNALIZED.value
    )


def test_legacy_unknown_value_elimination_in_binding_and_final_report():
    state = _state()
    state["generated_programs"] = "UNKNOWN"

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert result["field_values"]["generated_programs"] == "Not Available"
    assert "UNKNOWN" not in report
    assert "Generated Programs: Not Available" in report


def test_prediction_provenance_binding_resolves_decision_summary():
    state = _state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": ["rotation", "reflection"],
        "candidate_count": 3,
        "transformation_confidence": 0.91,
        "transformation_accuracy": 1.0,
        "selected_program": {
            "step_count": 1,
            "steps": [
                {
                    "operation": "mirror_vertical",
                    "parameters": {"axis": "vertical"},
                }
            ],
        },
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata={"execution_id": "exec-1"},
        report_level="normal",
    )
    summary = result["field_bindings"]["prediction_provenance_summary"]["value"]

    assert summary["decision_owner"] == "Transformation Synthesis Engine"
    assert summary["prediction_source"] == "transformation_synthesis"
    assert summary["winning_candidate"] == "mirror_vertical"
    assert summary["generated_concept_count"] == 2
    assert summary["candidate_count"] == 3
    assert summary["program_validation"] == "SUCCESS"


def test_candidate_arena_binding_detects_single_source_dominance():
    state = _state()
    state["ADAPTIVE_REUSE_REPORT"] = {
        "reuse_success_rate": 1.0,
        "reused_programs": [
            {
                "steps": [
                    {"operation": "reuse_transform", "parameters": {}}
                ],
                "step_count": 1,
            }
        ],
    }
    state["PREDICTION_PROVENANCE_REPORT"] = {
        "prediction_source": "adaptive_reuse",
        "decision_owner": "Adaptive Reuse Layer",
        "winning_candidate": "reuse_transform",
        "decision_confidence": 1.0,
    }
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

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata={"execution_id": "exec-1"},
        report_level="normal",
    )
    summary = result["field_bindings"]["candidate_arena_summary"]["value"]
    decision = result["field_bindings"]["prediction_provenance_summary"]["value"]

    assert summary["arena_state"] == "SINGLE_SOURCE_DOMINANCE"
    assert summary["candidate_count"] == 1
    assert summary["attempted_candidate_count"] == 2
    assert summary["explicit_rejection_count"] == 1
    assert summary["competitor_sources"] == ["adaptive_reuse"]
    assert summary["winner_takes_all_detected"] is True
    assert summary["dominance_source"] == "adaptive_reuse"
    assert summary["source_status"]["semantic_to_transformation_compiler"] == "BLOCKED"
    assert summary["source_outcomes"][0]["source"] == "semantic_to_transformation_compiler"
    assert summary["source_outcomes"][0]["status"] == "REJECTED"
    assert decision["compiler_attempted"] is True
    assert "Semantic Compilation" in decision["decision_pipeline"]


def test_selected_semantic_compiler_without_report_is_explicit_rejection():
    state = _state()
    state["tool_selection_report"] = {
        "enabled_tools": ["semantic_to_transformation_compiler"],
    }
    state["ADAPTIVE_REUSE_REPORT"] = {
        "reuse_success_rate": 1.0,
        "reused_programs": [
            {
                "steps": [
                    {"operation": "reuse_transform", "parameters": {}}
                ],
                "step_count": 1,
            }
        ],
    }
    state["PREDICTION_PROVENANCE_REPORT"] = {
        "prediction_source": "adaptive_reuse",
        "decision_owner": "Adaptive Reuse Layer",
        "winning_candidate": "reuse_transform",
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata={"execution_id": "exec-1"},
        report_level="normal",
    )
    semantic = result["field_bindings"]["semantic_compilation_summary"]["value"]
    decision = result["field_bindings"]["prediction_provenance_summary"]["value"]
    arena = result["field_bindings"]["candidate_arena_summary"]["value"]
    proposal = result["field_bindings"]["candidate_proposal_summary"]["value"]

    assert semantic["compiler_selected"] is True
    assert semantic["compiler_triggered"] is True
    assert semantic["compilation_status"] == "REQUIRED_REPORT_MISSING"
    assert decision["compiler_attempted"] is True
    assert "Semantic Compilation" in decision["decision_pipeline"]
    assert arena["attempted_candidate_count"] == 2
    assert arena["explicit_rejection_count"] == 1
    assert arena["source_status"]["semantic_to_transformation_compiler"] == "BLOCKED"
    assert proposal["proposal_phase_entered"] is True
    assert proposal["explicit_rejection_count"] == 1
    assert proposal["sources_rejected"] == ["semantic_to_transformation_compiler"]
    assert any(
        outcome["source"] == "semantic_to_transformation_compiler"
        and outcome["status"] == "REJECTED"
        for outcome in arena["source_outcomes"]
    )


def test_executable_semantic_coverage_identifies_unsupported_clusters():
    state = _state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": [
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
        ],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    coverage = result["field_bindings"][
        "executable_semantic_coverage_summary"
    ]["value"]

    assert coverage["generated_concepts"] == 18
    assert coverage["executable_concepts"] == 7
    assert coverage["unsupported_concepts"] == 11
    assert coverage["coverage_status"] == "LOW"
    assert "Spatial And Motion" in coverage["missing_cluster_counts"]
    assert "density_modulation" in coverage["unsupported_operations"]
    assert "connect_components" in coverage["supported_operations"]


def test_canonical_timing_bindings_use_existing_timing_sources():
    result = CanonicalReportBindingEngine().bind(
        _state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    fields = result["field_bindings"]

    assert fields["stage_timing_summary"]["canonical_source"] == "execution_timing_state"
    assert fields["runtime_timing_summary"]["canonical_source"] == "execution_timing_state"
    assert fields["top_time_consumers"]["canonical_source"] == "execution_timing_state"
    assert fields["active_compute_time"]["value"] == 17.0
    assert fields["untracked_time"]["value"] == 1.0
    assert fields["timing_coverage"]["display_value"] == "95%"
    stage_rows = fields["stage_timing_summary"]["value"]
    assert all(row["duration_seconds"] >= 0.0 for row in stage_rows)
    assert not any(row["stage_name"] == "Governance" for row in stage_rows)
    assert not any(row["duration_seconds"] == 99.0 for row in stage_rows)
    assert len({row["stage_name"] for row in stage_rows}) == len(stage_rows)
    assert stage_rows[0]["relationship_type"] == "ROOT"
    ranking = fields["resource_consumption_ranking"]["value"]
    assert [row["exclusive_duration"] for row in ranking] == sorted(
        [row["exclusive_duration"] for row in ranking],
        reverse=True,
    )
    assert sum(row["percentage_of_active_compute"] for row in ranking) <= 100.0001
    assert fields["top_time_consumers"]["value"][0]["stage_name"] == "Program Synthesis"


def test_timing_not_available_only_when_source_genuinely_missing():
    state = _state()
    state.pop("execution_timing")
    state["performance_report"] = {}

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata={},
        report_level="normal",
    )

    assert result["field_bindings"]["active_compute_time"]["binding_status"] == (
        BindingState.NOT_AVAILABLE.value
    )
    assert result["field_bindings"]["stage_timing_summary"]["binding_status"] == (
        BindingState.BOUND.value
    )
    assert result["field_bindings"]["stage_timing_summary"]["value"] == []
