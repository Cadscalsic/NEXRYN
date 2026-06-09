"""Object extraction for ARC-style grids."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from core.perception.shape_analyzer import ShapeAnalyzer


Cell = tuple[int, int]


@dataclass(frozen=True)
class ExtractedObject:
    id: str
    color: int
    cells: list[list[int]]
    size: int
    bbox: dict[str, int]
    center: dict[str, float]
    normalized_shape: list[list[int]]
    shape_signature: str
    canonical_shape_signature: str
    holes: int
    is_solid: bool
    edge_touching: bool
    shape_analysis: dict


class ObjectExtractor:
    """Extract connected same-color objects from a grid."""

    def __init__(
        self,
        background_color: int = 0,
        connectivity: int = 4,
        shape_analyzer: ShapeAnalyzer | None = None,
    ) -> None:
        self.background_color = int(background_color)
        self.connectivity = 8 if connectivity == 8 else 4
        self.shape_analyzer = shape_analyzer or ShapeAnalyzer()

    def normalize_grid(self, grid: Any) -> list[list[int]]:
        source = self._unwrap_grid(grid)
        if source is None:
            return []
        try:
            if isinstance(source, np.ndarray):
                if source.ndim != 2:
                    return []
                rows = source.tolist()
            else:
                rows = list(source)
        except TypeError:
            return []

        if not rows:
            return []

        normalized: list[list[int]] = []
        expected_width: int | None = None
        for row in rows:
            values = row.tolist() if isinstance(row, np.ndarray) else list(row)
            if expected_width is None:
                expected_width = len(values)
                if expected_width == 0:
                    return []
            elif len(values) != expected_width:
                return []
            try:
                normalized.append([int(value) for value in values])
            except (TypeError, ValueError):
                return []
        return normalized

    def extract_objects(self, grid: Any) -> list[dict]:
        normalized = self.normalize_grid(grid)
        if not normalized:
            return []

        height = len(normalized)
        width = len(normalized[0])
        visited: set[Cell] = set()
        objects: list[ExtractedObject] = []

        for row in range(height):
            for col in range(width):
                if (row, col) in visited:
                    continue
                color = normalized[row][col]
                if color == self.background_color:
                    visited.add((row, col))
                    continue
                cells = self.flood_fill(normalized, row, col, visited)
                objects.append(
                    self._build_object(
                        object_id=f"obj_{len(objects) + 1}",
                        color=color,
                        cells=cells,
                        height=height,
                        width=width,
                    )
                )

        return [asdict(obj) for obj in objects]

    def flood_fill(
        self,
        grid: list[list[int]],
        start_row: int,
        start_col: int,
        visited: set[Cell] | None = None,
    ) -> list[Cell]:
        if not grid:
            return []

        height = len(grid)
        width = len(grid[0])
        if not (0 <= start_row < height and 0 <= start_col < width):
            return []

        seen = visited if visited is not None else set()
        target_color = grid[start_row][start_col]
        queue: deque[Cell] = deque([(start_row, start_col)])
        component: list[Cell] = []

        while queue:
            row, col = queue.popleft()
            if (row, col) in seen:
                continue
            if not (0 <= row < height and 0 <= col < width):
                continue
            if grid[row][col] != target_color:
                continue
            seen.add((row, col))
            component.append((row, col))
            for neighbor in self._neighbors(row, col):
                if neighbor not in seen:
                    queue.append(neighbor)

        return sorted(component)

    def _build_object(
        self,
        object_id: str,
        color: int,
        cells: list[Cell],
        height: int,
        width: int,
    ) -> ExtractedObject:
        analysis = self.shape_analyzer.analyze(cells, height, width)
        return ExtractedObject(
            id=object_id,
            color=int(color),
            cells=[[row, col] for row, col in cells],
            size=analysis["size"],
            bbox=analysis["bbox"],
            center=analysis["center"],
            normalized_shape=analysis["normalized_shape"],
            shape_signature=analysis["shape_signature"],
            canonical_shape_signature=analysis["canonical_shape_signature"],
            holes=analysis["holes"],
            is_solid=analysis["is_solid"],
            edge_touching=analysis["edge_touching"],
            shape_analysis=analysis,
        )

    def _neighbors(self, row: int, col: int) -> tuple[Cell, ...]:
        cardinal = (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        )
        if self.connectivity == 8:
            return cardinal + (
                (row - 1, col - 1),
                (row - 1, col + 1),
                (row + 1, col - 1),
                (row + 1, col + 1),
            )
        return cardinal

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


__all__ = [
    "ExtractedObject",
    "ObjectExtractor",
]
