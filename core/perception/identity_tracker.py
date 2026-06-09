"""Identity continuity reporting over object tracking output."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp
from core.perception.object_tracker import ObjectTracker


class IdentityTracker:
    """Turn object tracking into explicit identity and lineage evidence."""

    def __init__(
        self,
        object_tracker: ObjectTracker | None = None,
    ) -> None:
        self.object_tracker = object_tracker or ObjectTracker()

    def track_identity(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str = "object_identity_preservation",
    ) -> dict[str, Any]:
        tracking = self.object_tracker.track(input_grid, output_grid)
        split_events = self._split_events(tracking)
        identity_state = self._identity_state(tracking, split_events)
        continuity = clamp(tracking.get("identity_continuity", 0.0))
        lineage_continuity = self._lineage_continuity(tracking, split_events)
        report = {
            "system": "identity_tracker",
            "source": source,
            "identity_state": identity_state,
            "identity_behavior": self._identity_behavior(identity_state),
            "identity_continuity": continuity,
            "lineage_continuity": lineage_continuity,
            "identity_continuity_state": tracking.get(
                "identity_continuity_state",
                "IDENTITY_CONTINUITY_WEAK",
            ),
            "lineage_mappings": self._lineage_mappings(tracking),
            "split_events": split_events,
            "added_objects": tracking.get("added_objects", []),
            "removed_objects": tracking.get("removed_objects", []),
            "changed_objects": tracking.get("changed_objects", []),
            "identity_runtime": tracking.get("identity_runtime", {}),
            "identity_runtime_state": tracking.get("identity_runtime_state"),
            "identity_runtime_confidence": tracking.get(
                "identity_runtime_confidence",
                0.0,
            ),
            "identity_runtime_gates": tracking.get("identity_runtime_gates", {}),
            "tracking": tracking,
        }
        report["dependency_evidence"] = self._dependency_evidence(report)
        return report

    def _identity_state(
        self,
        tracking: Mapping[str, Any],
        split_events: list[dict[str, Any]],
    ) -> str:
        if split_events:
            return "IDENTITY_SPLIT"
        if tracking.get("removed_objects"):
            return "IDENTITY_INTERRUPTED"
        if tracking.get("identity_continuity_state") == "IDENTITY_CONTINUITY_STABLE":
            return "IDENTITY_STABLE"
        if tracking.get("matches"):
            return "IDENTITY_CONTINUITY_PROVISIONAL"
        return "IDENTITY_UNRESOLVED"

    def _identity_behavior(self, identity_state: str) -> str:
        if identity_state == "IDENTITY_SPLIT":
            return "identity_split"
        if identity_state in {
            "IDENTITY_STABLE",
            "IDENTITY_CONTINUITY_PROVISIONAL",
        }:
            return "identity_preserved"
        return "identity_unresolved"

    def _lineage_mappings(
        self,
        tracking: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        mappings = [
            {
                "input_object": match.get("input_object"),
                "output_object": match.get("output_object"),
                "relation": "same_lineage",
                "confidence": clamp(match.get("identity_continuity", 0.0)),
                "identity_state": match.get("identity_state"),
            }
            for match in tracking.get("matches", [])
        ]
        for event in tracking.get("added_objects", []):
            source_candidate = event.get("source_candidate")
            if source_candidate:
                mappings.append({
                    "input_object": source_candidate,
                    "output_object": event.get("output_object"),
                    "relation": "descendant_lineage",
                    "confidence": clamp(event.get("confidence", 0.0)),
                    "identity_state": "identity_descendant_created",
                })
        return mappings

    def _split_events(
        self,
        tracking: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        descendants: dict[str, list[dict[str, Any]]] = {}
        for match in tracking.get("matches", []):
            descendants.setdefault(str(match.get("input_object")), []).append({
                "output_object": match.get("output_object"),
                "confidence": clamp(match.get("identity_continuity", 0.0)),
                "source": "object_match",
            })
        for event in tracking.get("added_objects", []):
            source_candidate = event.get("source_candidate")
            if not source_candidate:
                continue
            descendants.setdefault(str(source_candidate), []).append({
                "output_object": event.get("output_object"),
                "confidence": clamp(event.get("confidence", 0.0)),
                "source": "added_object_source_candidate",
                "placement_vector": event.get("placement_vector", {}),
            })

        split_events = []
        for input_object, outputs in sorted(descendants.items()):
            unique_outputs = {
                str(item.get("output_object"))
                for item in outputs
                if item.get("output_object")
            }
            if len(unique_outputs) <= 1:
                continue
            confidence = sum(item["confidence"] for item in outputs) / len(outputs)
            split_events.append({
                "event": "identity_split",
                "input_object": input_object,
                "output_objects": sorted(unique_outputs),
                "confidence": clamp(confidence),
                "evidence": outputs,
            })
        return split_events

    def _lineage_continuity(
        self,
        tracking: Mapping[str, Any],
        split_events: list[dict[str, Any]],
    ) -> float:
        mapping_count = len(self._lineage_mappings(tracking))
        expected_count = max(
            tracking.get("input_object_count", 0),
            tracking.get("output_object_count", 0),
            1,
        )
        coverage = clamp(mapping_count / expected_count)
        split_bonus = 0.08 if split_events else 0.0
        return clamp(
            tracking.get("identity_continuity", 0.0) * 0.60
            + coverage * 0.32
            + split_bonus
        )

    def _dependency_evidence(
        self,
        report: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        source = str(report.get("source", "object_identity_preservation"))
        dependencies = [
            self._dependency(
                source,
                f"identity_behavior:{report.get('identity_behavior')}",
                report.get("identity_continuity", 0.0),
                "identity_dependency",
                {"identity_state": report.get("identity_state")},
            ),
            self._dependency(
                source,
                "lineage_continuity",
                report.get("lineage_continuity", 0.0),
                "identity_dependency",
                {"lineage_mappings": report.get("lineage_mappings", [])},
            ),
            self._dependency(
                source,
                f"identity_continuity:{report.get('identity_continuity_state')}",
                report.get("identity_continuity", 0.0),
                "identity_dependency",
                {"identity_continuity": report.get("identity_continuity", 0.0)},
            ),
            self._dependency(
                source,
                f"identity_runtime:{report.get('identity_runtime_state')}",
                report.get("identity_runtime_confidence", 0.0),
                "identity_runtime_dependency",
                {
                    "identity_runtime_gates": report.get(
                        "identity_runtime_gates",
                        {},
                    ),
                    "identity_spine_continuity": report.get(
                        "identity_runtime",
                        {},
                    ).get("identity_spine_continuity", 0.0),
                },
            ),
        ]
        for gate, enabled in sorted(report.get("identity_runtime_gates", {}).items()):
            dependencies.append(
                self._dependency(
                    source,
                    f"identity_runtime_gate:{gate}",
                    0.90 if enabled else 0.45,
                    "identity_runtime_dependency",
                    {"gate": gate, "enabled": bool(enabled)},
                )
            )
        if report.get("split_events"):
            dependencies.append(
                self._dependency(
                    source,
                    "identity_split",
                    max(
                        event.get("confidence", 0.0)
                        for event in report.get("split_events", [])
                    ),
                    "identity_dependency",
                    {"split_events": report.get("split_events", [])},
                )
            )
        return dependencies

    def _dependency(
        self,
        source: str,
        target: str,
        confidence: float,
        dependency_type: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "source": source,
            "target": target,
            "relation": "depends_on",
            "confidence": clamp(confidence),
            "dependency_type": dependency_type,
            "required": True,
            "supported": True,
            "transfer_success": True,
            "metadata": metadata,
        }


__all__ = [
    "IdentityTracker",
]
