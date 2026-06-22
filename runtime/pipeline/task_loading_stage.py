"""Task selection, batching, and task metadata stage."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover - direct module execution support
    from _path_bootstrap import ensure_project_root

    ensure_project_root()
    __package__ = "runtime.pipeline"

from .base_stage import BaseStage
from .pipeline_context import PipelineContext
from .stage_result import StageResult


class TaskLoadingStage(BaseStage):
    name = "task_loading"
    critical = True

    def execute(self, context: PipelineContext) -> StageResult:
        if context.active_task is None and context.task_batch:
            task = context.task_batch[0]
            context.active_task = task if isinstance(task, dict) else {"task": task}
        context.execution_metadata.setdefault("task_loading", {})
        context.execution_metadata["task_loading"].update({
            "task_count": len(context.task_batch),
            "active_task_loaded": context.active_task is not None,
        })
        return StageResult(True, self.name, 0.0, context)


__all__ = ["TaskLoadingStage"]
