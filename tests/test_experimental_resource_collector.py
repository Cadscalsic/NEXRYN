from pathlib import Path

from runtime.budget import (
    EXPERIMENTAL_BUDGET_SOURCE,
    ExperimentalBudgetRequest,
    canonical_task_set_fingerprint,
    collect_realized_resource_telemetry,
    flatten_realized_resource_telemetry,
    issue_experimental_budget_grant,
    resolve_runtime_budget_authority,
    state_surface_fingerprint,
    validate_realized_usage_within_effective_ceiling,
)
from runtime.budget.budget_ablation_experiment import UNAVAILABLE
from runtime.planning.budget_policy import BudgetPolicy


def _receipt(**overrides):
    receipt = {
        "selected_route_count": 7,
        "admitted_route_count": 2,
        "peak_concurrent_active_route_count": 1,
        "maximum_requested_reasoning_depth": 5,
        "maximum_entered_reasoning_depth": 2,
        "maximum_completed_reasoning_depth": 1,
        "realized_overrun_state": "NO_REALIZED_OVERRUN",
        "prevented_overrun_state": "OVERRUN_PREVENTED",
        "attempted_overrun_state": "ATTEMPTED_OVERRUN_DETECTED",
    }
    receipt.update(overrides)
    return receipt


def test_peak_routes_does_not_automatically_equal_max_active_routes():
    telemetry = collect_realized_resource_telemetry(
        runtime_context={
            "cognitive_budget_report": {"max_active_routes": 4},
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT": _receipt(
                peak_concurrent_active_route_count=1,
            ),
        }
    )

    assert telemetry["peak_active_routes"]["value"] == 1
    assert telemetry["peak_active_routes"]["value"] != 4
    assert telemetry["peak_active_routes"]["source"] == (
        "RUNTIME_BUDGET_ENFORCEMENT_REPORT.peak_concurrent_active_route_count"
    )


def test_admitted_routes_is_read_from_realized_runtime_telemetry():
    telemetry = collect_realized_resource_telemetry(
        runtime_context={
            "cognitive_budget_report": {"max_active_routes": 4},
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT": _receipt(admitted_route_count=2),
        }
    )

    assert telemetry["admitted_routes"]["value"] == 2
    assert telemetry["admitted_routes"]["source"] == (
        "RUNTIME_BUDGET_ENFORCEMENT_REPORT.admitted_route_count"
    )


def test_entered_depth_does_not_automatically_equal_max_reasoning_depth():
    telemetry = collect_realized_resource_telemetry(
        runtime_context={
            "cognitive_budget_report": {"max_reasoning_depth": 4},
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT": _receipt(
                maximum_entered_reasoning_depth=2,
            ),
        }
    )

    assert telemetry["entered_reasoning_depth"]["value"] == 2
    assert telemetry["entered_reasoning_depth"]["value"] != 4


def test_exact_success_early_stop_can_have_realized_depth_below_ceiling():
    telemetry = collect_realized_resource_telemetry(
        runtime_context={
            "cognitive_budget_report": {"max_reasoning_depth": 4},
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT": _receipt(
                maximum_entered_reasoning_depth=0,
                maximum_completed_reasoning_depth=0,
            ),
        }
    )

    assert telemetry["entered_reasoning_depth"]["value"] == 0
    assert telemetry["completed_reasoning_depth"]["value"] == 0


def test_active_compute_time_is_not_populated_from_wall_time():
    telemetry = collect_realized_resource_telemetry(
        runtime_context={"RUNTIME_BUDGET_ENFORCEMENT_REPORT": _receipt()},
        wall_time=12.5,
    )

    assert telemetry["wall_time"]["value"] == 12.5
    assert telemetry["aggregate_active_compute_time"]["value"] == UNAVAILABLE


def test_unavailable_active_compute_becomes_not_available():
    telemetry = collect_realized_resource_telemetry(
        runtime_context={"RUNTIME_BUDGET_ENFORCEMENT_REPORT": _receipt()}
    )

    assert telemetry["aggregate_active_compute_time"] == {
        "value": UNAVAILABLE,
        "source": "NOT_AVAILABLE",
    }


def test_active_compute_uses_canonical_runtime_metric_when_available():
    telemetry = collect_realized_resource_telemetry(
        runtime_context={
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT": _receipt(),
            "performance_report": {"active_compute_time_seconds": 3.25},
        },
        wall_time=12.5,
    )

    assert telemetry["aggregate_active_compute_time"]["value"] == 3.25
    assert telemetry["aggregate_active_compute_time"]["source"] == (
        "performance_report.active_compute_time_seconds"
    )


def test_realized_use_above_effective_ceiling_fails_validity():
    failures = validate_realized_usage_within_effective_ceiling(
        realized={
            "admitted_routes": 3,
            "peak_active_routes": 2,
            "entered_reasoning_depth": 5,
            "completed_reasoning_depth": UNAVAILABLE,
        },
        effective_max_active_routes=2,
        effective_max_reasoning_depth=4,
    )

    assert failures == [
        "ADMITTED_ROUTES_EXCEEDS_EFFECTIVE_CEILING",
        "ENTERED_REASONING_DEPTH_EXCEEDS_EFFECTIVE_CEILING",
    ]


def test_task_set_fingerprint_is_independent_of_temp_absolute_path(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    for root in (left, right):
        (root / "task.json").write_text('{"train":[],"test":[]}', encoding="utf-8")

    left_report = canonical_task_set_fingerprint([left / "task.json"])
    right_report = canonical_task_set_fingerprint([right / "task.json"])

    assert left_report["task_set_fingerprint"] == right_report["task_set_fingerprint"]
    assert left_report["canonical_task_set_identity"] == (
        right_report["canonical_task_set_identity"]
    )


def test_state_fingerprint_uses_normalized_relative_state_identity(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    for root in (left, right):
        state = root / "runtime" / "artifacts" / "runtime_data"
        state.mkdir(parents=True)
        (state / "memory.json").write_text('{"value": 1}', encoding="utf-8")

    left_report = state_surface_fingerprint(
        root=left,
        surfaces=["runtime/artifacts/runtime_data"],
    )
    right_report = state_surface_fingerprint(
        root=right,
        surfaces=["runtime/artifacts/runtime_data"],
    )

    assert left_report["state_fingerprint"] == right_report["state_fingerprint"]
    assert left_report["state_identity_entries"] == right_report["state_identity_entries"]


def test_existing_p0b_authority_validation_remains_unchanged():
    request = ExperimentalBudgetRequest(
        experiment_id="exp_collector",
        requested_max_active_routes=1,
        requested_max_reasoning_depth=1,
        requested_max_dependency_depth=1,
        requested_max_hypotheses=1,
    )
    grant = issue_experimental_budget_grant(request, run_id="run_collector")
    budget = BudgetPolicy().fast()

    result = resolve_runtime_budget_authority(
        normal_budget=budget,
        runtime_context={
            "run_id": "run_collector",
            "experimental_budget_request": request.as_report(),
            "experimental_budget_grant": grant.as_report(),
        },
    )

    assert result["binding"]["budget_source"] == EXPERIMENTAL_BUDGET_SOURCE
    assert result["binding"]["effective_max_active_routes"] == 1
    assert result["binding"]["effective_max_reasoning_depth"] == 1


def test_flatten_realized_resource_telemetry_preserves_not_available():
    flattened = flatten_realized_resource_telemetry({
        "admitted_routes": {"value": 2, "source": "receipt"},
        "aggregate_active_compute_time": {
            "value": UNAVAILABLE,
            "source": "NOT_AVAILABLE",
        },
    })

    assert flattened == {
        "admitted_routes": 2,
        "aggregate_active_compute_time": UNAVAILABLE,
    }
