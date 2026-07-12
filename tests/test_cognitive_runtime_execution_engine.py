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


def test_parent_execution_becomes_official_cognitive_state_aggregate():
    runtime_lifecycle.clear()
    engine = CognitiveRuntimeExecutionEngine()
    root = engine.start_cycle(mode="adaptive")

    with engine.execution("concept_formation_runtime") as execution:
        execution.capture({"generated_concepts": [{"id": "concept:a"}, {"id": "concept:b"}]})
    with engine.execution("program_synthesis_runtime") as execution:
        execution.capture({"generated_programs": 3})
    with engine.execution("truth_runtime") as execution:
        execution.capture({"truth_candidates": [{"id": "truth:a"}, {"id": "truth:b"}]})
    with engine.execution("memory_runtime") as execution:
        execution.capture({"memory_entries": [{"id": "memory:a"}]})

    engine.complete_cycle()
    report = engine.build_report()
    parent = next(
        item for item in report["execution_instances"]
        if item["execution_id"] == root.execution_id
    )
    summary = report["parent_execution_aggregation"]
    tree_root = report["execution_tree"][0]

    assert parent["runtime_id"] == "execution_runtime"
    assert parent["generated_concepts"] == 2
    assert parent["generated_programs"] == 3
    assert parent["generated_truth_candidates"] == 2
    assert parent["generated_memory_entries"] == 1
    assert summary["parent_is_cognitive_state_source"] is True
    assert summary["aggregates_child_runtime_outputs"] is True
    assert summary["generated_concepts"] == 2
    assert tree_root["generated_programs"] == 3


def test_post_execution_pipeline_turns_cognitive_outputs_into_semantic_memory_entries():
    runtime_lifecycle.clear()
    engine = CognitiveRuntimeExecutionEngine()
    root = engine.start_cycle(mode="adaptive")

    with engine.execution("concept_formation_runtime") as execution:
        execution.capture({"generated_concepts": [{"id": f"concept:{index}"} for index in range(43)]})
    with engine.execution("program_synthesis_runtime") as execution:
        execution.capture({"generated_programs": 20})
    with engine.execution("truth_runtime") as execution:
        execution.capture({"truth_candidates": [{"id": f"truth:{index}"} for index in range(18)]})

    engine.complete_cycle()
    report = engine.build_report()
    parent = next(
        item for item in report["execution_instances"]
        if item["execution_id"] == root.execution_id
    )
    pipeline = report["post_execution_cognitive_pipeline"]

    assert report["parent_execution_aggregation"]["generated_concepts"] == 43
    assert report["parent_execution_aggregation"]["generated_programs"] == 20
    assert report["parent_execution_aggregation"]["generated_truth_candidates"] == 18
    assert pipeline["pipeline_available"] is True
    assert pipeline["reflection_to_experience_to_semantic_memory_productive"] is True
    assert pipeline["reflection_status"] == "COMPLETED"
    assert pipeline["experience_count"] == 1
    assert pipeline["semantic_memory_entries_generated"] > 0
    assert pipeline["semantic_memory_to_knowledge_fabric_productive"] is True
    assert pipeline["fabric_links"] > 0
    assert pipeline["knowledge_fabric_report"]["fabric_links"] == pipeline["fabric_links"]
    assert pipeline["knowledge_fabric_report"]["fabric_bridges"] == pipeline["fabric_bridges"]
    assert pipeline["knowledge_fabric_report"]["cross_domain_links"] == pipeline["cross_domain_links"]
    assert pipeline["fabric_density"] >= 0.0
    assert pipeline["fabric_connectivity"] > 0.0
    assert isinstance(pipeline["orphan_concepts"], list)
    assert isinstance(pipeline["isolated_domains"], list)
    assert pipeline["knowledge_fabric_connects_semantic_memory"] is True
    assert pipeline["knowledge_fabric_stores_relationships_only"] is True
    assert pipeline["semantic_memory_is_canonical_destination"] is True
    assert pipeline["memory_runtime_replaced"] is False
    assert parent["generated_memory_entries"] == pipeline["semantic_memory_entries_generated"]
    assert report["parent_execution_aggregation"]["generated_memory_entries"] > 0


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
