from runtime.resource_governance import (
    AdaptiveExecutionGovernor,
    BudgetPressureState,
    ExecutionPolicyName,
    LayerState,
    ResourceRequest,
    ResourceRequestDecisionType,
    RuntimeExecutionStrategy,
    RuntimeSignal,
    RuntimeSignalType,
    TerminalState,
)


def budgeted_governor(policy=ExecutionPolicyName.BALANCED, task="simple color remapping"):
    governor = AdaptiveExecutionGovernor(execution_policy=policy)
    profile = governor.profile_task(task)
    governor.create_initial_resource_plan(task)
    governor.create_budget(profile, execution_id="exec-1", task_id="task-1")
    return governor


def signal(signal_type, payload=None):
    return RuntimeSignal.create(
        execution_id="exec-1",
        task_id="task-1",
        signal_type=signal_type,
        source_layer="test",
        payload=payload or {},
    )


def test_budget_creation_from_task_profile():
    governor = budgeted_governor()

    budget = governor.cognitive_budget

    assert budget.execution_id == "exec-1"
    assert budget.policy == "BALANCED"
    assert budget.max_wall_time_seconds >= 30.0
    assert budget.max_candidates >= 10


def test_policy_specific_budget_allocation():
    low = budgeted_governor(ExecutionPolicyName.LOW_LATENCY).cognitive_budget
    accuracy = budgeted_governor(ExecutionPolicyName.MAX_ACCURACY).cognitive_budget

    assert low.max_wall_time_seconds < accuracy.max_wall_time_seconds
    assert low.max_candidates < accuracy.max_candidates
    assert low.max_report_cost_seconds < accuracy.max_report_cost_seconds


def test_budget_consumption_and_pressure_transitions():
    governor = budgeted_governor()
    budget = governor.cognitive_budget

    governor.consume_budget("candidates", budget.max_candidates * 0.7)
    status = governor.get_budget_status()

    assert status["budget_used"]["candidates"] == budget.max_candidates * 0.7
    assert status["budget_pressure_state"] in {
        BudgetPressureState.ELEVATED.value,
        BudgetPressureState.HIGH.value,
        BudgetPressureState.CRITICAL.value,
    }


def test_resource_request_approval_and_duplicate_rejection():
    governor = budgeted_governor()
    request = ResourceRequest(
        layer_name="semantic_compilation",
        resource_type="candidates",
        requested_amount=2,
        reason="all current candidates rejected",
        expected_value=0.8,
    )

    first = governor.request_resources(request)
    second = governor.request_resources(request)

    assert first.decision == ResourceRequestDecisionType.APPROVED
    assert second.decision == ResourceRequestDecisionType.REJECTED_DUPLICATE_REQUEST


def test_resource_request_rejection_for_low_value_and_policy():
    governor = budgeted_governor(ExecutionPolicyName.LOW_LATENCY)

    low_value = governor.request_resources(ResourceRequest(
        layer_name="semantic_compilation",
        resource_type="candidates",
        requested_amount=1,
        reason="weak request",
        expected_value=0.1,
    ))
    policy_blocked = governor.request_resources(ResourceRequest(
        layer_name="report_binding",
        resource_type="report_cost_seconds",
        requested_amount=0.1,
        reason="nice to have report",
        expected_value=0.8,
        urgency="LOW",
    ))

    assert low_value.decision == ResourceRequestDecisionType.REJECTED_LOW_VALUE
    assert policy_blocked.decision == ResourceRequestDecisionType.REJECTED_POLICY


def test_wall_time_and_candidate_budget_exhaustion_enters_best_effort_terminal_state():
    governor = budgeted_governor()
    budget = governor.cognitive_budget

    governor.consume_budget("wall_time_seconds", budget.max_wall_time_seconds + 1)

    assert governor.terminal_state_guard.terminal_record.state == "BEST_EFFORT_BUDGET_EXHAUSTED"
    assert governor.can_continue_execution() is False


def test_candidate_retry_repair_depth_and_route_enforcement():
    governor = budgeted_governor()
    budget = governor.cognitive_budget

    governor.consume_budget("candidates", budget.max_candidates + 1)
    assert governor.terminal_state_guard.terminal_record.state == "BEST_EFFORT_BUDGET_EXHAUSTED"

    governor = budgeted_governor()
    governor.consume_budget("retries", governor.cognitive_budget.max_retries)
    assert governor.evaluate_early_termination().terminal_state == TerminalState.RETRY_EXHAUSTED

    governor = budgeted_governor()
    governor.consume_budget("repairs", governor.cognitive_budget.max_repairs)
    assert governor.evaluate_early_termination().terminal_state == TerminalState.REPAIR_EXHAUSTED

    governor = budgeted_governor()
    governor.consume_budget("reasoning_depth", governor.cognitive_budget.max_reasoning_depth + 1)
    assert governor.terminal_state_guard.terminal_record.state == "BEST_EFFORT_BUDGET_EXHAUSTED"

    governor = budgeted_governor()
    governor.consume_budget("active_routes", governor.cognitive_budget.max_active_routes + 1)
    assert governor.terminal_state_guard.terminal_record.state == "BEST_EFFORT_BUDGET_EXHAUSTED"


def test_diminishing_return_detection_and_no_value_layer_suspension():
    governor = budgeted_governor()
    governor.activate_layer("semantic_compilation")

    state = governor.evaluate_diminishing_returns({"no_value": True})
    governor.evaluate_diminishing_returns({"duplicate_candidates": True})
    final_state = governor.evaluate_diminishing_returns({"unchanged_residual": True})
    governor.publish_signal(signal(RuntimeSignalType.LAYER_NO_VALUE_PRODUCED, {"layer_name": "semantic_compilation"}))

    assert state in {"DIMINISHING_RETURNS", "NO_VALUE"}
    assert final_state == "NO_VALUE"
    assert governor.get_layer_state("semantic_compilation") == LayerState.SUSPENDED


def test_deep_to_balanced_and_balanced_to_light_deescalation():
    governor = budgeted_governor()
    governor.escalation_controller.current_strategy = RuntimeExecutionStrategy.DEEP_EXECUTION

    first = governor.evaluate_deescalation("CONFIDENCE_STABILIZED")
    second = governor.evaluate_deescalation("RESIDUAL_COUNT_DECREASED")

    assert first.new_strategy == "BALANCED_EXECUTION"
    assert second.new_strategy == "LIGHT_EXECUTION"
    assert first.deescalated is True
    assert second.deescalated is True


def test_exact_success_termination_and_minimal_finalization():
    governor = budgeted_governor()
    governor.activate_layer("topology_reasoning")

    governor.publish_signal(signal(RuntimeSignalType.EXACT_SUCCESS))

    assert governor.terminal_state_guard.terminal_record.state == "EXACT_SUCCESS"
    assert governor.terminal_state_guard.minimal_finalization is True
    assert governor.get_layer_state("topology_reasoning") == LayerState.SUSPENDED
    assert governor.can_continue_execution() is False


def test_accepted_partial_success_and_best_effort_early_termination():
    governor = budgeted_governor()
    decision = governor.evaluate_early_termination(partial_success={
        "policy_permits": True,
        "accuracy": 0.95,
        "accuracy_threshold": 0.9,
        "remaining_residual": 0,
        "residual_threshold": 0,
    })

    assert decision.terminal_state == TerminalState.ACCEPTED_PARTIAL_SUCCESS
    assert governor.terminal_state_guard.terminal_record.state == "ACCEPTED_PARTIAL_SUCCESS"


def test_no_activation_or_retry_after_exact_success_and_critical_work_allowed():
    governor = budgeted_governor()
    governor.publish_signal(signal(RuntimeSignalType.EXACT_SUCCESS))

    transition = governor.request_capability("topology_reasoning", execution_id="exec-1")
    request = governor.request_resources(ResourceRequest(
        layer_name="retry",
        resource_type="retries",
        requested_amount=1,
        reason="retry after success",
        expected_value=1.0,
    ))

    assert transition.approved is False
    assert transition.rejection_reason == "TERMINAL_STATE_REACHED"
    assert request.decision == ResourceRequestDecisionType.REJECTED_TERMINAL_STATE
    assert governor.allow_critical_completion_work("minimal_execution_metadata") is True
    assert governor.terminal_state_guard.allow("deep_reasoning") is False


def test_bounded_post_success_duration_and_report():
    governor = budgeted_governor()
    governor.publish_signal(signal(RuntimeSignalType.EXACT_SUCCESS))

    report = governor.build_cognitive_resource_governance_report(diagnostic=True)
    rendered = governor.render_cognitive_resource_governance_report()

    assert report["COGNITIVE_RESOURCE_GOVERNANCE_REPORT"] is True
    assert report["final_strategy"] == "MINIMAL_FINALIZATION"
    assert report["post_success_duration"] <= governor.cognitive_budget.max_post_success_seconds
    assert report["observability_metrics"]["early_termination_triggered"] is True
    assert "COGNITIVE RESOURCE GOVERNANCE REPORT" in rendered
    assert "budget_ledger" in report
