"""Capability cooperation intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any


@dataclass
class CapabilityCooperationRecord:
    capability_pair: tuple[str, str]
    observations: int = 0
    combined_latency: float = 0.0
    prediction_gain: float = 0.0
    residual_reduction: float = 0.0

    def effectiveness(self) -> float:
        value = self.prediction_gain + self.residual_reduction
        return round(value / max(self.observations, 1), 4)

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_pair": list(self.capability_pair),
            "observations": self.observations,
            "combined_latency": self.combined_latency,
            "prediction_gain": self.prediction_gain,
            "residual_reduction": self.residual_reduction,
            "cooperation_effectiveness": self.effectiveness(),
        }


class CapabilityCooperationEngine:
    def __init__(self):
        self.records: dict[tuple[str, str], CapabilityCooperationRecord] = {}

    def record_cooperation(
        self,
        capabilities: list[str] | tuple[str, ...],
        combined_latency: float = 0.0,
        prediction_gain: float = 0.0,
        residual_reduction: float = 0.0,
    ) -> None:
        for pair in combinations(sorted(set(capabilities)), 2):
            record = self.records.setdefault(pair, CapabilityCooperationRecord(pair))
            record.observations += 1
            record.combined_latency += float(combined_latency)
            record.prediction_gain += float(prediction_gain)
            record.residual_reduction += float(residual_reduction)

    def best_pairs(self, limit: int = 5) -> list[CapabilityCooperationRecord]:
        return sorted(self.records.values(), key=lambda item: item.effectiveness(), reverse=True)[:limit]

    def as_dict(self) -> dict[str, Any]:
        return {"|".join(pair): record.as_dict() for pair, record in sorted(self.records.items())}


__all__ = ["CapabilityCooperationEngine", "CapabilityCooperationRecord"]
