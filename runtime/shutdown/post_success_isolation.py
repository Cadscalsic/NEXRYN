"""Post-success isolation policy."""

from __future__ import annotations

from copy import deepcopy


DISABLED_OPERATIONS = {
    "context_discovery",
    "concept_promotion",
    "truth_validation",
    "governance_reanalysis",
    "architecture_scans",
    "strategy_search",
    "deep_reasoning",
}

ALLOWED_OPERATIONS = {
    "memory_commit",
    "reward_commit",
    "minimal_reporting",
    "resource_cleanup",
    "shutdown",
}

SUCCESS_LOCK_KEYS = (
    "task_outcome",
    "reward_state",
    "learning_state",
    "evaluation_metrics",
)


class PostSuccessIsolation:
    """Freezes success data and blocks non-essential cognition."""

    def __init__(self) -> None:
        self.enabled = False
        self.success_lock: dict = {}

    def activate(self, context: dict | None) -> dict:
        context = context if isinstance(context, dict) else {}
        self.enabled = True
        self.success_lock = self.freeze_success(context)
        context["post_success_isolation"] = {
            "enabled": True,
            "disabled_operations": sorted(DISABLED_OPERATIONS),
            "allowed_operations": sorted(ALLOWED_OPERATIONS),
            "success_lock": deepcopy(self.success_lock),
        }
        return context

    def freeze_success(self, context: dict) -> dict:
        evaluation_result = dict(context.get("evaluation_result", {}) or {})
        return {
            "task_outcome": deepcopy(
                context.get("task_outcome")
                or context.get("minimal_success_record")
                or evaluation_result
            ),
            "reward_state": deepcopy(context.get("reward_state", {})),
            "learning_state": deepcopy(context.get("learning_state", {})),
            "evaluation_metrics": deepcopy(context.get("evaluation_metrics", {})),
        }

    def operation_allowed(self, operation: str) -> bool:
        if not self.enabled:
            return True
        return operation in ALLOWED_OPERATIONS

    def build_report(self) -> dict:
        return {
            "enabled": self.enabled,
            "disabled_operations": sorted(DISABLED_OPERATIONS),
            "allowed_operations": sorted(ALLOWED_OPERATIONS),
            "success_lock": deepcopy(self.success_lock),
        }
