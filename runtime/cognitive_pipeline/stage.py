"""Stage contract for the cognitive solver pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .context import CognitiveContext


@dataclass(frozen=True)
class CognitiveStageSpec:
    stage_id: str
    stage_name: str
    required_inputs: tuple[str, ...] = ()
    optional_inputs: tuple[str, ...] = ()
    generated_outputs: tuple[str, ...] = ()
    consumed_outputs: tuple[str, ...] = ()
    dependent_stages: tuple[str, ...] = ()
    blocking_conditions: tuple[str, ...] = ()


@dataclass
class CognitiveStage:
    spec: CognitiveStageSpec
    handler: Callable[[CognitiveContext], dict[str, Any] | None] | None = None
    confidence: float = 1.0
    dependencies: tuple[str, ...] = field(default_factory=tuple)

    def execute(self, context: CognitiveContext) -> dict[str, Any]:
        if self.handler is None:
            return {}
        return self.handler(context) or {}


__all__ = ["CognitiveStage", "CognitiveStageSpec"]
