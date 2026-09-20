"""Terminate thread, process, executor, and asyncio workers."""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import multiprocessing
import threading
import time
from typing import Any


class WorkerTerminationManager:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.workers: list[Any] = []
        self.terminated_resources: list[dict] = []
        self.failures: list[dict] = []

    def register(self, worker: Any) -> Any:
        self.workers.append(worker)
        return worker

    def terminate_all(self, timeout: float = 1.0) -> dict:
        started = time.perf_counter()
        self.logger.info("[SHUTDOWN] stopping workers")
        for worker in list(self.workers):
            self._terminate_worker(worker, timeout=timeout)
        self._terminate_asyncio_tasks()
        self._terminate_processes(timeout=timeout)
        self._join_threads(timeout=timeout)
        return {
            "duration": round(time.perf_counter() - started, 4),
            "terminated_resources": list(self.terminated_resources),
            "worker_failures": list(self.failures),
        }

    def _record(self, kind: str, worker: Any, success: bool, reason: str | None = None) -> None:
        entry = {
            "kind": kind,
            "resource": repr(worker),
            "success": success,
            "failure_reason": reason,
        }
        if success:
            self.terminated_resources.append(entry)
        else:
            self.failures.append(entry)

    def _terminate_worker(self, worker: Any, timeout: float) -> None:
        try:
            if isinstance(worker, concurrent.futures.Executor):
                self.logger.info("[SHUTDOWN] closing executors")
                try:
                    worker.shutdown(wait=False, cancel_futures=True)
                except TypeError:
                    worker.shutdown(wait=False)
                self._record("executor", worker, True)
            elif isinstance(worker, multiprocessing.Process):
                if worker.is_alive():
                    worker.terminate()
                    worker.join(timeout)
                self._record("process", worker, not worker.is_alive())
            elif isinstance(worker, threading.Thread):
                if worker is not threading.current_thread():
                    worker.join(timeout=timeout)
                self._record("thread", worker, not worker.is_alive())
            elif isinstance(worker, asyncio.Task):
                worker.cancel()
                self._record("async_task", worker, True)
            elif hasattr(worker, "terminate"):
                worker.terminate()
                self._record("background_worker", worker, True)
            elif hasattr(worker, "shutdown"):
                worker.shutdown(wait=False)
                self._record("background_worker", worker, True)
        except Exception as error:
            self._record(type(worker).__name__, worker, False, str(error))

    def _terminate_asyncio_tasks(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        for task in asyncio.all_tasks(loop):
            if not task.done() and task is not asyncio.current_task(loop):
                task.cancel()
                self._record("async_task", task, True)

    def _terminate_processes(self, timeout: float) -> None:
        for process in multiprocessing.active_children():
            try:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout)
                self._record("process", process, not process.is_alive())
            except Exception as error:
                self._record("process", process, False, str(error))

    def _join_threads(self, timeout: float) -> None:
        current = threading.current_thread()
        for thread in threading.enumerate():
            if thread is current or not thread.is_alive() or thread.daemon:
                continue
            try:
                thread.join(timeout=timeout)
                self._record("thread", thread, not thread.is_alive())
            except RuntimeError as error:
                self._record("thread", thread, False, str(error))
