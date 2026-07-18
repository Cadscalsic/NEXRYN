"""Reusable cognitive strategy descriptors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StrategyDescriptor:
    strategy_id: str
    strategy_name: str
    task_family: str
    capability_sequence: tuple[str, ...] = ()
    activation_order: tuple[str, ...] = ()
    escalation_rules: tuple[str, ...] = ()
    average_cost: float = 0.0
    average_success_rate: float = 0.0
    policy_preferences: tuple[str, ...] = ()
    recommended_budget: dict[str, float] = field(default_factory=dict)
    failure_patterns: tuple[str, ...] = ()
    terminal_state_statistics: dict[str, int] = field(default_factory=dict)
    status: str = "ACTIVE"

    def as_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "task_family": self.task_family,
            "capability_sequence": list(self.capability_sequence),
            "activation_order": list(self.activation_order),
            "escalation_rules": list(self.escalation_rules),
            "average_cost": self.average_cost,
            "average_success_rate": self.average_success_rate,
            "policy_preferences": list(self.policy_preferences),
            "recommended_budget": dict(self.recommended_budget),
            "failure_patterns": list(self.failure_patterns),
            "terminal_state_statistics": dict(self.terminal_state_statistics),
            "status": self.status,
        }


__all__ = ["StrategyDescriptor"]
