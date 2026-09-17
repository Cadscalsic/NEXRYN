"""Competition-valid ARC hidden-test evaluation boundary.

The harness deliberately keeps raw task data out of the solver callback. Hidden
test outputs are materialized only after every required prediction is frozen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from core.arc_task_boundary import (
    EvaluationTaskView,
    PredictionAttempt,
    SolverTaskView,
    freeze_attempt,
)
from runtime.evaluation.evaluation_engine import UnifiedEvaluationEngine


SolverCallback = Callable[[SolverTaskView, int, int], Any]


@dataclass(frozen=True)
class HiddenTestEvaluationResult:
    """Stable report for one task evaluated without hidden-label feedback."""

    report: dict[str, Any]


class NativeARCEvaluationHarness:
    """Run solver-visible inference, then evaluator-only exact scoring."""

    required_attempts = 2

    def __init__(self, evaluation_engine: UnifiedEvaluationEngine | None = None):
        self.evaluation_engine = evaluation_engine or UnifiedEvaluationEngine()

    def evaluate_task(
        self,
        raw_task: Mapping[str, Any],
        task_id: str,
        solver: SolverCallback,
    ) -> dict[str, Any]:
        if not isinstance(raw_task, Mapping):
            raise ValueError("ARC_RAW_TASK_REQUIRED")
        if not callable(solver):
            raise ValueError("ARC_SOLVER_CALLBACK_REQUIRED")

        solver_view = SolverTaskView.from_raw_task(raw_task, task_id)
        if solver_view.hidden_test_output_solver_visible:
            raise ValueError("HIDDEN_OUTPUT_VISIBLE_BEFORE_SOLVER_START")
        if not solver_view.test_examples:
            raise ValueError("ARC_TEST_EXAMPLES_REQUIRED")

        attempts: list[PredictionAttempt] = []
        leakage_state = "NO_HIDDEN_OUTPUT_EXPOSED"
        for test_index in range(len(solver_view.test_examples)):
            for attempt_index in range(self.required_attempts):
                prediction = solver(solver_view, test_index, attempt_index + 1)
                if isinstance(prediction, PredictionAttempt):
                    if prediction.task_id != str(task_id) or prediction.test_index != test_index:
                        raise ValueError("SOLVER_ATTEMPT_IDENTITY_MISMATCH")
                    generated = prediction
                else:
                    generated = PredictionAttempt.generated(
                        task_id=str(task_id),
                        test_index=test_index,
                        prediction=prediction,
                        generation_source=f"native_arc_solver_attempt_{attempt_index + 1}",
                    )
                attempts.append(freeze_attempt(generated))

        if len(attempts) != len(solver_view.test_examples) * self.required_attempts:
            raise ValueError("PREDICTION_FREEZE_CONTRACT_FAILED")

        evaluation_view = EvaluationTaskView.from_raw_task(
            raw_task,
            str(task_id),
            attempts=attempts,
        )
        evaluation = self._evaluate_hidden_view(evaluation_view)
        report = self._build_report(
            task_id=str(task_id),
            solver_view=solver_view,
            evaluation_view=evaluation_view,
            evaluation=evaluation,
            leakage_state=leakage_state,
        )
        return report

    def _evaluate_hidden_view(
        self,
        evaluation_view: EvaluationTaskView,
    ) -> dict[str, Any]:
        """Compare frozen attempts without making partial metrics authoritative."""
        results = []
        for attempt in evaluation_view.attempts:
            predicted = np.asarray(attempt.prediction)
            target = np.asarray(evaluation_view.hidden_test_outputs[attempt.test_index])
            exact_match = bool(predicted.shape == target.shape and np.array_equal(predicted, target))
            diagnostic = {}
            if predicted.shape == target.shape:
                diagnostic = self.evaluation_engine.evaluate(predicted, target)
            results.append({
                "attempt_id": attempt.attempt_id,
                "task_id": attempt.task_id,
                "test_index": attempt.test_index,
                "exact_match": exact_match,
                "success": exact_match,
                "diagnostic": diagnostic,
            })
        return {
            "evaluation_view_state": "EVALUATED",
            "results": results,
        }

    def evaluate_tasks(
        self,
        tasks: Sequence[tuple[str, Mapping[str, Any]]],
        solver: SolverCallback,
        run_id: str,
    ) -> dict[str, Any]:
        task_reports = [
            self.evaluate_task(raw_task, task_id, solver)
            for task_id, raw_task in tasks
        ]
        task_scores = [report["task_score"] for report in task_reports]
        return {
            "run_id": str(run_id),
            "benchmark_state": "EVALUATED",
            "metric": "EXACT_GRID_MATCH",
            "task_count": len(task_reports),
            "task_reports": task_reports,
            "aggregate_exact_accuracy": round(
                sum(task_scores) / max(len(task_scores), 1),
                4,
            ),
            "governance_authority": "NONE",
            "production_execution_authority": "NONE",
        }

    def _build_report(
        self,
        *,
        task_id: str,
        solver_view: SolverTaskView,
        evaluation_view: EvaluationTaskView,
        evaluation: Mapping[str, Any],
        leakage_state: str,
    ) -> dict[str, Any]:
        by_test: dict[int, list[Mapping[str, Any]]] = {}
        for row in evaluation.get("results", []) or []:
            by_test.setdefault(int(row["test_index"]), []).append(row)

        test_reports = []
        for test_index in range(len(solver_view.test_examples)):
            rows = by_test.get(test_index, [])
            attempt_reports = [
                {
                    "attempt_id": row.get("attempt_id"),
                    "exact_match": bool(row.get("exact_match", row.get("success", False))),
                    "success": bool(row.get("success", False)),
                }
                for row in rows
            ]
            test_reports.append({
                "test_index": test_index,
                "attempt_1": attempt_reports[0] if len(attempt_reports) > 0 else None,
                "attempt_2": attempt_reports[1] if len(attempt_reports) > 1 else None,
                "attempt_1_id": (
                    attempt_reports[0].get("attempt_id")
                    if len(attempt_reports) > 0
                    else None
                ),
                "attempt_2_id": (
                    attempt_reports[1].get("attempt_id")
                    if len(attempt_reports) > 1
                    else None
                ),
                "exact_match": any(item["exact_match"] for item in attempt_reports),
                "test_output_score": int(any(item["exact_match"] for item in attempt_reports)),
            })

        return {
            "task_id": task_id,
            "solver_view_identity": solver_view.solver_fingerprint,
            "evaluation_view_identity": evaluation_view.evaluation_fingerprint,
            "hidden_test_output_solver_visible": False,
            "prediction_freeze_state": "ALL_REQUIRED_ATTEMPTS_FROZEN",
            "attempt_count_per_test": self.required_attempts,
            "attempts": [attempt.as_report() for attempt in evaluation_view.attempts],
            "test_reports": test_reports,
            "task_score": int(all(item["exact_match"] for item in test_reports)),
            "metric": "EXACT_GRID_MATCH",
            "leakage_detection_state": leakage_state,
            "evaluation_integrity_state": "EVALUATOR_ONLY_AFTER_FREEZE",
            "evaluation_view_state": evaluation.get("evaluation_view_state"),
            "governance_authority": "NONE",
            "arena_authority": "NONE",
            "repair_feedback_to_solver": False,
        }


__all__ = ["HiddenTestEvaluationResult", "NativeARCEvaluationHarness"]