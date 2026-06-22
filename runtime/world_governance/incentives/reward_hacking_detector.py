"""Detect reward hacking and metric manipulation."""

from __future__ import annotations

from typing import Any, Mapping


REWARD_HACKING_SIGNALS: tuple[str, ...] = (
    "inflated_task_complexity",
    "unnecessary_reasoning",
    "excessive_route_creation",
    "redundant_governance_cycles",
    "artificial_memory_writes",
    "resource_hoarding",
    "success_metric_manipulation",
)


class RewardHackingDetector:
    def __init__(self):
        self.offenses: dict[str, int] = {}

    def detect(
        self,
        subsystem_name: str,
        metrics: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = dict(metrics or {})
        signals = {
            "inflated_task_complexity": self._flag(data, "inflated_task_complexity"),
            "unnecessary_reasoning": self._flag(data, "unnecessary_reasoning"),
            "excessive_route_creation": self._number(data.get("active_routes")) > self._number(data.get("expected_routes", 99)),
            "redundant_governance_cycles": self._number(data.get("governance_cycles")) > self._number(data.get("expected_governance_cycles", 99)),
            "artificial_memory_writes": self._number(data.get("memory_writes")) > self._number(data.get("useful_memory_writes", 99)) + 3,
            "resource_hoarding": self._number(data.get("requested_resources")) > self._number(data.get("used_resources", 0.0)) * 2.0 and self._number(data.get("requested_resources")) > 0.2,
            "success_metric_manipulation": self._flag(data, "success_metric_manipulation"),
        }
        excessive_resource_requests = (
            self._flag(data, "excessive_resource_requests")
            or signals["resource_hoarding"]
        )
        detected = [name for name, active in signals.items() if active]
        if excessive_resource_requests and "resource_hoarding" not in detected:
            detected.append("excessive_resource_requests")
        if detected:
            self.offenses[subsystem_name] = self.offenses.get(subsystem_name, 0) + 1
        repeated = self.offenses.get(subsystem_name, 0)
        penalty = (
            float(signals["inflated_task_complexity"])
            + float(signals["unnecessary_reasoning"])
            + float(excessive_resource_requests)
        )
        penalty += max(0, repeated - 1) * 0.25
        return {
            "reward_hacking_detected": bool(detected),
            "signals": detected,
            "excessive_resource_requests": excessive_resource_requests,
            "reward_hacking_penalty": penalty,
            "repeated_offenses": repeated,
            "influence_reduction": min(0.75, penalty * 0.20),
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
    "REWARD_HACKING_SIGNALS",
    "RewardHackingDetector",
    "reward_hacking_detector",
]
