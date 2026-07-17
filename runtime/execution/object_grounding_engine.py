from __future__ import annotations

from collections import deque
from typing import Any


class ObjectGroundingEngine:
    """Ground executable intent in concrete grid objects and regions."""

    def ground(
        self,
        input_grid: list[list[int]] | None = None,
        *,
        semantic_intent: str | None = None,
        candidate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        grid = self._normalize_grid(input_grid)
        objects = self._connected_objects(grid)
        operation = self._operation_from(candidate, semantic_intent)
        target_objects = self._select_targets(objects, candidate)
        scope = self._scope_for(operation, target_objects, objects)
        regions = {obj["object_id"]: obj["region"] for obj in objects}
        affected_regions = [
            regions[obj["object_id"]]
            for obj in target_objects
            if obj["object_id"] in regions
        ]
        return {
            "target_objects": target_objects,
            "candidate_objects": objects,
            "object_regions": regions,
            "affected_regions": affected_regions,
            "object_hierarchy": self._hierarchy(objects),
            "execution_boundaries": self._execution_boundaries(affected_regions, grid),
            "object_ownership": {
                obj["object_id"]: candidate.get("source", "semantic_execution")
                for obj in target_objects
            } if isinstance(candidate, dict) else {},
            "transformation_scope": scope,
            "identity_lineage": {
                obj["object_id"]: {
                    "source_object": obj["object_id"],
                    "lineage_preserved": True,
                }
                for obj in target_objects
            },
            "object_grounding_confidence": 1.0 if target_objects else 0.0,
            "object_grounding_operational": True,
        }

    def _normalize_grid(self, grid: Any) -> list[list[int]]:
        if not isinstance(grid, list):
            return []
        return [
            [cell for cell in row]
            for row in grid
            if isinstance(row, list)
        ]

    def _connected_objects(self, grid: list[list[int]]) -> list[dict[str, Any]]:
        if not grid:
            return []
        height = len(grid)
        width = max((len(row) for row in grid), default=0)
        seen: set[tuple[int, int]] = set()
        objects: list[dict[str, Any]] = []
        for row_index, row in enumerate(grid):
            for col_index, color in enumerate(row):
                if color == 0 or (row_index, col_index) in seen:
                    continue
                cells: list[list[int]] = []
                queue: deque[tuple[int, int]] = deque([(row_index, col_index)])
                seen.add((row_index, col_index))
                while queue:
                    r, c = queue.popleft()
                    cells.append([r, c])
                    for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                        if (
                            nr < 0
                            or nc < 0
                            or nr >= height
                            or nc >= len(grid[nr])
                            or (nr, nc) in seen
                            or grid[nr][nc] != color
                        ):
                            continue
                        seen.add((nr, nc))
                        queue.append((nr, nc))
                rows = [cell[0] for cell in cells]
                cols = [cell[1] for cell in cells]
                object_id = f"obj_{len(objects) + 1}"
                objects.append({
                    "object_id": object_id,
                    "color": color,
                    "cells": cells,
                    "cell_count": len(cells),
                    "region": {
                        "min_row": min(rows),
                        "max_row": max(rows),
                        "min_col": min(cols),
                        "max_col": max(cols),
                    },
                    "identity": {
                        "identity_id": object_id,
                        "lineage_preserved": True,
                    },
                })
        return objects

    def _operation_from(
        self,
        candidate: dict[str, Any] | None,
        semantic_intent: str | None,
    ) -> str:
        if isinstance(candidate, dict):
            return str(candidate.get("operation") or candidate.get("intent") or semantic_intent or "")
        return str(semantic_intent or "")

    def _select_targets(
        self,
        objects: list[dict[str, Any]],
        candidate: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if not objects:
            return []
        requested = set()
        if isinstance(candidate, dict):
            metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
            for value in (
                candidate.get("target_objects"),
                metadata.get("target_objects"),
                metadata.get("object_ids"),
            ):
                if isinstance(value, list):
                    requested.update(str(item) for item in value)
        if requested:
            selected = [obj for obj in objects if obj["object_id"] in requested]
            if selected:
                return selected
        return [max(objects, key=lambda obj: obj.get("cell_count", 0))]

    def _scope_for(
        self,
        operation: str,
        target_objects: list[dict[str, Any]],
        objects: list[dict[str, Any]],
    ) -> str:
        operation = operation.lower()
        if operation.startswith("global_") or operation in {"preserve_grid", "remap_palette"}:
            return "global"
        if len(target_objects) == len(objects) and len(objects) > 1:
            return "mixed"
        return "local"

    def _hierarchy(self, objects: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "root": "grid",
            "children": [obj["object_id"] for obj in objects],
            "relationships": [
                {
                    "source_object": objects[index]["object_id"],
                    "target_object": objects[index + 1]["object_id"],
                    "relationship": "spatial_peer",
                }
                for index in range(max(0, len(objects) - 1))
            ],
        }

    def _execution_boundaries(
        self,
        regions: list[dict[str, int]],
        grid: list[list[int]],
    ) -> dict[str, int]:
        if not regions:
            return {
                "min_row": 0,
                "max_row": max(0, len(grid) - 1),
                "min_col": 0,
                "max_col": max(0, max((len(row) for row in grid), default=1) - 1),
            }
        return {
            "min_row": min(region["min_row"] for region in regions),
            "max_row": max(region["max_row"] for region in regions),
            "min_col": min(region["min_col"] for region in regions),
            "max_col": max(region["max_col"] for region in regions),
        }


object_grounding_engine = ObjectGroundingEngine()


__all__ = ["ObjectGroundingEngine", "object_grounding_engine"]
