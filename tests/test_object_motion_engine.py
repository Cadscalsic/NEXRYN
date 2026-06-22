import numpy as np

from runtime.object_motion import (
    motion_pattern_classifier,
    object_motion_engine,
    support_surface_detector,
)
from runtime.transforms.primitive_executor import PrimitiveExecutor
from runtime.world.world_model import WorldModelEngine


def falling_input():
    return [
        [1, 0, 0, 0, 0],
        [0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 3],
        [8, 8, 8, 8, 8],
    ]


def falling_target():
    return [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [1, 0, 2, 0, 3],
        [8, 8, 8, 8, 8],
    ]


def test_motion_classifier_rejects_global_translation_when_variance_exists():
    report = motion_pattern_classifier.classify([(4, 0), (3, 0), (0, 0)])

    assert report["motion_pattern"] == "independent_translation"
    assert report["global_translation_assumptions"] is False
    assert report["translation_variance"] > 0.1


def test_support_surface_detector_finds_horizontal_floor():
    surfaces = support_surface_detector.detect(falling_input())

    assert surfaces
    assert surfaces[0]["support_type"] == "support_surface"
    assert surfaces[0]["row"] == 5
    assert surfaces[0]["color"] == 8


def test_object_motion_engine_computes_translation_per_object():
    report = object_motion_engine.analyze(falling_input(), falling_target())

    assert report["motion_pattern"] == "gravity_motion"
    assert report["translation_per_object"]["obj_1"] == (4, 0)
    assert report["translation_per_object"]["obj_2"] == (3, 0)
    assert report["translation_per_object"]["obj_3"] == (0, 0)
    assert report["fixed_objects"] == ["obj_4"]
    assert np.array_equal(report["predicted_grid"], np.array(falling_target()))


def test_object_level_translate_executes_independent_motion():
    result = PrimitiveExecutor().run_execution(
        falling_input(),
        [{
            "primitive": "object_level_translate",
            "parameters": {
                "translation_per_object": {
                    "obj_1": (4, 0),
                    "obj_2": (3, 0),
                    "obj_3": (0, 0),
                    "obj_4": (0, 0),
                },
                "fixed_objects": ["obj_4"],
            },
        }],
    )

    assert result["output_grid"].tolist() == falling_target()


def test_world_model_prefers_object_level_motion_over_global_translation():
    anticipation = WorldModelEngine().anticipate_program(
        input_grid=falling_input(),
        target_grid=falling_target(),
        synthesized_program={
            "step_count": 1,
            "steps": [{
                "operation": "translate_down",
                "parameters": {"translation": (1, 0)},
            }],
        },
    )

    assert anticipation["OBJECT_MOTION_REPORT"]["motion_pattern"] == "gravity_motion"
    assert anticipation["prediction_report"]["prediction_accuracy"] == 1.0
    assert anticipation["localized_synthesized_program"]["steps"][0]["operation"] == "object_level_translate"
    assert anticipation["transformation_localization"]["translation_per_object"]["obj_1"] == (4, 0)
