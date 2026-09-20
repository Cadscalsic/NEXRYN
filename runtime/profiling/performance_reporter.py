"""Build the unified NEXRYN performance intelligence report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.profiling.governance_profiler import governance_profiler
from runtime.profiling.memory_profiler import memory_profiler
from runtime.profiling.reasoning_profiler import reasoning_profiler
from runtime.profiling.runtime_profiler import runtime_profiler
from runtime.profiling.shutdown_profiler import shutdown_profiler
from runtime.profiling.stage_profiler import stage_profiler
from runtime.profiling.telemetry_collector import telemetry
from runtime.profiling.metric_bridge import runtime_metric_bridge


class PerformanceReporter:
    def build_report(
        self,
        runtime_context: dict[str, Any] | None = None,
        performance_report: dict[str, Any] | None = None,
        profile_level: str = "minimal",
    ) -> dict[str, Any]:
        runtime_context = runtime_context or {}
        performance_report = performance_report or runtime_context.get("performance_report", {})
        runtime_context = {
            **runtime_context,
            "performance_report": performance_report,
        }
        module_timings = list(performance_report.get("module_timings", []))
        if not module_timings:
            module_timings = list(performance_report.get("slowest_modules", []))
        performance_report = runtime_metric_bridge.merge(
            performance_report,
            module_timings=module_timings,
        )
        runtime_context["performance_report"] = performance_report

        runtime_metrics = runtime_profiler.profile(
            performance_report,
            module_timings,
        )
        stage_metrics = stage_profiler.profile(
            module_timings,
            runtime_metrics.total_runtime_seconds,
        )
        governance_metrics = governance_profiler.profile(
            module_timings,
            runtime_context,
        )
        reasoning_metrics = reasoning_profiler.profile(
            runtime_context,
            module_timings,
        )
        memory_metrics = memory_profiler.profile(
            performance_report,
            runtime_context,
        )
        shutdown_metrics = shutdown_profiler.profile(
            runtime_context,
            module_timings,
        )

        top_expensive = [
            {
                "rank": index + 1,
                "module": item.stage_name,
                "total_duration": item.total_duration,
                "execution_count": item.execution_count,
            }
            for index, item in enumerate(stage_metrics[:10])
        ]

        strategy_queries = memory_metrics.strategy_hits + memory_metrics.strategy_misses
        program_queries = memory_metrics.program_hits + memory_metrics.program_misses
        strategy_reuse_rate = round(
            memory_metrics.strategy_hits / max(strategy_queries, 1),
            4,
        )
        program_reuse_rate = round(
            memory_metrics.program_hits / max(program_queries, 1),
            4,
        )
        counterfactual_queries = (
            memory_metrics.counterfactual_hits
            + memory_metrics.counterfactual_misses
        )
        counterfactual_reuse_rate = round(
            memory_metrics.counterfactual_hits
            / max(counterfactual_queries, 1),
            4,
        )
        counterfactual_success_rate = round(
            memory_metrics.counterfactual_success
            / max(memory_metrics.counterfactual_hits, 1),
            4,
        )
        cache_total = memory_metrics.cache_hits + memory_metrics.cache_misses
        cache_hit_rate = round(
            memory_metrics.cache_hits / max(cache_total, 1),
            4,
        )
        adaptive_reuse_report = self._mapping(
            runtime_context.get("ADAPTIVE_REUSE_REPORT")
            or runtime_context.get("adaptive_reuse_report")
            or runtime_context.get("COGNITIVE_REUSE_REPORT")
            or performance_report.get("adaptive_reuse_engine")
        )
        reuse_efficiency = round(
            (
                adaptive_reuse_report.get("cache_hits", 0)
                / max(
                    adaptive_reuse_report.get("cache_hits", 0)
                    + adaptive_reuse_report.get("cache_misses", 0),
                    1,
                )
            ),
            4,
        )

        report = {
            "system": "performance_intelligence_layer",
            "profile_level": profile_level,
            "runtime_summary": runtime_metrics.as_dict(),
            "top_expensive_modules": top_expensive,
            "TOP_EXPENSIVE_MODULES": top_expensive,
            "stage_metrics": [
                item.as_dict()
                for item in stage_metrics
            ],
            "governance_overhead": governance_metrics.as_dict(),
            "cognitive_efficiency": {
                **reasoning_metrics.as_dict(),
                "COGNITIVE_EFFICIENCY_SCORE":
                reasoning_metrics.cognitive_efficiency,
            },
            "memory_efficiency": {
                **memory_metrics.as_dict(),
                "cache_hit_rate": cache_hit_rate,
                "strategy_reuse_rate": strategy_reuse_rate,
                "program_reuse_rate": program_reuse_rate,
                "counterfactual_reuse_rate": counterfactual_reuse_rate,
                "counterfactual_success_rate":
                counterfactual_success_rate,
                "STRATEGY_REUSE_RATE": strategy_reuse_rate,
            },
            "adaptive_reuse_efficiency": {
                "reuse_efficiency": reuse_efficiency,
                "top_reused_assets":
                adaptive_reuse_report.get("top_reused_assets", []),
                "reuse_opportunities_missed":
                adaptive_reuse_report.get("reuse_opportunities_missed", []),
                "estimated_governance_saved":
                adaptive_reuse_report.get("estimated_governance_saved", 0.0),
                "estimated_dependency_saved":
                adaptive_reuse_report.get("estimated_dependency_saved", 0.0),
                "estimated_runtime_saved":
                adaptive_reuse_report.get("estimated_runtime_saved", 0.0),
            },
            "shutdown_efficiency": {
                **shutdown_metrics.as_dict(),
                "POST_COMPLETION_LATENCY":
                shutdown_metrics.post_completion_latency,
            },
            "telemetry": telemetry.report(),
            "optimization_targets": self._optimization_targets(
                top_expensive,
                reasoning_metrics.cognitive_efficiency,
                memory_metrics.reuse_rate,
                shutdown_metrics.post_completion_latency,
            ),
            "COGNITIVE_EFFICIENCY_SCORE":
            reasoning_metrics.cognitive_efficiency,
            "STRATEGY_REUSE_RATE":
            strategy_reuse_rate,
            "COUNTERFACTUAL_REUSE_RATE":
            counterfactual_reuse_rate,
            "POST_COMPLETION_LATENCY":
            shutdown_metrics.post_completion_latency,
        }

        if profile_level == "detailed":
            report["telemetry_events"] = telemetry.snapshot()

        return report

    def _mapping(self, value):
        return value if isinstance(value, dict) else {}

    def write_report(
        self,
        report: dict[str, Any],
        output_path: str | Path,
    ) -> dict[str, Any]:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(report, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        return {
            "profile_output": str(path),
            "profile_written": True,
        }

    def _optimization_targets(
        self,
        top_expensive,
        cognitive_efficiency,
        reuse_rate,
        post_completion_latency,
    ):
        targets = []
        if top_expensive:
            targets.append({
                "target": top_expensive[0]["module"],
                "reason": "highest_total_duration",
            })
        if cognitive_efficiency < 0.05:
            targets.append({
                "target": "reasoning",
                "reason": "low_cognitive_efficiency",
            })
        if reuse_rate < 0.25:
            targets.append({
                "target": "memory_reuse",
                "reason": "low_reuse_rate",
            })
        if post_completion_latency > 1.0:
            targets.append({
                "target": "shutdown",
                "reason": "post_completion_latency_high",
            })
        return targets


performance_reporter = PerformanceReporter()


__all__ = [
    "PerformanceReporter",
    "performance_reporter",
]
