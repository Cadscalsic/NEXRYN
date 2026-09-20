"""Single runtime observability API backed by the unified metric store."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.metrics.canonical_metric_registry import canonical_metric_registry
from runtime.metrics.metric_validation_engine import metric_validation_engine
from runtime.metrics.unified_metric_store import unified_metric_store


class RuntimeObservabilityLayer:
    """Public metric API for reports, dashboards, and diagnostics."""

    system_name = "runtime_observability_layer"

    def __init__(self, store=None, registry=None, validator=None):
        self.store = store or unified_metric_store
        self.registry = registry or canonical_metric_registry
        self.validator = validator or metric_validation_engine

    def get_metric(self, metric_name: str, default=None):
        return self.store.get_metric(metric_name, default)

    def get_metrics(self, metric_names: list[str] | None = None) -> dict[str, Any]:
        if metric_names is None:
            return self.store.snapshot()
        return {
            name: self.get_metric(name)
            for name in metric_names
        }

    def ingest_report(
        self,
        report: Mapping[str, Any] | None,
        producer: str,
        source: str,
        confidence: float = 0.85,
    ) -> dict[str, Any]:
        return self.store.ingest_report(report, producer, source, confidence)

    def build_reconciliation_report(
        self,
        sources: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        validation = self.validator.validate()
        registry_report = self.registry.build_report()
        source_audit = self.registry.metric_source_audit(sources)
        store_report = self.store.build_report()
        return {
            "system": self.system_name,
            "METRIC_RECONCILIATION_REPORT": {
                "metrics_registered": registry_report["metrics_registered"],
                "metrics_validated": validation["metrics_validated"],
                "metrics_conflicts": validation["metrics_conflicts"],
                "metrics_repaired": validation["metrics_repaired"],
                "metric_sources": registry_report["metric_sources"],
                "metric_owners": registry_report["metric_owners"],
                "consistency_score": validation["consistency_score"],
                "observability_health": validation["observability_health"],
            },
            "METRIC_SOURCE_AUDIT": source_audit,
            "METRIC_CONFLICT_REPORT": validation["METRIC_CONFLICT_REPORT"],
            "METRIC_RECONCILIATION_WARNING":
            validation["METRIC_RECONCILIATION_WARNING"],
            "canonical_metrics": store_report["canonical_metrics"],
            "metric_records": store_report["metric_records"],
            "observability_api": "observability.get_metric",
        }

    def build_runtime_observability_report(
        self,
        performance_report: Mapping[str, Any] | None = None,
        runtime_attribution_report: Mapping[str, Any] | None = None,
        sources: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        performance_report = (
            performance_report if isinstance(performance_report, Mapping) else {}
        )
        runtime_attribution_report = (
            runtime_attribution_report
            if isinstance(runtime_attribution_report, Mapping)
            else {}
        )
        sources = sources if isinstance(sources, Mapping) else {}
        for source_name, payload in sources.items():
            if isinstance(payload, Mapping):
                self.ingest_report(
                    payload,
                    producer=str(payload.get("system") or source_name),
                    source=str(source_name),
                    confidence=0.85,
                )
        if performance_report:
            self.ingest_report(
                performance_report,
                producer=str(performance_report.get("system") or "performance_report"),
                source="performance_report",
                confidence=0.90,
            )

        validation = self.validator.validate()
        store_report = self.store.build_report()
        canonical_metrics = store_report.get("canonical_metrics", {})
        metric_records = store_report.get("metric_records", {})
        runtime_breakdown = dict(
            runtime_attribution_report.get("runtime_breakdown")
            or performance_report.get("runtime_breakdown")
            or {}
        )
        total_runtime = _number(
            runtime_attribution_report.get(
                "total_runtime",
                performance_report.get("total_runtime_seconds"),
            )
        )
        module_timings = list(performance_report.get("module_timings", []) or [])
        subsystem_coverage = self._subsystem_coverage(
            runtime_breakdown,
            module_timings,
            canonical_metrics,
        )
        instrumented_modules = [
            item
            for item in self._module_instrumentation(module_timings, total_runtime)
            if item["duration_seconds"] > 0.0
        ]
        missing_instrumentation = [
            item
            for item in self._module_instrumentation(module_timings, total_runtime)
            if item["duration_seconds"] <= 0.0
        ]
        metrics_missing = list(
            validation.get("METRIC_CONFLICT_REPORT", {}).get("missing_metrics", [])
        )
        metric_conflicts = validation.get("METRIC_CONFLICT_REPORT", {})
        metrics_repaired = list(validation.get("repaired_metrics", []))
        placeholder_metrics = self._placeholder_metrics(canonical_metrics)
        collected = self._metric_collection_records(metric_records)
        coverage_percentage = round(
            100.0
            * sum(subsystem_coverage.values())
            / max(len(subsystem_coverage), 1),
            2,
        )
        consistency_score = float(validation.get("consistency_score", 0.0) or 0.0)
        completeness = 1.0 - (
            len(metrics_missing) / max(len(self.registry.definitions), 1)
        )
        zero_duration_penalty = len(missing_instrumentation) / max(
            len(module_timings),
            1,
        )
        observability_score = round(
            max(
                0.0,
                (
                    coverage_percentage / 100.0 * 0.40
                    + consistency_score * 0.35
                    + completeness * 0.20
                    + max(0.0, 1.0 - zero_duration_penalty) * 0.05
                ),
            ),
            4,
        )
        observability_state = (
            "COMPLETE"
            if observability_score >= 0.90
            else "PARTIAL"
            if observability_score > 0.0
            else "EMERGING"
        )
        cognitive_coverage_state = (
            "OPERATIONAL"
            if coverage_percentage >= 75.0
            else "EMERGING"
            if coverage_percentage > 0.0
            else "PARTIAL"
        )
        overall_status = (
            "SUCCESS"
            if observability_state == "COMPLETE"
            else "SUCCESS_WITH_LIMITED_OBSERVABILITY"
        )
        now = str(datetime.utcnow())
        timing_sources = self._timing_sources(
            runtime_breakdown,
            metric_records,
            module_timings,
        )
        report = {
            "system": self.system_name,
            "RUNTIME_OBSERVABILITY_REPORT": True,
            "instrumented_modules": instrumented_modules,
            "missing_instrumentation": missing_instrumentation,
            "metrics_collected": collected,
            "metrics_missing": metrics_missing,
            "metrics_repaired": metrics_repaired,
            "metrics_reconciled": sorted(canonical_metrics.keys()),
            "timing_sources": timing_sources,
            "runtime_breakdown": runtime_breakdown,
            "metric_conflicts": metric_conflicts,
            "metric_resolution": {
                name: {
                    "owner": record.get("metric_owner"),
                    "source": record.get("metric_source"),
                    "collection_time": record.get("timestamp"),
                    "confidence": record.get("confidence", 0.0),
                    "validation_status": (
                        "reconciled"
                        if name not in metrics_missing
                        else "missing"
                    ),
                }
                for name, record in sorted(metric_records.items())
            },
            "coverage_percentage": coverage_percentage,
            "observability_score": observability_score,
            "subsystem_coverage": subsystem_coverage,
            "unattributed_runtime": _number(
                runtime_attribution_report.get("unattributed_runtime")
            ),
            "hidden_runtime": _number(
                runtime_attribution_report.get("hidden_runtime")
            ),
            "background_runtime": _number(
                runtime_attribution_report.get("background_runtime")
            ),
            "placeholder_metrics": placeholder_metrics,
            "unused_metrics": [],
            "stale_metrics": metric_conflicts.get("stale_metrics", []),
            "duplicate_metrics": metric_conflicts.get("duplicate_producers", []),
            "overhead_estimate": self._overhead_estimate(
                instrumented_modules,
                total_runtime,
            ),
            "start_timestamp": now,
            "end_timestamp": now,
            "duration_seconds": 0.0,
            "success": not missing_instrumentation and not metrics_missing,
            "failure": (
                None
                if not missing_instrumentation and not metrics_missing
                else "OBSERVABILITY_GAPS_DETECTED"
            ),
            "status_semantics": {
                "execution": "SUCCESS",
                "observability": observability_state,
                "cognitive_coverage": cognitive_coverage_state,
                "overall": overall_status,
            },
            "overall_status": overall_status,
        }
        return report

    def _module_instrumentation(self, module_timings, total_runtime):
        modules = []
        for index, item in enumerate(module_timings):
            if not isinstance(item, Mapping):
                continue
            name = str(item.get("module") or item.get("stage") or item.get("name") or f"module_{index}")
            duration = _number(item.get("seconds", item.get("total_duration")))
            modules.append({
                "module": name,
                "execution_start": item.get("execution_start") or item.get("start_timestamp"),
                "execution_end": item.get("execution_end") or item.get("end_timestamp"),
                "elapsed_time": round(duration, 6),
                "duration_seconds": round(duration, 6),
                "percentage_of_total_runtime": round(
                    duration / max(total_runtime, 0.0001),
                    4,
                ),
                "average_duration": round(duration, 6),
                "invocation_count": int(item.get("invocation_count", 1) or 1),
                "cpu_cost": round(duration, 6),
                "memory_cost": int(item.get("memory_cost", 0) or 0),
                "input_count": int(item.get("input_count", 0) or 0),
                "output_count": int(item.get("output_count", 0) or 0),
                "success": duration > 0.0,
                "failure": None if duration > 0.0 else "ZERO_DURATION_REPORTED",
            })
        return modules

    def _subsystem_coverage(self, runtime_breakdown, module_timings, metrics):
        subsystems = {
            "Execution": ("task_execution_time", "task_execution_time_seconds", ("execution", "task", "stage")),
            "Reasoning": ("reasoning_time", "reasoning_time_seconds", ("reason", "orchestrat")),
            "Dependency": ("dependency_time", "dependency_reasoning_time_seconds", ("dependency",)),
            "Process": ("process_time", "process_generation_time", ("process",)),
            "Causal": ("causal_time", "causal_generation_time", ("causal",)),
            "Truth": ("truth_time", "truth_time_seconds", ("truth",)),
            "Memory": ("memory_time", "memory_time_seconds", ("memory",)),
            "Reuse": ("reuse_time", "reuse_time_seconds", ("reuse",)),
            "Evaluation": ("evaluation_time", "evaluation_time_seconds", ("evaluation", "eval")),
            "Reporting": ("report_time", "report_time_seconds", ("report", "final")),
            "Training": ("training_time", "training_time_seconds", ("training",)),
            "Governance": ("governance_time", "governance_time_seconds", ("governance",)),
        }
        coverage = {}
        for subsystem, (breakdown_key, metric_key, module_tokens) in subsystems.items():
            has_breakdown = _number(runtime_breakdown.get(breakdown_key)) > 0.0
            has_metric = _number(metrics.get(metric_key)) > 0.0
            has_module = any(
                _number(item.get("seconds", item.get("total_duration"))) > 0.0
                and any(
                    token in str(item.get("module") or item.get("stage") or item.get("name") or "").lower()
                    for token in module_tokens
                )
                for item in module_timings
                if isinstance(item, Mapping)
            )
            coverage[subsystem] = round(
                min(
                    1.0,
                    (0.45 if has_breakdown else 0.0)
                    + (0.35 if has_metric else 0.0)
                    + (0.20 if has_module else 0.0),
                ),
                4,
            )
        return coverage

    def _metric_collection_records(self, metric_records):
        records = []
        for name, record in sorted(metric_records.items()):
            records.append({
                "metric_name": name,
                "value": record.get("value"),
                "owner": record.get("metric_owner"),
                "source": record.get("metric_source"),
                "collection_time": record.get("timestamp"),
                "confidence": record.get("confidence", 0.0),
                "validation_status": "collected" if record.get("metric_owner") else "missing_owner",
            })
        return records

    def _placeholder_metrics(self, metrics):
        placeholders = []
        for name, value in sorted(metrics.items()):
            if value is None:
                placeholders.append({"metric_name": name, "reason": "none_value"})
            elif name.endswith(("time", "time_seconds")) and _number(value) == 0.0:
                placeholders.append({"metric_name": name, "reason": "zero_timing"})
        return placeholders

    def _timing_sources(self, runtime_breakdown, metric_records, module_timings):
        sources = {}
        for key, value in sorted(runtime_breakdown.items()):
            if key in {"reconstructed_runtime", "untracked_runtime"}:
                continue
            sources[key] = {
                "duration_seconds": round(_number(value), 6),
                "source": "runtime_attribution_report",
                "owner": self.registry.owner_for(f"{key}_seconds"),
            }
        for name, record in metric_records.items():
            if "time" in name and _number(record.get("value")) > 0.0:
                sources[name] = {
                    "duration_seconds": round(_number(record.get("value")), 6),
                    "source": record.get("metric_source"),
                    "owner": record.get("metric_owner"),
                }
        if module_timings:
            sources["module_timings"] = {
                "duration_seconds": round(
                    sum(
                        _number(item.get("seconds", item.get("total_duration")))
                        for item in module_timings
                        if isinstance(item, Mapping)
                    ),
                    6,
                ),
                "source": "module_timings",
                "owner": "runtime_profiler",
            }
        return sources

    def _overhead_estimate(self, instrumented_modules, total_runtime):
        instrumentation_cost = len(instrumented_modules) * 0.000001
        return {
            "estimated_seconds": round(instrumentation_cost, 6),
            "percentage_of_runtime": round(
                instrumentation_cost / max(total_runtime, 0.0001),
                6,
            ),
            "within_target": (
                instrumentation_cost / max(total_runtime, 0.0001)
            ) < 0.01,
        }


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


runtime_observability_layer = RuntimeObservabilityLayer()


__all__ = [
    "RuntimeObservabilityLayer",
    "runtime_observability_layer",
]
