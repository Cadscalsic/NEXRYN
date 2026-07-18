"""Adapters for staged migration of legacy layers."""

from __future__ import annotations

from runtime.capability_architecture.activation_contract import ActivationContract, ActivationType
from runtime.capability_architecture.capability_contract import (
    CapabilityCategory,
    CapabilityContract,
    CapabilityLifecycleState,
)
from runtime.capability_architecture.health_contract import CapabilityHealthStatus, HealthContract
from runtime.capability_architecture.io_contract import InputContract, OutputContract
from runtime.capability_architecture.layer_descriptor import LayerDescriptor


class LegacyLayerAdapter:
    def adapt(
        self,
        layer_name: str,
        capability_name: str | None = None,
        category: CapabilityCategory = CapabilityCategory.COGNITIVE_REASONING,
    ) -> tuple[LayerDescriptor, CapabilityContract]:
        cap_name = capability_name or layer_name
        layer = LayerDescriptor(
            layer_id=f"legacy::{layer_name}",
            layer_name=layer_name,
            capabilities=(cap_name,),
            health_status=CapabilityHealthStatus.LEGACY,
            lifecycle_state=CapabilityLifecycleState.LEGACY,
            legacy_status="LEGACY",
            governance_state="ADAPTED",
        )
        capability = CapabilityContract(
            capability_id=f"legacy::{cap_name}",
            capability_name=cap_name,
            capability_version="legacy",
            owning_layer=layer_name,
            category=category,
            description=f"Legacy adapted capability for {layer_name}",
            activation_type=ActivationType.ON_DEMAND,
            input_contract=InputContract(optional_inputs=("legacy_context",)),
            output_contract=OutputContract(produced_outputs=("legacy_result",)),
            activation_contract=ActivationContract(activation_type=ActivationType.ON_DEMAND),
            health_contract=HealthContract(health_status=CapabilityHealthStatus.LEGACY),
            lifecycle_state=CapabilityLifecycleState.LEGACY,
            compatibility={"legacy_adapter": True},
        )
        return layer, capability


__all__ = ["LegacyLayerAdapter"]
