"""Policy recommendation intelligence."""

from __future__ import annotations

class PolicyRecommendationEngine:
    def recommend(self, task_family: str, task_complexity: str = "LOW") -> dict[str, str]:
        if task_family in {"color_mapping", "object_tracking"} and task_complexity == "LOW":
            policy = "LOW_LATENCY"
            reason = "simple_family_low_complexity"
        elif task_family in {"topology", "multi_step_transformations", "gravity"} or task_complexity in {"HIGH", "EXTREME"}:
            policy = "MAX_ACCURACY"
            reason = "complex_family_or_high_complexity"
        elif task_family == "training":
            policy = "TRAINING"
            reason = "training_family"
        else:
            policy = "BALANCED"
            reason = "balanced_default"
        return {"recommended_policy": policy, "reason": reason}


__all__ = ["PolicyRecommendationEngine"]
