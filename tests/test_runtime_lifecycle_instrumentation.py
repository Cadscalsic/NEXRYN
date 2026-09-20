from runtime.causal.causal_context_runtime import CausalContextRuntime
from runtime.dependency.dependency_execution_bridge import DependencyExecutionBridge
from runtime.instrumentation import RuntimeLifecycle, runtime_lifecycle
from runtime.memory.causal_context_memory import CausalContextMemory
from runtime.memory.process_context_memory import ProcessContextMemory
from runtime.process.process_context_runtime import ProcessContextRuntime


def test_runtime_lifecycle_records_standard_event_sequence():
    lifecycle = RuntimeLifecycle()
    execution = lifecycle.create(
        module_name="unit_runtime",
        runtime_name="Unit Runtime",
        caller="test",
        trigger="unit_test",
    )

    lifecycle.requested(execution)
    lifecycle.queued(execution)
    lifecycle.started(execution)
    lifecycle.running(execution)
    lifecycle.completed(execution, output_count=1, memory_cost=1)
    lifecycle.reported(execution)

    report = lifecycle.build_report()
    event_types = [event["event_type"] for event in report["event_timeline"]]

    assert report["RUNTIME_LIFECYCLE_REPORT"] is True
    assert report["executions_started"] == 1
    assert report["executions_completed"] == 1
    assert report["event_count"] >= 6
    assert report["lifecycle_consistency"] == 1.0
    assert report["missing_timestamps"] == []
    assert "ExecutionStarted" in event_types
    assert "ExecutionCompleted" in event_types
    assert report["executions"][0]["execution_start"]
    assert report["executions"][0]["execution_end"]


def test_core_runtimes_expose_lifecycle_timing_fields():
    runtime_lifecycle.clear()

    dependency = DependencyExecutionBridge().execute(
        activation_request={"request_state": "REQUESTED"},
        activation_decision={"activation_state": "DEPENDENCY_REQUIRED"},
        concepts=["path_finding"],
        activated_tools=["dependency_reasoning"],
    )
    process = ProcessContextRuntime(memory=ProcessContextMemory()).run(
        input_grid=[[1, 0, 0, 1]],
        output_grid=[[1, 1, 1, 1]],
        detected_concepts=["path_finding"],
        dependency_activation_report={
            "dependency_graph_discovery_report": dependency.get(
                "dependency_graph_discovery_report",
                {},
            ),
            "dependency_reports": dependency.get("dependency_reports", []),
        },
    )
    causal = CausalContextRuntime(memory=CausalContextMemory()).run(
        input_grid=[[1, 0, 0, 1]],
        output_grid=[[1, 1, 1, 1]],
        process_context_report=process,
        dependency_activation_report={
            "dependency_reports": dependency.get("dependency_reports", []),
            "dependency_chains_executed": dependency.get("chains_generated", 0),
        },
    )
    lifecycle = runtime_lifecycle.build_report()

    for report in (dependency, process, causal):
        assert report["execution_start"]
        assert report["execution_end"]
        assert report["elapsed_seconds"] > 0.0
        assert report["duration_seconds"] > 0.0
        assert report["wall_clock_time"] > 0.0
        assert report["runtime_lifecycle"]["lifecycle_events"]

    assert dependency["dependency_reasoning_time_seconds"] > 0.0
    assert process["process_generation_time"] > 0.0
    assert causal["causal_generation_time"] > 0.0
    assert lifecycle["executions_started"] >= 3
    assert lifecycle["executions_completed"] >= 3
    assert lifecycle["missing_timestamps"] == []
    assert lifecycle["invalid_transitions"] == []
