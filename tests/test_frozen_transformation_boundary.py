import dataclasses

import pytest

from runtime.reasoning.frozen_transformation import (
    FrozenTransformationArtifact,
    learn_transformation,
)


def _training_pairs():
    return [
        {"input": [[1, 0], [0, 2]], "output": [[3, 0], [0, 4]]},
        {"input": [[1, 2], [0, 1]], "output": [[3, 4], [0, 3]]},
    ]


def test_learning_uses_all_training_pairs_and_freezes_executable_artifact():
    artifact = learn_transformation(_training_pairs(), task_id="task_freeze")

    assert isinstance(artifact, FrozenTransformationArtifact)
    assert artifact.lifecycle_state == "TRANSFORMATION_FROZEN"
    assert artifact.frozen is True
    assert artifact.learned_from_training_examples == ("0", "1")
    assert artifact.training_consistency["state"] == (
        "CONSISTENT_ACROSS_TRAINING_EXAMPLES"
    )
    assert artifact.executable_program["steps"][0]["operation"] == "replace_color"


def test_artifact_identity_is_stable_and_provenance_points_to_training_data():
    first = learn_transformation(_training_pairs(), task_id="task_identity")
    second = learn_transformation(_training_pairs(), task_id="task_identity")

    assert first.artifact_id == second.artifact_id
    assert first.immutable_fingerprint == second.immutable_fingerprint
    assert first.parameter_provenance["0"]["parameter_sources"]["color_mapping"][
        "source"
    ] == "training.input/output.changed_cells"
    assert "target" not in first.as_dict()["parameter_provenance"]["0"]


def test_application_is_target_free_and_returns_artifact_provenance():
    artifact = learn_transformation(_training_pairs(), task_id="task_apply")

    result = artifact.apply([[1, 1], [2, 0]])

    assert result["application_state"] == "TARGET_FREE_PREDICTION"
    assert result["prediction_grid"] == [[3, 3], [4, 0]]
    assert result["artifact_id"] == artifact.artifact_id
    assert "accuracy" not in result
    assert "difference_count" not in result
    assert "residual_locations" not in result


def test_application_does_not_depend_on_unseen_target_value():
    artifact = learn_transformation(_training_pairs(), task_id="task_hidden")
    prediction_a = artifact.apply([[1, 0], [0, 2]])["prediction_grid"]
    prediction_b = artifact.apply([[1, 0], [0, 2]])["prediction_grid"]

    assert prediction_a == prediction_b == [[3, 0], [0, 4]]


def test_frozen_artifact_cannot_be_silently_mutated():
    artifact = learn_transformation(_training_pairs(), task_id="task_immutable")

    with pytest.raises(dataclasses.FrozenInstanceError):
        artifact.task_id = "changed"
    with pytest.raises(TypeError):
        artifact.executable_program["steps"] = ()


def test_conflicting_training_transformations_fail_closed():
    with pytest.raises(ValueError, match="TRAINING_TRANSFORMATION_CONFLICT"):
        learn_transformation(
            [
                {"input": [[1]], "output": [[2]]},
                {"input": [[1]], "output": [[3]]},
            ],
            task_id="task_conflict",
        )


def test_unsupported_shape_change_fails_closed():
    with pytest.raises(ValueError, match="NO_EXECUTABLE_TRANSFORMATION_LEARNED"):
        learn_transformation(
            [{"input": [[1, 0]], "output": [[1], [0]]}],
            task_id="task_shape_change",
        )


def test_two_step_compositional_program_is_learned_and_applies_target_free():
    training = [
        {"input": [[1, 2]], "output": [[3, 3]]},
        {"input": [[2, 1]], "output": [[3, 3]]},
    ]

    artifact = learn_transformation(training, task_id="task_two_step")

    assert artifact.executable_program["step_count"] == 2
    assert [step["operation"] for step in artifact.executable_program["steps"]] == [
        "replace_color",
        "replace_color",
    ]
    assert artifact.training_consistency["state"] == "CONSISTENT_ACROSS_TRAINING_EXAMPLES"
    assert artifact.apply([[1]])["prediction_grid"] == [[3]]


def test_program_identity_distinguishes_operation_order():
    training = [{"input": [[1]], "output": [[3]]}]

    left = learn_transformation(training, task_id="task_order_left")
    right = learn_transformation(
        [{"input": [[1]], "output": [[2]]}],
        task_id="task_order_right",
    )

    assert left.immutable_fingerprint != right.immutable_fingerprint
    assert left.apply([[1]])["prediction_grid"] == [[3]]
    assert right.apply([[1]])["prediction_grid"] == [[2]]


def test_multi_example_program_requires_all_training_examples_to_match():
    with pytest.raises(ValueError, match="TRAINING_TRANSFORMATION_CONFLICT"):
        learn_transformation(
            [
                {"input": [[1]], "output": [[2]]},
                {"input": [[1]], "output": [[3]]},
            ],
            task_id="task_requires_all_examples",
        )


def test_empty_or_malformed_training_fails_closed():
    with pytest.raises(ValueError, match="NO_TRAINING_EXAMPLES"):
        learn_transformation([], task_id="task_empty")
    with pytest.raises(ValueError, match="TRAINING_EXAMPLE_INPUT_OUTPUT_REQUIRED"):
        learn_transformation([{"input": [[1]]}], task_id="task_malformed")