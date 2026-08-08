from copy import deepcopy

from runtime.execution.execution_planner import ExecutionPlanner
from runtime.learning.training_report import build_training_report
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def _context():
    return {
        "run_id": "run_plan_001",
        "task_id": "task_plan_001",
        "enabled_tools": ["dependency_reasoning", "process_semantics"],
        "tool_selection_report": {
            "enabled_tools": ["dependency_reasoning", "process_semantics"],
            "selected_tools": ["dependency_reasoning", "process_semantics"],
            "selection_reason": {
                "dependency_reasoning": "dependency chain required",
                "process_semantics": "process semantics required",
            },
        },
        "selected_layers": ["dependency_reasoning_layer", "process_semantics_layer"],
        "route_selection_report": {
            "active_routes": [
                {"route_id": "route_dependency", "rank": 1, "score": 0.91},
                {"route_id": "route_process", "rank": 2, "score": 0.87},
                {"route_id": "route_auxiliary", "rank": 3, "score": 0.74},
            ]
        },
        "current_reasoning_budget": {
            "max_active_routes": 3,
            "max_reasoning_depth": 2,
            "max_dependency_depth": 3,
            "max_hypotheses": 4,
            "process_semantics_enabled": True,
        },
    }


def _plan_result():
    return ExecutionPlanner().plan(
        enabled_tools=["dependency_reasoning", "process_semantics"],
        attributed_concepts=["path_finding", "transformation_sequence"],
        active_routes=3,
        runtime_context=_context(),
    )


def test_canonical_execution_plan_has_version_and_distinct_id_domains():
    plan = _plan_result()["canonical_execution_plan"]

    assert plan["execution_plan_schema_version"] == "1.0"
    assert plan["execution_plan_id"].startswith("execution_plan_")
    assert plan["execution_plan_id"] != plan["run_id"]
    assert plan["execution_plan_state"] == "EXECUTION_PLAN_FINALIZED"
    assert plan["finalized"] is True
    assert plan["immutable"] is True
    assert plan["task_id"] not in {row["route_id"] for row in plan["route_reconciliation"]}
    for node in plan["nodes"]:
        assert node["execution_plan_id"] == plan["execution_plan_id"]
        assert node["execution_node_id"] != plan["execution_plan_id"]
        assert node["execution_node_id"] not in {row["route_id"] for row in plan["route_reconciliation"]}
        assert node["source_tool_selection_ids"]


def test_selected_tools_layers_and_routes_receive_one_disposition():
    plan = _plan_result()["canonical_execution_plan"]

    assert plan["selected_tool_count"] == 2
    assert plan["selected_tools_count"] == 2
    assert len(plan["tool_reconciliation"]) == 2
    assert plan["reconciled_tools_count"] == 2
    assert plan["selected_layer_count"] == 2
    assert plan["selected_layers_count"] == 2
    assert len(plan["layer_reconciliation"]) == 2
    assert plan["reconciled_layers_count"] == 2
    assert plan["active_route_count"] == 3
    assert plan["selected_routes_count"] == 3
    assert len(plan["route_reconciliation"]) == 3
    assert plan["reconciled_routes_count"] == 3
    assert plan["execution_nodes_materialized"] == plan["execution_node_count"]
    assert plan["maximum_active_routes"] == 3
    assert plan["maximum_reasoning_depth"] == 2
    assert plan["maximum_dependency_depth"] == 3
    assert plan["maximum_hypotheses"] == 4
    assert plan["route_balance"]["balanced"] is True
    for collection in ("tool_reconciliation", "layer_reconciliation", "route_reconciliation"):
        for row in plan[collection]:
            assert row["final_disposition"] in {
                "MATERIALIZED_AS_EXECUTION_NODE",
                "MERGED_INTO_EXECUTION_NODE",
                "PRUNED_BY_POLICY",
                "BLOCKED_BY_ADMISSION",
                "DEFERRED_BY_DEPENDENCY",
                "NOT_APPLICABLE_TO_FINAL_PLAN",
                "FAILED_TO_MATERIALIZE",
            }
            assert row["disposition_reason"]


def test_dependency_and_process_handoff_create_requests_without_invocation():
    plan = _plan_result()["canonical_execution_plan"]

    assert plan["dependency_activation_state"] == "REQUESTED"
    assert len(plan["dependency_activation_requests"]) == 1
    dependency_request = plan["dependency_activation_requests"][0]
    assert dependency_request["activation_request_id"].startswith("activation_request_")
    assert dependency_request["execution_node_id"] in {
        node["execution_node_id"] for node in plan["nodes"]
    }
    assert dependency_request["source_selection_id"]
    assert plan["process_stage_state"] == "MATERIALIZED"
    assert len(plan["process_stage_requests"]) == 1
    for node in plan["nodes"]:
        assert node["admission_state"] == "ADMISSION_REQUESTED"
        assert node["activation_state"] == "REQUESTED"
        assert node["invocation_state"] == "NOT_INVOKED"
        assert node["invocation_id"] is None


def test_route_merging_preserves_lineage_and_balances_counts():
    plan = _plan_result()["canonical_execution_plan"]
    merged = [
        row for row in plan["route_reconciliation"]
        if row["final_disposition"] == "MERGED_INTO_EXECUTION_NODE"
    ]

    assert merged
    for row in merged:
        assert row["merge_lineage"] == [row["route_id"]]
        assert row["merged_node_id"] == row["execution_node_id"]
    balance = plan["route_balance"]
    assert balance["active_route_count"] == (
        balance["MATERIALIZED_AS_EXECUTION_NODE"]
        + balance["MERGED_INTO_EXECUTION_NODE"]
        + balance["PRUNED_BY_POLICY"]
        + balance["BLOCKED_BY_ADMISSION"]
        + balance["DEFERRED_BY_DEPENDENCY"]
        + balance["NOT_APPLICABLE_TO_FINAL_PLAN"]
        + balance["FAILED_TO_MATERIALIZE"]
    )


def test_falsey_values_are_visible_and_do_not_become_missing():
    result = ExecutionPlanner().plan(
        enabled_tools=["dependency_reasoning"],
        active_routes=0,
        runtime_context={
            "run_id": "run_falsey",
            "task_id": "task_falsey",
            "enabled_tools": ["dependency_reasoning"],
            "tool_selection_report": {
                "enabled_tools": ["dependency_reasoning"],
                "selected_tools": ["dependency_reasoning"],
            },
            "current_reasoning_budget": {
                "max_dependency_depth": 0,
                "max_active_routes": 0,
            },
        },
    )
    plan = result["canonical_execution_plan"]
    row = plan["tool_reconciliation"][0]

    assert row["enabled_state"] is True
    assert row["selected_state"] is True
    assert row["planned_state"] is False
    assert row["invoked_state"] is False
    assert row["execution_count"] == 0
    assert row["final_disposition"] == "BLOCKED_BY_ADMISSION"
    assert plan["unresolved_selected_item_count"] == 0


def test_identical_inputs_are_idempotent_and_do_not_duplicate_nodes_or_requests():
    first = _plan_result()["canonical_execution_plan"]
    second = _plan_result()["canonical_execution_plan"]

    assert first["execution_plan_id"] == second["execution_plan_id"]
    assert first["execution_plan_fingerprint"] == second["execution_plan_fingerprint"]
    assert [node["execution_node_id"] for node in first["nodes"]] == [
        node["execution_node_id"] for node in second["nodes"]
    ]
    assert first["dependency_activation_requests"] == second["dependency_activation_requests"]


def test_execution_plan_report_is_concise_and_renderer_is_read_only():
    result = _plan_result()
    state = {
        "runtime_status": "completed",
        "operation": "replace_color",
        "leading_candidate": {"candidate_id": "candidate_1", "source": "test", "operation": "replace_color"},
        "EXECUTION_PLAN_REPORT": result["EXECUTION_PLAN_REPORT"],
        "ENGINEERING_CONCLUSION": {"current_open_decision": "none"},
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata={"execution_id": "run_plan_001", "timestamp": "now", "mode": "test"},
    )

    assert "EXECUTION PLAN REPORT" in report
    assert "Execution Plan State: CANONICAL_EXECUTION_PLAN_BOUND" in report
    assert "Planning State: EXECUTION_PLAN_FINALIZED" in report
    assert "Selected Tools Reconciled: 2/2" in report
    assert "Active Routes Reconciled: 3/3" in report
    assert "dependency_activation_requests" not in report
    assert result["canonical_execution_plan"]["execution_plan_validation_state"] == "VALID"


def test_current_run_canonical_plan_survives_training_report_and_human_binding():
    result = _plan_result()
    plan = result["canonical_execution_plan"]
    training_report = build_training_report(
        training_batch={"selected_task_count": 1},
        multi_task_results=[{
            "task": plan["task_id"],
            "status": "completed",
            "result": {
                **result,
                "retry_allowed": True,
                "episode_completed": False,
                "repair_attempts": 0,
            },
        }],
    )

    assert training_report["canonical_execution_plan"]["execution_plan_id"] == plan["execution_plan_id"]
    assert training_report["EXECUTION_PLAN_REPORT"]["execution_plan_id"] == plan["execution_plan_id"]
    assert training_report["ACTIVE_RUNTIME_REACHABILITY_AUDIT"]["execution_plan_id"] == plan["execution_plan_id"]
    assert (
        "CANONICAL_EXECUTION_PLAN_NOT_BOUND"
        not in training_report["ACTIVE_RUNTIME_REACHABILITY_AUDIT"]["reachability_gaps"]
    )

    rendered = DeterministicFinalReportRenderer().render(
        {
            "runtime_status": "completed",
            "operation": "training_batch",
            **training_report,
            "ENGINEERING_CONCLUSION": {"current_open_decision": "none"},
        },
        runtime_metadata={
            "execution_id": plan["run_id"],
            "timestamp": "now",
            "mode": "test",
        },
    )

    assert f"Execution Plan Id: {plan['execution_plan_id']}" in rendered
    assert "Execution Plan State: CANONICAL_EXECUTION_PLAN_BOUND" in rendered
    assert "Canonical Execution Plan Present: TRUE" in rendered


def test_legacy_plan_cannot_override_valid_canonical_plan_in_renderer():
    result = _plan_result()
    plan = result["canonical_execution_plan"]

    rendered = DeterministicFinalReportRenderer().render(
        {
            "runtime_status": "completed",
            "operation": "training_batch",
            "EXECUTION_PLAN_REPORT": {
                "execution_plan_id": "legacy_plan_wrong",
                "execution_plan_state": "LEGACY_PLAN_UNAVAILABLE",
                "selected_tool_count": 0,
            },
            "CANONICAL_EXECUTION_PLAN_REPORT": plan,
            "ENGINEERING_CONCLUSION": {"current_open_decision": "none"},
        },
        runtime_metadata={
            "execution_id": plan["run_id"],
            "timestamp": "now",
            "mode": "test",
        },
    )

    assert f"Execution Plan Id: {plan['execution_plan_id']}" in rendered
    assert "legacy_plan_wrong" not in rendered


def test_runtime_handoff_consumes_plan_without_invoking_components():
    result = _plan_result()
    handoff = ExecutionPlanner().consume_finalized_plan(
        result["canonical_execution_plan"]
    )

    assert handoff["orchestrator_consumption_state"] == "CANONICAL_PLAN_CONSUMED"
    assert handoff["runtime_stage_count"] == result["canonical_execution_plan"]["execution_node_count"]
    assert handoff["admission_record_count"] == result["canonical_execution_plan"]["execution_node_count"]
    assert handoff["activation_request_count"] == result["canonical_execution_plan"]["execution_node_count"]
    assert handoff["invocation_record_count"] == 0
    assert handoff["execution_invoked"] is False
    for stage in handoff["runtime_stages"]:
        assert stage["execution_node_id"]
        assert stage["stage_state"] == "MATERIALIZED"
        assert stage["invocation_state"] == "NOT_INVOKED"


def test_explicit_empty_selection_is_not_inferred_from_availability_or_enablement():
    result = ExecutionPlanner().plan(
        enabled_tools=["dependency_reasoning"],
        runtime_context={
            "run_id": "run_available_only",
            "task_id": "task_available_only",
            "tool_selection_report": {
                "available_tools": ["dependency_reasoning"],
                "enabled_tools": ["dependency_reasoning"],
                "selected_tools": [],
            },
        },
    )
    plan = result["canonical_execution_plan"]

    assert plan["selected_tool_count"] == 0
    assert plan["tool_reconciliation"] == []
    assert plan["execution_node_count"] == 0


def test_selected_but_disabled_tool_preserves_falsey_enablement():
    result = ExecutionPlanner().plan(
        runtime_context={
            "run_id": "run_selected_disabled",
            "task_id": "task_selected_disabled",
            "tool_selection_report": {
                "available_tools": ["dependency_reasoning"],
                "enabled_tools": [],
                "selected_tools": ["dependency_reasoning"],
            },
        },
    )
    row = result["canonical_execution_plan"]["tool_reconciliation"][0]

    assert row["available_state"] is True
    assert row["enabled_state"] is False
    assert row["selected_state"] is True
    assert row["planned_state"] is False


def test_activation_requests_keep_route_provenance():
    plan = _plan_result()["canonical_execution_plan"]
    request = plan["dependency_activation_requests"][0]
    node = next(
        item for item in plan["nodes"]
        if item["execution_node_id"] == request["execution_node_id"]
    )

    assert request["source_route_ids"] == node["source_route_ids"]
    assert request["source_route_ids"]


def test_finalized_plan_mutation_and_cross_run_handoff_fail_closed():
    planner = ExecutionPlanner()
    plan = _plan_result()["canonical_execution_plan"]

    stale = deepcopy(plan)
    stale["nodes"][0]["admission_state"] = "ADMITTED"
    stale_result = planner.consume_finalized_plan(stale)
    cross_run_result = planner.consume_finalized_plan(
        plan,
        runtime_context={"run_id": "different_run"},
    )
    changed_selection_result = planner.consume_finalized_plan(
        plan,
        runtime_context={
            "run_id": plan["run_id"],
            "tool_selection_report": {
                "selected_tools": ["dependency_reasoning"],
            },
        },
    )

    assert stale_result["orchestrator_consumption_state"] == "BLOCKED_BY_STALE_PLAN"
    assert stale_result["failure_reason"] == "PLAN_STALE"
    assert cross_run_result["orchestrator_consumption_state"] == "BLOCKED_BY_PLAN_IDENTITY"
    assert cross_run_result["failure_reason"] == "CROSS_RUN_PLAN_CONTAMINATION"
    assert changed_selection_result["orchestrator_consumption_state"] == "BLOCKED_BY_STALE_PLAN"
    assert changed_selection_result["failure_reason"] == "PLAN_STALE"


def test_blocked_process_semantics_has_exact_non_materialization_state():
    result = ExecutionPlanner().plan(
        enabled_tools=["process_semantics"],
        runtime_context={
            "run_id": "run_process_block",
            "task_id": "task_process_block",
            "tool_selection_report": {
                "enabled_tools": ["process_semantics"],
                "selected_tools": ["process_semantics"],
            },
            "current_reasoning_budget": {
                "process_semantics_enabled": False,
            },
        },
    )
    plan = result["canonical_execution_plan"]
    process_row = plan["tool_reconciliation"][0]
    process_request = plan["process_stage_requests"][0]

    assert process_row["final_disposition"] == "BLOCKED_BY_ADMISSION"
    assert process_row["disposition_reason"] == "process_semantics_enabled=False"
    assert plan["process_stage_state"] == "BLOCKED"
    assert process_request["non_materialization_reason"] == "process_semantics_enabled=False"


def test_authoritative_run_plan_survives_training_aggregation_over_runtime_reconstruction():
    planner = ExecutionPlanner()
    plan = planner.build_authoritative_run_plan(
        run_id="run_authoritative_001",
        task_files=["task_a.json", "task_b.json", "task_c.json"],
        selected_mode="adaptive",
        execution_profile={"execution_profile": "adaptive"},
        cognitive_pipeline="adaptive",
        declared_budget={
            "budget_source": "test_pre_execution_budget",
            "active_route_limit_scope": "RUN_WITH_TASK_ENTRIES",
            "reasoning_depth_limit_scope": "RUN_WITH_TASK_ENTRIES",
            "max_active_routes": 2,
            "max_reasoning_depth": 2,
            "max_dependency_depth": 2,
            "max_hypotheses": 2,
        },
    )
    admitted = planner.admit_authoritative_run_plan(plan, task_id="task_a.json")
    fingerprint = admitted["immutable_fingerprint"]

    report = build_training_report(
        training_batch={
            "selected_task_count": 3,
            "authoritative_execution_plan": admitted,
        },
        multi_task_results=[
            {
                "task": name,
                "status": "completed",
                "result": {
                    "run_id": admitted["run_id"],
                    "execution_plan_id": admitted["execution_plan_id"],
                    "cognitive_budget_report": {
                        "max_active_routes": 2,
                        "max_reasoning_depth": 2,
                    },
                    "introspection_report": {
                        "latest_report": {
                            "reasoning_depth": 4,
                            "active_routes": 12,
                            "pipeline_activity": {
                                "route_count": 12,
                                "reasoning_depth": 4,
                            },
                        }
                    },
                },
            }
            for name in ["task_a.json", "task_b.json", "task_c.json"]
        ],
    )

    aggregate = report["EXECUTION_PLAN_REPORT"]
    canonical = report["canonical_execution_plan"]
    budget = report["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert canonical["execution_plan_id"] == admitted["execution_plan_id"]
    assert canonical["planning_authority"] == "AUTHORITATIVE"
    assert aggregate["planning_state"] == "AUTHORITATIVE_PRE_EXECUTION_PLAN_FINALIZED"
    assert aggregate["temporal_authority_state"] == "PRE_EXECUTION_AUTHORITY_CONFIRMED"
    assert budget["runtime_budget_scope"] == "RUN_WITH_TASK_ENTRIES"
    assert budget["peak_concurrent_active_route_count"] == 12
    assert budget["maximum_entered_reasoning_depth"] == 4
    assert aggregate["retrospective_execution_plan"]["planning_authority"] == "DIAGNOSTIC_ONLY"
    assert canonical["immutable_fingerprint"] == fingerprint
    assert canonical["execution_plan_fingerprint"] == fingerprint
    assert [
        row["transition_name"]
        for row in aggregate["lifecycle_transitions"]
    ] == [
        "PLAN_BUILD_REQUESTED",
        "PLAN_BUILD_COMPLETED",
        "PLAN_FINALIZED",
        "PLAN_BOUND_TO_CURRENT_RUN",
        "EXECUTION_ADMITTED_WITH_PLAN_REFERENCE",
    ]
