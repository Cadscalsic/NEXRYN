"""Budget consumption and resource request enforcement."""

from __future__ import annotations

from runtime.resource_governance.cognitive_budget import (
    CognitiveBudget,
    ResourceRequest,
    ResourceRequestDecision,
    ResourceRequestDecisionType,
)
from runtime.resource_governance.execution_policy import ExecutionPolicyName


class BudgetEnforcer:
    def __init__(self):
        self.ledger: list[dict[str, object]] = []
        self.request_keys: set[tuple[str, str, str]] = set()
        self.violation_count = 0

    def consume(self, budget: CognitiveBudget, resource_type: str, amount: float) -> bool:
        budget.consume(resource_type, amount)
        exhausted = budget.remaining(resource_type) <= 0.0
        if exhausted:
            self.violation_count += 1
        self.ledger.append({
            "resource_type": resource_type,
            "amount": amount,
            "used": budget.used(resource_type),
            "remaining": budget.remaining(resource_type),
            "exhausted": exhausted,
        })
        return not exhausted

    def evaluate_request(
        self,
        budget: CognitiveBudget,
        request: ResourceRequest,
        policy: ExecutionPolicyName,
        terminal: bool = False,
        pressure: str = "NORMAL",
    ) -> ResourceRequestDecision:
        if terminal:
            return self._decision(ResourceRequestDecisionType.REJECTED_TERMINAL_STATE, 0.0, "terminal_state_reached", request)
        if request.key() in self.request_keys:
            return self._decision(ResourceRequestDecisionType.REJECTED_DUPLICATE_REQUEST, 0.0, "duplicate_resource_request", request)
        if policy == ExecutionPolicyName.LOW_LATENCY and request.urgency.upper() == "LOW":
            return self._decision(ResourceRequestDecisionType.REJECTED_POLICY, 0.0, "low_latency_policy_blocks_low_urgency_request", request)
        if request.expected_value < 0.2 and request.urgency.upper() != "CRITICAL":
            return self._decision(ResourceRequestDecisionType.REJECTED_LOW_VALUE, 0.0, "expected_value_too_low", request)
        remaining = budget.remaining(request.resource_type)
        if remaining <= 0:
            return self._decision(ResourceRequestDecisionType.REJECTED_BUDGET, 0.0, "budget_exhausted", request)
        if pressure in {"HIGH", "CRITICAL"} and request.expected_value < 0.7:
            return self._decision(ResourceRequestDecisionType.REJECTED_LOW_VALUE, 0.0, "budget_pressure_requires_higher_value", request)
        self.request_keys.add(request.key())
        if remaining < request.requested_amount:
            return self._decision(ResourceRequestDecisionType.PARTIALLY_APPROVED, remaining, "partial_budget_available", request)
        return self._decision(ResourceRequestDecisionType.APPROVED, request.requested_amount, "budget_available", request)

    def _decision(self, decision, amount, reason, request):
        item = ResourceRequestDecision(decision, amount, reason, request)
        self.ledger.append(item.as_dict())
        return item


__all__ = ["BudgetEnforcer"]
