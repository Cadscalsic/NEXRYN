"""Capability usage statistics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapabilityUsageRecord:
    activation_frequency: int = 0
    success_frequency: int = 0
    failure_frequency: int = 0
    suspension_frequency: int = 0
    deferred_frequency: int = 0
    policy_usage: dict[str, int] = field(default_factory=dict)
    strategy_usage: dict[str, int] = field(default_factory=dict)
    resource_usage: dict[str, float] = field(default_factory=dict)
    escalation_frequency: int = 0
    task_execution_cost: float = 0.0
    post_processing_cost: float = 0.0
    maintenance_cost: float = 0.0
    immediate_task_value: float = 0.0
    maintenance_value: float = 0.0
    deferred_value: float = 0.0
    result_blocking_value: float = 0.0
    serialization_cost: float = 0.0
    reporting_cost: float = 0.0
    persistence_cost: float = 0.0
    state_change_frequency: int = 0
    cache_hit_rate: float = 0.0
    unchanged_state_skip_rate: float = 0.0
    average_deferred_delay: float = 0.0
    maintenance_success_rate: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


class CapabilityUsageStatistics:
    def __init__(self):
        self.records: dict[str, CapabilityUsageRecord] = {}

    def record_usage(
        self,
        capability_name: str,
        policy: str = "BALANCED",
        strategy: str = "UNKNOWN",
        success: bool | None = None,
        suspended: bool = False,
        deferred: bool = False,
        escalated: bool = False,
        resource_usage: dict[str, float] | None = None,
        post_processing_metrics: dict[str, float] | None = None,
    ) -> CapabilityUsageRecord:
        record = self.records.setdefault(capability_name, CapabilityUsageRecord())
        record.activation_frequency += 1
        if success is True:
            record.success_frequency += 1
        if success is False:
            record.failure_frequency += 1
        if suspended:
            record.suspension_frequency += 1
        if deferred:
            record.deferred_frequency += 1
        if escalated:
            record.escalation_frequency += 1
        record.policy_usage[policy] = record.policy_usage.get(policy, 0) + 1
        record.strategy_usage[strategy] = record.strategy_usage.get(strategy, 0) + 1
        for key, value in dict(resource_usage or {}).items():
            record.resource_usage[key] = record.resource_usage.get(key, 0.0) + float(value)
        for key, value in dict(post_processing_metrics or {}).items():
            if hasattr(record, key):
                current = getattr(record, key)
                if isinstance(current, int):
                    setattr(record, key, current + int(value))
                else:
                    setattr(record, key, float(current) + float(value))
        return record

    def success_rate(self, capability_name: str) -> float:
        record = self.records.get(capability_name)
        if not record:
            return 0.0
        total = record.success_frequency + record.failure_frequency
        return round(record.success_frequency / max(total, 1), 4)

    def as_dict(self) -> dict[str, Any]:
        return {name: record.as_dict() for name, record in sorted(self.records.items())}


__all__ = ["CapabilityUsageRecord", "CapabilityUsageStatistics"]
