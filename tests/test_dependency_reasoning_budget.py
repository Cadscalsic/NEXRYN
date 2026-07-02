from runtime.pipeline import AdaptiveCognitivePipeline
from runtime.dependency.dependency_chain_executor import DependencyChainExecutor
from runtime.process.typed_process_dependency_memory import TypedProcessDependencyMemory


def test_adaptive_reasoning_budget_caps_dependency_explosion_by_default():
    pipeline = AdaptiveCognitivePipeline()

    pipeline.configure_reasoning_budget(mode="adaptive")

    assert pipeline.reasoning_budget["max_chain_depth"] == 4
    assert pipeline.reasoning_budget["max_dependency_depth"] == 4
    assert pipeline.reasoning_budget["max_concepts"] == 8


def test_cli_reasoning_budget_overrides_adaptive_caps():
    pipeline = AdaptiveCognitivePipeline()

    pipeline.configure_reasoning_budget(
        mode="adaptive",
        max_chain_depth=6,
        max_concepts=3,
    )

    assert pipeline.reasoning_budget["max_chain_depth"] == 6
    assert pipeline.reasoning_budget["max_dependency_depth"] == 6
    assert pipeline.reasoning_budget["max_concepts"] == 3


def test_pre_reasoning_plan_requests_dependency_when_gravity_enabled():
    pipeline = AdaptiveCognitivePipeline()
    context = {
        "task_id": "arc_concept_gravity_simulation_15.json",
        "input_grid": [
            [0, 2, 0],
            [0, 0, 0],
            [1, 1, 1],
        ],
        "output_grid": [
            [0, 0, 0],
            [0, 2, 0],
            [1, 1, 1],
        ],
        "requested_mode": "fast",
    }

    plan = pipeline._build_pre_reasoning_execution_plan(context)

    request = context["runtime_tool_requests"]["dependency_reasoning"]
    lifecycle = context["dependency_lifecycle_report"]
    assert plan["dependency_reasoning_enabled"] is True
    assert request["request_state"] == "REQUESTED"
    assert request["requested_by"] == "pre_reasoning_router"
    assert lifecycle["dependency_activation_state"] == "REQUESTED"


def test_budget_tool_selection_request_survives_runtime_context_sync():
    pipeline = AdaptiveCognitivePipeline()
    pipeline.prepare_task_run()
    context = {
        "task_id": "arc_concept_gravity_simulation_15.json",
        "input_grid": [
            [0, 2, 0],
            [0, 0, 0],
            [1, 1, 1],
        ],
        "output_grid": [
            [0, 0, 0],
            [0, 2, 0],
            [1, 1, 1],
        ],
    }

    pipeline.run_task_recognition(context)
    pipeline.allocate_cognitive_budget_after_memory_lookup(context)
    runtime_context = pipeline.runtime.get_context()

    for current in (context, runtime_context):
        assert current["input_grid"] == [
            [0, 2, 0],
            [0, 0, 0],
            [1, 1, 1],
        ]
        assert current["output_grid"] == [
            [0, 0, 0],
            [0, 2, 0],
            [1, 1, 1],
        ]
        request = current["runtime_tool_requests"]["dependency_reasoning"]
        lifecycle = current["dependency_lifecycle_report"]
        assert "dependency_reasoning" in current["enabled_tools"]
        assert request["request_state"] == "REQUESTED"
        assert lifecycle["dependency_activation_state"] == "REQUESTED"


def test_dependency_chain_executor_reuses_identical_dependency_snapshot():
    DependencyChainExecutor.clear_shared_cache()
    memory = TypedProcessDependencyMemory()
    executor = DependencyChainExecutor(memory=memory)

    first = executor.execute("replication", max_depth=8)
    second = executor.execute("replication", max_depth=8)

    assert first["dependency_cache_hit"] is False
    assert second["dependency_cache_hit"] is True
    assert second["dependencies"] == first["dependencies"]


def test_dependency_chain_executor_reuses_snapshot_across_executor_instances():
    DependencyChainExecutor.clear_shared_cache()
    memory = TypedProcessDependencyMemory()

    first = DependencyChainExecutor(memory=memory).execute("replication", max_depth=8)
    second = DependencyChainExecutor(memory=memory).execute("replication", max_depth=8)
    cache_report = DependencyChainExecutor.cache_report()

    assert first["dependency_cache_hit"] is False
    assert second["dependency_cache_hit"] is True
    assert second["dependency_cache_scope"] == "shared"
    assert second["dependencies"] == first["dependencies"]
    assert cache_report["dependency_executor_cache_hits"] == 1
