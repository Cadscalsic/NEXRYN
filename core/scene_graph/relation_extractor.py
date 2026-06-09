"""Relation extraction over perceived objects."""

from __future__ import annotations

from typing import Any, Mapping

from core.perception import ObjectExtractor, ObjectTracker, SpatialRelationEngine


class RelationExtractor:
    """Extract object relations and change relations from grids."""

    def __init__(
        self,
        object_extractor: ObjectExtractor | None = None,
        spatial_relation_engine: SpatialRelationEngine | None = None,
        object_tracker: ObjectTracker | None = None,
    ) -> None:
        self.object_extractor = object_extractor or ObjectExtractor()
        self.spatial_relation_engine = (
            spatial_relation_engine or SpatialRelationEngine()
        )
        self.object_tracker = object_tracker or ObjectTracker(
            self.object_extractor,
            self.spatial_relation_engine,
        )

    def extract_from_grid(self, grid: Any) -> dict[str, Any]:
        objects = self.object_extractor.extract_objects(grid)
        relations = self.extract_from_objects(objects)
        return {
            "system": "relation_extractor",
            "objects": objects,
            "relations": relations,
            "object_count": len(objects),
            "relation_count": len(relations),
        }

    def extract_from_objects(
        self,
        objects: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        return self.spatial_relation_engine.compute_relations(objects)

    def extract_changes(
        self,
        input_grid: Any,
        output_grid: Any,
    ) -> dict[str, Any]:
        tracking = self.object_tracker.track(input_grid, output_grid)
        return {
            "system": "relation_extractor",
            "mode": "change_relations",
            "tracking": tracking,
            "placement_relations": [
                event
                for event in tracking.get("lineage_events", [])
                if event.get("placement_vector")
            ],
        }


__all__ = [
    "RelationExtractor",
]
