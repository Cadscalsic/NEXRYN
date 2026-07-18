from runtime.capability_architecture import (
    ActivationContract,
    ActivationType,
    CapabilityCategory,
    CapabilityContract,
    InputContract,
    LayerDescriptor,
    OutputContract,
)
from runtime.capability_intelligence import (
    CapabilityIntelligenceEngine,
    CapabilityRecommendationState,
    CapabilityRetirementDetector,
    CapabilityRetirementState,
    StrategyDescriptor,
)
from runtime.resource_governance import AdaptiveExecutionGovernor
from runtime.resource_governance.execution_policy import ExecutionPolicyName


def cap(name, owner="Layer", policies=("BALANCED", "MAX_ACCURACY", "DIAGNOSTIC")):
    return CapabilityContract(
        capability_id=f"cap::{name}",
        capability_name=name,
        capability_version="1.0",
        owning_layer=owner,
        category=CapabilityCategory.COGNITIVE_REASONING,
        input_contract=InputContract(required_inputs=("task_profiles",)),
        output_contract=OutputContract(produced_outputs=("hypotheses",)),
        activation_contract=ActivationContract(
            activation_type=ActivationType.ON_DEMAND,
            execution_policies=tuple(policies),
        ),
        policy_permissions=tuple(policies),
    )


def test_capability_effectiveness_tracking():
    engine = CapabilityIntelligenceEngine()

    record = engine.effectiveness_tracker.record(
        "semantic_compilation",
        success=True,
        prediction_improvement=0.4,
        confidence_improvement=0.2,
        residual_reduction=0.3,
    )

    assert record.executions == 1
    assert engine.effectiveness_tracker.score("semantic_compilation") > 0


def test_strategy_registration_and_historical_lookup():
    engine = CapabilityIntelligenceEngine()
    strategy = StrategyDescriptor(
        strategy_id="strategy:rotation",
        strategy_name="rotation spatial strategy",
        task_family="rotation_scaling",
        capability_sequence=("spatial_reasoning", "scaling_execution"),
        average_cost=2.0,
        average_success_rate=0.9,
    )

    engine.register_strategy(strategy)

    assert engine.strategy_registry.by_task_family("rotation_scaling")[0].strategy_id == "strategy:rotation"
    assert engine.strategy_registry.resource_efficient()[0].strategy_id == "strategy:rotation"


def test_task_family_mapping_and_policy_recommendation():
    governor = AdaptiveExecutionGovernor()
    profile = governor.profile_task("gravity simulation objects fall onto support")
    engine = CapabilityIntelligenceEngine()

    signature = engine.task_signature_mapper.map_profile(profile)
    policy = engine.policy_recommendation_engine.recommend(signature.task_family, profile.task_complexity)

    assert signature.task_family == "gravity"
    assert policy["recommended_policy"] == "MAX_ACCURACY"


def test_capability_cooperation_tracking():
    engine = CapabilityIntelligenceEngine()

    engine.cooperation_engine.record_cooperation(
        ["topology_reasoning", "object_tracking"],
        combined_latency=0.2,
        prediction_gain=0.5,
        residual_reduction=0.3,
    )

    best = engine.cooperation_engine.best_pairs()[0]
    assert best.capability_pair == ("object_tracking", "topology_reasoning")
    assert best.effectiveness() > 0


def test_cost_predictions_use_observed_history_and_unknown_fallback():
    engine = CapabilityIntelligenceEngine()
    engine.cost_intelligence.record_cost("spatial_reasoning", latency=0.4, memory=10, activation_cost=2)
    engine.effectiveness_tracker.record("spatial_reasoning", success=True, prediction_improvement=0.5)

    known = engine.cost_predictor.predict("spatial_reasoning")
    unknown = engine.cost_predictor.predict("missing_capability")

    assert known["expected_latency"] == 0.4
    assert known["evidence"] == "observed_history"
    assert unknown["expected_latency"] == "UNKNOWN"
    assert unknown["evidence"] == "insufficient_history"


def test_capability_recommendations_and_prioritization():
    governor = AdaptiveExecutionGovernor()
    profile = governor.profile_task("rotation and scaling transformation")
    engine = CapabilityIntelligenceEngine()
    engine.effectiveness_tracker.record("spatial_reasoning", success=True, prediction_improvement=0.5)

    rec = engine.recommend_for_task(profile, "BALANCED")

    assert "semantic_compilation" in rec["recommended_capabilities"]
    assert rec["capability_priorities"]["spatial_reasoning"] >= 0.5
    assert rec["policy_recommendation"]["recommended_policy"] in {"BALANCED", "MAX_ACCURACY"}


def test_adaptive_capability_learning_updates_memory():
    engine = CapabilityIntelligenceEngine()

    record = engine.learn_from_execution(
        task_signature="topology_object_tracking",
        task_family="topology",
        policy="MAX_ACCURACY",
        capabilities_used=["object_tracking", "topology_reasoning"],
        terminal_state="EXACT_SUCCESS",
        execution_time=1.0,
        resource_cost=2.0,
        prediction_quality=0.9,
        confidence_score=0.8,
    )

    assert record.task_family == "topology"
    assert engine.strategy_memory.count("topology") == 1
    assert engine.task_family_memory.get("topology").successful_strategies
    assert engine.usage_statistics.success_rate("topology_reasoning") == 1.0


def test_capability_retirement_detection():
    engine = CapabilityIntelligenceEngine()
    detector = CapabilityRetirementDetector()
    engine.effectiveness_tracker.record("weak_capability", success=False)
    engine.usage_statistics.record_usage("weak_capability", success=False)

    weak = detector.evaluate(
        "weak_capability",
        usage=engine.usage_statistics.records["weak_capability"],
        effectiveness=engine.effectiveness_tracker.records["weak_capability"],
    )
    unused = detector.evaluate("unused_capability")

    assert weak["retirement_state"] == CapabilityRetirementState.REVIEW_REQUIRED.value
    assert unused["retirement_state"] == CapabilityRetirementState.LOW_USAGE.value


def test_governor_integration_recommends_but_does_not_activate():
    governor = AdaptiveExecutionGovernor()
    governor.register_capability_layer(
        LayerDescriptor(layer_id="layer::spatial", layer_name="SpatialLayer", capabilities=("spatial_reasoning",)),
        [cap("spatial_reasoning", owner="SpatialLayer")],
    )

    before = governor.layer_states()
    recommendation = governor.recommend_capabilities_for_task("spatial relation task")
    report = governor.build_capability_intelligence_report("spatial relation task")

    assert recommendation["recommended_capabilities"]
    assert governor.layer_states() == before
    assert report["CAPABILITY_INTELLIGENCE_REPORT"] is True


def test_backward_compatibility_and_graceful_degradation_unknown():
    governor = AdaptiveExecutionGovernor()
    profile = governor.profile_task("unknown abstract task")

    report = governor.capability_intelligence.build_report(profile, "BALANCED")

    assert report["governor_approval_status"] == "UNKNOWN"
    assert report["observability_metrics"]["capability_cost_predictions"] >= 0
    assert "UNKNOWN" in {
        item["recommendation"]
        for item in governor.capability_intelligence.recommend_for_task(profile)["recommendations"]
    } or report["recommended_capabilities"] or report["optional_capabilities"]


def test_diagnostic_capability_is_avoided_under_balanced_policy():
    governor = AdaptiveExecutionGovernor()
    governor.register_capability_layer(
        LayerDescriptor(layer_id="layer::diag", layer_name="DiagnosticLayer", capabilities=("diagnostic_profiler",)),
        [cap("diagnostic_profiler", owner="DiagnosticLayer", policies=("DIAGNOSTIC",))],
    )
    profile = governor.profile_task("diagnostic profiler task")

    rec = governor.capability_intelligence.recommend_for_task(profile, "BALANCED")

    assert "diagnostic_profiler" not in rec["recommended_capabilities"]


def test_capability_intelligence_report_rendering():
    governor = AdaptiveExecutionGovernor()
    profile = governor.profile_task("simple color mapping")

    rendered = governor.capability_intelligence.render_report(profile, "BALANCED")

    assert "CAPABILITY INTELLIGENCE REPORT" in rendered
