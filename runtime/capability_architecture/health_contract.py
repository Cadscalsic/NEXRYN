"""Capability health contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CapabilityHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    INCOMPATIBLE = "INCOMPATIBLE"
    BLOCKED = "BLOCKED"
    DISABLED = "DISABLED"
    LEGACY = "LEGACY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class HealthContract:
    health_status: CapabilityHealthStatus = CapabilityHealthStatus.HEALTHY
    registration_health: CapabilityHealthStatus = CapabilityHealthStatus.HEALTHY
    dependency_health: CapabilityHealthStatus = CapabilityHealthStatus.HEALTHY
    compatibility_health: CapabilityHealthStatus = CapabilityHealthStatus.HEALTHY
    activation_health: CapabilityHealthStatus = CapabilityHealthStatus.HEALTHY
    execution_health: CapabilityHealthStatus = CapabilityHealthStatus.HEALTHY

    def activatable(self) -> bool:
        blocked = {
            CapabilityHealthStatus.INCOMPATIBLE,
            CapabilityHealthStatus.BLOCKED,
            CapabilityHealthStatus.DISABLED,
        }
        return not {
            self.health_status,
            self.registration_health,
            self.dependency_health,
            self.compatibility_health,
            self.activation_health,
            self.execution_health,
        }.intersection(blocked)

    def as_dict(self) -> dict[str, Any]:
        return {
            "health_status": self.health_status.value,
            "registration_health": self.registration_health.value,
            "dependency_health": self.dependency_health.value,
            "compatibility_health": self.compatibility_health.value,
            "activation_health": self.activation_health.value,
            "execution_health": self.execution_health.value,
        }


__all__ = ["CapabilityHealthStatus", "HealthContract"]
