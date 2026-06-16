"""Passive spatial relation analysis for ARC-style objects.

The engine accepts object dictionaries from the perception object extractor or
hand-authored ARC object records. It only reports spatial facts; it does not
promote truth, mutate concepts, or alter runtime state.
"""

from __future__ import annotations

from math import sqrt
from typing import Any, Iterable, Mapping, Sequence


Cell = tuple[int, int]
BBox = dict[str, int]
SpatialObject = dict[str, Any]


def normalize_object(obj: Mapping[str, Any], fallback_id: str | None = None) -> SpatialObject:
    """Return a stable object dict with cells, bbox, center, area, and id."""
    cells = _normalize_cells(obj.get("cells", []))
    bbox = object_bbox(obj) if obj.get("bbox") or cells else _empty_bbox()
    center = object_center({**dict(obj), "cells": cells, "bbox": bbox})
    normalized = dict(obj)
    normalized["id"] = str(obj.get("id", fallback_id or "object"))
    normalized["cells"] = cells
    normalized["bbox"] = bbox
    normalized["center"] = center
    normalized["area"] = int(obj.get("area", obj.get("size", len(cells))))
    return normalized


def object_center(obj: Mapping[str, Any]) -> list[float]:
    """Compute or normalize an object center as ``[row, col]``."""
    center = obj.get("center")
    if isinstance(center, Mapping):
        if "row" in center and "col" in center:
            return [round(float(center["row"]), 4), round(float(center["col"]), 4)]
    if isinstance(center, Sequence) and not isinstance(center, (str, bytes)):
        if len(center) >= 2:
            return [round(float(center[0]), 4), round(float(center[1]), 4)]

    cells = _normalize_cells(obj.get("cells", []))
    if cells:
        return [
            round(sum(row for row, _ in cells) / len(cells), 4),
            round(sum(col for _, col in cells) / len(cells), 4),
        ]

    bbox = obj.get("bbox", {})
    if bbox:
        return [
            round((float(bbox["min_row"]) + float(bbox["max_row"])) / 2.0, 4),
            round((float(bbox["min_col"]) + float(bbox["max_col"])) / 2.0, 4),
        ]
    return [0.0, 0.0]


def object_bbox(obj: Mapping[str, Any]) -> BBox:
    """Compute or normalize an inclusive ARC bounding box."""
    bbox = obj.get("bbox")
    if isinstance(bbox, Mapping) and {
        "min_row",
        "max_row",
        "min_col",
        "max_col",
    }.issubset(bbox):
        min_row = int(bbox["min_row"])
        max_row = int(bbox["max_row"])
        min_col = int(bbox["min_col"])
        max_col = int(bbox["max_col"])
    else:
        cells = _normalize_cells(obj.get("cells", []))
        if not cells:
            return _empty_bbox()
        min_row = min(row for row, _ in cells)
        max_row = max(row for row, _ in cells)
        min_col = min(col for _, col in cells)
        max_col = max(col for _, col in cells)

    return {
        "min_row": min_row,
        "max_row": max_row,
        "min_col": min_col,
        "max_col": max_col,
        "height": max_row - min_row + 1,
        "width": max_col - min_col + 1,
    }


def manhattan_distance(first: Sequence[float], second: Sequence[float]) -> float:
    return round(abs(float(first[0]) - float(second[0])) + abs(float(first[1]) - float(second[1])), 4)


def euclidean_distance(first: Sequence[float], second: Sequence[float]) -> float:
    delta_row = float(first[0]) - float(second[0])
    delta_col = float(first[1]) - float(second[1])
    return round(sqrt(delta_row * delta_row + delta_col * delta_col), 4)


def boxes_overlap(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    """Return true when inclusive bounding boxes share at least one cell."""
    return not (
        int(first["max_row"]) < int(second["min_row"])
        or int(second["max_row"]) < int(first["min_row"])
        or int(first["max_col"]) < int(second["min_col"])
        or int(second["max_col"]) < int(first["min_col"])
    )


def boxes_touch(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    """Return true when boxes are cardinally adjacent without overlapping."""
    if boxes_overlap(first, second):
        return False
    row_overlap = _ranges_overlap(
        int(first["min_row"]),
        int(first["max_row"]),
        int(second["min_row"]),
        int(second["max_row"]),
    )
    col_overlap = _ranges_overlap(
        int(first["min_col"]),
        int(first["max_col"]),
        int(second["min_col"]),
        int(second["max_col"]),
    )
    vertical_touch = (
        int(first["max_row"]) + 1 == int(second["min_row"])
        or int(second["max_row"]) + 1 == int(first["min_row"])
    ) and col_overlap
    horizontal_touch = (
        int(first["max_col"]) + 1 == int(second["min_col"])
        or int(second["max_col"]) + 1 == int(first["min_col"])
    ) and row_overlap
    return vertical_touch or horizontal_touch


class SpatialRelationsEngine:
    """Extract deterministic spatial relation reports from ARC objects."""

    system_name = "spatial_relations_engine"

    def analyze_grid(
        self,
        grid: Any,
        object_extractor: Any | None = None,
    ) -> dict[str, Any]:
        """Extract ARC objects with the existing perception layer, then analyze them."""
        if object_extractor is None:
            from core.perception import ObjectExtractor

            object_extractor = ObjectExtractor()
        return self.analyze(object_extractor.extract_objects(grid))

    def analyze(self, objects: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        normalized = [
            normalize_object(obj, fallback_id=f"object_{index + 1}")
            for index, obj in enumerate(objects)
        ]
        relations: list[dict[str, Any]] = []
        for source_index, source in enumerate(normalized):
            for target_index, target in enumerate(normalized):
                if source_index == target_index:
                    continue
                relations.extend(self.relation_between(source, target))

        return {
            "system": self.system_name,
            "objects_analyzed": len(normalized),
            "relations": relations,
            "spatial_signature": self.build_spatial_signature(normalized),
        }

    def relation_between(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        source_obj = normalize_object(source)
        target_obj = normalize_object(target)
        source_bbox = source_obj["bbox"]
        target_bbox = target_obj["bbox"]
        source_center = source_obj["center"]
        target_center = target_obj["center"]
        relations: list[dict[str, Any]] = []

        directional = self._directional_relations(source_obj, target_obj)
        for relation in directional:
            relations.append(self._relation(source_obj, target_obj, relation))

        if boxes_overlap(source_bbox, target_bbox):
            relations.append(self._relation(source_obj, target_obj, "overlaps"))
        if self.detect_adjacency(source_obj, target_obj)["touches"]:
            relations.append(self._relation(source_obj, target_obj, "touches"))
        if self.detect_adjacency(source_obj, target_obj)["adjacent_to"]:
            relations.append(self._relation(source_obj, target_obj, "adjacent_to"))
        if self._contains_bbox(source_bbox, target_bbox):
            relations.append(self._relation(source_obj, target_obj, "contains"))
            relations.append(self._relation(source_obj, target_obj, "surrounds"))
        if self._contains_bbox(target_bbox, source_bbox):
            relations.append(self._relation(source_obj, target_obj, "inside"))
        if source_center == target_center:
            relations.append(self._relation(source_obj, target_obj, "same_position"))

        alignment = self._alignment_between(source_obj, target_obj)
        if alignment["aligned_row"]:
            relations.append(self._relation(source_obj, target_obj, "aligned_row"))
        if alignment["aligned_column"]:
            relations.append(self._relation(source_obj, target_obj, "aligned_column"))

        shifted = self._shifted_by(source_obj, target_obj)
        if shifted is not None:
            relations.append(
                self._relation(
                    source_obj,
                    target_obj,
                    "shifted_by",
                    evidence={"shift": shifted},
                )
            )

        relations.extend(
            [
                self._relation(
                    source_obj,
                    target_obj,
                    "distance_between",
                    evidence=self.compute_distance(source_obj, target_obj),
                ),
                self._relation(
                    source_obj,
                    target_obj,
                    "relative_position",
                    evidence={"relative_position": self._relative_position(source_center, target_center)},
                ),
                self._relation(
                    source_obj,
                    target_obj,
                    "bounding_box_relation",
                    evidence=self.bounding_box_relation(source_obj, target_obj),
                ),
                self._relation(
                    source_obj,
                    target_obj,
                    "center_relation",
                    evidence=self._center_relation(source_obj, target_obj),
                ),
                self._relation(
                    source_obj,
                    target_obj,
                    "direction_vector",
                    evidence=self.compute_direction_vector(source_obj, target_obj),
                ),
            ]
        )
        return relations

    def compute_direction_vector(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> dict[str, Any]:
        source_center = object_center(source)
        target_center = object_center(target)
        delta_row = round(target_center[0] - source_center[0], 4)
        delta_col = round(target_center[1] - source_center[1], 4)
        return {
            "delta_row": delta_row,
            "delta_col": delta_col,
            "axis": self._axis(delta_row, delta_col),
            "direction": self._direction_name(delta_row, delta_col),
        }

    def compute_distance(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> dict[str, Any]:
        source_center = object_center(source)
        target_center = object_center(target)
        return {
            "manhattan": manhattan_distance(source_center, target_center),
            "euclidean": euclidean_distance(source_center, target_center),
        }

    def bounding_box_relation(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> dict[str, Any]:
        source_bbox = object_bbox(source)
        target_bbox = object_bbox(target)
        relation = "disjoint"
        if source_bbox == target_bbox:
            relation = "same_bbox"
        elif self._contains_bbox(source_bbox, target_bbox):
            relation = "contains"
        elif self._contains_bbox(target_bbox, source_bbox):
            relation = "inside"
        elif boxes_overlap(source_bbox, target_bbox):
            relation = "overlaps"
        elif boxes_touch(source_bbox, target_bbox):
            relation = "touches"
        return {
            "relation": relation,
            "source_bbox": dict(source_bbox),
            "target_bbox": dict(target_bbox),
        }

    def detect_alignment(self, objects: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        normalized = [
            normalize_object(obj, fallback_id=f"object_{index + 1}")
            for index, obj in enumerate(objects)
        ]
        patterns: list[dict[str, Any]] = []
        for index, source in enumerate(normalized):
            for target in normalized[index + 1 :]:
                alignment = self._alignment_between(source, target)
                if alignment["aligned_row"]:
                    patterns.append(
                        {
                            "relation": "aligned_row",
                            "objects": [source["id"], target["id"]],
                            "row": source["center"][0],
                        }
                    )
                if alignment["aligned_column"]:
                    patterns.append(
                        {
                            "relation": "aligned_column",
                            "objects": [source["id"], target["id"]],
                            "col": source["center"][1],
                        }
                    )
        return patterns

    def detect_adjacency(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> dict[str, bool]:
        source_obj = normalize_object(source)
        target_obj = normalize_object(target)
        source_cells = set(source_obj["cells"])
        target_cells = set(target_obj["cells"])
        touches = bool(source_cells and target_cells and self._cells_touch(source_cells, target_cells))
        if not touches:
            touches = boxes_touch(source_obj["bbox"], target_obj["bbox"])
        adjacent = touches or self._cells_diagonal_or_one_gap(source_cells, target_cells)
        return {"touches": touches, "adjacent_to": adjacent}

    def build_spatial_signature(self, objects: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        normalized = [
            normalize_object(obj, fallback_id=f"object_{index + 1}")
            for index, obj in enumerate(objects)
        ]
        relative_layout = []
        for index, source in enumerate(normalized):
            for target in normalized[index + 1 :]:
                vector = self.compute_direction_vector(source, target)
                relative_layout.append(
                    {
                        "source": source["id"],
                        "target": target["id"],
                        "relative_position": self._relative_position(source["center"], target["center"]),
                        "direction": vector["direction"],
                        "delta_row": vector["delta_row"],
                        "delta_col": vector["delta_col"],
                    }
                )
        return {
            "object_count": len(normalized),
            "alignment_patterns": self.detect_alignment(normalized),
            "relative_layout": relative_layout,
        }

    def _relation(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
        relation: str,
        evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        base_evidence: dict[str, Any] = {
            "source_bbox": dict(source["bbox"]),
            "target_bbox": dict(target["bbox"]),
            "source_center": list(source["center"]),
            "target_center": list(target["center"]),
        }
        if evidence:
            base_evidence.update(dict(evidence))
        return {
            "source": source["id"],
            "target": target["id"],
            "relation": relation,
            "confidence": 1.0,
            "evidence": base_evidence,
        }

    def _directional_relations(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> list[str]:
        source_bbox = source["bbox"]
        target_bbox = target["bbox"]
        relations: list[str] = []
        if source_bbox["max_col"] < target_bbox["min_col"]:
            relations.append("left_of")
        elif source_bbox["min_col"] > target_bbox["max_col"]:
            relations.append("right_of")
        if source_bbox["max_row"] < target_bbox["min_row"]:
            relations.append("above")
        elif source_bbox["min_row"] > target_bbox["max_row"]:
            relations.append("below")
        return relations

    def _alignment_between(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> dict[str, bool]:
        return {
            "aligned_row": source["center"][0] == target["center"][0],
            "aligned_column": source["center"][1] == target["center"][1],
        }

    def _shifted_by(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> dict[str, float] | None:
        vector = self.compute_direction_vector(source, target)
        if vector["delta_row"] == 0 and vector["delta_col"] == 0:
            return None
        if self._normalized_shape(source["cells"]) == self._normalized_shape(target["cells"]):
            return {"delta_row": vector["delta_row"], "delta_col": vector["delta_col"]}
        source_bbox = source["bbox"]
        target_bbox = target["bbox"]
        if (
            source_bbox["height"] == target_bbox["height"]
            and source_bbox["width"] == target_bbox["width"]
            and source.get("area") == target.get("area")
        ):
            return {"delta_row": vector["delta_row"], "delta_col": vector["delta_col"]}
        return None

    def _relative_position(self, source_center: Sequence[float], target_center: Sequence[float]) -> str:
        delta_row = round(float(target_center[0]) - float(source_center[0]), 4)
        delta_col = round(float(target_center[1]) - float(source_center[1]), 4)
        return self._direction_name(delta_row, delta_col)

    def _center_relation(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> dict[str, Any]:
        vector = self.compute_direction_vector(source, target)
        return {
            "source_center": list(object_center(source)),
            "target_center": list(object_center(target)),
            **vector,
        }

    def _contains_bbox(self, outer: Mapping[str, Any], inner: Mapping[str, Any]) -> bool:
        if dict(outer) == dict(inner):
            return False
        return (
            int(outer["min_row"]) <= int(inner["min_row"])
            and int(outer["min_col"]) <= int(inner["min_col"])
            and int(outer["max_row"]) >= int(inner["max_row"])
            and int(outer["max_col"]) >= int(inner["max_col"])
        )

    def _cells_touch(self, source_cells: set[Cell], target_cells: set[Cell]) -> bool:
        return any(
            (row + d_row, col + d_col) in target_cells
            for row, col in source_cells
            for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )

    def _cells_diagonal_or_one_gap(self, source_cells: set[Cell], target_cells: set[Cell]) -> bool:
        if not source_cells or not target_cells:
            return False
        for source_row, source_col in source_cells:
            for target_row, target_col in target_cells:
                d_row = abs(source_row - target_row)
                d_col = abs(source_col - target_col)
                if max(d_row, d_col) == 1:
                    return True
                if (d_row == 2 and d_col == 0) or (d_row == 0 and d_col == 2):
                    return True
        return False

    def _normalized_shape(self, cells: Iterable[Cell]) -> tuple[Cell, ...]:
        cell_list = list(cells)
        if not cell_list:
            return ()
        min_row = min(row for row, _ in cell_list)
        min_col = min(col for _, col in cell_list)
        return tuple(sorted((row - min_row, col - min_col) for row, col in cell_list))

    def _axis(self, delta_row: float, delta_col: float) -> str:
        if delta_row == 0 and delta_col == 0:
            return "same_position"
        if delta_row == 0:
            return "horizontal"
        if delta_col == 0:
            return "vertical"
        return "diagonal"

    def _direction_name(self, delta_row: float, delta_col: float) -> str:
        vertical = "below" if delta_row > 0 else "above" if delta_row < 0 else ""
        horizontal = "right" if delta_col > 0 else "left" if delta_col < 0 else ""
        return "_".join(part for part in (vertical, horizontal) if part) or "same"


def _normalize_cells(cells: Iterable[Any]) -> list[Cell]:
    normalized: list[Cell] = []
    for cell in cells or []:
        if isinstance(cell, Sequence) and not isinstance(cell, (str, bytes)) and len(cell) >= 2:
            normalized.append((int(cell[0]), int(cell[1])))
    return sorted(normalized)


def _empty_bbox() -> BBox:
    return {
        "min_row": 0,
        "max_row": 0,
        "min_col": 0,
        "max_col": 0,
        "height": 1,
        "width": 1,
    }


def _ranges_overlap(first_min: int, first_max: int, second_min: int, second_max: int) -> bool:
    return first_min <= second_max and second_min <= first_max


__all__ = [
    "SpatialRelationsEngine",
    "normalize_object",
    "object_center",
    "object_bbox",
    "manhattan_distance",
    "euclidean_distance",
    "boxes_touch",
    "boxes_overlap",
]
