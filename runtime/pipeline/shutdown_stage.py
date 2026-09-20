"""Resource cleanup, memory flush, and fast runtime termination stage."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover - direct module execution support
    from _path_bootstrap import ensure_project_root

    ensure_project_root()
    __package__ = "runtime.pipeline"

from .base_stage import BaseStage
from .pipeline_context import PipelineContext
from .stage_result import StageResult
from runtime.shutdown import ShutdownController


class ShutdownStage(BaseStage):
    name = "shutdown"
    critical = True

    def execute(self, context: PipelineContext) -> StageResult:
        controller = ShutdownController()
        shutdown_context = {
            "execution_metadata": context.execution_metadata,
            "evaluation_metrics": context.execution_metadata.get(
                "evaluation_metrics",
                {},
            ),
            "evaluation_result": context.execution_metadata.get(
                "evaluation_result",
                {},
            ),
            "shutdown_mode": "fast",
        }
        shutdown_context = controller.execute_shutdown(
            shutdown_context,
            exit_process=False,
        )
        context.execution_metadata["shutdown"] = shutdown_context.get(
            "SHUTDOWN_REPORT",
            {},
        )
        context.execution_metadata["shutdown"].setdefault(
            "runtime_terminated",
            True,
        )
        return StageResult(True, self.name, 0.0, context, should_continue=False)


__all__ = ["ShutdownStage"]
