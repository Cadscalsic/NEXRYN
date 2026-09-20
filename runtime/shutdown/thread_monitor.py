"""Runtime thread, process, and asyncio task monitor."""

from __future__ import annotations

import asyncio
import multiprocessing
import threading


class ThreadMonitor:
    def active_threads(self) -> list[dict]:
        current = threading.current_thread()
        return [
            {
                "name": thread.name,
                "ident": thread.ident,
                "daemon": thread.daemon,
                "alive": thread.is_alive(),
            }
            for thread in threading.enumerate()
            if thread is not current and thread.is_alive()
        ]

    def active_processes(self) -> list[dict]:
        return [
            {
                "name": process.name,
                "pid": process.pid,
                "alive": process.is_alive(),
                "daemon": process.daemon,
            }
            for process in multiprocessing.active_children()
            if process.is_alive()
        ]

    def active_tasks(self) -> list[dict]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return []
        tasks = [
            task
            for task in asyncio.all_tasks(loop)
            if not task.done()
        ]
        return [
            {
                "name": task.get_name(),
                "done": task.done(),
                "cancelled": task.cancelled(),
            }
            for task in tasks
        ]

    def hanging_resources(self) -> dict:
        threads = self.active_threads()
        processes = self.active_processes()
        tasks = self.active_tasks()
        return {
            "active_threads": threads,
            "active_processes": processes,
            "active_tasks": tasks,
            "hanging_resources": {
                "threads": threads,
                "processes": processes,
                "async_tasks": tasks,
            },
        }
