"""Historical strategy memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class StrategyExecutionRecord:
    strategy_id: str
    task_signature: str
    task_family: str
    execution_policy: str
    capabilities_used: tuple[str, ...]
    capabilities_unused: tuple[str, ...] = ()
    activated_layers: tuple[str, ...] = ()
    suspended_layers: tuple[str, ...] = ()
    escalation_path: tuple[str, ...] = ()
    terminal_state: str = "UNKNOWN"
    execution_time: float = 0.0
    resource_cost: float = 0.0
    prediction_quality: float = 0.0
    confidence_score: float = 0.0
    deferred_work: tuple[str, ...] = ()
    strategy_effectiveness: float = 0.0

    @classmethod
    def create(cls, **kwargs: Any) -> "StrategyExecutionRecord":
        kwargs.setdefault("strategy_id", f"strategy-memory-{uuid4()}")
        return cls(**kwargs)

    def as_dict(self) -> dict[str, Any]:
        data = dict(self.__dict__)
        for key in ("capabilities_used", "capabilities_unused", "activated_layers", "suspended_layers", "escalation_path", "deferred_work"):
            data[key] = list(data[key])
        return data


class StrategyMemoryEngine:
    def __init__(self):
        self.records: list[StrategyExecutionRecord] = []

    def remember(self, record: StrategyExecutionRecord) -> StrategyExecutionRecord:
        self.records.append(record)
        return record

    def lookup(self, task_family: str, policy: str | None = None) -> list[StrategyExecutionRecord]:
        matches = [item for item in self.records if item.task_family == task_family]
        if policy:
            matches = [item for item in matches if item.execution_policy == policy]
        return sorted(matches, key=lambda item: item.strategy_effectiveness, reverse=True)

    def count(self, task_family: str | None = None) -> int:
        return len(self.lookup(task_family)) if task_family else len(self.records)


__all__ = ["StrategyExecutionRecord", "StrategyMemoryEngine"]
