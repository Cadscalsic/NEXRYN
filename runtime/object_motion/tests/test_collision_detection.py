from runtime.object_motion import collision_detection_engine


def test_collision_detection_reports_boundary_and_support_contact():
    obj = {"id": "obj_1", "cells": [(0, 1)], "color": 2}

    boundary = collision_detection_engine.check([[0, 2, 0]], obj, translation=(-1, 0))
    support = collision_detection_engine.check(
        [[0, 2, 0], [8, 8, 8]],
        obj,
        translation=(1, 0),
        fixed_cells={(1, 1)},
    )

    assert boundary["collision_type"] == "boundary_collision"
    assert support["collision_type"] == "support_surface_collision"

