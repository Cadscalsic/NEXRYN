"""Observed capability cost intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CapabilityCostRecord:
    observations: int = 0
    total_latency: float = 0.0
    total_memory: float = 0.0
    total_activation_cost: float = 0.0
    escalation_count: int = 0
    serialization_cost: float = 0.0

    def average_latency(self) -> float:
        return round(self.total_latency / max(self.observations, 1), 6)

    def average_memory(self) -> float:
        return round(self.total_memory / max(self.observations, 1), 6)

    def average_activation_cost(self) -> float:
        return round(self.total_activation_cost / max(self.observations, 1), 6)

    def as_dict(self) -> dict[str, Any]:
        return {
            **dict(self.__dict__),
            "average_latency": self.average_latency(),
            "average_memory": self.average_memory(),
            "average_activation_cost": self.average_activation_cost(),
        }


class CapabilityCostIntelligence:
    def __init__(self):
        self.records: dict[str, CapabilityCostRecord] = {}

    def record_cost(
        self,
        capability_name: str,
        latency: float = 0.0,
        memory: float = 0.0,
        activation_cost: float = 0.0,
        escalated: bool = False,
        serialization_cost: float = 0.0,
    ) -> CapabilityCostRecord:
        record = self.records.setdefault(capability_name, CapabilityCostRecord())
        record.observations += 1
        record.total_latency += float(latency)
        record.total_memory += float(memory)
        record.total_activation_cost += float(activation_cost)
        record.escalation_count += int(escalated)
        record.serialization_cost += float(serialization_cost)
        return record

    def get(self, capability_name: str) -> CapabilityCostRecord | None:
        return self.records.get(capability_name)

    def as_dict(self) -> dict[str, Any]:
        return {name: record.as_dict() for name, record in sorted(self.records.items())}


__all__ = ["CapabilityCostIntelligence", "CapabilityCostRecord"]
