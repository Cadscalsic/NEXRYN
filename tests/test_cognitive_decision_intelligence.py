from runtime.world_governance import (
    CognitiveDecisionIntelligenceEngine,
    CognitivePolicyEngine,
    WorldKernel,
)


def test_cdi_builds_decision_space_and_selects_decision():
    policy_engine = CognitivePolicyEngine()
    task_profile = policy_engine.classify_task({
        "goal": "investigate_novel_pattern",
        "difficulty": 0.8,
        "novelty": 0.85,
        "risk_level": 0.45,
    })
    evaluations = policy_engine.evaluate_policies(task_profile)

    report = CognitiveDecisionIntelligenceEngine().reason_over_policy_evaluations(
        task_profile,
        evaluations,
        policy_engine.policy_statistics,
    )

    cdi = report["COGNITIVE_DECISION_INTELLIGENCE_REPORT"]

    assert cdi["Decision Space"]["decision_count"] == len(evaluations)
    assert cdi["Candidate Decisions"]
    assert cdi["Simulation Results"]
    assert cdi["Selected Decision"]["Decision"]["Associated Policy"]["policy_id"]
    assert cdi["Decision Justification"]["why_selected"]
    assert cdi["Decision Confidence"]["Decision Confidence"] > 0


def test_cdi_preserves_rejected_decisions():
    policy_engine = CognitivePolicyEngine()
    task_profile = policy_engine.classify_task({
        "goal": "known_task",
        "similarity_to_previous_tasks": 0.9,
        "memory_availability": 0.9,
        "risk_level": 0.1,
    })
    evaluations = policy_engine.evaluate_policies(task_profile)

    report = CognitiveDecisionIntelligenceEngine().reason_over_policy_evaluations(
        task_profile,
        evaluations,
        policy_engine.policy_statistics,
    )

    rejected = report["COGNITIVE_DECISION_INTELLIGENCE_REPORT"][
        "Rejected Alternatives"
    ]

    assert rejected
    assert all("reason_for_rejection" in item for item in rejected)
    assert all("potential_future_applicability" in item for item in rejected)


def test_policy_selection_contains_decision_intelligence_report():
    policy_engine = CognitivePolicyEngine()

    report = policy_engine.select_policy({
        "goal": "reuse_known_pattern",
        "similarity_to_previous_tasks": 0.92,
        "memory_availability": 0.9,
        "risk_level": 0.1,
    })

    policy_report = report["COGNITIVE_POLICY_REPORT"]
    decision_report = policy_report["Cognitive Decision Intelligence Report"]

    assert decision_report["Selected Decision"]
    assert decision_report["Policy Ranking"]
    assert decision_report["Selected Decision"]["Decision"][
        "Associated Policy"
    ]["policy_id"] == policy_report["Selected Policy"]["policy"]["policy_id"]


def test_world_kernel_exposes_cognitive_decision_report():
    kernel = WorldKernel()

    report = kernel.evaluate_cognitive_decision({
        "goal": "decision_visible_task",
        "difficulty": 0.4,
        "risk_level": 0.2,
    })
    world_report = kernel.build_report()

    assert report["COGNITIVE_DECISION_INTELLIGENCE_REPORT"]["Decision Space"]
    assert world_report["COGNITIVE_DECISION_INTELLIGENCE_REPORT"][
        "Selected Decision"
    ]


def test_executive_cycle_begins_with_decision_reasoning():
    kernel = WorldKernel()

    report = kernel.govern_cognitive_cycle(
        {
            "goal": "decision_governed_cycle",
            "difficulty": 0.75,
            "novelty": 0.8,
            "risk_level": 0.45,
        },
        runtime_events=[
            {
                "runtime_id": "adaptive_search",
                "confidence": 0.7,
                "progress": 0.6,
                "truth_growth": 1,
                "knowledge_density": 0.6,
                "resource_consumption": 0.4,
            }
        ],
        execution_result={"success": True},
    )

    executive = report["WORLD_GOVERNANCE_EXECUTIVE_REPORT"]
    decision = report["COGNITIVE_DECISION_INTELLIGENCE_REPORT"]

    assert decision["Selected Decision"]["Decision"]["Decision ID"]
    assert executive["Cognitive Decision Intelligence Report"] == decision
    assert executive["Decision Learning"]["simulation_accuracy"] >= 0


def test_decision_outcome_learning_updates_statistics():
    engine = CognitiveDecisionIntelligenceEngine()
    policy_engine = CognitivePolicyEngine(decision_intelligence_engine=engine)
    task_profile = policy_engine.classify_task({
        "goal": "decision_learning_task",
        "similarity_to_previous_tasks": 0.85,
        "risk_level": 0.1,
    })
    evaluations = policy_engine.evaluate_policies(task_profile)
    report = engine.reason_over_policy_evaluations(
        task_profile,
        evaluations,
        policy_engine.policy_statistics,
    )

    update = engine.record_decision_outcome(
        report,
        {
            "success": True,
            "truth_yield": 0.6,
            "memory_yield": 1.0,
            "learning_value": 0.8,
        },
    )

    assert update["prediction_error"] >= 0
    assert update["decision_statistics"]["success_rate"] == 1.0
    assert update["world_model_decision_knowledge"]["preferred_policy"]
    assert update["dna_decision_traits"]["decision_stability"] >= 0
