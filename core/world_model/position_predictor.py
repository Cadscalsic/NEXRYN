"""Position-aware prediction for object-centric transformations."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from core.epistemic_models import clamp
from core.perception import ObjectExtractor, SceneGraphEngine, SpatialRelationEngine


class PositionPredictor:
    """Predict where object-level operations should apply in a grid."""

    def __init__(
        self,
        scene_graph_engine: SceneGraphEngine | None = None,
        object_extractor: ObjectExtractor | None = None,
        spatial_relation_engine: SpatialRelationEngine | None = None,
    ) -> None:
        self.scene_graph_engine = scene_graph_engine or SceneGraphEngine()
        self.object_extractor = object_extractor or ObjectExtractor()
        self.spatial_relation_engine = (
            spatial_relation_engine or SpatialRelationEngine()
        )

    def learn_position_rule(
        self,
        input_grid: Any,
        output_grid: Any | None = None,
        scene_graph_comparison: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        comparison = (
            dict(scene_graph_comparison)
            if isinstance(scene_graph_comparison, Mapping)
            else self.scene_graph_engine.compare_scene_graphs(input_grid, output_grid)
            if output_grid is not None
            else {}
        )
        added_events = [
            event
            for event in comparison.get("object_events", [])
            if event.get("event") == "object_added"
            and event.get("placement_vector")
        ]
        split_events = [
            event
            for event in comparison.get("object_events", [])
            if event.get("event") == "object_split_possible"
            and event.get("placement_vectors")
        ]

        if added_events:
            event = max(added_events, key=lambda item: item.get("confidence", 0.0))
            return {
                "system": "position_predictor",
                "rule_state": "POSITION_RULE_LEARNED",
                "operation": "duplicate_object",
                "source_object": event.get("source_candidate"),
                "placement_vector": event["placement_vector"],
                "confidence": clamp(event.get("confidence", 0.82)),
                "evidence_event": event,
            }
        if split_events:
            event = max(split_events, key=lambda item: item.get("confidence", 0.0))
            vector = event["placement_vectors"][-1]
            return {
                "system": "position_predictor",
                "rule_state": "POSITION_RULE_LEARNED",
                "operation": "duplicate_object",
                "source_object": event.get("input_object"),
                "placement_vector": vector,
                "confidence": clamp(event.get("confidence", 0.78)),
                "evidence_event": event,
            }
        return {
            "system": "position_predictor",
            "rule_state": "POSITION_RULE_MISSING",
            "operation": None,
            "source_object": None,
            "placement_vector": {},
            "confidence": 0.0,
            "evidence_event": {},
        }

    def predict_positioned_operation(
        self,
        input_grid: Any,
        operation: str,
        position_rule: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = self.object_extractor.normalize_grid(input_grid)
        objects = self.object_extractor.extract_objects(normalized)
        if operation != "duplicate_object":
            return {
                "system": "position_predictor",
                "operation": operation,
                "prediction_state": "UNSUPPORTED_POSITION_OPERATION",
                "predicted_grid": normalized,
                "confidence": 0.0,
            }

        rule = dict(position_rule or {})
        source = self._source_object(objects, rule)
        vector = rule.get("placement_vector", {})
        if not source or not vector:
            source = objects[0] if objects else None
            vector = {"delta_row": 0, "delta_col": self._default_horizontal_gap(source)}

        if not source:
            return {
                "system": "position_predictor",
                "operation": operation,
                "prediction_state": "NO_SOURCE_OBJECT",
                "predicted_grid": normalized,
                "confidence": 0.0,
            }

        predicted_grid = self._place_duplicate(
            normalized,
            source,
            int(round(float(vector.get("delta_row", 0)))),
            int(round(float(vector.get("delta_col", 0)))),
        )
        return {
            "system": "position_predictor",
            "operation": operation,
            "prediction_state": "POSITION_PREDICTED",
            "source_object": source["id"],
            "placement_vector": {
                "delta_row": int(round(float(vector.get("delta_row", 0)))),
                "delta_col": int(round(float(vector.get("delta_col", 0)))),
                "axis": vector.get("axis", "unknown"),
                "direction": vector.get("direction", "unknown"),
            },
            "predicted_grid": predicted_grid,
            "confidence": clamp(rule.get("confidence", 0.72)),
        }

    def diagnose_position_mismatch(
        self,
        predicted_grid: Any,
        expected_grid: Any,
    ) -> dict[str, Any]:
        predicted = self.object_extractor.normalize_grid(predicted_grid)
        expected = self.object_extractor.normalize_grid(expected_grid)
        predicted_scene = self.scene_graph_engine.build_scene_graph(predicted)
        expected_scene = self.scene_graph_engine.build_scene_graph(expected)
        predicted_objects = predicted_scene.get("nodes", {})
        expected_objects = expected_scene.get("nodes", {})
        matches = self.scene_graph_engine._match_nodes(  # intentional local reuse
            predicted_objects,
            expected_objects,
        )
        misplaced = [
            match
            for match in matches
            if match.get("shape_preserved")
            and not match.get("position_preserved")
        ]
        difference_count = self._difference_count(predicted, expected)
        return {
            "system": "position_predictor",
            "failure_type": (
                "localized_prediction_mismatch"
                if misplaced or difference_count
                else "position_prediction_aligned"
            ),
            "difference_count": difference_count,
            "object_match_count": len(matches),
            "misplaced_objects": misplaced,
            "predicted_object_count": predicted_scene["summary"]["object_count"],
            "expected_object_count": expected_scene["summary"]["object_count"],
        }

    def _source_object(
        self,
        objects: list[Mapping[str, Any]],
        rule: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        source_id = rule.get("source_object")
        for obj in objects:
            if obj.get("id") == source_id:
                return obj
        return objects[0] if objects else None

    def _default_horizontal_gap(self, source: Mapping[str, Any] | None) -> int:
        if not source:
            return 1
        return int(source.get("bbox", {}).get("width", 1)) + 1

    def _place_duplicate(
        self,
        grid: list[list[int]],
        source: Mapping[str, Any],
        delta_row: int,
        delta_col: int,
    ) -> list[list[int]]:
        if not grid:
            return []
        predicted = deepcopy(grid)
        height = len(predicted)
        width = len(predicted[0])
        color = int(source.get("color", 1))
        for row, col in source.get("cells", []):
            target_row = int(row) + delta_row
            target_col = int(col) + delta_col
            if 0 <= target_row < height and 0 <= target_col < width:
                predicted[target_row][target_col] = color
        return predicted

    def _difference_count(
        self,
        predicted: list[list[int]],
        expected: list[list[int]],
    ) -> int:
        height = max(len(predicted), len(expected))
        width = max(
            max((len(row) for row in predicted), default=0),
            max((len(row) for row in expected), default=0),
        )
        differences = 0
        for row in range(height):
            for col in range(width):
                left = predicted[row][col] if row < len(predicted) and col < len(predicted[row]) else None
                right = expected[row][col] if row < len(expected) and col < len(expected[row]) else None
                if left != right:
                    differences += 1
        return differences


__all__ = [
    "PositionPredictor",
]
