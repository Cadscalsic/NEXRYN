"""Shape-level analysis for ARC-style perceived objects."""

from __future__ import annotations

from collections import deque
from typing import Iterable


Cell = tuple[int, int]
BBox = dict[str, int]


class ShapeAnalyzer:
    """Compute translation-stable shape features for object cells."""

    def compute_bbox(self, cells: Iterable[Cell]) -> BBox:
        cell_list = list(cells)
        if not cell_list:
            return {
                "min_row": 0,
                "min_col": 0,
                "max_row": 0,
                "max_col": 0,
                "height": 0,
                "width": 0,
            }

        rows = [row for row, _ in cell_list]
        cols = [col for _, col in cell_list]
        min_row = min(rows)
        max_row = max(rows)
        min_col = min(cols)
        max_col = max(cols)
        return {
            "min_row": min_row,
            "min_col": min_col,
            "max_row": max_row,
            "max_col": max_col,
            "height": max_row - min_row + 1,
            "width": max_col - min_col + 1,
        }

    def normalize_shape(self, cells: Iterable[Cell]) -> list[Cell]:
        cell_list = list(cells)
        if not cell_list:
            return []
        min_row = min(row for row, _ in cell_list)
        min_col = min(col for _, col in cell_list)
        return sorted((row - min_row, col - min_col) for row, col in cell_list)

    def shape_signature(self, cells: Iterable[Cell]) -> str:
        normalized = sorted((int(row), int(col)) for row, col in cells)
        return "|".join(f"{row},{col}" for row, col in normalized)

    def canonical_signature(self, cells: Iterable[Cell]) -> str:
        normalized = self.normalize_shape(cells)
        variants = [
            self.normalize_shape(transform)
            for transform in self._shape_transforms(normalized)
        ]
        signatures = [self.shape_signature(variant) for variant in variants]
        return min(signatures) if signatures else ""

    def detect_holes(self, cells: Iterable[Cell]) -> int:
        cell_list = list(cells)
        if not cell_list:
            return 0

        bbox = self.compute_bbox(cell_list)
        occupied = set(self.normalize_shape(cell_list))
        height = bbox["height"]
        width = bbox["width"]
        visited: set[Cell] = set()
        holes = 0

        for row in range(height):
            for col in range(width):
                if (row, col) in occupied or (row, col) in visited:
                    continue

                queue: deque[Cell] = deque([(row, col)])
                component: set[Cell] = set()
                touches_boundary = False

                while queue:
                    current = queue.popleft()
                    if current in visited or current in occupied:
                        continue
                    current_row, current_col = current
                    if not (0 <= current_row < height and 0 <= current_col < width):
                        continue

                    visited.add(current)
                    component.add(current)
                    if (
                        current_row in {0, height - 1}
                        or current_col in {0, width - 1}
                    ):
                        touches_boundary = True
                    for neighbor in self._neighbors(current_row, current_col):
                        queue.append(neighbor)

                if component and not touches_boundary:
                    holes += 1

        return holes

    def is_solid(self, cells: Iterable[Cell]) -> bool:
        cell_list = list(cells)
        if not cell_list:
            return False
        bbox = self.compute_bbox(cell_list)
        return len(cell_list) == bbox["height"] * bbox["width"]

    def analyze(
        self,
        cells: Iterable[Cell],
        grid_height: int = 0,
        grid_width: int = 0,
    ) -> dict:
        cell_list = sorted((int(row), int(col)) for row, col in cells)
        bbox = self.compute_bbox(cell_list)
        normalized = self.normalize_shape(cell_list)
        cell_set = set(cell_list)
        rows = [row for row, _ in cell_list]
        cols = [col for _, col in cell_list]
        perimeter = [
            [row, col]
            for row, col in cell_list
            if any(
                (row + d_row, col + d_col) not in cell_set
                for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
        ]

        return {
            "size": len(cell_list),
            "bbox": bbox,
            "center": {
                "row": sum(rows) / len(rows) if rows else 0.0,
                "col": sum(cols) / len(cols) if cols else 0.0,
            },
            "normalized_shape": [[row, col] for row, col in normalized],
            "shape_signature": self.shape_signature(normalized),
            "canonical_shape_signature": self.canonical_signature(normalized),
            "holes": self.detect_holes(cell_list),
            "is_solid": self.is_solid(cell_list),
            "edge_touching": self.touches_edge(cell_list, grid_height, grid_width),
            "height": bbox["height"],
            "width": bbox["width"],
            "area": bbox["height"] * bbox["width"],
            "density": (
                round(len(cell_list) / (bbox["height"] * bbox["width"]), 4)
                if bbox["height"] and bbox["width"]
                else 0.0
            ),
            "horizontal_symmetry": self._has_horizontal_symmetry(normalized),
            "vertical_symmetry": self._has_vertical_symmetry(normalized),
            "perimeter_size": len(perimeter),
            "perimeter_cells": perimeter,
            "anchors": self._anchors(bbox),
        }

    def touches_edge(self, cells: Iterable[Cell], height: int, width: int) -> bool:
        if height <= 0 or width <= 0:
            return False
        return any(
            row == 0 or col == 0 or row == height - 1 or col == width - 1
            for row, col in cells
        )

    def _anchors(self, bbox: BBox) -> dict[str, list[int]]:
        return {
            "top_left": [bbox["min_row"], bbox["min_col"]],
            "top_right": [bbox["min_row"], bbox["max_col"]],
            "bottom_left": [bbox["max_row"], bbox["min_col"]],
            "bottom_right": [bbox["max_row"], bbox["max_col"]],
        }

    def _neighbors(self, row: int, col: int) -> tuple[Cell, ...]:
        return (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        )

    def _shape_transforms(self, cells: list[Cell]) -> list[list[Cell]]:
        if not cells:
            return [[]]
        return [
            [(row, col) for row, col in cells],
            [(row, -col) for row, col in cells],
            [(-row, col) for row, col in cells],
            [(-row, -col) for row, col in cells],
            [(col, row) for row, col in cells],
            [(col, -row) for row, col in cells],
            [(-col, row) for row, col in cells],
            [(-col, -row) for row, col in cells],
        ]

    def _has_horizontal_symmetry(self, normalized_cells: list[Cell]) -> bool:
        if not normalized_cells:
            return False
        cells = set(normalized_cells)
        max_row = max(row for row, _ in normalized_cells)
        return all((max_row - row, col) in cells for row, col in cells)

    def _has_vertical_symmetry(self, normalized_cells: list[Cell]) -> bool:
        if not normalized_cells:
            return False
        cells = set(normalized_cells)
        max_col = max(col for _, col in normalized_cells)
        return all((row, max_col - col) in cells for row, col in cells)


__all__ = [
    "ShapeAnalyzer",
]
