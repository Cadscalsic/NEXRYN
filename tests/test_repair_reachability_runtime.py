import numpy as np

from runtime.repair.recoverability_gate import RecoverabilityGate
from runtime.repair.repair_route_selector import RepairRouteSelector
from runtime.stages.evaluation import evaluation_stage


def _base_context(predicted, target, **overrides):
    context = {
        "predicted_output": predicted,
        "output_grid": target,
        "cognitive_cycle": {"task_id": "repair_reachability_regression"},
        "task_id": "repair_reachability_regression",
        "run_id": "repair_reachability_run",
        "cognitive_budget_report": {
            "max_active_routes": 2,
            "max_reasoning_depth": 2,
            "max_hypotheses": 4,
        },
        "MAX_REPAIR_ATTEMPTS_PER_TASK": 3,
        "MAX_LOCALIZED_REPAIR_ATTEMPTS": 3,
    }
    context.update(overrides)
    return context


def test_recoverable_failure_reaches_repair_admission_and_arena_reentry():
    predicted = np.zeros((5, 5), dtype=int)
    target = predicted.copy()
    for row, col in [(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)]:
        target[row, col] = 7

    result = evaluation_stage(_base_context(predicted, target))

    report = result["REPAIR_REACHABILITY_REPORT"]
    audit = result["REPAIR_REACHABILITY_AUDIT"]
    assert result["pre_runtime_repair_evaluation_result"]["success_state"] == (
        "RECOVERABLE_FAILURE"
    )
    assert report["repair_admission_state"] == "REPAIR_REQUIRED"
    assert report["repair_route"] == "localized_color_repair"
    assert report["repair_candidate_count"] >= 1
    assert report["arena_reentry_attempted"] is True
    assert report["repair_attempts"] >= 1
    assert audit["repair_engine_reachable"] is True
    assert result["FINAL_REPAIR_REPORT"]["repair_attempts"] >= 1
    assert report["residual_count_after"] < report["residual_count_before"]
    origin = result["CURRENT_CANDIDATE_ORIGIN_REPORT"]
    assert origin["authority"] == "OBSERVATION_ONLY"
    assert origin["behavioral_authority"] == "NONE"
    assert origin["current_candidate_handoff_observed"] is True
    assert origin["construction_observable"] is False
    assert origin["producer_component"] == "NOT_OBSERVABLE"
    assert origin["handoff_evidence"]["source_candidate_id"] == (
        "current_candidate"
    )


def test_exact_success_does_not_trigger_repair():
    predicted = np.zeros((3, 3), dtype=int)

    result = evaluation_stage(_base_context(predicted, predicted.copy()))

    assert result["REPAIR_ADMISSION_REPORT"]["repair_required"] is False
    assert result["REPAIR_REACHABILITY_REPORT"]["repair_candidate_count"] == 0
    assert result["FINAL_REPAIR_REPORT"]["repair_attempts"] == 0


def test_retry_allowed_false_blocks_repair_admission():
    evaluation = {
        "success_state": "RECOVERABLE_FAILURE",
        "episode_completed": False,
        "retry_allowed": False,
        "accuracy": 0.8,
        "difference_count": 1,
    }
    residual = {
        "residual_difference_count": 1,
        "residual_locations": [[1, 1]],
        "residual_type": "localized_color_residual",
    }

    report = RecoverabilityGate().evaluate(
        evaluation_result=evaluation,
        residual_analysis=residual,
        task_context={"MAX_REPAIR_ATTEMPTS_PER_TASK": 1},
    )

    assert report["repair_admission_state"] == "BLOCKED"
    assert report["repair_reason"] == "retry_not_allowed"


def test_missing_residual_evidence_blocks_repair_safely():
    evaluation = {
        "success_state": "RECOVERABLE_FAILURE",
        "episode_completed": False,
        "retry_allowed": True,
        "accuracy": 0.8,
        "difference_count": 1,
    }

    report = RecoverabilityGate().evaluate(
        evaluation_result=evaluation,
        residual_analysis={},
        task_context={"MAX_REPAIR_ATTEMPTS_PER_TASK": 1},
    )

    assert report["repair_admission_state"] == "BLOCKED"
    assert report["repair_reason"] == "residual_evidence_not_actionable"


def test_localized_color_residual_selects_localized_color_repair():
    route = RepairRouteSelector().select({
        "residual_type": "localized_color_residual",
        "residual_difference_count": 1,
        "residual_locations": [[0, 0]],
    })

    assert route["route_selected"] is True
    assert route["repair_route"] == "localized_color_repair"


def test_repair_budget_prevents_infinite_runtime_repair_loop():
    predicted = np.zeros((5, 5), dtype=int)
    target = predicted.copy()
    for row, col in [(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)]:
        target[row, col] = 4

    result = evaluation_stage(
        _base_context(
            predicted,
            target,
            repair_budget={"repair_attempts": 1, "max_repair_attempts_per_task": 1},
        )
    )

    assert result["REPAIR_ADMISSION_REPORT"]["repair_admission_state"] == "DEFERRED"
    assert result["REPAIR_REACHABILITY_REPORT"]["repair_stop_reason"] == (
        "NO_VALID_REPAIR_CANDIDATE"
    )


def test_fast_minimal_closure_carries_required_repair_decision():
    predicted = np.zeros((5, 5), dtype=int)
    target = predicted.copy()
    for row, col in [(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)]:
        target[row, col] = 7

    result = evaluation_stage(
        _base_context(
            predicted,
            target,
            mode="fast",
            report_level="minimal",
        )
    )

    assert result["fast_minimal_evaluation_closure"]["enabled"] is True
    assert result["final_evaluation_closure_must_wait_for_repair_decision"] is True
    assert result["REPAIR_REACHABILITY_REPORT"]["arena_reentry_attempted"] is True


def test_repair_telemetry_uses_authoritative_admitted_runtime_facts():
    predicted = np.zeros((5, 5), dtype=int)
    target = predicted.copy()
    for row, col in [(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)]:
        target[row, col] = 7

    result = evaluation_stage(
        _base_context(
            predicted,
            target,
            RUNTIME_BUDGET_ENFORCEMENT_REPORT={
                "peak_active_routes": 2,
                "admitted_route_count": 2,
                "executed_route_count": 2,
                "admitted_reasoning_depth": 2,
                "completed_reasoning_depth": 2,
            },
            planned_reasoning_depth=4,
        )
    )

    telemetry = result["REPAIR_RUNTIME_BUDGET_REPORT"]
    assert telemetry["repair_routes_requested"] > telemetry["repair_routes_admitted"]
    assert telemetry["admitted_route_count"] == 2
    assert telemetry["requested_reasoning_depth"] == 4
    assert telemetry["completed_reasoning_depth"] == 2


def test_repair_handoff_preserves_observed_candidate_origin_without_authority():
    predicted = np.zeros((5, 5), dtype=int)
    target = predicted.copy()
    for row, col in [(0, 0), (0, 1), (1, 0), (1, 1), (2, 2)]:
        target[row, col] = 7

    result = evaluation_stage(
        _base_context(
            predicted,
            target,
            candidate_origin_report={
                "system": "candidate_origin_provenance",
                "report_state": "OBSERVED",
                "authority": "OBSERVATION_ONLY",
                "behavioral_authority": "NONE",
                "candidate_id": "current_candidate",
                "producer_component": "transformation_stage",
                "producer_operation_id": "transformation_execution",
                "parent_candidate_id": None,
                "program_id": None,
                "strategy_id": "strategy:local",
                "retrieval_source": None,
                "transformation_source": "transformation_report",
                "prediction_source": "execution_result.output_grid",
                "run_id": "repair_reachability_run",
                "task_id": "repair_reachability_regression",
            },
        )
    )

    origin = result["CURRENT_CANDIDATE_ORIGIN_REPORT"]
    assert origin["construction_observable"] is True
    assert origin["producer_component"] == "transformation_stage"
    assert origin["producer_operation_id"] == "transformation_execution"
    assert origin["strategy_id"] == "strategy:local"
    assert origin["authority"] == "OBSERVATION_ONLY"
    assert origin["behavioral_authority"] == "NONE"
    assert result["evaluation_result"]["difference_count"] < 5
