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
