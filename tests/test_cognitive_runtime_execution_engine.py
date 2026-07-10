from runtime.cognitive_runtime.execution_binding import ExecutionBindingLayer
from runtime.cognitive_runtime.execution_engine import CognitiveRuntimeExecutionEngine
from runtime.cognitive_runtime.framework import CognitiveRuntimeFramework
from runtime.instrumentation import runtime_lifecycle
from runtime.metrics.runtime_metric_synchronizer import RuntimeMetricSynchronizer


def _exercise_required(engine):
    engine.start_cycle(mode="adaptive")
    for runtime_id in (
        "reasoning_runtime",
        "search_runtime",
        "evidence_builder_runtime",
        "memory_runtime",
        "truth_runtime",
        "evaluation_runtime",
    ):
        with engine.execution(runtime_id) as execution:
            execution.capture({
                "confidence": 0.8,
                "concepts": ["a", "b"],
                "route_statistics": {"routes_created": 2},
                "truth_candidates": [{"id": "t"}],
                "entries_stored": 1,
            })
            sum(range(2000))
    engine.complete_cycle()


def test_factory_creates_real_hierarchical_execution_instances():
    runtime_lifecycle.clear()
    engine = CognitiveRuntimeExecutionEngine()
    _exercise_required(engine)
    report = engine.build_report()

    assert report["COGNITIVE_EXECUTION_ENGINE_REPORT"] is True
    assert report["synthetic_execution_count"] == 0
    assert report["missing_execution_instances"] == []
    assert report["execution_coverage"] == 1.0
    assert report["lifecycle_coverage"] == 1.0
    assert len(report["execution_tree"]) == 1
    assert len(report["execution_tree"][0]["children"]) == 6
    types = {item["execution_type"] for item in report["execution_instances"]}
    assert {
        "ReasoningExecution",
        "SearchExecution",
        "EvidenceBuilderExecution",
        "MemoryExecution",
        "TruthExecution",
        "EvaluationExecution",
    }.issubset(types)
    assert all(
        "synthetic_execution" not in item["execution_id"]
        for item in report["execution_instances"]
    )


def test_evaluation_evidence_does_not_publish_truth_candidates():
    runtime_lifecycle.clear()
    engine = CognitiveRuntimeExecutionEngine()
    engine.start_cycle(mode="deep")

    with engine.execution("evaluation_runtime") as execution:
        execution.capture({"evaluations": [{"id": "eval:a", "score": 0.9}]})
    with engine.execution("truth_runtime") as execution:
        execution.capture({"evaluations": [{"id": "truth:a", "confidence": 0.9}]})

    report = engine.build_report()
    by_runtime = {
        item["runtime_id"]: item
        for item in report["execution_instances"]
        if item["runtime_id"] in {"evaluation_runtime", "truth_runtime"}
    }

    assert by_runtime["evaluation_runtime"]["generated_truth_candidates"] == 0
    assert by_runtime["truth_runtime"]["generated_truth_candidates"] == 1


def test_execution_lifecycle_binding_populates_runtime_metrics():
    runtime_lifecycle.clear()
    engine = CognitiveRuntimeExecutionEngine()
    _exercise_required(engine)
    lifecycle = runtime_lifecycle.build_report()
    cognitive = CognitiveRuntimeFramework().build_report(
        performance_report={},
        runtime_lifecycle_report=lifecycle,
    )

    binding = ExecutionBindingLayer().bind(
        cognitive["runtime_registry"],
        lifecycle,
    )
    synchronized = RuntimeMetricSynchronizer().synchronize(
        performance_report={
            "reasoning_time_seconds": 0.0,
            "search_time_seconds": 0.0,
            "memory_time_seconds": 0.0,
            "truth_time_seconds": 0.0,
            "evaluation_time_seconds": 0.0,
        },
        lifecycle_report=lifecycle,
        runtime_registry=cognitive["runtime_registry"],
    )["performance_report"]

    assert binding["registry_synchronization"] in {"SYNCHRONIZED", "PARTIAL"}
    assert not any(
        "Lifecycle incomplete" in failure["binding_errors"]
        for failure in binding["failed_bindings"]
        if failure["binding_target"] in {
            "reasoning_runtime",
            "search_runtime",
            "memory_runtime",
            "truth_runtime",
            "evaluation_runtime",
        }
    )
    for metric in (
        "reasoning_time_seconds",
        "search_time_seconds",
        "memory_time_seconds",
        "truth_time_seconds",
        "evaluation_time_seconds",
    ):
        assert synchronized[metric] > 0.0


def test_bound_executions_archive_with_snapshots_and_events():
    runtime_lifecycle.clear()
    engine = CognitiveRuntimeExecutionEngine()
    _exercise_required(engine)
    engine.bind_and_archive()
    report = engine.build_report()

    cognitive = [
        item for item in report["execution_instances"]
        if item["runtime_id"] != "execution_runtime"
    ]
    assert all(item["binding_status"] == "BOUND" for item in cognitive)
    assert all(item["archived"] is True for item in cognitive)
    assert all(item["duration_seconds"] > 0.0 for item in cognitive)
    assert all(item["cpu_time"] >= 0.0 for item in cognitive)
    assert all(item["snapshots"] for item in cognitive)
    assert all(
        {"CREATED", "REQUESTED", "STARTED", "COMPLETED", "VALIDATED", "BOUND", "ARCHIVED"}
        .issubset({event["status"] for event in item["lifecycle_events"]})
        for item in cognitive
    )
