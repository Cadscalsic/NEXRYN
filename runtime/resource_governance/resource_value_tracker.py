"""Per-layer value evidence tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALUE_WEIGHTS = {
    "concepts_generated": 1.0,
    "valid_hypotheses_generated": 1.5,
    "candidates_generated": 1.2,
    "prediction_improvement": 3.0,
    "confidence_improvement": 2.0,
    "residual_reduction": 3.0,
    "contradiction_resolution": 2.5,
    "dependency_resolution": 2.0,
    "execution_success": 4.0,
    "unique_information_produced": 1.5,
}


@dataclass
class LayerValueRecord:
    evidence: dict[str, float] = field(default_factory=dict)
    resource_cost: float = 0.0

    def value(self) -> float:
        return sum(VALUE_WEIGHTS.get(name, 1.0) * amount for name, amount in self.evidence.items())

    def efficiency(self) -> float:
        return round(self.value() / max(self.resource_cost, 1.0), 6)


class ResourceValueTracker:
    def __init__(self):
        self.records: dict[str, LayerValueRecord] = {}

    def record(self, layer_name: str, evidence: dict[str, float] | None = None, resource_cost: float = 0.0) -> LayerValueRecord:
        record = self.records.setdefault(layer_name, LayerValueRecord())
        for key, value in dict(evidence or {}).items():
            record.evidence[key] = record.evidence.get(key, 0.0) + float(value)
        record.resource_cost += max(0.0, float(resource_cost))
        return record

    def efficiency(self, layer_name: str) -> float:
        return self.records.get(layer_name, LayerValueRecord()).efficiency()

    def as_dict(self) -> dict[str, Any]:
        return {
            name: {
                "evidence": dict(record.evidence),
                "resource_cost": record.resource_cost,
                "value": record.value(),
                "efficiency": record.efficiency(),
            }
            for name, record in sorted(self.records.items())
        }


__all__ = ["LayerValueRecord", "ResourceValueTracker"]
