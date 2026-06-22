from runtime.world_governance import (
    CognitiveDiversityManager,
    CognitiveEvolutionPolicyEngine,
    EvolutionObjectives,
    GrowthOpportunityDetector,
    InvestmentAllocator,
    StagnationDetector,
    world_governance_reporter,
)


def test_growth_opportunities_are_detected_from_context_and_potential_worlds():
    detector = GrowthOpportunityDetector()

    opportunities = detector.detect(
        {
            "concepts": [
                {"name": "relational_shape", "value": 0.8, "maturity": 0.2},
            ],
            "strategies": [
                {"name": "symmetry_probe", "reuse_count": 6, "success_rate": 0.8},
            ],
        },
        {
            "POTENTIAL_WORLDS_REPORT": {
                "candidate_name": "context_bridge",
                "candidate_type": "context",
                "world_score": 0.3,
                "identity_risk": 0.1,
                "truth_risk": 0.1,
                "governance_risk": 0.1,
            }
        },
    )

    names = {item.target for item in opportunities}
    assert {"relational_shape", "symmetry_probe", "context_bridge"} <= names


def test_investment_allocator_freezes_saturated_and_locked_targets():
    allocator = InvestmentAllocator()
    opportunities = GrowthOpportunityDetector().detect({
        "concepts": [
            {"name": "stable_truth_anchor", "value": 0.9, "maturity": 0.1},
            {"name": "saturated_symmetry", "value": 0.9, "maturity": 0.1},
        ],
        "locked_truths": ["stable_truth_anchor"],
        "saturated_concepts": ["saturated_symmetry"],
    })

    decisions = allocator.allocate(
        opportunities,
        {
            "locked_truths": ["stable_truth_anchor"],
            "saturated_concepts": ["saturated_symmetry"],
        },
        {},
    )

    action_by_target = {item.target: item.action for item in decisions}
    assert action_by_target["stable_truth_anchor"] == "FREEZE"
    assert action_by_target["saturated_symmetry"] == "FREEZE"


def test_stagnation_detector_identifies_repeated_low_gain_cycles():
    assessment = StagnationDetector().assess({
        "repeated_governance_cycles": 4,
        "learning_improvement_rate": 0.0,
        "reasoning_cycles_without_accuracy_gain": 3,
    })

    assert assessment.stagnation_level == "HIGH"
    assert "governance" in assessment.affected_domains
    assert "learning" in assessment.affected_domains


def test_diversity_manager_prevents_single_path_domination_safely():
    report = CognitiveDiversityManager().evaluate({
        "dominant_concept_share": 0.8,
        "dominant_strategy_share": 0.7,
        "active_reasoning_paths": 1,
        "alternative_explanations": 1,
    })

    assert report["diversity_score"] < 0.5
    assert "prevent_concept_monopoly" in report["interventions"]
    assert report["identity_safe"] is True


def test_cognitive_evolution_policy_report_prioritizes_safe_investment():
    engine = CognitiveEvolutionPolicyEngine(
        EvolutionObjectives(
            reasoning_accuracy=0.2,
            generalization=0.3,
            strategy_reuse=0.2,
            memory_efficiency=0.1,
            contextual_understanding=0.1,
            cognitive_diversity=0.05,
            runtime_efficiency=0.05,
        )
    )

    report = engine.evaluate(
        {
            "concepts": [
                {"name": "object_relation", "value": 0.8, "maturity": 0.2},
                {"name": "color_lock", "value": 0.9, "maturity": 0.2},
            ],
            "strategies": [
                {"name": "symmetry_probe", "reuse_count": 7, "success_rate": 0.85},
            ],
            "underrepresented_contexts": [
                {"name": "temporal_context", "importance": 0.7, "maturity": 0.1},
            ],
            "saturated_concepts": ["color_lock"],
            "cognitive_investment_budget": 0.6,
            "dominant_strategy_share": 0.7,
            "active_reasoning_paths": 1,
            "learning_improvement_rate": 0.0,
            "reasoning_cycles_without_accuracy_gain": 3,
        },
        {
            "POTENTIAL_WORLDS_REPORT": {
                "candidate_name": "generalized_context_bridge",
                "candidate_type": "context",
                "world_score": 0.25,
                "identity_risk": 0.1,
                "truth_risk": 0.1,
                "governance_risk": 0.1,
            }
        },
    )

    cognitive = report["COGNITIVE_EVOLUTION_REPORT"]
    actions = {
        item["target"]: item["action"]
        for item in cognitive["investment_allocations"]
    }

    assert cognitive["stagnation_level"] in {"MEDIUM", "HIGH"}
    assert "color_lock" in cognitive["frozen_concepts"]
    assert actions["object_relation"] == "EXPAND"
    assert actions["temporal_context"] == "DIVERSIFY"
    assert cognitive["resource_budget_usage"]["used"] <= 0.6
    assert world_governance_reporter.build_report()["COGNITIVE_EVOLUTION_REPORT"]
