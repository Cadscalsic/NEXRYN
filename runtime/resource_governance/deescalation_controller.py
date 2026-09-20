"""Controlled runtime de-escalation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from runtime.resource_governance.diminishing_return_detector import DiminishingReturnState
from runtime.resource_governance.escalation_controller import RuntimeExecutionStrategy


class FinalizationStrategy(str, Enum):
    MINIMAL_FINALIZATION = "MINIMAL_FINALIZATION"


@dataclass(frozen=True)
class DeescalationDecision:
    previous_strategy: str
    new_strategy: str
    deescalated: bool
    reason: str

    def as_dict(self):
        return {
            "previous_strategy": self.previous_strategy,
            "new_strategy": self.new_strategy,
            "deescalated": self.deescalated,
            "reason": self.reason,
        }


@dataclass
class DeescalationController:
    decisions: list[DeescalationDecision] = field(default_factory=list)

    def evaluate(self, current_strategy: str, signal_type: str = "", diminishing_state: str = "VALUE_STABLE", terminal: bool = False) -> DeescalationDecision:
        previous = current_strategy
        new = previous
        reason = "no_deescalation_required"
        if terminal or signal_type in {"EXACT_SUCCESS", "UNRECOVERABLE_FAILURE"}:
            new = FinalizationStrategy.MINIMAL_FINALIZATION.value
            reason = "terminal_minimal_finalization"
        elif current_strategy == RuntimeExecutionStrategy.RECOVERY_EXECUTION.value and signal_type in {"RESIDUAL_COUNT_DECREASED", "CONFIDENCE_STABILIZED"}:
            new = RuntimeExecutionStrategy.BALANCED_EXECUTION.value
            reason = "bounded_recovery_complete"
        elif current_strategy == RuntimeExecutionStrategy.DEEP_EXECUTION.value and signal_type in {"CONFIDENCE_STABILIZED", "CONTRADICTION_RESOLVED"}:
            new = RuntimeExecutionStrategy.BALANCED_EXECUTION.value
            reason = "deep_work_no_longer_required"
        elif current_strategy == RuntimeExecutionStrategy.BALANCED_EXECUTION.value and signal_type in {"RESIDUAL_COUNT_DECREASED", "CONFIDENCE_STABILIZED"}:
            new = RuntimeExecutionStrategy.LIGHT_EXECUTION.value
            reason = "light_execution_sufficient"
        elif diminishing_state in {DiminishingReturnState.DIMINISHING_RETURNS.value, DiminishingReturnState.NO_VALUE.value} and current_strategy == RuntimeExecutionStrategy.DEEP_EXECUTION.value:
            new = RuntimeExecutionStrategy.BALANCED_EXECUTION.value
            reason = "diminishing_returns"
        decision = DeescalationDecision(previous, new, new != previous, reason)
        self.decisions.append(decision)
        return decision


__all__ = ["DeescalationController", "DeescalationDecision", "FinalizationStrategy"]
