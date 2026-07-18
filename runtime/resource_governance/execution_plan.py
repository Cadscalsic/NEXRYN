"""Lightweight adaptive execution plan."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from runtime.resource_governance.layer_state_registry import LayerState


@dataclass
class ExecutionPlan:
    required_layers: set[str] = field(default_factory=set)
    active_layers: set[str] = field(default_factory=set)
    on_demand_layers: set[str] = field(default_factory=set)
    deferred_layers: set[str] = field(default_factory=set)
    blocked_layers: set[str] = field(default_factory=set)
    diagnostic_layers: set[str] = field(default_factory=set)
    completed_layers: set[str] = field(default_factory=set)
    failed_layers: set[str] = field(default_factory=set)
    pre_execution_capabilities: set[str] = field(default_factory=set)
    required_task_capabilities: set[str] = field(default_factory=set)
    active_task_capabilities: set[str] = field(default_factory=set)
    on_demand_task_capabilities: set[str] = field(default_factory=set)
    evaluation_capabilities: set[str] = field(default_factory=set)
    critical_post_processing: set[str] = field(default_factory=set)
    bounded_post_processing: set[str] = field(default_factory=set)
    deferred_maintenance: set[str] = field(default_factory=set)
    change_triggered_maintenance: set[str] = field(default_factory=set)
    diagnostic_capabilities: set[str] = field(default_factory=set)
    prohibited_after_terminal: set[str] = field(default_factory=set)
    completed_capabilities: set[str] = field(default_factory=set)
    failed_capabilities: set[str] = field(default_factory=set)

    @classmethod
    def from_states(cls, states: dict[str, LayerState]) -> "ExecutionPlan":
        plan = cls()
        for layer_name, state in states.items():
            plan.record(layer_name, state)
        return plan

    def record(self, layer_name: str, state: LayerState) -> None:
        target = {
            LayerState.REQUIRED: self.required_layers,
            LayerState.ACTIVE: self.active_layers,
            LayerState.ON_DEMAND: self.on_demand_layers,
            LayerState.DEFERRED: self.deferred_layers,
            LayerState.BLOCKED: self.blocked_layers,
            LayerState.DIAGNOSTIC_ONLY: self.diagnostic_layers,
            LayerState.COMPLETED: self.completed_layers,
            LayerState.FAILED: self.failed_layers,
        }.get(state)
        if target is not None:
            target.add(str(layer_name))

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "required_layers": sorted(self.required_layers),
            "active_layers": sorted(self.active_layers),
            "on_demand_layers": sorted(self.on_demand_layers),
            "deferred_layers": sorted(self.deferred_layers),
            "blocked_layers": sorted(self.blocked_layers),
            "diagnostic_layers": sorted(self.diagnostic_layers),
            "completed_layers": sorted(self.completed_layers),
            "failed_layers": sorted(self.failed_layers),
            "pre_execution_capabilities": sorted(self.pre_execution_capabilities),
            "required_task_capabilities": sorted(self.required_task_capabilities),
            "active_task_capabilities": sorted(self.active_task_capabilities),
            "on_demand_task_capabilities": sorted(self.on_demand_task_capabilities),
            "evaluation_capabilities": sorted(self.evaluation_capabilities),
            "critical_post_processing": sorted(self.critical_post_processing),
            "bounded_post_processing": sorted(self.bounded_post_processing),
            "deferred_maintenance": sorted(self.deferred_maintenance),
            "change_triggered_maintenance": sorted(self.change_triggered_maintenance),
            "diagnostic_capabilities": sorted(self.diagnostic_capabilities),
            "prohibited_after_terminal": sorted(self.prohibited_after_terminal),
            "completed_capabilities": sorted(self.completed_capabilities),
            "failed_capabilities": sorted(self.failed_capabilities),
        }

    def update_layers(
        self,
        layer_names: Iterable[str],
        state: LayerState,
    ) -> None:
        for layer_name in layer_names:
            self.record(layer_name, state)

    def record_capability(
        self,
        capability_name: str,
        execution_phase: str,
        state: str = "ON_DEMAND",
        post_processing_category: str | None = None,
    ) -> None:
        phase = str(execution_phase)
        status = str(state)
        category = str(post_processing_category or "")
        target = None
        if phase == "PRE_EXECUTION":
            target = self.pre_execution_capabilities
        elif phase == "TASK_EXECUTION":
            target = {
                "REQUIRED": self.required_task_capabilities,
                "ACTIVE": self.active_task_capabilities,
                "ON_DEMAND": self.on_demand_task_capabilities,
            }.get(status, self.on_demand_task_capabilities)
        elif phase == "EVALUATION":
            target = self.evaluation_capabilities
        elif phase in {"POST_PROCESSING", "MAINTENANCE"}:
            target = {
                "CRITICAL_SYNC": self.critical_post_processing,
                "BOUNDED_SYNC": self.bounded_post_processing,
                "DEFERRED": self.deferred_maintenance,
                "CHANGE_TRIGGERED": self.change_triggered_maintenance,
                "DIAGNOSTIC_ONLY": self.diagnostic_capabilities,
                "PROHIBITED_AFTER_TERMINAL": self.prohibited_after_terminal,
            }.get(category, self.deferred_maintenance)
        elif phase == "DIAGNOSTIC":
            target = self.diagnostic_capabilities
        if target is not None:
            target.add(str(capability_name))


__all__ = ["ExecutionPlan"]
