"""Policy-aware cognitive budget allocation."""

from __future__ import annotations

import time

from runtime.resource_governance.cognitive_budget import CognitiveBudget
from runtime.resource_governance.execution_policy import ExecutionPolicy, ExecutionPolicyName
from runtime.resource_governance.task_profiler import TaskProfile


class BudgetAllocator:
    def allocate(
        self,
        task_profile: TaskProfile,
        execution_policy: ExecutionPolicy,
        execution_id: str = "runtime_execution",
        task_id: str = "unknown_task",
    ) -> CognitiveBudget:
        policy = execution_policy.name
        base = _policy_base(policy)
        multiplier = _complexity_multiplier(task_profile)
        return CognitiveBudget(
            execution_id=execution_id,
            task_id=task_id,
            policy=policy.value,
            max_wall_time_seconds=round(base["wall"] * multiplier, 3),
            max_active_compute_seconds=round(base["compute"] * multiplier, 3),
            max_reasoning_depth=max(1, int(base["depth"] * multiplier)),
            max_dependency_depth=max(1, int(base["dependency"] * multiplier)),
            max_active_routes=max(1, int(base["routes"] * multiplier)),
            max_hypotheses=max(1, int(base["hypotheses"] * multiplier)),
            max_candidates=max(1, int(base["candidates"] * multiplier)),
            max_retries=base["retries"],
            max_repairs=base["repairs"],
            max_escalations=base["escalations"],
            max_layer_activations=max(1, int(base["activations"] * multiplier)),
            max_memory_growth_bytes=int(base["memory"] * multiplier),
            max_report_cost_seconds=base["report"],
            max_post_success_seconds=base["post_success"],
            max_serialization_seconds=base["serialization"],
            max_maintenance_seconds=base["maintenance"],
            created_at=time.monotonic(),
        )


def _complexity_multiplier(profile: TaskProfile) -> float:
    if profile.task_complexity == "EXTREME":
        return 2.0
    if profile.task_complexity == "HIGH":
        return 1.5
    if profile.task_complexity == "MEDIUM":
        return 1.2
    return 1.0


def _policy_base(policy: ExecutionPolicyName) -> dict[str, float | int]:
    if policy == ExecutionPolicyName.LOW_LATENCY:
        return _base(8.0, 6.0, 2, 2, 2, 3, 3, 1, 1, 1, 8, 2_000_000, 0.4, 0.1, 0.2, 0.1)
    if policy == ExecutionPolicyName.MAX_ACCURACY:
        return _base(45.0, 36.0, 8, 5, 8, 14, 18, 3, 3, 3, 28, 16_000_000, 2.0, 0.3, 1.0, 0.5)
    if policy == ExecutionPolicyName.RESEARCH:
        return _base(90.0, 72.0, 10, 7, 12, 24, 30, 4, 4, 4, 40, 32_000_000, 4.0, 0.4, 2.0, 1.0)
    if policy == ExecutionPolicyName.DIAGNOSTIC:
        return _base(60.0, 36.0, 6, 5, 6, 12, 12, 2, 2, 2, 24, 12_000_000, 3.0, 0.2, 1.5, 0.5)
    if policy == ExecutionPolicyName.TRAINING:
        return _base(45.0, 30.0, 5, 4, 6, 10, 12, 2, 2, 2, 24, 16_000_000, 1.5, 0.25, 1.0, 0.75)
    return _base(30.0, 24.0, 4, 3, 5, 8, 10, 2, 2, 2, 20, 8_000_000, 1.0, 0.2, 0.6, 0.3)


def _base(wall, compute, depth, dependency, routes, hypotheses, candidates, retries, repairs, escalations, activations, memory, report, post_success, serialization, maintenance):
    return {
        "wall": wall,
        "compute": compute,
        "depth": depth,
        "dependency": dependency,
        "routes": routes,
        "hypotheses": hypotheses,
        "candidates": candidates,
        "retries": retries,
        "repairs": repairs,
        "escalations": escalations,
        "activations": activations,
        "memory": memory,
        "report": report,
        "post_success": post_success,
        "serialization": serialization,
        "maintenance": maintenance,
    }


__all__ = ["BudgetAllocator"]
