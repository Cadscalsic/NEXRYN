"""Unified metric store: one runtime source of metric truth."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.metrics.canonical_metric_registry import (
    canonical_metric_registry,
)


class UnifiedMetricStore:
    """Collect samples, reconcile them, and expose canonical metrics."""

    system_name = "unified_metric_store"

    def __init__(self, registry=None):
        self.registry = registry or canonical_metric_registry
        self.samples: dict[str, list[dict[str, Any]]] = {}
        self.canonical: dict[str, dict[str, Any]] = {}

    def clear(self) -> None:
        self.samples = {}
        self.canonical = {}

    def update_metric(
        self,
        metric_name: str,
        value: Any,
        producer: str,
        source: str,
        confidence: float = 1.0,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        metric_name = str(metric_name)
        sample = {
            "metric_name": metric_name,
            "value": value,
            "producer": str(producer),
            "source": str(source),
            "confidence": float(confidence if confidence is not None else 1.0),
            "timestamp": timestamp or str(datetime.utcnow()),
            "owner": self.registry.owner_for(metric_name),
        }
        self.samples.setdefault(metric_name, [])
        self.samples[metric_name].append(sample)
        self.registry.record_update(
            metric_name,
            value,
            producer,
            source,
            confidence,
        )
        self.canonical[metric_name] = self._reconcile_metric(metric_name)
        return dict(self.canonical[metric_name])

    def ingest_report(
        self,
        report: Mapping[str, Any] | None,
        producer: str,
        source: str,
        confidence: float = 0.85,
    ) -> dict[str, Any]:
        report = report if isinstance(report, Mapping) else {}
        updates = {}
        for metric_name in self.registry.definitions:
            if metric_name in report:
                updates[metric_name] = self.update_metric(
                    metric_name,
                    report.get(metric_name),
                    producer=producer,
                    source=source,
                    confidence=confidence,
                )
        return updates

    def get_metric(self, metric_name: str, default=None):
        record = self.canonical.get(str(metric_name))
        if not record:
            return default
        return record.get("value", default)

    def get_record(self, metric_name: str) -> dict[str, Any]:
        return dict(self.canonical.get(str(metric_name), {}))

    def snapshot(self) -> dict[str, Any]:
        return {
            name: record.get("value")
            for name, record in sorted(self.canonical.items())
        }

    def provenance(self, metric_name: str) -> list[dict[str, Any]]:
        return [dict(item) for item in self.samples.get(str(metric_name), [])]

    def build_report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "metrics_registered": len(self.registry.definitions),
            "metrics_available": len(self.canonical),
            "canonical_metrics": self.snapshot(),
            "metric_records": {
                name: dict(record)
                for name, record in sorted(self.canonical.items())
            },
            "sample_count": sum(len(items) for items in self.samples.values()),
        }

    def _reconcile_metric(self, metric_name: str) -> dict[str, Any]:
        samples = self.samples.get(metric_name, [])
        if not samples:
            return {}
        aggregation = self.registry.aggregation_for(metric_name)
        owner = self.registry.owner_for(metric_name)
        owner_samples = [
            sample for sample in samples if sample.get("producer") == owner
        ]
        candidates = owner_samples or samples
        if aggregation == "sum":
            value = sum(self._number(sample.get("value")) for sample in candidates)
            source_sample = candidates[-1]
        elif aggregation == "max":
            source_sample = max(
                candidates,
                key=lambda sample: (
                    self._number(sample.get("value")),
                    sample.get("confidence", 0.0),
                ),
            )
            value = source_sample.get("value")
        elif aggregation == "min":
            source_sample = min(
                candidates,
                key=lambda sample: self._number(sample.get("value")),
            )
            value = source_sample.get("value")
        else:
            source_sample = max(
                candidates,
                key=lambda sample: sample.get("timestamp", ""),
            )
            value = source_sample.get("value")
        return {
            "metric_name": metric_name,
            "value": value,
            "metric_owner": owner,
            "metric_source": source_sample.get("source"),
            "producer": source_sample.get("producer"),
            "confidence": source_sample.get("confidence", 1.0),
            "timestamp": source_sample.get("timestamp"),
            "sample_count": len(samples),
            "aggregation": aggregation,
            "owner_sample_available": bool(owner_samples),
        }

    def _number(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


unified_metric_store = UnifiedMetricStore()


__all__ = [
    "UnifiedMetricStore",
    "unified_metric_store",
]
