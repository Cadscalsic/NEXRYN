"""Capability recommendation and prioritization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CapabilityRecommendationState(str, Enum):
    RECOMMENDED = "RECOMMENDED"
    OPTIONAL = "OPTIONAL"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"
    TASK_RECOMMENDED = "TASK_RECOMMENDED"
    TASK_OPTIONAL = "TASK_OPTIONAL"
    POST_PROCESSING_REQUIRED = "POST_PROCESSING_REQUIRED"
    POST_PROCESSING_BOUNDED = "POST_PROCESSING_BOUNDED"
    MAINTENANCE_DEFERRED = "MAINTENANCE_DEFERRED"
    MAINTENANCE_CHANGE_TRIGGERED = "MAINTENANCE_CHANGE_TRIGGERED"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    AVOID = "AVOID"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CapabilityRecommendation:
    capability_name: str
    recommendation: CapabilityRecommendationState
    priority: float
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_name": self.capability_name,
            "recommendation": self.recommendation.value,
            "priority": self.priority,
            "reason": self.reason,
        }


class CapabilityRecommendationEngine:
    def recommend(
        self,
        candidates: list[str],
        expected_capabilities: set[str],
        optional_capabilities: set[str],
        effectiveness_scores: dict[str, float],
        cost_predictions: dict[str, dict[str, Any]],
        policy_allowed: set[str] | None = None,
    ) -> list[CapabilityRecommendation]:
        allowed = policy_allowed or set(candidates)
        recommendations = []
        for capability in candidates:
            score = effectiveness_scores.get(capability, 0.0)
            cost = cost_predictions.get(capability, {})
            if capability not in allowed:
                state, reason, priority = CapabilityRecommendationState.AVOID, "policy_blocked", -1.0
            elif capability in expected_capabilities:
                state, reason, priority = CapabilityRecommendationState.RECOMMENDED, "task_profile_expected_capability", 1.0 + score
            elif capability in optional_capabilities:
                state, reason, priority = CapabilityRecommendationState.OPTIONAL, "task_profile_optional_capability", 0.5 + score
            elif cost.get("expected_latency") == "UNKNOWN" and score == 0.0:
                state, reason, priority = CapabilityRecommendationState.UNKNOWN, "insufficient_history", 0.0
            elif score < 0:
                state, reason, priority = CapabilityRecommendationState.NOT_RECOMMENDED, "negative_effectiveness", score
            else:
                state, reason, priority = CapabilityRecommendationState.OPTIONAL, "historical_support", score
            recommendations.append(CapabilityRecommendation(capability, state, round(priority, 4), reason))
        return sorted(recommendations, key=lambda item: item.priority, reverse=True)


__all__ = [
    "CapabilityRecommendation",
    "CapabilityRecommendationEngine",
    "CapabilityRecommendationState",
]
