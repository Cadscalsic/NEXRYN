import pytest

from runtime.budget import (
    EXPERIMENTAL_BUDGET_SOURCE,
    NORMAL_BUDGET_SOURCE,
    PRODUCTION_DEFAULT_DEPTH,
    PRODUCTION_DEFAULT_ROUTES,
    ExperimentalBudgetAuthorityError,
    ExperimentalBudgetGrant,
    ExperimentalBudgetRequest,
    issue_experimental_budget_grant,
    resolve_runtime_budget_authority,
)
from runtime.execution.execution_planner import ExecutionPlanner
from runtime.pipeline.legacy_pipeline import AdaptiveCognitivePipeline
from runtime.planning.budget_policy import BudgetPolicy
from runtime.planning.cognitive_cost_estimator import CognitiveCostEstimator
from runtime.planning.task_complexity_analyzer import TaskComplexityAnalyzer
from runtime.search.adaptive_search_policy import AdaptiveSearchPolicyEngine


def _request(
    experiment_id="exp_budget_contract",
    routes=1,
    depth=1,
    dependency_depth=1,
    hypotheses=1,
):
    return ExperimentalBudgetRequest(
        experiment_id=experiment_id,
        requested_max_active_routes=routes,
        requested_max_reasoning_depth=depth,
        requested_max_dependency_depth=dependency_depth,
        requested_max_hypotheses=hypotheses,
    )


def _grant(request=None, run_id="run_budget_contract"):
    request = request or _request()
    return issue_experimental_budget_grant(request, run_id=run_id)


def _context(request=None, grant=None, run_id="run_budget_contract"):
    data = {
        "run_id": run_id,
    }
    if request is not None:
        data["experimental_budget_request"] = request.as_report()
    if grant is not None:
        data["experimental_budget_grant"] = grant.as_report()
    return data


def _profile_and_cost(task=None):
    task = task or {
        "input_grid": [[0, 1], [0, 0]],
        "output_grid": [[0, 2], [0, 0]],
    }
    profile = TaskComplexityAnalyzer().analyze(task)
    cost = CognitiveCostEstimator().estimate(profile)
    profile.estimated_cost = cost.total_cost
    return profile, cost


def test_normal_run_preserves_existing_production_budget_behavior():
    budget = BudgetPolicy().fast()
    result = resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context={"run_id": "run_normal"},
    )

    assert result["grant_applied"] is False
    assert budget.max_active_routes == 3
    assert budget.max_reasoning_depth == 2
    assert result["binding"]["budget_source"] == NORMAL_BUDGET_SOURCE


def test_experiment_request_has_no_runtime_authority_without_grant():
    budget = BudgetPolicy().fast()
    request = _request(routes=1, depth=1)
    result = resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context=_context(request=request, grant=None),
    )

    assert result["grant_applied"] is False
    assert budget.max_active_routes == 3
    assert budget.max_reasoning_depth == 2
    assert result["binding"]["binding_state"] == "EXPERIMENT_REQUEST_NON_AUTHORITATIVE"


def test_valid_1_1_grant_produces_effective_1_1_runtime_ceiling():
    budget = BudgetPolicy().fast()
    request = _request(routes=1, depth=1)
    grant = _grant(request)
    result = resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context=_context(request=request, grant=grant),
    )

    assert result["grant_applied"] is True
    assert budget.max_active_routes == 1
    assert budget.max_reasoning_depth == 1
    assert result["binding"]["budget_source"] == EXPERIMENTAL_BUDGET_SOURCE
    assert result["binding"]["effective_max_active_routes"] == 1
    assert result["binding"]["effective_max_reasoning_depth"] == 1


def test_runtime_usage_cannot_exceed_1_1_experimental_ceiling():
    request = _request(routes=1, depth=1)
    grant = _grant(request)
    budget = BudgetPolicy().fast()
    resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context=_context(request=request, grant=grant),
    )
    routes = [
        {"route_id": "route_a", "rank": 1},
        {"route_id": "route_b", "rank": 2},
    ]
    result = ExecutionPlanner().plan(
        runtime_context={
            "run_id": "run_budget_contract",
            "task_id": "task_budget_contract",
            "current_reasoning_budget": {
                "budget_source": EXPERIMENTAL_BUDGET_SOURCE,
                "run_id": "run_budget_contract",
                "task_id": "task_budget_contract",
                "max_active_routes": budget.max_active_routes,
                "max_reasoning_depth": budget.max_reasoning_depth,
            },
            "route_selection_report": {
                "available_routes": routes,
                "candidate_routes": routes,
                "active_routes": routes,
            },
            "planned_reasoning_depth": 2,
        }
    )
    receipt = result["canonical_execution_plan"]["RUNTIME_BUDGET_ENFORCEMENT_REPORT"]

    assert receipt["admitted_route_count"] <= 1
    assert receipt["maximum_reasoning_depth"] == 1
    assert receipt["depth_enforcement_state"] == "REASONING_DEPTH_LIMIT_REACHED"


def test_valid_experimental_grant_is_current_run_scoped():
    request = _request()
    grant = _grant(request, run_id="run_a")
    budget = BudgetPolicy().fast()
    result = resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context=_context(request=request, grant=grant, run_id="run_b"),
    )

    assert result["grant_applied"] is False
    assert result["binding"]["binding_state"] == "EXPERIMENTAL_BUDGET_GRANT_REJECTED"
    assert "foreign-run" in result["binding"]["rejection_reason"]


def test_foreign_run_grant_is_rejected_or_ignored_fail_closed():
    request = _request(routes=1, depth=1)
    grant = _grant(request, run_id="other_run")
    budget = BudgetPolicy().fast()
    resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context=_context(request=request, grant=grant),
    )

    assert budget.max_active_routes == 3
    assert budget.max_reasoning_depth == 2


def test_stale_or_invalid_grant_cannot_influence_runtime_budget():
    request = _request()
    stale_grant = ExperimentalBudgetGrant(
        experiment_id=request.experiment_id,
        run_id="run_budget_contract",
        granted_max_active_routes=1,
        granted_max_reasoning_depth=1,
        granted_max_dependency_depth=1,
        granted_max_hypotheses=1,
        stale=True,
    )
    budget = BudgetPolicy().fast()
    result = resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context=_context(request=request, grant=stale_grant),
    )

    assert result["grant_applied"] is False
    assert budget.max_active_routes == 3
    assert result["binding"]["rejection_reason"] == "experimental grant is stale"


def test_experimental_grant_does_not_mutate_production_defaults():
    request = _request(routes=1, depth=1)
    budget = BudgetPolicy().fast()
    resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context=_context(request=request, grant=_grant(request)),
    )

    assert PRODUCTION_DEFAULT_ROUTES == 2
    assert PRODUCTION_DEFAULT_DEPTH == 2


def test_experimental_grant_is_nonpersistent():
    request = _request()
    grant = _grant(request)

    assert request.persistent is False
    assert request.production_policy_mutation is False
    assert grant.persistent is False
    assert grant.promotable is False


def test_adaptive_search_policy_cannot_expand_above_experimental_ceiling():
    request = _request(routes=1, depth=1)
    grant = _grant(request)
    budget = BudgetPolicy().deep()
    report = AdaptiveSearchPolicyEngine(persist_memory=False).plan(task_analysis={})
    AdaptiveSearchPolicyEngine(persist_memory=False).apply_budget(budget, report)
    resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context=_context(request=request, grant=grant),
    )

    assert budget.max_active_routes <= 1
    assert budget.max_reasoning_depth <= 1


def test_runtime_budget_source_reports_experimental_budget_grant():
    profile, cost = _profile_and_cost()
    request = _request(routes=1, depth=1)
    grant = _grant(request)
    pipeline = AdaptiveCognitivePipeline()
    pipeline.runtime.set_observational_profile(profile, cost)
    result = pipeline.allocate_cognitive_budget_after_memory_lookup(
        _context(request=request, grant=grant)
    )

    assert result["cognitive_budget_report"]["runtime_budget_source"] == (
        EXPERIMENTAL_BUDGET_SOURCE
    )
    assert result["cognitive_budget_report"]["max_active_routes"] == 1
    assert result["cognitive_budget_report"]["max_reasoning_depth"] == 1


def test_normal_runtime_budget_source_remains_cognitive_budget_report():
    profile, cost = _profile_and_cost()
    pipeline = AdaptiveCognitivePipeline()
    pipeline.runtime.set_observational_profile(profile, cost)
    result = pipeline.allocate_cognitive_budget_after_memory_lookup(
        {"run_id": "run_normal"}
    )

    assert result["cognitive_budget_report"]["runtime_budget_source"] == (
        NORMAL_BUDGET_SOURCE
    )


def test_request_grant_effective_provenance_is_consistent():
    request = _request(routes=3, depth=3, dependency_depth=3, hypotheses=3)
    grant = _grant(request)
    budget = BudgetPolicy().fast()
    result = resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context=_context(request=request, grant=grant),
    )

    assert request.requested_max_active_routes == grant.granted_max_active_routes
    assert grant.granted_max_active_routes == result["binding"]["effective_max_active_routes"]
    assert result["binding"]["experiment_id"] == request.experiment_id


def test_invalid_budget_values_fail_closed():
    with pytest.raises(ExperimentalBudgetAuthorityError):
        _request(routes=0)
    with pytest.raises(ExperimentalBudgetAuthorityError):
        ExperimentalBudgetGrant(
            experiment_id="exp_invalid",
            run_id="run_invalid",
            granted_max_active_routes=1,
            granted_max_reasoning_depth=-1,
            granted_max_dependency_depth=1,
            granted_max_hypotheses=1,
        )


def test_execution_plan_declared_budget_remains_non_enforcement_authority():
    plan = ExecutionPlanner().build_authoritative_run_plan(
        run_id="run_plan_only",
        task_files=["task.json"],
        selected_mode="adaptive",
        declared_budget={
            "budget_source": "plan_only_experiment",
            "max_active_routes": 1,
            "max_reasoning_depth": 1,
        },
    )
    budget = BudgetPolicy().fast()
    result = resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context={"authoritative_execution_plan": plan},
    )

    assert result["grant_applied"] is False
    assert budget.max_active_routes == 3
    assert plan["constitutional_boundary"] == (
        "TEMPORAL_PLANNING_AUTHORITY_ONLY_NO_RUNTIME_BUDGET_ENFORCEMENT"
    )


def test_experiment_budget_grants_no_non_budget_authority():
    request = _request()
    result = resolve_runtime_budget_authority(
        normal_budget=BudgetPolicy().fast(),
        runtime_context=_context(request=request, grant=_grant(request)),
    )

    assert result["binding"]["non_budget_authority_changed"] is False
    assert result["binding"]["production_policy_mutation"] is False
    assert result["binding"]["persistent"] is False
