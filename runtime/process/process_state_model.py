"""State -> Transition -> State model for semantic process contexts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from core.epistemic_models import clamp


@dataclass(frozen=True)
class ProcessState:
    name: str
    predicates: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProcessSemanticContext:
    concept: str
    preconditions: list[str]
    transition_steps: list[str]
    postconditions: list[str]
    invariants: list[str]
    temporal_constraints: list[str]
    context_strength: float

    def as_dict(self) -> dict[str, Any]:
        strength = clamp(self.context_strength)
        return {
            **asdict(self),
            "context_name": f"{self.concept}_context",
            "context_type": "PROCESS_CONTEXT",
            "process_context_strength": strength,
            "context_confidence": strength,
            "process_context_generated": True,
            "process_semantic_context_synthesized": True,
            "state_transition_state": {
                "initial_state": ProcessState(
                    name=f"{self.concept}_pre_state",
                    predicates=list(self.preconditions),
                ).as_dict(),
                "transition": list(self.transition_steps),
                "final_state": ProcessState(
                    name=f"{self.concept}_post_state",
                    predicates=list(self.postconditions),
                ).as_dict(),
            },
            "temporal_reasoning_enabled": False,
        }


__all__ = ["ProcessSemanticContext", "ProcessState"]
