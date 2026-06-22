"""Performance evaluation for cognitive economy accountability."""

from __future__ import annotations

from typing import Any, Mapping


class PerformanceEvaluator:
    def __init__(self):
        self.history: list[dict[str, Any]] = []

    def evaluate(self, metrics: Mapping[str, Any] | None = None) -> dict[str, Any]:
        data = dict(metrics or {})
        successes = max(1.0, self._number(data.get("success_count", data.get("successes", 1.0))))
        total_cost = self._number(data.get("total_cost", data.get("runtime_cost", 0.0)))
        strategy_reuse = self._number(data.get("strategy_reuse_rate"))
        program_reuse = self._number(data.get("program_reuse_rate"))
        cache_hit = self._number(data.get("cache_hit_rate"))
        reasoning_depth = self._number(data.get("average_reasoning_depth", data.get("reasoning_depth")))
        budget_compliance = data.get("budget_compliance", True) is True
        reasoning_efficiency = self._bounded(1.0 - reasoning_depth / 10.0)
        cost_per_success = total_cost / successes
        report = {
            "cost_per_success": cost_per_success,
            "strategy_reuse_rate": strategy_reuse,
            "program_reuse_rate": program_reuse,
            "cache_hit_rate": cache_hit,
            "reasoning_efficiency": reasoning_efficiency,
            "budget_compliance": budget_compliance,
            "performance_score": self._bounded(
                (strategy_reuse + program_reuse + cache_hit + reasoning_efficiency) / 4.0
                + (0.10 if budget_compliance else -0.20)
            ),
        }
        self.history.append(report)
        return report

    def economy_report(self) -> dict[str, Any]:
        if not self.history:
            return {
                "cost_per_success": 0.0,
                "cost_per_strategy": 0.0,
                "reuse_rate": 0.0,
                "thinking_avoidance_rate": 0.0,
                "average_reasoning_depth": 0.0,
                "average_budget_utilization": 0.0,
                "governance_cost": 0.0,
            }
        recent = self.history[-100:]
        avg = lambda key: sum(float(item.get(key, 0.0)) for item in recent) / len(recent)
        reuse_rate = (avg("strategy_reuse_rate") + avg("program_reuse_rate") + avg("cache_hit_rate")) / 3.0
        return {
            "cost_per_success": avg("cost_per_success"),
            "cost_per_strategy": avg("cost_per_success") / max(0.1, avg("strategy_reuse_rate")),
            "reuse_rate": reuse_rate,
            "thinking_avoidance_rate": avg("reasoning_efficiency"),
            "average_reasoning_depth": max(0.0, 10.0 * (1.0 - avg("reasoning_efficiency"))),
            "average_budget_utilization": avg("average_budget_utilization"),
            "governance_cost": avg("governance_cost"),
        }

    def _number(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _bounded(self, value: float) -> float:
        return min(1.0, max(0.0, value))


performance_evaluator = PerformanceEvaluator()


__all__ = [
    "PerformanceEvaluator",
    "performance_evaluator",
]
