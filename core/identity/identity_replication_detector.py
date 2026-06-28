"""Detect lineage-preserving identity replication events."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp


class IdentityReplicationDetector:
    """Classify ARC-style duplication as replication, not identity split."""

    SHAPE_SIMILARITY_THRESHOLD = 0.86

    def detect(self, tracking: Mapping[str, Any] | None) -> dict[str, Any]:
        events = self.detect_events(tracking)
        if not events:
            return {
                "identity_transition": None,
                "source_object": None,
                "replicated_objects": [],
                "replication_confidence": 0.0,
                "replication_events": [],
            }
        best = max(events, key=lambda event: event["replication_confidence"])
        return {
            "identity_transition": "IDENTITY_REPLICATION",
            "source_object": best["source_object"],
            "replicated_objects": best["replicated_objects"],
            "replication_confidence": best["replication_confidence"],
            "replication_events": events,
        }

    def detect_events(self, tracking: Mapping[str, Any] | None) -> list[dict[str, Any]]:
        tracking = tracking if isinstance(tracking, Mapping) else {}
        inputs = self._objects_by_id(tracking.get("input_tracked_objects", []))
        outputs = self._objects_by_id(tracking.get("output_tracked_objects", []))
        descendants: dict[str, list[dict[str, Any]]] = {}
        output_sources: dict[str, set[str]] = {}

        for match in tracking.get("matches", []):
            self._add_descendant(
                descendants,
                output_sources,
                match.get("input_object"),
                match.get("output_object"),
                match.get("identity_continuity", 0.0),
                match,
            )
        for event in tracking.get("added_objects", []):
            self._add_descendant(
                descendants,
                output_sources,
                event.get("source_candidate"),
                event.get("output_object"),
                event.get("confidence", 0.0),
                event,
            )

        events = []
        for source, lineage in sorted(descendants.items()):
            targets = sorted({item["target"] for item in lineage})
            if len(targets) <= 1 or source not in inputs:
                continue
            if any(len(output_sources.get(target, set())) > 1 for target in targets):
                continue

            scores = []
            evidence = []
            for target in targets:
                descendant = outputs.get(target)
                if descendant is None:
                    scores = []
                    break
                preservation = self._preservation_score(inputs[source], descendant)
                if preservation < self.SHAPE_SIMILARITY_THRESHOLD:
                    scores = []
                    break
                lineage_confidence = max(
                    (
                        item["confidence"]
                        for item in lineage
                        if item["target"] == target
                    ),
                    default=0.0,
                )
                scores.append(clamp(preservation * 0.70 + lineage_confidence * 0.30))
                evidence.append({
                    "target": target,
                    "preservation_score": round(preservation, 4),
                    "lineage_confidence": round(lineage_confidence, 4),
                })
            if scores:
                events.append({
                    "identity_transition": "IDENTITY_REPLICATION",
                    "source_object": source,
                    "replicated_objects": targets,
                    "replication_confidence": round(
                        clamp(sum(scores) / len(scores)),
                        4,
                    ),
                    "evidence": evidence,
                })
        return events

    def _objects_by_id(self, objects: Any) -> dict[str, Mapping[str, Any]]:
        return {
            str(obj.get("object_id")): obj
            for obj in list(objects or [])
            if isinstance(obj, Mapping) and obj.get("object_id") is not None
        }

    def _add_descendant(
        self,
        descendants: dict[str, list[dict[str, Any]]],
        output_sources: dict[str, set[str]],
        source: Any,
        target: Any,
        confidence: Any,
        evidence: Mapping[str, Any],
    ) -> None:
        if source is None or target is None:
            return
        source = str(source)
        target = str(target)
        descendants.setdefault(source, []).append({
            "target": target,
            "confidence": clamp(confidence),
            "evidence": dict(evidence),
        })
        output_sources.setdefault(target, set()).add(source)

    def _preservation_score(
        self,
        source: Mapping[str, Any],
        descendant: Mapping[str, Any],
    ) -> float:
        same_color = 1.0 if source.get("color") == descendant.get("color") else 0.0
        same_shape = (
            1.0
            if source.get("canonical_shape_signature") == descendant.get(
                "canonical_shape_signature"
            )
            else 0.0
        )
        same_size = 1.0 if source.get("size") == descendant.get("size") else 0.0
        return clamp(same_color * 0.30 + same_shape * 0.55 + same_size * 0.15)


identity_replication_detector = IdentityReplicationDetector()


__all__ = [
    "IdentityReplicationDetector",
    "identity_replication_detector",
]
