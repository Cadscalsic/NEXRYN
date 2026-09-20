from runtime.world_governance import (
    NON_VOTING_CONSTITUTIONAL_CORE,
    cognitive_budget_controller,
    constitutional_veto,
    incentive_engine,
    incentive_reporter,
    influence_controller,
    reward_hacking_detector,
    trust_score_manager,
    voting_eligibility_manager,
    world_governance_reporter,
)


def test_constitutional_principles_cannot_be_voted_on():
    report = constitutional_veto.evaluate({
        "proposal_name": "vote_truth_priority",
        "votes_on": ["truth_priority"],
    })

    assert "truth_priority" in NON_VOTING_CONSTITUTIONAL_CORE
    assert report["decision"] == "CONSTITUTIONAL_VETO"
    assert report["allowed"] is False


def test_cognitive_budget_is_assigned_and_overruns_trigger_review():
    budget = cognitive_budget_controller.assign_budget({
        "task_complexity": 0.4,
        "available_resources": 0.5,
    })
    usage = cognitive_budget_controller.evaluate_usage(
        budget,
        {
            "runtime": budget.max_runtime + 1,
            "reasoning_depth": budget.max_reasoning_depth + 1,
        },
    )

    assert budget.max_reasoning_depth > 0
    assert usage["budget_compliance"] is False
    assert "trigger_efficiency_review" in usage["actions"]


def test_reward_hacking_is_detected_and_reduces_influence():
    hacking = reward_hacking_detector.detect(
        "route_builder",
        {
            "inflated_task_complexity": True,
            "unnecessary_reasoning": True,
            "requested_resources": 0.9,
            "used_resources": 0.2,
        },
    )
    influence = influence_controller.update(
        "route_builder",
        0.9,
        {
            "reward_hacking_detected": hacking["reward_hacking_detected"],
            "influence_reduction": hacking["influence_reduction"],
        },
    )

    assert hacking["reward_hacking_detected"] is True
    assert hacking["reward_hacking_penalty"] >= 2.0
    assert influence["influence_score"] < 0.85
    assert influence["constitutional_authority_modified"] is False


def test_reuse_is_rewarded_more_than_computation_volume():
    reuse_reward = incentive_engine.evaluate(
        "strategy_memory",
        {
            "accuracy_gain": 0.3,
            "strategy_reuse_rate": 0.9,
            "runtime_efficiency": 0.8,
            "identity_alignment": 0.9,
            "truth_alignment": 0.9,
            "reasoning_depth": 10,
        },
    )
    recompute_reward = incentive_engine.evaluate(
        "deep_reasoner",
        {
            "accuracy_gain": 0.3,
            "strategy_reuse_rate": 0.0,
            "runtime_efficiency": 0.2,
            "identity_alignment": 0.9,
            "truth_alignment": 0.9,
            "reasoning_depth": 99,
            "number_of_hypotheses": 100,
        },
    )

    assert reuse_reward["reward_score"] > recompute_reward["reward_score"]
    assert "reasoning_depth" in reuse_reward["not_rewarded"]
    assert "number_of_hypotheses" in reuse_reward["not_rewarded"]


def test_voting_eligibility_uses_progressive_suspension():
    eligibility = voting_eligibility_manager.evaluate(
        "complexity_estimator",
        {
            "trust_score": 0.7,
            "performance_score": 0.6,
            "identity_alignment": 0.8,
            "inflated_task_complexity": True,
        },
    )

    assert eligibility.can_vote is True
    assert eligibility.suspension_level == "PROBATION"
    assert eligibility.suspension_reason == "inflated_complexity_reporting"


def test_trust_and_influence_are_separate_from_authority():
    trust = trust_score_manager.update(
        "context_engine",
        {
            "reliability": 0.8,
            "alignment": 0.9,
            "efficiency": 0.7,
            "reuse_effectiveness": 0.8,
        },
    )
    influence = influence_controller.update(
        "context_engine",
        trust["trust_score"],
        {"authority_score": 0.3},
    )

    assert trust["trust_score"] > 0.0
    assert influence["influence_score"] > 0.0
    assert influence["authority_score"] == 0.3
    assert influence["constitutional_authority_modified"] is False


def test_incentive_reporter_emits_required_reports():
    report = incentive_reporter.evaluate_subsystem(
        "strategy_memory",
        {
            "accuracy_gain": 0.4,
            "strategy_reuse_rate": 0.8,
            "program_reuse_rate": 0.4,
            "cache_hit_rate": 0.7,
            "runtime_efficiency": 0.8,
            "identity_alignment": 0.9,
            "truth_alignment": 0.9,
            "total_cost": 0.3,
            "success_count": 1,
            "budget_usage": {
                "runtime": 1,
                "reasoning_depth": 1,
                "active_routes": 1,
                "governance_cycles": 1,
                "context_expansions": 1,
            },
        },
        {"task_complexity": 0.3},
    )

    incentive = report["CONSTITUTIONAL_INCENTIVE_REPORT"]
    economy = report["COGNITIVE_ECONOMY_REPORT"]
    governance_report = world_governance_reporter.build_report()

    assert incentive["subsystem_name"] == "strategy_memory"
    assert incentive["reward_score"] > 0.0
    assert "reuse_rate" in economy
    assert governance_report["CONSTITUTIONAL_INCENTIVE_REPORT"]
    assert governance_report["COGNITIVE_ECONOMY_REPORT"]
