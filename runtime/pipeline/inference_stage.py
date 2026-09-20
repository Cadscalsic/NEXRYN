"""Strategy retrieval, program retrieval, and reasoning stage."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover - direct module execution support
    from _path_bootstrap import ensure_project_root

    ensure_project_root()
    __package__ = "runtime.pipeline"

from .base_stage import BaseStage
from .pipeline_context import PipelineContext
from .stage_result import StageResult


class InferenceStage(BaseStage):
    name = "inference"

    def execute(self, context: PipelineContext) -> StageResult:
        gate = context.execution_metadata.get("knowledge_reuse_gate_report", {})
        reasoning_skipped = gate.get("skip_deep_reasoning") is True
        context.execution_metadata["inference"] = {
            "strategy_retrieval": True,
            "program_retrieval": True,
            "reasoning_invoked": not reasoning_skipped,
        }
        return StageResult(True, self.name, 0.0, context)


__all__ = ["InferenceStage"]
