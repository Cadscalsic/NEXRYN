"""Shared context passed through modular pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

root = Path(__file__).resolve().parents[2]
root_text = str(root)
if root_text not in sys.path:
    sys.path.insert(0, root_text)

if TYPE_CHECKING:
    from runtime.state.runtime_state import RuntimeState


class _LazyRuntimeState:
    def __init__(self) -> None:
        object.__setattr__(self, "_target", None)

    def _load(self) -> "RuntimeState":
        target = object.__getattribute__(self, "_target")
        if target is None:
            from runtime.state.runtime_state import RuntimeState

            target = RuntimeState()
            object.__setattr__(self, "_target", target)
        return target

    def __getattr__(self, name: str) -> Any:
        return getattr(self._load(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._load(), name, value)

    def get_context(self) -> dict[str, Any]:
        return self._load().get_context()


@dataclass
class PipelineContext:
    runtime_state: "RuntimeState" = field(default_factory=_LazyRuntimeState)
    task_batch: list[Any] = field(default_factory=list)
    active_task: dict[str, Any] | None = None
    memory_state: dict[str, Any] = field(default_factory=dict)
    governance_state: dict[str, Any] = field(default_factory=dict)
    profiling_state: dict[str, Any] = field(default_factory=dict)
    execution_metadata: dict[str, Any] = field(default_factory=dict)

    def record_stage_profile(
        self,
        stage_name: str,
        profile: dict[str, Any],
    ) -> None:
        stages = self.profiling_state.setdefault("stages", {})
        stages[stage_name] = dict(profile)

    def as_runtime_context(self) -> dict[str, Any]:
        context = (
            self.runtime_state.get_context()
            if hasattr(self.runtime_state, "get_context")
            else {}
        )
        return {
            **dict(context or {}),
            "task_batch": self.task_batch,
            "active_task": self.active_task,
            "memory_state": self.memory_state,
            "governance_state": self.governance_state,
            "profiling_state": self.profiling_state,
            "execution_metadata": self.execution_metadata,
        }


__all__ = ["PipelineContext"]
