"""In-memory grounding evidence ledger for localization reuse."""

from __future__ import annotations

from typing import Any, Mapping


class GroundingMemory:
    def __init__(self):
        self.successful_localizations: list[dict[str, Any]] = []
        self.failed_localizations: list[dict[str, Any]] = []
        self.object_patterns: list[dict[str, Any]] = []
        self.transformation_patterns: list[dict[str, Any]] = []
        self.grounding_templates: list[dict[str, Any]] = []

    def record(self, report: Mapping[str, Any], success: bool | None = None) -> dict[str, Any]:
        payload = dict(report)
        if success is None:
            success = bool(
                payload.get("target_objects")
                and payload.get("localization_confidence", 0.0) >= 0.60
            )
        if success:
            self.successful_localizations.append(payload)
        else:
            self.failed_localizations.append(payload)
        self.object_patterns.extend(payload.get("target_objects", []) or [])
        self.transformation_patterns.extend(
            payload.get("transformation_targets", []) or []
        )
        template = {
            "operation": payload.get("operation"),
            "transformation_scope": payload.get("transformation_scope"),
            "hint_count": len(payload.get("localization_hints", []) or []),
        }
        if template not in self.grounding_templates:
            self.grounding_templates.append(template)
        return self.report()

    def reuse_hints(self, operation: str | None = None) -> list[dict[str, Any]]:
        operation = str(operation or "").lower()
        hints = []
        for item in reversed(self.successful_localizations[-25:]):
            if operation and str(item.get("operation", "")).lower() != operation:
                continue
            hints.extend(item.get("localization_hints", []) or [])
        return hints[:10]

    def report(self) -> dict[str, Any]:
        return {
            "system": "grounding_memory",
            "successful_localization_count": len(self.successful_localizations),
            "failed_localization_count": len(self.failed_localizations),
            "object_pattern_count": len(self.object_patterns),
            "transformation_pattern_count": len(self.transformation_patterns),
            "grounding_template_count": len(self.grounding_templates),
            "successful_localizations": self.successful_localizations[-25:],
            "failed_localizations": self.failed_localizations[-25:],
            "object_patterns": self.object_patterns[-25:],
            "transformation_patterns": self.transformation_patterns[-25:],
            "grounding_templates": self.grounding_templates[-25:],
        }


grounding_memory = GroundingMemory()


__all__ = ["GroundingMemory", "grounding_memory"]
