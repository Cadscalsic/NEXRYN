import copy

import pytest

from core.arc_task_boundary import (
    EvaluationTaskView,
    PredictionAttempt,
    SolverTaskView,
    freeze_attempt,
)
from core.loader import ARCJSONLoader
from runtime.evaluation.evaluation_engine import UnifiedEvaluationEngine
from runtime.stages.task_loading import task_loading_stage


CANARY = [[9, 8], [7, 6]]


def _raw_task(hidden_output=None):
    task = {
        "train": [
            {
                "input": [[1, 0], [0, 2]],
                "output": [[3, 0], [0, 2]],
            }
        ],
        "test": [
            {
                "input": [[1, 1], [0, 2]],
            }
        ],
    }
    if hidden_output is not None:
        task["test"][0]["output"] = copy.deepcopy(hidden_output)
    return task


def _write_task(tmp_path, payload):
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "task.json"
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")
    return path


def _contains_object(root, predicate, seen=None):
    if seen is None:
        seen = set()
    obj_id = id(root)
    if obj_id in seen:
        return False
    seen.add(obj_id)
    try:
        if predicate(root):
            return True
    except Exception:
        pass
    if isinstance(root, dict):
        return any(
            _contains_object(key, predicate, seen)
            or _contains_object(value, predicate, seen)
            for key, value in root.items()
        )
    if isinstance(root, (list, tuple, set, frozenset)):
        return any(_contains_object(value, predicate, seen) for value in root)
    if hasattr(root, "__dict__") and root.__class__.__module__.startswith("core"):
        return _contains_object(vars(root), predicate, seen)
    return False


def test_solver_task_view_redacts_hidden_test_output_from_object_graph():
    view = SolverTaskView.from_raw_task(_raw_task(hidden_output=CANARY), "task_a2")

    assert view.test_examples[0]["input"].to_list() == [[1, 1], [0, 2]]
    assert "output" not in view.test_examples[0]
    assert not _contains_object(view, lambda value: value == CANARY)


def test_task_loading_solver_context_excludes_raw_loader_and_hidden_output(tmp_path):
    path = _write_task(tmp_path, _raw_task(hidden_output=CANARY))

    context = task_loading_stage({"task_path": str(path), "task_id": "task_a2"})

    assert context["task_loaded"] is True
    assert "loader" not in context
    assert "raw_task_data" not in context
    assert isinstance(context["solver_task_view"], SolverTaskView)
    assert not _contains_object(context, lambda value: isinstance(value, ARCJSONLoader))
    assert not _contains_object(context, lambda value: isinstance(value, EvaluationTaskView))
    assert not _contains_object(context, lambda value: value == CANARY)


def test_prediction_attempt_freeze_is_required_before_evaluation():
    attempt = PredictionAttempt.generated(
        task_id="task_a2",
        test_index=0,
        prediction=[[3, 3], [0, 2]],
        generation_source="test_solver",
    )

    with pytest.raises(ValueError, match="PREDICTION_ATTEMPT_NOT_FROZEN"):
        EvaluationTaskView.from_raw_task(
            _raw_task(hidden_output=CANARY),
            "task_a2",
            attempts=[attempt],
        )

    frozen = freeze_attempt(attempt)
    view = EvaluationTaskView.from_raw_task(
        _raw_task(hidden_output=[[3, 3], [0, 2]]),
        "task_a2",
        attempts=[frozen],
    )

    result = UnifiedEvaluationEngine().evaluate_task_view(view)
    assert result["evaluation_view_state"] == "EVALUATED"
    assert result["results"][0]["success"] is True
    assert result["evaluated_attempts"][0]["state"] == "EVALUATED"


def test_evaluator_rejects_altered_or_unfrozen_attempt():
    attempt = PredictionAttempt.generated(
        task_id="task_a2",
        test_index=0,
        prediction=[[3, 3], [0, 2]],
        generation_source="test_solver",
    )
    frozen = freeze_attempt(attempt)
    altered = PredictionAttempt(
        attempt_id=frozen.attempt_id,
        task_id=frozen.task_id,
        test_index=frozen.test_index,
        prediction=((9, 9), (9, 9)),
        generation_source=frozen.generation_source,
        state=frozen.state,
        attempt_fingerprint=frozen.attempt_fingerprint,
    )

    with pytest.raises(ValueError, match="PREDICTION_ATTEMPT_FINGERPRINT_MISMATCH"):
        EvaluationTaskView.from_raw_task(
            _raw_task(hidden_output=CANARY),
            "task_a2",
            attempts=[altered],
        )


def test_hidden_output_canaries_do_not_change_solver_view_or_prediction(tmp_path):
    paths = [
        _write_task(tmp_path / "a", _raw_task(hidden_output=[[9, 9], [9, 9]])),
        _write_task(tmp_path / "b", _raw_task(hidden_output=[[4, 4], [4, 4]])),
        _write_task(tmp_path / "c", _raw_task(hidden_output=None)),
    ]
    contexts = [
        task_loading_stage({"task_path": str(path), "task_id": "task_a2"})
        for path in paths
    ]

    fingerprints = {
        context["solver_task_view"].solver_fingerprint
        for context in contexts
    }
    assert len(fingerprints) == 1
    assert all(context["test_input_grid"].to_list() == [[1, 1], [0, 2]] for context in contexts)


def test_arc_benchmark_mode_declares_hidden_label_memory_guard(tmp_path):
    path = _write_task(tmp_path, _raw_task(hidden_output=CANARY))

    context = task_loading_stage(
        {
            "task_path": str(path),
            "task_id": "task_a2",
            "arc_benchmark_mode": True,
        }
    )

    assert context["arc_benchmark_memory_policy"]["hidden_label_memory_writes"] == (
        "DISABLED_FOR_BASELINE"
    )
    assert context["hidden_test_output_solver_visible"] is False
