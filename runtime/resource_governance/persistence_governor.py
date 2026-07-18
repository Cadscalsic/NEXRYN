"""Persistence contract governance for post-execution work."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from runtime.resource_governance.execution_policy import ExecutionPolicyName


class PersistenceContractType(str, Enum):
    CRITICAL_CHECKPOINT = "CRITICAL_CHECKPOINT"
    DELTA_CHECKPOINT = "DELTA_CHECKPOINT"
    FULL_STATE_SAVE = "FULL_STATE_SAVE"
    DEFERRED_STATE_SAVE = "DEFERRED_STATE_SAVE"
    DIAGNOSTIC_SNAPSHOT = "DIAGNOSTIC_SNAPSHOT"


@dataclass(frozen=True)
class PersistenceContract:
    contract_type: str
    synchronous: bool
    max_duration: float
    changed_state_only: bool
    full_state_allowed: bool
    reason: str

    def as_dict(self):
        return dict(self.__dict__)


class PersistenceGovernor:
    def select_contract(
        self,
        policy: ExecutionPolicyName,
        state_changed: bool = False,
        shutdown_required: bool = False,
    ) -> PersistenceContract:
        if policy == ExecutionPolicyName.DIAGNOSTIC:
            return PersistenceContract(PersistenceContractType.DIAGNOSTIC_SNAPSHOT.value, True, 1.0, False, True, "diagnostic_snapshot_allowed")
        if shutdown_required and state_changed and policy in {ExecutionPolicyName.MAX_ACCURACY, ExecutionPolicyName.RESEARCH}:
            return PersistenceContract(PersistenceContractType.FULL_STATE_SAVE.value, False, 2.0, False, True, "full_save_deferred_to_maintenance_window")
        if state_changed and policy in {ExecutionPolicyName.BALANCED, ExecutionPolicyName.MAX_ACCURACY, ExecutionPolicyName.RESEARCH}:
            return PersistenceContract(PersistenceContractType.DELTA_CHECKPOINT.value, True, 0.15, True, False, "changed_state_delta_checkpoint")
        if policy == ExecutionPolicyName.TRAINING:
            return PersistenceContract(PersistenceContractType.DELTA_CHECKPOINT.value, True, 0.4, True, False, "training_delta_checkpoint")
        if policy == ExecutionPolicyName.LOW_LATENCY:
            return PersistenceContract(PersistenceContractType.CRITICAL_CHECKPOINT.value, True, 0.05, True, False, "low_latency_critical_checkpoint")
        return PersistenceContract(PersistenceContractType.CRITICAL_CHECKPOINT.value, True, 0.1, True, False, "critical_checkpoint")


__all__ = ["PersistenceContract", "PersistenceContractType", "PersistenceGovernor"]
