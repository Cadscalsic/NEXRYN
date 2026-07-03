"""Single runtime observability API backed by the unified metric store."""

from __future__ import annotations

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


runtime_observability_layer = RuntimeObservabilityLayer()


__all__ = [
    "RuntimeObservabilityLayer",
    "runtime_observability_layer",
]
