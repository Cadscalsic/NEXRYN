"""Cognitive budget assignment and compliance checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass
class TaskBudget:
    max_runtime: float
    max_reasoning_depth: int
    max_active_routes: int
    max_governance_cycles: int
    max_context_expansions: int
    assigned_by: str = "world_governance_cognitive_economy"
    self_assigned: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CognitiveBudgetController:
    def assign_budget(
        self,
        task_profile: Mapping[str, Any] | None = None,
        available_resources: float | None = None,
    ) -> TaskBudget:
        profile = dict(task_profile or {})
        complexity = self._number(profile.get("complexity", profile.get("task_complexity", 0.5)))
        resources = self._number(available_resources if available_resources is not None else profile.get("available_resources", 1.0))
        scale = max(0.25, min(1.0, (complexity * 0.7 + resources * 0.3)))
        return TaskBudget(
            max_runtime=round(2.0 + 8.0 * scale, 4),
            max_reasoning_depth=max(1, int(2 + 6 * scale)),
            max_active_routes=max(1, int(2 + 5 * scale)),
            max_governance_cycles=max(1, int(1 + 3 * scale)),
            max_context_expansions=max(1, int(2 + 6 * scale)),
        )

    def evaluate_usage(
        self,
        budget: TaskBudget | Mapping[str, Any],
        usage: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        budget_data = budget.as_dict() if hasattr(budget, "as_dict") else dict(budget)
        usage_data = dict(usage or {})
        ratios = {}
        exceeded = []
        limit_keys = (
            "max_runtime",
            "max_reasoning_depth",
            "max_active_routes",
            "max_governance_cycles",
            "max_context_expansions",
        )
        for key in limit_keys:
            limit = budget_data.get(key, 0.0)
            used = self._number(usage_data.get(key.replace("max_", ""), usage_data.get(key, 0.0)))
            limit_value = max(0.0001, self._number(limit))
            ratios[key] = used / limit_value
            if used > limit_value:
                exceeded.append(key)
        average_utilization = sum(ratios.values()) / max(1, len(ratios))
        compliant = not exceeded
        return {
            "budget": budget_data,
            "usage": usage_data,
            "budget_compliance": compliant,
            "exceeded_limits": exceeded,
            "average_budget_utilization": average_utilization,
            "actions": (
                ["increase_efficiency_bonus", "increase_trust_score"]
                if compliant and average_utilization <= 0.85
                else ["reduce_reward_score", "decrease_trust_score", "trigger_efficiency_review"]
            ),
        }

    def _number(self, value: Any) -> float:
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return 0.0


cognitive_budget_controller = CognitiveBudgetController()


__all__ = [
    "TaskBudget",
    "CognitiveBudgetController",
    "cognitive_budget_controller",
]
