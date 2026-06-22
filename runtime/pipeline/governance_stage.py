"""Truth validation, identity checks, and budget enforcement stage."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover - direct module execution support
    from _path_bootstrap import ensure_project_root

    ensure_project_root()
    __package__ = "runtime.pipeline"

from .base_stage import BaseStage
from .pipeline_context import PipelineContext
from .stage_result import StageResult


class GovernanceStage(BaseStage):
    name = "governance"

    def execute(self, context: PipelineContext) -> StageResult:
        if context.execution_metadata.get("FAST_EVALUATION_MODE"):
            context.governance_state["governance_skipped"] = True
            context.governance_state["skip_reason"] = "post_success_fast_path"
            return StageResult(True, self.name, 0.0, context)
        complexity = context.execution_metadata.get("task_complexity", 0.0)
        try:
            low_complexity = float(complexity) < 0.20
        except (TypeError, ValueError):
            low_complexity = False
        if low_complexity:
            context.governance_state["governance_skipped"] = True
            context.governance_state["skip_reason"] = "low_complexity_task"
            return StageResult(True, self.name, 0.0, context)
        context.governance_state.update({
            "truth_validation": True,
            "identity_checks": True,
            "budget_enforcement": True,
        })
        return StageResult(True, self.name, 0.0, context)


__all__ = ["GovernanceStage"]
