"""Budget enforcement for evaluation metrics."""

from __future__ import annotations

import time
from typing import Any


MAX_EVALUATION_TIME = 1.0
MAX_METRIC_COUNT = 20
MAX_REPORT_DEPTH = 1


class MetricsBudgetController:
    def __init__(
        self,
        max_evaluation_time: float = MAX_EVALUATION_TIME,
        max_metric_count: int = MAX_METRIC_COUNT,
        max_report_depth: int = MAX_REPORT_DEPTH,
    ) -> None:
        self.max_evaluation_time = max_evaluation_time
        self.max_metric_count = max_metric_count
        self.max_report_depth = max_report_depth

    def enforce(
        self,
        metrics: dict[str, Any],
        started_at: float,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        elapsed = time.perf_counter() - started_at
        truncated = len(metrics) > self.max_metric_count
        if truncated:
            metrics = dict(list(metrics.items())[: self.max_metric_count])
        flattened = {
            key: self._truncate_depth(value, depth=0)
            for key, value in metrics.items()
        }
        over_time = elapsed > self.max_evaluation_time
        return flattened, {
            "metrics_truncated": truncated or flattened != metrics,
            "defer_reporting": over_time or truncated,
            "continue_shutdown": True,
            "evaluation_duration": elapsed,
        }

    def _truncate_depth(self, value: Any, depth: int) -> Any:
        if depth >= self.max_report_depth:
            if isinstance(value, dict):
                return {"truncated": True, "key_count": len(value)}
            if isinstance(value, list):
                return list(value[: self.max_metric_count])
            return value
        if isinstance(value, dict):
            return {
                key: self._truncate_depth(child, depth + 1)
                for key, child in list(value.items())[: self.max_metric_count]
            }
        if isinstance(value, list):
            return [
                self._truncate_depth(child, depth + 1)
                for child in value[: self.max_metric_count]
            ]
        return value
