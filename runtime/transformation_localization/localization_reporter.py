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
            readiness.get("sandbox_execution_authorized") is True,
            "target_objects": localization.get("target_objects", []),
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
