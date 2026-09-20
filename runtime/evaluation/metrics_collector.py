"""Minimal metric collection for evaluation decisions only."""

from __future__ import annotations

from typing import Any


ALLOWED_METRIC_KEYS = {
    "accuracy",
    "difference_count",
    "residual_locations",
    "success_state",
    "confidence_score",
    "episode_completed",
    "retry_allowed",
    "shutdown_mode",
    "execution_time",
}


class MetricsCollector:
    """Collects only the fields needed to decide task success."""

    def collect(self, runtime_context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = runtime_context if isinstance(runtime_context, dict) else {}
        source = self._find_metric_source(context)
        accuracy = self._number(
            source.get("accuracy"),
            source.get("prediction_accuracy"),
            context.get("accuracy"),
            context.get("prediction_accuracy"),
            default=1.0 if context.get("episode_completed") is True else 0.0,
        )
        difference_count = int(self._number(
            source.get("difference_count"),
            source.get("residual_difference_count"),
            context.get("difference_count"),
            context.get("residual_difference_count"),
            default=0 if context.get("episode_completed") is True else 1,
        ))
        success_state = str(
            source.get("success_state")
            or context.get("success_state")
            or ("SUCCESS" if accuracy >= 1.0 and difference_count == 0 else "INCOMPLETE")
        )
        confidence = self._number(
            source.get("confidence_score"),
            source.get("confidence"),
            source.get("prediction_confidence"),
            context.get("confidence_score"),
            context.get("confidence"),
            context.get("prediction_confidence"),
            default=accuracy,
        )
        episode_completed = bool(
            source.get("episode_completed", context.get("episode_completed", False))
            or success_state == "SUCCESS"
            or (accuracy >= 1.0 and difference_count == 0)
        )
        retry_allowed = bool(
            source.get(
                "retry_allowed",
                context.get("retry_allowed", not episode_completed),
            )
        )
        shutdown_mode = str(
            source.get("shutdown_mode")
            or context.get("shutdown_mode")
            or ("fast" if episode_completed and not retry_allowed else "normal")
        )
        metrics = {
            "accuracy": round(max(0.0, min(1.0, accuracy)), 4),
            "difference_count": max(0, difference_count),
            "residual_locations": self._bounded_locations(
                source.get("residual_locations", context.get("residual_locations", []))
            ),
            "success_state": success_state,
            "confidence_score": round(max(0.0, min(1.0, confidence)), 4),
            "episode_completed": episode_completed,
            "retry_allowed": retry_allowed,
            "shutdown_mode": shutdown_mode,
            "execution_time": self._number(
                source.get("execution_time"),
                context.get("execution_time"),
                context.get("pipeline_execution_time"),
                default=0.0,
            ),
        }
        return {key: metrics[key] for key in ALLOWED_METRIC_KEYS if key in metrics}

    def _find_metric_source(self, context: dict[str, Any]) -> dict[str, Any]:
        for key in (
            "evaluation_result",
            "evaluation_metrics",
            "minimal_success_record",
            "prediction_report",
            "task_outcome",
        ):
            value = context.get(key)
            if isinstance(value, dict):
                return value
        metadata = context.get("execution_metadata")
        if isinstance(metadata, dict):
            for key in ("evaluation_result", "evaluation_metrics", "prediction_report"):
                value = metadata.get(key)
                if isinstance(value, dict):
                    return value
        return {}

    def _number(self, *values: Any, default: float) -> float:
        for value in values:
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return float(default)

    def _bounded_locations(self, locations: Any) -> list[Any]:
        if not isinstance(locations, list):
            return []
        return list(locations[:20])
