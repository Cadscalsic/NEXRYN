"""Allocate directional cognitive budgets without executing learning."""

from __future__ import annotations

from typing import Any, Mapping


PRIORITY_BUDGETS: tuple[str, ...] = (
    "concept_learning",
    "context_learning",
    "strategy_refinement",
    "program_reuse",
    "memory_optimization",
    "performance_optimization",
)


class PriorityAllocator:
    def allocate(
        self,
        target_domains: list[str],
        runtime_context: Mapping[str, Any] | None = None,
        available_resources: float | None = None,
    ) -> dict[str, float]:
        context = dict(runtime_context or {})
        budget = self._budget(context, available_resources)
        frozen = set(context.get("frozen_concepts", []) or [])
        saturated = set(context.get("saturated_domains", []) or [])
        locked = set(context.get("locked_truths", []) or [])
        weights = {key: 0.0 for key in PRIORITY_BUDGETS}

        for domain in target_domains:
            if domain in frozen or domain in saturated or domain in locked:
                continue
            if domain in {"generalization", "process_understanding", "causal_reasoning"}:
                weights["concept_learning"] += 1.0
            if domain in {"context_reuse", "cognitive_diversity"}:
                weights["context_learning"] += 1.0
            if domain == "strategy_reuse":
                weights["strategy_refinement"] += 1.0
                weights["program_reuse"] += 0.5
            if domain == "memory_efficiency":
                weights["memory_optimization"] += 1.0
            if domain == "runtime_efficiency":
                weights["performance_optimization"] += 1.0

        if not any(weights.values()):
            weights["memory_optimization"] = 0.5
            weights["performance_optimization"] = 0.5

        total = sum(weights.values()) or 1.0
        return {
            key: budget * value / total
            for key, value in weights.items()
        }

    def _budget(self, context: Mapping[str, Any], available: float | None) -> float:
        value = available if available is not None else context.get("available_resources", 1.0)
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 1.0


priority_allocator = PriorityAllocator()


__all__ = [
    "PRIORITY_BUDGETS",
    "PriorityAllocator",
    "priority_allocator",
]
