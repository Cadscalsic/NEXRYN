"""Simulate downward object settling until support or boundary."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np

from runtime.object_motion.collision_detection_engine import collision_detection_engine
from runtime.object_motion.contracts import GravityResult
from runtime.object_motion.motion_budget_controller import motion_budget_controller


class GravityReasoningEngine:
    def simulate(self, grid: Any, obj: dict, fixed_cells=None, support_objects=None) -> dict:
        array = np.array(grid)
        fixed_cells = fixed_cells or set()
        support_objects = support_objects or {}
        distance = 0
        while motion_budget_controller.can_iterate_gravity():
            motion_budget_controller.record_gravity()
            candidate = distance + 1
            report = collision_detection_engine.check(
                array,
                obj,
                translation=(candidate, 0),
                fixed_cells=fixed_cells,
            )
            if report["collision_detected"]:
                support = self._support_for_collision(report, support_objects)
                final_cells = self._translated_cells(obj, distance)
                return asdict(GravityResult(
                    object_id=self._object_id(obj),
                    translation=(distance, 0),
                    final_position=self._anchor(final_cells),
                    support_object=support,
                    iterations=motion_budget_controller.gravity_iterations,
                    final_cells=final_cells,
                ))
            distance = candidate
        final_cells = self._translated_cells(obj, distance)
        return asdict(GravityResult(
            object_id=self._object_id(obj),
            translation=(distance, 0),
            final_position=self._anchor(final_cells),
            support_object=None,
            iterations=motion_budget_controller.gravity_iterations,
            final_cells=final_cells,
        ))

    def _translated_cells(self, obj, distance):
        return [
            [int(row) + int(distance), int(col)]
            for row, col in obj.get("cells", []) or []
        ]

    def _support_for_collision(self, report, support_objects):
        location = report.get("collision_location")
        if not location:
            return None
        row, col = location
        return support_objects.get((row, col))

    def _object_id(self, obj):
        return str(obj.get("id", obj.get("object_id", "")))

    def _anchor(self, cells):
        if not cells:
            return (0, 0)
        rows = [int(cell[0]) for cell in cells]
        cols = [int(cell[1]) for cell in cells]
        return (min(rows), min(cols))


gravity_reasoning_engine = GravityReasoningEngine()


__all__ = [
    "GravityResult",
    "GravityReasoningEngine",
    "gravity_reasoning_engine",
]
