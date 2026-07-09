from runtime.cognitive_runtime.execution_binding import ExecutionBindingLayer
from runtime.metrics.runtime_metric_synchronizer import RuntimeMetricSynchronizer


def _execution(execution_id="reasoning_runtime:1", duration=0.025):
    return {
        "execution_id": execution_id,
        "runtime_name": "Reasoning Runtime",
        "module_name": "reasoning_runtime",
        "execution_start": "2026-07-08T10:00:00+00:00",
        "execution_end": "2026-07-08T10:00:00.025000+00:00",
        "duration_seconds": duration,
        "elapsed_seconds": duration,
        "cpu_time": 0.02,
        "memory_cost": 512,
        "lifecycle_events": [{"stage": "COMPLETED"}],
        "status": "COMPLETED",
        "completion_reason": "completed",
    }


def test_execution_binding_transfers_lifecycle_contract_and_telemetry():
    registry = {
        "reasoning_runtime": {
            "execution_id": "reasoning_runtime:1",
            "owner": "reasoning_runtime",
            "timing_metric": "reasoning_time_seconds",
            "duration_seconds": 0.0,
            "metrics": {},
        }
    }

    report = ExecutionBindingLayer().bind(
        registry,
        {"executions": [_execution()]},
    )

    entry = registry["reasoning_runtime"]
    assert entry["duration_seconds"] == 0.025
    assert entry["execution_start"]
    assert entry["execution_end"]
    assert entry["cpu_time"] == 0.02
    assert entry["memory_cost"] == 512
    assert entry["lifecycle_events"]
    assert entry["status"] == "COMPLETED"
    assert entry["completion_reason"] == "completed"
    assert entry["telemetry_source"] == "runtime_lifecycle"
    assert entry["last_binding_timestamp"]
    assert entry["metrics"]["reasoning_time_seconds"] == 0.025
    assert report["EXECUTION_BINDING_REPORT"] is True
    assert report["registry_synchronization"] == "SYNCHRONIZED"
    assert report["binding_coverage"] == 1.0
    assert report["timing_coverage"] == 1.0


def test_bound_registry_is_a_metric_synchronization_source():
    registry = {
        "reasoning_runtime": {
            "execution_id": "reasoning_runtime:1",
            "owner": "reasoning_runtime",
            "timing_metric": "reasoning_time_seconds",
            "duration_seconds": 0.0,
            "metrics": {},
        }
    }
    lifecycle = {"executions": [_execution()]}
    ExecutionBindingLayer().bind(registry, lifecycle)

    result = RuntimeMetricSynchronizer().synchronize(
        {"reasoning_time_seconds": 0.0},
        lifecycle,
        runtime_registry=registry,
    )

    assert result["performance_report"]["reasoning_time_seconds"] == 0.025
    bound = result["RUNTIME_METRIC_SYNCHRONIZATION_REPORT"]["metrics_bound"]
    assert bound[0]["measurement_source"] == "execution_binding_layer"


def test_binding_failures_are_explicit():
    registry = {
        "reasoning_runtime": {
            "execution_id": "reasoning_runtime:missing",
            "owner": "reasoning_runtime",
            "timing_metric": "reasoning_time_seconds",
        }
    }

    report = ExecutionBindingLayer().bind(registry, {"executions": []})

    assert report["registry_synchronization"] == "UNSYNCHRONIZED"
    assert report["failed_bindings"][0]["binding_errors"] == ["Lifecycle missing"]
