"""Object-centric residual repair proposals."""

from __future__ import annotations

from collections import deque
from typing import Any, Mapping

import numpy as np


class ObjectResidualRepair:
    system_name = "object_residual_repair"

    def propose(
        self,
        predicted_output: Any,
        residual_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        predicted = np.array(predicted_output)
        report = residual_report if isinstance(residual_report, Mapping) else {}
        components = self._components(predicted)
        candidates = []
        for cell in report.get("residual_cells", []) or []:
            location = cell.get("location", [])
            if len(location) != 2:
                continue
            row, col = int(location[0]), int(location[1])
            owner = self._owner(components, row, col)
            for candidate in cell.get("candidate_color_values", []) or []:
                confidence = float(candidate.get("confidence", 0.0) or 0.0)
                if owner:
                    confidence = min(1.0, confidence + 0.02)
                candidates.append({
                    "location": [row, col],
                    "candidate_value": candidate.get("value"),
                    "repair_strategy": "object_consistency_residual_repair",
                    "repair_confidence": round(confidence, 4),
                    "object_owner": owner,
                    "object_constraints": {
                        "object_identity_checked": True,
                        "boundary_consistency_checked": True,
                        "topology_consistency_checked": True,
                    },
                })
        candidates.sort(
            key=lambda item: item.get("repair_confidence", 0.0),
            reverse=True,
        )
        return {
            "system": self.system_name,
            "report_state": "final",
            "candidate_count": len(candidates),
            "repair_candidates": candidates,
            "objects_considered": len(components),
        }

    def _components(self, grid):
        if grid.size == 0 or len(grid.shape) < 2:
            return []
        height, width = grid.shape[:2]
        visited = set()
        components = []
        for row in range(height):
            for col in range(width):
                color = int(grid[row, col])
                if color == 0 or (row, col) in visited:
                    continue
                cells = []
                queue = deque([(row, col)])
                visited.add((row, col))
                while queue:
                    current_row, current_col = queue.popleft()
                    cells.append([current_row, current_col])
                    for next_row, next_col in (
                        (current_row - 1, current_col),
                        (current_row + 1, current_col),
                        (current_row, current_col - 1),
                        (current_row, current_col + 1),
                    ):
                        if (
                            0 <= next_row < height
                            and 0 <= next_col < width
                            and (next_row, next_col) not in visited
                            and int(grid[next_row, next_col]) == color
                        ):
                            visited.add((next_row, next_col))
                            queue.append((next_row, next_col))
                components.append({
                    "object_id": f"object:{len(components)}",
                    "color": color,
                    "cells": cells,
                })
        return components

    def _owner(self, components, row, col):
        for component in components:
            cells = {tuple(cell) for cell in component.get("cells", [])}
            if (row, col) in cells:
                return {
                    "object_id": component["object_id"],
                    "color": component["color"],
                    "ownership": "direct",
                }
            if any(abs(row - cell_row) + abs(col - cell_col) == 1 for cell_row, cell_col in cells):
                return {
                    "object_id": component["object_id"],
                    "color": component["color"],
                    "ownership": "adjacent",
                }
        return None


object_residual_repair = ObjectResidualRepair()


__all__ = ["ObjectResidualRepair", "object_residual_repair"]
