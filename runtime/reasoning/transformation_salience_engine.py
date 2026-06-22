"""Salience scoring for localized transformations."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping


class TransformationSalienceEngine:
    """Rank transformations by explanatory salience, never by majority size."""

    system_name = "transformation_salience_engine"

    CHANGE_TO_TRANSFORMATION = {
        "translation": "object_translation",
        "rotation": "object_rotation",
        "reflection": "object_reflection",
        "scaling": "object_scaling",
        "color_change": "object_color_change",
        "topology_change": "object_topology_change",
        "size_change": "object_size_change",
    }

    def score_changes(
        self,
        object_change_report: list[Mapping[str, Any]] | None,
        causal_support: float = 1.0,
    ) -> dict[str, Any]:
        salience_scores: dict[str, float] = defaultdict(float)
        residual_reduction: dict[str, float] = defaultdict(float)
        invariant_penalties = {}

        for report in object_change_report or []:
            if not isinstance(report, Mapping) or not report.get("changed"):
                continue
            transformation = self.CHANGE_TO_TRANSFORMATION.get(
                str(report.get("change_type")),
                str(report.get("change_type", "unknown")),
            )
            reduction = self._clamp(report.get("explanatory_power", 0.0))
            score = (
                self._clamp(report.get("change_magnitude", 0.0)) * 0.35
                + self._clamp(report.get("explanatory_power", 0.0)) * 0.35
                + reduction * 0.20
                + self._clamp(causal_support) * 0.10
            )
            salience_scores[transformation] += score
            residual_reduction[transformation] += reduction

        dominant = None
        if salience_scores:
            dominant = max(
                salience_scores,
                key=lambda key: salience_scores[key],
            )

        return {
            "system": self.system_name,
            "TRANSFORMATION_SALIENCE_REPORT": {
                "dominant_transformation": dominant,
                "salience_scores": {
                    key: round(self._clamp(value), 4)
                    for key, value in salience_scores.items()
                },
                "invariant_penalties": invariant_penalties,
                "residual_reduction": {
                    key: round(self._clamp(value), 4)
                    for key, value in residual_reduction.items()
                },
            },
            "dominant_transformation": dominant,
            "salience_scores": {
                key: round(self._clamp(value), 4)
                for key, value in salience_scores.items()
            },
            "invariant_penalties": invariant_penalties,
            "residual_reduction": {
                key: round(self._clamp(value), 4)
                for key, value in residual_reduction.items()
            },
        }

    def _clamp(self, value: Any) -> float:
        if not isinstance(value, (int, float)):
            return 0.0
        return max(0.0, min(float(value), 1.0))


transformation_salience_engine = TransformationSalienceEngine()


__all__ = [
    "TransformationSalienceEngine",
    "transformation_salience_engine",
]
