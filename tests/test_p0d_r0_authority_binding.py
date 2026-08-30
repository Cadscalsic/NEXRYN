from runtime.budget import (
    EXPERIMENTAL_BUDGET_SOURCE,
    ExperimentalBudgetRequest,
    collect_realized_resource_telemetry,
    flatten_realized_resource_telemetry,
    issue_experimental_budget_grant,
    observe_runtime_budget_authority,
    production_budget_snapshot,
)
from runtime.pipeline.legacy_pipeline import AdaptiveCognitivePipeline


def _request(experiment_id="p0d_r0_test", routes=1, depth=1):
    return ExperimentalBudgetRequest(
        experiment_id=experiment_id,
        requested_max_active_routes=routes,
        requested_max_reasoning_depth=depth,
        requested_max_dependency_depth=depth,
        requested_max_hypotheses=max(routes, depth),
    )


def _run_pipeline(*, request, grant, run_id, task_path="data/training/task_001.json"):
    pipeline = AdaptiveCognitivePipeline()
    result = pipeline.run(
        task_path=task_path,
        mode="adaptive",
        report_level="minimal",
        post_success_mode="fast",
        profile=False,
        experimental_budget_request=request,
        experimental_budget_grant=grant,
        run_id=run_id,
    )
    return pipeline, result


def test_real_pipeline_accepts_grant_bound_to_actual_run_id(capsys):
    run_id = "p0d_r0_actual_run"
    request = _request(routes=1, depth=1)
    grant = issue_experimental_budget_grant(request, run_id=run_id)

    pipeline, result = _run_pipeline(request=request, grant=grant, run_id=run_id)
    observed = observe_runtime_budget_authority(
        runtime_context=pipeline.runtime.get_context(),
        result=result,
    )

    assert observed["observed_authority_source"] == EXPERIMENTAL_BUDGET_SOURCE
    assert observed["observed_binding_state"] == "EXPERIMENTAL_BUDGET_GRANT_ACCEPTED"
    assert observed["measurement_authority_valid"] is True
    report = pipeline.runtime.get_context()["cognitive_budget_report"]
    assert request.requested_max_active_routes == grant.granted_max_active_routes
    assert grant.granted_max_active_routes == report["effective_max_active_routes"]
    assert request.requested_max_reasoning_depth == grant.granted_max_reasoning_depth
    assert grant.granted_max_reasoning_depth == report["effective_max_reasoning_depth"]


def test_real_pipeline_rejects_mismatched_grant_run_id_fail_closed(capsys):
    request = _request(routes=1, depth=1)
    grant = issue_experimental_budget_grant(request, run_id="run_a")

    pipeline, result = _run_pipeline(
        request=request,
        grant=grant,
        run_id="run_b",
    )
    observed = observe_runtime_budget_authority(
        runtime_context=pipeline.runtime.get_context(),
        result=result,
    )

    assert observed["observed_authority_source"] != EXPERIMENTAL_BUDGET_SOURCE
    assert observed["observed_binding_state"] == "EXPERIMENTAL_BUDGET_GRANT_REJECTED"
    assert observed["measurement_authority_valid"] is False


def test_observation_rejects_driver_expected_authority_when_runtime_rejected():
    observed = observe_runtime_budget_authority(
        runtime_context={
            "cognitive_budget_report": {
                "runtime_budget_source": "COGNITIVE_BUDGET_REPORT",
                "runtime_budget_binding_state": "EXPERIMENTAL_BUDGET_GRANT_REJECTED",
            },
        },
        expected_authority_source=EXPERIMENTAL_BUDGET_SOURCE,
    )

    assert observed["expected_authority_source"] == EXPERIMENTAL_BUDGET_SOURCE
    assert observed["observed_authority_source"] == "COGNITIVE_BUDGET_REPORT"
    assert observed["observed_binding_state"] == "EXPERIMENTAL_BUDGET_GRANT_REJECTED"
    assert observed["measurement_authority_valid"] is False


def test_real_pipeline_1_1_smoke_stays_within_accepted_experimental_ceiling(capsys):
    run_id = "p0d_r0_smoke_1_1"
    request = _request(routes=1, depth=1)
    grant = issue_experimental_budget_grant(request, run_id=run_id)

    pipeline, result = _run_pipeline(request=request, grant=grant, run_id=run_id)
    telemetry = collect_realized_resource_telemetry(
        runtime_context=pipeline.runtime.get_context(),
        result=result,
        wall_time=0.0,
    )
    realized = flatten_realized_resource_telemetry(telemetry)

    assert realized["admitted_routes"] <= 1
    assert realized["peak_active_routes"] <= 1
    assert realized["entered_reasoning_depth"] <= 1


def test_production_path_without_experimental_grant_remains_production_default(capsys):
    before = production_budget_snapshot()
    pipeline = AdaptiveCognitivePipeline()
    pipeline.run(
        task_path="data/training/task_001.json",
        mode="adaptive",
        report_level="minimal",
        post_success_mode="fast",
        profile=False,
        run_id="p0d_r0_production_default",
    )
    after = production_budget_snapshot()

    assert before == {"max_active_routes": 2, "max_reasoning_depth": 2}
    assert after == before
    assert pipeline.runtime.get_context()["cognitive_budget_report"][
        "runtime_budget_source"
    ] == "COGNITIVE_BUDGET_REPORT"


def test_grant_properties_remain_current_run_only_nonpersistent_nonpromotable():
    request = _request()
    grant = issue_experimental_budget_grant(request, run_id="p0d_r0_properties")

    assert grant.scope == "CURRENT_RUN_ONLY"
    assert grant.persistent is False
    assert grant.promotable is False
