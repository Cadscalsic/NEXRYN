"""Controlled runtime execution strategy escalation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from runtime.resource_governance.execution_policy import ExecutionPolicyName


class RuntimeExecutionStrategy(str, Enum):
    LIGHT_EXECUTION = "LIGHT_EXECUTION"
    BALANCED_EXECUTION = "BALANCED_EXECUTION"
    DEEP_EXECUTION = "DEEP_EXECUTION"
    RECOVERY_EXECUTION = "RECOVERY_EXECUTION"
    DIAGNOSTIC_EXECUTION = "DIAGNOSTIC_EXECUTION"


@dataclass(frozen=True)
class EscalationDecision:
    previous_strategy: RuntimeExecutionStrategy
    new_strategy: RuntimeExecutionStrategy
    escalated: bool
    reason: str
    signal_type: str

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "previous_strategy": self.previous_strategy.value,
            "new_strategy": self.new_strategy.value,
            "escalated": self.escalated,
            "reason": self.reason,
            "signal_type": self.signal_type,
        }


@dataclass
class EscalationController:
    current_strategy: RuntimeExecutionStrategy = RuntimeExecutionStrategy.LIGHT_EXECUTION
    escalation_count: int = 0
    max_escalation_count: int = 3
    decisions: list[EscalationDecision] = field(default_factory=list)

    def evaluate(
        self,
        signal_type: str,
        policy: ExecutionPolicyName = ExecutionPolicyName.BALANCED,
        critical: bool = False,
    ) -> EscalationDecision:
        previous = self.current_strategy
        new = previous
        reason = "no_escalation_required"

        if policy == ExecutionPolicyName.DIAGNOSTIC and signal_type in {"LAYER_FAILED", "CONTRADICTION_DETECTED", "UNRECOVERABLE_FAILURE"}:
            new = RuntimeExecutionStrategy.DIAGNOSTIC_EXECUTION
            reason = "diagnostic_policy_triggered"
        elif signal_type in {"LOCALIZED_RESIDUAL", "RECOVERABLE_FAILURE"}:
            new = RuntimeExecutionStrategy.RECOVERY_EXECUTION
            reason = "recovery_signal_detected"
        elif previous == RuntimeExecutionStrategy.LIGHT_EXECUTION and signal_type in {
            "CONFIDENCE_DROP",
            "RESIDUAL_DETECTED",
            "COMPILER_REJECTED",
            "DEPENDENCY_GAP_DETECTED",
            "ROTATION_SIGNAL_DETECTED",
            "SPATIAL_RELATION_DETECTED",
        }:
            new = RuntimeExecutionStrategy.BALANCED_EXECUTION
            reason = "light_plan_insufficient"
        elif previous == RuntimeExecutionStrategy.BALANCED_EXECUTION and signal_type in {
            "CONTRADICTION_DETECTED",
            "RESIDUAL_COUNT_INCREASED",
            "CANDIDATE_COUNT_LOW",
            "UNSUPPORTED_CONCEPT_DETECTED",
        }:
            new = RuntimeExecutionStrategy.DEEP_EXECUTION
            reason = "balanced_plan_insufficient"
        elif critical and previous == RuntimeExecutionStrategy.LIGHT_EXECUTION:
            new = RuntimeExecutionStrategy.BALANCED_EXECUTION
            reason = "critical_signal_gradual_escalation"

        escalated = new != previous and self.escalation_count < self.max_escalation_count
        if escalated:
            self.current_strategy = new
            self.escalation_count += 1
        else:
            new = previous
        decision = EscalationDecision(previous, new, escalated, reason, str(signal_type))
        self.decisions.append(decision)
        return decision


__all__ = [
    "EscalationController",
    "EscalationDecision",
    "RuntimeExecutionStrategy",
]
