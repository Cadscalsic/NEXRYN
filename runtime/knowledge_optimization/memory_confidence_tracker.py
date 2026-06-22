"""Track confidence for reusable memory assets."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


class MemoryConfidenceTracker:
    def __init__(self) -> None:
        self.memory_confidence: dict[str, dict[str, Any]] = {}

    def update(
        self,
        memory_key: str,
        metrics: Mapping[str, Any] | None = None,
        reuse_succeeded: bool | None = None,
    ) -> dict[str, Any]:
        data = dict(metrics or {})
        current = self.memory_confidence.get(
            str(memory_key),
            {
                "strategy_confidence": 0.5,
                "concept_confidence": 0.5,
                "context_confidence": 0.5,
                "truth_confidence": 0.5,
                "reuse_frequency": 0,
                "last_success_timestamp": None,
            },
        )
        succeeded = bool(reuse_succeeded if reuse_succeeded is not None else data.get("reuse_succeeded", False))
        delta = 0.05 if succeeded else -0.05
        for key in (
            "strategy_confidence",
            "concept_confidence",
            "context_confidence",
            "truth_confidence",
        ):
            current[key] = self._bounded(data.get(key, current[key]) + delta)
        current["reuse_frequency"] = int(current.get("reuse_frequency", 0)) + 1
        if succeeded:
            current["last_success_timestamp"] = str(datetime.utcnow())
        self.memory_confidence[str(memory_key)] = current
        return {"memory_key": str(memory_key), **current}

    def average_confidence(self) -> float:
        if not self.memory_confidence:
            return 0.0
        values = []
        for item in self.memory_confidence.values():
            values.extend([
                float(item.get("strategy_confidence", 0.0)),
                float(item.get("concept_confidence", 0.0)),
                float(item.get("context_confidence", 0.0)),
                float(item.get("truth_confidence", 0.0)),
            ])
        return sum(values) / max(1, len(values))

    def _bounded(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


memory_confidence_tracker = MemoryConfidenceTracker()


__all__ = [
    "MemoryConfidenceTracker",
    "memory_confidence_tracker",
]
