"""Bounded success evaluation and termination readiness stage."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover - direct module execution support
    from _path_bootstrap import ensure_project_root

    ensure_project_root()
    __package__ = "runtime.pipeline"

from .base_stage import BaseStage
from .pipeline_context import PipelineContext
from .stage_result import StageResult
from runtime.evaluation import EvaluationController


class EvaluationStage(BaseStage):
    name = "evaluation"

    def execute(self, context: PipelineContext) -> StageResult:
        runtime_context = context.as_runtime_context()
        runtime_context.update(context.execution_metadata)
        evaluated = EvaluationController().evaluate(runtime_context)
        for key in (
            "evaluation_result",
            "evaluation_metrics",
            "evaluation_budget_report",
            "evaluation_report",
            "deferred_reporting_queue",
            "FAST_EVALUATION_MODE",
            "evaluation_fast_path",
            "report_deferred_count",
            "metrics_truncated",
            "shutdown_mode",
        ):
            if key in evaluated:
                context.execution_metadata[key] = evaluated[key]
        context.execution_metadata["evaluation"] = {
            "success_metrics_recorded": True,
            "residual_analysis": False,
            "termination_ready": bool(
                evaluated.get("FAST_EVALUATION_MODE")
                or context.execution_metadata.get("termination_ready", False)
            ),
            "bounded": True,
        }
        return StageResult(True, self.name, 0.0, context)


__all__ = ["EvaluationStage"]
