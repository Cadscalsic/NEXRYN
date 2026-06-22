"""Object-relative motion and support-surface reasoning."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from core.perception import ObjectExtractor
from runtime.object_motion.collision_detection_engine import collision_detection_engine
from runtime.object_motion.gravity_reasoning_engine import gravity_reasoning_engine
from runtime.object_motion.motion_budget_controller import motion_budget_controller
from runtime.object_motion.motion_pattern_classifier import motion_pattern_classifier
from runtime.object_motion.object_constraint_analyzer import object_constraint_analyzer
from runtime.object_motion.object_motion_reporter import object_motion_reporter
from runtime.object_motion.relative_translation_engine import relative_translation_engine
from runtime.object_motion.support_surface_detector import support_surface_detector

logger = logging.getLogger(__name__)


class ObjectMotionEngine:
    def __init__(self, object_extractor=None):
        self.object_extractor = object_extractor or ObjectExtractor()

    def analyze(self, input_grid: Any, target_grid: Any | None = None) -> dict:
        motion_budget_controller.reset()
        input_array = np.array(input_grid)
        input_objects = self.object_extractor.extract_objects(input_array)
        target_objects = (
            self.object_extractor.extract_objects(target_grid)
            if target_grid is not None
            else []
        )
        support_surfaces = support_surface_detector.detect(input_array, input_objects)
        constraints = object_constraint_analyzer.analyze(input_objects, support_surfaces)
        translation_per_object = (
            relative_translation_engine.compute(input_objects, target_objects)
            if target_objects
            else {}
        )
        if not translation_per_object and support_surfaces:
            translation_per_object = self._gravity_translations(
                input_array,
                input_objects,
                support_surfaces,
            )
        pattern = motion_pattern_classifier.classify(
            list(translation_per_object.values()),
            support_surfaces=support_surfaces,
        )
        collisions = self._collisions(input_array, input_objects, translation_per_object, support_surfaces)
        blocking_collisions = [
            collision
            for collision in collisions
            if collision.get("collision_type") != "support_surface_collision"
        ]
        pattern = motion_pattern_classifier.classify(
            list(translation_per_object.values()),
            support_surfaces=support_surfaces,
            collision_count=len(blocking_collisions),
        )
        prediction = self.apply_translations(input_array, input_objects, translation_per_object, constraints)
        report = object_motion_reporter.build(
            pattern,
            translation_per_object,
            support_surfaces,
            constraints,
            collisions,
            motion_budget_controller.motion_simulations,
            budget_report=motion_budget_controller.report(),
        )
        report["predicted_grid"] = prediction
        report["object_count"] = len(input_objects)
        logger.info("[MOTION] pattern=%s", report["motion_pattern"])
        logger.info("[MOTION] variance=%s", report["translation_variance"])
        logger.info("[MOTION] support_surfaces=%s", len(support_surfaces))
        logger.info("[MOTION] translations=%s", translation_per_object)
        logger.info("[MOTION] collisions=%s", len(collisions))
        return report

    def apply_translations(self, grid, objects, translation_per_object, constraints=None):
        array = np.array(grid)
        output = np.array(array, copy=True)
        constraints = constraints or {}
        fixed = set(constraints.get("fixed_objects", []))
        movable_ids = set(constraints.get("movable_objects", []))
        for obj in objects:
            object_id = str(obj.get("id", obj.get("object_id", "")))
            if object_id in fixed:
                continue
            if movable_ids and object_id not in movable_ids:
                continue
            translation = translation_per_object.get(object_id, (0, 0))
            if tuple(translation) == (0, 0):
                continue
            for row, col in obj.get("cells", []) or []:
                output[int(row), int(col)] = 0
        for obj in objects:
            object_id = str(obj.get("id", obj.get("object_id", "")))
            if object_id in fixed:
                continue
            translation = translation_per_object.get(object_id, (0, 0))
            dr, dc = int(translation[0]), int(translation[1])
            for row, col in obj.get("cells", []) or []:
                nr = int(row) + dr
                nc = int(col) + dc
                if 0 <= nr < output.shape[0] and 0 <= nc < output.shape[1]:
                    output[nr, nc] = int(obj.get("color", array[int(row), int(col)]))
        motion_budget_controller.record_motion()
        return output

    def _gravity_translations(self, grid, objects, support_surfaces):
        fixed_cells, support_by_cell = self._support_cells(support_surfaces)
        translations = {}
        support_ids = {surface.get("object_id") for surface in support_surfaces}
        for obj in objects:
            object_id = str(obj.get("id", obj.get("object_id", "")))
            if object_id in support_ids:
                translations[object_id] = (0, 0)
                continue
            result = gravity_reasoning_engine.simulate(
                grid,
                obj,
                fixed_cells=fixed_cells,
                support_objects=support_by_cell,
            )
            translations[object_id] = tuple(result.get("translation", (0, 0)))
        return translations

    def _collisions(self, grid, objects, translations, support_surfaces):
        fixed_cells, _support_by_cell = self._support_cells(support_surfaces)
        collisions = []
        for obj in objects:
            if not motion_budget_controller.can_check_collision():
                break
            motion_budget_controller.record_collision()
            report = collision_detection_engine.check(
                grid,
                obj,
                translation=translations.get(str(obj.get("id")), (0, 0)),
                fixed_cells=fixed_cells,
            )
            if report["collision_detected"]:
                collisions.append(report)
        return collisions

    def _support_cells(self, support_surfaces):
        fixed = set()
        by_cell = {}
        for surface in support_surfaces or []:
            row = int(surface.get("row", 0))
            object_id = surface.get("object_id")
            for col in surface.get("columns", []) or []:
                cell = (row, int(col))
                fixed.add(cell)
                by_cell[cell] = object_id
        return fixed, by_cell


object_motion_engine = ObjectMotionEngine()


__all__ = [
    "ObjectMotionEngine",
    "object_motion_engine",
]
