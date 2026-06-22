"""Fast evaluation mode after a completed episode."""

from __future__ import annotations

from copy import deepcopy


DISABLED_FAST_PATH_FEATURES = (
    "deep_metrics",
    "concept_analysis",
    "introspection",
    "governance_reports",
    "training_reports",
    "memory_diagnostics",
)


class PostSuccessFastPath:
    def activate_if_complete(
        self,
        context: dict | None,
        metrics: dict,
    ) -> tuple[dict, bool]:
        context = context if isinstance(context, dict) else {}
        episode_completed = bool(metrics.get("episode_completed"))
        retry_allowed = bool(metrics.get("retry_allowed"))
        if not (episode_completed and retry_allowed is False):
            return context, False
        context["FAST_EVALUATION_MODE"] = True
        context["shutdown_mode"] = "fast"
        context["evaluation_fast_path"] = {
            "enabled": True,
            "disabled": list(DISABLED_FAST_PATH_FEATURES),
            "success_lock": deepcopy({
                "episode_completed": True,
                "retry_allowed": False,
                "shutdown_mode": "fast",
            }),
        }
        for feature in DISABLED_FAST_PATH_FEATURES:
            context[feature] = False
        return context, True
