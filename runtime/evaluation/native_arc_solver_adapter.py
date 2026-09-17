from __future__ import annotations

from dataclasses import dataclass

from core.arc_task_boundary import EvaluationTaskView, PredictionAttempt, SolverTaskView
from runtime.reasoning.frozen_transformation import FrozenTransformationArtifact, learn_transformation


@dataclass(frozen=True)
class NativeARCSolverAdapter:
    """Thin adapter from SolverTaskView to a frozen transformation artifact and generated attempts."""

    task_id: str | None = None
    artifact: FrozenTransformationArtifact | None = None
    attempt_diversity_state: str = "ATTEMPT_DIVERSITY_NOT_AVAILABLE"

    def __call__(self, solver_view: SolverTaskView, test_index: int, attempt_index: int) -> PredictionAttempt:
        if isinstance(solver_view, EvaluationTaskView):
            raise ValueError("EVALUATION_TASK_VIEW_NOT_ALLOWED")
        if not isinstance(solver_view, SolverTaskView):
            raise ValueError("SOLVER_TASK_VIEW_REQUIRED")
        if not solver_view.train_examples:
            raise ValueError("NO_TRAINING_EXAMPLES")

        task_id = str(self.task_id or solver_view.task_id)
        artifact = self._learn_artifact(task_id, solver_view)

        if not 0 <= test_index < len(solver_view.test_examples):
            raise ValueError("TEST_INDEX_OUT_OF_RANGE")

        prediction = artifact.apply(solver_view.test_examples[test_index]["input"])
        prediction_grid = tuple(tuple(int(cell) for cell in row) for row in prediction["prediction_grid"])

        generation_source = (
            f"native_arc_solver_adapter:task_id={task_id};artifact_id={artifact.artifact_id};"
            f"artifact_fingerprint={artifact.immutable_fingerprint};target_free=True;"
            f"attempt_index={attempt_index};attempt_diversity_state={self.attempt_diversity_state}"
        )
        return PredictionAttempt.generated(
            task_id=task_id,
            test_index=test_index,
            prediction=prediction_grid,
            generation_source=generation_source,
        )

    def _learn_artifact(self, task_id: str, solver_view: SolverTaskView) -> FrozenTransformationArtifact:
        training = [
            {"input": ex["input"].to_list(), "output": ex["output"].to_list()}
            for ex in solver_view.train_examples
            if "output" in ex
        ]
        if not training:
            raise ValueError("NO_TRAINING_EXAMPLES")

        artifact = learn_transformation(training, task_id=task_id)
        if self.artifact is None:
            object.__setattr__(self, "artifact", artifact)
        elif self.artifact.immutable_fingerprint != artifact.immutable_fingerprint:
            raise ValueError("ARTIFACT_FINGERPRINT_MISMATCH")
        return artifact


__all__ = ["NativeARCSolverAdapter"]
