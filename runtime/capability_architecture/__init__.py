"""Canonical capability architecture."""

from runtime.capability_architecture.activation_contract import (
    ActivationContract,
    ActivationType,
)
from runtime.capability_architecture.capability_contract import (
    CapabilityCategory,
    CapabilityContract,
    CapabilityCriticality,
    CapabilityLifecycleState,
    ExecutionPhase,
    IdempotencyContract,
    PostProcessingCategory,
)
from runtime.capability_architecture.capability_cost_profile import (
    CapabilityCostLevel,
    CapabilityCostProfile,
)
from runtime.capability_architecture.capability_descriptor import CapabilityDescriptor
from runtime.capability_architecture.capability_discovery_engine import (
    CapabilityDiscoveryEngine,
)
from runtime.capability_architecture.capability_governor import CapabilityGovernor
from runtime.capability_architecture.capability_lifecycle_manager import (
    CapabilityLifecycleManager,
)
from runtime.capability_architecture.capability_registry import CapabilityRegistry
from runtime.capability_architecture.capability_validator import (
    CapabilityValidationResult,
    CapabilityValidator,
)
from runtime.capability_architecture.dependency_contract import DependencyContract
from runtime.capability_architecture.health_contract import (
    CapabilityHealthStatus,
    HealthContract,
)
from runtime.capability_architecture.io_contract import InputContract, OutputContract
from runtime.capability_architecture.layer_descriptor import LayerDescriptor
from runtime.capability_architecture.layer_registry import LayerRegistry
from runtime.capability_architecture.legacy_layer_adapter import LegacyLayerAdapter


__all__ = [
    "ActivationContract",
    "ActivationType",
    "CapabilityCategory",
    "CapabilityContract",
    "CapabilityCostLevel",
    "CapabilityCostProfile",
    "CapabilityCriticality",
    "CapabilityDescriptor",
    "CapabilityDiscoveryEngine",
    "CapabilityGovernor",
    "CapabilityHealthStatus",
    "CapabilityLifecycleManager",
    "CapabilityLifecycleState",
    "CapabilityRegistry",
    "CapabilityValidationResult",
    "CapabilityValidator",
    "DependencyContract",
    "ExecutionPhase",
    "HealthContract",
    "IdempotencyContract",
    "InputContract",
    "LayerDescriptor",
    "LayerRegistry",
    "LegacyLayerAdapter",
    "OutputContract",
    "PostProcessingCategory",
]
