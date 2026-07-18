"""Capability architecture facade for governor visibility."""

from __future__ import annotations

from typing import Any

from runtime.capability_architecture.capability_contract import CapabilityContract
from runtime.capability_architecture.capability_discovery_engine import CapabilityDiscoveryEngine
from runtime.capability_architecture.capability_lifecycle_manager import CapabilityLifecycleManager
from runtime.capability_architecture.capability_registry import CapabilityRegistry
from runtime.capability_architecture.layer_descriptor import LayerDescriptor
from runtime.capability_architecture.layer_registry import LayerRegistry
from runtime.capability_architecture.legacy_layer_adapter import LegacyLayerAdapter


class CapabilityGovernor:
    def __init__(
        self,
        capability_registry: CapabilityRegistry | None = None,
        layer_registry: LayerRegistry | None = None,
    ):
        self.capability_registry = capability_registry or CapabilityRegistry()
        self.layer_registry = layer_registry or LayerRegistry()
        self.discovery = CapabilityDiscoveryEngine(self.capability_registry, self.layer_registry)
        self.lifecycle_manager = CapabilityLifecycleManager()
        self.legacy_adapter = LegacyLayerAdapter()
        self.governor_visibility_status = "INCOMPLETE"

    def register_layer(self, descriptor: LayerDescriptor) -> bool:
        return self.layer_registry.register(descriptor)

    def register_capability(self, contract: CapabilityContract):
        result = self.capability_registry.register(contract)
        self._refresh_visibility()
        return result

    def register_legacy_layer(self, layer_name: str, capability_name: str | None = None):
        layer, capability = self.legacy_adapter.adapt(layer_name, capability_name)
        self.register_layer(layer)
        return self.register_capability(capability)

    def can_activate_capability(
        self,
        capability_name: str,
        policy="BALANCED",
    ) -> bool:
        contract = self.capability_registry.get(capability_name)
        if contract is None:
            return False
        if not contract.allows_policy(policy):
            return False
        if not contract.health_contract.activatable():
            return False
        if contract.lifecycle_state.value in {"DEPRECATED", "DISABLED", "FAILED", "UNREGISTERED"}:
            return False
        return True

    def boot(self, layer_contracts: list[tuple[LayerDescriptor, list[CapabilityContract]]]) -> dict[str, Any]:
        for layer, capabilities in layer_contracts:
            self.register_layer(layer)
            for capability in capabilities:
                self.register_capability(capability)
        self._refresh_visibility()
        return self.build_report()

    def build_report(self) -> dict[str, Any]:
        health_summary: dict[str, int] = {}
        categories: dict[str, int] = {}
        permissions: dict[str, int] = {}
        for capability in self.capability_registry.all():
            health = capability.health_contract.health_status.value
            health_summary[health] = health_summary.get(health, 0) + 1
            categories[capability.category.value] = categories.get(capability.category.value, 0) + 1
            for policy in capability.policy_permissions:
                policy_value = getattr(policy, "value", str(policy))
                permissions[policy_value] = permissions.get(policy_value, 0) + 1
        dependency_graph_valid = self.capability_registry.dependency_validation_failures == 0
        return {
            "CAPABILITY_ARCHITECTURE_REPORT": True,
            "registered_layers": len(self.layer_registry.all()),
            "registered_capabilities": len(self.capability_registry.all()),
            "capability_categories": categories,
            "ownership_conflicts": len(self.capability_registry.ownership_conflicts),
            "legacy_layers": len(self.layer_registry.legacy_layers()),
            "dependency_graph_status": "VALID" if dependency_graph_valid else "INVALID",
            "registration_failures": len(self.capability_registry.registration_failures) + len(self.layer_registry.registration_failures),
            "compatibility_status": "VALID" if self.capability_registry.compatibility_failures == 0 else "INVALID",
            "health_summary": health_summary,
            "discovery_status": "OPERATIONAL",
            "governor_visibility_status": self.governor_visibility_status,
            "observability_metrics": {
                "registered_capability_count": len(self.capability_registry.all()),
                "registered_layer_count": len(self.layer_registry.all()),
                "legacy_layer_count": len(self.layer_registry.legacy_layers()),
                "registration_failure_count": len(self.capability_registry.registration_failures) + len(self.layer_registry.registration_failures),
                "ownership_conflict_count": len(self.capability_registry.ownership_conflicts),
                "dependency_validation_failures": self.capability_registry.dependency_validation_failures,
                "compatibility_failures": self.capability_registry.compatibility_failures,
                "capability_health_summary": health_summary,
                "activation_contract_count": len(self.capability_registry.all()),
                "policy_permission_summary": permissions,
                "registry_status": self.capability_registry.registry_status,
            },
        }

    def render_report(self) -> str:
        report = self.build_report()
        return "\n".join([
            "==================================================",
            "CAPABILITY ARCHITECTURE REPORT",
            "==================================================",
            "",
            "Registered Layers:",
            str(report["registered_layers"]),
            "",
            "Registered Capabilities:",
            str(report["registered_capabilities"]),
            "",
            "Ownership Conflicts:",
            str(report["ownership_conflicts"]),
            "",
            "Legacy Layers:",
            str(report["legacy_layers"]),
            "",
            "Dependency Graph:",
            report["dependency_graph_status"],
            "",
            "Capability Registry:",
            report["observability_metrics"]["registry_status"],
            "",
            "Governor Visibility:",
            report["governor_visibility_status"],
        ])

    def _refresh_visibility(self) -> None:
        self.governor_visibility_status = (
            "COMPLETE" if self.capability_registry.all() and self.layer_registry.all() else "INCOMPLETE"
        )


__all__ = ["CapabilityGovernor"]
