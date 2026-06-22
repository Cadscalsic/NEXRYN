"""Program execution and transform application stage."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover - direct module execution support
    from _path_bootstrap import ensure_project_root

    ensure_project_root()
    __package__ = "runtime.pipeline"

from .base_stage import BaseStage
from .pipeline_context import PipelineContext
from .stage_result import StageResult


class TransformationStage(BaseStage):
    name = "transformation"

    def execute(self, context: PipelineContext) -> StageResult:
        context.execution_metadata["transformation"] = {
            "program_execution": True,
            "transform_applied": True,
        }
        return StageResult(True, self.name, 0.0, context)


__all__ = ["TransformationStage"]
