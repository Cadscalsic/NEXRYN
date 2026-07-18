"""Deterministic capability cost prediction."""

from __future__ import annotations

from typing import Any

from runtime.capability_intelligence.capability_cost_intelligence import CapabilityCostIntelligence
from runtime.capability_intelligence.capability_effectiveness_tracker import CapabilityEffectivenessTracker


class CapabilityCostPredictor:
    def __init__(
        self,
        cost_intelligence: CapabilityCostIntelligence,
        effectiveness_tracker: CapabilityEffectivenessTracker,
    ):
        self.cost_intelligence = cost_intelligence
        self.effectiveness_tracker = effectiveness_tracker

    def predict(self, capability_name: str) -> dict[str, Any]:
        cost = self.cost_intelligence.get(capability_name)
        usefulness = self.effectiveness_tracker.score(capability_name)
        if cost is None:
            return {
                "capability_name": capability_name,
                "expected_latency": "UNKNOWN",
                "expected_memory": "UNKNOWN",
                "expected_usefulness": usefulness if usefulness else "UNKNOWN",
                "expected_escalation_probability": "UNKNOWN",
                "expected_repair_probability": "UNKNOWN",
                "evidence": "insufficient_history",
            }
        return {
            "capability_name": capability_name,
            "expected_latency": cost.average_latency(),
            "expected_memory": cost.average_memory(),
            "expected_usefulness": usefulness,
            "expected_escalation_probability": round(cost.escalation_count / max(cost.observations, 1), 4),
            "expected_repair_probability": 0.0,
            "evidence": "observed_history",
        }


__all__ = ["CapabilityCostPredictor"]
