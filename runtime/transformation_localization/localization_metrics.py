"""Shared metrics and constants for transformation localization."""

from __future__ import annotations

EXECUTION_THRESHOLD = 0.75
LOCALIZATION_EXECUTION_THRESHOLD = 0.70
HIGH_HYPOTHESIS_CONFIDENCE = 0.90

MAX_LOCALIZATION_TIME = 0.5
MAX_LOCALIZATION_ATTEMPTS = 3
MAX_OBJECT_MATCHES = 10
MAX_WORLD_MODEL_RETRIES = 2

SUPPORTED_TRANSFORMATIONS = {
    "translation",
    "translate",
    "translate_down",
    "translate_up",
    "translate_left",
    "translate_right",
    "rotation",
    "rotate",
    "reflection",
    "reflect",
    "scaling",
    "scale",
    "color_mapping",
    "replace_color",
    "map_colors",
    "duplicate_object",
}


def clamp(value: object, minimum: float = 0.0, maximum: float = 1.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = minimum
    return max(minimum, min(number, maximum))


__all__ = [
    "EXECUTION_THRESHOLD",
    "LOCALIZATION_EXECUTION_THRESHOLD",
    "HIGH_HYPOTHESIS_CONFIDENCE",
    "MAX_LOCALIZATION_TIME",
    "MAX_LOCALIZATION_ATTEMPTS",
    "MAX_OBJECT_MATCHES",
    "MAX_WORLD_MODEL_RETRIES",
    "SUPPORTED_TRANSFORMATIONS",
    "clamp",
]
