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


def test_temporal_validation_requires_complete_horizon_before_promotion():
    validator = EvolutionValidator()

    first = validator.update_temporal_validation(
        "growth_strategy",
        accuracy=0.96,
        success=True,
    )
    second = validator.update_temporal_validation(
        "growth_strategy",
        accuracy=0.96,
        success=True,
    )
    third = validator.update_temporal_validation(
        "growth_strategy",
        accuracy=0.96,
        success=True,
    )

    assert first["required_window"] == 3
    assert first["window_size"] == 1
    assert first["promotion_score"] >= 0.95
    assert first["promotion_allowed"] is False
    assert first["deferred_reason"] == "temporal_horizon_incomplete"

    assert second["window_size"] == 2
    assert second["promotion_allowed"] is False
    assert second["deferred_reason"] == "temporal_horizon_incomplete"

    assert third["window_size"] == 3
    assert third["promotion_allowed"] is True
    assert third["deferred_reason"] is None


def test_strategy_promotion_candidate_waits_for_temporal_maturity():
    validator = EvolutionValidator()
    original = {"type": "growth_v1", "confidence": 0.91}
    evolved = {"type": "growth_v2", "confidence": 0.94}
    result = {
        "accuracy": 0.96,
        "success": True,
        "semantic_consistency": True,
        "entropy_stable": True,
        "ontology_safe": True,
    }

    first = validator.validate_strategy(original, evolved, result)
    second = validator.validate_strategy(original, evolved, result)
    third = validator.validate_strategy(original, evolved, result)

    assert first["base_promotion_candidate"] is True
    assert first["promotion_candidate"] is False
    assert first["promotion_deferred_reason"] == (
        "temporal_horizon_incomplete"
    )
    assert first["temporal_validation"]["window_size"] == 1

    assert second["promotion_candidate"] is False
    assert second["temporal_validation"]["window_size"] == 2

    assert third["promotion_candidate"] is True
    assert third["temporal_validation"]["window_size"] == 3
    assert third["temporal_validation"]["promotion_allowed"] is True
