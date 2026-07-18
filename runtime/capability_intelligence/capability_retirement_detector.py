"""Capability retirement recommendations."""

from __future__ import annotations

from enum import Enum

from runtime.capability_intelligence.capability_effectiveness_tracker import CapabilityEffectivenessRecord
from runtime.capability_intelligence.capability_usage_statistics import CapabilityUsageRecord


class CapabilityRetirementState(str, Enum):
    ACTIVE = "ACTIVE"
    LOW_USAGE = "LOW_USAGE"
    LEGACY = "LEGACY"
    DEPRECATED = "DEPRECATED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class CapabilityRetirementDetector:
    def evaluate(
        self,
        capability_name: str,
        usage: CapabilityUsageRecord | None = None,
        effectiveness: CapabilityEffectivenessRecord | None = None,
        lifecycle_state: str = "REGISTERED",
        legacy: bool = False,
    ) -> dict[str, str]:
        if lifecycle_state == "DEPRECATED":
            state = CapabilityRetirementState.DEPRECATED
            reason = "capability_deprecated"
        elif legacy:
            state = CapabilityRetirementState.LEGACY
            reason = "legacy_capability"
        elif usage is None or usage.activation_frequency == 0:
            state = CapabilityRetirementState.LOW_USAGE
            reason = "no_usage_history"
        elif effectiveness and effectiveness.failed_activations > effectiveness.successful_activations:
            state = CapabilityRetirementState.REVIEW_REQUIRED
            reason = "failures_exceed_successes"
        elif effectiveness and effectiveness.score() <= 0:
            state = CapabilityRetirementState.REVIEW_REQUIRED
            reason = "low_or_negative_effectiveness"
        else:
            state = CapabilityRetirementState.ACTIVE
            reason = "capability_currently_useful"
        return {
            "capability_name": capability_name,
            "retirement_state": state.value,
            "reason": reason,
        }


__all__ = ["CapabilityRetirementDetector", "CapabilityRetirementState"]
