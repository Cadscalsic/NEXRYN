"""Activation safeguards for adaptive execution transitions."""

from __future__ import annotations

from dataclasses import dataclass, field

from runtime.resource_governance.execution_policy import ExecutionPolicyName
from runtime.resource_governance.layer_state_registry import LayerState


class ActivationRejectionReason:
    LAYER_NOT_REGISTERED = "LAYER_NOT_REGISTERED"
    CAPABILITY_NOT_REGISTERED = "CAPABILITY_NOT_REGISTERED"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    DEPENDENCY_CYCLE = "DEPENDENCY_CYCLE"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    ACTIVATION_LIMIT_REACHED = "ACTIVATION_LIMIT_REACHED"
    TERMINAL_STATE_REACHED = "TERMINAL_STATE_REACHED"
    LAYER_ALREADY_COMPLETED = "LAYER_ALREADY_COMPLETED"
    LAYER_BLOCKED = "LAYER_BLOCKED"
    ACTIVATION_LOOP_DETECTED = "ACTIVATION_LOOP_DETECTED"
    INVALID_EXECUTION_CONTEXT = "INVALID_EXECUTION_CONTEXT"


@dataclass(frozen=True)
class ActivationGuardDecision:
    approved: bool
    rejection_reason: str | None = None
    detail: str = ""


@dataclass
class ActivationGuardLimits:
    max_escalation_count: int = 3
    max_activation_count_per_layer: int = 2
    max_repeated_signal_count: int = 4
    max_dependency_depth: int = 6
    max_transition_count: int = 50
    cooldown_transitions: int = 1


@dataclass
class ActivationGuard:
    limits: ActivationGuardLimits = field(default_factory=ActivationGuardLimits)
    activation_counts: dict[str, int] = field(default_factory=dict)
    signal_counts: dict[str, int] = field(default_factory=dict)
    guard_events: list[dict[str, str]] = field(default_factory=list)
    terminal_success: bool = False
    _recent_pairs: list[tuple[str, str]] = field(default_factory=list)

    def note_signal(self, signal_type: str) -> None:
        self.signal_counts[str(signal_type)] = self.signal_counts.get(str(signal_type), 0) + 1

    def approve_activation(
        self,
        execution_id: str,
        layer_name: str,
        previous_state: LayerState,
        signal_type: str,
        policy: ExecutionPolicyName,
        transition_count: int,
        dependency_cycle: bool = False,
        dependency_missing: bool = False,
        policy_constraints: tuple[str, ...] = (),
    ) -> ActivationGuardDecision:
        reason = None
        if not execution_id:
            reason = ActivationRejectionReason.INVALID_EXECUTION_CONTEXT
        elif self.terminal_success:
            reason = ActivationRejectionReason.TERMINAL_STATE_REACHED
        elif previous_state == LayerState.NOT_REGISTERED:
            reason = ActivationRejectionReason.LAYER_NOT_REGISTERED
        elif previous_state == LayerState.BLOCKED:
            reason = ActivationRejectionReason.LAYER_BLOCKED
        elif previous_state == LayerState.COMPLETED:
            reason = ActivationRejectionReason.LAYER_ALREADY_COMPLETED
        elif dependency_cycle:
            reason = ActivationRejectionReason.DEPENDENCY_CYCLE
        elif dependency_missing:
            reason = ActivationRejectionReason.DEPENDENCY_MISSING
        elif transition_count >= self.limits.max_transition_count:
            reason = ActivationRejectionReason.ACTIVATION_LIMIT_REACHED
        elif self.activation_counts.get(layer_name, 0) >= self.limits.max_activation_count_per_layer:
            reason = ActivationRejectionReason.ACTIVATION_LIMIT_REACHED
        elif self.signal_counts.get(str(signal_type), 0) > self.limits.max_repeated_signal_count:
            reason = ActivationRejectionReason.ACTIVATION_LOOP_DETECTED
        elif policy_constraints and policy.value not in policy_constraints:
            reason = ActivationRejectionReason.POLICY_BLOCKED
        elif (layer_name, str(signal_type)) in self._recent_pairs:
            reason = ActivationRejectionReason.ACTIVATION_LOOP_DETECTED

        if reason is not None:
            self.guard_events.append({
                "layer_name": layer_name,
                "signal_type": str(signal_type),
                "rejection_reason": reason,
            })
            return ActivationGuardDecision(False, reason)
        return ActivationGuardDecision(True)

    def record_activation(self, layer_name: str, signal_type: str) -> None:
        self.activation_counts[layer_name] = self.activation_counts.get(layer_name, 0) + 1
        self._recent_pairs.append((layer_name, str(signal_type)))
        self._recent_pairs = self._recent_pairs[-self.limits.cooldown_transitions:]

    def mark_terminal_success(self) -> None:
        self.terminal_success = True


__all__ = [
    "ActivationGuard",
    "ActivationGuardDecision",
    "ActivationGuardLimits",
    "ActivationRejectionReason",
]
