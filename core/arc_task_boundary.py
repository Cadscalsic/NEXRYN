from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from core.grid import ARCGrid


ATTEMPT_STATES = ("GENERATED", "FROZEN", "COMMITTED", "EVALUATED")


@dataclass(frozen=True)
class SolverTaskView:
    task_id: str
    train_examples: tuple[dict[str, ARCGrid], ...]
    test_examples: tuple[dict[str, ARCGrid], ...]
    solver_fingerprint: str
    hidden_test_output_solver_visible: bool = False
    authority: str = "SOLVER_VISIBLE_DATA_ONLY"

    @classmethod
    def from_raw_task(
        cls,
        raw_task: Mapping[str, Any],
        task_id: str,
    ) -> "SolverTaskView":
        train_examples = tuple(
            {
                "input": ARCGrid(example["input"]),
                "output": ARCGrid(example["output"]),
            }
            for example in raw_task.get("train", [])
        )
        test_examples = tuple(
            {"input": ARCGrid(example["input"])}
            for example in raw_task.get("test", [])
        )
        payload = {
            "task_id": str(task_id),
            "train": [
                {
                    "input": item["input"].to_list(),
                    "output": item["output"].to_list(),
                }
                for item in train_examples
            ],
            "test": [
                {"input": item["input"].to_list()}
                for item in test_examples
            ],
        }
        return cls(
            task_id=str(task_id),
            train_examples=train_examples,
            test_examples=test_examples,
            solver_fingerprint=_stable_id("solver_task_view", payload),
        )

    def first_train_example(self) -> dict[str, ARCGrid] | None:
        return self.train_examples[0] if self.train_examples else None

    def first_test_example(self) -> dict[str, ARCGrid] | None:
        return self.test_examples[0] if self.test_examples else None


@dataclass(frozen=True)
class PredictionAttempt:
    attempt_id: str
    task_id: str
    test_index: int
    prediction: tuple[tuple[int, ...], ...]
    generation_source: str
    state: str = "GENERATED"
    attempt_fingerprint: str = ""

    @classmethod
    def generated(
        cls,
        *,
        task_id: str,
        test_index: int,
        prediction: Any,
        generation_source: str,
    ) -> "PredictionAttempt":
        normalized_prediction = _tuple_grid(prediction)
        payload = {
            "task_id": str(task_id),
            "test_index": int(test_index),
            "prediction": normalized_prediction,
            "generation_source": str(generation_source),
        }
        attempt_id = _stable_id("prediction_attempt", payload)
        return cls(
            attempt_id=attempt_id,
            task_id=str(task_id),
            test_index=int(test_index),
            prediction=normalized_prediction,
            generation_source=str(generation_source),
        )

    def fingerprint_payload(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "task_id": self.task_id,
            "test_index": self.test_index,
            "prediction": self.prediction,
            "generation_source": self.generation_source,
            "state": self.state,
        }

    def expected_fingerprint(self) -> str:
        return _stable_id("prediction_attempt_fingerprint", self.fingerprint_payload())

    def as_report(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "task_id": self.task_id,
            "test_index": self.test_index,
            "prediction": [list(row) for row in self.prediction],
            "generation_source": self.generation_source,
            "state": self.state,
            "attempt_fingerprint": self.attempt_fingerprint,
        }


@dataclass(frozen=True)
class EvaluationTaskView:
    task_id: str
    attempts: tuple[PredictionAttempt, ...]
    hidden_test_outputs: tuple[tuple[tuple[int, ...], ...], ...]
    evaluation_fingerprint: str
    authority: str = "EVALUATOR_ONLY_AFTER_FREEZE"

    @classmethod
    def from_raw_task(
        cls,
        raw_task: Mapping[str, Any],
        task_id: str,
        attempts: Iterable[PredictionAttempt],
    ) -> "EvaluationTaskView":
        frozen_attempts = tuple(attempts)
        for attempt in frozen_attempts:
            _require_valid_frozen_attempt(attempt, task_id)
        hidden_outputs = tuple(
            _tuple_grid(example["output"])
            for example in raw_task.get("test", [])
            if isinstance(example, Mapping) and "output" in example
        )
        if not hidden_outputs:
            raise ValueError("HIDDEN_TEST_OUTPUT_MISSING")
        payload = {
            "task_id": str(task_id),
            "attempts": [attempt.as_report() for attempt in frozen_attempts],
            "hidden_test_outputs": hidden_outputs,
        }
        return cls(
            task_id=str(task_id),
            attempts=frozen_attempts,
            hidden_test_outputs=hidden_outputs,
            evaluation_fingerprint=_stable_id("evaluation_task_view", payload),
        )


def freeze_attempt(attempt: PredictionAttempt) -> PredictionAttempt:
    if attempt.state != "GENERATED":
        raise ValueError("PREDICTION_ATTEMPT_NOT_GENERATED")
    frozen = PredictionAttempt(
        attempt_id=attempt.attempt_id,
        task_id=attempt.task_id,
        test_index=attempt.test_index,
        prediction=attempt.prediction,
        generation_source=attempt.generation_source,
        state="FROZEN",
    )
    return PredictionAttempt(
        attempt_id=frozen.attempt_id,
        task_id=frozen.task_id,
        test_index=frozen.test_index,
        prediction=frozen.prediction,
        generation_source=frozen.generation_source,
        state=frozen.state,
        attempt_fingerprint=frozen.expected_fingerprint(),
    )


def _require_valid_frozen_attempt(
    attempt: PredictionAttempt,
    task_id: str,
) -> None:
    if attempt.state not in {"FROZEN", "COMMITTED"}:
        raise ValueError("PREDICTION_ATTEMPT_NOT_FROZEN")
    if str(attempt.task_id) != str(task_id):
        raise ValueError("PREDICTION_ATTEMPT_TASK_MISMATCH")
    if not attempt.attempt_fingerprint:
        raise ValueError("PREDICTION_ATTEMPT_FINGERPRINT_MISSING")
    if attempt.attempt_fingerprint != attempt.expected_fingerprint():
        raise ValueError("PREDICTION_ATTEMPT_FINGERPRINT_MISMATCH")


def _tuple_grid(value: Any) -> tuple[tuple[int, ...], ...]:
    if isinstance(value, ARCGrid):
        value = value.to_list()
    elif hasattr(value, "tolist"):
        value = value.tolist()
    return tuple(tuple(int(cell) for cell in row) for row in value)


def _stable_id(prefix: str, payload: Any) -> str:
    text = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=True,
        default=str,
        separators=(",", ":"),
    )
    return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


__all__ = [
    "ATTEMPT_STATES",
    "EvaluationTaskView",
    "PredictionAttempt",
    "SolverTaskView",
    "freeze_attempt",
]
