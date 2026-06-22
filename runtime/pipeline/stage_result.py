"""Result object returned by every pipeline stage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pipeline_context import PipelineContext


@dataclass
class StageResult:
    success: bool
    stage_name: str
    execution_time: float
    updated_context: "PipelineContext"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    should_continue: bool = True


__all__ = ["StageResult"]
