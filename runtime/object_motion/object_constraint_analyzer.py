"""Classify movable objects and environmental constraints."""

from __future__ import annotations

from dataclasses import asdict

from runtime.object_motion.contracts import ConstraintProfile


class ObjectConstraintAnalyzer:
    def analyze(self, objects: list[dict], support_surfaces: list[dict]) -> dict:
        support_ids = {
            str(surface.get("object_id"))
            for surface in support_surfaces
            if surface.get("object_id")
        }
        fixed = []
        movable = []
        for obj in objects:
            object_id = str(obj.get("id", obj.get("object_id", "")))
            if object_id in support_ids:
                fixed.append(object_id)
            else:
                movable.append(object_id)
        return asdict(ConstraintProfile(
            movable_objects=movable,
            fixed_objects=fixed,
            support_objects=sorted(support_ids),
            obstacles=fixed,
            anchors=fixed,
        ))


object_constraint_analyzer = ObjectConstraintAnalyzer()


__all__ = [
    "ConstraintProfile",
    "ObjectConstraintAnalyzer",
    "object_constraint_analyzer",
]
