"""Capability discovery APIs."""

from __future__ import annotations

from runtime.capability_architecture.capability_registry import CapabilityRegistry
from runtime.capability_architecture.layer_registry import LayerRegistry


class CapabilityDiscoveryEngine:
    def __init__(self, capability_registry: CapabilityRegistry, layer_registry: LayerRegistry):
        self.capability_registry = capability_registry
        self.layer_registry = layer_registry

    def get_capability(self, capability_name: str):
        return self.capability_registry.get(capability_name)

    def get_layer(self, layer_name: str):
        return self.layer_registry.get(layer_name)

    def find_capabilities_by_category(self, category: str):
        return self.capability_registry.by_category(category)

    def find_capabilities_by_signal(self, signal: str):
        return self.capability_registry.by_signal(signal)

    def find_capabilities_by_policy(self, policy):
        return self.capability_registry.by_policy(policy)

    def find_capabilities_by_cost(self, cost_level: str):
        return [
            item for item in self.capability_registry.all()
            if str(item.cost_profile.estimated_activation_cost) == str(cost_level)
        ]

    def find_capabilities_by_activation_type(self, activation_type: str):
        return self.capability_registry.by_activation_type(activation_type)

    def find_dependencies(self, capability_name: str):
        return self.capability_registry.dependencies_for(capability_name)

    def find_capability_owner(self, capability_name: str):
        return self.capability_registry.owner(capability_name)


__all__ = ["CapabilityDiscoveryEngine"]
