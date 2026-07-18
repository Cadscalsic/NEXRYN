"""Canonical deferred maintenance plan objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class MaintenanceWorkStatus(str, Enum):
    PLANNED = "PLANNED"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    DEFERRED = "DEFERRED"
    SKIPPED_UNCHANGED = "SKIPPED_UNCHANGED"
    SKIPPED_POLICY = "SKIPPED_POLICY"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_PERMANENT = "FAILED_PERMANENT"
    CANCELLED = "CANCELLED"


@dataclass
class MaintenanceWorkItem:
    work_id: str
    execution_id: str
    work_type: str
    component_name: str
    work_category: str
    trigger_reason: str
    capability_id: str = ""
    dependency_versions: dict[str, Any] = field(default_factory=dict)
    input_signature: str = ""
    priority: str = "MEDIUM"
    estimated_cost: str = "LOW"
    budget_requirements: dict[str, Any] = field(default_factory=dict)
    dependencies: tuple[str, ...] = ()
    max_duration: float = 0.1
    max_memory: int = 0
    max_serialized_bytes: int = 0
    idempotency_key: str = ""
    status: str = MaintenanceWorkStatus.PLANNED.value
    attempts: int = 0
    last_error: str | None = None
    created_at: str = field(default_factory=lambda: str(datetime.utcnow()))
    completed_at: str | None = None

    @classmethod
    def create(
        cls,
        execution_id: str,
        work_type: str,
        component_name: str,
        work_category: str,
        trigger_reason: str,
        dependency_versions: dict[str, Any] | None = None,
        input_signature: str = "",
        priority: str = "MEDIUM",
        estimated_cost: str = "LOW",
        max_duration: float = 0.1,
        max_memory: int = 0,
        max_serialized_bytes: int = 0,
        idempotency_key: str | None = None,
        status: str = MaintenanceWorkStatus.PLANNED.value,
    ) -> "MaintenanceWorkItem":
        versions = dict(dependency_versions or {})
        key = idempotency_key or f"{work_type}:{input_signature}:{sorted(versions.items())}"
        return cls(
            work_id=f"maintenance-{uuid4()}",
            execution_id=str(execution_id),
            work_type=str(work_type),
            component_name=str(component_name),
            work_category=str(work_category),
            trigger_reason=str(trigger_reason),
            capability_id=str(work_type),
            dependency_versions=versions,
            input_signature=str(input_signature),
            priority=str(priority),
            estimated_cost=str(estimated_cost),
            budget_requirements={
                "max_duration": float(max_duration),
                "max_memory": int(max_memory),
                "max_serialized_bytes": int(max_serialized_bytes),
            },
            max_duration=float(max_duration),
            max_memory=int(max_memory),
            max_serialized_bytes=int(max_serialized_bytes),
            idempotency_key=key,
            status=status,
        )

    def as_dict(self) -> dict[str, Any]:
        data = dict(self.__dict__)
        data.update({
            "source_versions": dict(self.dependency_versions),
            "current_status": self.status,
            "retry_count": self.attempts,
        })
        return data


@dataclass
class PostExecutionPlan:
    execution_id: str
    task_id: str
    terminal_state: str
    execution_policy: str
    task_profile: dict[str, Any]
    critical_sync_work: list[MaintenanceWorkItem] = field(default_factory=list)
    bounded_sync_work: list[MaintenanceWorkItem] = field(default_factory=list)
    deferred_work: list[MaintenanceWorkItem] = field(default_factory=list)
    change_triggered_work: list[MaintenanceWorkItem] = field(default_factory=list)
    diagnostic_work: list[MaintenanceWorkItem] = field(default_factory=list)
    prohibited_work: list[MaintenanceWorkItem] = field(default_factory=list)
    maintenance_reasons: list[str] = field(default_factory=list)
    state_change_signatures: dict[str, str] = field(default_factory=dict)
    synchronous_budget: dict[str, Any] = field(default_factory=dict)
    deferred_budget: dict[str, Any] = field(default_factory=dict)
    persistence_contract: dict[str, Any] = field(default_factory=dict)
    reporting_contract: dict[str, Any] = field(default_factory=dict)
    plan_status: str = "PLANNED"
    result_available_timestamp: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "terminal_state": self.terminal_state,
            "execution_policy": self.execution_policy,
            "task_profile": dict(self.task_profile),
            "critical_sync_work": [item.as_dict() for item in self.critical_sync_work],
            "bounded_sync_work": [item.as_dict() for item in self.bounded_sync_work],
            "deferred_work": [item.as_dict() for item in self.deferred_work],
            "change_triggered_work": [item.as_dict() for item in self.change_triggered_work],
            "diagnostic_work": [item.as_dict() for item in self.diagnostic_work],
            "prohibited_work": [item.as_dict() for item in self.prohibited_work],
            "maintenance_reasons": list(self.maintenance_reasons),
            "state_change_signatures": dict(self.state_change_signatures),
            "synchronous_budget": dict(self.synchronous_budget),
            "deferred_budget": dict(self.deferred_budget),
            "persistence_contract": dict(self.persistence_contract),
            "reporting_contract": dict(self.reporting_contract),
            "plan_status": self.plan_status,
            "result_available_timestamp": self.result_available_timestamp,
        }


__all__ = ["MaintenanceWorkItem", "MaintenanceWorkStatus", "PostExecutionPlan"]
