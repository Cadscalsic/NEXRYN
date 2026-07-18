"""Capability resource cost contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CapabilityCostLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class CapabilityCostProfile:
    estimated_latency: str | float = CapabilityCostLevel.LOW.value
    estimated_memory_cost: str | float = CapabilityCostLevel.LOW.value
    estimated_cpu_cost: str | float = CapabilityCostLevel.LOW.value
    estimated_search_cost: str | float = CapabilityCostLevel.LOW.value
    estimated_reporting_cost: str | float = CapabilityCostLevel.LOW.value
    estimated_activation_cost: str | float = CapabilityCostLevel.LOW.value
    estimated_serialization_cost: str | float = CapabilityCostLevel.LOW.value

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


__all__ = ["CapabilityCostLevel", "CapabilityCostProfile"]
