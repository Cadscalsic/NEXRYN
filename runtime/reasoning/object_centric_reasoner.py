"""Object-centric reasoning facade for localized transformation salience."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.reasoning.change_detection_engine import ChangeDetectionEngine
from runtime.reasoning.invariant_filter import InvariantFilter
from runtime.reasoning.transformation_salience_engine import TransformationSalienceEngine


class ObjectCentricReasoner:
    """Ask which objects changed before ranking what stayed stable."""

    system_name = "object_centric_reasoner"

    PRIMITIVE_TO_TRANSFORMATION = {
        "translate_left": "object_translation",
        "translate_right": "object_translation",
        "translate_up": "object_translation",
        "translate_down": "object_translation",
        "object_translation": "object_translation",
        "replace_color": "object_color_change",
        "expand_object": "object_size_change",
        "shrink_object": "object_size_change",
        "grow_topology": "object_topology_change",
        "compress_topology": "object_topology_change",
        "duplicate_object": "object_topology_change",
        "remove_object": "object_topology_change",
    }

    def __init__(
        self,
        change_detector: ChangeDetectionEngine | None = None,
        salience_engine: TransformationSalienceEngine | None = None,
        invariant_filter: InvariantFilter | None = None,
    ) -> None:
        self.change_detector = change_detector or ChangeDetectionEngine()
        self.salience_engine = salience_engine or TransformationSalienceEngine()
        self.invariant_filter = invariant_filter or InvariantFilter()

    def reason(
        self,
        input_objects: list[Mapping[str, Any]] | None,
        output_objects: list[Mapping[str, Any]] | None,
        hypotheses: list[Mapping[str, Any]] | None = None,
        causal_support: float = 1.0,
    ) -> dict[str, Any]:
        change_detection = self.change_detector.detect_changes(
            input_objects,
            output_objects,
        )
        object_change_report = change_detection["object_change_report"]
        salience = self.salience_engine.score_changes(
            object_change_report,
            causal_support=causal_support,
        )
        annotated_hypotheses = self.annotate_hypotheses(
            hypotheses or [],
            salience,
            object_change_report,
        )
        arbitration_report = self._arbitration_preview(
            annotated_hypotheses,
        )
        return {
            "system": self.system_name,
            "OBJECT_CHANGE_REPORT": object_change_report,
            "TRANSFORMATION_SALIENCE_REPORT": salience["TRANSFORMATION_SALIENCE_REPORT"],
            "ARBITRATION_REPORT": arbitration_report,
            "object_change_report": object_change_report,
            "transformation_salience_report": salience,
            "arbitration_report": arbitration_report,
            "annotated_hypotheses": annotated_hypotheses,
        }

    def annotate_hypotheses(
        self,
        hypotheses: list[Mapping[str, Any]],
        salience_report: Mapping[str, Any],
        object_change_report: list[Mapping[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        salience_scores = dict(salience_report.get("salience_scores", {}) or {})
        residual_reduction = dict(salience_report.get("residual_reduction", {}) or {})
        changed_objects = [
            report
            for report in object_change_report or []
            if isinstance(report, Mapping) and report.get("changed")
        ]
        total_objects = max(len(object_change_report or []), 1)
        changed_power = min(len(changed_objects) / total_objects, 1.0)
        annotated = self.invariant_filter.annotate(hypotheses)

        for hypothesis in annotated:
            transformation = self._hypothesis_transformation(hypothesis)
            transformation_salience = salience_scores.get(transformation, 0.0)
            hypothesis["transformation_salience"] = round(transformation_salience, 4)
            hypothesis["residual_reduction"] = round(
                residual_reduction.get(transformation, 0.0),
                4,
            )
            if hypothesis["semantic_class"] == "invariant":
                hypothesis["explanatory_power"] = min(
                    float(hypothesis.get("explanatory_power", 0.0) or 0.0),
                    0.35,
                )
            else:
                hypothesis["explanatory_power"] = round(
                    max(
                        float(hypothesis.get("explanatory_power", 0.0) or 0.0),
                        residual_reduction.get(transformation, 0.0),
                        transformation_salience,
                        changed_power if transformation_salience > 0 else 0.0,
                    ),
                    4,
                )
            hypothesis["object_centric_transformation"] = transformation
        return annotated

    def _hypothesis_transformation(self, hypothesis: Mapping[str, Any]) -> str:
        primitive = str(hypothesis.get("primitive", ""))
        hypothesis_type = str(hypothesis.get("type", ""))
        if primitive in self.PRIMITIVE_TO_TRANSFORMATION:
            return self.PRIMITIVE_TO_TRANSFORMATION[primitive]
        if "translation" in hypothesis_type or "translation" in primitive:
            return "object_translation"
        if "color" in hypothesis_type or "color" in primitive:
            return "object_color_change"
        if "size" in hypothesis_type or "size" in primitive:
            return "object_size_change"
        if "topology" in hypothesis_type or "topology" in primitive:
            return "object_topology_change"
        return primitive or hypothesis_type or "unknown"

    def _arbitration_preview(
        self,
        hypotheses: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        if not hypotheses:
            return {
                "candidate_count": 0,
                "winning_hypothesis": None,
                "explanatory_power": 0.0,
                "residual_reduction": 0.0,
                "invariant_penalty": 0.0,
                "final_score": 0.0,
            }
        winner = max(
            hypotheses,
            key=lambda hypothesis: hypothesis.get("transformation_salience", 0.0),
        )
        return {
            "candidate_count": len(hypotheses),
            "winning_hypothesis": winner.get("primitive"),
            "explanatory_power": winner.get("explanatory_power", 0.0),
            "residual_reduction": winner.get("residual_reduction", 0.0),
            "invariant_penalty": winner.get("invariant_penalty", 0.0),
            "final_score": winner.get("transformation_salience", 0.0),
        }


object_centric_reasoner = ObjectCentricReasoner()


__all__ = [
    "ObjectCentricReasoner",
    "object_centric_reasoner",
]
