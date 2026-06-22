"""Shutdown latency profiler."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ShutdownMetrics:
    episode_completed_timestamp: float | None
    shutdown_started_timestamp: float | None
    runtime_terminated_timestamp: float | None
    post_completion_latency: float
    background_tasks_remaining: int
    cleanup_duration: float
    memory_flush_duration: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ShutdownProfiler:
    def profile(
        self,
        runtime_context: dict[str, Any] | None,
        module_timings: list[dict[str, Any]] | None,
    ) -> ShutdownMetrics:
        runtime_context = runtime_context or {}
        module_timings = module_timings or []
        shutdown_report = self._mapping(runtime_context.get("post_success_shutdown"))
        finalization = self._mapping(
            runtime_context.get("runtime_finalization_report")
            or runtime_context.get("finalization_report")
        )
        episode_completed = self._number(
            shutdown_report.get("episode_completed_timestamp")
            or runtime_context.get("episode_completed_timestamp")
        )
        shutdown_started = self._number(
            finalization.get("shutdown_started_timestamp")
            or runtime_context.get("shutdown_started_timestamp")
        )
        terminated = self._number(
            finalization.get("runtime_terminated_timestamp")
            or runtime_context.get("runtime_terminated_timestamp")
        )
        cleanup = sum(
            self._number(item.get("seconds"))
            for item in module_timings
            if "finalize" in str(item.get("module", ""))
            or "shutdown" in str(item.get("module", ""))
        )
        memory_flush = sum(
            self._number(item.get("seconds"))
            for item in module_timings
            if "cache" in str(item.get("module", ""))
            or "memory" in str(item.get("module", ""))
        )
        latency = (
            max(0.0, terminated - episode_completed)
            if episode_completed and terminated
            else cleanup
        )
        return ShutdownMetrics(
            episode_completed_timestamp=episode_completed or None,
            shutdown_started_timestamp=shutdown_started or None,
            runtime_terminated_timestamp=terminated or None,
            post_completion_latency=round(latency, 4),
            background_tasks_remaining=int(self._number(finalization.get("background_tasks_remaining"))),
            cleanup_duration=round(cleanup, 4),
            memory_flush_duration=round(memory_flush, 4),
        )

    def _mapping(self, value):
        return value if isinstance(value, dict) else {}

    def _number(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


shutdown_profiler = ShutdownProfiler()


__all__ = [
    "ShutdownMetrics",
    "ShutdownProfiler",
    "shutdown_profiler",
]
