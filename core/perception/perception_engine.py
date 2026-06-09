"""Observation-only perception layer for ARC-style grids.

The perception engine converts raw grids into object-centric scene evidence.
It deliberately avoids truth evaluation, governance decisions, promotion,
identity commitments, and causal conclusions. The structures produced here are
descriptive hints for downstream NEXRYN systems to reason over.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

import numpy as np

from core.perception.object_extractor import ObjectExtractor
from core.perception.shape_analyzer import ShapeAnalyzer
from core.perception.spatial_relations import SpatialRelationEngine


Cell = tuple[int, int]
BBox = dict[str, int]


@dataclass(frozen=True)
class PerceivedObject:
    """A connected, same-color component observed in a grid."""

    id: str
    color: int
    cells: list[list[int]]
    size: int
    bbox: BBox
    center: dict[str, float]
    normalized_shape: list[list[int]]
    shape_signature: str
    holes: int
    is_solid: bool
    edge_touching: bool


@dataclass(frozen=True)
class SpatialRelation:
    """A directional or attribute relation observed between two objects."""

    source: str
    relation: str
    target: str
    confidence: float


@dataclass(frozen=True)
class SceneGraph:
    """Compact graph form of perceived objects and their relations."""

    nodes: dict[str, dict[str, Any]]
    edges: list[dict[str, Any]]


class PerceptionEngine:
    """Extract object and relation evidence from ARC-style grids."""

    def __init__(
        self,
        background_color: int = 0,
        connectivity: int = 4,
    ) -> None:
        """Create a perception engine.

        Args:
            background_color: Color ignored during component extraction.
            connectivity: Component connectivity. Accepted values are 4 or 8.
        """

        self.background_color = int(background_color)
        self.connectivity = 8 if connectivity == 8 else 4
        self.shape_analyzer = ShapeAnalyzer()
        self.object_extractor = ObjectExtractor(
            background_color=self.background_color,
            connectivity=self.connectivity,
            shape_analyzer=self.shape_analyzer,
        )
        self.spatial_relation_engine = SpatialRelationEngine()

    def normalize_grid(self, grid: Any) -> list[list[int]]:
        """Return a defensive, rectangular ``list[list[int]]`` grid copy.

        Supports Python lists, ``numpy.ndarray`` instances, and simple ARCGrid
        wrappers exposing ``grid``, ``data``, ``cells``, ``to_list()``, or
        ``tolist()``. Invalid, scalar, ragged, or non-integer inputs return an
        empty grid instead of mutating or raising.
        """

        return self.object_extractor.normalize_grid(grid)

    def extract_objects(self, grid: Any) -> list[dict[str, Any]]:
        """Extract non-background connected components as object dicts."""

        return self.object_extractor.extract_objects(grid)

    def flood_fill(
        self,
        grid: list[list[int]],
        start_row: int,
        start_col: int,
        visited: set[Cell] | None = None,
    ) -> list[Cell]:
        """Collect a same-color connected component from ``start``."""

        return self.object_extractor.flood_fill(
            grid,
            start_row,
            start_col,
            visited,
        )

    def build_object(
        self,
        object_id: str,
        color: int,
        cells: Iterable[Cell],
        height: int,
        width: int,
    ) -> PerceivedObject:
        """Build all object features from component cells."""

        cell_list = sorted((int(row), int(col)) for row, col in cells)
        bbox = self.compute_bbox(cell_list)
        normalized_shape = self.normalize_shape(cell_list)
        rows = [row for row, _ in cell_list]
        cols = [col for _, col in cell_list]

        return PerceivedObject(
            id=object_id,
            color=int(color),
            cells=[[row, col] for row, col in cell_list],
            size=len(cell_list),
            bbox=bbox,
            center={
                "row": sum(rows) / len(rows) if rows else 0.0,
                "col": sum(cols) / len(cols) if cols else 0.0,
            },
            normalized_shape=[[row, col] for row, col in normalized_shape],
            shape_signature=self.compute_shape_signature(normalized_shape),
            holes=self.detect_holes(cell_list),
            is_solid=self.is_solid(cell_list),
            edge_touching=self.touches_edge(cell_list, height, width),
        )

    def compute_bbox(self, cells: Iterable[Cell]) -> BBox:
        """Return the bounding box for cells using inclusive coordinates."""

        return self.shape_analyzer.compute_bbox(cells)

    def normalize_shape(self, cells: Iterable[Cell]) -> list[Cell]:
        """Shift cells so their minimum row and column become zero."""

        return self.shape_analyzer.normalize_shape(cells)

    def compute_shape_signature(self, cells: Iterable[Cell]) -> str:
        """Return a deterministic signature for normalized shape cells."""

        return self.shape_analyzer.shape_signature(cells)

    def detect_holes(self, cells: Iterable[Cell]) -> int:
        """Count enclosed empty components inside an object's bounding box."""

        return self.shape_analyzer.detect_holes(cells)

    def is_solid(self, cells: Iterable[Cell]) -> bool:
        """Return whether the object fully occupies its bounding box."""

        return self.shape_analyzer.is_solid(cells)

    def touches_edge(self, cells: Iterable[Cell], height: int, width: int) -> bool:
        """Return whether any cell touches the grid boundary."""

        return self.shape_analyzer.touches_edge(cells, height, width)

    def compute_relations(
        self,
        objects: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Compute deterministic observed relations between object pairs."""

        return self.spatial_relation_engine.compute_relations(objects)

    def is_touching(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> bool:
        """Return True when objects share a side-adjacent cell pair."""

        source_cells = self._cell_set(source)
        target_cells = self._cell_set(target)
        return any(
            (row + d_row, col + d_col) in target_cells
            for row, col in source_cells
            for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )

    def is_adjacent(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> bool:
        """Return True for diagonal contact or one-cell separation."""

        for source_row, source_col in self._cell_set(source):
            for target_row, target_col in self._cell_set(target):
                d_row = abs(source_row - target_row)
                d_col = abs(source_col - target_col)
                if d_row == 1 and d_col == 1:
                    return True
                if (d_row == 2 and d_col == 0) or (d_row == 0 and d_col == 2):
                    return True
        return False

    def compare_shapes(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> bool:
        """Compare objects by normalized shape signature."""

        return source.get("shape_signature") == target.get("shape_signature")

    def compare_sizes(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> bool:
        """Compare objects by occupied cell count."""

        return int(source.get("size", -1)) == int(target.get("size", -2))

    def compare_colors(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> bool:
        """Compare objects by color."""

        return int(source.get("color", -1)) == int(target.get("color", -2))

    def build_scene_graph(
        self,
        objects: list[Mapping[str, Any]],
        relations: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Build a JSON-serializable scene graph from objects and relations."""

        graph = SceneGraph(
            nodes={
                str(obj["id"]): {
                    "color": obj["color"],
                    "size": obj["size"],
                    "shape_signature": obj["shape_signature"],
                    "center": obj["center"],
                }
                for obj in objects
            },
            edges=[
                {
                    "source": relation["source"],
                    "relation": relation["relation"],
                    "target": relation["target"],
                }
                for relation in relations
            ],
        )
        return asdict(graph)

    def summarize_scene(
        self,
        objects: list[Mapping[str, Any]],
        relations: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Summarize observed scene-level properties."""

        colors = sorted({int(obj["color"]) for obj in objects})
        size_counts = Counter(int(obj["size"]) for obj in objects)
        color_counts = Counter(int(obj["color"]) for obj in objects)
        shape_counts = Counter(str(obj["shape_signature"]) for obj in objects)
        largest = max(objects, key=lambda obj: (obj["size"], obj["id"]), default=None)
        smallest = min(objects, key=lambda obj: (obj["size"], obj["id"]), default=None)

        return {
            "object_count": len(objects),
            "colors_present": colors,
            "largest_object": largest["id"] if largest else None,
            "smallest_object": smallest["id"] if smallest else None,
            "relation_count": len(relations),
            "has_touching_objects": any(
                relation["relation"] == "touching" for relation in relations
            ),
            "has_repeated_shapes": any(count > 1 for count in shape_counts.values()),
            "has_repeated_colors": any(count > 1 for count in color_counts.values()),
            "has_repeated_sizes": any(count > 1 for count in size_counts.values()),
        }

    def compare_scenes(self, input_grid: Any, output_grid: Any) -> dict[str, Any]:
        """Compare two perceived scenes and emit soft transformation hints."""

        input_scene = self.perceive(input_grid)
        output_scene = self.perceive(output_grid)
        input_objects = input_scene["objects"]
        output_objects = output_scene["objects"]
        input_colors = set(input_scene["summary"]["colors_present"])
        output_colors = set(output_scene["summary"]["colors_present"])

        matches = self._match_objects(input_objects, output_objects)
        matched_inputs = {match[0]["id"] for match in matches}
        matched_outputs = {match[1]["id"] for match in matches}

        size_changes: list[dict[str, Any]] = []
        position_changes: list[dict[str, Any]] = []
        shape_changes: list[dict[str, Any]] = []
        hints: set[str] = set()

        if len(output_objects) > len(input_objects):
            hints.add("object_added")
        if len(output_objects) < len(input_objects):
            hints.add("object_removed")

        for source, target in matches:
            if not self.compare_sizes(source, target):
                size_changes.append({
                    "input_object": source["id"],
                    "output_object": target["id"],
                    "from": source["size"],
                    "to": target["size"],
                })
                hints.add("object_resized")

            if source["center"] != target["center"]:
                position_changes.append({
                    "input_object": source["id"],
                    "output_object": target["id"],
                    "from": source["center"],
                    "to": target["center"],
                })
                hints.add("object_moved")

            if self.compare_shapes(source, target):
                hints.add("shape_preserved")
            else:
                shape_changes.append({
                    "input_object": source["id"],
                    "output_object": target["id"],
                    "from": source["shape_signature"],
                    "to": target["shape_signature"],
                })
                hints.add("shape_changed")

            if not self.compare_colors(source, target):
                hints.add("color_changed")

        if self._has_possible_duplication(input_objects, output_objects):
            hints.add("duplication_possible")
        if self._has_possible_symmetry(output_objects):
            hints.add("symmetry_possible")
        if self._topology_changed(input_objects, output_objects):
            hints.add("topology_changed")
        if any(self.compare_shapes(source, target) for source, target in matches):
            hints.add("identity_preserved_possible")

        for source in input_objects:
            if source["id"] not in matched_inputs:
                shape_changes.append({
                    "input_object": source["id"],
                    "output_object": None,
                    "from": source["shape_signature"],
                    "to": None,
                })
        for target in output_objects:
            if target["id"] not in matched_outputs:
                shape_changes.append({
                    "input_object": None,
                    "output_object": target["id"],
                    "from": None,
                    "to": target["shape_signature"],
                })

        return {
            "input_scene": input_scene,
            "output_scene": output_scene,
            "object_count_delta": len(output_objects) - len(input_objects),
            "colors_added": sorted(output_colors - input_colors),
            "colors_removed": sorted(input_colors - output_colors),
            "size_changes": size_changes,
            "position_changes": position_changes,
            "shape_changes": shape_changes,
            "possible_transformations": sorted(hints),
        }

    def perceive(self, grid: Any) -> dict[str, Any]:
        """Perceive a grid as objects, relations, graph, and summary."""

        normalized = self.normalize_grid(grid)
        height = len(normalized)
        width = len(normalized[0]) if normalized else 0
        objects = self.extract_objects(normalized)
        relations = self.compute_relations(objects)
        scene_graph = self.build_scene_graph(objects, relations)
        summary = self.summarize_scene(objects, relations)

        return {
            "system": "perception_engine",
            "height": height,
            "width": width,
            "background_color": self.background_color,
            "objects": objects,
            "relations": relations,
            "scene_graph": scene_graph,
            "summary": summary,
        }

    def _unwrap_grid(self, grid: Any) -> Any:
        if grid is None:
            return None
        for method_name in ("to_list", "tolist"):
            method = getattr(grid, method_name, None)
            if callable(method):
                return method()
        for attr_name in ("grid", "data", "cells"):
            if hasattr(grid, attr_name):
                return getattr(grid, attr_name)
        return grid

    def _neighbors(
        self,
        row: int,
        col: int,
        connectivity: int,
    ) -> tuple[Cell, ...]:
        cardinal = (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        )
        if connectivity == 8:
            return cardinal + (
                (row - 1, col - 1),
                (row - 1, col + 1),
                (row + 1, col - 1),
                (row + 1, col + 1),
            )
        return cardinal

    def _directional_relations(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> list[SpatialRelation]:
        relations: list[SpatialRelation] = []
        source_center = source["center"]
        target_center = target["center"]

        if source_center["col"] < target_center["col"]:
            relations.append(self._relation(source, "left_of", target))
            relations.append(self._relation(target, "right_of", source))
        elif source_center["col"] > target_center["col"]:
            relations.append(self._relation(source, "right_of", target))
            relations.append(self._relation(target, "left_of", source))

        if source_center["row"] < target_center["row"]:
            relations.append(self._relation(source, "above", target))
            relations.append(self._relation(target, "below", source))
        elif source_center["row"] > target_center["row"]:
            relations.append(self._relation(source, "below", target))
            relations.append(self._relation(target, "above", source))

        if self._contains_bbox(source["bbox"], target["bbox"]):
            relations.append(self._relation(source, "contains", target))
            relations.append(self._relation(target, "inside", source))
        elif self._contains_bbox(target["bbox"], source["bbox"]):
            relations.append(self._relation(target, "contains", source))
            relations.append(self._relation(source, "inside", target))

        return relations

    def _symmetric_relations(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> list[SpatialRelation]:
        relations: list[SpatialRelation] = []
        checks = (
            ("touching", self.is_touching(source, target)),
            ("adjacent", self.is_adjacent(source, target)),
            ("same_color", self.compare_colors(source, target)),
            ("same_shape", self.compare_shapes(source, target)),
            ("same_size", self.compare_sizes(source, target)),
            (
                "aligned_row",
                source["center"]["row"] == target["center"]["row"],
            ),
            (
                "aligned_col",
                source["center"]["col"] == target["center"]["col"],
            ),
            (
                "overlaps_bbox",
                self._overlaps_bbox(source["bbox"], target["bbox"]),
            ),
            ("near", self._bbox_gap(source["bbox"], target["bbox"]) <= 2),
        )

        for relation_name, enabled in checks:
            if enabled:
                relations.append(self._relation(source, relation_name, target))
                relations.append(self._relation(target, relation_name, source))

        return relations

    def _relation(
        self,
        source: Mapping[str, Any],
        relation: str,
        target: Mapping[str, Any],
        confidence: float = 1.0,
    ) -> SpatialRelation:
        return SpatialRelation(
            source=str(source["id"]),
            relation=relation,
            target=str(target["id"]),
            confidence=float(confidence),
        )

    def _cell_set(self, obj: Mapping[str, Any]) -> set[Cell]:
        return {(int(row), int(col)) for row, col in obj.get("cells", [])}

    def _contains_bbox(self, outer: BBox, inner: BBox) -> bool:
        if outer == inner:
            return False
        return (
            outer["min_row"] <= inner["min_row"]
            and outer["min_col"] <= inner["min_col"]
            and outer["max_row"] >= inner["max_row"]
            and outer["max_col"] >= inner["max_col"]
        )

    def _overlaps_bbox(self, first: BBox, second: BBox) -> bool:
        return not (
            first["max_row"] < second["min_row"]
            or second["max_row"] < first["min_row"]
            or first["max_col"] < second["min_col"]
            or second["max_col"] < first["min_col"]
        )

    def _bbox_gap(self, first: BBox, second: BBox) -> int:
        row_gap = max(
            second["min_row"] - first["max_row"] - 1,
            first["min_row"] - second["max_row"] - 1,
            0,
        )
        col_gap = max(
            second["min_col"] - first["max_col"] - 1,
            first["min_col"] - second["max_col"] - 1,
            0,
        )
        return max(row_gap, col_gap)

    def _match_objects(
        self,
        input_objects: list[Mapping[str, Any]],
        output_objects: list[Mapping[str, Any]],
    ) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
        matched: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
        used_outputs: set[str] = set()

        for source in input_objects:
            candidates = [
                target
                for target in output_objects
                if target["id"] not in used_outputs
            ]
            if not candidates:
                continue

            target = max(
                candidates,
                key=lambda candidate: self._match_score(source, candidate),
            )
            if self._match_score(source, target) > 0:
                matched.append((source, target))
                used_outputs.add(str(target["id"]))

        return matched

    def _match_score(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> int:
        score = 0
        if self.compare_shapes(source, target):
            score += 4
        if self.compare_colors(source, target):
            score += 3
        if self.compare_sizes(source, target):
            score += 2
        if source["center"] == target["center"]:
            score += 1
        return score

    def _has_possible_duplication(
        self,
        input_objects: list[Mapping[str, Any]],
        output_objects: list[Mapping[str, Any]],
    ) -> bool:
        input_shapes = Counter(obj["shape_signature"] for obj in input_objects)
        output_shapes = Counter(obj["shape_signature"] for obj in output_objects)
        return any(output_shapes[shape] > count for shape, count in input_shapes.items())

    def _has_possible_symmetry(self, objects: list[Mapping[str, Any]]) -> bool:
        by_shape: dict[str, list[Mapping[str, Any]]] = {}
        for obj in objects:
            by_shape.setdefault(str(obj["shape_signature"]), []).append(obj)
        return any(
            len(group) > 1
            and (
                len({obj["center"]["row"] for obj in group}) == 1
                or len({obj["center"]["col"] for obj in group}) == 1
            )
            for group in by_shape.values()
        )

    def _topology_changed(
        self,
        input_objects: list[Mapping[str, Any]],
        output_objects: list[Mapping[str, Any]],
    ) -> bool:
        input_topology = sorted((obj["shape_signature"], obj["holes"]) for obj in input_objects)
        output_topology = sorted((obj["shape_signature"], obj["holes"]) for obj in output_objects)
        return input_topology != output_topology
