from runtime.object_motion import gravity_reasoning_engine, motion_budget_controller


def test_gravity_reasoning_falls_until_support():
    motion_budget_controller.reset()
    grid = [
        [0, 2, 0],
        [0, 0, 0],
        [0, 0, 0],
        [8, 8, 8],
    ]
    obj = {"id": "obj_1", "cells": [(0, 1)], "color": 2}
    fixed_cells = {(3, 0), (3, 1), (3, 2)}

    result = gravity_reasoning_engine.simulate(
        grid,
        obj,
        fixed_cells=fixed_cells,
        support_objects={(3, 1): "floor"},
    )

    assert result["translation"] == (2, 0)
    assert result["final_position"] == (2, 1)
    assert result["support_object"] == "floor"
    assert result["iterations"] > 0

