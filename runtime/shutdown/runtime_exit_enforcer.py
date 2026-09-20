"""Final runtime exit enforcement."""

from __future__ import annotations

import logging
import os
import sys

from .thread_monitor import ThreadMonitor
from .worker_termination_manager import WorkerTerminationManager


class RuntimeExitEnforcer:
    def __init__(
        self,
        monitor: ThreadMonitor | None = None,
        worker_manager: WorkerTerminationManager | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.monitor = monitor or ThreadMonitor()
        self.worker_manager = worker_manager or WorkerTerminationManager()
        self.logger = logger or logging.getLogger(__name__)

    def verify_exit_ready(self) -> dict:
        resources = self.monitor.hanging_resources()
        return {
            **resources,
            "no_active_threads": not resources["active_threads"],
            "no_active_processes": not resources["active_processes"],
            "no_pending_tasks": not resources["active_tasks"],
        }

    def force_terminate_remaining_resources(self) -> dict:
        report = self.worker_manager.terminate_all(timeout=0.2)
        report["exit_ready_after_force"] = self.verify_exit_ready()
        return report

    def enforce_exit(self, exit_process: bool = True, code: int = 0) -> dict:
        readiness = self.verify_exit_ready()
        if (
            readiness["no_active_threads"]
            and readiness["no_active_processes"]
            and readiness["no_pending_tasks"]
        ):
            if exit_process:
                sys.exit(code)
            return {"exit": "ready", **readiness}

        force_report = self.force_terminate_remaining_resources()
        readiness = self.verify_exit_ready()
        if exit_process:
            if (
                readiness["no_active_threads"]
                and readiness["no_active_processes"]
                and readiness["no_pending_tasks"]
            ):
                sys.exit(code)
            os._exit(code)
        return {"exit": "forced", **readiness, "force_report": force_report}
