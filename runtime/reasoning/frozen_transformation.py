"""Minimal training-to-application transformation boundary."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from itertools import permutations
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from runtime.engines.transformation_engine import TransformationEngine


SCHEMA_VERSION = "1.0"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _fingerprint(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        _plain(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"transformation_sha256_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _artifact_identity_payload(artifact: "FrozenTransformationArtifact") -> dict[str, Any]:
    return {
        "schema_version": artifact.schema_version,
        "task_id": artifact.task_id,
        "training_examples": list(artifact.learned_from_training_examples),
        "representation": artifact.transformation_representation,
        "program": artifact.executable_program,
        "provenance": artifact.parameter_provenance,
        "consistency": artifact.training_consistency,
    }


@dataclass(frozen=True)
class FrozenTransformationArtifact:
    artifact_id: str
    schema_version: str
    task_id: str
    learned_from_training_examples: tuple[str, ...]
    transformation_representation: Mapping[str, Any]
    executable_program: Mapping[str, Any]
    parameter_provenance: Mapping[str, Any]
    training_consistency: Mapping[str, Any]
    lifecycle_state: str
    frozen: bool
    immutable_fingerprint: str
    target_independent_application: bool

    def __post_init__(self) -> None:
        if self.lifecycle_state != "TRANSFORMATION_FROZEN" or not self.frozen:
            raise ValueError("TRANSFORMATION_ARTIFACT_NOT_FROZEN")
        object.__setattr__(self, "transformation_representation", _freeze(self.transformation_representation))
        object.__setattr__(self, "executable_program", _freeze(self.executable_program))
        object.__setattr__(self, "parameter_provenance", _freeze(self.parameter_provenance))
        object.__setattr__(self, "training_consistency", _freeze(self.training_consistency))
        if _fingerprint(_artifact_identity_payload(self)) != self.immutable_fingerprint:
            raise ValueError("TRANSFORMATION_ARTIFACT_FINGERPRINT_MISMATCH")

    def apply(self, input_grid: Any) -> dict[str, Any]:
        """Apply the frozen program without accepting target/evaluator inputs."""
        if not self.target_independent_application:
            raise ValueError("TARGET_INDEPENDENT_APPLICATION_REQUIRED")
        result = TransformationEngine().execute(
            _grid_array(input_grid),
            _plain(self.executable_program),
        )
        return {
            "prediction": result["output_grid"],
            "prediction_grid": result["output_grid"].tolist(),
            "artifact_id": self.artifact_id,
            "artifact_fingerprint": self.immutable_fingerprint,
            "application_state": "TARGET_FREE_PREDICTION",
            "execution_trace": result["execution_trace"],
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "learned_from_training_examples": list(self.learned_from_training_examples),
            "transformation_representation": _plain(self.transformation_representation),
            "executable_program": _plain(self.executable_program),
            "parameter_provenance": _plain(self.parameter_provenance),
            "training_consistency": _plain(self.training_consistency),
            "lifecycle_state": self.lifecycle_state,
            "frozen": self.frozen,
            "immutable_fingerprint": self.immutable_fingerprint,
            "target_independent_application": self.target_independent_application,
        }


def _canonical_step(step: Mapping[str, Any]) -> tuple[Any, ...]:
    operation = str(step.get("operation", ""))
    parameters = step.get("parameters", {})
    if isinstance(parameters, Mapping):
        items = tuple(
            (str(key), _canonical_scalar(value))
            for key, value in sorted(parameters.items(), key=lambda item: str(item[0]))
        )
    else:
        items = ("parameters", _canonical_scalar(parameters))
    return (operation, items)


def _canonical_scalar(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(
            (str(key), _canonical_scalar(item))
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        )
    if isinstance(value, (list, tuple)):
        return tuple(_canonical_scalar(item) for item in value)
    return value


def _candidate_program_signature(program: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(_canonical_step(step) for step in program.get("steps", []))


def _candidate_programs_from_mapping(mapping: Mapping[int, int]) -> list[Mapping[str, Any]]:
    ordered = sorted(mapping.items())
    if not ordered:
        return []

    programs: list[Mapping[str, Any]] = []
    for source_value, target_value in ordered:
        programs.append(
            {
                "step_count": 1,
                "steps": [
                    {
                        "operation": "replace_color",
                        "parameters": {"source": [int(source_value)], "target": [int(target_value)]},
                        "order": 0,
                    }
                ],
            }
        )

    if len(ordered) >= 2:
        for permutation in permutations(ordered):
            steps = [
                {
                    "operation": "replace_color",
                    "parameters": {"source": [int(source_value)], "target": [int(target_value)]},
                    "order": idx,
                }
                for idx, (source_value, target_value) in enumerate(permutation)
            ]
            programs.append({"step_count": len(steps), "steps": steps})

    deduped: list[Mapping[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for program in programs:
        signature = _candidate_program_signature(program)
        if signature in seen:
            continue
        seen.add(signature)
        deduped.append(program)
    return deduped


def learn_transformation(
    training_examples: Sequence[Mapping[str, Any]],
    *,
    task_id: str = "training_task",
) -> FrozenTransformationArtifact:
    """Learn one executable, target-independent program from all train pairs."""
    examples = list(training_examples or [])
    if not examples:
        raise ValueError("NO_TRAINING_EXAMPLES")

    candidate_sets: list[tuple[list[Mapping[str, Any]], dict[str, Any]]] = []
    for index, example in enumerate(examples):
        if not isinstance(example, Mapping) or "input" not in example or "output" not in example:
            raise ValueError("TRAINING_EXAMPLE_INPUT_OUTPUT_REQUIRED")
        source = _grid_array(example["input"])
        target = _grid_array(example["output"])
        candidates, example_provenance = _learn_pair(source, target, index)
        if not candidates:
            raise ValueError("NO_EXECUTABLE_TRANSFORMATION_LEARNED")
        candidate_sets.append((candidates, example_provenance))

    program = None
    ordered_candidates = sorted(
        candidate_sets[0][0],
        key=lambda candidate: (
            -(candidate.get("step_count", 1)),
            _candidate_program_signature(candidate),
        ),
    )
    for candidate in ordered_candidates:
        candidate_signature = _candidate_program_signature(candidate)
        if all(
            any(
                candidate_signature == _candidate_program_signature(other)
                for other in other_candidates
            )
            for other_candidates, _ in candidate_sets[1:]
        ):
            program = candidate
            break

    if program is None:
        raise ValueError("TRAINING_TRANSFORMATION_CONFLICT")

    consistency = {
        "state": "CONSISTENT_ACROSS_TRAINING_EXAMPLES",
        "example_count": len(examples),
        "validated_example_indices": list(range(len(examples))),
        "program_identity": _candidate_program_signature(program),
    }
    representation = {
        "operation": program["steps"][0]["operation"],
        "learning_state": "TRANSFORMATION_LEARNED",
        "program_depth": program["step_count"],
    }
    provenance: dict[str, Any] = {}
    for index, (candidates, example_provenance) in enumerate(candidate_sets):
        canonical = _candidate_program_signature(program)
        if any(canonical == _candidate_program_signature(candidate) for candidate in candidates):
            provenance[str(index)] = {
                **example_provenance,
                "canonical_program": canonical,
            }
        else:
            provenance[str(index)] = example_provenance

    identity_payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": str(task_id),
        "training_examples": [str(index) for index in range(len(examples))],
        "representation": representation,
        "program": program,
        "provenance": provenance,
        "consistency": consistency,
    }
    fingerprint = _fingerprint(identity_payload)
    return FrozenTransformationArtifact(
        artifact_id=fingerprint.replace("transformation_sha256_", "frozen_transformation:"),
        schema_version=SCHEMA_VERSION,
        task_id=str(task_id),
        learned_from_training_examples=tuple(str(index) for index in range(len(examples))),
        transformation_representation=representation,
        executable_program=program,
        parameter_provenance=provenance,
        training_consistency=consistency,
        lifecycle_state="TRANSFORMATION_FROZEN",
        frozen=True,
        immutable_fingerprint=fingerprint,
        target_independent_application=True,
    )


def _grid_array(value: Any) -> np.ndarray:
    if hasattr(value, "grid"):
        value = value.grid
    return np.asarray(value)


def _learn_pair(source: np.ndarray, target: np.ndarray, index: int):
    if source.shape != target.shape:
        return [], {"training_example_index": index, "state": "SHAPE_CHANGE_UNSUPPORTED"}
    if np.array_equal(source, target):
        program = {"step_count": 1, "steps": [{"operation": "preserve_objects", "parameters": {}, "order": 0}]}
        return [program], {"training_example_index": index, "parameter_sources": {}, "operation": "preserve_objects"}

    mapping: dict[int, int] = {}
    for source_value, target_value in zip(source.flat, target.flat):
        source_value = int(source_value)
        target_value = int(target_value)
        if source_value == target_value:
            continue
        prior = mapping.get(source_value)
        if prior is not None and prior != target_value:
            return [], {"training_example_index": index, "state": "CONFLICTING_PARAMETER_MAPPING"}
        mapping[source_value] = target_value
    if not mapping:
        return [], {"training_example_index": index, "state": "NO_CHANGE"}

    candidates = _candidate_programs_from_mapping(mapping)
    provenance = {
        "training_example_index": index,
        "operation": "replace_color",
        "parameter_sources": {
            "color_mapping": {
                "source": "training.input/output.changed_cells",
                "mapping": {str(key): value for key, value in mapping.items()},
            },
        },
    }
    return candidates, provenance


__all__ = ["FrozenTransformationArtifact", "learn_transformation"]