"""Canonical cognitive budget objects for adaptive execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BudgetPressureState(str, Enum):
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EXHAUSTED = "EXHAUSTED"


class ResourceRequestDecisionType(str, Enum):
    APPROVED = "APPROVED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"
    REJECTED_BUDGET = "REJECTED_BUDGET"
    REJECTED_LOW_VALUE = "REJECTED_LOW_VALUE"
    REJECTED_POLICY = "REJECTED_POLICY"
    REJECTED_TERMINAL_STATE = "REJECTED_TERMINAL_STATE"
    REJECTED_DUPLICATE_REQUEST = "REJECTED_DUPLICATE_REQUEST"


@dataclass
class CognitiveBudget:
    execution_id: str
    task_id: str
    policy: str
    max_wall_time_seconds: float
    max_active_compute_seconds: float
    max_reasoning_depth: int
    max_dependency_depth: int
    max_active_routes: int
    max_hypotheses: int
    max_candidates: int
    max_retries: int
    max_repairs: int
    max_escalations: int
    max_layer_activations: int
    max_memory_growth_bytes: int
    max_report_cost_seconds: float
    max_post_success_seconds: float
    max_serialization_seconds: float
    max_maintenance_seconds: float
    created_at: float = 0.0
    consumed: dict[str, float] = field(default_factory=dict)

    def limits(self) -> dict[str, float]:
        return {
            "wall_time_seconds": self.max_wall_time_seconds,
            "active_compute_seconds": self.max_active_compute_seconds,
            "reasoning_depth": float(self.max_reasoning_depth),
            "dependency_depth": float(self.max_dependency_depth),
            "active_routes": float(self.max_active_routes),
            "hypotheses": float(self.max_hypotheses),
            "candidates": float(self.max_candidates),
            "retries": float(self.max_retries),
            "repairs": float(self.max_repairs),
            "escalations": float(self.max_escalations),
            "layer_activations": float(self.max_layer_activations),
            "memory_growth_bytes": float(self.max_memory_growth_bytes),
            "report_cost_seconds": self.max_report_cost_seconds,
            "post_success_seconds": self.max_post_success_seconds,
            "serialization_seconds": self.max_serialization_seconds,
            "maintenance_seconds": self.max_maintenance_seconds,
        }

    def used(self, resource_type: str) -> float:
        return float(self.consumed.get(resource_type, 0.0))

    def remaining(self, resource_type: str) -> float:
        return max(0.0, self.limits().get(resource_type, 0.0) - self.used(resource_type))

    def consume(self, resource_type: str, amount: float) -> float:
        amount = max(0.0, float(amount))
        self.consumed[resource_type] = self.used(resource_type) + amount
        return self.consumed[resource_type]

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "policy": self.policy,
            "limits": self.limits(),
            "consumed": dict(self.consumed),
        }


@dataclass(frozen=True)
class ResourceRequest:
    layer_name: str
    resource_type: str
    requested_amount: float
    reason: str
    expected_value: float = 0.0
    urgency: str = "MEDIUM"
    request_id: str | None = None

    def key(self) -> tuple[str, str, str]:
        return (self.layer_name, self.resource_type, self.reason)


@dataclass(frozen=True)
class ResourceRequestDecision:
    decision: ResourceRequestDecisionType
    approved_amount: float
    reason: str
    request: ResourceRequest

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "approved_amount": self.approved_amount,
            "reason": self.reason,
            "layer_name": self.request.layer_name,
            "resource_type": self.request.resource_type,
            "requested_amount": self.request.requested_amount,
            "expected_value": self.request.expected_value,
            "urgency": self.request.urgency,
        }


__all__ = [
    "BudgetPressureState",
    "CognitiveBudget",
    "ResourceRequest",
    "ResourceRequestDecision",
    "ResourceRequestDecisionType",
]
