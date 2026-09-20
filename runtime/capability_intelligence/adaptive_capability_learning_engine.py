"""Bounded adaptive capability learning."""

from __future__ import annotations

from typing import Any

from runtime.capability_intelligence.capability_cooperation_engine import CapabilityCooperationEngine
from runtime.capability_intelligence.capability_cost_intelligence import CapabilityCostIntelligence
from runtime.capability_intelligence.capability_effectiveness_tracker import CapabilityEffectivenessTracker
from runtime.capability_intelligence.capability_usage_statistics import CapabilityUsageStatistics
from runtime.capability_intelligence.strategy_memory_engine import StrategyExecutionRecord, StrategyMemoryEngine
from runtime.capability_intelligence.task_family_memory import TaskFamilyMemory


class AdaptiveCapabilityLearningEngine:
    def __init__(
        self,
        usage_statistics: CapabilityUsageStatistics,
        effectiveness_tracker: CapabilityEffectivenessTracker,
        cost_intelligence: CapabilityCostIntelligence,
        cooperation_engine: CapabilityCooperationEngine,
        strategy_memory: StrategyMemoryEngine,
        task_family_memory: TaskFamilyMemory,
    ):
        self.usage_statistics = usage_statistics
        self.effectiveness_tracker = effectiveness_tracker
        self.cost_intelligence = cost_intelligence
        self.cooperation_engine = cooperation_engine
        self.strategy_memory = strategy_memory
        self.task_family_memory = task_family_memory

    def learn_from_execution(
        self,
        task_signature: str,
        task_family: str,
        policy: str,
        capabilities_used: list[str],
        terminal_state: str,
        execution_time: float,
        resource_cost: float,
        prediction_quality: float,
        confidence_score: float,
    ) -> StrategyExecutionRecord:
        success = terminal_state in {"EXACT_SUCCESS", "ACCEPTED_PARTIAL_SUCCESS"}
        effectiveness = round((prediction_quality + confidence_score) / max(resource_cost, 1.0), 4)
        for capability in capabilities_used:
            self.usage_statistics.record_usage(
                capability,
                policy=policy,
                strategy=task_signature,
                success=success,
                resource_usage={"cost": resource_cost / max(len(capabilities_used), 1)},
            )
            self.effectiveness_tracker.record(
                capability,
                success=success,
                prediction_improvement=prediction_quality,
                confidence_improvement=confidence_score,
            )
            self.cost_intelligence.record_cost(
                capability,
                latency=execution_time / max(len(capabilities_used), 1),
                activation_cost=resource_cost / max(len(capabilities_used), 1),
            )
        self.cooperation_engine.record_cooperation(
            capabilities_used,
            combined_latency=execution_time,
            prediction_gain=prediction_quality,
        )
        record = StrategyExecutionRecord.create(
            task_signature=task_signature,
            task_family=task_family,
            execution_policy=policy,
            capabilities_used=tuple(capabilities_used),
            terminal_state=terminal_state,
            execution_time=execution_time,
            resource_cost=resource_cost,
            prediction_quality=prediction_quality,
            confidence_score=confidence_score,
            strategy_effectiveness=effectiveness,
        )
        self.strategy_memory.remember(record)
        self.task_family_memory.record(
            task_family,
            record.strategy_id,
            capabilities_used,
            policy,
            success,
            budget={"resource_cost": resource_cost},
            execution_strategy=task_signature,
        )
        return record


__all__ = ["AdaptiveCapabilityLearningEngine"]
