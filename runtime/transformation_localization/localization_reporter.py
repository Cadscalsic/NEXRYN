"""Reporting utilities for transformation localization."""

from __future__ import annotations

from typing import Any, Mapping


class LocalizationReporter:
    def build(
        self,
        localization: Mapping[str, Any],
        readiness: Mapping[str, Any],
        budget_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        budget_report = budget_report if isinstance(budget_report, Mapping) else {}
        readiness_report = localization.get("EXECUTION READINESS REPORT", {})
        if not isinstance(readiness_report, Mapping):
            readiness_report = {}
        grounding_report = localization.get("OBJECT GROUNDING REPORT", {})
        if not isinstance(grounding_report, Mapping):
            grounding_report = {}
        return {
            "system": "LOCALIZATION_REPORT",
            "localization_confidence": localization.get("localization_confidence", 0.0),
            "execution_readiness": readiness.get("execution_readiness", 0.0),
            "readiness_class": readiness.get("readiness_class"),
            "localization_confidence_band":
            readiness.get("localization_confidence_band"),
            "execution_governance_state":
            readiness.get("execution_governance_state"),
            "sandbox_execution_authorized":
            readiness.get("sandbox_execution_authorized") is True
            or readiness_report.get("readiness_class") == "EXECUTION_PROBATION",
            "execution_probation":
            readiness_report.get("readiness_class") == "EXECUTION_PROBATION",
            "target_objects": localization.get("target_objects", []),
            "affected_objects": localization.get("affected_objects", []),
            "anchor_objects": localization.get("anchor_objects", []),
            "transformation_targets":
            localization.get("transformation_targets", []),
            "candidate_object_regions":
            localization.get("candidate_object_regions", []),
            "candidate_transform_regions":
            localization.get("candidate_transform_regions", []),
            "localization_hints": localization.get("localization_hints", []),
            "object_detection": grounding_report.get("object_detection", 0.0),
            "transformation_detection":
            grounding_report.get("transformation_detection", 0.0),
            "causal_support": grounding_report.get("causal_support", 0.0),
            "OBJECT GROUNDING REPORT": grounding_report,
            "EXECUTION READINESS REPORT": readiness_report,
            "LOCALIZATION EXPLAINER REPORT":
            grounding_report.get("LOCALIZATION EXPLAINER REPORT", {}),
            "fallback_used": localization.get("fallback_used"),
            "localization_attempts": budget_report.get("localization_attempts", 0),
            "execution_authorized": readiness.get("execution_ready") is True,
            "execution_rejected_reason": (
                None
                if readiness.get("execution_ready") is True
                else readiness.get("readiness_state")
            ),
            "localization_duration": budget_report.get("localization_duration", 0.0),
            "fallback_usage": bool(localization.get("fallback_used")),
            "execution_rejections": 0
            if readiness.get("execution_ready") is True
            else 1,
            "retry_count": localization.get("world_model_retry_count", 0),
        }


localization_reporter = LocalizationReporter()


__all__ = [
    "LocalizationReporter",
    "localization_reporter",
]
