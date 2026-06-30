"""Memory and reuse efficiency profiling."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class MemoryMetrics:
    cache_hits: int
    cache_misses: int
    strategy_hits: int
    strategy_misses: int
    context_hits: int
    context_misses: int
    program_hits: int
    program_misses: int
    truth_hits: int
    truth_misses: int
    counterfactual_hits: int
    counterfactual_misses: int
    counterfactual_success: int
    reuse_rate: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class MemoryProfiler:
    def profile(
        self,
        performance_report: dict[str, Any] | None,
        runtime_context: dict[str, Any] | None,
    ) -> MemoryMetrics:
        performance_report = performance_report or {}
        runtime_context = runtime_context or {}
        reuse_report = self._mapping(
            runtime_context.get("COGNITIVE_REUSE_REPORT")
            or runtime_context.get("cognitive_reuse_report")
            or runtime_context.get("knowledge_reuse_report")
        )
        knowledge_reuse_report = self._mapping(
            runtime_context.get("knowledge_reuse_report")
        )
        truth_reuse_report = self._mapping(
            runtime_context.get("truth_reuse_report")
        )
        strategy_reuse_report = self._mapping(
            runtime_context.get("strategy_reuse_report")
        )
        counterfactual_reuse_report = self._mapping(
            runtime_context.get("counterfactual_reuse_report")
        )
        supervisor_report = self._mapping(
            runtime_context.get("META_SUPERVISOR_REPORT")
            or runtime_context.get("meta_supervisor_report")
        )
        cache_hits = int(self._number(performance_report.get("cache_hits")))
        cache_misses = int(self._number(performance_report.get("cache_misses")))
        strategy_hits = int(self._number(
            performance_report.get("strategy_hits")
            or strategy_reuse_report.get("strategy_hits")
            or reuse_report.get("strategy_hits")
            or knowledge_reuse_report.get("strategy_hits")
        ))
        program_hits = int(self._number(
            performance_report.get("program_hits")
            or reuse_report.get("program_hits")
            or knowledge_reuse_report.get("program_hits")
        ))
        context_hits = int(self._number(
            performance_report.get("context_hits")
            or reuse_report.get("context_hits")
            or knowledge_reuse_report.get("context_hits")
        ))
        truth_hits = int(self._number(
            performance_report.get("truth_hits")
            or reuse_report.get("truth_hits")
            or truth_reuse_report.get("truth_hits")
        ))
        strategy_misses = int(self._number(
            performance_report.get("strategy_misses")
            or strategy_reuse_report.get("strategy_misses")
        ))
        program_misses = int(self._number(
            performance_report.get("program_misses")
        ))
        context_misses = int(self._number(
            performance_report.get("context_misses")
        ))
        truth_misses = int(self._number(
            performance_report.get("truth_misses")
        ))
        counterfactual_hits = int(self._number(
            performance_report.get("counterfactual_hits")
            or counterfactual_reuse_report.get("counterfactual_hits")
        ))
        counterfactual_misses = int(self._number(
            performance_report.get("counterfactual_misses")
            or counterfactual_reuse_report.get("counterfactual_misses")
        ))
        counterfactual_success = int(self._number(
            performance_report.get("counterfactual_success")
            or counterfactual_reuse_report.get("counterfactual_success")
        ))
        if not strategy_hits and not strategy_misses:
            strategy_misses = int(
                supervisor_report.get("selected_action")
                != "REUSE_KNOWN_STRATEGY"
            )
        if not program_hits and not program_misses:
            program_misses = int(
                supervisor_report.get("selected_action")
                != "REUSE_EXECUTABLE_PROGRAM"
            )
        if not context_hits and not context_misses:
            context_misses = int(
                supervisor_report.get("selected_action")
                != "REUSE_VALIDATED_CONTEXT"
            )
        if not truth_hits and not truth_misses:
            truth_misses = int(
                supervisor_report.get("selected_action")
                != "REUSE_LOCKED_TRUTH"
            )
        reuse_events = (
            cache_hits
            + strategy_hits
            + program_hits
            + context_hits
            + truth_hits
            + counterfactual_hits
        )
        queries = (
            reuse_events
            + cache_misses
            + strategy_misses
            + program_misses
            + context_misses
            + truth_misses
            + counterfactual_misses
        )
        return MemoryMetrics(
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            strategy_hits=strategy_hits,
            strategy_misses=strategy_misses,
            context_hits=context_hits,
            context_misses=context_misses,
            program_hits=program_hits,
            program_misses=program_misses,
            truth_hits=truth_hits,
            truth_misses=truth_misses,
            counterfactual_hits=counterfactual_hits,
            counterfactual_misses=counterfactual_misses,
            counterfactual_success=counterfactual_success,
            reuse_rate=round(reuse_events / max(queries, 1), 4),
        )

    def _mapping(self, value):
        return value if isinstance(value, dict) else {}

    def _number(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


memory_profiler = MemoryProfiler()


__all__ = [
    "MemoryMetrics",
    "MemoryProfiler",
    "memory_profiler",
]
