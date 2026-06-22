"""Probabilistic execution readiness calibration."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.transformation_localization.localization_metrics import (
    EXECUTION_THRESHOLD,
    HIGH_HYPOTHESIS_CONFIDENCE,
    LOCALIZATION_EXECUTION_THRESHOLD,
    clamp,
)


class ExecutionReadinessCalibrator:
    def evaluate(
        self,
        hypothesis_confidence: float = 0.0,
        localization_confidence: float = 0.0,
        prediction_accuracy: float = 0.0,
        integrity_preserved: bool = True,
        identity_stable: bool = True,
        contradiction_detected: bool = False,
    ) -> dict[str, Any]:
        hypothesis_confidence = clamp(hypothesis_confidence)
        localization_confidence = clamp(localization_confidence)
        prediction_accuracy = clamp(prediction_accuracy)
        evidence_score = max(hypothesis_confidence, prediction_accuracy)
        readiness = clamp(
            evidence_score * 0.45
            + localization_confidence * 0.35
            + prediction_accuracy * 0.20
        )
        probabilistic_ready = (
            evidence_score >= HIGH_HYPOTHESIS_CONFIDENCE
            and localization_confidence >= LOCALIZATION_EXECUTION_THRESHOLD
        )
        safety_blocked = (
            contradiction_detected
            or not integrity_preserved
            or not identity_stable
        )
        execution_ready = (
            probabilistic_ready
            and readiness >= EXECUTION_THRESHOLD
            and not safety_blocked
        )
        return {
            "execution_readiness": round(readiness, 4),
            "execution_ready": execution_ready,
            "execution_threshold": EXECUTION_THRESHOLD,
            "hypothesis_confidence": round(hypothesis_confidence, 4),
            "localization_confidence": round(localization_confidence, 4),
            "prediction_accuracy": round(prediction_accuracy, 4),
            "safety_blocked": safety_blocked,
            "readiness_state": (
                "EXECUTION_READY"
                if execution_ready
                else "EXECUTION_BLOCKED_BY_SAFETY"
                if safety_blocked
                else "LOCALIZATION_OR_CONFIDENCE_INSUFFICIENT"
            ),
        }


execution_readiness_calibrator = ExecutionReadinessCalibrator()


__all__ = [
    "ExecutionReadinessCalibrator",
    "execution_readiness_calibrator",
]
