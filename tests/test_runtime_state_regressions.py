import pytest

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
