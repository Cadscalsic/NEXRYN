import numpy as np

from runtime.stages.transformation import (
    _apply_output_shape_intent,
    _derive_output_shape_intent,
)


def test_output_shape_intent_derives_visible_train_dimension_rule():
    train_examples = (
        {
            "input": np.zeros((15, 15), dtype=int),
            "output": np.zeros((15, 7), dtype=int),
        },
        {
            "input": np.zeros((7, 15), dtype=int),
            "output": np.zeros((7, 7), dtype=int),
        },
    )

    intent = _derive_output_shape_intent(
        train_examples,
        np.zeros((19, 15), dtype=int),
    )

    assert intent["supported"] is True
    assert intent["intended_shape"] == [19, 7]
    assert intent["source"] == "solver_visible_train_pairs"
    assert intent["authority"] == "DATA_ONLY"
    assert intent["hidden_target_shape_used"] is False


def test_hidden_shape_canary_same_solver_visible_data_same_intent():
    train_examples = (
        {
            "input": np.zeros((15, 15), dtype=int),
            "output": np.zeros((15, 7), dtype=int),
        },
        {
            "input": np.zeros((7, 15), dtype=int),
            "output": np.zeros((7, 7), dtype=int),
        },
    )
    test_input = np.zeros((19, 15), dtype=int)

    intent_a = _derive_output_shape_intent(train_examples, test_input)
    intent_b = _derive_output_shape_intent(train_examples, test_input)

    assert intent_a["intended_shape"] == intent_b["intended_shape"]
    assert intent_a["provenance"] == intent_b["provenance"]


def test_shape_changing_prediction_with_unsupported_intent_fails_closed():
    train_examples = (
        {
            "input": np.zeros((30, 30), dtype=int),
            "output": np.zeros((9, 4), dtype=int),
        },
        {
            "input": np.zeros((30, 30), dtype=int),
            "output": np.zeros((4, 5), dtype=int),
        },
    )

    predicted, intent = _apply_output_shape_intent(
        np.zeros((30, 30), dtype=int),
        train_examples,
        np.zeros((30, 30), dtype=int),
    )

    assert predicted is None
    assert intent["supported"] is False
    assert intent["materialization_state"] == "UNSUPPORTED_OUTPUT_SHAPE_INTENT"


def test_output_shape_intent_derives_visible_transpose_dimension_rule():
    train_examples = (
        {
            "input": np.zeros((16, 12), dtype=int),
            "output": np.zeros((12, 16), dtype=int),
        },
        {
            "input": np.zeros((10, 10), dtype=int),
            "output": np.zeros((10, 10), dtype=int),
        },
        {
            "input": np.zeros((14, 9), dtype=int),
            "output": np.zeros((9, 14), dtype=int),
        },
    )

    intent = _derive_output_shape_intent(
        train_examples,
        np.zeros((30, 30), dtype=int),
    )

    assert intent["supported"] is True
    assert intent["rule_type"] == "VISIBLE_TRAIN_DIMENSION_TRANSPOSE"
    assert intent["intended_shape"] == [30, 30]


def test_shape_intent_does_not_crop_or_pad_to_train_derived_shape():
    train_examples = (
        {
            "input": np.zeros((15, 15), dtype=int),
            "output": np.zeros((15, 7), dtype=int),
        },
        {
            "input": np.zeros((7, 15), dtype=int),
            "output": np.zeros((7, 7), dtype=int),
        },
    )

    predicted, intent = _apply_output_shape_intent(
        np.ones((19, 15), dtype=int),
        train_examples,
        np.zeros((19, 15), dtype=int),
    )

    assert predicted is None
    assert intent["supported"] is True
    assert intent["intended_shape"] == [19, 7]
    assert intent["materialization_state"] == "PREDICTION_SHAPE_INTENT_MISMATCH"


def test_same_shape_task_leaves_prediction_unchanged():
    train_examples = (
        {
            "input": np.zeros((3, 3), dtype=int),
            "output": np.ones((3, 3), dtype=int),
        },
    )
    original = np.ones((3, 3), dtype=int)

    predicted, intent = _apply_output_shape_intent(
        original,
        train_examples,
        np.zeros((3, 3), dtype=int),
    )

    assert predicted is original
    assert intent["materialization_state"] == "OUTPUT_SHAPE_INTENT_NOT_REQUIRED"
