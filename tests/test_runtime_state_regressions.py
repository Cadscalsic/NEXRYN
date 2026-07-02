import pytest

from runtime.cache import CacheManager
from runtime.cognition import AdaptiveReuseEngine
from runtime.pipeline import AdaptiveCognitivePipeline
from runtime.state.runtime_state import RuntimeState


def test_runtime_state_initializes_timing_and_tracks_added_context():

    state = RuntimeState()

    assert state.start_timestamp is None
    assert state.stop_timestamp is None

    state.update_context(
        "example",
        1,
    )

    snapshot = state.get_delta_snapshot()

    assert snapshot["latest_delta"]["delta_changes"]["example"] == {
        "change_type": "added",
    }


def test_pipeline_stage_failure_is_not_swallowed():

    pipeline = AdaptiveCognitivePipeline()

    def fail_stage(context):

        raise ValueError(
            "expected failure",
        )

    pipeline.pipeline_stages = [
        {
            "stage_name": "intentional_failure",
            "callable": fail_stage,
        },
    ]

    with pytest.raises(
        RuntimeError,
        match="Pipeline stage failed: intentional_failure",
    ):

        pipeline.run_stage_cycle()

    assert pipeline.failed_stages == [
        "intentional_failure",
    ]

    assert pipeline.runtime.failed_stages == [
        "intentional_failure",
    ]


def test_prepare_task_run_resets_transient_execution_state():

    pipeline = AdaptiveCognitivePipeline()

    pipeline.completed_stages.append(
        "old_stage",
    )

    pipeline.failed_stages.append(
        "old_failure",
    )

    pipeline.stage_execution_history.append({
        "stage_name": "old_stage",
    })

    pipeline.runtime.update_context(
        "old_context",
        True,
    )

    pipeline.prepare_task_run()

    assert pipeline.completed_stages == []
    assert pipeline.failed_stages == []
    assert pipeline.stage_execution_history == []
    assert pipeline.runtime.get_context() == {}


def test_dependency_reasoning_budget_reuses_unchanged_cached_chain():

    pipeline = AdaptiveCognitivePipeline()
    pipeline.configure_reasoning_budget(
        mode="fast",
        max_concepts=1,
        cache_dependencies=True,
    )
    pipeline.prepare_task_run()

    pipeline.run_dependency_reasoning_cycle()
    first_report = pipeline.performance_report()

    pipeline.run_dependency_reasoning_cycle()
    second_report = pipeline.performance_report()
    context = pipeline.runtime.get_context()

    assert first_report["dependency_chains_executed"] == 1
    assert second_report["dependency_chains_executed"] == 1
    assert second_report["cache_hits"] >= 1
    assert second_report["cache_misses"] == 1
    assert second_report["concepts_processed"] == 2
    assert context["dependency_reasoning_report"]["max_chain_depth"] == 8
    assert context["dependency_reasoning_report"]["telemetry_enabled"] is False


def test_semantic_concepts_activate_dependency_context_and_context_cache(tmp_path):

    pipeline = AdaptiveCognitivePipeline()
    pipeline.adaptive_cache_manager = CacheManager(
        cache_dir=tmp_path,
        auto_migrate=False,
    )
    pipeline.adaptive_reuse_engine = AdaptiveReuseEngine(
        cache_manager=pipeline.adaptive_cache_manager,
    )
    pipeline.configure_reasoning_budget(
        mode="fast",
        max_concepts=1,
        cache_dependencies=True,
    )
    pipeline.prepare_task_run()
    pipeline.runtime.bulk_update_context({
        "semantic_abstractions": [
            {
                "concept": "shape_preservation",
                "confidence": 0.92,
            },
        ],
    })

    pipeline.run_dependency_reasoning_cycle()
    pipeline.run_context_truth_advancement_cycle()
    first_report = pipeline.performance_report()

    pipeline.run_context_truth_advancement_cycle()
    second_report = pipeline.performance_report()
    context = pipeline.runtime.get_context()

    assert first_report["dependency_chains_executed"] == 1
    assert first_report["context_count"] > 0
    assert context["process_dependency_chains"]["shape_preservation"][
        "dependency_chain_depth"
    ] > 0
    assert context["semantic_context_report"]["semantic_context_count"] > 0
    assert second_report["context_reuse_report"]["context_hits"] >= 1


def test_process_contexts_are_registered_before_semantic_contexts(tmp_path):

    pipeline = AdaptiveCognitivePipeline()
    pipeline.adaptive_cache_manager = CacheManager(
        cache_dir=tmp_path,
        auto_migrate=False,
    )
    pipeline.adaptive_reuse_engine = AdaptiveReuseEngine(
        cache_manager=pipeline.adaptive_cache_manager,
    )
    pipeline.configure_reasoning_budget(
        mode="fast",
        max_concepts=1,
        cache_dependencies=True,
    )
    pipeline.prepare_task_run()
    pipeline.runtime.bulk_update_context({
        "semantic_abstractions": [
            {
                "concept": "growth",
                "confidence": 0.92,
            },
        ],
        "world_model_report": {
            "world_state": "training_task_observed",
            "world_confidence": 0.88,
        },
    })

    pipeline.run_dependency_reasoning_cycle()
    pipeline.run_process_semantic_cycle()
    pipeline.run_context_truth_advancement_cycle()

    report = pipeline.performance_report()
    context = pipeline.runtime.get_context()

    assert report["dependency_time"] > 0.0
    assert report["dependency_activation_state"] == "COMPLETED"
    assert report["dependency_chains_executed"] == 1
    assert report["process_context_count"] > 0
    assert report["causal_context_count"] > 0
    assert report["world_context_count"] > 0
    assert report["semantic_context_count"] > 0
    assert context["process_context_registry_report"][
        "process_context_count"
    ] > 0
    assert context["typed_context_registry_report"][
        "causal_context_count"
    ] > 0
    assert context["typed_context_registry_report"][
        "world_context_count"
    ] > 0
    assert any(
        item.get("context_type") == "PROCESS_CONTEXT"
        for item in context["context_registry_report"]["contexts"]
    )
    assert any(
        item.get("context_type") == "CAUSAL_CONTEXT"
        for item in context["context_registry_report"]["contexts"]
    )
    assert any(
        item.get("context_type") == "WORLD_CONTEXT"
        for item in context["context_registry_report"]["contexts"]
    )


def test_object_counting_enters_dependency_and_process_context_cycles(tmp_path):

    pipeline = AdaptiveCognitivePipeline()
    pipeline.adaptive_cache_manager = CacheManager(
        cache_dir=tmp_path,
        auto_migrate=False,
    )
    pipeline.adaptive_reuse_engine = AdaptiveReuseEngine(
        cache_manager=pipeline.adaptive_cache_manager,
    )
    pipeline.configure_reasoning_budget(
        mode="fast",
        max_concepts=1,
        cache_dependencies=True,
    )
    pipeline.prepare_task_run()
    pipeline.runtime.bulk_update_context({
        "task_id": "arc_concept_object_counting_03.json",
        "target_concepts": ["object_counting"],
        "semantic_abstractions": [
            {
                "concept": "object_counting",
                "confidence": 0.92,
            },
        ],
        "world_model_report": {
            "world_state": "object_counting_task_observed",
            "world_confidence": 0.88,
        },
    })

    pipeline.run_dependency_reasoning_cycle()
    pipeline.run_process_semantic_cycle()
    pipeline.run_context_truth_advancement_cycle()

    report = pipeline.performance_report()
    context = pipeline.runtime.get_context()

    assert report["dependency_chains_executed"] == 1
    assert "object_counting" in context["process_dependency_chains"]
    assert report["process_context_count"] > 0
    assert any(
        item.get("concept") == "object_counting"
        and item.get("context_type") == "PROCESS_CONTEXT"
        for item in context["context_registry_report"]["contexts"]
    )


def test_stage_cycle_activates_dependency_context_before_success_shutdown(tmp_path):

    pipeline = AdaptiveCognitivePipeline()
    pipeline.adaptive_cache_manager = CacheManager(
        cache_dir=tmp_path,
        auto_migrate=False,
    )
    pipeline.adaptive_reuse_engine = AdaptiveReuseEngine(
        cache_manager=pipeline.adaptive_cache_manager,
    )
    pipeline.configure_reasoning_budget(
        mode="fast",
        max_concepts=1,
        cache_dependencies=True,
    )
    pipeline.prepare_task_run()
    pipeline.runtime.bulk_update_context({
        "semantic_abstractions": [
            {
                "concept": "shape_preservation",
                "confidence": 0.92,
            },
        ],
    })

    def successful_evaluation(context):

        return {
            **context,
            "episode_completed": True,
            "evaluation_result": {
                "episode_completed": True,
                "success_state": "LEARNING_PROGRESS",
                "failure_detected": False,
                "retry_allowed": False,
            },
        }

    pipeline.pipeline_stages = [
        {
            "stage_name": "evaluation",
            "callable": successful_evaluation,
        },
    ]

    pipeline.run_stage_cycle()
    report = pipeline.performance_report()
    context = pipeline.runtime.get_context()

    assert report["dependency_chains_executed"] == 1
    assert report["context_count"] > 0
    assert report["active_compute_time_seconds"] > 0.0
    assert context["dependency_context_activation_report"][
        "dependency_chains_available"
    ] is True
    assert context["semantic_context_report"]["semantic_context_count"] > 0
