"""Object targeting helpers for transformation localization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from runtime.transformation_localization.localization_metrics import (
    MAX_OBJECT_MATCHES,
    clamp,
)


@dataclass
class LocalizationResult:
    target_objects: list[dict[str, Any]]
    transformation_scope: str
    localization_confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_objects": self.target_objects,
            "transformation_scope": self.transformation_scope,
            "localization_confidence": round(clamp(self.localization_confidence), 4),
        }


class ObjectTargetingEngine:
    def identify(
        self,
        localization: Mapping[str, Any] | None = None,
        synthesized_program: Mapping[str, Any] | None = None,
    ) -> LocalizationResult:
        localization = localization if isinstance(localization, Mapping) else {}
        synthesized_program = (
            synthesized_program if isinstance(synthesized_program, Mapping) else {}
        )
        targets = []
        for report in localization.get("localization_reports", []) or []:
            if not isinstance(report, Mapping):
                continue
            anchor = report.get("anchor_object")
            if anchor:
                targets.append({
                    "object_id": anchor,
                    "role": "anchor",
                    "translation_vector": report.get("relative_offset", [0, 0]),
                    "identity_preserved": bool(report.get("topology_preserved", True)),
                })
            for match in report.get("object_matches", []) or []:
                if not isinstance(match, Mapping):
                    continue
                targets.append({
                    "object_id": match.get("input_object_id"),
                    "target_object_id": match.get("output_object_id"),
                    "role": "matched_object",
                    "translation_vector": match.get("centroid_delta", [0, 0]),
                    "identity_preserved": match.get("topology_preserved") is True,
                    "identity_confidence": clamp(match.get("identity_confidence")),
                })
        if not targets:
            targets = self._targets_from_program(synthesized_program)
        targets = targets[:MAX_OBJECT_MATCHES]
        confidence = 0.85 if targets else 0.0
        scope = "object_level" if targets else "unlocalized"
        return LocalizationResult(targets, scope, confidence)

    def _targets_from_program(
        self,
        synthesized_program: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        targets = []
        for index, step in enumerate(synthesized_program.get("steps", []) or []):
            if not isinstance(step, Mapping):
                continue
            parameters = step.get("parameters", {}) or {}
            if not isinstance(parameters, Mapping):
                parameters = {}
            object_id = (
                parameters.get("source_object")
                or parameters.get("anchor_object")
                or parameters.get("target_object")
            )
            if object_id:
                targets.append({
                    "object_id": object_id,
                    "role": "program_target",
                    "step_index": index,
                    "translation_vector": [
                        int(parameters.get("delta_row", 0) or 0),
                        int(parameters.get("delta_col", 0) or 0),
                    ],
                    "identity_preserved": True,
                })
        return targets


object_targeting_engine = ObjectTargetingEngine()


__all__ = [
    "LocalizationResult",
    "ObjectTargetingEngine",
    "object_targeting_engine",
]
