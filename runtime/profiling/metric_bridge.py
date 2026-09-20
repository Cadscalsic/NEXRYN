"""Unified timing bridge for runtime and performance intelligence reports."""

from __future__ import annotations

from typing import Any


TIMING_FIELDS = (
    "active_compute_time_seconds",
    "idle_time_seconds",
    "startup_time_seconds",
    "shutdown_time_seconds",
    "task_execution_time_seconds",
    "governance_time_seconds",
    "dependency_reasoning_time_seconds",
    "reasoning_time_seconds",
    "truth_time_seconds",
    "cache_time_seconds",
    "reuse_time_seconds",
    "context_time_seconds",
    "memory_time_seconds",
    "localization_time_seconds",
    "evaluation_time_seconds",
    "report_time_seconds",
    "process_generation_time",
    "causal_generation_time",
    "finalization_time_seconds",
)


class RuntimeMetricBridge:
    def synchronize(
        self,
        performance_report: dict[str, Any] | None = None,
        module_timings: list[dict[str, Any]] | None = None,
        runtime_metrics: dict[str, Any] | None = None,
    ) -> dict[str, float]:
        performance_report = performance_report or {}
        runtime_metrics = runtime_metrics or {}
        module_timings = list(
            module_timings
            or performance_report.get("module_timings", [])
            or performance_report.get("slowest_modules", [])
            or []
        )

        active_compute = self._first_positive(
            performance_report.get("active_compute_time_seconds"),
            runtime_metrics.get("active_compute_time_seconds"),
            self._sum_modules(module_timings),
        )
        total_runtime = self._first_positive(
            performance_report.get("total_runtime_seconds"),
            performance_report.get("execution_time"),
            runtime_metrics.get("total_runtime_seconds"),
            active_compute,
        )
        total_runtime = max(total_runtime, active_compute)
        startup = self._first_positive(
            performance_report.get("startup_time_seconds"),
            runtime_metrics.get("startup_time_seconds"),
            runtime_metrics.get("boot_duration"),
            self._module_time(module_timings, "runtime_boot"),
        )
        shutdown = self._first_positive(
            performance_report.get("shutdown_time_seconds"),
            runtime_metrics.get("shutdown_time_seconds"),
            self._module_time_contains(module_timings, ("shutdown", "finalize")),
        )
        task_execution = self._first_positive(
            performance_report.get("task_execution_time_seconds"),
            runtime_metrics.get("task_execution_time_seconds"),
            self._module_time(module_timings, "stage_cycle"),
            self._module_time_contains(module_timings, ("task", "stage")),
        )
        active_compute = max(active_compute, task_execution)
        total_runtime = max(total_runtime, active_compute)
        governance = self._first_positive(
            performance_report.get("governance_time_seconds"),
            runtime_metrics.get("governance_time_seconds"),
            self._module_time_contains(module_timings, ("governance",)),
        )
        dependency = self._first_positive(
            performance_report.get("dependency_reasoning_time_seconds"),
            performance_report.get("dependency_time"),
            runtime_metrics.get("dependency_reasoning_time_seconds"),
            runtime_metrics.get("dependency_time"),
            self._module_time_contains(module_timings, ("dependency",)),
        )
        reasoning = self._first_positive(
            performance_report.get("reasoning_time_seconds"),
            performance_report.get("reasoning_time"),
            runtime_metrics.get("reasoning_time_seconds"),
            runtime_metrics.get("reasoning_time"),
            self._module_time_contains(
                module_timings,
                ("reason", "orchestrat"),
                exclude=("dependency_reasoning",),
            ),
        )
        truth = self._first_positive(
            performance_report.get("truth_time_seconds"),
            performance_report.get("truth_time"),
            runtime_metrics.get("truth_time_seconds"),
            runtime_metrics.get("truth_time"),
            self._module_time_contains(module_timings, ("truth",)),
        )
        cache_time = self._first_positive(
            performance_report.get("cache_time_seconds"),
            performance_report.get("cache_time"),
            runtime_metrics.get("cache_time_seconds"),
            runtime_metrics.get("cache_time"),
            self._module_time_contains(module_timings, ("cache",)),
        )
        reuse = self._first_positive(
            performance_report.get("reuse_time_seconds"),
            performance_report.get("reuse_time"),
            runtime_metrics.get("reuse_time_seconds"),
            runtime_metrics.get("reuse_time"),
            self._module_time_contains(module_timings, ("reuse",)),
        )
        context = self._first_positive(
            performance_report.get("context_time_seconds"),
            performance_report.get("context_time"),
            runtime_metrics.get("context_time_seconds"),
            runtime_metrics.get("context_time"),
            self._module_time_contains(module_timings, ("context", "semantic")),
        )
        memory = self._first_positive(
            performance_report.get("memory_time_seconds"),
            performance_report.get("memory_time"),
            runtime_metrics.get("memory_time_seconds"),
            runtime_metrics.get("memory_time"),
            self._module_time_contains(module_timings, ("memory",)),
        )
        localization = self._first_positive(
            performance_report.get("localization_time_seconds"),
            performance_report.get("localization_time"),
            runtime_metrics.get("localization_time_seconds"),
            runtime_metrics.get("localization_time"),
            self._module_time_contains(module_timings, ("localization", "localisation")),
        )
        evaluation = self._first_positive(
            performance_report.get("evaluation_time_seconds"),
            performance_report.get("evaluation_time"),
            runtime_metrics.get("evaluation_time_seconds"),
            runtime_metrics.get("evaluation_time"),
            self._module_time_contains(module_timings, ("evaluation", "eval")),
        )
        report_time = self._first_positive(
            performance_report.get("report_time_seconds"),
            performance_report.get("report_time"),
            runtime_metrics.get("report_time_seconds"),
            runtime_metrics.get("report_time"),
            self._module_time_contains(module_timings, ("report",)),
        )
        process_generation = self._first_positive(
            performance_report.get("process_generation_time"),
            runtime_metrics.get("process_generation_time"),
            self._module_time_contains(module_timings, ("process",)),
        )
        causal_generation = self._first_positive(
            performance_report.get("causal_generation_time"),
            runtime_metrics.get("causal_generation_time"),
            self._module_time_contains(module_timings, ("causal",)),
        )
        finalization = self._first_positive(
            performance_report.get("finalization_time_seconds"),
            runtime_metrics.get("finalization_time_seconds"),
            runtime_metrics.get("finalization_duration"),
            self._module_time_contains(module_timings, ("finalize", "final_context")),
        )
        idle = self._number(performance_report.get("idle_time_seconds"), None)
        if idle is None or active_compute + idle > total_runtime:
            idle = max(0.0, total_runtime - active_compute)

        return {
            "active_compute_time_seconds": round(active_compute, 4),
            "idle_time_seconds": round(idle, 4),
            "startup_time_seconds": round(startup, 4),
            "shutdown_time_seconds": round(shutdown, 4),
            "task_execution_time_seconds": round(task_execution, 4),
            "governance_time_seconds": round(governance, 4),
            "dependency_reasoning_time_seconds": round(dependency, 4),
            "reasoning_time_seconds": round(reasoning, 4),
            "truth_time_seconds": round(truth, 4),
            "cache_time_seconds": round(cache_time, 4),
            "reuse_time_seconds": round(reuse, 4),
            "context_time_seconds": round(context, 4),
            "memory_time_seconds": round(memory, 4),
            "localization_time_seconds": round(localization, 4),
            "evaluation_time_seconds": round(evaluation, 4),
            "report_time_seconds": round(report_time, 4),
            "process_generation_time": round(process_generation, 4),
            "causal_generation_time": round(causal_generation, 4),
            "finalization_time_seconds": round(finalization, 4),
        }

    def merge(
        self,
        performance_report: dict[str, Any],
        module_timings: list[dict[str, Any]] | None = None,
        runtime_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        timings = self.synchronize(
            performance_report,
            module_timings=module_timings,
            runtime_metrics=runtime_metrics,
        )
        merged = dict(performance_report or {})
        merged.update(timings)
        merged["metric_timing_bridge"] = {
            "source": "runtime_metric_bridge",
            "fields": list(TIMING_FIELDS),
            "synchronized": True,
        }
        return merged

    def _module_time(self, module_timings, module_name):
        return sum(
            self._number(item.get("seconds"), 0.0)
            for item in module_timings
            if item.get("module") == module_name
        )

    def _module_time_contains(self, module_timings, names, exclude=()):
        return sum(
            self._number(item.get("seconds"), 0.0)
            for item in module_timings
            if any(name in str(item.get("module", "")) for name in names)
            and not any(name in str(item.get("module", "")) for name in exclude)
        )

    def _sum_modules(self, module_timings):
        return sum(self._number(item.get("seconds"), 0.0) for item in module_timings)

    def _first_positive(self, *values):
        for value in values:
            number = self._number(value, 0.0)
            if number > 0.0:
                return number
        return 0.0

    def _number(self, value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default


runtime_metric_bridge = RuntimeMetricBridge()


__all__ = ["RuntimeMetricBridge", "runtime_metric_bridge", "TIMING_FIELDS"]
