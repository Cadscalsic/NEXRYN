from runtime.object_motion import object_constraint_analyzer


def test_constraint_analysis_marks_support_objects_fixed():
    objects = [{"id": "obj_1"}, {"id": "floor"}]
    supports = [{"object_id": "floor", "row": 3, "columns": [0, 1, 2]}]

    profile = object_constraint_analyzer.analyze(objects, supports)

    assert profile["movable_objects"] == ["obj_1"]
    assert profile["fixed_objects"] == ["floor"]
    assert profile["support_objects"] == ["floor"]
    assert profile["anchors"] == ["floor"]

