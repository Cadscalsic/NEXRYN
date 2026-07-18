"""Canonical capability registry."""

from __future__ import annotations

from typing import Any

from runtime.capability_architecture.capability_contract import (
    CapabilityContract,
    CapabilityLifecycleState,
)
from runtime.capability_architecture.capability_validator import (
    CapabilityValidationResult,
    CapabilityValidator,
)


class CapabilityRegistry:
    def __init__(self, validator: CapabilityValidator | None = None):
        self.validator = validator or CapabilityValidator()
        self._capabilities: dict[str, CapabilityContract] = {}
        self._owners: dict[str, str] = {}
        self.registration_failures: list[dict[str, Any]] = []
        self.ownership_conflicts: list[dict[str, str]] = []
        self.dependency_validation_failures = 0
        self.compatibility_failures = 0
        self.registry_status = "OPERATIONAL"

    def register(self, contract: CapabilityContract) -> CapabilityValidationResult:
        existing_owner = self._owners.get(contract.capability_name)
        result = self.validator.validate(
            contract,
            existing_owner=existing_owner,
            known_capabilities=set(self._capabilities),
        )
        if not result.valid:
            failure = {
                "capability_name": contract.capability_name,
                "owning_layer": contract.owning_layer,
                "errors": list(result.errors),
            }
            self.registration_failures.append(failure)
            if "OWNERSHIP_CONFLICT" in result.errors:
                self.ownership_conflicts.append({
                    "capability_name": contract.capability_name,
                    "existing_owner": existing_owner or "",
                    "new_owner": contract.owning_layer,
                })
            if "DEPENDENCY_NOT_REGISTERED" in result.errors:
                self.dependency_validation_failures += 1
            if "HEALTH_NOT_ACTIVATABLE" in result.errors:
                self.compatibility_failures += 1
            return result
        contract.lifecycle_state = CapabilityLifecycleState.REGISTERED
        contract.registration_status = "REGISTERED"
        self._capabilities[contract.capability_name] = contract
        self._owners[contract.capability_name] = contract.owning_layer
        return result

    def get(self, capability_name: str) -> CapabilityContract | None:
        return self._capabilities.get(str(capability_name))

    def owner(self, capability_name: str) -> str | None:
        return self._owners.get(str(capability_name))

    def all(self) -> list[CapabilityContract]:
        return list(self._capabilities.values())

    def by_category(self, category: str) -> list[CapabilityContract]:
        return [item for item in self.all() if item.category.value == str(category)]

    def by_signal(self, signal: str) -> list[CapabilityContract]:
        return [
            item for item in self.all()
            if str(signal) in item.activation_contract.activation_signals
        ]

    def by_policy(self, policy) -> list[CapabilityContract]:
        return [item for item in self.all() if item.allows_policy(policy)]

    def by_activation_type(self, activation_type: str) -> list[CapabilityContract]:
        return [
            item for item in self.all()
            if item.activation_type.value == str(activation_type)
        ]

    def dependencies_for(self, capability_name: str) -> tuple[str, ...]:
        contract = self.get(capability_name)
        return contract.dependency_contract.all_required_capabilities() if contract else ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "capabilities": {
                item.capability_name: item.as_dict()
                for item in self.all()
            },
            "owners": dict(self._owners),
            "registration_failures": list(self.registration_failures),
            "ownership_conflicts": list(self.ownership_conflicts),
            "dependency_validation_failures": self.dependency_validation_failures,
            "compatibility_failures": self.compatibility_failures,
            "registry_status": self.registry_status,
        }


__all__ = ["CapabilityRegistry"]
