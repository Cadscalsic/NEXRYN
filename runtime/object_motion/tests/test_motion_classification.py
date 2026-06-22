from runtime.object_motion import motion_pattern_classifier


def test_motion_classification_separates_global_and_independent_motion():
    global_report = motion_pattern_classifier.classify([(2, 0), (2, 0)])
    independent_report = motion_pattern_classifier.classify([(4, 0), (3, 0), (0, 0)])

    assert global_report["motion_pattern"] == "global_translation"
    assert independent_report["motion_pattern"] == "independent_translation"
    assert independent_report["global_translation_allowed"] is False


def test_motion_classification_detects_gravity_when_all_moving_objects_fall_to_support():
    report = motion_pattern_classifier.classify(
        [(2, 0), (3, 0)],
        support_surfaces=[{"object_id": "floor"}],
    )

    assert report["motion_pattern"] == "gravity_motion"

