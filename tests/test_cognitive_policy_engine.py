from runtime.world_governance import (
    CognitivePolicyEngine,
    WorldKernel,
)


def test_policy_engine_classifies_task_and_selects_policy():
    engine = CognitivePolicyEngine()

    report = engine.select_policy({
        "goal": "investigate_new_relation",
        "difficulty": 0.82,
        "novelty": 0.88,
        "risk_level": 0.4,
        "required_confidence": 0.9,
    })

    policy_report = report["COGNITIVE_POLICY_REPORT"]

    assert policy_report["Task Profile"]["novelty"] == 0.88
    assert policy_report["Selected Policy"]["policy"]["policy_id"] in {
        "novel_task_policy",
        "deep_investigation_policy",
    }
    assert policy_report["Selection Score"] > 0
    assert policy_report["Rejected Policies"]
    assert policy_report["Decision Graph"]["graph_type"] == "policy_decision_graph"


def test_known_task_policy_prioritizes_memory_reuse():
    engine = CognitivePolicyEngine()

    report = engine.select_policy({
        "goal": "reuse_known_pattern",
        "difficulty": 0.2,
        "novelty": 0.05,
        "risk_level": 0.1,
        "similarity_to_previous_tasks": 0.92,
        "memory_availability": 0.9,
    })

    selected = report["COGNITIVE_POLICY_REPORT"]["Selected Policy"]["policy"]
    schedule = report["COGNITIVE_POLICY_REPORT"]["Runtime Schedule"]

    assert selected["policy_id"] == "known_task_policy"
    assert schedule["mandatory_runtimes"] == [
        "memory_runtime",
        "evaluation_runtime",
    ]


def test_world_kernel_policy_evaluation_is_reported():
    kernel = WorldKernel()

    report = kernel.evaluate_cognitive_policy({
        "goal": "policy_report_task",
        "difficulty": 0.1,
        "risk_level": 0.1,
        "expected_search_cost": 0.1,
    })
    world_report = kernel.build_report()

    assert report["COGNITIVE_POLICY_REPORT"]["Selected Policy"]
    assert world_report["COGNITIVE_POLICY_REPORT"]["Selected Policy"]


def test_executive_cycle_is_policy_driven():
    kernel = WorldKernel()

    report = kernel.govern_cognitive_cycle({
        "goal": "known_governed_task",
        "difficulty": 0.2,
        "novelty": 0.05,
        "risk_level": 0.1,
        "similarity_to_previous_tasks": 0.95,
        "memory_availability": 0.95,
    })

    policy = report["COGNITIVE_POLICY_REPORT"]["Selected Policy"]["policy"]
    executive = report["WORLD_GOVERNANCE_EXECUTIVE_REPORT"]

    assert policy["policy_id"] == "known_task_policy"
    assert executive["Execution Graph"]["planning_basis"] == "cognitive_policy_engine"
    assert executive["Execution Intent"]["policy_evaluation"]["Selected Policy"][
        "policy"
    ]["policy_id"] == "known_task_policy"
    assert {
        item["runtime_id"]
        for item in executive["Activated Runtimes"]
    } == {"memory_runtime", "evaluation_runtime"}
    assert executive["Runtime Budgets"]["budget_policy"] == "known_task_policy"


def test_policy_learning_updates_statistics():
    engine = CognitivePolicyEngine()
    engine.select_policy({
        "goal": "reuse_known_pattern",
        "similarity_to_previous_tasks": 0.9,
        "memory_availability": 0.9,
        "risk_level": 0.1,
    })

    update = engine.record_policy_outcome(
        "known_task_policy",
        {
            "success": True,
            "confidence": 0.94,
            "cost": 0.2,
            "runtime": 2,
            "reuse_yield": 1.0,
        },
    )

    stats = update["learning_update"]

    assert stats["activation_count"] == 1
    assert stats["success_rate"] == 1.0
    assert stats["average_confidence"] == 0.94
