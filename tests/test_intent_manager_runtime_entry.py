import pytest

from runtime.execution.execution_planner import ExecutionPlanner
from runtime.intent import IntentCurrentAuthorityEngine, IntentLifecycleStatus
from runtime.intent.intent_manager import IntentManager, build_runtime_objective_ref


def _manager(tmp_path):
    engine = IntentCurrentAuthorityEngine(tmp_path / "intent")
    return IntentManager(authority_engine=engine), engine


def test_runtime_objective_creates_authority_free_proposal_and_active_intent(tmp_path):
    manager, engine = _manager(tmp_path)

    result = manager.orchestrate_runtime_objective(
        "governed_task_execution:task_a.json",
        run_id="run_a",
        task_id="task_a.json",
        source_type="TASK_DERIVED",
        objective_ref="governed_task_execution:task_a.json",
    )
    current = engine.get_current_intent_state(result.intent_id)

    assert manager.authority == "NONE"
    assert result.orchestration_state == "INTENT_OPERATIONAL_ENTRY_ESTABLISHED"
    assert result.assessment_state == "INTENT_ASSESSMENT_PASSED"
    assert result.intent_status == IntentLifecycleStatus.ACTIVE.value
    assert result.telemetry["intent_proposal_created"] is True
    assert result.telemetry["goal_activation"] is False
    assert result.telemetry["plan_activation"] is False
    assert current["intent_id"] == result.intent_id
    assert current["goal_authority"] == "NONE"
    assert current["planning_authority"] == "NONE"
    assert current["budget_authority"] == "NONE"
    assert current["execution_authority"] == "NONE"
    assert current["truth_authority"] == "NONE"
    assert current["knowledge_authority"] == "NONE"


@pytest.mark.parametrize(
    "objective",
    [None, "", "NOT_DEFINED", "COMPLETED", "report: final", "telemetry: marker"],
)
def test_invalid_and_diagnostic_objectives_fail_closed(tmp_path, objective):
    manager, _ = _manager(tmp_path)

    result = manager.orchestrate_runtime_objective(objective, run_id="run_a")

    assert result.orchestration_state == "NO_INTENT_PROPOSAL"
    assert result.intent_proposal_id is None
    assert result.intent_decision_id is None
    assert result.telemetry["intent_proposal_created"] is False


def test_duplicate_objective_reuses_current_active_intent(tmp_path):
    manager, _ = _manager(tmp_path)

    first = manager.orchestrate_runtime_objective(
        "governed_task_execution:task_a.json",
        run_id="run_a",
        task_id="task_a.json",
    )
    second = manager.orchestrate_runtime_objective(
        "governed_task_execution:task_a.json",
        run_id="run_a",
        task_id="task_a.json",
    )

    assert first.intent_id == second.intent_id
    assert first.intent_proposal_id is not None
    assert second.intent_proposal_id is None
    assert second.orchestration_state == "CURRENT_INTENT_ALREADY_ACTIVE"


def test_cross_run_identity_is_stable_and_provenance_is_separate(tmp_path):
    first_manager, _ = _manager(tmp_path / "first")
    second_manager, _ = _manager(tmp_path / "second")

    first = first_manager.orchestrate_runtime_objective(
        "governed_task_execution:task_a.json",
        run_id="run_a",
        task_id="task_a.json",
    )
    second = second_manager.orchestrate_runtime_objective(
        "governed_task_execution:task_a.json",
        run_id="run_b",
        task_id="task_a.json",
    )

    assert first.intent_id == second.intent_id
    assert first.run_id != second.run_id
    assert first.objective_ref == second.objective_ref


def test_noncurrent_existing_intent_is_not_auto_reactivated(tmp_path):
    manager, engine = _manager(tmp_path)
    active = manager.orchestrate_runtime_objective(
        "governed_task_execution:task_a.json",
        run_id="run_a",
        task_id="task_a.json",
    )
    current = engine.get_current_intent_state(active.intent_id)
    invalidated = engine.current_state_from_decision(
        current,
        engine.invalidate_intent(current, reason="test_noncurrent"),
    )
    engine.persist_current_state(invalidated)

    result = manager.orchestrate_runtime_objective(
        "governed_task_execution:task_a.json",
        run_id="run_a",
        task_id="task_a.json",
    )

    assert result.orchestration_state == "NONCURRENT_INTENT_EXISTS"
    assert result.intent_status == IntentLifecycleStatus.INVALIDATED.value
    assert result.intent_proposal_id is None


@pytest.mark.parametrize(
    "source_type,expected_source",
    [
        ("SELF_IMPROVEMENT_PROPOSED", "SELF_IMPROVEMENT_PROPOSED"),
        ("REPAIR_PROPOSED", "REPAIR_PROPOSED"),
        ("TRAINING_OBJECTIVE", "TRAINING_PROPOSED"),
    ],
)
def test_sensitive_sources_remain_proposals_or_governed_by_authority(
    tmp_path,
    source_type,
    expected_source,
):
    manager, _ = _manager(tmp_path)

    result = manager.orchestrate_runtime_objective(
        "governed_task_execution:task_a.json",
        run_id="run_a",
        task_id="task_a.json",
        source_type=source_type,
    )

    assert result.source == expected_source
    assert result.authority_source == "intent_current_authority_engine"
    assert result.telemetry["budget_authority"] == "NONE"
    assert result.telemetry["execution_authority"] == "NONE"


def test_runtime_plan_naturally_reaches_intent_manager_without_consumption(tmp_path):
    plan = ExecutionPlanner().build_authoritative_run_plan(
        run_id="run_intent_manager",
        task_files=["task_a.json"],
        selected_mode="adaptive",
        cognitive_pipeline="adaptive",
        declared_budget={
            "max_active_routes": 6,
            "max_reasoning_depth": 2,
            "max_dependency_depth": 2,
        },
        intent_state_dir=tmp_path / "intent",
    )

    assert plan["intent_manager_owner"] == "intent_manager"
    assert plan["intent_manager_authority"] == "NONE"
    assert plan["natural_intent_authority_applicability"] == "APPLICABLE"
    assert plan["natural_intent_proposal_count"] == 1
    assert plan["natural_intent_assessment_count"] == 1
    assert plan["natural_intent_authority_invocation_count"] == 1
    assert plan["natural_active_intent_count"] == 1
    assert plan["intent_cognitive_consumption"] is False
    assert plan["goal_active_authority"] == "NONE"
    assert plan["planning_authority"] == "AUTHORITATIVE"
    assert plan["declared_budget"]["max_active_routes"] == 6


def test_objective_ref_helper_uses_task_identity_not_run_identity():
    assert build_runtime_objective_ref("data/tasks/task_a.json") == (
        "governed_task_execution:task_a.json"
    )


def test_intent_manager_attack_matrix_has_zero_authority_bypasses(tmp_path):
    scenarios = [
        {"name": "empty objective", "objective": ""},
        {"name": "missing objective", "objective": None},
        {"name": "not defined objective", "objective": "NOT_DEFINED"},
        {"name": "diagnostic status string", "objective": "COMPLETED"},
        {"name": "report text", "objective": "report: final"},
        {"name": "same objective duplicate first", "objective": "governed_task_execution:dup.json"},
        {"name": "same objective duplicate second", "objective": "governed_task_execution:dup.json"},
        {"name": "cross run identity a", "objective": "governed_task_execution:cross.json", "run_id": "run_a"},
        {"name": "cross run identity b", "objective": "governed_task_execution:cross.json", "run_id": "run_b"},
        {"name": "task local objective", "objective": "governed_task_execution:local.json", "task_local": True},
        {"name": "copied proposal id", "objective": {"objective": "intent_proposal_copied"}},
        {"name": "copied intent id", "objective": {"objective": "intent_copied"}},
        {"name": "corrupt fingerprint label", "objective": "intent_fingerprint_corrupt"},
        {"name": "missing source", "objective": "governed_task_execution:missing_source.json", "source_type": ""},
        {"name": "missing provenance", "objective": "governed_task_execution:missing_provenance.json"},
        {"name": "direct active request", "objective": "ACTIVE"},
        {"name": "assessment bypass attempt", "objective": "BYPASS_ASSESSMENT"},
        {"name": "authority bypass attempt", "objective": "BYPASS_AUTHORITY"},
        {"name": "self improvement", "objective": "governed_task_execution:self.json", "source_type": "SELF_IMPROVEMENT_PROPOSED"},
        {"name": "repair", "objective": "governed_task_execution:repair.json", "source_type": "REPAIR_PROPOSED"},
        {"name": "training", "objective": "governed_task_execution:training.json", "source_type": "TRAINING_OBJECTIVE"},
        {"name": "direct goal activation", "objective": "activate_goal"},
        {"name": "direct plan activation", "objective": "activate_plan"},
        {"name": "budget grant", "objective": "grant_budget"},
        {"name": "execution grant", "objective": "grant_execution"},
        {"name": "truth mutation", "objective": "mutate_truth"},
        {"name": "knowledge mutation", "objective": "mutate_knowledge"},
    ]
    manager, _ = _manager(tmp_path)
    bypasses = []
    results = []

    for scenario in scenarios:
        result = manager.orchestrate_runtime_objective(
            scenario["objective"],
            run_id=scenario.get("run_id", "run_attack"),
            task_id=scenario["name"],
            source_type=scenario.get("source_type", "TASK_DERIVED"),
            task_local=scenario.get("task_local", True),
        )
        results.append(result)
        telemetry = result.telemetry
        if (
            manager.authority != "NONE"
            or telemetry["goal_activation"]
            or telemetry["plan_activation"]
            or telemetry["budget_authority"] != "NONE"
            or telemetry["execution_authority"] != "NONE"
            or telemetry["truth_authority"] != "NONE"
            or telemetry["knowledge_authority"] != "NONE"
            or telemetry["capability_authority"] != "NONE"
        ):
            bypasses.append(scenario["name"])

    assert len(scenarios) == 27
    assert bypasses == []
    assert all(result.authority_source == "intent_current_authority_engine" for result in results)
