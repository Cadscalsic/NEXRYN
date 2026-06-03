from runtime.evolution.evolution_validator import EvolutionValidator


def test_strategy_promotion_registry_prevents_duplicate_promotions():
    validator = EvolutionValidator()
    strategy = {
        "type": "structural_object_count",
        "confidence": 1.0,
    }

    first = validator.promote_strategy(strategy)
    second = validator.promote_strategy(strategy)
    summary = validator.build_promotion_summary()
    validation = validator.build_validation_report()

    assert first["newly_promoted"] is True
    assert second["newly_promoted"] is False
    assert summary["promotion_count"] == 1
    assert summary["promoted_strategies"] == [{
        "strategy": "structural_object_count",
        "status": "promoted",
        "confidence": 1.0,
    }]
    assert validation["promoted_count"] == 1
