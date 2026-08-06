from copy import deepcopy

from runtime.dependency.dependency_execution_runtime import DependencyExecutionRuntime
from runtime.execution.execution_dispatcher import ExecutionDispatcher
from runtime.execution.execution_planner import ExecutionPlanner
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def _plan_result():
    context = {
        "run_id": "run_dep_exec_001",
        "task_id": "task_dep_exec_001",
        "enabled_tools": ["dependency_reasoning"],
        "tool_selection_report": {
            "enabled_tools": ["dependency_reasoning"],
            "selected_tools": ["dependency_reasoning"],
        },
        "route_selection_report": {
            "active_routes": [
                {"route_id": "route_dependency_exec", "rank": 1, "score": 0.93},
            ],
        },
        "current_reasoning_budget": {
            "max_dependency_depth": 3,
            "max_active_routes": 1,
        },
    }
    return ExecutionPlanner().plan(
        enabled_tools=["dependency_reasoning"],
        attributed_concepts=["alpha_dependency"],
        active_routes=1,
        runtime_context=context,
    )


def _link(run_id="run_dep_exec_001", task_id="task_dep_exec_001", **overrides):
    link = {
        "dependency_link_id": "dependency_link_alpha_beta",
        "source": "alpha_dependency",
        "target": "beta_dependency",
        "dependency_type": "requires",
        "direction": "source_to_target",
        "run_id": run_id,
        "task_id": task_id,
        "confidence": 0.81,
        "origin": "unit_fixture",
    }
    link.update(overrides)
    return link


def _context(links):
    plan = _plan_result()["canonical_execution_plan"]
    return {
        "run_id": plan["run_id"],
        "task_id": plan["task_id"],
        "tool_selection_report": {
            "selected_tools": ["dependency_reasoning"],
        },
        "dependency_graph_report": {
            "dependency_links": links,
        },
    }


def test_dependency_execution_receipt_has_schema_and_distinct_id_domains():
    plan = _plan_result()["canonical_execution_plan"]
    receipt = DependencyExecutionRuntime().execute(
        canonical_plan=plan,
        runtime_context=_context([_link()]),
    )
    chain = receipt["chain_records"][0]
    result = receipt["result_records"][0]

    assert receipt["dependency_execution_schema_version"] == "1.0"
    assert receipt["dependency_execution_id"] != receipt["execution_plan_id"]
    assert receipt["dependency_execution_id"] != receipt["invocation_id"]
    assert chain["dependency_chain_id"] != chain["ordered_link_ids"][0]
    assert result["dependency_result_id"] != receipt["dependency_execution_id"]
    assert receipt["execution_plan_id"] == plan["execution_plan_id"]
    assert receipt["execution_node_id"] == plan["dependency_activation_requests"][0]["execution_node_id"]
    assert receipt["activation_request_id"] == plan["dependency_activation_requests"][0]["activation_request_id"]
    assert receipt["invocation_id"].startswith("invocation_")


def test_loaded_links_do_not_imply_eligible_or_used_links():
    plan = _plan_result()["canonical_execution_plan"]
    unsupported = _link(dependency_type="observes")
    receipt = DependencyExecutionRuntime().execute(
        canonical_plan=plan,
        runtime_context=_context([unsupported]),
    )

    assert receipt["input_link_count"] == 1
    assert receipt["eligible_link_count"] == 0
    assert receipt["planned_chain_count"] == 0
    assert receipt["attempted_chain_count"] == 0
    assert receipt["executed_chain_count"] == 0
    assert receipt["used_link_count"] == 0
    assert receipt["maximum_executed_depth"] == 0
    assert receipt["result_count"] == 0
    assert receipt["dependency_coverage"] == "NOT_DEFINED"
    assert receipt["non_execution_reason"] == "NO_ELIGIBLE_DEPENDENCY_LINKS"
    assert receipt["link_eligibility"][0]["eligibility_state"] == "TYPE_UNSUPPORTED"


def test_empty_valid_link_collection_remains_visible_without_invocation():
    plan = _plan_result()["canonical_execution_plan"]
    receipt = DependencyExecutionRuntime().execute(
        canonical_plan=plan,
        runtime_context=_context([]),
    )

    assert receipt["input_link_count"] == 0
    assert receipt["eligible_link_count"] == 0
    assert receipt["attempted_chain_count"] == 0
    assert receipt["non_execution_reason"] == "NO_DEPENDENCY_LINK_RECORDS"


def test_admitted_request_invokes_existing_executor_once_and_captures_result():
    plan = _plan_result()["canonical_execution_plan"]
    runtime = DependencyExecutionRuntime()
    receipt = runtime.execute(
        canonical_plan=plan,
        runtime_context=_context([_link()]),
    )
    duplicate = runtime.execute(
        canonical_plan=plan,
        runtime_context=_context([_link()]),
    )
    chain = receipt["chain_records"][0]
    result = receipt["result_records"][0]

    assert receipt == duplicate
    assert receipt["execution_state"] == "RESULT_CAPTURED"
    assert receipt["request_consumption_state"] == "REQUEST_ADMITTED"
    assert receipt["planned_chain_count"] == 1
    assert receipt["attempted_chain_count"] == 1
    assert receipt["executed_chain_count"] == 1
    assert receipt["used_link_count"] == 1
    assert receipt["maximum_executed_depth"] == 1
    assert chain["chain_state"] == "CHAIN_EXECUTED"
    assert chain["ordered_link_ids"] == ["dependency_link_alpha_beta"]
    assert chain["used_link_ids"] == ["dependency_link_alpha_beta"]
    assert result["dependency_execution_id"] == receipt["dependency_execution_id"]
    assert result["invocation_id"] == receipt["invocation_id"]
    assert result["dependency_chain_id"] == chain["dependency_chain_id"]
    assert receipt["process_context_count"] == 0
    assert receipt["causal_context_count"] == 0
    assert receipt["evidence_acceptance_state"] == "NOT_EVALUATED"


def test_selection_and_stale_plan_cannot_invoke_executor():
    plan = _plan_result()["canonical_execution_plan"]
    stale = deepcopy(plan)
    stale["nodes"][0]["admission_state"] = "ADMITTED"
    selection_only = DependencyExecutionRuntime().execute(
        canonical_plan={},
        runtime_context={
            "run_id": "run_dep_exec_001",
            "task_id": "task_dep_exec_001",
            "tool_selection_report": {
                "selected_tools": ["dependency_reasoning"],
            },
        },
    )
    stale_receipt = DependencyExecutionRuntime().execute(
        canonical_plan=stale,
        runtime_context=_context([_link()]),
    )

    assert selection_only["non_execution_reason"] == "PLAN_NOT_VALID"
    assert selection_only["attempted_chain_count"] == 0
    assert stale_receipt["non_execution_reason"] == "PLAN_STALE"
    assert stale_receipt["attempted_chain_count"] == 0


def test_cross_run_and_legacy_unverifiable_links_fail_closed():
    plan = _plan_result()["canonical_execution_plan"]
    runtime = DependencyExecutionRuntime()
    cross_run = runtime.execute(
        canonical_plan=plan,
        runtime_context=_context([
            _link(run_id="older_run", task_id="task_dep_exec_001"),
        ]),
    )
    legacy = runtime.execute(
        canonical_plan=plan,
        runtime_context=_context([
            _link(run_id="", task_id=""),
        ]),
    )

    assert cross_run["link_eligibility"][0]["eligibility_state"] == "OUT_OF_RUN_SCOPE"
    assert cross_run["non_execution_reason"] == "NO_ELIGIBLE_DEPENDENCY_LINKS"
    assert legacy["link_eligibility"][0]["eligibility_state"] == "ELIGIBILITY_NOT_VERIFIED"
    assert legacy["non_execution_reason"] == "NO_ELIGIBLE_DEPENDENCY_LINKS"


def test_dispatcher_prefers_canonical_dependency_execution_receipt():
    plan_result = _plan_result()
    dispatch = ExecutionDispatcher().dispatch(
        execution_plan=plan_result["execution_plan"],
        runtime_context={
            **_context([_link()]),
            "canonical_execution_plan": plan_result["canonical_execution_plan"],
        },
    )
    report = dispatch["runtime_updates"]["DEPENDENCY_EXECUTION_RECEIPT"]

    assert dispatch["EXECUTION_DISPATCH_REPORT"]["dependency_runtime_called"] is True
    assert report["execution_state"] == "RESULT_CAPTURED"
    assert report["attempted_chain_count"] == 1
    assert dispatch["runtime_updates"].get("process_context_runtime_report") is None
    assert dispatch["runtime_updates"].get("causal_context_runtime_report") is None


def test_renderer_reads_dependency_receipt_without_rendering_raw_results():
    plan_result = _plan_result()
    receipt = DependencyExecutionRuntime().execute(
        canonical_plan=plan_result["canonical_execution_plan"],
        runtime_context=_context([_link()]),
    )
    report = DeterministicFinalReportRenderer().render(
        {
            "runtime_status": "completed",
            "operation": "dependency_execution",
            "EXECUTION_PLAN_REPORT": plan_result["EXECUTION_PLAN_REPORT"],
            "DEPENDENCY_EXECUTION_RECEIPT": receipt,
            "ENGINEERING_CONCLUSION": {"current_open_decision": "none"},
        },
        runtime_metadata={
            "execution_id": receipt["run_id"],
            "timestamp": "now",
            "mode": "test",
        },
    )

    assert "Dependency Execution State: RESULT_CAPTURED" in report
    assert "Dependency Chains Executed: 1" in report
    assert "Dependency Results Captured: 1" in report
    assert "raw_result" not in report
    assert "result_records" not in report
