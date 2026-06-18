"""Trace objects for reasoned process dependency execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProcessDependencyTrace:
    concept: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "trace_length": len(self.steps),
            "process_dependency_trace_generated": True,
        }


__all__ = ["ProcessDependencyTrace"]
