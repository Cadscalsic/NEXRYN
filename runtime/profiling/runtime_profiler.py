"""Runtime-level cost metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class RuntimeMetrics:
    total_runtime_seconds: float
    startup_time_seconds: float
    shutdown_time_seconds: float
    active_compute_time_seconds: float
    idle_time_seconds: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


class RuntimeProfiler:
    def profile(
        self,
        performance_report: dict[str, Any] | None,
        module_timings: list[dict[str, Any]] | None = None,
    ) -> RuntimeMetrics:
        performance_report = performance_report or {}
        module_timings = module_timings or performance_report.get("module_timings", [])
        total_runtime = self._float(performance_report.get("total_runtime_seconds"))
        startup = self._module_time(module_timings, "runtime_boot")
        shutdown = sum(
            self._float(item.get("seconds"))
            for item in module_timings
            if "finalize" in str(item.get("module", ""))
            or "shutdown" in str(item.get("module", ""))
        )
        active_compute = sum(self._float(item.get("seconds")) for item in module_timings)
        idle = max(0.0, total_runtime - active_compute)
        return RuntimeMetrics(
            total_runtime_seconds=round(total_runtime, 4),
            startup_time_seconds=round(startup, 4),
            shutdown_time_seconds=round(shutdown, 4),
            active_compute_time_seconds=round(active_compute, 4),
            idle_time_seconds=round(idle, 4),
        )

    def _module_time(self, module_timings, module_name):
        return sum(
            self._float(item.get("seconds"))
            for item in module_timings
            if item.get("module") == module_name
        )

    def _float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


runtime_profiler = RuntimeProfiler()


__all__ = [
    "RuntimeMetrics",
    "RuntimeProfiler",
    "runtime_profiler",
]
