"""Post-execution maintenance budget contract."""

from __future__ import annotations

from dataclasses import dataclass

from runtime.resource_governance.execution_policy import ExecutionPolicyName


@dataclass(frozen=True)
class MaintenanceBudget:
    synchronous_budget_seconds: float
    deferred_budget_seconds: float
    serialization_budget_bytes: int
    persistence_budget_seconds: float
    reporting_budget_seconds: float

    @classmethod
    def for_policy(cls, policy: ExecutionPolicyName) -> "MaintenanceBudget":
        if policy == ExecutionPolicyName.LOW_LATENCY:
            return cls(0.1, 10.0, 16_384, 0.05, 0.05)
        if policy == ExecutionPolicyName.MAX_ACCURACY:
            return cls(0.5, 45.0, 131_072, 0.25, 0.25)
        if policy == ExecutionPolicyName.RESEARCH:
            return cls(1.5, 120.0, 524_288, 0.75, 0.75)
        if policy == ExecutionPolicyName.DIAGNOSTIC:
            return cls(2.0, 120.0, 1_048_576, 1.0, 1.0)
        if policy == ExecutionPolicyName.TRAINING:
            return cls(0.6, 60.0, 131_072, 0.4, 0.3)
        return cls(0.3, 30.0, 65_536, 0.15, 0.15)

    def as_dict(self):
        return dict(self.__dict__)


__all__ = ["MaintenanceBudget"]
