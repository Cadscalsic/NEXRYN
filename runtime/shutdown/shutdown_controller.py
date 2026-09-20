"""Single authority for deterministic runtime termination."""

from __future__ import annotations

import faulthandler
import logging
import time

from .post_success_isolation import PostSuccessIsolation
from .resource_cleanup_manager import ResourceCleanupManager
from .runtime_exit_enforcer import RuntimeExitEnforcer
from .shutdown_reporter import SHUTDOWN_REPORT, ShutdownReporter
from .shutdown_state_machine import ShutdownState, ShutdownStateMachine
from .shutdown_timeout_guard import ShutdownTimeoutGuard
from .thread_monitor import ThreadMonitor
from .worker_termination_manager import WorkerTerminationManager


class ShutdownController:
    def __init__(
        self,
        resource_cleanup_manager: ResourceCleanupManager | None = None,
        worker_termination_manager: WorkerTerminationManager | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.state_machine = ShutdownStateMachine()
        self.isolation = PostSuccessIsolation()
        self.resource_cleanup_manager = (
            resource_cleanup_manager or ResourceCleanupManager(self.logger)
        )
        self.worker_termination_manager = (
            worker_termination_manager or WorkerTerminationManager(self.logger)
        )
        self.monitor = ThreadMonitor()
        self.timeout_guard = ShutdownTimeoutGuard(logger=self.logger)
        self.reporter = ShutdownReporter()
        self.exit_enforcer = RuntimeExitEnforcer(
            monitor=self.monitor,
            worker_manager=self.worker_termination_manager,
            logger=self.logger,
        )
        self._faulthandler_enabled = False

    def begin_shutdown(self, context: dict | None = None) -> dict:
        context = context if isinstance(context, dict) else {}
        self.logger.info("[SHUTDOWN] start")
        self.timeout_guard.start()
        self.reporter.shutdown_start_time = time.time()
        self.reporter.post_completion_started_at = time.time()
        self._enable_fault_handler()
        if self.state_machine.state == ShutdownState.TASK_RUNNING:
            self.state_machine.transition_to(ShutdownState.TASK_COMPLETED)
        self.isolation.activate(context)
        context["shutdown_state"] = self.state_machine.as_report()
        context["shutdown_mode"] = context.get("shutdown_mode", "fast")
        return context

    def commit_learning(self, context: dict | None = None) -> dict:
        context = context if isinstance(context, dict) else {}
        self.logger.info("[SHUTDOWN] committing learning")
        self.logger.info("[SHUTDOWN] flushing memory")
        if self.state_machine.state == ShutdownState.TASK_COMPLETED:
            self.state_machine.transition_to(ShutdownState.LEARNING_COMMITTED)
        if self.state_machine.state == ShutdownState.LEARNING_COMMITTED:
            self.state_machine.transition_to(ShutdownState.SHUTDOWN_STARTED)
        context.setdefault("learning_commit", {"status": "preserved"})
        context["shutdown_state"] = self.state_machine.as_report()
        return context

    def cleanup_resources(self, context: dict | None = None) -> dict:
        context = context if isinstance(context, dict) else {}
        if self.state_machine.state == ShutdownState.SHUTDOWN_STARTED:
            self.state_machine.transition_to(ShutdownState.RESOURCE_CLEANUP)
        cleanup_start = time.perf_counter()
        cleanup_report = self.resource_cleanup_manager.cleanup_all()
        cleanup_duration = time.perf_counter() - cleanup_start
        self.reporter.mark_cleanup_duration(cleanup_duration)
        for failure in cleanup_report.get("cleanup_failures", []):
            self.reporter.add_failure(failure)
        context["resource_cleanup_report"] = cleanup_report
        self.timeout_guard.check(self.force_shutdown)
        return context

    def terminate_workers(self, context: dict | None = None) -> dict:
        context = context if isinstance(context, dict) else {}
        worker_report = self.worker_termination_manager.terminate_all(timeout=0.2)
        for resource in worker_report.get("terminated_resources", []):
            self.reporter.add_terminated(resource)
        for failure in worker_report.get("worker_failures", []):
            self.reporter.add_failure(failure)
        if self.state_machine.state == ShutdownState.RESOURCE_CLEANUP:
            self.state_machine.transition_to(ShutdownState.WORKERS_TERMINATED)
        context["worker_termination_report"] = worker_report
        self.timeout_guard.check(self.force_shutdown)
        return context

    def complete_shutdown(
        self,
        context: dict | None = None,
        exit_process: bool = False,
    ) -> dict:
        context = context if isinstance(context, dict) else {}
        if self.state_machine.state == ShutdownState.WORKERS_TERMINATED:
            self.state_machine.transition_to(ShutdownState.SHUTDOWN_COMPLETED)
        resources = self.monitor.hanging_resources()
        report = self.reporter.build(
            active_threads=resources["active_threads"],
            active_processes=resources["active_processes"],
        )
        report["active_tasks"] = resources["active_tasks"]
        report["state_machine"] = self.state_machine.as_report()
        report["post_success_isolation"] = self.isolation.build_report()
        report["timeout_exceeded"] = self.timeout_guard.timeout_exceeded
        context[SHUTDOWN_REPORT] = report
        context["shutdown_state"] = self.state_machine.as_report()
        self._disable_fault_handler()
        self.logger.info("[SHUTDOWN] completed")
        if exit_process:
            self.exit_enforcer.enforce_exit(exit_process=True, code=0)
        return context

    def execute_shutdown(
        self,
        context: dict | None = None,
        exit_process: bool = False,
    ) -> dict:
        context = self.begin_shutdown(context)
        context = self.commit_learning(context)
        context = self.cleanup_resources(context)
        context = self.terminate_workers(context)
        return self.complete_shutdown(context, exit_process=exit_process)

    def force_shutdown(self) -> None:
        self.reporter.forced_termination = True
        self.worker_termination_manager.terminate_all(timeout=0.1)

    def _enable_fault_handler(self) -> None:
        try:
            faulthandler.dump_traceback_later(timeout=30, repeat=True)
            self._faulthandler_enabled = True
        except Exception as error:
            self.logger.warning("[SHUTDOWN] faulthandler enable failed: %s", error)

    def _disable_fault_handler(self) -> None:
        if not self._faulthandler_enabled:
            return
        try:
            faulthandler.cancel_dump_traceback_later()
        except Exception as error:
            self.logger.warning("[SHUTDOWN] faulthandler disable failed: %s", error)
        finally:
            self._faulthandler_enabled = False
