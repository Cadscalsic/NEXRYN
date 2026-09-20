"""Queue for expensive reports that must not run during shutdown."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Deque


DEFERRED_REPORT_TYPES = {
    "concept_debug_reports",
    "training_reports",
    "governance_summaries",
    "telemetry_exports",
    "long_term_statistics",
}

QUEUE_MODES = {"background", "next_runtime_cycle", "manual_analysis_mode"}


@dataclass
class DeferredReportTask:
    report_type: str
    payload: dict[str, Any]
    mode: str = "next_runtime_cycle"


class DeferredReportingQueue:
    def __init__(self) -> None:
        self._queue: Deque[DeferredReportTask] = deque()

    def defer(
        self,
        report_type: str,
        payload: dict[str, Any] | None = None,
        mode: str = "next_runtime_cycle",
    ) -> DeferredReportTask:
        if report_type not in DEFERRED_REPORT_TYPES:
            report_type = "telemetry_exports"
        if mode not in QUEUE_MODES:
            mode = "next_runtime_cycle"
        task = DeferredReportTask(report_type, dict(payload or {}), mode)
        self._queue.append(task)
        return task

    def defer_expensive_defaults(self, mode: str = "next_runtime_cycle") -> int:
        before = len(self._queue)
        for report_type in sorted(DEFERRED_REPORT_TYPES):
            self.defer(report_type, {"deferred_by": "evaluation_controller"}, mode)
        return len(self._queue) - before

    def pending_count(self) -> int:
        return len(self._queue)

    def snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "report_type": task.report_type,
                "payload": dict(task.payload),
                "mode": task.mode,
            }
            for task in self._queue
        ]

    def execute_during_shutdown(self) -> list[Any]:
        return []
