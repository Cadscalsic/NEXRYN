class StrategyLifecycleManager:
    """Prevents newly validated strategies from being pruned immediately."""

    PROTECTED_VALIDATION_STATES = {
        "validated",
        "stable",
    }

    def protection_report(self, validation_events):
        protected_strategies = sorted({
            event.get("evolved_strategy")
            for event in validation_events
            if (
                event.get("validation_status")
                in self.PROTECTED_VALIDATION_STATES
                and event.get("evolved_strategy")
            )
        })
        return {
            "system": "strategy_lifecycle_manager",
            "protected_strategies": protected_strategies,
            "protection_reason":
            "newly_validated_strategy_requires_next_cycle_observation",
            "same_cycle_validated_strategy_pruning_forbidden": True,
        }


__all__ = [
    "StrategyLifecycleManager",
]
