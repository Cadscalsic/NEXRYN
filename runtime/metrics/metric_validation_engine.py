"""Validation and reconciliation diagnostics for canonical metrics."""

from __future__ import annotations

from typing import Any

from runtime.metrics.unified_metric_store import unified_metric_store


class MetricValidationEngine:
    """Detect duplicate producers, conflicts, stale/missing/orphan metrics."""

    system_name = "metric_validation_engine"

    def __init__(self, store=None):
        self.store = store or unified_metric_store

    def validate(self, required_metrics: list[str] | None = None) -> dict[str, Any]:
        required_metrics = required_metrics or list(self.store.registry.definitions)
        conflicts = []
        duplicate_producers = []
        stale_metrics = []
        missing_metrics = []
        orphan_metrics = []
        repaired = []
        for metric_name in required_metrics:
            samples = self.store.samples.get(metric_name, [])
            if not samples:
                missing_metrics.append(metric_name)
                continue
            producers = sorted({sample.get("producer") for sample in samples})
            if len(producers) > 1:
                duplicate_producers.append({
                    "metric_name": metric_name,
                    "producers": producers,
                })
            values = {
                self._normalized(sample.get("value"))
                for sample in samples
            }
            if len(values) > 1:
                canonical = self.store.get_record(metric_name)
                conflicts.append({
                    "metric_name": metric_name,
                    "values": sorted(values),
                    "canonical_value": canonical.get("value"),
                    "canonical_owner": canonical.get("metric_owner"),
                    "sample_count": len(samples),
                })
                repaired.append(metric_name)
            owner = self.store.registry.owner_for(metric_name)
            if owner == "unknown":
                orphan_metrics.append(metric_name)
            if any(not sample.get("timestamp") for sample in samples):
                stale_metrics.append(metric_name)
        validated = len(required_metrics) - len(missing_metrics)
        consistency_score = round(
            max(0.0, 1.0 - (len(conflicts) / max(validated, 1))),
            4,
        )
        return {
            "system": self.system_name,
            "METRIC_CONFLICT_REPORT": {
                "duplicate_producers": duplicate_producers,
                "conflicting_values": conflicts,
                "stale_metrics": stale_metrics,
                "missing_metrics": missing_metrics,
                "orphan_metrics": orphan_metrics,
                "invalid_updates": [],
            },
            "metrics_validated": validated,
            "metrics_conflicts": len(conflicts),
            "metrics_repaired": len(repaired),
            "repaired_metrics": repaired,
            "consistency_score": consistency_score,
            "observability_health": (
                "healthy"
                if consistency_score >= 0.90 and not missing_metrics
                else "degraded"
                if consistency_score >= 0.70
                else "critical"
            ),
            "METRIC_RECONCILIATION_WARNING": bool(conflicts or missing_metrics),
        }

    def _normalized(self, value):
        if isinstance(value, float):
            return round(value, 4)
        return value


metric_validation_engine = MetricValidationEngine()


__all__ = ["MetricValidationEngine", "metric_validation_engine"]
