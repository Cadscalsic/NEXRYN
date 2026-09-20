"""Canonical layer descriptor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.capability_architecture.activation_contract import ActivationContract
from runtime.capability_architecture.capability_cost_profile import CapabilityCostProfile
from runtime.capability_architecture.capability_contract import CapabilityLifecycleState
from runtime.capability_architecture.health_contract import CapabilityHealthStatus


@dataclass
class LayerDescriptor:
    layer_id: str
    layer_name: str
    layer_version: str = "1.0"
    capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    cost_profile: CapabilityCostProfile = field(default_factory=CapabilityCostProfile)
    health_status: CapabilityHealthStatus = CapabilityHealthStatus.HEALTHY
    activation_rules: tuple[ActivationContract, ...] = ()
    execution_permissions: tuple[str, ...] = ()
    ownership_information: dict[str, Any] = field(default_factory=dict)
    supported_policies: tuple[str, ...] = (
        "LOW_LATENCY",
        "BALANCED",
        "MAX_ACCURACY",
        "RESEARCH",
        "DIAGNOSTIC",
        "TRAINING",
    )
    lifecycle_state: CapabilityLifecycleState = CapabilityLifecycleState.REGISTERING
    legacy_status: str = "NATIVE"
    governance_state: str = "GOVERNED"

    def as_dict(self) -> dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "layer_name": self.layer_name,
            "layer_version": self.layer_version,
            "capabilities": list(self.capabilities),
            "dependencies": list(self.dependencies),
            "cost_profile": self.cost_profile.as_dict(),
            "health_status": self.health_status.value,
            "activation_rules": [rule.as_dict() for rule in self.activation_rules],
            "execution_permissions": list(self.execution_permissions),
            "ownership_information": dict(self.ownership_information),
            "supported_policies": [getattr(policy, "value", str(policy)) for policy in self.supported_policies],
            "lifecycle_state": self.lifecycle_state.value,
            "legacy_status": self.legacy_status,
            "governance_state": self.governance_state,
        }


__all__ = ["LayerDescriptor"]
