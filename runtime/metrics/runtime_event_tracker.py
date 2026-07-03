"""Runtime event tracking that derives metrics from events."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from runtime.metrics.unified_metric_store import unified_metric_store


class RuntimeEventTracker:
    """Track runtime events and update canonical metrics."""

    system_name = "runtime_event_tracker"

    EVENT_TO_METRIC = {
        "route_creation": "active_routes",
        "route_execution": "reasoning_depth",
        "strategy_reuse": "strategy_hits",
        "truth_reuse": "truth_hits",
        "context_reuse": "context_hits",
        "dependency_execution": "dependency_chains_executed",
        "process_generation": "process_context_count",
        "causal_generation": "causal_context_count",
        "repair_execution": "repair_success_rate",
        "prediction_generation": "prediction_accuracy",
    }

    def __init__(self, store=None):
        self.store = store or unified_metric_store
        self.events: list[dict[str, Any]] = []

    def track(
        self,
        event_type: str,
        value: Any = 1,
        producer: str | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "event_type": str(event_type),
            "value": value,
            "producer": producer or self.system_name,
            "source": source or "runtime_event",
            "metadata": dict(metadata or {}),
            "timestamp": str(datetime.utcnow()),
        }
        self.events.append(event)
        metric_name = self.EVENT_TO_METRIC.get(event["event_type"])
        if metric_name:
            self.store.update_metric(
                metric_name,
                value,
                producer=event["producer"],
                source=event["source"],
                confidence=0.95,
                timestamp=event["timestamp"],
            )
        return event

    def build_report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "event_count": len(self.events),
            "events_by_type": {
                event_type: len([
                    event for event in self.events
                    if event["event_type"] == event_type
                ])
                for event_type in sorted({event["event_type"] for event in self.events})
            },
            "recent_events": self.events[-10:],
        }


runtime_event_tracker = RuntimeEventTracker()


__all__ = ["RuntimeEventTracker", "runtime_event_tracker"]
