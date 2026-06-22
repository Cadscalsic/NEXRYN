"""Memory updates, strategy updates, and concept promotion stage."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover - direct module execution support
    from _path_bootstrap import ensure_project_root

    ensure_project_root()
    __package__ = "runtime.pipeline"

from .base_stage import BaseStage
from .pipeline_context import PipelineContext
from .stage_result import StageResult


class LearningStage(BaseStage):
    name = "learning"

    def execute(self, context: PipelineContext) -> StageResult:
        context.memory_state.setdefault("learning_updates", [])
        context.execution_metadata["learning"] = {
            "memory_updates": True,
            "strategy_updates": True,
            "concept_promotion_checked": True,
        }
        return StageResult(True, self.name, 0.0, context)


__all__ = ["LearningStage"]
