from runtime.metrics.runtime_metric_attribution_engine import (
    RuntimeMetricAttributionEngine,
)


def _instance(runtime_id, execution_id, parent=None, **values):
    payload = {
        "runtime_id": runtime_id,
        "execution_id": execution_id,
        "execution_parent": parent,
        "execution_start": "2026-07-14T10:00:01+00:00" if parent else "2026-07-14T10:00:00+00:00",
        "execution_end": "2026-07-14T10:00:02+00:00" if parent else "2026-07-14T10:00:03+00:00",
        "duration_seconds": 1.0 if parent else 3.0,
        "elapsed_seconds": 1.0 if parent else 3.0,
        "cpu_time": 0.01,
        "memory_usage": 512,
        "generated_concepts": 0,
        "generated_programs": 0,
        "generated_truth_candidates": 0,
        "generated_memory_entries": 0,
        "snapshots": [{"snapshot_id": f"{execution_id}:snapshot"}],
        "lifecycle_events": [{"status": "CREATED"}, {"status": "COMPLETED"}],
    }
    payload.update(values)
    return payload


def test_runtime_metric_attribution_records_required_contract_fields():
    report = RuntimeMetricAttributionEngine().build_report([
        _instance("execution_runtime", "root"),
        _instance("program_synthesis_runtime", "program", "root", generated_programs=2),
        _instance("truth_runtime", "truth", "root", generated_truth_candidates=3),
    ])

    records = report["verified_runtime_metrics"]
    required = {
        "metric_id",
        "metric_name",
        "runtime_owner",
        "execution_id",
        "measurement_scope",
        "measurement_start",
        "measurement_end",
        "measurement_duration",
        "measurement_source",
        "measurement_method",
        "measurement_confidence",
    }

    assert report["RUNTIME_METRIC_ATTRIBUTION_REPORT"] is True
    assert records
    assert all(required.issubset(record) for record in records)
    assert len({record["metric_id"] for record in records}) == len(records)
    assert report["runtime_metric_validation"]["validation_success"] is True
    assert report["runtime_metric_consistency"]["metric_ownership_consistency"] is True
    assert report["runtime_metric_coverage"]["coverage_score"] > 0.0


def test_parent_execution_does_not_own_child_output_metrics():
    report = RuntimeMetricAttributionEngine().build_report([
        _instance("execution_runtime", "root", generated_programs=4),
        _instance("program_synthesis_runtime", "program", "root", generated_programs=4),
    ])

    program_metrics = [
        record for record in report["verified_runtime_metrics"]
        if record["metric_name"] == "program_count"
    ]
    root_metrics = report["runtime_metric_breakdown"]["execution_runtime"]

    assert program_metrics
    assert {record["runtime_owner"] for record in program_metrics} == {
        "program_synthesis_runtime"
    }
    assert "program_count" not in {
        record["metric_name"] for record in root_metrics
    }
    assert report["runtime_metric_summary"]["runtime_owners"]["execution_runtime"][
        "parent_aggregation_only"
    ] is True
