"""Shutdown report construction."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


SHUTDOWN_REPORT = "SHUTDOWN_REPORT"


@dataclass
class ShutdownReporter:
    shutdown_start_time: float = field(default_factory=time.time)
    cleanup_duration: float = 0.0
    terminated_resources: list = field(default_factory=list)
    cleanup_failures: list = field(default_factory=list)
    forced_termination: bool = False
    post_completion_started_at: float | None = None
    active_threads: list = field(default_factory=list)
    active_processes: list = field(default_factory=list)

    def mark_cleanup_duration(self, duration: float) -> None:
        self.cleanup_duration = round(float(duration), 4)

    def add_terminated(self, resource: dict) -> None:
        self.terminated_resources.append(resource)

    def add_failure(self, failure: dict) -> None:
        self.cleanup_failures.append(failure)

    def build(self, active_threads=None, active_processes=None) -> dict:
        now = time.time()
        if active_threads is not None:
            self.active_threads = list(active_threads)
        if active_processes is not None:
            self.active_processes = list(active_processes)
        return {
            "shutdown_start_time": self.shutdown_start_time,
            "shutdown_duration": round(now - self.shutdown_start_time, 4),
            "cleanup_duration": self.cleanup_duration,
            "active_threads": list(self.active_threads),
            "active_processes": list(self.active_processes),
            "terminated_resources": list(self.terminated_resources),
            "cleanup_failures": list(self.cleanup_failures),
            "forced_termination": self.forced_termination,
            "post_completion_latency": round(
                now - self.post_completion_started_at,
                4,
            )
            if self.post_completion_started_at is not None
            else 0.0,
        }
