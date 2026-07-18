"""Canonical capability contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from runtime.capability_architecture.activation_contract import ActivationContract, ActivationType
from runtime.capability_architecture.capability_cost_profile import CapabilityCostProfile
from runtime.capability_architecture.dependency_contract import DependencyContract
from runtime.capability_architecture.health_contract import HealthContract
from runtime.capability_architecture.io_contract import InputContract, OutputContract


class CapabilityCategory(str, Enum):
    COGNITIVE_REASONING = "COGNITIVE_REASONING"
    TRANSFORMATION = "TRANSFORMATION"
    PROGRAM_SYNTHESIS = "PROGRAM_SYNTHESIS"
    COMPILATION = "COMPILATION"
    EXECUTION = "EXECUTION"
    VALIDATION = "VALIDATION"
    MEMORY = "MEMORY"
    GOVERNANCE = "GOVERNANCE"
    MAINTENANCE = "MAINTENANCE"
    REPORTING = "REPORTING"
    PERSISTENCE = "PERSISTENCE"
    DIAGNOSTIC = "DIAGNOSTIC"
    RESOURCE_GOVERNANCE = "RESOURCE_GOVERNANCE"
    LEARNING = "LEARNING"
    TRAINING = "TRAINING"
    UTILITY = "UTILITY"
    SAFETY = "SAFETY"


class CapabilityLifecycleState(str, Enum):
    REGISTERING = "REGISTERING"
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEFERRED = "DEFERRED"
    COMPLETED = "COMPLETED"
    LEGACY = "LEGACY"
    DEPRECATED = "DEPRECATED"
    DISABLED = "DISABLED"
    FAILED = "FAILED"
    UNREGISTERED = "UNREGISTERED"


class CapabilityCriticality(str, Enum):
    MANDATORY = "MANDATORY"
    IMPORTANT = "IMPORTANT"
    OPTIONAL = "OPTIONAL"
    DEFERABLE = "DEFERABLE"
    NON_CRITICAL = "NON_CRITICAL"


class ExecutionPhase(str, Enum):
    PRE_EXECUTION = "PRE_EXECUTION"
    TASK_EXECUTION = "TASK_EXECUTION"
    EVALUATION = "EVALUATION"
    POST_PROCESSING = "POST_PROCESSING"
    MAINTENANCE = "MAINTENANCE"
    DIAGNOSTIC = "DIAGNOSTIC"


class PostProcessingCategory(str, Enum):
    CRITICAL_SYNC = "CRITICAL_SYNC"
    BOUNDED_SYNC = "BOUNDED_SYNC"
    DEFERRED = "DEFERRED"
    CHANGE_TRIGGERED = "CHANGE_TRIGGERED"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    PROHIBITED_AFTER_TERMINAL = "PROHIBITED_AFTER_TERMINAL"


class IdempotencyContract(str, Enum):
    IDEMPOTENT = "IDEMPOTENT"
    IDEMPOTENT_WITH_KEY = "IDEMPOTENT_WITH_KEY"
    NON_IDEMPOTENT = "NON_IDEMPOTENT"
    UNKNOWN = "UNKNOWN"


@dataclass
class CapabilityContract:
    capability_id: str
    capability_name: str
    capability_version: str
    owning_layer: str
    category: CapabilityCategory
    description: str = ""
    execution_category: str = "COGNITIVE_REASONING"
    activation_type: ActivationType = ActivationType.ON_DEMAND
    cost_profile: CapabilityCostProfile = field(default_factory=CapabilityCostProfile)
    dependency_contract: DependencyContract = field(default_factory=DependencyContract)
    input_contract: InputContract = field(default_factory=InputContract)
    output_contract: OutputContract = field(default_factory=OutputContract)
    activation_contract: ActivationContract = field(default_factory=ActivationContract)
    health_contract: HealthContract = field(default_factory=HealthContract)
    policy_permissions: tuple[str, ...] = (
        "LOW_LATENCY",
        "BALANCED",
        "MAX_ACCURACY",
        "RESEARCH",
        "DIAGNOSTIC",
        "TRAINING",
    )
    deferability: str = "DEFERABLE"
    criticality: CapabilityCriticality = CapabilityCriticality.OPTIONAL
    compatibility: dict[str, Any] = field(default_factory=dict)
    lifecycle_state: CapabilityLifecycleState = CapabilityLifecycleState.REGISTERING
    registration_status: str = "PENDING"
    governance_status: str = "GOVERNED"
    execution_phase: ExecutionPhase = ExecutionPhase.TASK_EXECUTION
    secondary_phases: tuple[ExecutionPhase, ...] = ()
    post_processing_category: PostProcessingCategory = PostProcessingCategory.DEFERRED
    blocks_result_availability: bool = False
    synchronous_allowed: bool = False
    maximum_synchronous_duration: float = 0.0
    maximum_serialized_bytes: int = 0
    maximum_objects_visited: int = 0
    maximum_registry_scans: int = 0
    trigger_conditions: tuple[str, ...] = ()
    required_state_changes: tuple[str, ...] = ()
    idempotency_contract: IdempotencyContract = IdempotencyContract.IDEMPOTENT_WITH_KEY
    result_dependency: bool = False
    maintenance_priority: str = "MEDIUM"
    critical_completion_required: bool = False
    safe_to_skip: bool = True
    diagnostic_only: bool = False
    change_triggered: bool = False

    def allows_policy(self, policy) -> bool:
        policy_value = _policy_value(policy)
        return (
            policy_value in {_policy_value(item) for item in self.policy_permissions}
            and self.activation_contract.allows_policy(policy)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "capability_name": self.capability_name,
            "capability_version": self.capability_version,
            "owning_layer": self.owning_layer,
            "category": self.category.value,
            "description": self.description,
            "execution_category": getattr(self.execution_category, "value", str(self.execution_category)),
            "activation_type": self.activation_type.value,
            "cost_profile": self.cost_profile.as_dict(),
            "dependency_contract": self.dependency_contract.as_dict(),
            "input_contract": self.input_contract.as_dict(),
            "output_contract": self.output_contract.as_dict(),
            "activation_contract": self.activation_contract.as_dict(),
            "health_contract": self.health_contract.as_dict(),
            "policy_permissions": [_policy_value(policy) for policy in self.policy_permissions],
            "deferability": self.deferability,
            "criticality": self.criticality.value,
            "compatibility": dict(self.compatibility),
            "lifecycle_state": self.lifecycle_state.value,
            "registration_status": self.registration_status,
            "governance_status": self.governance_status,
            "execution_phase": self.execution_phase.value,
            "secondary_phases": [phase.value for phase in self.secondary_phases],
            "post_processing_category": self.post_processing_category.value,
            "blocks_result_availability": self.blocks_result_availability,
            "synchronous_allowed": self.synchronous_allowed,
            "maximum_synchronous_duration": self.maximum_synchronous_duration,
            "maximum_serialized_bytes": self.maximum_serialized_bytes,
            "maximum_objects_visited": self.maximum_objects_visited,
            "maximum_registry_scans": self.maximum_registry_scans,
            "trigger_conditions": list(self.trigger_conditions),
            "required_state_changes": list(self.required_state_changes),
            "idempotency_contract": self.idempotency_contract.value,
            "result_dependency": self.result_dependency,
            "maintenance_priority": self.maintenance_priority,
            "critical_completion_required": self.critical_completion_required,
            "safe_to_skip": self.safe_to_skip,
            "diagnostic_only": self.diagnostic_only,
            "change_triggered": self.change_triggered,
        }


def _policy_value(policy) -> str:
    return getattr(policy, "value", str(policy))


__all__ = [
    "CapabilityCategory",
    "CapabilityContract",
    "CapabilityCriticality",
    "CapabilityLifecycleState",
    "ExecutionPhase",
    "IdempotencyContract",
    "PostProcessingCategory",
]
