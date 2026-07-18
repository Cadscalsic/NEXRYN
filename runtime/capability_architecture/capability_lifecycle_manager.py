"""Capability lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.capability_architecture.capability_contract import (
    CapabilityContract,
    CapabilityLifecycleState,
)


ALLOWED_TRANSITIONS = {
    CapabilityLifecycleState.REGISTERING: {CapabilityLifecycleState.REGISTERED, CapabilityLifecycleState.FAILED, CapabilityLifecycleState.UNREGISTERED},
    CapabilityLifecycleState.REGISTERED: {CapabilityLifecycleState.ACTIVE, CapabilityLifecycleState.SUSPENDED, CapabilityLifecycleState.DEFERRED, CapabilityLifecycleState.DEPRECATED, CapabilityLifecycleState.DISABLED},
    CapabilityLifecycleState.ACTIVE: {CapabilityLifecycleState.SUSPENDED, CapabilityLifecycleState.COMPLETED, CapabilityLifecycleState.FAILED},
    CapabilityLifecycleState.SUSPENDED: {CapabilityLifecycleState.ACTIVE, CapabilityLifecycleState.DEFERRED, CapabilityLifecycleState.DISABLED},
    CapabilityLifecycleState.DEFERRED: {CapabilityLifecycleState.ACTIVE, CapabilityLifecycleState.COMPLETED, CapabilityLifecycleState.DISABLED},
    CapabilityLifecycleState.LEGACY: {CapabilityLifecycleState.REGISTERED, CapabilityLifecycleState.DEPRECATED, CapabilityLifecycleState.DISABLED},
    CapabilityLifecycleState.DEPRECATED: {CapabilityLifecycleState.DISABLED},
    CapabilityLifecycleState.FAILED: {CapabilityLifecycleState.REGISTERED, CapabilityLifecycleState.DISABLED},
}


@dataclass
class CapabilityLifecycleManager:
    transitions: list[dict[str, Any]] = field(default_factory=list)

    def transition(
        self,
        contract: CapabilityContract,
        new_state: CapabilityLifecycleState,
        reason: str,
    ) -> bool:
        previous = contract.lifecycle_state
        allowed = new_state in ALLOWED_TRANSITIONS.get(previous, set())
        self.transitions.append({
            "capability_name": contract.capability_name,
            "previous_state": previous.value,
            "new_state": new_state.value,
            "reason": reason,
            "approved": allowed,
        })
        if allowed:
            contract.lifecycle_state = new_state
        return allowed


__all__ = ["ALLOWED_TRANSITIONS", "CapabilityLifecycleManager"]
