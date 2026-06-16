from core.context.context_strength_engine import ContextStrengthEngine
from runtime.context.process_context_registry import ProcessContextRegistry
from runtime.evolution.evolution_validator import EvolutionValidator


def promoted_structural_strategy():
    return {
        "strategy": "structural_object_count",
        "status": "promoted",
        "confidence": 1.0,
        "primitive": "duplicate_object",
        "world_model_fit": 1.0,
    }


def test_registry_rejects_unpromoted_or_unsafe_strategies():
    registry = ProcessContextRegistry()

    unpromoted = registry.register_promoted_strategy({
        "strategy": "structural_object_count",
        "confidence": 1.0,
    })
    unsafe = registry.register_promoted_strategy({
        "strategy": "structural_object_count",
        "status": "promoted",
        "confidence": 1.0,
        "ontology_safe": False,
    })
    domination = registry.register_promoted_strategy({
        "strategy": "structural_object_count",
        "status": "promoted",
        "confidence": 1.0,
        "anti_domination_risk": True,
    })

    assert unpromoted["registered"] is False
    assert unpromoted["rejection_reason"] == (
        "strategy_not_promoted_or_validation_incomplete"
    )
    assert unsafe["registered"] is False
    assert unsafe["rejection_reason"] == "ontology_safety_failed"
    assert domination["registered"] is False
    assert domination["rejection_reason"] == (
        "anti_domination_protection_triggered"
    )
    assert registry.context_count == 0


def test_promoted_process_strategy_registers_reusable_contexts():
    registry = ProcessContextRegistry()

    report = registry.register_promoted_strategy(promoted_structural_strategy())

    assert report["registered"] is True
    assert report["context_count"] > 2
    assert "replication_context" in report["context_names"]
    assert "growth_context" in report["context_names"]
    for context in report["registered_contexts"]:
        assert set([
            "context_name",
            "source_strategy",
            "preconditions",
            "transitions",
            "expected_outcomes",
            "context_confidence",
        ]).issubset(context)
        assert context["source_strategy"] == "structural_object_count"
        assert context["preconditions"]
        assert context["transitions"]
        assert context["expected_outcomes"]
        assert context["context_confidence"] > 0.90


def test_evolution_promotion_consolidates_process_contexts():
    validator = EvolutionValidator()

    promotion = validator.promote_strategy({
        "type": "structural_object_count",
        "confidence": 1.0,
        "primitive": "duplicate_object",
        "world_model_fit": 1.0,
    })

    registry_report = promotion["process_context_registry_report"]
    assert promotion["newly_promoted"] is True
    assert registry_report["context_count"] > 2
    assert "replication_context" in registry_report["context_names"]
    assert "growth_context" in registry_report["context_names"]


def test_context_strength_consumes_registry_process_context():
    registry = ProcessContextRegistry()
    registry.register_promoted_strategy(promoted_structural_strategy())

    strength = ContextStrengthEngine().consume_math_reasoning(
        0.50,
        math_reasoning_report={
            "math_reasoning_signature": {
                "typed_dependencies_generated": True,
                "transformations_detected": True,
            },
        },
        process_context_report={},
        dependency_semantics_report={},
        runtime_context={
            "concept": "replication",
            "process_context_registry_report": registry.report(),
        },
    )

    assert strength["final_context_strength"] > 0.90
    assert strength["process_context_generated"] is True
    assert strength["rejection_reasons"] == []
    assert "process_transition_sequence" in strength["evidence_used"]
    assert "temporal_state_sequence" in strength["evidence_used"]
