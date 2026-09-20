from runtime.pipeline import AdaptiveCognitivePipeline
from runtime.planning.budget_policy import BudgetPolicy
from runtime.planning.cache_invalidation_engine import CacheInvalidationEngine
from runtime.planning.cognitive_budget_engine import CognitiveBudgetEngine
from runtime.planning.cognitive_cache_manager import CognitiveCacheManager
from runtime.planning.runtime_finalization_optimizer import (
    RuntimeFinalizationOptimizer,
)


def test_stable_context_hash_ignores_volatile_runtime_telemetry():
    cache = CognitiveCacheManager()
    stable = {
        "task_path": "task.json",
        "semantic_context": {"context": "color_context"},
        "dependency_chain_coverage": 0.9908,
        "performance_report": {"execution_time": 332.0},
        "runtime_boot": {"timestamp": "old"},
        "telemetry_enabled": True,
    }
    noisy = {
        **stable,
        "performance_report": {"execution_time": 12.0},
        "runtime_boot": {"timestamp": "new"},
        "telemetry_enabled": False,
        "cache_metrics_report": {"cache_hits": 100},
    }

    assert cache.stable_context_hash(stable) == cache.stable_context_hash(noisy)


def test_concept_version_hash_drives_selective_invalidation():
    cache = CognitiveCacheManager()
    invalidation = CacheInvalidationEngine()
    version = cache.concept_version_hash("e", "d", "c")
    changed_version = cache.concept_version_hash("e2", "d", "c")

    assert invalidation.concept_version_changed(
        {"concept_version_hash": version},
        {"concept_version_hash": version},
    ) is False
    assert invalidation.concept_version_changed(
        {"concept_version_hash": version},
        {"concept_version_hash": changed_version},
    ) is True


def test_dynamic_telemetry_reduces_only_after_saturation():
    budget = BudgetPolicy().adaptive()
    report = CognitiveBudgetEngine().reduce_telemetry_if_saturated(
        budget,
        {
            "evidence_saturated": True,
            "dependency_chain_coverage": 0.9908,
            "dependency_explanation_quality": 0.9731,
        },
    )

    assert report["telemetry_reduced"] is True
    assert report["telemetry_enabled"] is False
    assert budget.report_level == "summary"


def test_finalization_optimizer_prefers_fast_when_reuse_ready():
    optimizer = RuntimeFinalizationOptimizer()
    budget = BudgetPolicy().adaptive()

    mode = optimizer.choose_mode(
        reasoning_budget=budget,
        invalidated_concepts=[],
        runtime_context={
            "evidence_saturated": True,
            "dependency_chain_coverage": 0.9908,
            "dependency_explanation_quality": 0.9731,
        },
    )
    report = optimizer.fast_report(reused_concepts=["color_preservation"])

    assert mode == "fast"
    assert "historical_scans" in report["skipped_operations"]
    assert "ontology_reconciliation" in report["skipped_operations"]
    assert "memory_compression" in report["skipped_operations"]
    assert "stable_truth_revalidation" in report["skipped_operations"]
    assert report["estimated_cost_reduction"] >= 0.70


def test_pipeline_finalization_uses_fast_path_for_saturated_runtime():
    pipeline = AdaptiveCognitivePipeline()
    pipeline.configure_reasoning_budget(mode="adaptive")
    pipeline.prepare_task_run()
    pipeline.runtime.apply_reasoning_budget(BudgetPolicy().adaptive())
    pipeline.runtime.bulk_update_context({
        "evidence_saturated": True,
        "dependency_chain_coverage": 0.9908,
        "dependency_explanation_quality": 0.9731,
    })

    context = pipeline.finalize_runtime()

    assert context["runtime_finalization_report"]["finalization_mode"] == "fast"
    assert context["runtime_finalization_report"][
        "estimated_cost_reduction"
    ] >= 0.70


def test_pipeline_allocates_budget_only_after_memory_lookup():
    pipeline = AdaptiveCognitivePipeline()
    pipeline.cognitive_cache_manager = CognitiveCacheManager(
        persistence_enabled=False
    )
    pipeline.prepare_task_run()
    pipeline.pipeline_stages = [
        {
            "stage_name": "task_loading",
            "callable": lambda context: context,
        }
    ]
    pipeline.runtime.bulk_update_context({
        "input_grid": [[1, 0], [0, 0]],
        "output_grid": [[2, 0], [0, 0]],
    })

    pipeline.run_stage_cycle()
    context = pipeline.runtime.get_context()

    assert context["task_recognition_report"]["recognition_state"] == "completed"
    assert context["memory_lookup_report"]["exact_cache_hit"] is False
    assert context["budget_allocation_after_memory_lookup"] is True
    assert (
        context["memory_decision_before_budget"]
        == context["cognitive_execution_decision"]
    )


def test_identical_task_reuses_pipeline_memory_before_reasoning():
    pipeline = AdaptiveCognitivePipeline()
    pipeline.cognitive_cache_manager = CognitiveCacheManager(
        persistence_enabled=False
    )
    pipeline.pipeline_stages = [
        {
            "stage_name": "task_loading",
            "callable": lambda context: context,
        }
    ]
    task_context = {
        "input_grid": [[1, 0], [0, 0]],
        "output_grid": [[2, 0], [0, 0]],
    }

    pipeline.prepare_task_run()
    pipeline.runtime.bulk_update_context(dict(task_context))
    context = pipeline.runtime.get_context()
    pipeline.run_task_recognition(context)
    cache_key = pipeline._pipeline_result_cache_key(context)
    pipeline.cognitive_cache_manager.store(
        cache_key,
        {
            **context,
            "cache_safety_complete": True,
            "governance_report": {"status": "cached_safe"},
            "answer": "reused",
        },
        metadata=pipeline._cache_metadata(context),
    )

    pipeline.prepare_task_run()
    pipeline.runtime.bulk_update_context(dict(task_context))
    pipeline.run_stage_cycle()
    reused = pipeline.runtime.get_context()
    performance = pipeline.performance_report()

    assert reused["pipeline_cache_hit"] is True
    assert reused["answer"] == "reused"
    assert reused["cognitive_execution_decision"]["decision"] == "reuse_cached_result"
    assert performance["cache_hits"] > performance["cache_misses"]
    assert performance["new_reasoning"] == 0
    assert performance["reasoning_avoidance_ratio"] == 1.0
