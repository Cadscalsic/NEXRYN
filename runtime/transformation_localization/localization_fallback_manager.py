"""Progressive fallback for failed precise localization."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from runtime.transformation_localization.localization_metrics import (
    LOCALIZATION_EXECUTION_THRESHOLD,
    SUPPORTED_TRANSFORMATIONS,
    clamp,
)


class LocalizationFallbackManager:
    fallback_order = [
        "object_level",
        "region_level",
        "global_transformation",
    ]

    def apply(
        self,
        localization: Mapping[str, Any] | None,
        synthesized_program: Mapping[str, Any] | None,
        hypothesis: Mapping[str, Any] | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        result = deepcopy(localization if isinstance(localization, Mapping) else {})
        synthesized_program = (
            synthesized_program if isinstance(synthesized_program, Mapping) else {}
        )
        hypothesis = hypothesis if isinstance(hypothesis, Mapping) else {}
        current = clamp(result.get("localization_confidence"))
        if current >= LOCALIZATION_EXECUTION_THRESHOLD and not force:
            result.setdefault("fallback_used", None)
            return result

        operation = self._operation(synthesized_program, hypothesis)
        fallback = self._select_fallback(result, operation)
        if fallback is None:
            result["fallback_used"] = None
            return result

        hypothesis_confidence = clamp(hypothesis.get("confidence"))
        if hypothesis_confidence <= 0.0:
            hypothesis_confidence = clamp(result.get("transformation_confidence", 0.85))
        fallback_confidence = max(current, clamp(hypothesis_confidence * fallback["confidence_factor"]))
        result.update({
            "fallback_used": fallback["name"],
            "fallback_scope": fallback["scope"],
            "fallback_reason": "precise_localization_below_execution_threshold",
            "localization_confidence": round(fallback_confidence, 4),
            "localization_ready": fallback_confidence >= LOCALIZATION_EXECUTION_THRESHOLD,
            "localized_step_count": max(
                int(result.get("localized_step_count", 0) or 0),
                int(synthesized_program.get("step_count", 0) or len(synthesized_program.get("steps", []) or [])),
            ),
        })
        if "localized_program" not in result and synthesized_program:
            result["localized_program"] = deepcopy(synthesized_program)
        return result

    def _select_fallback(
        self,
        localization: Mapping[str, Any],
        operation: str,
    ) -> dict[str, Any] | None:
        if localization.get("target_objects"):
            return {
                "name": "object_level_fallback",
                "scope": "object_level",
                "confidence_factor": 0.88,
            }
        if operation in SUPPORTED_TRANSFORMATIONS:
            if operation.startswith("translate") or operation in {
                "translation",
                "duplicate_object",
            }:
                return {
                    "name": "global_translation_fallback",
                    "scope": "global_transformation",
                    "confidence_factor": 0.86,
                }
            return {
                "name": "global_transformation_fallback",
                "scope": "global_transformation",
                "confidence_factor": 0.82,
            }
        if localization.get("localization_reports"):
            return {
                "name": "region_level_fallback",
                "scope": "region_level",
                "confidence_factor": 0.78,
            }
        return None

    def _operation(
        self,
        synthesized_program: Mapping[str, Any],
        hypothesis: Mapping[str, Any],
    ) -> str:
        primitive = hypothesis.get("primitive") or hypothesis.get("type")
        if primitive:
            return str(primitive).lower()
        for step in synthesized_program.get("steps", []) or []:
            if isinstance(step, Mapping):
                operation = step.get("operation") or step.get("primitive")
                if operation:
                    return str(operation).lower()
        return "unknown"


localization_fallback_manager = LocalizationFallbackManager()


__all__ = [
    "LocalizationFallbackManager",
    "localization_fallback_manager",
]
