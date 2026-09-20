"""Collision checks for object motion."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np

from runtime.object_motion.contracts import CollisionReport


class CollisionDetectionEngine:
    def check(
        self,
        grid: Any,
        obj: dict,
        translation=(0, 0),
        fixed_cells: set[tuple[int, int]] | None = None,
    ) -> dict:
        array = np.array(grid)
        fixed_cells = fixed_cells or set()
        dr, dc = translation
        object_id = str(obj.get("id", obj.get("object_id", "")))
        for row, col in obj.get("cells", []) or []:
            target = (int(row) + int(dr), int(col) + int(dc))
            if target[0] < 0 or target[0] >= array.shape[0]:
                return asdict(CollisionReport(True, "boundary_collision", target, object_id))
            if target[1] < 0 or target[1] >= array.shape[1]:
                return asdict(CollisionReport(True, "boundary_collision", target, object_id))
            if target in fixed_cells:
                return asdict(CollisionReport(True, "support_surface_collision", target, object_id))
            if array[target] != 0 and target not in {
                (int(cell[0]), int(cell[1])) for cell in obj.get("cells", []) or []
            }:
                return asdict(CollisionReport(True, "object_collision", target, object_id))
        return asdict(CollisionReport(False, "none", None, object_id))


collision_detection_engine = CollisionDetectionEngine()


__all__ = [
    "CollisionReport",
    "CollisionDetectionEngine",
    "collision_detection_engine",
]
