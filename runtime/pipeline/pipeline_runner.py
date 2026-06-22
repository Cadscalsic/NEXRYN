"""Stage-oriented pipeline runner and legacy compatibility entrypoints."""

from __future__ import annotations

import time
from typing import Any

from .pipeline_context import PipelineContext
from .stage_registry import StageRegistry
from .task_loading_stage import TaskLoadingStage
from .preprocessing_stage import PreprocessingStage
from .object_detection_stage import ObjectDetectionStage
from .inference_stage import InferenceStage
from .transformation_stage import TransformationStage
from .evaluation_stage import EvaluationStage
from .governance_stage import GovernanceStage
from .learning_stage import LearningStage
from .reporting_stage import ReportingStage
from .shutdown_stage import ShutdownStage


BUDGET_KEYS = (
    "max_reasoning_depth",
    "max_active_routes",
    "max_hypotheses",
    "max_governance_cycles",
    "max_runtime",
)


class ModularPipelineRunner:
    def __init__(self, registry: StageRegistry | None = None) -> None:
        self.registry = registry or default_stage_registry()

    def run(
        self,
        context: PipelineContext | None = None,
        mode: str = "adaptive",
        budgets: dict[str, Any] | None = None,
    ) -> PipelineContext:
        context = context or PipelineContext()
        context.execution_metadata["budget_limits"] = dict(budgets or {})
        context.execution_metadata.setdefault("stage_results", [])
        started_at = time.perf_counter()
        for stage in self.registry.stages_for_mode(mode):
            if self._fast_path_skips_stage(context, stage):
                continue
            if not self._budget_allows(context, started_at):
                context.execution_metadata["budget_stop_reason"] = "budget_exhausted"
                break
            result = self._run_stage_with_retry(stage, context)
            context = result.updated_context
            context.execution_metadata["stage_results"].append({
                "stage_name": result.stage_name,
                "success": result.success,
                "execution_time": result.execution_time,
                "warnings": list(result.warnings),
                "errors": list(result.errors),
            })
            if not result.success and stage.critical:
                context.execution_metadata["self_repair_triggered"] = True
                context.execution_metadata["self_repair_reason"] = result.errors
                break
            if not result.should_continue:
                break
        context.execution_metadata["pipeline_execution_time"] = (
            time.perf_counter() - started_at
        )
        return context

    def _fast_path_skips_stage(self, context: PipelineContext, stage) -> bool:
        if not context.execution_metadata.get("FAST_EVALUATION_MODE"):
            return False
        if "evaluation_result" not in context.execution_metadata:
            return False
        return stage.name not in {"shutdown"}

    def _run_stage_with_retry(self, stage, context: PipelineContext):
        attempts = max(1, int(getattr(stage, "retry_count", 0)) + 1)
        last_result = None
        for _ in range(attempts):
            last_result = stage.run(context)
            if last_result.success:
                return last_result
        return last_result

    def _budget_allows(
        self,
        context: PipelineContext,
        started_at: float,
    ) -> bool:
        limits = dict(context.execution_metadata.get("budget_limits", {}))
        usage = dict(context.execution_metadata.get("budget_usage", {}))
        if "max_runtime" in limits:
            usage["runtime"] = time.perf_counter() - started_at
        for key in BUDGET_KEYS:
            if key not in limits:
                continue
            usage_key = key.replace("max_", "")
            try:
                if float(usage.get(usage_key, 0.0)) > float(limits[key]):
                    return False
            except (TypeError, ValueError):
                return False
        context.execution_metadata["budget_usage"] = usage
        return True


def default_stage_registry() -> StageRegistry:
    registry = StageRegistry()
    for stage in (
        TaskLoadingStage(),
        PreprocessingStage(),
        ObjectDetectionStage(),
        InferenceStage(),
        TransformationStage(),
        EvaluationStage(),
        GovernanceStage(),
        LearningStage(),
        ReportingStage(),
        ShutdownStage(),
    ):
        registry.register(stage)
    return registry


def run_modular_pipeline(
    context: PipelineContext | None = None,
    mode: str = "adaptive",
    budgets: dict[str, Any] | None = None,
) -> PipelineContext:
    return ModularPipelineRunner().run(context=context, mode=mode, budgets=budgets)


def run_pipeline(*args, use_legacy: bool = True, **kwargs):
    if use_legacy:
        from .legacy_pipeline import pipeline

        return pipeline.run(*args, **kwargs)
    return run_modular_pipeline(*args, **kwargs)


__all__ = [
    "BUDGET_KEYS",
    "ModularPipelineRunner",
    "default_stage_registry",
    "run_modular_pipeline",
    "run_pipeline",
]
