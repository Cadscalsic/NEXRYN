"""Probabilistic execution readiness calibration."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.transformation_localization.localization_metrics import (
    EXECUTION_THRESHOLD,
    HIGH_HYPOTHESIS_CONFIDENCE,
    LOCALIZATION_HIGH_CONFIDENCE,
    LOCALIZATION_MEDIUM_CONFIDENCE,
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
        identity_confidence: float | None = None,
        dependency_support: float = 1.0,
        arbitration_score: float | None = None,
        winning_hypothesis_stable: bool = True,
        dependency_evidence_exists: bool = True,
        contradiction_detected: bool = False,
    ) -> dict[str, Any]:
        hypothesis_confidence = clamp(hypothesis_confidence)
        localization_confidence = clamp(localization_confidence)
        prediction_accuracy = clamp(prediction_accuracy)
        if identity_confidence is None:
            identity_confidence = 1.0 if identity_stable else 0.0
        else:
            identity_confidence = clamp(identity_confidence)
        dependency_support = clamp(dependency_support)
        arbitration_score = (
            max(hypothesis_confidence, prediction_accuracy)
            if arbitration_score is None
            else clamp(arbitration_score)
        )
        evidence_score = max(hypothesis_confidence, prediction_accuracy)
        readiness = clamp(
            (
                hypothesis_confidence
                + dependency_support
                + identity_confidence
                + localization_confidence
            )
            / 4.0
        )
        localization_confidence_band = (
            "HIGH"
            if localization_confidence >= LOCALIZATION_HIGH_CONFIDENCE
            else "MEDIUM"
            if localization_confidence >= LOCALIZATION_MEDIUM_CONFIDENCE
            else "LOW"
        )
        probabilistic_ready = (
            evidence_score >= HIGH_HYPOTHESIS_CONFIDENCE
            and localization_confidence >= LOCALIZATION_EXECUTION_THRESHOLD
        )
        adaptive_probable = (
            arbitration_score > 0.85
            and winning_hypothesis_stable
            and dependency_evidence_exists
            and localization_confidence_band in {"HIGH", "MEDIUM"}
        )
        safety_blocked = (
            contradiction_detected
            or not integrity_preserved
            or not identity_stable
        )
        readiness_class = (
            "READINESS_HIGH"
            if readiness >= EXECUTION_THRESHOLD
            else "READINESS_MEDIUM"
            if readiness >= 0.70
            else "READINESS_LOW"
        )
        execution_governance_state = (
            "EXECUTION_SAFE"
            if readiness_class == "READINESS_HIGH"
            and localization_confidence_band == "HIGH"
            else "EXECUTION_PROBABLE"
            if readiness_class in {"READINESS_HIGH", "READINESS_MEDIUM"}
            and (probabilistic_ready or adaptive_probable)
            else "EXECUTION_EXPLORATORY"
        )
        execution_ready = (
            (probabilistic_ready or adaptive_probable or readiness_class == "READINESS_MEDIUM")
            and readiness >= 0.70
            and localization_confidence_band in {"HIGH", "MEDIUM"}
            and not safety_blocked
        )
        return {
            "execution_readiness": round(readiness, 4),
            "execution_ready": execution_ready,
            "execution_threshold": EXECUTION_THRESHOLD,
            "readiness_score": round(readiness, 4),
            "readiness_class": readiness_class,
            "execution_governance_state": execution_governance_state,
            "sandbox_execution_authorized":
            execution_ready and readiness_class == "READINESS_MEDIUM",
            "hypothesis_confidence": round(hypothesis_confidence, 4),
            "dependency_support": round(dependency_support, 4),
            "identity_confidence": round(identity_confidence, 4),
            "localization_confidence": round(localization_confidence, 4),
            "localization_confidence_band": localization_confidence_band,
            "prediction_accuracy": round(prediction_accuracy, 4),
            "arbitration_score": round(arbitration_score, 4),
            "winning_hypothesis_stable": bool(winning_hypothesis_stable),
            "dependency_evidence_exists": bool(dependency_evidence_exists),
            "safety_blocked": safety_blocked,
            "readiness_state": (
                execution_governance_state
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
