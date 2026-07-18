"""Task-family memory for capability intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskFamilyRecord:
    task_family: str
    successful_strategies: list[str] = field(default_factory=list)
    expensive_failures: list[str] = field(default_factory=list)
    useful_capabilities: dict[str, int] = field(default_factory=dict)
    recommended_policies: dict[str, int] = field(default_factory=dict)
    average_budgets: dict[str, float] = field(default_factory=dict)
    average_execution_strategies: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


class TaskFamilyMemory:
    def __init__(self):
        self.records: dict[str, TaskFamilyRecord] = {}

    def record(
        self,
        task_family: str,
        strategy_id: str,
        capabilities: list[str],
        policy: str,
        success: bool,
        budget: dict[str, float] | None = None,
        execution_strategy: str = "UNKNOWN",
    ) -> TaskFamilyRecord:
        record = self.records.setdefault(task_family, TaskFamilyRecord(task_family))
        if success:
            record.successful_strategies.append(strategy_id)
        else:
            record.expensive_failures.append(strategy_id)
        for capability in capabilities:
            record.useful_capabilities[capability] = record.useful_capabilities.get(capability, 0) + int(success)
        record.recommended_policies[policy] = record.recommended_policies.get(policy, 0) + int(success)
        record.average_execution_strategies[execution_strategy] = record.average_execution_strategies.get(execution_strategy, 0) + 1
        for key, value in dict(budget or {}).items():
            previous = record.average_budgets.get(key, 0.0)
            record.average_budgets[key] = round((previous + float(value)) / 2 if previous else float(value), 4)
        return record

    def get(self, task_family: str) -> TaskFamilyRecord | None:
        return self.records.get(task_family)

    def as_dict(self) -> dict[str, Any]:
        return {name: record.as_dict() for name, record in sorted(self.records.items())}


__all__ = ["TaskFamilyMemory", "TaskFamilyRecord"]
