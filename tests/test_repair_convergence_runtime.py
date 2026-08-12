import numpy as np

from runtime.repair.repair_convergence_assessor import RepairConvergenceAssessor
from runtime.repair.repair_novelty_guard import RepairNoveltyGuard
from runtime.repair.residual_trajectory import classify_trajectory
from runtime.stages.evaluation import evaluation_stage


def _context(predicted, target, **overrides):
    data = {
        "predicted_output": predicted,
        "output_grid": target,
        "cognitive_cycle": {"task_id": "repair_convergence_regression"},
        "task_id": "repair_convergence_regression",
        "run_id": "repair_convergence_run",
        "cognitive_budget_report": {
            "max_active_routes": 2,
            "max_reasoning_depth": 2,
            "max_hypotheses": 4,
        },
        "MAX_REPAIR_ITERATIONS_PER_TASK": 3,
        "MAX_REPAIR_CANDIDATES_PER_ITERATION": 3,
        "MAX_LOCALIZED_REPAIR_ATTEMPTS": 3,
        "MAX_REPAIR_ATTEMPTS_PER_TASK": 3,
    }
    data.update(overrides)
    return data


def _five_cell_residual():
    predicted = np.zeros((6, 6), dtype=int)
    target = predicted.copy()
    for row, col in [(0, 0), (0, 1), (1, 0), (1, 1), (3, 5)]:
        target[row, col] = 7
    return predicted, target


def test_repair_convergence_reanalyzes_promotes_and_reaches_exact_success():
    predicted, target = _five_cell_residual()

    result = evaluation_stage(_context(predicted, target))

    assert result["pre_runtime_repair_evaluation_result"]["success_state"] == (
        "RECOVERABLE_FAILURE"
    )
    assert result["evaluation_result"]["success_state"] == "EXACT_SUCCESS"
    assert result["evaluation_result"]["difference_count"] == 0
    assert result["evaluation_result"]["episode_completed"] is True
    assert result["evaluation_result"]["retry_allowed"] is False
    assert result["REPAIR_CONVERGENCE_AUDIT"][
        "post_repair_residual_recomputed"
    ] is True
    assert result["REPAIR_CONVERGENCE_AUDIT"][
        "repaired_candidate_promoted_to_iteration_baseline"
    ] is True
    assert result["REPAIR_CONVERGENCE_AUDIT"][
        "next_repair_receives_latest_state"
    ] is True
    assert result["REPAIR_CONVERGENCE_REPORT"]["Convergence State"] == (
        "EXACT_SUCCESS"
    )
    assert result["REPAIR_RESIDUAL_TRAJECTORY"]["residual_counts"] == [5, 2, 0]


def test_next_repair_targets_remaining_residual_cells_only():
    predicted, target = _five_cell_residual()

    result = evaluation_stage(_context(predicted, target))
    iterations = result["REPAIR_ITERATION_STATES"]

    assert iterations[0]["residual_after"]["locations"] == [[1, 1], [3, 5]]
    assert iterations[1]["residual_before"]["locations"] == [[1, 1], [3, 5]]
    assert iterations[1]["residual_after"]["locations"] == []
    assert result["BASELINE_PROMOTION_REPORT"]["baseline_promotion_state"] == (
        "PROMOTED"
    )


def test_arena_reentry_uses_current_repaired_baseline():
    predicted, target = _five_cell_residual()

    result = evaluation_stage(_context(predicted, target))
    arena_reports = result["REPAIR_SESSION_MEMORY"]["repair_iterations"]

    assert len(arena_reports) == 2
    assert arena_reports[1]["parent_candidate_id"] == (
        arena_reports[0]["current_candidate_id"]
    )


def test_partial_improvement_does_not_declare_exact_success_when_budget_stops():
    predicted, target = _five_cell_residual()

    result = evaluation_stage(
        _context(
            predicted,
            target,
            MAX_REPAIR_ITERATIONS_PER_TASK=1,
        )
    )

    assert result["evaluation_result"]["success_state"] != "EXACT_SUCCESS"
    assert result["evaluation_result"]["difference_count"] == 2
    assert result["evaluation_result"]["episode_completed"] is False
    assert result["FINAL_REPAIR_REPORT"]["repair_stop_reason"] == (
        "REPAIR_BUDGET_EXHAUSTED"
    )
    assert result["current_task_current_residual"] == 2


def test_fast_minimal_closure_waits_for_productive_convergence_session():
    predicted, target = _five_cell_residual()

    result = evaluation_stage(
        _context(
            predicted,
            target,
            mode="fast",
            report_level="minimal",
        )
    )

    assert result["fast_minimal_evaluation_closure"]["enabled"] is True
    assert result["evaluation_result"]["success_state"] == "EXACT_SUCCESS"
    assert result["current_task_residual_trajectory"] == [5, 2, 0]


def test_trajectory_classification_states():
    assert classify_trajectory([5, 3, 2, 0]) == "EXACT_SUCCESS"
    assert classify_trajectory([5, 2, 2, 2]) == "STAGNATION"
    assert classify_trajectory([5, 2, 4, 2]) == "OSCILLATION"
    assert classify_trajectory([5, 7]) == "REGRESSION"


def test_convergence_assessor_continues_only_for_bounded_improvement():
    assessor = RepairConvergenceAssessor()

    improving = assessor.assess(
        {"residual_counts": [5, 3, 2]},
        remaining_budget=1,
    )
    exact = assessor.assess(
        {"residual_counts": [5, 3, 2, 0]},
        remaining_budget=1,
    )

    assert improving["continue_repair"] is True
    assert improving["recommended_next_action"] == "CONTINUE_MINIMAL_REPAIR"
    assert exact["continue_repair"] is False
    assert exact["exact_success_detected"] is True


def test_duplicate_repair_signature_is_rejected():
    guard = RepairNoveltyGuard()
    candidate = {
        "candidate_id": "repair_1",
        "operation": "replace_color",
        "program": {"steps": [{"operation": "replace_color"}]},
        "metadata": {
            "parent_candidate_id": "baseline",
            "target_residual_fingerprint": "abc",
            "repair_operation": "recolor_residual_cells",
            "target_locations": [[1, 1]],
        },
    }

    first = guard.review(candidate)
    second = guard.review(candidate, previous_signatures={first["repair_signature"]})

    assert first["repair_novelty_state"] == "NOVEL_REPAIR"
    assert second["repair_novelty_state"] == "DUPLICATE_REPAIR"
