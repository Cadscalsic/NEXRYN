"""Low-overhead candidate prediction/evaluation timing."""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
import time
from pathlib import Path
from typing import Any, Iterator, Mapping

def profiler_path() -> Path | None:
    path = os.environ.get("NEXRYN_CANDIDATE_COST_PROFILE_PATH")
    return Path(path) if path else None


class CandidateCostProfiler:
    """Aggregate candidate timing without per-subcall fsync telemetry."""

    authority = "OBSERVATION_ONLY"
    behavioral_authority = "NONE"

    def __init__(
        self,
        *,
        task_id: str | None = None,
        candidate_count: int = 0,
        sample_interval: int = 0,
    ) -> None:
        self.task_id = task_id or os.environ.get(
            "NEXRYN_CANDIDATE_COST_PROFILE_TASK_ID"
        )
        self.candidate_count = int(candidate_count or 0)
        self.sample_interval = max(int(sample_interval or 0), 0)
        self.candidates_started = 0
        self.candidates_completed = 0
        self.last_candidate_index: int | None = None
        self.aggregate_prediction_ms = 0.0
        self.aggregate_evaluation_ms = 0.0
        self.aggregate_scene_graph_ms = 0.0
        self.aggregate_matching_ms = 0.0
        self.aggregate_difference_count_ms = 0.0
        self.aggregate_scoring_ms = 0.0
        self.max_prediction_ms = 0.0
        self.max_evaluation_ms = 0.0
        self.max_candidate_ms = 0.0
        self.sampled_prediction_duration_ms: list[float] = []
        self.sampled_evaluation_duration_ms: list[float] = []
        self.sampled_candidate_duration_ms: list[float] = []
        self.source_node_counts: list[int] = []
        self.target_node_counts: list[int] = []
        self.attempted_matches: list[int] = []
        self.matched_nodes: list[int] = []
        self._candidate_started_at: float | None = None
        self._candidate_prediction_ms = 0.0
        self._candidate_evaluation_ms = 0.0

    def candidate_started(self, candidate_index: int) -> None:
        self.candidates_started += 1
        self.last_candidate_index = int(candidate_index)
        self._candidate_started_at = time.perf_counter()
        self._candidate_prediction_ms = 0.0
        self._candidate_evaluation_ms = 0.0

    def candidate_completed(self, candidate_index: int) -> None:
        self.candidates_completed += 1
        self.last_candidate_index = int(candidate_index)
        candidate_ms = self._elapsed_ms(self._candidate_started_at)
        self.max_candidate_ms = max(self.max_candidate_ms, candidate_ms)
        if self._should_sample(int(candidate_index)):
            self.sampled_prediction_duration_ms.append(
                round(self._candidate_prediction_ms, 4)
            )
            self.sampled_evaluation_duration_ms.append(
                round(self._candidate_evaluation_ms, 4)
            )
            self.sampled_candidate_duration_ms.append(round(candidate_ms, 4))

    @contextmanager
    def prediction_timer(self) -> Iterator[None]:
        started_at = time.perf_counter()
        try:
            yield
        finally:
            elapsed = self._elapsed_ms(started_at)
            self.aggregate_prediction_ms += elapsed
            self._candidate_prediction_ms += elapsed
            self.max_prediction_ms = max(self.max_prediction_ms, elapsed)

    @contextmanager
    def evaluation_timer(self) -> Iterator[None]:
        started_at = time.perf_counter()
        try:
            yield
        finally:
            elapsed = self._elapsed_ms(started_at)
            self.aggregate_evaluation_ms += elapsed
            self._candidate_evaluation_ms += elapsed
            self.max_evaluation_ms = max(self.max_evaluation_ms, elapsed)

    @contextmanager
    def owner_timer(self, owner: str) -> Iterator[None]:
        started_at = time.perf_counter()
        try:
            yield
        finally:
            elapsed = self._elapsed_ms(started_at)
            if owner == "scene_graph":
                self.aggregate_scene_graph_ms += elapsed
            elif owner == "matching":
                self.aggregate_matching_ms += elapsed
            elif owner == "difference_count":
                self.aggregate_difference_count_ms += elapsed
            elif owner == "scoring":
                self.aggregate_scoring_ms += elapsed

    def record_matching_shape(
        self,
        source_nodes: Mapping[str, Any],
        target_nodes: Mapping[str, Any],
        matches: list[Mapping[str, Any]],
    ) -> None:
        source_count = len(source_nodes or {})
        target_count = len(target_nodes or {})
        self.source_node_counts.append(source_count)
        self.target_node_counts.append(target_count)
        self.attempted_matches.append(source_count * target_count)
        self.matched_nodes.append(len(matches or []))

    def report(self) -> dict[str, Any]:
        evaluation_ms = self.aggregate_evaluation_ms
        prediction_ms = self.aggregate_prediction_ms
        total_ms = prediction_ms + evaluation_ms
        return {
            "system": "candidate_cost_profiler",
            "authority": self.authority,
            "behavioral_authority": self.behavioral_authority,
            "task_id": self.task_id,
            "candidate_count": self.candidate_count,
            "candidates_started": self.candidates_started,
            "candidates_completed": self.candidates_completed,
            "last_candidate_index": self.last_candidate_index,
            "candidate_index_at_timeout": None,
            "sampled_prediction_duration_ms": self.sampled_prediction_duration_ms,
            "sampled_evaluation_duration_ms": self.sampled_evaluation_duration_ms,
            "sampled_candidate_duration_ms": self.sampled_candidate_duration_ms,
            "aggregate_prediction_ms": round(prediction_ms, 4),
            "aggregate_evaluation_ms": round(evaluation_ms, 4),
            "max_prediction_ms": round(self.max_prediction_ms, 4),
            "max_evaluation_ms": round(self.max_evaluation_ms, 4),
            "max_candidate_ms": round(self.max_candidate_ms, 4),
            "aggregate_scene_graph_ms": round(self.aggregate_scene_graph_ms, 4),
            "aggregate_matching_ms": round(self.aggregate_matching_ms, 4),
            "aggregate_difference_count_ms": round(
                self.aggregate_difference_count_ms,
                4,
            ),
            "aggregate_scoring_ms": round(self.aggregate_scoring_ms, 4),
            "prediction_time_share": _share(prediction_ms, total_ms),
            "evaluation_time_share": _share(evaluation_ms, total_ms),
            "scene_graph_time_share": _share(self.aggregate_scene_graph_ms, total_ms),
            "matching_time_share": _share(self.aggregate_matching_ms, total_ms),
            "scoring_time_share": _share(self.aggregate_scoring_ms, total_ms),
            "source_node_count_distribution": _distribution(self.source_node_counts),
            "target_node_count_distribution": _distribution(self.target_node_counts),
            "match_attempt_distribution": _distribution(self.attempted_matches),
            "matched_node_distribution": _distribution(self.matched_nodes),
        }

    def flush(self, path: Path | None = None) -> Path | None:
        destination = path or profiler_path()
        if destination is None:
            return None
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(self.report(), sort_keys=True, ensure_ascii=True) + "\n")
        return destination

    def _should_sample(self, candidate_index: int) -> bool:
        if candidate_index in {1, self.candidate_count}:
            return True
        if self.candidate_count and candidate_index == (self.candidate_count + 1) // 2:
            return True
        return bool(self.sample_interval and candidate_index % self.sample_interval == 0)

    def _elapsed_ms(self, started_at: float | None) -> float:
        if started_at is None:
            return 0.0
        return (time.perf_counter() - started_at) * 1000.0


def build_profiler(
    runtime_context: Mapping[str, Any] | None,
    *,
    candidate_count: int,
) -> CandidateCostProfiler | None:
    context = runtime_context if isinstance(runtime_context, Mapping) else {}
    enabled = (
        context.get("low_overhead_candidate_profiler_enabled") is True
        or os.environ.get("NEXRYN_CANDIDATE_COST_PROFILE_ENABLED") == "1"
        or profiler_path() is not None
    )
    if not enabled:
        return None
    return CandidateCostProfiler(
        task_id=context.get("task_id"),
        candidate_count=candidate_count,
        sample_interval=int(context.get("candidate_cost_sample_interval", 0) or 0),
    )


def _distribution(values: list[int]) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for value in values:
        key = str(int(value))
        distribution[key] = distribution.get(key, 0) + 1
    return dict(sorted(distribution.items(), key=lambda item: int(item[0])))


def _share(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round(float(value) / total, 4)


__all__ = [
    "CandidateCostProfiler",
    "build_profiler",
    "profiler_path",
]
