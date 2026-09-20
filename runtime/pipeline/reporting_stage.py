"""Runtime, profiling, and telemetry reporting stage."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover - direct module execution support
    from _path_bootstrap import ensure_project_root

    ensure_project_root()
    __package__ = "runtime.pipeline"

from .base_stage import BaseStage
from .pipeline_context import PipelineContext
from .stage_result import StageResult


class ReportingStage(BaseStage):
    name = "reporting"

    def execute(self, context: PipelineContext) -> StageResult:
        context.execution_metadata["reporting"] = {
            "runtime_reports": True,
            "profiling_reports": True,
            "telemetry_reports": True,
        }
        return StageResult(True, self.name, 0.0, context)


__all__ = ["ReportingStage"]
