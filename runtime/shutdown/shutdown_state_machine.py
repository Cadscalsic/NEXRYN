"""Monotonic shutdown state machine."""

from __future__ import annotations

from enum import Enum


class ShutdownState(str, Enum):
    TASK_RUNNING = "TASK_RUNNING"
    TASK_COMPLETED = "TASK_COMPLETED"
    LEARNING_COMMITTED = "LEARNING_COMMITTED"
    SHUTDOWN_STARTED = "SHUTDOWN_STARTED"
    RESOURCE_CLEANUP = "RESOURCE_CLEANUP"
    WORKERS_TERMINATED = "WORKERS_TERMINATED"
    SHUTDOWN_COMPLETED = "SHUTDOWN_COMPLETED"


ORDERED_STATES = (
    ShutdownState.TASK_RUNNING,
    ShutdownState.TASK_COMPLETED,
    ShutdownState.LEARNING_COMMITTED,
    ShutdownState.SHUTDOWN_STARTED,
    ShutdownState.RESOURCE_CLEANUP,
    ShutdownState.WORKERS_TERMINATED,
    ShutdownState.SHUTDOWN_COMPLETED,
)

ALLOWED_TRANSITIONS = {
    ORDERED_STATES[index]: ORDERED_STATES[index + 1]
    for index in range(len(ORDERED_STATES) - 1)
}


class ShutdownStateMachine:
    """Allows only forward progress through shutdown."""

    def __init__(self) -> None:
        self.state = ShutdownState.TASK_RUNNING
        self.history = [self.state.value]

    def transition_to(self, target: ShutdownState | str) -> ShutdownState:
        target = ShutdownState(target)
        if target == self.state:
            return self.state
        expected = ALLOWED_TRANSITIONS.get(self.state)
        if target != expected:
            raise ValueError(
                f"Invalid shutdown transition: {self.state.value} -> {target.value}"
            )
        self.state = target
        self.history.append(target.value)
        return self.state

    def advance(self) -> ShutdownState:
        expected = ALLOWED_TRANSITIONS.get(self.state)
        if expected is None:
            return self.state
        return self.transition_to(expected)

    def as_report(self) -> dict:
        return {
            "state": self.state.value,
            "history": list(self.history),
            "terminal": self.state == ShutdownState.SHUTDOWN_COMPLETED,
        }
