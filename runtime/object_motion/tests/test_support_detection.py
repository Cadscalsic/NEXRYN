from runtime.object_motion import support_surface_detector


def test_support_detection_finds_floor_run():
    grid = [
        [0, 1, 0, 0],
        [0, 0, 0, 0],
        [8, 8, 8, 8],
    ]

    surfaces = support_surface_detector.detect(grid)

    assert surfaces[0]["row"] == 2
    assert surfaces[0]["support_type"] == "support_surface"
    assert surfaces[0]["stability_score"] == 1.0

