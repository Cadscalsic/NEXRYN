import pytest

from core.arc_task_boundary import (
    EvaluationTaskView,
    PredictionAttempt,
    SolverTaskView,
)
from runtime.evaluation.arc_hidden_test_harness import NativeARCEvaluationHarness
from runtime.evaluation.native_arc_solver_adapter import NativeARCSolverAdapter


def _task():
    return {
        "train": [
            {"input": [[1, 0], [0, 2]], "output": [[3, 0], [0, 2]]},
            {"input": [[2, 0], [0, 1]], "output": [[2, 0], [0, 3]]},
        ],
        "test": [
            {"input": [[1, 1], [0, 2]], "output": [[3, 3], [0, 2]]},
            {"input": [[2, 2], [0, 1]], "output": [[2, 2], [0, 3]]},
        ],
    }


def _conflict_task():
    return {
        "train": [
            {"input": [[1]], "output": [[2]]},
            {"input": [[1]], "output": [[3]]},
        ],
        "test": [{"input": [[1]], "output": [[2]]}],
    }


def test_adapter_accepts_solver_view_and_builds_frozen_artifact_before_prediction():
    task = _task()
    view = SolverTaskView.from_raw_task(task, "adapter_1")
    adapter = NativeARCSolverAdapter()

    attempt = adapter(view, 0, 1)

    assert isinstance(attempt, PredictionAttempt)
    assert attempt.task_id == "adapter_1"
    assert attempt.test_index == 0
    assert attempt.prediction == ((3, 3), (0, 2))
    assert "artifact_id=" in attempt.generation_source
    assert "artifact_fingerprint=" in attempt.generation_source
    assert "target_free=True" in attempt.generation_source
    assert "attempt_diversity_state=ATTEMPT_DIVERSITY_NOT_AVAILABLE" in attempt.generation_source


def test_adapter_is_compatible_with_native_harness_and_keeps_hidden_outputs_hidden():
    task = _task()
    report = NativeARCEvaluationHarness().evaluate_task(task, "adapter_harness", NativeARCSolverAdapter())

    assert report["hidden_test_output_solver_visible"] is False
    assert report["evaluation_integrity_state"] == "EVALUATOR_ONLY_AFTER_FREEZE"
    assert report["task_score"] == 1
    assert [item["test_index"] for item in report["test_reports"]] == [0, 1]
    assert all(item["attempt_1"]["exact_match"] is True for item in report["test_reports"])
    assert all(item["attempt_2"]["exact_match"] is True for item in report["test_reports"])


def test_adapter_rejects_evaluation_view_and_hidden_output_objects():
    adapter = NativeARCSolverAdapter()
    hidden_view = EvaluationTaskView(
        task_id="adapter_eval",
        attempts=(
            PredictionAttempt.generated(
                task_id="adapter_eval",
                test_index=0,
                prediction=((3, 3), (0, 2)),
                generation_source="probe",
            ),
        ),
        hidden_test_outputs=((3, 3), (0, 2)),
        evaluation_fingerprint="probe_fingerprint",
    )

    with pytest.raises(ValueError, match="EVALUATION_TASK_VIEW_NOT_ALLOWED"):
        adapter(hidden_view, 0, 1)


def test_adapter_reuses_one_frozen_artifact_for_all_test_examples_and_marks_duplicate_attempts():
    task = _task()
    adapter = NativeARCSolverAdapter()

    first = adapter(SolverTaskView.from_raw_task(task, "adapter_2"), 0, 1)
    second = adapter(SolverTaskView.from_raw_task(task, "adapter_2"), 1, 1)

    assert first.attempt_id != second.attempt_id
    assert "artifact_id=" in first.generation_source
    assert "artifact_id=" in second.generation_source
    assert "attempt_diversity_state=ATTEMPT_DIVERSITY_NOT_AVAILABLE" in second.generation_source


def test_conflicting_transformations_fail_closed_for_adapter():
    view = SolverTaskView.from_raw_task(_conflict_task(), "adapter_conflict")
    adapter = NativeARCSolverAdapter()

    with pytest.raises(ValueError, match="TRAINING_TRANSFORMATION_CONFLICT"):
        adapter(view, 0, 1)


def test_unsupported_shape_changes_fail_closed_for_adapter():
    raw = {
        "train": [{"input": [[1, 0]], "output": [[1], [0]]}],
        "test": [{"input": [[1, 0]], "output": [[1], [0]]}],
    }
    adapter = NativeARCSolverAdapter()

    with pytest.raises(ValueError, match="NO_EXECUTABLE_TRANSFORMATION_LEARNED"):
        adapter(SolverTaskView.from_raw_task(raw, "adapter_shape"), 0, 1)
