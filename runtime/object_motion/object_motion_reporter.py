"""Build object motion reports."""

from __future__ import annotations

from dataclasses import asdict

from runtime.object_motion.contracts import MotionReport


class ObjectMotionReporter:
    def build(
        self,
        motion_pattern,
        translation_per_object,
        support_surfaces,
        constraints,
        collisions,
        gravity_simulations,
        prediction_improvement=0.0,
        budget_report=None,
    ):
        base_report = asdict(MotionReport(
            motion_pattern=motion_pattern.get("motion_pattern", motion_pattern),
            translation_variance=(
                motion_pattern.get("translation_variance", 0.0)
                if isinstance(motion_pattern, dict)
                else 0.0
            ),
            translation_per_object={
                key: tuple(value)
                for key, value in (translation_per_object or {}).items()
            },
            support_count=len(support_surfaces or []),
            collision_count=len(collisions or []),
            support_surfaces=support_surfaces or [],
            constraints=constraints or {},
        ))
        return {
            **base_report,
            "system": "OBJECT_MOTION_REPORT",
            "fixed_objects": constraints.get("fixed_objects", []),
            "movable_objects": constraints.get("movable_objects", []),
            "support_objects": constraints.get("support_objects", []),
            "collisions": collisions or [],
            "gravity_simulations": gravity_simulations,
            "prediction_improvement": round(float(prediction_improvement), 4),
            "motion_constraints": {
                "gravity": bool(support_surfaces),
                "support_surface": bool(support_surfaces),
                "collision_detection": True,
                "environmental_constraints": bool(support_surfaces),
                "object_settling": bool(support_surfaces),
                "contact_reasoning": bool(collisions),
            },
            "reusable_concepts": [
                "gravity",
                "support_surface",
                "collision_detection",
                "independent_object_motion",
                "obstacle_aware_translation",
                "relative_distance",
                "environmental_constraints",
                "object_settling",
                "contact_reasoning",
            ],
            "budget": budget_report or {},
        }


object_motion_reporter = ObjectMotionReporter()


__all__ = [
    "ObjectMotionReporter",
    "object_motion_reporter",
]
