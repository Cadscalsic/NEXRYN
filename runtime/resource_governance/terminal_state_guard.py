"""Terminal-state protection for resource governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


CRITICAL_COMPLETION_WORK = {
    "final_result_preservation",
    "minimal_evaluation_state",
    "minimal_execution_metadata",
    "critical_error_reporting",
    "lightweight_timing_summary",
    "deferred_work_declaration",
    "minimal_safe_checkpoint",
}


@dataclass
class TerminalRecord:
    state: str
    termination_reason: str
    final_prediction_state: Any = None
    final_confidence: float | None = None
    remaining_budget: dict[str, Any] | None = None
    best_candidate: Any = None
    unresolved_residual: Any = None
    deferred_work_requirements: list[str] = field(default_factory=list)
    critical_persistence_requirements: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "termination_reason": self.termination_reason,
            "final_prediction_state": self.final_prediction_state,
            "final_confidence": self.final_confidence,
            "remaining_budget": self.remaining_budget or {},
            "best_candidate": self.best_candidate,
            "unresolved_residual": self.unresolved_residual,
            "deferred_work_requirements": list(self.deferred_work_requirements),
            "critical_persistence_requirements": list(self.critical_persistence_requirements),
        }


class TerminalStateGuard:
    def __init__(self):
        self.terminal_record: TerminalRecord | None = None
        self.minimal_finalization = False
        self.rejections: list[dict[str, str]] = []

    @property
    def terminal(self) -> bool:
        return self.terminal_record is not None

    def enter_terminal(self, record: TerminalRecord) -> TerminalRecord:
        self.terminal_record = record
        return record

    def enter_minimal_finalization(self) -> None:
        self.minimal_finalization = True

    def allow(self, action: str, critical: bool = False) -> bool:
        if not self.terminal:
            return True
        if critical or action in CRITICAL_COMPLETION_WORK:
            return True
        self.rejections.append({"action": action, "reason": "TERMINAL_STATE_REACHED"})
        return False


__all__ = ["CRITICAL_COMPLETION_WORK", "TerminalRecord", "TerminalStateGuard"]
