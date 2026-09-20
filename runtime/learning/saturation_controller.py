"""Learning saturation controller for frozen concepts."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.learning.saturation_detector import (
    LearningSaturationDetector,
)
from runtime.meta.supervisor import meta_supervisor


class LearningSaturationController:
    """Convert saturation detection into runtime control flags."""

    def __init__(
        self,
        detector: LearningSaturationDetector | None = None,
    ) -> None:
        self.detector = detector or LearningSaturationDetector()

    def evaluate(
        self,
        concept_name: str,
        runtime_context: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        report = self.detector.evaluate(
            concept_name,
            dict(runtime_context or {}),
        )
        report["LEARNING_SATURATION_REPORT"] = {
            "concept_name": report["concept_name"],
            "evidence_saturated": report["evidence_saturated"],
            "dependency_chain_coverage": report["dependency_chain_coverage"],
            "transfer_reliability": report["transfer_reliability"],
            "recovery_streak": report["recovery_streak"],
            "learning_state": report["learning_state"],
        }
        if report["learning_state"] == self.detector.LEARNING_SATURATED:
            report.update({
                "recommended_next_step": "freeze_concept",
                "enable_adaptive_training": False,
                "enable_truth_rehearsal": False,
                "enable_context_reconstruction": False,
                "allow_integrity_monitoring": True,
                "allow_anomaly_detection": True,
                "allow_cache_verification": True,
            })
        return report

    def apply(
        self,
        runtime_context: Mapping[str, Any] | None,
        concept_name: str,
    ) -> dict[str, Any]:
        context = dict(runtime_context or {})
        if not meta_supervisor.is_action_allowed("strategy_evolution"):
            context["learning_saturation_report"] = {
                "system": "learning_saturation_controller",
                "status": "blocked_by_meta_supervisor",
                "enable_adaptive_training": False,
                "enable_context_reconstruction": False,
                "allow_integrity_monitoring": True,
            }
            context["enable_adaptive_training"] = False
            context["enable_context_reconstruction"] = False
            context["allow_integrity_monitoring"] = True
            return context
        report = self.evaluate(concept_name, context)
        context["LEARNING_SATURATION_REPORT"] = report[
            "LEARNING_SATURATION_REPORT"
        ]
        context["learning_saturation_report"] = report
        if report["learning_state"] == self.detector.LEARNING_SATURATED:
            context["learning_state"] = "LEARNING_SATURATED"
            context["recommended_next_step"] = "freeze_concept"
            context["enable_adaptive_training"] = False
            context["enable_truth_rehearsal"] = False
            context["enable_context_reconstruction"] = False
            context["allow_integrity_monitoring"] = True
            context["allow_anomaly_detection"] = True
            context["allow_cache_verification"] = True
        return context


learning_saturation_controller = LearningSaturationController()


__all__ = [
    "LearningSaturationController",
    "learning_saturation_controller",
]
