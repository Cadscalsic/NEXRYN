"""Canonical execution transition record."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ExecutionTransition:
    transition_id: str
    execution_id: str
    layer_name: str
    capability_name: str
    previous_state: str
    new_state: str
    trigger_signal: str
    reason: str
    priority: str
    policy: str
    dependencies_activated: tuple[str, ...] = ()
    approved: bool = True
    rejection_reason: str | None = None
    timestamp: str = field(default_factory=lambda: str(datetime.utcnow()))

    @classmethod
    def create(
        cls,
        execution_id: str,
        layer_name: str,
        capability_name: str,
        previous_state: str,
        new_state: str,
        trigger_signal: str,
        reason: str,
        priority: str,
        policy: str,
        dependencies_activated: list[str] | tuple[str, ...] | None = None,
        approved: bool = True,
        rejection_reason: str | None = None,
    ) -> "ExecutionTransition":
        return cls(
            transition_id=f"transition-{uuid4()}",
            execution_id=str(execution_id or ""),
            layer_name=str(layer_name),
            capability_name=str(capability_name),
            previous_state=str(previous_state),
            new_state=str(new_state),
            trigger_signal=str(trigger_signal),
            reason=str(reason),
            priority=str(priority),
            policy=str(policy),
            dependencies_activated=tuple(dependencies_activated or ()),
            approved=bool(approved),
            rejection_reason=rejection_reason,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "execution_id": self.execution_id,
            "layer_name": self.layer_name,
            "capability_name": self.capability_name,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "trigger_signal": self.trigger_signal,
            "reason": self.reason,
            "priority": self.priority,
            "policy": self.policy,
            "dependencies_activated": list(self.dependencies_activated),
            "approved": self.approved,
            "rejection_reason": self.rejection_reason,
            "timestamp": self.timestamp,
        }


__all__ = ["ExecutionTransition"]
