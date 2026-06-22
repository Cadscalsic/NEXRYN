from runtime.meta.meta_controller import MetaControllerEngine
from runtime.learning.operator_reward_engine import OperatorRewardEngine
from runtime.motivation import (
    CognitiveCandyManager,
    MotivationPolicy,
    MotivationSystem,
    PenaltyEngine,
    RewardEngine,
)


def test_partial_localized_progress_rewards_progress_and_minor_penalty():
    system = MotivationSystem()

    reports = system.evaluate({
        "evaluation_result": {
            "accuracy": 0.96,
            "difference_count": 1,
            "partial_success": True,
        },
        "prediction_report": {
            "prediction_accuracy": 0.96,
        },
        "transformation_localization": {
            "localization_ready": True,
            "localization_confidence": 0.97,
        },
        "residual_difference_count": 1,
        "failure_cause": "localized_prediction_mismatch",
        "identity_confidence": 1.0,
        "causal_consistency": 1.0,
        "identity_governance_state": "IDENTITY_GOVERNANCE_STABLE",
        "stable_truth": True,
    })

    report = reports["MOTIVATION_REPORT"]
    penalties = report["penalty_distribution"]

    assert report["outcome_class"] == "partial_success"
    assert report["reward_distribution"]["localization_reward"] >= 0.90
    assert penalties["minor"] > 0.0
    assert penalties["moderate"] == 0.0
    assert penalties["major"] == 0.0
    assert penalties["critical"] == 0.0


def test_exact_success_gets_high_reward_and_candy_report_fields():
    system = MotivationSystem()

    reports = system.evaluate({
        "evaluation_result": {
            "exact_success": True,
            "accuracy": 1.0,
            "difference_count": 0,
        },
        "identity_confidence": 1.0,
        "causal_consistency": 1.0,
        "identity_governance_state": "IDENTITY_GOVERNANCE_STABLE",
        "stable_truth": True,
        "reasoning_depth": 1,
        "active_routes": 1,
        "performance_report": {
            "total_runtime_seconds": 1.0,
        },
    })

    motivation_report = reports["MOTIVATION_REPORT"]
    candy_report = reports["COGNITIVE_CANDY_REPORT"]

    assert motivation_report["outcome_class"] == "exact_success"
    assert motivation_report["reward_score"] >= 0.92
    assert motivation_report["penalty_score"] == 0.0
    assert set(candy_report) >= {
        "truth_candy",
        "curiosity_candy",
        "efficiency_candy",
        "generalization_candy",
        "reuse_candy",
        "recovery_candy",
    }
    assert candy_report["system"] == "COGNITIVE_CANDY_REPORT"
    assert "budget_adjustments" in candy_report


def test_critical_failure_is_penalized_and_cannot_be_reward_overridden():
    system = MotivationSystem()

    reports = system.evaluate({
        "evaluation_result": {
            "accuracy": 0.99,
            "partial_success": True,
        },
        "truth_corruption_detected": True,
        "identity_confidence": 1.0,
        "causal_consistency": 1.0,
        "stable_truth": True,
    })

    report = reports["MOTIVATION_REPORT"]

    assert report["outcome_class"] == "critical_failure"
    assert report["penalty_distribution"]["critical"] == 1.0
    assert report["truth_alignment"] == 0.0
    assert report["final_decision_score"] == 0.0
    assert report["net_motivation"] < 0.0


def test_motivation_audit_report_contains_required_fields():
    reports = MotivationSystem().evaluate({})

    audit = reports["MOTIVATION_AUDIT_REPORT"]
    required = {
        "file_location",
        "trigger_conditions",
        "reward_types",
        "penalty_types",
        "severity_level",
        "affected_modules",
        "exploration_impact",
    }

    assert audit["system"] == "MOTIVATION_AUDIT_REPORT"
    assert audit["mechanisms"]
    for mechanism in audit["mechanisms"]:
        assert required <= set(mechanism)


def test_meta_escalates_when_motivation_reports_critical_failure():
    decision = MetaControllerEngine().decide({
        "motivation_report": {
            "outcome_class": "critical_failure",
            "penalty_score": 1.0,
        },
    })

    assert decision.action == "ESCALATE_TO_GOVERNANCE"
    assert decision.enable_governance is True
    assert decision.enable_self_improvement is False
    assert decision.enable_strategy_evolution is False


def test_reward_and_penalty_engines_keep_cause_based_components():
    reward = RewardEngine().evaluate({
        "evaluation_result": {
            "accuracy": 0.95,
            "partial_success": True,
        },
        "transformation_localization": {
            "localization_ready": True,
            "localization_confidence": 0.95,
        },
        "residual_difference_count": 1,
    })
    penalty = PenaltyEngine().evaluate({
        "evaluation_result": {
            "difference_count": 1,
        },
        "failure_cause": "localized_prediction_mismatch",
    })

    assert reward["reward_distribution"]["localization_reward"] > 0.0
    assert penalty["penalties"][0]["cause"] == "localized_prediction_mismatch"
    assert penalty["highest_severity"] == "minor"


def test_reuse_candy_is_highest_value_signal_and_shapes_future_budget():
    system = MotivationSystem()

    reports = system.evaluate({
        "evaluation_result": {
            "exact_success": True,
            "accuracy": 1.0,
        },
        "pipeline_cache_hit": True,
        "strategy_reuse_applied": True,
        "program_reuse_applied": True,
        "context_reuse_applied": True,
        "memory_lookup_report": {
            "exact_cache_hit": True,
        },
        "cache_metrics_report": {
            "cache_hit_rate": 1.0,
        },
        "thinking_avoidance_score": 1.0,
        "identity_confidence": 1.0,
        "causal_consistency": 1.0,
        "stable_truth": True,
        "max_reasoning_depth": 10,
        "max_active_routes": 5,
    })

    reward = reports["MOTIVATION_REPORT"]["reward_allocation"]
    candy = reports["COGNITIVE_CANDY_REPORT"]
    adapter = reports["candy_budget_adapter"]

    assert reward["reward_formula"]["reuse_gain"] == 0.30
    assert candy["reuse_candy"] >= 0.80
    assert candy["dominant_motivation"] == "reuse_candy"
    assert candy["budget_adjustments"]["reasoning_budget_multiplier"] == 0.8
    assert adapter["recommendation_only"] is True
    assert adapter["recommended_budget"]["motivation_policy_applied"] is False


def test_reward_hacking_reduces_safety_without_overriding_protected_candy():
    manager = CognitiveCandyManager()

    report = manager.allocate(
        {
            "truth_candy": 1.0,
            "curiosity_candy": 1.0,
            "efficiency_candy": 1.0,
            "generalization_candy": 1.0,
            "reuse_candy": 1.0,
            "recovery_candy": 1.0,
        },
        penalty_score=1.0,
        safety_multiplier=0.1,
        reward_hacking_risk=0.9,
    )

    assert report["truth_candy"] >= 0.75
    assert report["generalization_candy"] >= 0.75
    assert report["reuse_candy"] <= 0.11
    assert report["reward_hacking_risk"] == 0.9


def test_motivation_detects_reward_hacking_and_recommends_reduced_exploration():
    reports = MotivationSystem().evaluate({
        "evaluation_result": {
            "accuracy": 0.9,
            "partial_success": True,
        },
        "inflated_complexity": True,
        "unnecessary_reasoning": True,
        "excessive_resource_requests": True,
        "curiosity_candy": 0.0,
        "reasoning_depth": 12,
        "reasoning_depth_limit": 4,
    })

    hacking = reports["reward_hacking_report"]
    candy = reports["COGNITIVE_CANDY_REPORT"]

    assert hacking["reward_hacking_detected"] is True
    assert hacking["reward_hacking_penalty"] > 0.0
    assert candy["reward_hacking_risk"] > 0.0
    assert candy["constitutional_constraints"]["directly_controls_execution"] is False


def test_motivation_policy_is_recommendation_only():
    report = MotivationPolicy().recommend({
        "reuse_candy": 0.9,
        "efficiency_candy": 0.9,
        "curiosity_candy": 0.1,
        "recovery_candy": 0.1,
    })

    assert report["direct_execution_control"] is False
    assert report["governance_decides"] is True
    assert report["budget_adjustments"]["reasoning_budget_multiplier"] == 0.8
    assert report["budget_adjustments"]["governance_budget_multiplier"] == 0.9
    assert report["budget_adjustments"]["exploration_budget_multiplier"] == 0.5
    assert report["budget_adjustments"]["self_repair_priority_delta"] == 0.2


def test_legacy_operator_reward_engine_rewards_meaningful_partial_progress():
    engine = OperatorRewardEngine()

    report = engine.update_operator_weights(
        [{"primitive": "replace_color"}],
        [[1, 2], [3, 4]],
        [[1, 2], [3, 5]],
    )

    event = report["events"][0]

    assert report["metrics"]["outcome_class"] == "partial_success"
    assert event["event_type"] == "partial_reward"
    assert event["outcome_class"] == "partial_success"
    assert report["operator_weights"]["replace_color"]["reward_count"] == 1
    assert report["operator_weights"]["replace_color"]["punish_count"] == 0
