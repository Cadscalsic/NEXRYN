"""Stage and module duration profiling."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class StageMetrics:
    stage_name: str
    execution_count: int
    total_duration: float
    average_duration: float
    percentage_of_runtime: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class StageProfiler:
    def profile(
        self,
        module_timings: list[dict[str, Any]] | None,
        total_runtime_seconds: float,
    ) -> list[StageMetrics]:
        grouped: dict[str, list[float]] = {}
        for item in module_timings or []:
            name = str(item.get("module", "unknown"))
            grouped.setdefault(name, []).append(self._float(item.get("seconds")))

        metrics = []
        denominator = max(float(total_runtime_seconds or 0.0), 0.0001)
        for stage_name, durations in grouped.items():
            total = sum(durations)
            count = len(durations)
            metrics.append(
                StageMetrics(
                    stage_name=stage_name,
                    execution_count=count,
                    total_duration=round(total, 4),
                    average_duration=round(total / max(count, 1), 4),
                    percentage_of_runtime=round(total / denominator, 4),
                )
            )
        return sorted(metrics, key=lambda item: item.total_duration, reverse=True)

    def _float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


stage_profiler = StageProfiler()


__all__ = [
    "StageMetrics",
    "StageProfiler",
    "stage_profiler",
]
