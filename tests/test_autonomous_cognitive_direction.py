from runtime.world_governance import (
    CognitiveDirectionEngine,
    LongTermObjectives,
    PriorityAllocator,
    PurposeEngine,
    TradeoffManager,
    world_governance_reporter,
)


def test_purpose_engine_explains_meta_purpose_and_blocks_core_touch():
    purpose = PurposeEngine()

    assert "reliable" in purpose.why_this_goal_exists("maximize_trustworthy_cognition")
    assert purpose.purpose_alignment({
        "generalization": 0.9,
        "strategy_reuse": 0.8,
        "modifies": ["identity_continuity"],
    }) == 0.0


def test_cognitive_direction_estimates_distance_from_objectives():
    engine = CognitiveDirectionEngine(
        LongTermObjectives(
            generalization=0.30,
            process_understanding=0.25,
            strategy_reuse=0.15,
            context_reuse=0.10,
            memory_efficiency=0.10,
            runtime_efficiency=0.05,
            causal_reasoning=0.03,
            cognitive_diversity=0.02,
        )
    )

    report = engine.evaluate({
        "generalization": 0.2,
        "process_understanding": 0.1,
        "strategy_reuse_rate": 0.8,
        "available_resources": 0.7,
    })

    direction = report["AUTONOMOUS_DIRECTION_REPORT"]
    assert direction["objective_distances"]["generalization"] > 0.0
    assert direction["objective_distances"]["process_understanding"] > 0.0
    assert direction["target_domains"]


def test_priority_allocator_respects_budget_and_avoids_saturated_domains():
    allocation = PriorityAllocator().allocate(
        ["strategy_reuse", "memory_efficiency", "runtime_efficiency"],
        {
            "available_resources": 0.5,
            "saturated_domains": ["strategy_reuse"],
        },
    )

    assert sum(allocation.values()) <= 0.5
    assert allocation["memory_optimization"] > 0.0
    assert allocation["performance_optimization"] > 0.0
    assert allocation["strategy_refinement"] == 0.0


def test_tradeoff_manager_explains_exploration_and_reuse_pressure():
    tradeoffs = TradeoffManager().analyze({
        "exploration_need": 0.8,
        "reuse_pressure": 0.2,
        "strategy_reuse_rate": 0.7,
        "innovation_need": 0.3,
    })

    by_name = {item["tradeoff"]: item for item in tradeoffs}
    assert by_name["exploration_vs_exploitation"]["posture"] == "LEFT_PRESSURE"
    assert "policy" in by_name["reuse_vs_innovation"]


def test_direction_engine_prioritizes_purposeful_future_work_and_reports():
    engine = CognitiveDirectionEngine()

    report = engine.evaluate({
        "generalization": 0.2,
        "process_understanding": 0.15,
        "strategy_reuse_rate": 0.25,
        "context_reuse_rate": 0.2,
        "memory_efficiency": 0.5,
        "runtime_efficiency": 0.4,
        "causal_reasoning": 0.1,
        "diversity_score": 0.35,
        "available_resources": 0.6,
        "target_strategy_reuse": 0.65,
        "identity_risk": 0.1,
        "truth_risk": 0.1,
    })

    direction = report["AUTONOMOUS_DIRECTION_REPORT"]
    decision = report["direction_decision"]

    assert direction["selected_direction"] in {
        "EXPAND",
        "STABILIZE",
        "DIVERSIFY",
        "OPTIMIZE",
        "EXPLORE",
    }
    assert direction["expected_value"] > 0.0
    assert direction["purpose_alignment"] > 0.0
    assert sum(direction["resource_allocation"].values()) <= 0.6
    assert decision["recommendation"] in {
        "PRIORITIZE",
        "PRIORITIZE_WITH_LIMITS",
        "DEFER",
        "REQUIRE_REVIEW",
    }
    assert world_governance_reporter.build_report()["AUTONOMOUS_DIRECTION_REPORT"]


def test_direction_engine_does_not_invest_through_constitutional_violation():
    report = CognitiveDirectionEngine().evaluate({
        "modifies": ["human_support_mission"],
        "generalization": 0.9,
        "identity_risk": 0.1,
        "truth_risk": 0.1,
    })

    assert report["direction_decision"]["recommendation"] == "BLOCKED_BY_CONSTITUTION"
    assert report["kernel_decision"] is None
