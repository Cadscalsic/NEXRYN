"""Registry for dynamic ARC concept models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


class DynamicConceptRegistry:
    """Track concept family use, support, reuse, and prediction gain."""

    system_name = "dynamic_concept_registry"

    def __init__(self):
        self.records = {}

    def register(
        self,
        model: Mapping[str, Any],
        simulation_report: Mapping[str, Any] | None = None,
        reused: bool = False,
    ) -> dict[str, Any]:
        simulation_report = (
            simulation_report
            if isinstance(simulation_report, Mapping)
            else {}
        )
        family = str(model.get("concept_family", "unknown"))
        record = self.records.setdefault(
            family,
            {
                "concept_family": family,
                "activation_frequency": 0,
                "success_count": 0,
                "reuse_count": 0,
                "prediction_gain_total": 0.0,
                "causal_support_total": 0.0,
                "process_support_total": 0.0,
                "last_observed_at": None,
            },
        )
        accuracy = float(
            simulation_report.get("simulation_accuracy", 0.0) or 0.0
        )
        prediction_gain = float(
            simulation_report.get("prediction_gain", 0.0) or 0.0
        )
        record["activation_frequency"] += 1
        record["success_count"] += 1 if accuracy >= 0.80 else 0
        record["reuse_count"] += 1 if reused else 0
        record["prediction_gain_total"] += prediction_gain
        record["causal_support_total"] += float(model.get("causal_support", 0.0) or 0.0)
        record["process_support_total"] += float(model.get("process_support", 0.0) or 0.0)
        record["last_observed_at"] = str(datetime.utcnow())
        return self.summary(family)

    def summary(self, family: str) -> dict[str, Any]:
        record = dict(self.records.get(family, {}))
        frequency = max(record.get("activation_frequency", 0), 1)
        record["success_rate"] = round(record.get("success_count", 0) / frequency, 4)
        record["reuse_rate"] = round(record.get("reuse_count", 0) / frequency, 4)
        record["prediction_gain"] = round(
            record.get("prediction_gain_total", 0.0) / frequency,
            4,
        )
        record["causal_support"] = round(
            record.get("causal_support_total", 0.0) / frequency,
            4,
        )
        record["process_support"] = round(
            record.get("process_support_total", 0.0) / frequency,
            4,
        )
        return record

    def build_report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "dynamic_concept_families": {
                family: self.summary(family)
                for family in sorted(self.records)
            },
        }


dynamic_concept_registry = DynamicConceptRegistry()


__all__ = ["DynamicConceptRegistry", "dynamic_concept_registry"]
