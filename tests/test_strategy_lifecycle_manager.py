from runtime.evolution.evolution_memory_manager import EvolutionMemoryManager
from runtime.learning.strategy_lifecycle_manager import (
    StrategyLifecycleManager,
)


def test_strategy_lifecycle_protects_newly_validated_strategy():
    report = StrategyLifecycleManager().protection_report([{
        "evolved_strategy": "adaptive_hybrid_color_change",
        "validation_status": "validated",
    }])

    assert report["protected_strategies"] == [
        "adaptive_hybrid_color_change",
    ]
    assert report["same_cycle_validated_strategy_pruning_forbidden"] is True


def test_score_pruning_skips_same_cycle_validated_strategy():
    memory = EvolutionMemoryManager()
    memory.strategy_population["adaptive_hybrid_color_change"] = {
        "usage_count": 1,
        "success_count": 0,
        "failure_count": 1,
        "average_confidence": 0.0,
        "active": True,
    }

    pruned = memory.prune_strategies(
        protected_strategies=["adaptive_hybrid_color_change"],
    )

    assert pruned == []
    assert memory.strategy_population[
        "adaptive_hybrid_color_change"
    ]["active"] is True


def test_score_pruning_can_remove_strategy_in_later_cycle():
    memory = EvolutionMemoryManager()
    memory.strategy_population["adaptive_hybrid_color_change"] = {
        "usage_count": 1,
        "success_count": 0,
        "failure_count": 1,
        "average_confidence": 0.0,
        "active": True,
    }

    pruned = memory.prune_strategies()

    assert pruned == ["adaptive_hybrid_color_change"]


def test_promoted_strategy_requires_three_consecutive_failures_before_pruning():
    memory = EvolutionMemoryManager()
    memory.register_strategy({
        "type": "structural_object_size",
        "confidence": 1.0,
    })
    memory.mark_strategy_promoted("structural_object_size")

    memory.update_strategy("structural_object_size", False, 0.0)
    assert memory.prune_strategies(minimum_score=1.0) == []

    memory.update_strategy("structural_object_size", False, 0.0)
    assert memory.prune_strategies(minimum_score=1.0) == []

    memory.update_strategy("structural_object_size", False, 0.0)
    assert memory.prune_strategies(minimum_score=1.0) == [
        "structural_object_size",
    ]


def test_promoted_strategy_success_resets_consecutive_failure_grace():
    memory = EvolutionMemoryManager()
    memory.register_strategy({
        "type": "adaptive_color_change",
        "confidence": 1.0,
    })
    memory.mark_strategy_promoted("adaptive_color_change")

    memory.update_strategy("adaptive_color_change", False, 0.0)
    memory.update_strategy("adaptive_color_change", False, 0.0)
    memory.update_strategy("adaptive_color_change", True, 1.0)
    memory.update_strategy("adaptive_color_change", False, 0.0)

    assert memory.prune_strategies(minimum_score=1.0) == []
    assert memory.strategy_population["adaptive_color_change"][
        "consecutive_failure_count"
    ] == 1


def test_entropy_pruning_respects_promoted_strategy_failure_grace():
    memory = EvolutionMemoryManager()
    memory.register_strategy({
        "type": "recursive_structural_color_change_merged",
        "confidence": 1.0,
        "mutation_applied": True,
    })
    memory.mark_strategy_promoted(
        "recursive_structural_color_change_merged"
    )

    assert memory.prune_high_entropy_strategies() == []

    for _ in range(3):
        memory.update_strategy(
            "recursive_structural_color_change_merged",
            False,
            0.0,
        )

    assert memory.prune_high_entropy_strategies() == [
        "recursive_structural_color_change_merged",
    ]


def test_high_accuracy_strategy_requires_five_failures_before_pruning():
    memory = EvolutionMemoryManager()
    memory.register_strategy({
        "type": "adaptive_color_change",
        "confidence": 1.0,
    })
    memory.update_strategy(
        "adaptive_color_change",
        True,
        1.0,
        accuracy=0.99,
    )

    for _ in range(4):
        memory.update_strategy(
            "adaptive_color_change",
            False,
            0.0,
            accuracy=0.0,
        )
        assert memory.prune_strategies(minimum_score=1.0) == []

    memory.update_strategy(
        "adaptive_color_change",
        False,
        0.0,
        accuracy=0.0,
    )

    assert memory.prune_strategies(minimum_score=1.0) == [
        "adaptive_color_change",
    ]


def test_derived_strategy_merge_requires_causal_support():
    memory = EvolutionMemoryManager()
    memory.register_strategy({
        "type": "object_translation",
        "confidence": 1.0,
    })
    memory.register_strategy({
        "type": "recursive_object_translation",
        "confidence": 1.0,
        "parent_strategy": "object_translation",
        "mutation_applied": True,
    })

    allowed, reason = memory.can_merge(
        "object_translation",
        "recursive_object_translation",
    )

    assert allowed is False
    assert reason == "derived_strategy_causal_support_required"


def test_derived_strategy_merge_is_allowed_after_causal_support():
    memory = EvolutionMemoryManager()
    memory.register_strategy({
        "type": "object_translation",
        "confidence": 1.0,
        "causal_support_ready": True,
    })
    memory.register_strategy({
        "type": "recursive_object_translation",
        "confidence": 1.0,
        "parent_strategy": "object_translation",
        "mutation_applied": True,
        "causal_support_ready": True,
    })

    allowed, reason = memory.can_merge(
        "object_translation",
        "recursive_object_translation",
    )

    assert allowed is True
    assert reason == "merge_allowed"
