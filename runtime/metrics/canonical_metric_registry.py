"""Canonical metric ownership and provenance registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping


@dataclass
class MetricDefinition:
    metric_name: str
    metric_owner: str
    metric_source: str
    aggregation: str = "max"
    confidence: float = 1.0
    description: str = ""

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = str(datetime.utcnow())
        return data


class CanonicalMetricRegistry:
    """Register metric ownership, provenance, and update metadata."""

    system_name = "canonical_metric_registry"

    DEFAULT_METRICS = {
        "reasoning_depth": ("reasoning_engine", "introspection_report", "max"),
        "active_routes": ("reasoning_engine", "introspection_report", "max"),
        "execution_nodes": ("reasoning_engine", "introspection_report", "max"),
        "strategy_hits": ("strategy_memory", "strategy_reuse_report", "max"),
        "truth_hits": ("truth_memory", "truth_reuse_report", "max"),
        "context_hits": ("context_memory", "context_reuse_report", "max"),
        "dependency_chain_depth": ("dependency_runtime", "dependency_report", "max"),
        "dependency_depth": ("dependency_runtime", "dependency_report", "max"),
        "dependency_chains_executed": ("dependency_runtime", "dependency_report", "max"),
        "process_context_count": ("process_runtime", "process_context_report", "max"),
        "causal_context_count": ("causal_runtime", "causal_context_report", "max"),
        "reuse_rate": ("reuse_runtime", "adaptive_reuse_report", "max"),
        "cache_hits": ("cache_runtime", "cache_report", "max"),
        "cache_misses": ("cache_runtime", "cache_report", "max"),
        "prediction_accuracy": ("evaluation_runtime", "evaluation_report", "max"),
        "repair_success_rate": ("repair_runtime", "repair_report", "max"),
    }

    def __init__(self):
        self.definitions: dict[str, MetricDefinition] = {}
        self.update_history: list[dict[str, Any]] = []
        for metric, (owner, source, aggregation) in self.DEFAULT_METRICS.items():
            self.register_metric(metric, owner, source, aggregation=aggregation)

    def register_metric(
        self,
        metric_name: str,
        metric_owner: str,
        metric_source: str,
        aggregation: str = "max",
        confidence: float = 1.0,
        description: str = "",
    ) -> dict[str, Any]:
        definition = MetricDefinition(
            metric_name=str(metric_name),
            metric_owner=str(metric_owner),
            metric_source=str(metric_source),
            aggregation=str(aggregation or "max"),
            confidence=float(confidence if confidence is not None else 1.0),
            description=str(description or ""),
        )
        self.definitions[definition.metric_name] = definition
        return definition.as_dict()

    def definition_for(self, metric_name: str) -> MetricDefinition | None:
        return self.definitions.get(str(metric_name))

    def owner_for(self, metric_name: str) -> str:
        definition = self.definition_for(metric_name)
        return definition.metric_owner if definition else "unknown"

    def source_for(self, metric_name: str) -> str:
        definition = self.definition_for(metric_name)
        return definition.metric_source if definition else "unknown"

    def aggregation_for(self, metric_name: str) -> str:
        definition = self.definition_for(metric_name)
        return definition.aggregation if definition else "latest"

    def record_update(
        self,
        metric_name: str,
        value: Any,
        producer: str,
        source: str,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        if metric_name not in self.definitions:
            self.register_metric(
                metric_name,
                metric_owner=producer,
                metric_source=source,
                aggregation="latest",
                confidence=confidence,
            )
        update = {
            "metric_name": metric_name,
            "metric_owner": self.owner_for(metric_name),
            "metric_source": source,
            "producer": producer,
            "value": value,
            "confidence": float(confidence if confidence is not None else 1.0),
            "timestamp": str(datetime.utcnow()),
        }
        self.update_history.append(update)
        return update

    def metric_source_audit(
        self,
        sources: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        sources = sources if isinstance(sources, Mapping) else {}
        metrics = {}
        for metric_name, definition in self.definitions.items():
            producers = [
                producer
                for producer, payload in sources.items()
                if isinstance(payload, Mapping) and metric_name in payload
            ]
            metrics[metric_name] = {
                "producer": producers,
                "canonical_owner": definition.metric_owner,
                "canonical_source": definition.metric_source,
                "storage_location": "runtime.metrics.unified_metric_store",
                "update_frequency": "runtime_event_or_report_sync",
                "consumer": "runtime_observability_layer",
                "aggregation": definition.aggregation,
            }
        return {
            "system": self.system_name,
            "METRIC_SOURCE_AUDIT": True,
            "metrics": metrics,
            "metric_count": len(metrics),
            "sources_inspected": sorted(sources.keys()),
        }

    def build_report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "metrics_registered": len(self.definitions),
            "metric_owners": {
                name: definition.metric_owner
                for name, definition in sorted(self.definitions.items())
            },
            "metric_sources": {
                name: definition.metric_source
                for name, definition in sorted(self.definitions.items())
            },
            "update_count": len(self.update_history),
        }


canonical_metric_registry = CanonicalMetricRegistry()


__all__ = [
    "CanonicalMetricRegistry",
    "MetricDefinition",
    "canonical_metric_registry",
]
