from copy import deepcopy

from runtime.budget.runtime_budget_enforcer import RuntimeBudgetEnforcer
from runtime.execution.execution_planner import ExecutionPlanner
from runtime.meta.meta_controller import MetaControllerEngine
from runtime.planning.production_budget import (
    PRODUCTION_MAX_ACTIVE_ROUTES,
    PRODUCTION_MAX_DEPENDENCY_DEPTH,
    PRODUCTION_MAX_REASONING_DEPTH,
)
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def _budget(**overrides):
    data = {
        "budget_snapshot_id": "budget_run_task_1",
        "budget_source": "current_reasoning_budget",
        "run_id": "run_budget",
        "task_id": "task_budget",
        "max_active_routes": 2,
        "max_reasoning_depth": 2,
        "max_dependency_depth": 3,
        "active_route_limit_scope": "TASK_CONCURRENT_ACTIVE_ROUTES",
        "reasoning_depth_limit_scope": "TASK_GOVERNED_REASONING_DEPTH",
    }
    data.update(overrides)
    return data


def _context(**overrides):
    routes = [
        {"route_id": "route_a", "rank": 1, "score": 0.9},
        {"route_id": "route_b", "rank": 2, "score": 0.8},
        {"route_id": "route_c", "rank": 3, "score": 0.7},
    ]
    data = {
        "run_id": "run_budget",
        "task_id": "task_budget",
        "enabled_tools": [
            "dependency_reasoning",
            "process_semantics",
            "causal_validation",
        ],
        "tool_selection_report": {
            "selected_tools": [
                "dependency_reasoning",
                "process_semantics",
                "causal_validation",
            ],
            "enabled_tools": [
                "dependency_reasoning",
                "process_semantics",
                "causal_validation",
            ],
        },
        "route_selection_report": {
            "available_routes": routes,
            "candidate_routes": routes,
            "active_routes": routes,
        },
        "planned_reasoning_depth": 4,
        "available_graph_depth": 9,
        "dependency_execution_depth": 6,
        "current_reasoning_budget": _budget(),
    }
    data.update(overrides)
    return data


def test_runtime_budget_receipt_has_schema_version_and_uses_authority():
    result = ExecutionPlanner().plan(runtime_context=_context())
    receipt = result["canonical_execution_plan"]["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert receipt["runtime_budget_schema_version"] == "1.0"
    assert receipt["runtime_budget_snapshot_id"] == "budget_run_task_1"
    assert receipt["maximum_active_routes"] == 2
    assert receipt["maximum_reasoning_depth"] == 2
    assert RuntimeBudgetEnforcer().verify_receipt(receipt) is True


def test_authoritative_production_budget_configuration_source_is_six():
    plan = ExecutionPlanner().build_authoritative_run_plan(
        run_id="run_production_budget",
        task_files=["task_a", "task_b", "task_c"],
        selected_mode="adaptive",
        execution_profile={"execution_profile": "adaptive"},
        cognitive_pipeline="adaptive",
        declared_budget={
            "budget_source": "main_adaptive_pre_execution_governed_defaults",
            "max_active_routes": PRODUCTION_MAX_ACTIVE_ROUTES,
            "max_reasoning_depth": PRODUCTION_MAX_REASONING_DEPTH,
            "max_dependency_depth": PRODUCTION_MAX_DEPENDENCY_DEPTH,
            "max_hypotheses": 4,
        },
    )

    assert PRODUCTION_MAX_ACTIVE_ROUTES == 6
    assert plan["declared_budget"]["max_active_routes"] == 6
    assert plan["maximum_active_routes"] == 6
    assert plan["maximum_reasoning_depth"] == 2
    assert plan["maximum_dependency_depth"] == 2
    assert plan["maximum_hypotheses"] == 4


def test_execution_planner_treats_none_active_routes_as_missing():
    result = ExecutionPlanner().plan(
        runtime_context=_context(
            introspection_report={"active_routes": None},
            route_selection_report={},
            planned_reasoning_depth=None,
        )
    )
    receipt = result["canonical_execution_plan"][
        "RUNTIME_BUDGET_ENFORCEMENT_REPORT"
    ]

    assert result["canonical_execution_plan"]["active_route_count"] == 3
    assert receipt["planned_reasoning_depth"] == 0


def test_missing_conflicting_and_stale_budget_inputs_fail_closed():
    enforcer = RuntimeBudgetEnforcer()
    missing = enforcer.build_receipt(
        budget={},
        context={"run_id": "run_budget", "task_id": "task_budget"},
        execution_plan_id="plan_1",
    )
    conflict = enforcer.build_receipt(
        budget=_budget(authority_conflict=True),
        context=_context(),
        execution_plan_id="plan_1",
    )
    stale = enforcer.build_receipt(
        budget=_budget(budget_state="STALE"),
        context=_context(),
        execution_plan_id="plan_1",
    )

    assert missing["runtime_budget_state"] == "RUNTIME_BUDGET_ENFORCEMENT_INPUT_UNAVAILABLE"
    assert conflict["runtime_budget_state"] == "RUNTIME_BUDGET_AUTHORITY_CONFLICT"
    assert stale["runtime_budget_state"] == "BUDGET_SNAPSHOT_STALE"


def test_cross_run_and_cross_task_budget_scope_are_rejected():
    enforcer = RuntimeBudgetEnforcer()
    cross_run = enforcer.build_receipt(
        budget=_budget(run_id="other_run"),
        context=_context(),
        execution_plan_id="plan_1",
    )
    cross_task = enforcer.build_receipt(
        budget=_budget(task_id="other_task"),
        context=_context(),
        execution_plan_id="plan_1",
    )

    assert cross_run["runtime_budget_state"] == "ROUTE_BUDGET_CROSS_RUN_CONTAMINATION"
    assert cross_task["runtime_budget_state"] == "ROUTE_BUDGET_CROSS_TASK_CONTAMINATION"


def test_selected_routes_are_not_active_or_completed_without_lifecycle():
    result = ExecutionPlanner().plan(runtime_context=_context())
    receipt = result["canonical_execution_plan"]["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert receipt["selected_route_count"] == 3
    assert receipt["admitted_route_count"] == 2
    assert receipt["current_active_route_count"] == 0
    assert receipt["peak_concurrent_active_route_count"] == 0
    assert receipt["completed_route_count"] == 0
    assert receipt["deferred_by_budget_route_count"] == 1
    assert receipt["route_budget_enforcement_state"] == "ROUTE_BUDGET_LIMIT_REACHED"


def test_sequential_activations_may_exceed_concurrent_limit_without_violation():
    lifecycle = [
        {"event_id": "1", "route_id": "route_a", "state": "ACTIVE_ROUTE"},
        {"event_id": "2", "route_id": "route_a", "state": "COMPLETED_ROUTE"},
        {"event_id": "3", "route_id": "route_b", "state": "ACTIVE_ROUTE"},
        {"event_id": "4", "route_id": "route_b", "state": "COMPLETED_ROUTE"},
        {"event_id": "5", "route_id": "route_c", "state": "ACTIVE_ROUTE"},
        {"event_id": "6", "route_id": "route_c", "state": "COMPLETED_ROUTE"},
    ]
    result = ExecutionPlanner().plan(
        runtime_context=_context(route_lifecycle_records=lifecycle)
    )
    receipt = result["canonical_execution_plan"]["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert receipt["total_route_activation_count"] == 3
    assert receipt["peak_concurrent_active_route_count"] == 1
    assert receipt["route_budget_violation_count"] == 0


def test_peak_concurrent_activity_over_limit_fails_closed():
    lifecycle = [
        {"event_id": "1", "route_id": "route_a", "state": "ACTIVE_ROUTE"},
        {"event_id": "2", "route_id": "route_b", "state": "ACTIVE_ROUTE"},
        {"event_id": "3", "route_id": "route_c", "state": "ACTIVE_ROUTE"},
    ]
    result = ExecutionPlanner().plan(
        runtime_context=_context(route_lifecycle_records=lifecycle)
    )
    plan = result["canonical_execution_plan"]
    receipt = plan["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert receipt["peak_concurrent_active_route_count"] == 3
    assert receipt["route_budget_enforcement_state"] == "ROUTE_BUDGET_EXCEEDED"
    assert plan["execution_plan_validation_state"] == "CONFLICTED"


def test_depth_values_remain_distinct_and_entry_is_authoritative():
    lifecycle = [
        {"event_id": "d1", "depth": 1, "state": "REASONING_DEPTH_ENTRY_AUTHORIZED"},
        {"event_id": "d2", "depth": 1, "state": "REASONING_DEPTH_EXITED"},
        {"event_id": "d3", "depth": 2, "state": "REASONING_DEPTH_ENTRY_AUTHORIZED"},
        {"event_id": "d4", "depth": 2, "state": "REASONING_DEPTH_EXITED"},
    ]
    result = ExecutionPlanner().plan(
        runtime_context=_context(reasoning_depth_lifecycle_records=lifecycle)
    )
    receipt = result["canonical_execution_plan"]["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert receipt["planned_reasoning_depth"] == 4
    assert receipt["maximum_entered_reasoning_depth"] == 2
    assert receipt["maximum_completed_reasoning_depth"] == 2
    assert receipt["available_graph_depth"] == 9
    assert receipt["dependency_execution_depth"] == 6
    assert receipt["depth_enforcement_state"] == "REASONING_DEPTH_LIMIT_REACHED"


def test_over_limit_depth_entry_conflicts_plan_integrity():
    lifecycle = [
        {"event_id": "d1", "depth": 3, "state": "REASONING_DEPTH_ENTRY_AUTHORIZED"},
    ]
    result = ExecutionPlanner().plan(
        runtime_context=_context(reasoning_depth_lifecycle_records=lifecycle)
    )
    plan = result["canonical_execution_plan"]
    receipt = plan["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert receipt["depth_enforcement_state"] == "REASONING_DEPTH_EXCEEDED"
    assert plan["execution_plan_validation_state"] == "CONFLICTED"


def test_route_scores_rankings_and_tool_selection_remain_unchanged():
    context = _context()
    before_routes = deepcopy(context["route_selection_report"]["active_routes"])
    before_tools = deepcopy(context["tool_selection_report"]["selected_tools"])
    result = ExecutionPlanner().plan(runtime_context=context)
    receipt = result["canonical_execution_plan"]["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert context["route_selection_report"]["active_routes"] == before_routes
    assert context["tool_selection_report"]["selected_tools"] == before_tools
    assert [row["route_score"] for row in receipt["route_dispositions"]] == [0.9, 0.8, 0.7]
    assert [row["route_rank"] for row in receipt["route_dispositions"]] == [1, 2, 3]


def test_reporting_consumes_budget_receipt_read_only():
    result = ExecutionPlanner().plan(runtime_context=_context())
    state = {
        "runtime_status": "completed",
        "operation": "budget_check",
        "EXECUTION_PLAN_REPORT": result["EXECUTION_PLAN_REPORT"],
        "RUNTIME_BUDGET_ENFORCEMENT_REPORT": result["EXECUTION_PLAN_REPORT"][
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT"
        ],
        "ENGINEERING_CONCLUSION": {"current_open_decision": "none"},
    }
    before = deepcopy(state["RUNTIME_BUDGET_ENFORCEMENT_REPORT"])

    rendered_once = DeterministicFinalReportRenderer().render(state)
    DeterministicFinalReportRenderer().render(state)

    assert "RUNTIME BUDGET ENFORCEMENT REPORT" in rendered_once
    assert "Selected Routes: 3" in rendered_once
    assert "Admitted Routes: 2" in rendered_once
    assert "Peak Concurrent Active Routes: 0" in rendered_once
    assert state["RUNTIME_BUDGET_ENFORCEMENT_REPORT"] == before


def test_human_report_displays_authoritative_budget_receipt_not_constant():
    result = ExecutionPlanner().plan(
        runtime_context=_context(
            current_reasoning_budget=_budget(max_active_routes=5),
        )
    )
    state = {
        "runtime_status": "completed",
        "operation": "budget_check",
        "EXECUTION_PLAN_REPORT": result["EXECUTION_PLAN_REPORT"],
        "RUNTIME_BUDGET_ENFORCEMENT_REPORT": result["EXECUTION_PLAN_REPORT"][
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT"
        ],
        "ENGINEERING_CONCLUSION": {"current_open_decision": "none"},
    }

    rendered = DeterministicFinalReportRenderer().render(state)

    assert "Maximum Active Routes: 5" in rendered
    assert f"Maximum Active Routes: {PRODUCTION_MAX_ACTIVE_ROUTES}" not in rendered


def test_production_runtime_budget_ceiling_is_six_without_depth_changes():
    routes = [
        {"route_id": f"route_{index:02d}", "rank": index, "score": 1.0 - index / 100}
        for index in range(1, 8)
    ]
    route_lifecycle = [
        {
            "event_id": f"route_{index:02d}_{'active' if index <= 6 else 'deferred'}",
            "route_id": route["route_id"],
            "state": "ACTIVE_ROUTE" if index <= 6 else "DEFERRED_BY_BUDGET",
        }
        for index, route in enumerate(routes, start=1)
    ]
    depth_lifecycle = [
        {"event_id": "depth_1_attempted", "depth": 1, "state": "ATTEMPTED_REASONING_DEPTH"},
        {"event_id": "depth_1_entered", "depth": 1, "state": "REASONING_DEPTH_ENTRY_AUTHORIZED"},
        {"event_id": "depth_2_attempted", "depth": 2, "state": "ATTEMPTED_REASONING_DEPTH"},
        {"event_id": "depth_2_entered", "depth": 2, "state": "REASONING_DEPTH_ENTRY_AUTHORIZED"},
        {"event_id": "depth_3_attempted", "depth": 3, "state": "ATTEMPTED_REASONING_DEPTH"},
        {"event_id": "depth_3_blocked", "depth": 3, "state": "DEPTH_ENTRY_BLOCKED_BY_BUDGET"},
    ]
    receipt = RuntimeBudgetEnforcer().build_receipt(
        budget=_budget(
            budget_snapshot_id="budget_gate_6_7_3",
            max_active_routes=PRODUCTION_MAX_ACTIVE_ROUTES,
            max_reasoning_depth=2,
            max_dependency_depth=3,
        ),
        context=_context(
            route_selection_report={
                "available_routes": routes,
                "candidate_routes": routes,
                "active_routes": routes,
            },
            route_lifecycle_records=route_lifecycle,
            reasoning_depth_lifecycle_records=depth_lifecycle,
            planned_reasoning_depth=3,
        ),
        execution_plan_id="plan_budget_gate_6_7_3",
        route_records=[
            {
                "route_id": route["route_id"],
                "route_rank": route["rank"],
                "route_score": route["score"],
            }
            for route in routes
        ],
        nodes=[
            {
                "execution_node_id": f"node_{index:02d}",
                "materialization_state": "MATERIALIZED",
            }
            for index in range(1, 8)
        ],
    )

    assert receipt["runtime_budget_state"] == "RUNTIME_BUDGET_FINALIZED"
    assert receipt["maximum_active_routes"] == PRODUCTION_MAX_ACTIVE_ROUTES
    assert receipt["admitted_route_count"] == 6
    assert receipt["deferred_by_budget_route_count"] == 1
    assert receipt["peak_concurrent_active_route_count"] == 6
    assert receipt["peak_concurrent_active_route_count"] <= PRODUCTION_MAX_ACTIVE_ROUTES
    assert receipt["route_budget_enforcement_state"] == "ROUTE_BUDGET_LIMIT_REACHED"
    assert receipt["attempted_overrun_state"] == "ATTEMPTED_OVERRUN_DETECTED"
    assert receipt["prevented_overrun_state"] == "OVERRUN_PREVENTED"
    assert receipt["realized_overrun_state"] == "NO_REALIZED_OVERRUN"
    assert receipt["maximum_reasoning_depth"] == 2
    assert receipt["depth_enforcement_state"] == "REASONING_DEPTH_LIMIT_REACHED"


def test_production_ceiling_does_not_expand_fewer_eligible_routes():
    result = ExecutionPlanner().plan(
        runtime_context=_context(
            current_reasoning_budget=_budget(
                max_active_routes=PRODUCTION_MAX_ACTIVE_ROUTES,
            ),
        )
    )
    receipt = result["canonical_execution_plan"]["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert receipt["selected_route_count"] == 3
    assert receipt["admitted_route_count"] == 3
    assert receipt["admitted_route_count"] < PRODUCTION_MAX_ACTIVE_ROUTES
    assert receipt["route_budget_enforcement_state"] == "ROUTE_BUDGET_ADMITTED"


def test_meta_default_production_route_ceiling_is_six_but_depth_stays_two():
    decision = MetaControllerEngine().decide(
        runtime_context={"mode": "adaptive"},
        reasoning_budget={
            "mode": "adaptive",
            "max_active_routes": PRODUCTION_MAX_ACTIVE_ROUTES,
            "max_reasoning_depth": 4,
        },
    )

    assert decision.max_active_routes == PRODUCTION_MAX_ACTIVE_ROUTES
    assert decision.max_reasoning_depth == 2


def test_regression_fixture_distinguishes_selected_twelve_from_active_routes():
    routes = [
        {"route_id": f"route_{index:02d}", "rank": index, "score": 1.0 - index / 100}
        for index in range(1, 13)
    ]
    result = ExecutionPlanner().plan(
        runtime_context=_context(
            route_selection_report={
                "available_routes": routes,
                "candidate_routes": routes,
                "active_routes": routes,
            },
            planned_reasoning_depth=4,
            current_reasoning_budget=_budget(
                budget_snapshot_id="budget_regression_2_12_4",
                max_active_routes=2,
                max_reasoning_depth=2,
            ),
        )
    )
    receipt = result["canonical_execution_plan"]["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert receipt["maximum_active_routes"] == 2
    assert receipt["available_route_count"] == 12
    assert receipt["candidate_route_count"] == 12
    assert receipt["selected_route_count"] == 12
    assert receipt["admitted_route_count"] == 2
    assert receipt["peak_concurrent_active_route_count"] == 0
    assert receipt["maximum_reasoning_depth"] == 2
    assert receipt["planned_reasoning_depth"] == 4
    assert receipt["maximum_entered_reasoning_depth"] == 0
    assert receipt["route_budget_enforcement_state"] == "ROUTE_BUDGET_LIMIT_REACHED"
    assert receipt["depth_enforcement_state"] == "REASONING_DEPTH_LIMIT_REACHED"


def test_budget_gate_prevents_route_and_depth_overruns_before_entry():
    routes = [
        {"route_id": f"route_{index:02d}", "rank": index, "score": 1.0 - index / 100}
        for index in range(1, 13)
    ]
    route_lifecycle = []
    for index, route in enumerate(routes, start=1):
        state = "ACTIVE_ROUTE" if index <= 2 else "DEFERRED_BY_BUDGET"
        route_lifecycle.append({
            "event_id": f"route_{index:02d}_{state.lower()}",
            "route_id": route["route_id"],
            "state": state,
        })
    for index, route in enumerate(routes[:2], start=1):
        route_lifecycle.append({
            "event_id": f"route_{index:02d}_released",
            "route_id": route["route_id"],
            "state": "RELEASED_ROUTE",
        })
    depth_lifecycle = [
        {"event_id": "depth_1_attempted", "depth": 1, "state": "ATTEMPTED_REASONING_DEPTH"},
        {"event_id": "depth_1_entered", "depth": 1, "state": "REASONING_DEPTH_ENTRY_AUTHORIZED"},
        {"event_id": "depth_1_exited", "depth": 1, "state": "REASONING_DEPTH_EXITED"},
        {"event_id": "depth_2_attempted", "depth": 2, "state": "ATTEMPTED_REASONING_DEPTH"},
        {"event_id": "depth_2_entered", "depth": 2, "state": "REASONING_DEPTH_ENTRY_AUTHORIZED"},
        {"event_id": "depth_2_exited", "depth": 2, "state": "REASONING_DEPTH_EXITED"},
        {"event_id": "depth_3_attempted", "depth": 3, "state": "ATTEMPTED_REASONING_DEPTH"},
        {"event_id": "depth_3_blocked", "depth": 3, "state": "DEPTH_ENTRY_BLOCKED_BY_BUDGET"},
        {"event_id": "depth_4_attempted", "depth": 4, "state": "ATTEMPTED_REASONING_DEPTH"},
        {"event_id": "depth_4_blocked", "depth": 4, "state": "DEPTH_ENTRY_BLOCKED_BY_BUDGET"},
    ]
    result = ExecutionPlanner().plan(
        runtime_context=_context(
            route_selection_report={
                "available_routes": routes,
                "candidate_routes": routes,
                "active_routes": routes,
            },
            route_lifecycle_records=route_lifecycle,
            reasoning_depth_lifecycle_records=depth_lifecycle,
            planned_reasoning_depth=4,
            current_reasoning_budget=_budget(
                budget_snapshot_id="budget_gate_2_12_4",
                max_active_routes=2,
                max_reasoning_depth=2,
            ),
        )
    )
    receipt = result["canonical_execution_plan"]["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert receipt["runtime_budget_state"] == "RUNTIME_BUDGET_FINALIZED"
    assert receipt["selected_route_count"] == 12
    assert receipt["admitted_route_count"] == 2
    assert receipt["deferred_by_budget_route_count"] == 10
    assert receipt["peak_concurrent_active_route_count"] == 2
    assert receipt["maximum_entered_reasoning_depth"] == 2
    assert receipt["maximum_completed_reasoning_depth"] == 2
    assert receipt["maximum_requested_reasoning_depth"] == 4
    assert receipt["depth_admission_count"] == 2
    assert receipt["depth_block_count"] == 2
    assert receipt["attempted_overrun_state"] == "ATTEMPTED_OVERRUN_DETECTED"
    assert receipt["prevented_overrun_state"] == "OVERRUN_PREVENTED"
    assert receipt["realized_overrun_state"] == "NO_REALIZED_OVERRUN"
    assert receipt["violation_reason"] == "NONE"
