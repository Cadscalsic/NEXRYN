"""Classify global versus independent object motion."""

from __future__ import annotations

TRANSLATION_VARIANCE_THRESHOLD = 0.1


class MotionPatternClassifier:
    def classify(self, translations, support_surfaces=None, collision_count=0):
        vectors = list(translations or [])
        variance = self.translation_variance(vectors)
        non_zero = [vector for vector in vectors if tuple(vector) != (0, 0)]
        downward = bool(non_zero) and all(int(vector[0]) > 0 for vector in non_zero)
        if collision_count:
            pattern = "collision_motion"
        elif downward and support_surfaces:
            pattern = "gravity_motion"
        elif support_surfaces and variance > TRANSLATION_VARIANCE_THRESHOLD:
            pattern = "constraint_driven_motion"
        elif variance <= TRANSLATION_VARIANCE_THRESHOLD:
            pattern = "global_translation"
        else:
            pattern = "independent_translation"
        return {
            "motion_pattern": pattern,
            "motion_subtype": (
                "object_settling"
                if pattern in {"gravity_motion", "constraint_driven_motion"}
                else "uniform_motion"
                if pattern == "global_translation"
                else "object_relative_motion"
            ),
            "translation_variance": round(variance, 4),
            "global_translation_allowed": variance <= TRANSLATION_VARIANCE_THRESHOLD,
            "global_translation_assumptions": variance <= TRANSLATION_VARIANCE_THRESHOLD,
        }

    def translation_variance(self, vectors):
        if len(vectors) <= 1:
            return 0.0
        rows = [float(vector[0]) for vector in vectors]
        cols = [float(vector[1]) for vector in vectors]
        mean_row = sum(rows) / len(rows)
        mean_col = sum(cols) / len(cols)
        return sum(
            ((row - mean_row) ** 2 + (col - mean_col) ** 2)
            for row, col in zip(rows, cols)
        ) / len(vectors)


motion_pattern_classifier = MotionPatternClassifier()


__all__ = [
    "TRANSLATION_VARIANCE_THRESHOLD",
    "MotionPatternClassifier",
    "motion_pattern_classifier",
]
