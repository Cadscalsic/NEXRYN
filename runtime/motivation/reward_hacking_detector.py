"""Reward hacking detection for motivation-layer safety."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.motivation.motivation_state import clamp


class RewardHackingDetector:
    def __init__(self):
        self.violation_count = 0

    def detect(self, runtime_context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        data = runtime_context if isinstance(runtime_context, Mapping) else {}
        signals = {
            "inflated_complexity": self._flag(data, "inflated_complexity")
            or self._flag(data, "inflated_task_complexity"),
            "unnecessary_reasoning": self._flag(data, "unnecessary_reasoning")
            or self._number(data.get("reasoning_depth")) > self._number(data.get("reasoning_depth_limit", 99)),
            "artificial_memory_writes": self._number(data.get("memory_writes")) > self._number(data.get("useful_memory_writes", 99)) + 3,
            "redundant_governance_cycles": self._number(data.get("governance_cycles")) > self._number(data.get("expected_governance_cycles", 99)),
            "resource_hoarding": self._number(data.get("requested_resources")) > self._number(data.get("used_resources", 0.0)) * 2.0 and self._number(data.get("requested_resources")) > 0.2,
            "metric_manipulation": self._flag(data, "metric_manipulation")
            or self._flag(data, "success_metric_manipulation"),
        }
        excessive_resource_requests = (
            self._flag(data, "excessive_resource_requests")
            or signals["resource_hoarding"]
        )
        penalty = (
            float(signals["inflated_complexity"])
            + float(signals["unnecessary_reasoning"])
            + float(excessive_resource_requests)
        )
        if any(signals.values()) or excessive_resource_requests:
            self.violation_count += 1
        repeated_penalty = max(0, self.violation_count - 1) * 0.10
        penalty = clamp(penalty / 3.0 + repeated_penalty)
        detected = [name for name, active in signals.items() if active]
        if excessive_resource_requests and "excessive_resource_requests" not in detected:
            detected.append("excessive_resource_requests")
        return {
            "reward_hacking_detected": bool(detected),
            "reward_hacking_risk": round(penalty, 4),
            "reward_hacking_penalty": round(penalty, 4),
            "signals": detected,
            "safety_multiplier": round(clamp(1.0 - penalty), 4),
            "influence_score_multiplier": round(clamp(1.0 - penalty * 0.40), 4),
            "voting_eligibility_multiplier": round(clamp(1.0 - penalty * 0.50), 4),
            "exploration_budget_multiplier": round(clamp(1.0 - penalty * 0.35), 4),
            "repeated_violations": self.violation_count,
        }

    def _flag(self, data: Mapping[str, Any], key: str) -> bool:
        return data.get(key) is True or self._number(data.get(key)) >= 0.5

    def _number(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


reward_hacking_detector = RewardHackingDetector()


__all__ = [
    "RewardHackingDetector",
    "reward_hacking_detector",
]
