from runtime.metrics.runtime_metric_synchronizer import RuntimeMetricSynchronizer


def _execution(runtime_name, module_name, elapsed_seconds):
    execution_id = f"{module_name}:{elapsed_seconds}"
    return {
        "execution_id": execution_id,
        "module_name": module_name,
        "runtime_name": runtime_name,
        "execution_end": "2026-07-07 00:00:00",
        "elapsed_seconds": elapsed_seconds,
        "duration_seconds": elapsed_seconds,
        "wall_clock_time": elapsed_seconds,
        "status": "COMPLETED",
    }


def test_lifecycle_timings_repair_zero_runtime_metrics():
    lifecycle_report = {
        "executions": [
            _execution("Dependency Runtime", "dependency_execution_bridge", 0.011),
            _execution("Process Runtime", "process_context_runtime", 0.012),
            _execution("Causal Runtime", "causal_context_runtime", 0.013),
            _execution("Truth Runtime", "truth_runtime", 0.014),
            _execution("Adaptive Reuse Runtime", "adaptive_reuse_layer", 0.015),
            _execution("Memory Runtime", "memory_runtime", 0.016),
            _execution("Reasoning Runtime", "reasoning_orchestrator", 0.017),
            _execution("Evaluation Runtime", "evaluation_controller", 0.018),
        ]
    }
    performance_report = {
        "dependency_reasoning_time_seconds": 0.0,
        "process_generation_time": 0.0,
        "causal_generation_time": 0.0,
        "truth_time_seconds": 0.0,
        "reuse_time_seconds": 0.0,
        "memory_time_seconds": 0.0,
        "reasoning_time_seconds": 0.0,
        "evaluation_time_seconds": 0.0,
        "canonical_metrics": {
            "dependency_reasoning_time_seconds": 0.0,
        },
    }

    result = RuntimeMetricSynchronizer().synchronize(
        performance_report=performance_report,
        lifecycle_report=lifecycle_report,
    )

    report = result["performance_report"]
    sync_report = result["RUNTIME_METRIC_SYNCHRONIZATION_REPORT"]

    assert report["dependency_reasoning_time_seconds"] == 0.011
    assert report["process_generation_time"] == 0.012
    assert report["causal_generation_time"] == 0.013
    assert report["truth_time_seconds"] == 0.014
    assert report["reuse_time_seconds"] == 0.015
    assert report["memory_time_seconds"] == 0.016
    assert report["reasoning_time_seconds"] == 0.017
    assert report["evaluation_time_seconds"] == 0.018
    assert report["canonical_metrics"]["dependency_reasoning_time_seconds"] == 0.011
    assert report["metric_records"]["dependency_reasoning_time_seconds"][
        "metric_owner"
    ] == "dependency_runtime"
    assert sync_report["metrics_received"] == 8
    assert len(sync_report["metrics_bound"]) == 8
    assert len(sync_report["metrics_repaired"]) == 8
    assert sync_report["binding_success_rate"] == 1.0
    assert sync_report["coverage_before"] == 0.0
    assert sync_report["coverage_after"] == 1.0
    assert sync_report["remaining_placeholder_metrics"] == []
    assert sync_report["missing_runtime_metrics"] == []


def test_metric_owner_is_inferred_when_registry_lacks_definition():
    lifecycle_report = {
        "executions": [
            _execution("Custom Runtime", "custom_runtime", 0.01),
        ]
    }
    synchronizer = RuntimeMetricSynchronizer()
    synchronizer.registry.register_metric(
        "custom_runtime_time_seconds",
        "unknown",
        "test",
    )
    synchronizer._required_runtime_metrics = lambda: [
        "custom_runtime_time_seconds"
    ]
    synchronizer._metric_for_execution = (
        lambda execution: "custom_runtime_time_seconds"
    )

    result = synchronizer.synchronize(
        performance_report={"custom_runtime_time_seconds": 0.0},
        lifecycle_report=lifecycle_report,
    )

    bound = result["RUNTIME_METRIC_SYNCHRONIZATION_REPORT"]["metrics_bound"]
    assert bound[0]["owner"] != "unknown"
