from copy import deepcopy
import json

from runtime.reporting.compact_report_compression_engine import (
    CompactReportCompressionEngine,
)
from runtime.reporting.compact_report_builder import CompactReportBuilder


class FakeArray:
    shape = (20, 20)
    dtype = "int64"

    def tolist(self):
        return [[1] * 20 for _ in range(20)]

    def __eq__(self, other):
        return isinstance(other, FakeArray)


def _canonical_report():
    repeated = {
        "runtime_id": "runtime.alpha",
        "status": "completed",
        "duration": 1.25,
        "telemetry": {"confidence": 0.9},
    }
    return {
        "runtime_status": "completed",
        "tasks_executed": 4,
        "successful_tasks": 3,
        "failed_tasks": 1,
        "warnings": ["search entropy remains zero"],
        "errors": ["metric rejected"],
        "execution_coverage": 0.75,
        "snapshot_coverage": 0.5,
        "lifecycle_coverage": 0.75,
        "total_runtime_seconds": 12.5,
        "generated_concepts": 6,
        "generated_programs": 3,
        "validated_programs": 2,
        "average_program_confidence": 0.81,
        "overall_search_quality": 0.72,
        "search_efficiency": 0.67,
        "search_coverage": 0.75,
        "search_entropy": 0,
        "runtime_timing_summary": {
            "total_wall_time": 12.5,
            "active_compute_time": 10.0,
            "untracked_time": 0.5,
            "timing_coverage": 0.96,
        },
        "stage_timing_summary": [
            {
                "stage_name": "Reasoning",
                "duration_seconds": 4.0,
                "percentage_of_total_runtime": 32.0,
                "timing_scope": "RUNTIME_STAGE",
                "timing_status": "OBSERVED",
            },
            {
                "stage_name": "Search",
                "duration_seconds": 3.0,
                "percentage_of_total_runtime": 24.0,
                "timing_scope": "RUNTIME_STAGE",
                "timing_status": "OBSERVED",
            },
        ],
        "top_time_consumers": [
            {
                "rank": 1,
                "stage_name": "Reasoning",
                "duration_seconds": 4.0,
                "percentage_of_total_runtime": 32.0,
            },
        ],
        "timing_coverage": 0.96,
        "untracked_time": 0.5,
        "active_compute_time": 10.0,
        "report_generation_time": 0.2,
        "finalization_time": 0.3,
        "runtime_metric_confidence_by_id": {
            "metric.good": 0.91,
            "metric.low": 0.25,
            "metric.bad": {"confidence": 0.2, "status": "rejected"},
        },
        "execution_timeline": [
            {"event": "created", "timestamp": "2026-07-15T00:00:00Z"},
            {"event": "started", "timestamp": "2026-07-15T00:00:01Z"},
            {"event": "completed", "timestamp": "2026-07-15T00:00:02Z"},
            {"event": "failed", "timestamp": "2026-07-15T00:00:03Z"},
        ],
        "snapshot_payloads": [
            {
                "snapshot_type": "runtime",
                "snapshot_generation_success": True,
                "payload": {"large": list(range(100))},
            },
            {
                "snapshot_type": "final",
                "snapshot_generation_success": False,
                "payload": {"large": list(range(100))},
            },
        ],
        "successful_bindings": [
            {"runtime_id": "a", "status": "bound", "latency": 0.1},
            {"runtime_id": "b", "status": "failed", "latency": 0.2},
        ],
        "execution_registry": {
            "a": {"status": "completed"},
            "b": {"status": "failed"},
        },
        "execution_tree": {
            "first_child": repeated,
            "second_child": deepcopy(repeated),
        },
        "knowledge_fabric": {
            "fabric_links": ["a:b", "b:c"],
            "fabric_bridges": ["bridge"],
            "cross_domain_links": ["vision:memory"],
            "orphan_concepts": ["orphan"],
        },
        "array_payload": FakeArray(),
    }


def _compress(profile="normal", **kwargs):
    return CompactReportCompressionEngine().compress(
        _canonical_report(),
        profile=profile,
        **kwargs,
    )


def test_heavy_key_detection_and_measurable_ratio():
    result = _compress()
    compressed = result["compressed_report"]
    stats = result["compression_statistics"]

    assert "runtime_metric_confidence_by_id" not in compressed
    assert "runtime_metric_confidence_by_id_summary" in compressed
    assert stats["heavy_keys_detected"] > 0
    assert stats["heavy_keys_removed"] > 0
    assert stats["actual_size_after"] < stats["actual_size_before"]
    assert stats["report_compression_ratio"] > 0


def test_array_summarization_and_timeline_meaning():
    result = _compress()
    compressed = result["compressed_report"]
    timeline = compressed["execution_timeline_summary"]

    assert compressed["array_payload"]["array_summary"] is True
    assert timeline["total_events"] == 4
    assert timeline["created_events"] == 1
    assert timeline["started_events"] == 1
    assert timeline["completed_events"] == 1
    assert timeline["failed_events"] == 1
    assert result["compression_statistics"]["arrays_summarized"] > 0


def test_repeated_report_collapse_and_duplicate_stats():
    result = _compress()
    tree = result["compressed_report"]["execution_tree"]
    stats = result["compression_statistics"]

    assert tree["second_child"]["collapsed_duplicate_report"] is True
    assert stats["repeated_reports_collapsed"] > 0
    assert stats["duplicate_fields_removed"] > 0


def test_snapshot_metric_binding_and_execution_registry_compression():
    compressed = _compress()["compressed_report"]

    snapshots = compressed["snapshot_payloads_summary"]
    metric_map = compressed["runtime_metric_confidence_by_id_summary"]
    bindings = compressed["successful_bindings_summary"]
    registry = compressed["execution_registry_summary"]

    assert snapshots["snapshot_count"] == 2
    assert snapshots["latest_snapshot_type"] == "final"
    assert snapshots["snapshot_generation_failures"] == 1
    assert metric_map["validated_metric_count"] == 2
    assert metric_map["rejected_metric_count"] == 1
    assert "metric.low" in metric_map["metrics_below_threshold"]
    assert bindings["bound_runtime_count"] == 1
    assert bindings["failed_binding_count"] == 1
    assert registry["runtime_count"] == 2
    assert registry["failed_runtime_count"] == 1


def test_anomaly_and_semantic_preservation():
    result = _compress()
    compressed = result["compressed_report"]
    stats = result["compression_statistics"]

    assert compressed["runtime_status"] == "completed"
    assert compressed["warnings"] == ["search entropy remains zero"]
    assert compressed["errors"] == ["metric rejected"]
    assert compressed["tasks_executed"] == 4
    assert compressed["average_program_confidence"] == 0.81
    assert compressed["overall_search_quality"] == 0.72
    assert compressed["fabric_links"] == ["a:b", "b:c"]
    assert "compression_warnings" in compressed
    assert stats["semantic_preservation_score"] == 1.0
    assert stats["critical_information_preserved"] is True


def test_deterministic_output_and_canonical_immutability():
    canonical = _canonical_report()
    original = deepcopy(canonical)
    engine = CompactReportCompressionEngine()

    first = engine.compress(canonical, profile="normal")
    second = engine.compress(canonical, profile="normal")

    assert canonical == original
    assert json.dumps(first["compressed_report"], sort_keys=True) == json.dumps(
        second["compressed_report"],
        sort_keys=True,
    )


def test_minimal_budget_and_technical_appendix_generation(tmp_path):
    result = CompactReportCompressionEngine(console_budgets={"MINIMAL": 600}).compress(
        _canonical_report(),
        profile="minimal",
        artifact_directory=tmp_path,
        write_appendix=True,
    )
    compressed = result["compressed_report"]
    stats = result["compression_statistics"]

    assert "runtime_status" in compressed
    assert "runtime_metric_confidence_by_id" not in compressed
    assert compressed["technical_appendix_available"] is True
    assert stats["technical_appendix_artifact_written"] is True
    assert (tmp_path / "runtime_technical_appendix.json").exists()


def test_compression_preserves_timing_summaries_by_report_level():
    normal = _compress(profile="normal")["compressed_report"]
    minimal = _compress(profile="minimal")["compressed_report"]

    assert "stage_timing_summary" in normal
    assert normal["stage_timing_summary"][0]["stage_name"] == "Reasoning"
    assert "runtime_timing_summary" in minimal
    assert "top_time_consumers" in minimal
    assert minimal["untracked_time"] == 0.5
    assert "stage_timing_summary" not in minimal


def test_compact_report_builder_surfaces_engine_statistics():
    compact = CompactReportBuilder().compact_context(
        _canonical_report(),
        level="normal",
    )
    stats = compact["compact_report"]

    assert stats["heavy_keys_removed"] > 0
    assert stats["arrays_summarized"] > 0
    assert stats["repeated_reports_collapsed"] > 0
    assert stats["report_compression_ratio"] > 0
    assert stats["critical_information_preserved"] is True


def test_anomaly_collection_handles_integer_dictionary_keys():
    compact = CompactReportBuilder().compact_context(
        {
            "runtime_status": "completed",
            "execution_coverage": 0.5,
            "nested_runtime_reports": {
                0: {
                    "route_coverage": 0.25,
                    "search_entropy": 0,
                },
                1: {
                    "warnings": ["integer keyed report entry"],
                },
            },
        },
        level="normal",
    )

    warnings = compact["compression_warnings"]
    assert any("nested_runtime_reports.0.route_coverage" in warning for warning in warnings)
    assert any("nested_runtime_reports.0.search_entropy" in warning for warning in warnings)
    assert any("nested_runtime_reports.1.warnings" in warning for warning in warnings)
