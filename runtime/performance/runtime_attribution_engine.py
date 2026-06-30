"""Runtime attribution and visibility for NEXRYN execution."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping


ATTRIBUTION_FIELDS = {
    "boot_time": ("boot_duration", "startup_time_seconds"),
    "task_selection_time": ("task_selection_duration",),
    "task_execution_time": ("task_execution_time_seconds",),
    "idle_time": ("idle_time_seconds",),
    "pre_reasoning_time": ("pre_reasoning_time_seconds",),
    "dependency_time": ("dependency_reasoning_time_seconds",),
    "promotion_time": ("promotion_time_seconds",),
    "context_time": ("context_time_seconds",),
    "truth_time": ("truth_time_seconds",),
    "cache_time": ("cache_time_seconds",),
    "reuse_time": ("reuse_time_seconds",),
    "governance_time": ("governance_time_seconds",),
    "localization_time": ("localization_time_seconds",),
    "memory_time": ("memory_time_seconds",),
    "reasoning_time": ("reasoning_time_seconds",),
    "report_time": ("report_time_seconds", "finalization_time_seconds"),
    "shutdown_time": ("shutdown_time_seconds",),
}


class RuntimeAttributionEngine:
    system_name = "runtime_attribution_engine"

    def build_report(
        self,
        total_runtime: float,
        performance_report: Mapping[str, Any] | None = None,
        runtime_metrics: Mapping[str, Any] | None = None,
        module_timings: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        performance_report = performance_report if isinstance(performance_report, Mapping) else {}
        runtime_metrics = runtime_metrics if isinstance(runtime_metrics, Mapping) else {}
        module_timings = (
            module_timings
            or performance_report.get("module_timings", [])
            or performance_report.get("slowest_modules", [])
            or []
        )
        total_runtime = round(max(_number(total_runtime), 0.0), 4)

        breakdown = {}
        for category, keys in ATTRIBUTION_FIELDS.items():
            value = self._first_available(keys, performance_report, runtime_metrics)
            breakdown[category] = round(value, 4)

        module_categories = self._module_categories(module_timings)
        for category, value in module_categories.items():
            breakdown[category] = round(max(breakdown.get(category, 0.0), value), 4)

        attributed = round(sum(breakdown.values()), 4)
        unattributed = round(max(0.0, total_runtime - attributed), 4)
        if unattributed:
            fallback_category = self._fallback_category(performance_report, runtime_metrics)
            if fallback_category:
                breakdown[fallback_category] = round(
                    breakdown.get(fallback_category, 0.0) + unattributed,
                    4,
                )
            else:
                breakdown["untracked_runtime"] = unattributed
            breakdown["reconstructed_runtime"] = unattributed
        attributed = round(
            sum(
                value
                for key, value in breakdown.items()
                if key not in {"reconstructed_runtime", "untracked_runtime"}
            ),
            4,
        )
        attributed = round(min(attributed, total_runtime), 4)
        unattributed = round(max(0.0, total_runtime - attributed), 4)

        top_modules = sorted(
            [
                {
                    "module": item.get("module") or item.get("stage") or item.get("name"),
                    "seconds": _number(item.get("seconds", item.get("total_duration"))),
                }
                for item in module_timings
                if isinstance(item, Mapping)
            ],
            key=lambda item: item["seconds"],
            reverse=True,
        )[:10]

        top_stages = sorted(
            [
                {"stage": key, "seconds": value}
                for key, value in breakdown.items()
            ],
            key=lambda item: item["seconds"],
            reverse=True,
        )[:10]

        return {
            "system": self.system_name,
            "RUNTIME ATTRIBUTION REPORT": True,
            "total_runtime": total_runtime,
            "attributed_runtime": attributed,
            "unattributed_runtime": unattributed,
            "untracked_runtime": unattributed,
            "hidden_runtime": unattributed,
            "background_runtime": 0.0,
            "loop_runtime": module_categories.get("loop_runtime", 0.0),
            "top_expensive_modules": top_modules,
            "top_expensive_stages": top_stages,
            "runtime_breakdown": breakdown,
            "every_second_attributed": unattributed <= 0.001,
            "runtime_attribution_reconstructed": True,
        }

    def _first_available(
        self,
        keys: tuple[str, ...],
        performance_report: Mapping[str, Any],
        runtime_metrics: Mapping[str, Any],
    ) -> float:
        for key in keys:
            for source in (performance_report, runtime_metrics):
                if source.get(key) is not None:
                    return _number(source.get(key))
        return 0.0

    def _module_categories(
        self,
        module_timings: list[Mapping[str, Any]],
    ) -> dict[str, float]:
        categories = defaultdict(float)
        for item in module_timings:
            name = str(item.get("module") or item.get("stage") or item.get("name") or "").lower()
            seconds = _number(item.get("seconds", item.get("total_duration")))
            if "dependency" in name:
                categories["dependency_time"] += seconds
            elif "promotion" in name:
                categories["promotion_time"] += seconds
            elif "context" in name:
                categories["context_time"] += seconds
            elif "truth" in name:
                categories["truth_time"] += seconds
            elif "stage_cycle" in name:
                categories["task_execution_time"] += seconds
            elif "task" in name or "stage" in name:
                categories["task_execution_time"] += seconds
            elif "cache" in name:
                categories["cache_time"] += seconds
            elif "reuse" in name:
                categories["reuse_time"] += seconds
            elif "governance" in name:
                categories["governance_time"] += seconds
            elif "localization" in name:
                categories["localization_time"] += seconds
            elif "memory" in name:
                categories["memory_time"] += seconds
            elif "reason" in name:
                categories["reasoning_time"] += seconds
            elif "loop" in name:
                categories["loop_runtime"] += seconds
            elif "report" in name:
                categories["report_time"] += seconds
        return dict(categories)

    def _fallback_category(
        self,
        performance_report: Mapping[str, Any],
        runtime_metrics: Mapping[str, Any],
    ) -> str | None:
        merged = {**dict(runtime_metrics), **dict(performance_report)}
        explicit_dependency_time = (
            _number(merged.get("dependency_reasoning_time_seconds"))
            or _number(merged.get("dependency_chain_execution_time"))
        )
        if explicit_dependency_time > 0:
            return "dependency_time"
        if _number(merged.get("reasoning_time_seconds")) > 0:
            return "reasoning_time"
        return None


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


runtime_attribution_engine = RuntimeAttributionEngine()


__all__ = [
    "RuntimeAttributionEngine",
    "runtime_attribution_engine",
]
