from runtime.pipeline import pipeline
from runtime.pipeline.base_stage import BaseStage
from runtime.pipeline.pipeline_context import PipelineContext
from runtime.pipeline.pipeline_runner import ModularPipelineRunner, run_modular_pipeline
from runtime.pipeline.stage_registry import StageRegistry
from runtime.pipeline.stage_result import StageResult


def test_backward_compatible_pipeline_import_is_lazy():
    assert hasattr(pipeline, "run")


def test_fast_mode_runs_independent_stages_and_profiles():
    context = run_modular_pipeline(
        PipelineContext(task_batch=[{"task_id": "demo"}]),
        mode="fast",
    )

    assert context.active_task == {"task_id": "demo"}
    assert context.execution_metadata["shutdown"]["runtime_terminated"] is True
    assert set(context.profiling_state["stages"]) == {
        "task_loading",
        "object_detection",
        "inference",
        "evaluation",
        "shutdown",
    }
    for profile in context.profiling_state["stages"].values():
        assert "execution_time" in profile
        assert "memory_usage" in profile
        assert "cache_hits" in profile
        assert "cache_misses" in profile
        assert "budget_usage" in profile


def test_governance_skips_low_complexity_tasks():
    context = PipelineContext()
    context.execution_metadata["task_complexity"] = 0.1

    result = run_modular_pipeline(context, mode="adaptive")

    assert result.governance_state["governance_skipped"] is True
    assert result.governance_state["skip_reason"] == "low_complexity_task"


class FailingStage(BaseStage):
    name = "task_loading"
    critical = True

    def execute(self, context):
        raise RuntimeError("stage failed")


def test_critical_stage_failure_triggers_self_repair_without_crash():
    registry = StageRegistry()
    registry.register(FailingStage())

    context = ModularPipelineRunner(registry).run(PipelineContext(), mode="fast")

    assert context.execution_metadata["self_repair_triggered"] is True
    assert "stage failed" in context.execution_metadata["self_repair_reason"][0]


def test_runner_enforces_budget_before_stage_execution():
    context = PipelineContext()
    context.execution_metadata["budget_usage"] = {"reasoning_depth": 3}

    result = run_modular_pipeline(
        context,
        mode="fast",
        budgets={"max_reasoning_depth": 1},
    )

    assert result.execution_metadata["budget_stop_reason"] == "budget_exhausted"
    assert result.execution_metadata["stage_results"] == []
