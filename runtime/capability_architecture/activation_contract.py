"""Capability activation contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

class ActivationType(str, Enum):
    ALWAYS_REQUIRED = "ALWAYS_REQUIRED"
    ON_DEMAND = "ON_DEMAND"
    OPTIONAL = "OPTIONAL"
    DEFERRED = "DEFERRED"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    TRAINING_ONLY = "TRAINING_ONLY"
    CHANGE_TRIGGERED = "CHANGE_TRIGGERED"
    POST_EXECUTION_ONLY = "POST_EXECUTION_ONLY"


@dataclass(frozen=True)
class ActivationContract:
    activation_type: ActivationType = ActivationType.ON_DEMAND
    activation_signals: tuple[str, ...] = ()
    execution_policies: tuple[str, ...] = (
        "LOW_LATENCY",
        "BALANCED",
        "MAX_ACCURACY",
        "RESEARCH",
        "DIAGNOSTIC",
        "TRAINING",
    )
    activation_constraints: tuple[str, ...] = ()
    required_budget_types: tuple[str, ...] = ()
    activation_priority: str = "MEDIUM"
    allowed_execution_strategies: tuple[str, ...] = ()

    def allows_policy(self, policy) -> bool:
        return _policy_value(policy) in {_policy_value(item) for item in self.execution_policies}

    def as_dict(self) -> dict[str, Any]:
        return {
            "activation_type": self.activation_type.value,
            "activation_signals": list(self.activation_signals),
            "execution_policies": [_policy_value(policy) for policy in self.execution_policies],
            "activation_constraints": list(self.activation_constraints),
            "required_budget_types": list(self.required_budget_types),
            "activation_priority": self.activation_priority,
            "allowed_execution_strategies": list(self.allowed_execution_strategies),
        }


def _policy_value(policy) -> str:
    return getattr(policy, "value", str(policy))


__all__ = ["ActivationContract", "ActivationType"]
