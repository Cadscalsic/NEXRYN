"""Reasoning efficiency profiler."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ReasoningMetrics:
    reasoning_depth: int
    active_routes: int
    semantic_concept_count: int
    hypothesis_count: int
    counterfactual_count: int
    cognitive_efficiency: float
    cost_per_hypothesis: float
    cost_per_route: float
    cost_per_success: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReasoningProfiler:
    def profile(
        self,
        runtime_context: dict[str, Any] | None,
        module_timings: list[dict[str, Any]] | None = None,
    ) -> ReasoningMetrics:
        runtime_context = runtime_context or {}
        performance_report = self._mapping(
            runtime_context.get("performance_report")
        )
        reasoning_report = self._mapping(runtime_context.get("reasoning_report"))
        routing_report = self._mapping(reasoning_report.get("routing_report"))
        evaluation = self._mapping(runtime_context.get("evaluation_result"))
        reasoning_depth = int(self._number(
            reasoning_report.get("reasoning_depth")
            or runtime_context.get("reasoning_depth")
            or performance_report.get("reasoning_depth")
            or performance_report.get("dependency_chain_depth")
            or 0
        ))
        active_routes = int(self._number(
            reasoning_report.get("active_routes")
            or routing_report.get("route_count")
            or performance_report.get("dependency_chains_executed")
            or 0
        ))
        semantic_concepts = runtime_context.get("semantic_concepts", []) or []
        semantic_concept_count = int(self._number(
            performance_report.get("semantic_concept_count")
            or performance_report.get("concepts_processed")
            or len(semantic_concepts)
            or 0
        ))
        hypothesis_count = len(runtime_context.get("hypotheses", []) or [])
        counterfactual_count = len(runtime_context.get("counterfactuals", []) or [])
        reasoning_cost = self._reasoning_cost(
            module_timings or [],
            reasoning_depth,
            active_routes,
            hypothesis_count,
        )
        accuracy_gain = self._number(
            evaluation.get("accuracy_gain")
            or evaluation.get("accuracy")
            or runtime_context.get("prediction_accuracy")
            or 0.0
        )
        success_count = 1 if (
            evaluation.get("exact_success") is True
            or evaluation.get("success_state") in {"SUCCESS", "EXACT_SUCCESS"}
        ) else 0
        return ReasoningMetrics(
            reasoning_depth=reasoning_depth,
            active_routes=active_routes,
            semantic_concept_count=semantic_concept_count,
            hypothesis_count=hypothesis_count,
            counterfactual_count=counterfactual_count,
            cognitive_efficiency=round(accuracy_gain / max(reasoning_cost, 0.0001), 4),
            cost_per_hypothesis=round(reasoning_cost / max(hypothesis_count, 1), 4),
            cost_per_route=round(reasoning_cost / max(active_routes, 1), 4),
            cost_per_success=round(reasoning_cost / max(success_count, 1), 4),
        )

    def _reasoning_cost(self, module_timings, depth, routes, hypotheses):
        timed_cost = sum(
            self._number(item.get("seconds"))
            for item in module_timings
            if "reason" in str(item.get("module", ""))
        )
        structural_cost = max(1.0, depth + routes + (hypotheses * 0.5))
        return max(timed_cost, structural_cost)

    def _mapping(self, value):
        return value if isinstance(value, dict) else {}

    def _number(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


reasoning_profiler = ReasoningProfiler()


__all__ = [
    "ReasoningMetrics",
    "ReasoningProfiler",
    "reasoning_profiler",
]
