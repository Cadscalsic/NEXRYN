"""Adaptive runtime closure state and reporting primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResultLifecycleState(str, Enum):
    TASK_RUNNING = "TASK_RUNNING"
    TERMINAL_STATE_REACHED = "TERMINAL_STATE_REACHED"
    MINIMAL_FINALIZATION = "MINIMAL_FINALIZATION"
    RESULT_AVAILABLE = "RESULT_AVAILABLE"
    POST_PROCESSING_PENDING = "POST_PROCESSING_PENDING"
    MAINTENANCE_COMPLETE = "MAINTENANCE_COMPLETE"


class ClosureState(str, Enum):
    CLOSED_CLEANLY = "CLOSED_CLEANLY"
    CLOSED_WITH_DEFERRED_MAINTENANCE = "CLOSED_WITH_DEFERRED_MAINTENANCE"
    CLOSED_WITH_MAINTENANCE_FAILURE = "CLOSED_WITH_MAINTENANCE_FAILURE"
    CLOSED_WITH_POLICY_VIOLATION = "CLOSED_WITH_POLICY_VIOLATION"
    CLOSURE_FAILED = "CLOSURE_FAILED"


@dataclass
class RuntimeClosureRecord:
    lifecycle_state: ResultLifecycleState = ResultLifecycleState.TASK_RUNNING
    task_result_status: str = "RUNNING"
    post_processing_status: str = "NOT_STARTED"
    maintenance_status: str = "NOT_STARTED"
    closure_state: ClosureState | None = None
    validation_errors: list[str] = field(default_factory=list)

    @property
    def result_available(self) -> bool:
        return self.lifecycle_state in {
            ResultLifecycleState.RESULT_AVAILABLE,
            ResultLifecycleState.POST_PROCESSING_PENDING,
            ResultLifecycleState.MAINTENANCE_COMPLETE,
        }

    def transition(self, state: ResultLifecycleState) -> None:
        self.lifecycle_state = state

    def validate(
        self,
        terminal_state: str | None,
        critical_completed: bool,
        deferred_count: int,
        prohibited_count: int,
        bypass_count: int,
        policy_violation_count: int,
        maintenance_failure_count: int,
    ) -> ClosureState:
        self.validation_errors.clear()
        if not terminal_state:
            self.validation_errors.append("TERMINAL_STATE_MISSING")
        if not self.result_available:
            self.validation_errors.append("RESULT_NOT_AVAILABLE")
        if not critical_completed:
            self.validation_errors.append("CRITICAL_FINALIZATION_INCOMPLETE")
        if prohibited_count:
            self.validation_errors.append("PROHIBITED_WORK_PRESENT")
        if bypass_count:
            self.validation_errors.append("GOVERNOR_BYPASS_DETECTED")
        if policy_violation_count:
            self.validation_errors.append("POLICY_VIOLATION_DETECTED")

        if self.validation_errors:
            self.closure_state = (
                ClosureState.CLOSED_WITH_POLICY_VIOLATION
                if {"GOVERNOR_BYPASS_DETECTED", "POLICY_VIOLATION_DETECTED", "PROHIBITED_WORK_PRESENT"}
                & set(self.validation_errors)
                else ClosureState.CLOSURE_FAILED
            )
        elif maintenance_failure_count:
            self.closure_state = ClosureState.CLOSED_WITH_MAINTENANCE_FAILURE
        elif deferred_count:
            self.closure_state = ClosureState.CLOSED_WITH_DEFERRED_MAINTENANCE
        else:
            self.closure_state = ClosureState.CLOSED_CLEANLY
        return self.closure_state

    def as_dict(self) -> dict[str, Any]:
        return {
            "lifecycle_state": self.lifecycle_state.value,
            "task_result_status": self.task_result_status,
            "post_processing_status": self.post_processing_status,
            "maintenance_status": self.maintenance_status,
            "closure_state": self.closure_state.value if self.closure_state else None,
            "validation_errors": list(self.validation_errors),
            "result_available": self.result_available,
        }


__all__ = ["ClosureState", "ResultLifecycleState", "RuntimeClosureRecord"]
