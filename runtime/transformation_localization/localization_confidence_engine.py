"""Probabilistic confidence synthesis for localization evidence."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.transformation_localization.localization_metrics import (
    HIGH_HYPOTHESIS_CONFIDENCE,
    clamp,
)


class LocalizationConfidenceEngine:
    weights = {
        "object_detection": 0.25,
        "transformation": 0.25,
        "geometric_grounding": 0.20,
        "semantic_support": 0.15,
        "causal_support": 0.15,
    }

    def evaluate(
        self,
        localization: Mapping[str, Any] | None = None,
        hypothesis: Mapping[str, Any] | None = None,
        synthesized_program: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        localization = localization if isinstance(localization, Mapping) else {}
        hypothesis = hypothesis if isinstance(hypothesis, Mapping) else {}
        synthesized_program = (
            synthesized_program if isinstance(synthesized_program, Mapping) else {}
        )

        components = {
            "object_detection": self._object_detection(localization),
            "transformation": self._transformation(localization, hypothesis),
            "geometric_grounding": self._geometric_grounding(
                localization,
                hypothesis,
                synthesized_program,
            ),
            "semantic_support": self._semantic_support(hypothesis, synthesized_program),
            "causal_support": self._causal_support(localization, hypothesis),
        }
        confidence = sum(
            components[name] * self.weights[name]
            for name in self.weights
        )
        existing = clamp(localization.get("localization_confidence"))
        confidence = max(existing, confidence)
        explanation = None
        hypothesis_confidence = clamp(
            hypothesis.get("confidence", synthesized_program.get("confidence", 0.0))
        )
        if hypothesis_confidence >= HIGH_HYPOTHESIS_CONFIDENCE and confidence <= 0.0:
            explanation = (
                "high_hypothesis_confidence_without_localization_evidence"
            )
        return {
            "localization_confidence": round(clamp(confidence), 4),
            "confidence_components": {
                key: round(value, 4)
                for key, value in components.items()
            },
            "confidence_weights": dict(self.weights),
            "zero_confidence_explanation": explanation,
        }

    def _object_detection(self, localization: Mapping[str, Any]) -> float:
        reports = localization.get("localization_reports", []) or []
        matches = [
            match
            for report in reports
            if isinstance(report, Mapping)
            for match in report.get("object_matches", []) or []
            if isinstance(match, Mapping)
        ]
        if matches:
            values = [
                clamp(match.get("identity_confidence", match.get("match_confidence", 0.0)))
                for match in matches
            ]
            return sum(values) / len(values)
        target_objects = localization.get("target_objects", []) or []
        if target_objects:
            return 0.85
        reports_with_anchor = [
            report
            for report in reports
            if isinstance(report, Mapping) and report.get("anchor_object")
        ]
        return 0.75 if reports_with_anchor else 0.0

    def _transformation(
        self,
        localization: Mapping[str, Any],
        hypothesis: Mapping[str, Any],
    ) -> float:
        reports = localization.get("localization_reports", []) or []
        values = [
            clamp(report.get("placement_confidence"))
            for report in reports
            if isinstance(report, Mapping)
        ]
        values.extend(
            clamp(report.get("localization_confidence"))
            for report in reports
            if isinstance(report, Mapping)
        )
        values.append(clamp(hypothesis.get("confidence")))
        values = [value for value in values if value > 0.0]
        return max(values) if values else 0.0

    def _geometric_grounding(
        self,
        localization: Mapping[str, Any],
        hypothesis: Mapping[str, Any],
        synthesized_program: Mapping[str, Any],
    ) -> float:
        grounding = hypothesis.get("geometric_grounding", {})
        if isinstance(grounding, Mapping):
            grounded = clamp(grounding.get("confidence"))
            if grounded > 0.0:
                return grounded
        reports = localization.get("localization_reports", []) or []
        has_offset = any(
            isinstance(report, Mapping)
            and report.get("relative_offset") not in (None, [0, 0])
            for report in reports
        )
        has_constraints = any(
            isinstance(report, Mapping) and bool(report.get("spatial_constraints"))
            for report in reports
        )
        has_steps = bool(synthesized_program.get("steps"))
        return clamp((0.45 if has_offset else 0.0) + (0.25 if has_constraints else 0.0) + (0.20 if has_steps else 0.0))

    def _semantic_support(
        self,
        hypothesis: Mapping[str, Any],
        synthesized_program: Mapping[str, Any],
    ) -> float:
        explicit = clamp(hypothesis.get("semantic_support"))
        if explicit > 0.0:
            return explicit
        operations = [
            str(step.get("operation", step.get("primitive", ""))).lower()
            for step in synthesized_program.get("steps", []) or []
            if isinstance(step, Mapping)
        ]
        return 0.85 if operations else 0.0

    def _causal_support(
        self,
        localization: Mapping[str, Any],
        hypothesis: Mapping[str, Any],
    ) -> float:
        explicit = clamp(hypothesis.get("causal_support"))
        reports = localization.get("localization_reports", []) or []
        evidence_values = []
        for report in reports:
            if not isinstance(report, Mapping):
                continue
            evidence = report.get("causal_evidence", {})
            if isinstance(evidence, Mapping):
                placement = evidence.get("placement_reasoning", {})
                if isinstance(placement, Mapping):
                    for item in placement.get("dependency_evidence", []) or []:
                        if isinstance(item, Mapping):
                            evidence_values.append(clamp(item.get("confidence", 1.0)))
                if evidence:
                    evidence_values.append(0.80)
            for constraint in report.get("spatial_constraints", []) or []:
                if isinstance(constraint, Mapping) and constraint.get("type") == "causal_dependency":
                    evidence_values.append(clamp(constraint.get("confidence", 1.0)))
        if evidence_values:
            return max(explicit, sum(evidence_values) / len(evidence_values))
        return explicit


localization_confidence_engine = LocalizationConfidenceEngine()


__all__ = [
    "LocalizationConfidenceEngine",
    "localization_confidence_engine",
]
