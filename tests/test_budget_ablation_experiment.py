import pytest

from runtime.budget import (
    BudgetAblationError,
    BudgetExperimentConfig,
    BudgetExperimentTask,
    PRODUCTION_DEFAULT_DEPTH,
    PRODUCTION_DEFAULT_ROUTES,
    run_screening_ablation,
    screening_configs,
    task_set_fingerprint,
)


def _tasks():
    return [
        BudgetExperimentTask(
            task_id="task_easy",
            task_signature="sig_easy",
            payload={"difficulty": "easy"},
        ),
        BudgetExperimentTask(
            task_id="task_route_sensitive",
            task_signature="sig_route",
            payload={"difficulty": "route"},
        ),
    ]


def _evaluator(task, config):
    route_sensitive = task.task_id == "task_route_sensitive"
    exact = task.task_id == "task_easy" or (
        route_sensitive
        and config.route_budget >= 3
        and config.depth_budget >= 2
    )
    requested_routes = 4 if route_sensitive else 1
    requested_depth = 3 if route_sensitive else 1
    admitted_routes = min(requested_routes, config.route_budget)
    entered_depth = min(requested_depth, config.depth_budget)
    return {
        "run_id": f"run_{config.config_id}_{task.task_id}",
        "requested_routes": requested_routes,
        "admitted_routes": admitted_routes,
        "peak_active_routes": admitted_routes,
        "requested_reasoning_depth": requested_depth,
        "entered_reasoning_depth": entered_depth,
        "completed_reasoning_depth": entered_depth,
        "accuracy": 1.0 if exact else 0.5,
        "final_score": 1.0 if exact else 0.5,
        "success_state": "EXACT_SUCCESS" if exact else "RECOVERABLE_FAILURE",
        "exact_success": exact,
        "recoverable_failure": not exact,
        "routing_overload_detected": requested_routes > config.route_budget,
        "repair_attempts": 0 if exact else 1,
        "repair_successes": 0,
        "residual_count": 0 if exact else 1,
        "wall_time": round(0.01 * config.route_budget * config.depth_budget, 4),
        "aggregate_active_compute_time": round(0.005 * admitted_routes * entered_depth, 4),
        "realized_overrun": "NO_REALIZED_OVERRUN",
        "reachability_gap_count": 0,
    }


def test_screening_contract_preserves_production_default_and_exact_config_order():
    result = run_screening_ablation(
        tasks=_tasks(),
        evaluator=_evaluator,
        seed=123,
        execution_mode="fast",
        report_policy="minimal",
        code_checkpoint="5e108a8",
    )

    assert PRODUCTION_DEFAULT_ROUTES == 2
    assert PRODUCTION_DEFAULT_DEPTH == 2
    assert result["production_default"] == {"routes": 2, "depth": 2}
    assert result["production_default_changed"] is False
    assert result["runtime_authority_changed"] is False
    assert result["screening_configs"] == [
        "1/1",
        "1/2",
        "2/1",
        "2/2",
        "2/3",
        "3/2",
        "3/3",
        "4/4",
    ]


def test_experiment_override_is_explicit_nonpersistent_and_authority_free():
    seen = []

    def evaluator(task, config):
        seen.append(config.as_budget_override())
        return _evaluator(task, config)

    result = run_screening_ablation(
        tasks=_tasks(),
        evaluator=evaluator,
        seed=123,
        execution_mode="fast",
        report_policy="minimal",
        code_checkpoint="5e108a8",
    )

    assert seen
    assert all(item["experiment_only_override"] is True for item in seen)
    assert all(item["persistent"] is False for item in seen)
    assert all(item["authority"] == "NONE" for item in seen)
    assert result["production_policy_mutation"] == "FORBIDDEN"


def test_results_keep_per_task_identity_for_every_configuration():
    result = run_screening_ablation(
        tasks=_tasks(),
        evaluator=_evaluator,
        seed=123,
        execution_mode="fast",
        report_policy="minimal",
        code_checkpoint="5e108a8",
    )

    per_task = result["per_task_results"]

    assert len(per_task) == len(_tasks()) * len(screening_configs())
    assert {
        (item["task_id"], item["task_signature"])
        for item in per_task
    } == {
        ("task_easy", "sig_easy"),
        ("task_route_sensitive", "sig_route"),
    }
    assert all(item["seed"] == 123 for item in per_task)
    assert all(item["execution_mode"] == "fast" for item in per_task)
    assert all(item["report_policy"] == "minimal" for item in per_task)
    assert all(item["code_checkpoint"] == "5e108a8" for item in per_task)


def test_task_set_is_frozen_once_and_reused_identically_across_configurations():
    seen_by_config = {}

    def evaluator(task, config):
        seen_by_config.setdefault(config.config_id, []).append(task.task_id)
        return _evaluator(task, config)

    result = run_screening_ablation(
        tasks=_tasks(),
        evaluator=evaluator,
        seed=123,
        execution_mode="fast",
        report_policy="minimal",
        code_checkpoint="5e108a8",
    )

    expected_order = ["task_easy", "task_route_sensitive"]
    assert result["experiment_contract"]["controlled_variables"]["task_order"] == expected_order
    assert [item["task_id"] for item in result["frozen_task_set"]] == expected_order
    assert set(seen_by_config) == set(result["screening_configs"])
    assert all(order == expected_order for order in seen_by_config.values())


def test_experiment_provenance_is_stable_and_present_on_each_measurement():
    result = run_screening_ablation(
        tasks=_tasks(),
        evaluator=_evaluator,
        seed=123,
        execution_mode="fast",
        report_policy="minimal",
        code_checkpoint="5e108a8",
        repeat_id="repeat_001",
    )
    repeat_result = run_screening_ablation(
        tasks=_tasks(),
        evaluator=_evaluator,
        seed=123,
        execution_mode="fast",
        report_policy="minimal",
        code_checkpoint="5e108a8",
        repeat_id="repeat_001",
    )
    different_repeat = run_screening_ablation(
        tasks=_tasks(),
        evaluator=_evaluator,
        seed=123,
        execution_mode="fast",
        report_policy="minimal",
        code_checkpoint="5e108a8",
        repeat_id="repeat_002",
    )

    assert result["experiment_id"].startswith("budget_ablation_sha256_")
    assert result["task_set_fingerprint"].startswith("task_set_sha256_")
    assert result["experiment_id"] == repeat_result["experiment_id"]
    assert result["task_set_fingerprint"] == repeat_result["task_set_fingerprint"]
    assert result["experiment_id"] != different_repeat["experiment_id"]
    assert result["experiment_contract"]["controlled_variables"]["repeat_id"] == "repeat_001"
    assert all(
        item["experiment_id"] == result["experiment_id"]
        and item["repeat_id"] == "repeat_001"
        and item["task_set_fingerprint"] == result["task_set_fingerprint"]
        for item in result["per_task_results"]
    )


def test_task_payload_is_immutable_and_included_in_task_set_fingerprint():
    payload = {"difficulty": "easy", "tags": ["baseline"]}
    task = BudgetExperimentTask(
        task_id="task_payload",
        task_signature="sig_payload",
        payload=payload,
    )
    before = task_set_fingerprint([task])
    payload["difficulty"] = "mutated"
    payload["tags"].append("late")
    after = task_set_fingerprint([task])

    assert before == after
    with pytest.raises(TypeError):
        task.payload["difficulty"] = "mutated_again"


def test_metrics_distinguish_requested_admitted_active_and_depth_capacity():
    result = run_screening_ablation(
        tasks=_tasks(),
        evaluator=_evaluator,
        seed=123,
        execution_mode="fast",
        report_policy="minimal",
        code_checkpoint="5e108a8",
    )
    constrained = next(
        item
        for item in result["per_task_results"]
        if item["task_id"] == "task_route_sensitive"
        and item["configuration_id"] == "2/2"
    )

    assert constrained["requested_routes"] == 4
    assert constrained["admitted_routes"] == 2
    assert constrained["peak_active_routes"] == 2
    assert constrained["requested_reasoning_depth"] == 3
    assert constrained["entered_reasoning_depth"] == 2
    assert constrained["completed_reasoning_depth"] == 2
    assert constrained["routing_overload_detected"] is True
    assert constrained["realized_overrun"] == "NO_REALIZED_OVERRUN"


def test_summaries_and_mcv_report_dimension_isolated_effects_without_composite_score():
    result = run_screening_ablation(
        tasks=_tasks(),
        evaluator=_evaluator,
        seed=123,
        execution_mode="fast",
        report_policy="minimal",
        code_checkpoint="5e108a8",
    )
    by_config = {
        item["configuration_id"]: item
        for item in result["per_config_summary"]
    }
    comparisons = {
        (item["effect_type"], item["from"], item["to"]): item
        for item in result["dimension_comparisons"]
    }

    assert by_config["2/2"]["mean_accuracy"] == 0.75
    assert by_config["3/2"]["mean_accuracy"] == 1.0
    assert comparisons[("ROUTE_EFFECT", "2/2", "3/2")]["delta_accuracy"] == 0.25
    assert comparisons[("DEPTH_EFFECT", "2/2", "2/3")]["delta_accuracy"] == 0.0
    assert "mcv_accuracy_per_wall_time" in comparisons[("ROUTE_EFFECT", "2/2", "3/2")]
    assert "composite_score" not in result


def test_unavailable_metrics_are_reported_explicitly_not_fabricated():
    def sparse_evaluator(task, config):
        return {"success_state": "RECOVERABLE_FAILURE", "accuracy": None}

    result = run_screening_ablation(
        tasks=[{"task_id": "task_sparse", "task_signature": "sig_sparse"}],
        evaluator=sparse_evaluator,
        seed=123,
        execution_mode="fast",
        report_policy="minimal",
        code_checkpoint="5e108a8",
    )
    measurement = result["per_task_results"][0]
    summary = result["per_config_summary"][0]

    assert measurement["accuracy"] == "UNAVAILABLE"
    assert measurement["final_score"] == "UNAVAILABLE"
    assert summary["mean_accuracy"] == "UNAVAILABLE"
    assert summary["mean_final_score"] == "UNAVAILABLE"


def test_invalid_budgets_and_tasks_fail_closed():
    with pytest.raises(BudgetAblationError, match="route_budget must be positive"):
        BudgetExperimentConfig(route_budget=0, depth_budget=2)

    with pytest.raises(BudgetAblationError, match="depth_budget must be positive"):
        BudgetExperimentConfig(route_budget=2, depth_budget=-1)

    with pytest.raises(BudgetAblationError, match="task_id is required"):
        BudgetExperimentTask(task_id="", task_signature="sig")

    with pytest.raises(BudgetAblationError, match="at least one task is required"):
        run_screening_ablation(
            tasks=[],
            evaluator=_evaluator,
            seed=123,
            execution_mode="fast",
            report_policy="minimal",
            code_checkpoint="5e108a8",
        )


def test_reported_route_capacity_cannot_exceed_experimental_ceiling():
    def over_admitted(task, config):
        return {
            "success_state": "RECOVERABLE_FAILURE",
            "admitted_routes": config.route_budget + 1,
        }

    with pytest.raises(BudgetAblationError, match="admitted_routes exceeds"):
        run_screening_ablation(
            tasks=[{"task_id": "task_over", "task_signature": "sig_over"}],
            evaluator=over_admitted,
            seed=123,
            execution_mode="fast",
            report_policy="minimal",
            code_checkpoint="5e108a8",
        )


def test_reported_depth_capacity_cannot_exceed_experimental_ceiling():
    def over_depth(task, config):
        return {
            "success_state": "RECOVERABLE_FAILURE",
            "completed_reasoning_depth": config.depth_budget + 1,
        }

    with pytest.raises(BudgetAblationError, match="completed_reasoning_depth exceeds"):
        run_screening_ablation(
            tasks=[{"task_id": "task_over", "task_signature": "sig_over"}],
            evaluator=over_depth,
            seed=123,
            execution_mode="fast",
            report_policy="minimal",
            code_checkpoint="5e108a8",
        )
