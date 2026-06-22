"""Base class for stage-oriented pipeline execution."""

from __future__ import annotations

import time
import tracemalloc
from typing import Any

if __package__ in {None, ""}:  # pragma: no cover - direct module execution support
    from _path_bootstrap import ensure_project_root

    ensure_project_root()
    __package__ = "runtime.pipeline"

from .pipeline_context import PipelineContext
from .stage_result import StageResult


class BaseStage:
    name = "base"
    critical = False
    retry_count = 0

    def execute(self, context: PipelineContext) -> StageResult:
        raise NotImplementedError

    def run(self, context: PipelineContext) -> StageResult:
        started_at = time.perf_counter()
        tracemalloc_started = False
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            tracemalloc_started = True
        start_memory = tracemalloc.get_traced_memory()[0]
        try:
            result = self.execute(context)
        except Exception as exc:  # pragma: no cover - defensive orchestration
            result = StageResult(
                success=False,
                stage_name=self.name,
                execution_time=0.0,
                updated_context=context,
                errors=[str(exc)],
                should_continue=not self.critical,
            )
        end_memory = tracemalloc.get_traced_memory()[0]
        if tracemalloc_started:
            tracemalloc.stop()
        execution_time = time.perf_counter() - started_at
        result.execution_time = execution_time
        result.updated_context.record_stage_profile(
            self.name,
            {
                "execution_time": execution_time,
                "memory_usage": max(0, end_memory - start_memory),
                "cache_hits": self._metric(result.updated_context, "cache_hits"),
                "cache_misses": self._metric(result.updated_context, "cache_misses"),
                "budget_usage": self._budget_usage(result.updated_context),
                "success": result.success,
                "warnings": list(result.warnings),
                "errors": list(result.errors),
            },
        )
        return result

    def _metric(self, context: PipelineContext, key: str) -> Any:
        return context.execution_metadata.get(key, 0)

    def _budget_usage(self, context: PipelineContext) -> dict[str, Any]:
        return dict(context.execution_metadata.get("budget_usage", {}))


__all__ = ["BaseStage"]
