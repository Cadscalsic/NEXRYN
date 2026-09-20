"""Serializable capability descriptor helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.capability_architecture.capability_contract import CapabilityContract


@dataclass(frozen=True)
class CapabilityDescriptor:
    contract: CapabilityContract

    @property
    def capability_name(self) -> str:
        return self.contract.capability_name

    @property
    def owning_layer(self) -> str:
        return self.contract.owning_layer

    def as_dict(self) -> dict[str, Any]:
        return self.contract.as_dict()


__all__ = ["CapabilityDescriptor"]
