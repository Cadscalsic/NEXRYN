"""Strategy registry for reusable execution plans."""

from __future__ import annotations

from runtime.capability_intelligence.strategy_descriptor import StrategyDescriptor


class StrategyRegistry:
    def __init__(self):
        self._strategies: dict[str, StrategyDescriptor] = {}

    def register(self, strategy: StrategyDescriptor) -> StrategyDescriptor:
        self._strategies[strategy.strategy_id] = strategy
        return strategy

    def by_task_family(self, task_family: str) -> list[StrategyDescriptor]:
        return [item for item in self._strategies.values() if item.task_family == task_family]

    def successful(self) -> list[StrategyDescriptor]:
        return [item for item in self._strategies.values() if item.average_success_rate >= 0.5 and item.status == "ACTIVE"]

    def resource_efficient(self) -> list[StrategyDescriptor]:
        return sorted(self.successful(), key=lambda item: item.average_cost)

    def all(self) -> list[StrategyDescriptor]:
        return list(self._strategies.values())


__all__ = ["StrategyRegistry"]
