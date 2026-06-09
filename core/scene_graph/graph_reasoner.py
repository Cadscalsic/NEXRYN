"""Reason over scene graphs to localize placement dependencies."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp
from core.perception import ObjectTracker
from core.scene_graph.scene_graph_builder import SceneGraphBuilder


class GraphReasoner:
    """Convert scene graph observations into placement and dependency evidence."""

    def __init__(
        self,
        scene_graph_builder: SceneGraphBuilder | None = None,
        object_tracker: ObjectTracker | None = None,
    ) -> None:
        self.scene_graph_builder = scene_graph_builder or SceneGraphBuilder()
        self.object_tracker = object_tracker or ObjectTracker()

    def reason_about_scene(self, grid: Any) -> dict[str, Any]:
        graph = self.scene_graph_builder.build(grid)
        evidence = self._relation_dependency_evidence(graph)
        return {
            "system": "graph_reasoner",
            "mode": "scene",
            "scene_graph": graph,
            "dependency_evidence": evidence,
            "dependency_evidence_count": len(evidence),
        }

    def reason_about_placement(
        self,
        input_grid: Any,
        output_grid: Any,
        operation: str = "duplicate_object",
    ) -> dict[str, Any]:
        tracking = self.object_tracker.track(input_grid, output_grid)
        placement_rules = [
            self._placement_rule(event, operation)
            for event in tracking.get("added_objects", [])
            if event.get("placement_vector")
        ]
        dependency_evidence = self._placement_dependency_evidence(
            placement_rules,
            tracking,
        )
        return {
            "system": "graph_reasoner",
            "mode": "placement",
            "operation": operation,
            "tracking": tracking,
            "placement_rules": placement_rules,
            "dependency_evidence": dependency_evidence,
            "dependency_evidence_count": len(dependency_evidence),
            "localized_prediction_ready": bool(placement_rules),
        }

    def explain_localized_mismatch(
        self,
        predicted_grid: Any,
        expected_grid: Any,
    ) -> dict[str, Any]:
        tracking = self.object_tracker.track(predicted_grid, expected_grid)
        mismatch_events = [
            *tracking.get("added_objects", []),
            *tracking.get("removed_objects", []),
            *tracking.get("moved_objects", []),
        ]
        return {
            "system": "graph_reasoner",
            "failure_type": (
                "localized_prediction_mismatch"
                if mismatch_events
                else "position_prediction_aligned"
            ),
            "mismatch_events": mismatch_events,
            "difference_locality": {
                "added": len(tracking.get("added_objects", [])),
                "removed": len(tracking.get("removed_objects", [])),
                "moved": len(tracking.get("moved_objects", [])),
            },
            "tracking": tracking,
        }

    def _placement_rule(
        self,
        event: Mapping[str, Any],
        operation: str,
    ) -> dict[str, Any]:
        vector = dict(event.get("placement_vector", {}))
        return {
            "operation": operation,
            "source_object": event.get("source_candidate"),
            "target_object": event.get("output_object"),
            "placement_vector": vector,
            "direction": vector.get("direction", "unknown"),
            "axis": vector.get("axis", "unknown"),
            "confidence": clamp(event.get("confidence", 0.0)),
            "evidence_event": dict(event),
        }

    def _placement_dependency_evidence(
        self,
        placement_rules: list[Mapping[str, Any]],
        tracking: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        evidence = []
        for rule in placement_rules:
            vector = rule.get("placement_vector", {})
            direction = vector.get("direction", "unknown")
            axis = vector.get("axis", "unknown")
            evidence.append(self._dependency(
                f"operation:{rule.get('operation')}",
                f"placement:{direction}",
                rule.get("confidence", 0.0),
                {"placement_vector": vector, "axis": axis},
            ))
            source = rule.get("source_object")
            if source:
                evidence.append(self._dependency(
                    f"object_lineage:{source}",
                    f"produces:{rule.get('target_object')}",
                    rule.get("confidence", 0.0),
                    {"placement_vector": vector},
                ))
        if tracking.get("localized_change_count", 0):
            evidence.append(self._dependency(
                "localized_change",
                "scene_graph_alignment",
                tracking.get("tracking_confidence", 0.0),
                {"localized_change_count": tracking.get("localized_change_count")},
            ))
        if tracking.get("identity_continuity") is not None:
            evidence.append(self._dependency(
                "object_identity_preservation",
                f"identity_continuity:{tracking.get('identity_continuity_state')}",
                tracking.get("identity_continuity", 0.0),
                {
                    "identity_continuity": tracking.get("identity_continuity"),
                    "identity_changes": tracking.get("identity_changes", []),
                },
            ))
        return evidence

    def _relation_dependency_evidence(
        self,
        graph: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        evidence = []
        for relation, edges in graph.get("relation_index", {}).items():
            confidence = sum(edge.get("confidence", 1.0) for edge in edges)
            confidence = confidence / max(len(edges), 1)
            evidence.append(self._dependency(
                "scene_graph",
                f"relation:{relation}",
                confidence,
                {"edge_count": len(edges)},
            ))
        return evidence

    def _dependency(
        self,
        source: str,
        target: str,
        confidence: float,
        metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "source": source,
            "target": target,
            "confidence": clamp(confidence),
            "supported": True,
            "transfer_success": True,
            "dependency_type": "scene_graph_dependency",
            "metadata": dict(metadata),
        }


__all__ = [
    "GraphReasoner",
]
