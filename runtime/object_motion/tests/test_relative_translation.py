from runtime.object_motion import relative_translation_engine


def test_relative_translation_computes_per_object_vectors():
    source = [
        {"id": "obj_1", "color": 1, "size": 1, "center": {"row": 0, "col": 0}},
        {"id": "obj_2", "color": 2, "size": 1, "center": {"row": 1, "col": 1}},
    ]
    target = [
        {"id": "out_1", "color": 1, "size": 1, "center": {"row": 4, "col": 0}},
        {"id": "out_2", "color": 2, "size": 1, "center": {"row": 4, "col": 1}},
    ]

    translations = relative_translation_engine.compute(source, target)

    assert translations == {"obj_1": (4, 0), "obj_2": (3, 0)}

