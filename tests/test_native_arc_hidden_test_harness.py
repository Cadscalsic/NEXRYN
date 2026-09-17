import copy

import pytest

from core.arc_task_boundary import EvaluationTaskView, SolverTaskView
from runtime.evaluation.arc_hidden_test_harness import NativeARCEvaluationHarness
from runtime.transformation_compilation.semantic_to_transformation_compiler import (
    SemanticToTransformationCompiler,
)


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


def _solver_factory(attempt_outputs):
    seen = []

    def solver(view, test_index, attempt_index):
        seen.append((test_index, attempt_index, view))
        assert isinstance(view, SolverTaskView)
        assert view.hidden_test_output_solver_visible is False
        assert all("output" in example for example in view.train_examples)
        assert all("output" not in example for example in view.test_examples)
        return copy.deepcopy(attempt_outputs[test_index][attempt_index - 1])

    solver.seen = seen
    return solver


def test_harness_keeps_training_outputs_and_test_inputs_solver_visible():
    def inspect(view, test_index, attempt_index):
        assert view.train_examples[0]["output"].to_list() == [[3, 0], [0, 2]]
        assert view.test_examples[test_index]["input"].to_list()[0][0] in {1, 2}
        assert "output" not in view.test_examples[test_index]
        return [[3, 3], [0, 2]]

    report = NativeARCEvaluationHarness().evaluate_task(_task(), "native_1", inspect)
    assert report["hidden_test_output_solver_visible"] is False


def test_harness_freezes_two_attempts_before_evaluator_access():
    order = []

    def solver(view, test_index, attempt_index):
        assert not hasattr(view, "hidden_test_outputs")
        order.append(("solver", test_index, attempt_index))
        return _task()["test"][test_index]["input"]

    report = NativeARCEvaluationHarness().evaluate_task(_task(), "native_2", solver)
    assert report["prediction_freeze_state"] == "ALL_REQUIRED_ATTEMPTS_FROZEN"
    assert len(report["attempts"]) == 4
    assert order == [("solver", 0, 1), ("solver", 0, 2), ("solver", 1, 1), ("solver", 1, 2)]
    assert report["evaluation_integrity_state"] == "EVALUATOR_ONLY_AFTER_FREEZE"


def test_hidden_outputs_do_not_enter_compiler_candidate_generation_or_repair():
    observed = []
    compiler = SemanticToTransformationCompiler()

    def solver(view, test_index, attempt_index):
        visible_test = view.test_examples[test_index]
        assert "output" not in visible_test
        observed.append(visible_test["input"].to_list())
        compiler_report = compiler.compile(
            input_grid=view.train_examples[0]["input"].to_list(),
            output_grid=view.train_examples[0]["output"].to_list(),
            detected_concepts=["color_mapping"],
        )
        assert compiler_report["candidate_output_grid"] != _task()["test"][test_index]["output"]
        return visible_test["input"].to_list()

    report = NativeARCEvaluationHarness().evaluate_task(_task(), "native_3", solver)
    assert report["repair_feedback_to_solver"] is False
    assert len(observed) == 4


def test_exact_match_can_be_awarded_to_attempt_one_or_attempt_two():
    task = _task()

    def solver(view, test_index, attempt_index):
        if attempt_index == 1:
            return [[0, 0], [0, 0]]
        return task["test"][test_index]["output"]

    report = NativeARCEvaluationHarness().evaluate_task(task, "native_4", solver)
    assert all(item["attempt_1"]["exact_match"] is False for item in report["test_reports"])
    assert all(item["attempt_2"]["exact_match"] is True for item in report["test_reports"])
    assert all(item["attempt_1_id"] and item["attempt_2_id"] for item in report["test_reports"])
    assert report["task_score"] == 1
    assert report["metric"] == "EXACT_GRID_MATCH"


def test_both_incorrect_attempts_score_zero_and_partial_metrics_are_not_authoritative():
    report = NativeARCEvaluationHarness().evaluate_task(
        _task(),
        "native_5",
        lambda view, test_index, attempt_index: [[9]],
    )
    assert report["task_score"] == 0
    assert all(item["test_output_score"] == 0 for item in report["test_reports"])
    assert "final_score" not in report


def test_multiple_test_examples_preserve_order_and_identities():
    solver = _solver_factory([
        ([[3, 3], [0, 2]], [[3, 3], [0, 2]]),
        ([[2, 2], [0, 3]], [[2, 2], [0, 3]]),
    ])
    report = NativeARCEvaluationHarness().evaluate_task(_task(), "native_6", solver)
    assert [item["test_index"] for item in report["test_reports"]] == [0, 1]
    assert [item["test_index"] for item in report["attempts"]] == [0, 0, 1, 1]
    assert len({item["attempt_id"] for item in report["attempts"]}) == 4


def test_unfrozen_attempts_and_malformed_tasks_fail_closed():
    harness = NativeARCEvaluationHarness()
    with pytest.raises(ValueError, match="ARC_TEST_EXAMPLES_REQUIRED"):
        harness.evaluate_task({"train": _task()["train"], "test": []}, "native_7", lambda *_: [[0]])

    with pytest.raises(ValueError, match="ARC_SOLVER_CALLBACK_REQUIRED"):
        harness.evaluate_task(_task(), "native_8", None)


def test_reconstruction_and_hidden_success_have_distinct_semantics():
    report = NativeARCEvaluationHarness().evaluate_task(
        _task(),
        "native_9",
        lambda view, test_index, attempt_index: view.train_examples[0]["output"].to_list(),
    )
    assert "success_state" not in report
    assert report["metric"] == "EXACT_GRID_MATCH"
    assert report["evaluation_integrity_state"] == "EVALUATOR_ONLY_AFTER_FREEZE"


def test_evaluator_view_is_not_constructed_until_predictions_are_frozen():
    calls = []

    def solver(view, test_index, attempt_index):
        calls.append(type(view).__name__)
        assert not isinstance(view, EvaluationTaskView)
        return [[0, 0], [0, 0]]

    NativeARCEvaluationHarness().evaluate_task(_task(), "native_10", solver)
    assert calls == ["SolverTaskView"] * 4