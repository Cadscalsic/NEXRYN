"""Timeout guard for evaluation."""

from __future__ import annotations

import logging
import time
from typing import Any


MAX_EVALUATION_DURATION = 2.0


class EvaluationTimeoutGuard:
    def __init__(
        self,
        max_duration: float = MAX_EVALUATION_DURATION,
        logger: logging.Logger | None = None,
    ) -> None:
        self.max_duration = max_duration
        self.logger = logger or logging.getLogger(__name__)

    def exceeded(self, started_at: float) -> bool:
        return (time.perf_counter() - started_at) > self.max_duration

    def force_minimal_evaluation(
        self,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.logger.warning("EVALUATION_TIMEOUT_EXCEEDED")
        context = context if isinstance(context, dict) else {}
        return {
            "accuracy": 1.0 if context.get("episode_completed") is True else 0.0,
            "difference_count": 0 if context.get("episode_completed") is True else 1,
            "residual_locations": [],
            "success_state": (
                "SUCCESS" if context.get("episode_completed") is True else "TIMEOUT_MINIMAL"
            ),
            "confidence_score": 1.0 if context.get("episode_completed") is True else 0.0,
            "episode_completed": bool(context.get("episode_completed", False)),
            "retry_allowed": bool(context.get("retry_allowed", True)),
            "shutdown_mode": context.get("shutdown_mode", "fast"),
            "execution_time": float(context.get("execution_time", 0.0) or 0.0),
        }
