from dataclasses import fields

from runtime.evaluation import (
    AsyncMetricsWriter,
    DeferredReportingQueue,
    EvaluationController,
    EvaluationResult,
    MetricsBudgetController,
    PostSuccessFastPath,
)
from runtime.evaluation.post_success_fast_path import DISABLED_FAST_PATH_FEATURES
from runtime.pipeline import run_modular_pipeline
from runtime.pipeline.pipeline_context import PipelineContext


def test_evaluation_result_has_only_allowed_fields():
    assert [field.name for field in fields(EvaluationResult)] == [
        "accuracy",
        "success_state",
        "difference_count",
        "confidence",
        "episode_completed",
        "retry_allowed",
        "shutdown_mode",
        "evaluation_duration",
    ]


def test_post_success_fast_path_disables_heavy_features():
    context, activated = PostSuccessFastPath().activate_if_complete(
        {},
        {
            "episode_completed": True,
            "retry_allowed": False,
            "shutdown_mode": "fast",
        },
    )

    assert activated is True
    assert context["FAST_EVALUATION_MODE"] is True
    assert context["shutdown_mode"] == "fast"
    for feature in DISABLED_FAST_PATH_FEATURES:
        assert context[feature] is False


def test_evaluation_controller_defers_reports_and_returns_minimal_result(tmp_path):
    writer = AsyncMetricsWriter(tmp_path / "evaluation.jsonl")
    queue = DeferredReportingQueue()
    context = EvaluationController(
        reporting_queue=queue,
        metrics_writer=writer,
    ).evaluate({
        "accuracy": 1.0,
        "difference_count": 0,
        "episode_completed": True,
        "retry_allowed": False,
        "shutdown_mode": "fast",
    })

    assert context["FAST_EVALUATION_MODE"] is True
    assert context["evaluation_result"]["episode_completed"] is True
    assert context["evaluation_result"]["retry_allowed"] is False
    assert context["report_deferred_count"] >= 5
    assert queue.execute_during_shutdown() == []


def test_metrics_budget_truncates_and_continues_shutdown():
    metrics = {f"metric_{index}": index for index in range(25)}
    bounded, report = MetricsBudgetController().enforce(metrics, started_at=0.0)

    assert len(bounded) == 20
    assert report["metrics_truncated"] is True
    assert report["defer_reporting"] is True
    assert report["continue_shutdown"] is True


def test_async_metrics_writer_returns_without_waiting(tmp_path):
    thread = AsyncMetricsWriter(tmp_path / "evaluation.jsonl").write_async({
        "evaluation_summary": {"accuracy": 1.0},
        "blocked_key": {"must_not_persist": True},
    })

    assert thread.daemon is True
    thread.join(timeout=1)
    assert not thread.is_alive()
    assert "blocked_key" not in (tmp_path / "evaluation.jsonl").read_text()


def test_adaptive_pipeline_skips_governance_after_completed_evaluation():
    context = PipelineContext(task_batch=[{"task_id": "demo"}])
    context.execution_metadata.update({
        "accuracy": 1.0,
        "difference_count": 0,
        "episode_completed": True,
        "retry_allowed": False,
        "shutdown_mode": "fast",
    })

    result = run_modular_pipeline(context, mode="adaptive")
    stage_names = [
        item["stage_name"]
        for item in result.execution_metadata["stage_results"]
    ]

    assert "evaluation" in stage_names
    assert "shutdown" in stage_names
    assert "governance" not in stage_names
    assert "learning" not in stage_names
    assert "reporting" not in stage_names
