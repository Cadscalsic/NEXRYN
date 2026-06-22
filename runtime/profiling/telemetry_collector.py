"""Lightweight telemetry stream for runtime profiling."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
import time
from typing import Any


@dataclass
class TelemetryEvent:
    category: str
    metric_name: str
    value: Any
    timestamp: float
    iso_timestamp: str


class TelemetryCollector:
    """In-memory, disableable telemetry with deferred export."""

    def __init__(self, enabled: bool = False, max_events: int = 10000):
        self.enabled = enabled
        self.events: deque[TelemetryEvent] = deque(maxlen=max_events)
        self.dropped_events = 0

    def configure(self, enabled: bool | None = None, max_events: int | None = None):
        if enabled is not None:
            self.enabled = bool(enabled)
        if max_events is not None and max_events != self.events.maxlen:
            self.events = deque(self.events, maxlen=max(1, int(max_events)))

    def record(self, category: str, metric_name: str, value: Any) -> None:
        if not self.enabled:
            return
        try:
            self.events.append(
                TelemetryEvent(
                    category=str(category),
                    metric_name=str(metric_name),
                    value=value,
                    timestamp=time.perf_counter(),
                    iso_timestamp=str(datetime.utcnow()),
                )
            )
        except Exception:
            self.dropped_events += 1

    def snapshot(self) -> list[dict[str, Any]]:
        return [asdict(event) for event in list(self.events)]

    def report(self) -> dict[str, Any]:
        by_category: dict[str, int] = {}
        for event in self.events:
            by_category[event.category] = by_category.get(event.category, 0) + 1
        return {
            "enabled": self.enabled,
            "event_count": len(self.events),
            "dropped_events": self.dropped_events,
            "events_by_category": by_category,
        }

    def clear(self) -> None:
        self.events.clear()
        self.dropped_events = 0


telemetry = TelemetryCollector()


__all__ = [
    "TelemetryCollector",
    "TelemetryEvent",
    "telemetry",
]
