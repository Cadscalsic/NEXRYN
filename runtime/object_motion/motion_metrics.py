"""Metrics emitted by object-relative motion reasoning."""

OBJECT_MOTION_METRICS = {
    "false_global_translation_rate": 0.0,
    "independent_motion_detection_rate": 0.0,
    "gravity_reasoning_accuracy": 0.0,
    "support_detection_accuracy": 0.0,
    "collision_resolution_accuracy": 0.0,
    "prediction_improvement": 0.0,
}


def metric_names() -> list[str]:
    return list(OBJECT_MOTION_METRICS)

