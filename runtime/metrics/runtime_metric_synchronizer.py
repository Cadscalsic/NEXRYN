"""Bind lifecycle execution timings into canonical runtime metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.metrics.canonical_metric_registry import canonical_metric_registry


TIMING_BINDINGS = {
    "dependency": "dependency_reasoning_time_seconds",
    "dependency_execution": "dependency_reasoning_time_seconds",
    "dependency_activation": "dependency_reasoning_time_seconds",
    "process": "process_generation_time",
    "causal": "causal_generation_time",
    "truth": "truth_time_seconds",
    "reuse": "reuse_time_seconds",
    "adaptive_reuse": "reuse_time_seconds",
    "memory": "memory_time_seconds",
    "evaluation": "evaluation_time_seconds",
    "reasoning": "reasoning_time_seconds",
    "orchestrator": "reasoning_time_seconds",
    "execution": "task_execution_time_seconds",
    "governance": "governance_time_seconds",
    "reporting": "report_time_seconds",
    "report": "report_time_seconds",
}


class RuntimeMetricSynchronizer:
    """Synchronize reports with lifecycle timings as the authority."""

    system_name = "runtime_metric_synchronizer"

    def __init__(self, registry=None):
        self.registry = registry or canonical_metric_registry

    def synchronize(
        self,
        performance_report: Mapping[str, Any] | None = None,
        lifecycle_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        performance = dict(performance_report or {})
        lifecycle = lifecycle_report if isinstance(lifecycle_report, Mapping) else {}
        before_metrics = self._timing_snapshot(performance)
        before_coverage = self._coverage(before_metrics)
        bound_records = []
        rejected = []
        owner_resolution = {}

        for execution in lifecycle.get("executions", []) or []:
            if not isinstance(execution, Mapping):
                continue
            metric_name = self._metric_for_execution(execution)
            duration = self._duration(execution)
            if not metric_name or duration <= 0.0:
                rejected.append({
                    "execution_id": execution.get("execution_id"),
                    "module_name": execution.get("module_name"),
                    "runtime_name": execution.get("runtime_name"),
                    "reason": "no_binding_or_duration",
                })
                continue
            owner = self.registry.owner_for(metric_name)
            if owner == "unknown":
                owner = self._owner_from_execution(execution)
            owner_resolution[metric_name] = owner
            bound_records.append({
                "metric_name": metric_name,
                "metric_value": round(duration, 6),
                "owner": owner,
                "runtime": execution.get("runtime_name") or execution.get("module_name"),
                "execution_id": execution.get("execution_id"),
                "module_name": execution.get("module_name"),
                "collection_timestamp": execution.get("execution_end") or str(datetime.utcnow()),
                "measurement_source": "runtime_lifecycle",
                "confidence": 1.0,
                "validation_status": "validated",
            })

        aggregated = {}
        for record in bound_records:
            metric_name = record["metric_name"]
            aggregated[metric_name] = round(
                aggregated.get(metric_name, 0.0) + record["metric_value"],
                6,
            )

        repaired = []
        inferred = []
        for metric_name, value in aggregated.items():
            current = _number(performance.get(metric_name))
            if current <= 0.0 or value > current:
                if current <= 0.0:
                    repaired.append({
                        "metric_name": metric_name,
                        "old_value": current,
                        "new_value": value,
                        "repair_reason": "lifecycle_timing_available",
                    })
                else:
                    inferred.append({
                        "metric_name": metric_name,
                        "old_value": current,
                        "new_value": value,
                        "repair_reason": "lifecycle_timing_exceeds_reported_value",
                    })
                performance[metric_name] = value
                alias = self._legacy_alias(metric_name)
                if alias:
                    performance[alias] = value

        canonical = dict(performance.get("canonical_metrics", {}) or {})
        metric_records = dict(performance.get("metric_records", {}) or {})
        for record in bound_records:
            metric_name = record["metric_name"]
            if metric_name in aggregated:
                record = {**record, "metric_value": aggregated[metric_name]}
            canonical[metric_name] = max(
                _number(canonical.get(metric_name)),
                _number(record.get("metric_value")),
            )
            metric_records[metric_name] = {
                "metric_name": metric_name,
                "value": canonical[metric_name],
                "metric_owner": record["owner"],
                "metric_source": "runtime_lifecycle",
                "producer": record["owner"],
                "confidence": 1.0,
                "timestamp": record["collection_timestamp"],
                "sample_count": 1,
                "aggregation": self.registry.aggregation_for(metric_name),
                "owner_sample_available": True,
                "execution_id": record["execution_id"],
                "runtime": record["runtime"],
                "module_name": record["module_name"],
                "validation_status": "validated",
            }
        performance["canonical_metrics"] = canonical
        performance["metric_records"] = metric_records

        after_metrics = self._timing_snapshot(performance)
        after_coverage = self._coverage(after_metrics)
        placeholders = [
            name for name, value in after_metrics.items()
            if _number(value) <= 0.0
        ]
        report = {
            "system": self.system_name,
            "RUNTIME_METRIC_SYNCHRONIZATION_REPORT": True,
            "metrics_received": len(lifecycle.get("executions", []) or []),
            "metrics_bound": bound_records,
            "metrics_repaired": repaired,
            "metrics_inferred": inferred,
            "metrics_rejected": rejected,
            "owner_resolution": owner_resolution,
            "binding_failures": rejected,
            "binding_success_rate": round(
                len(bound_records)
                / max(len(bound_records) + len(rejected), 1),
                4,
            ),
            "coverage_before": before_coverage,
            "coverage_after": after_coverage,
            "observability_before": before_coverage,
            "observability_after": after_coverage,
            "remaining_placeholder_metrics": placeholders,
            "missing_runtime_metrics": [
                name for name in self._required_runtime_metrics()
                if name not in after_metrics or _number(after_metrics.get(name)) <= 0.0
            ],
            "synchronized_metrics": after_metrics,
            "timestamp": str(datetime.utcnow()),
        }
        performance["runtime_metric_synchronization_report"] = report
        performance["RUNTIME_METRIC_SYNCHRONIZATION_REPORT"] = report
        return {
            "performance_report": performance,
            "RUNTIME_METRIC_SYNCHRONIZATION_REPORT": report,
        }

    def _metric_for_execution(self, execution):
        text = " ".join([
            str(execution.get("runtime_name", "")),
            str(execution.get("module_name", "")),
            str(execution.get("trigger", "")),
        ]).lower()
        for token, metric_name in TIMING_BINDINGS.items():
            if token in text:
                return metric_name
        return ""

    def _owner_from_execution(self, execution):
        runtime_name = str(execution.get("runtime_name") or "").lower()
        module_name = str(execution.get("module_name") or "runtime")
        if "runtime" in runtime_name:
            return runtime_name.replace(" ", "_").lower()
        return module_name

    def _duration(self, execution):
        for key in (
            "elapsed_seconds",
            "duration_seconds",
            "wall_clock_time",
            "elapsed_time",
        ):
            value = _number(execution.get(key))
            if value > 0.0:
                return value
        return 0.0

    def _legacy_alias(self, metric_name):
        return {
            "dependency_reasoning_time_seconds": "dependency_reasoning_time",
            "truth_time_seconds": "truth_time",
            "reuse_time_seconds": "reuse_time",
            "memory_time_seconds": "memory_time",
            "evaluation_time_seconds": "evaluation_time",
            "reasoning_time_seconds": "reasoning_time",
        }.get(metric_name)

    def _timing_snapshot(self, report):
        metrics = {}
        for metric_name in self._required_runtime_metrics():
            if metric_name in report:
                metrics[metric_name] = report.get(metric_name)
        return metrics

    def _coverage(self, metrics):
        required = self._required_runtime_metrics()
        present = [
            metric_name for metric_name in required
            if _number(metrics.get(metric_name)) > 0.0
        ]
        return round(len(present) / max(len(required), 1), 4)

    def _required_runtime_metrics(self):
        return [
            "dependency_reasoning_time_seconds",
            "process_generation_time",
            "causal_generation_time",
            "truth_time_seconds",
            "reuse_time_seconds",
            "memory_time_seconds",
            "reasoning_time_seconds",
            "evaluation_time_seconds",
        ]


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


runtime_metric_synchronizer = RuntimeMetricSynchronizer()


__all__ = [
    "RuntimeMetricSynchronizer",
    "runtime_metric_synchronizer",
]
