"""Canonical early termination controller."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TerminalState(str, Enum):
    EXACT_SUCCESS = "EXACT_SUCCESS"
    ACCEPTED_PARTIAL_SUCCESS = "ACCEPTED_PARTIAL_SUCCESS"
    BEST_EFFORT_BUDGET_EXHAUSTED = "BEST_EFFORT_BUDGET_EXHAUSTED"
    UNRECOVERABLE_FAILURE = "UNRECOVERABLE_FAILURE"
    NO_VALUE_CONVERGENCE = "NO_VALUE_CONVERGENCE"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"
    REPAIR_EXHAUSTED = "REPAIR_EXHAUSTED"
    CRITICAL_GOVERNANCE_FAILURE = "CRITICAL_GOVERNANCE_FAILURE"
    CANCELLED = "CANCELLED"
    RUNTIME_FAILURE = "RUNTIME_FAILURE"


@dataclass(frozen=True)
class TerminationDecision:
    should_terminate: bool
    terminal_state: TerminalState | None = None
    reason: str = ""
    evidence: dict[str, Any] | None = None


class EarlyTerminationController:
    def evaluate(
        self,
        signal_type: str = "",
        budget_pressure: str = "NORMAL",
        diminishing_state: str = "VALUE_STABLE",
        retries_used: float = 0,
        max_retries: float = 1,
        repairs_used: float = 0,
        max_repairs: float = 1,
        partial_success: dict[str, Any] | None = None,
        external_stop: bool = False,
        critical_failure: bool = False,
    ) -> TerminationDecision:
        if signal_type == "EXACT_SUCCESS":
            return TerminationDecision(True, TerminalState.EXACT_SUCCESS, "exact_success_confirmed")
        if external_stop:
            return TerminationDecision(True, TerminalState.CANCELLED, "external_stop_requested")
        if critical_failure:
            return TerminationDecision(True, TerminalState.CRITICAL_GOVERNANCE_FAILURE, "critical_governance_failure")
        if signal_type == "UNRECOVERABLE_FAILURE":
            return TerminationDecision(True, TerminalState.UNRECOVERABLE_FAILURE, "unrecoverable_failure")
        if diminishing_state == "NO_VALUE":
            return TerminationDecision(True, TerminalState.NO_VALUE_CONVERGENCE, "no_value_convergence")
        if retries_used >= max_retries and max_retries >= 0:
            return TerminationDecision(True, TerminalState.RETRY_EXHAUSTED, "retry_budget_exhausted")
        if repairs_used >= max_repairs and max_repairs >= 0:
            return TerminationDecision(True, TerminalState.REPAIR_EXHAUSTED, "repair_budget_exhausted")
        if budget_pressure == "EXHAUSTED":
            return TerminationDecision(True, TerminalState.BEST_EFFORT_BUDGET_EXHAUSTED, "budget_exhausted")
        if partial_success and partial_success.get("policy_permits") and partial_success.get("accuracy", 0.0) >= partial_success.get("accuracy_threshold", 0.9) and partial_success.get("remaining_residual", 1) <= partial_success.get("residual_threshold", 0):
            return TerminationDecision(True, TerminalState.ACCEPTED_PARTIAL_SUCCESS, "partial_success_accepted", partial_success)
        return TerminationDecision(False)


__all__ = ["EarlyTerminationController", "TerminalState", "TerminationDecision"]
