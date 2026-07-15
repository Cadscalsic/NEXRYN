from copy import deepcopy

from runtime.reporting.canonical_report_binding_engine import (
    canonical_report_binding_engine,
)
from runtime.reporting.compact_report_compression_engine import (
    compact_report_compression_engine,
)
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer
from runtime.reporting.representation_layer_validation_engine import (
    RepresentationLayerValidationEngine,
)


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


def _artifacts(report_level="normal"):
    state = _state()
    metadata = _metadata()
    binding = canonical_report_binding_engine.bind(
        state,
        runtime_metadata=metadata,
        report_level=report_level,
    )
    bound_state = dict(state)
    bound_state["CANONICAL_REPORT_BINDING"] = binding
    bound_state["report_field_registry"] = binding["report_field_registry"]
    bound_state["canonical_source_registry"] = binding[
        "canonical_source_registry"
    ]
    bound_state["binding_diagnostics"] = binding["binding_diagnostics"]
    compressed = compact_report_compression_engine.compress(
        bound_state,
        profile=report_level,
    )["compressed_report"]
    rendered = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=metadata,
        report_level=report_level,
    )
    return state, binding, compressed, rendered


def test_field_validation_and_representation_completeness():
    state, binding, compressed, rendered = _artifacts()

    report = RepresentationLayerValidationEngine().validate(
        state,
        binding_report=binding,
        compressed_report=compressed,
        rendered_report=rendered,
        report_level="normal",
    )

    assert report["representation_validation_success"] is True
    assert report["FIELD_VALIDATION"]["validation_success"] is True
    assert report["REPRESENTATION_COMPLETENESS"]["missing_fields"] == []
    assert report["representation_coverage"] == 1.0
    assert report["visible_field_count"] > 0


def test_canonical_source_validation_detects_missing_source():
    state, binding, compressed, rendered = _artifacts()
    broken = deepcopy(binding)
    broken["canonical_source_registry"].pop("program_registry")

    report = RepresentationLayerValidationEngine().validate(
        state,
        binding_report=broken,
        compressed_report=compressed,
        rendered_report=rendered,
    )

    assert report["representation_validation_success"] is False
    assert "canonical_source_missing:average_program_confidence" in (
        report["validation_errors"]
    )


def test_visibility_validation_blocks_diagnostic_exposure_in_normal_report():
    state, binding, compressed, rendered = _artifacts()
    exposed = deepcopy(compressed)
    exposed["metric_ownership_map"] = {"generated_programs": "Program Runtime"}

    report = RepresentationLayerValidationEngine().validate(
        state,
        binding_report=binding,
        compressed_report=exposed,
        rendered_report=rendered,
        report_level="normal",
    )

    assert report["report_level_compliance"] is False
    assert "diagnostic_field_exposed:metric_ownership_map" in (
        report["validation_errors"]
    )


def test_compression_validation_detects_heavy_raw_structure_and_bad_ratio():
    state, binding, compressed, rendered = _artifacts()
    bad_compressed = deepcopy(compressed)
    bad_compressed["execution_registry"] = {
        "exec-1": {"status": "completed"},
    }
    bad_compressed["compact_report"]["actual_size_before"] = 100
    bad_compressed["compact_report"]["actual_size_after"] = 75
    bad_compressed["compact_report"]["report_compression_ratio"] = 0.9

    report = RepresentationLayerValidationEngine().validate(
        state,
        binding_report=binding,
        compressed_report=bad_compressed,
        rendered_report=rendered,
    )

    assert "heavy_structure_not_compressed:execution_registry" in (
        report["validation_errors"]
    )
    assert "compression_ratio_mismatch" in report["validation_errors"]


def test_duplication_detection_finds_duplicate_report_field():
    state, binding, compressed, rendered = _artifacts()
    duplicated = deepcopy(binding)
    duplicated["field_bindings"]["duplicate_generated_programs"] = deepcopy(
        duplicated["field_bindings"]["generated_programs"]
    )

    report = RepresentationLayerValidationEngine().validate(
        state,
        binding_report=duplicated,
        compressed_report=compressed,
        rendered_report=rendered,
    )

    assert report["duplicate_field_count"] >= 1
    assert "duplicate_report_field:generated_programs" in (
        report["validation_errors"]
    )


def test_required_field_completeness_detects_missing_binding():
    state, binding, compressed, rendered = _artifacts()
    incomplete = deepcopy(binding)
    incomplete["field_bindings"].pop("generated_programs")

    report = RepresentationLayerValidationEngine().validate(
        state,
        binding_report=incomplete,
        compressed_report=compressed,
        rendered_report=rendered,
    )

    assert "generated_programs" in (
        report["REPRESENTATION_COMPLETENESS"]["missing_fields"]
    )


def test_report_level_compliance_allows_diagnostic_externalization():
    state, binding, compressed, rendered = _artifacts(report_level="debug")

    report = RepresentationLayerValidationEngine().validate(
        state,
        binding_report=binding,
        compressed_report=compressed,
        rendered_report=rendered,
        report_level="debug",
    )

    assert report["VISIBILITY_VALIDATION"]["report_level"] == "DIAGNOSTIC"
    assert report["VISIBILITY_VALIDATION"]["validation_success"] is True


def test_human_readability_validation_blocks_raw_structures_and_unknown():
    state, binding, compressed, _rendered = _artifacts()
    raw_report = (
        "<<< NEXRYN_REPORT_BEGIN >>>\n"
        "\nREPORT HEADER\n"
        "{'raw': 'dict'}\n"
        "Generated Programs: UNKNOWN\n"
        "<<< NEXRYN_REPORT_END >>>"
    )

    report = RepresentationLayerValidationEngine().validate(
        state,
        binding_report=binding,
        compressed_report=compressed,
        rendered_report=raw_report,
    )

    assert "raw_python_structure_detected" in report["validation_errors"]
    assert "unknown_value_with_canonical_data" in report["validation_errors"]


def test_architectural_integrity_detects_registry_owner_mismatch():
    state, binding, compressed, rendered = _artifacts()
    broken = deepcopy(binding)
    broken["report_field_registry"]["generated_programs"]["owner"] = (
        "Search Runtime"
    )

    report = RepresentationLayerValidationEngine().validate(
        state,
        binding_report=broken,
        compressed_report=compressed,
        rendered_report=rendered,
    )

    assert "owner_registry_mismatch:generated_programs" in (
        report["validation_errors"]
    )


def test_deterministic_representation_validation():
    state, binding, compressed, rendered = _artifacts()
    engine = RepresentationLayerValidationEngine()

    first = engine.validate(
        state,
        binding_report=binding,
        compressed_report=compressed,
        rendered_report=rendered,
    )
    second = engine.validate(
        state,
        binding_report=binding,
        compressed_report=compressed,
        rendered_report=rendered,
    )

    assert first["representation_health_score"] == second[
        "representation_health_score"
    ]
    assert first["validation_errors"] == second["validation_errors"]
    assert first["representation_states"] == second["representation_states"]
