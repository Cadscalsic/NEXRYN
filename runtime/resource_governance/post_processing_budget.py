"""Canonical post-processing budget separated from task-solving budget."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from runtime.resource_governance.execution_policy import ExecutionPolicyName


class PostProcessingDecision(str, Enum):
    RUN_CRITICAL_SYNC = "RUN_CRITICAL_SYNC"
    RUN_BOUNDED_SYNC = "RUN_BOUNDED_SYNC"
    DEFER = "DEFER"
    RUN_IF_CHANGED = "RUN_IF_CHANGED"
    SKIP_UNCHANGED = "SKIP_UNCHANGED"
    SKIP_POLICY = "SKIP_POLICY"
    SKIP_DIAGNOSTIC_ONLY = "SKIP_DIAGNOSTIC_ONLY"
    REJECT_AFTER_TERMINAL = "REJECT_AFTER_TERMINAL"


@dataclass
class PostProcessingBudget:
    maximum_sync_seconds: float = 0.3
    maximum_bounded_operations: int = 4
    maximum_serialized_bytes: int = 65_536
    maximum_objects_visited: int = 1_000
    maximum_registry_scans: int = 2
    maximum_relationship_insertions: int = 25
    maximum_deepcopy_calls: int = 0
    maximum_report_nodes: int = 200
    maximum_persistence_bytes: int = 65_536
    maximum_maintenance_cpu_seconds: float = 30.0
    used_sync_seconds: float = 0.0
    bounded_operations_used: int = 0
    serialized_bytes_used: int = 0
    objects_visited: int = 0
    registry_scans: int = 0
    relationship_insertions: int = 0
    deepcopy_calls: int = 0
    report_nodes: int = 0
    persistence_bytes: int = 0
    maintenance_cpu_seconds: float = 0.0
    decision_ledger: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def for_policy(cls, policy: ExecutionPolicyName) -> "PostProcessingBudget":
        if policy == ExecutionPolicyName.LOW_LATENCY:
            return cls(0.1, 2, 16_384, 300, 1, 5, 0, 60, 16_384, 10.0)
        if policy == ExecutionPolicyName.MAX_ACCURACY:
            return cls(0.5, 6, 131_072, 2_000, 3, 50, 0, 400, 131_072, 45.0)
        if policy == ExecutionPolicyName.RESEARCH:
            return cls(1.5, 10, 524_288, 8_000, 8, 250, 1, 1_500, 524_288, 120.0)
        if policy == ExecutionPolicyName.DIAGNOSTIC:
            return cls(2.0, 12, 1_048_576, 12_000, 12, 300, 2, 2_000, 1_048_576, 120.0)
        if policy == ExecutionPolicyName.TRAINING:
            return cls(0.6, 8, 131_072, 4_000, 5, 100, 0, 500, 131_072, 60.0)
        return cls()

    def can_run_bounded(
        self,
        duration: float = 0.0,
        serialized_bytes: int = 0,
        objects_visited: int = 0,
    ) -> bool:
        return (
            self.used_sync_seconds + float(duration) <= self.maximum_sync_seconds
            and self.bounded_operations_used < self.maximum_bounded_operations
            and self.serialized_bytes_used + int(serialized_bytes) <= self.maximum_serialized_bytes
            and self.objects_visited + int(objects_visited) <= self.maximum_objects_visited
        )

    def consume_bounded(
        self,
        capability_id: str,
        duration: float = 0.0,
        serialized_bytes: int = 0,
        objects_visited: int = 0,
    ) -> bool:
        if not self.can_run_bounded(duration, serialized_bytes, objects_visited):
            self.record_decision(capability_id, PostProcessingDecision.DEFER, "post_processing_budget_exceeded")
            return False
        self.used_sync_seconds += float(duration)
        self.bounded_operations_used += 1
        self.serialized_bytes_used += int(serialized_bytes)
        self.objects_visited += int(objects_visited)
        return True

    def record_decision(
        self,
        capability_id: str,
        decision: PostProcessingDecision,
        reason: str,
    ) -> None:
        self.decision_ledger.append({
            "capability_id": str(capability_id),
            "decision": decision.value,
            "reason": str(reason),
        })

    def exceeded(self) -> bool:
        return (
            self.used_sync_seconds > self.maximum_sync_seconds
            or self.bounded_operations_used > self.maximum_bounded_operations
            or self.serialized_bytes_used > self.maximum_serialized_bytes
        )

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


__all__ = ["PostProcessingBudget", "PostProcessingDecision"]
