from runtime.world_governance import (
    CognitiveParliament,
    RepresentativeRegistry,
    RepresentationBalancer,
    RepresentativeOpinion,
    world_governance_reporter,
)


def test_routine_tasks_do_not_invoke_parliament():
    parliament = CognitiveParliament()

    report = parliament.deliberate({
        "proposal_name": "solve_current_arc_task",
        "proposal_type": "routine_task",
    })

    parliament_report = report["COGNITIVE_PARLIAMENT_REPORT"]
    assert parliament_report["final_decision"] == "ROUTINE_TASK_NO_PARLIAMENT"
    assert parliament_report["representatives_consulted"] == 0


def test_constitutional_identity_is_not_a_representative():
    registry = RepresentativeRegistry()
    names = {representative.name for representative in registry.all()}

    assert "Constitutional Identity" not in names
    assert all(not representative.constitutional_exempt for representative in registry.all())


def test_constitutional_violation_is_blocked_before_kernel_approval():
    parliament = CognitiveParliament()

    report = parliament.deliberate({
        "proposal_name": "truth_priority_override",
        "proposal_type": "identity_impacting_change",
        "candidate_type": "program",
        "modifies": ["truth_priority"],
        "expected_value": 0.9,
        "generalization": 0.9,
    })

    parliament_report = report["COGNITIVE_PARLIAMENT_REPORT"]
    assert parliament_report["constitutional_status"] == "BLOCK"
    assert parliament_report["final_decision"] == "CONSTITUTIONAL_BLOCK"
    assert report["kernel_decision"] is None


def test_strategy_domination_is_detected_and_penalized():
    registry = RepresentativeRegistry()
    representatives = registry.voting_representatives()
    opinions = [
        RepresentativeOpinion(
            representative.name,
            "SUPPORT",
            0.8,
            0.7,
            0.1,
            "supporting test opinion",
        )
        for representative in representatives
    ]

    report = RepresentationBalancer().evaluate(
        opinions,
        representatives,
        {
            "dominant_strategy_share": 0.8,
            "dominant_representatives": ["Strategy Memory"],
        },
    )

    assert "strategy_domination" in report["domination_risks"]
    assert report["balancing_penalties"]["Strategy Memory"] > 0.0


def test_conflicting_perspectives_are_reported_explicitly():
    parliament = CognitiveParliament()

    report = parliament.deliberate(
        {
            "proposal_name": "expensive_accuracy_path",
            "proposal_type": "program_promotion",
            "candidate_type": "program",
            "expected_value": 0.75,
            "expected_accuracy_gain": 0.8,
            "expected_generalization_gain": 0.5,
            "expected_efficiency_gain": 0.7,
            "conceptual_diversity_gain": 0.05,
            "resource_cost": 0.6,
            "generalization": 0.7,
            "identity_risk": 0.2,
            "truth_risk": 0.2,
            "governance_risk": 0.2,
        },
        {
            "dominant_strategy_share": 0.7,
        },
    )

    parliament_report = report["COGNITIVE_PARLIAMENT_REPORT"]
    conflict_types = {
        item["conflict_type"]
        for item in report["conflict_analysis"]["conflicts"]
    }
    assert parliament_report["conflict_count"] >= 1
    assert "accuracy_vs_resource_cost" in conflict_types
    assert "efficiency_vs_diversity" in conflict_types


def test_safe_major_decision_is_deliberated_and_reported():
    parliament = CognitiveParliament()

    report = parliament.deliberate({
        "proposal_name": "contextual_transfer_strategy",
        "proposal_type": "strategy_promotion",
        "candidate_type": "strategy",
        "expected_value": 0.8,
        "generalization": 0.8,
        "strategy_reuse": 0.75,
        "expected_accuracy_gain": 0.6,
        "expected_generalization_gain": 0.8,
        "identity_risk": 0.1,
        "truth_risk": 0.1,
        "governance_risk": 0.1,
        "successful_observations": 3,
        "reusable": True,
        "admission_level": "TRUSTED_TOOL",
    })

    parliament_report = report["COGNITIVE_PARLIAMENT_REPORT"]
    assert parliament_report["representatives_consulted"] > 0
    assert parliament_report["support_count"] > parliament_report["reject_count"]
    assert parliament_report["constitutional_status"] == "PASS"
    assert parliament_report["final_decision"] in {
        "CONSENSUS_REACHED",
        "CONSENSUS_WITH_LIMITS",
        "ESCALATE_TO_WORLD_KERNEL",
    }
    assert world_governance_reporter.build_report()["COGNITIVE_PARLIAMENT_REPORT"]
