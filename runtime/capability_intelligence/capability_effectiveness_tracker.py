"""Capability effectiveness tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapabilityEffectivenessRecord:
    executions: int = 0
    successful_activations: int = 0
    failed_activations: int = 0
    prediction_improvements: float = 0.0
    confidence_improvements: float = 0.0
    residual_reduction: float = 0.0
    candidate_quality: float = 0.0
    repair_effectiveness: float = 0.0
    semantic_concept_usefulness: float = 0.0
    successful_task_contribution: int = 0
    failed_task_contribution: int = 0

    def score(self) -> float:
        value = (
            self.prediction_improvements * 2.0
            + self.confidence_improvements
            + self.residual_reduction * 1.5
            + self.candidate_quality
            + self.repair_effectiveness
            + self.semantic_concept_usefulness
            + self.successful_task_contribution
            - self.failed_task_contribution
        )
        return round(value / max(self.executions, 1), 4)

    def as_dict(self) -> dict[str, Any]:
        data = dict(self.__dict__)
        data["effectiveness_score"] = self.score()
        return data


class CapabilityEffectivenessTracker:
    def __init__(self):
        self.records: dict[str, CapabilityEffectivenessRecord] = {}

    def record(
        self,
        capability_name: str,
        success: bool = True,
        prediction_improvement: float = 0.0,
        confidence_improvement: float = 0.0,
        residual_reduction: float = 0.0,
        candidate_quality: float = 0.0,
        repair_effectiveness: float = 0.0,
        semantic_concept_usefulness: float = 0.0,
    ) -> CapabilityEffectivenessRecord:
        record = self.records.setdefault(capability_name, CapabilityEffectivenessRecord())
        record.executions += 1
        record.successful_activations += int(success)
        record.failed_activations += int(not success)
        record.prediction_improvements += float(prediction_improvement)
        record.confidence_improvements += float(confidence_improvement)
        record.residual_reduction += float(residual_reduction)
        record.candidate_quality += float(candidate_quality)
        record.repair_effectiveness += float(repair_effectiveness)
        record.semantic_concept_usefulness += float(semantic_concept_usefulness)
        record.successful_task_contribution += int(success)
        record.failed_task_contribution += int(not success)
        return record

    def score(self, capability_name: str) -> float:
        return self.records.get(capability_name, CapabilityEffectivenessRecord()).score()

    def as_dict(self) -> dict[str, Any]:
        return {name: record.as_dict() for name, record in sorted(self.records.items())}


__all__ = ["CapabilityEffectivenessRecord", "CapabilityEffectivenessTracker"]
