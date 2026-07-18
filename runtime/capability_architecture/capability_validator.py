"""Capability registration validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.capability_architecture.capability_contract import (
    CapabilityContract,
    CapabilityLifecycleState,
    ExecutionPhase,
    PostProcessingCategory,
)
from runtime.capability_architecture.health_contract import CapabilityHealthStatus


@dataclass(frozen=True)
class CapabilityValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


class CapabilityValidator:
    def validate(
        self,
        contract: CapabilityContract,
        existing_owner: str | None = None,
        known_capabilities: set[str] | None = None,
    ) -> CapabilityValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        known = known_capabilities or set()
        if not contract.capability_id:
            errors.append("CAPABILITY_ID_REQUIRED")
        if not contract.capability_name:
            errors.append("CAPABILITY_NAME_REQUIRED")
        if not contract.owning_layer:
            errors.append("OWNING_LAYER_REQUIRED")
        if existing_owner and existing_owner != contract.owning_layer:
            errors.append("OWNERSHIP_CONFLICT")
        missing_deps = [
            dep for dep in contract.dependency_contract.capability_dependencies
            if dep not in known and dep != contract.capability_name
        ]
        if missing_deps:
            errors.append("DEPENDENCY_NOT_REGISTERED")
        if not contract.input_contract.required_inputs and not contract.input_contract.optional_inputs:
            warnings.append("INPUT_CONTRACT_EMPTY")
        if not contract.output_contract.produced_outputs and not contract.output_contract.optional_outputs:
            errors.append("OUTPUT_CONTRACT_EMPTY")
        if not contract.activation_contract.execution_policies:
            errors.append("POLICY_PERMISSION_EMPTY")
        if contract.lifecycle_state in {
            CapabilityLifecycleState.DISABLED,
            CapabilityLifecycleState.FAILED,
            CapabilityLifecycleState.UNREGISTERED,
        }:
            errors.append("INVALID_LIFECYCLE_FOR_REGISTRATION")
        if not isinstance(contract.execution_phase, ExecutionPhase):
            errors.append("EXECUTION_PHASE_REQUIRED")
        if contract.execution_phase in {ExecutionPhase.POST_PROCESSING, ExecutionPhase.MAINTENANCE}:
            if not isinstance(contract.post_processing_category, PostProcessingCategory):
                errors.append("POST_PROCESSING_CATEGORY_REQUIRED")
            if contract.blocks_result_availability and not contract.critical_completion_required:
                errors.append("BLOCKING_CAPABILITY_MUST_BE_CRITICAL_COMPLETION")
            if contract.synchronous_allowed and contract.maximum_synchronous_duration <= 0:
                errors.append("SYNCHRONOUS_CAPABILITY_REQUIRES_DURATION_LIMIT")
            if contract.change_triggered and not contract.required_state_changes:
                errors.append("CHANGE_TRIGGERED_REQUIRES_STATE_SIGNATURE")
        if (
            contract.post_processing_category == PostProcessingCategory.CRITICAL_SYNC
            and not contract.critical_completion_required
        ):
            errors.append("CRITICAL_SYNC_REQUIRES_CRITICAL_COMPLETION")
        if (
            contract.post_processing_category == PostProcessingCategory.DIAGNOSTIC_ONLY
            and not contract.diagnostic_only
        ):
            warnings.append("DIAGNOSTIC_CATEGORY_WITHOUT_DIAGNOSTIC_FLAG")
        if not contract.health_contract.activatable():
            errors.append("HEALTH_NOT_ACTIVATABLE")
        if contract.health_contract.health_status == CapabilityHealthStatus.UNKNOWN:
            warnings.append("HEALTH_UNKNOWN")
        return CapabilityValidationResult(not errors, tuple(errors), tuple(warnings))


__all__ = ["CapabilityValidationResult", "CapabilityValidator"]
