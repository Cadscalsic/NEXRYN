import json

import numpy as np

from core.perception import PerceptionEngine


def relation_names(scene):
    return {relation["relation"] for relation in scene["relations"]}


def test_empty_grid():
    scene = PerceptionEngine().perceive([])

    assert scene["height"] == 0
    assert scene["width"] == 0
    assert scene["objects"] == []
    assert scene["summary"]["object_count"] == 0


def test_single_object_extraction():
    scene = PerceptionEngine().perceive([[0, 1], [0, 1]])

    assert len(scene["objects"]) == 1
    assert scene["objects"][0]["id"] == "obj_1"
    assert scene["objects"][0]["color"] == 1
    assert scene["objects"][0]["size"] == 2


def test_multiple_colors():
    scene = PerceptionEngine().perceive([[1, 0, 2]])

    assert [obj["color"] for obj in scene["objects"]] == [1, 2]


def test_same_color_separated_objects():
    scene = PerceptionEngine().perceive([[1, 0, 1]])

    assert len(scene["objects"]) == 2
    assert [obj["color"] for obj in scene["objects"]] == [1, 1]


def test_bounding_box_correctness():
    obj = PerceptionEngine().perceive([
        [0, 0, 0],
        [0, 2, 2],
        [0, 2, 0],
    ])["objects"][0]

    assert obj["bbox"] == {
        "min_row": 1,
        "min_col": 1,
        "max_row": 2,
        "max_col": 2,
        "height": 2,
        "width": 2,
    }


def test_center_correctness():
    obj = PerceptionEngine().perceive([[0, 0, 0], [1, 1, 1]])["objects"][0]

    assert obj["center"] == {"row": 1.0, "col": 1.0}


def test_shape_normalization():
    engine = PerceptionEngine()

    assert engine.normalize_shape([(4, 5), (4, 6), (5, 5)]) == [
        (0, 0),
        (0, 1),
        (1, 0),
    ]


def test_shape_signature_stability():
    engine = PerceptionEngine()

    assert engine.compute_shape_signature([(1, 0), (0, 1), (0, 0)]) == (
        "0,0|0,1|1,0"
    )


def test_hole_detection():
    scene = PerceptionEngine().perceive([
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ])

    assert scene["objects"][0]["holes"] == 1


def test_solidity_detection():
    scene = PerceptionEngine().perceive([[1, 1], [1, 1]])

    assert scene["objects"][0]["is_solid"] is True


def test_edge_touching_detection():
    scene = PerceptionEngine().perceive([[1, 0], [0, 0]])

    assert scene["objects"][0]["edge_touching"] is True


def test_left_of():
    scene = PerceptionEngine().perceive([[1, 0, 2]])

    assert "left_of" in relation_names(scene)


def test_right_of():
    scene = PerceptionEngine().perceive([[1, 0, 2]])

    assert "right_of" in relation_names(scene)


def test_above():
    scene = PerceptionEngine().perceive([[1], [0], [2]])

    assert "above" in relation_names(scene)


def test_below():
    scene = PerceptionEngine().perceive([[1], [0], [2]])

    assert "below" in relation_names(scene)


def test_touching():
    scene = PerceptionEngine().perceive([[1, 2]])

    assert "touching" in relation_names(scene)


def test_adjacent():
    scene = PerceptionEngine().perceive([[1, 0, 2]])

    assert "adjacent" in relation_names(scene)


def test_same_color():
    scene = PerceptionEngine().perceive([[1, 0, 1]])

    assert "same_color" in relation_names(scene)


def test_same_shape():
    scene = PerceptionEngine().perceive([[1, 0, 2]])

    assert "same_shape" in relation_names(scene)


def test_same_size():
    scene = PerceptionEngine().perceive([[1, 0, 2]])

    assert "same_size" in relation_names(scene)


def test_scene_graph_nodes():
    scene = PerceptionEngine().perceive([[1, 0, 2]])

    assert set(scene["scene_graph"]["nodes"]) == {"obj_1", "obj_2"}


def test_scene_graph_edges():
    scene = PerceptionEngine().perceive([[1, 0, 2]])

    assert scene["scene_graph"]["edges"]
    assert scene["scene_graph"]["edges"][0]["source"] == "obj_1"


def test_object_count_delta():
    comparison = PerceptionEngine().compare_scenes([[1]], [[1, 0, 2]])

    assert comparison["object_count_delta"] == 1
    assert "object_added" in comparison["possible_transformations"]


def test_color_changes():
    comparison = PerceptionEngine().compare_scenes([[1]], [[2]])

    assert comparison["colors_added"] == [2]
    assert comparison["colors_removed"] == [1]
    assert "color_changed" in comparison["possible_transformations"]


def test_movement_hints():
    comparison = PerceptionEngine().compare_scenes(
        [[1, 0, 0]],
        [[0, 1, 0]],
    )

    assert comparison["position_changes"]
    assert "object_moved" in comparison["possible_transformations"]


def test_duplication_hints():
    comparison = PerceptionEngine().compare_scenes(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    assert "duplication_possible" in comparison["possible_transformations"]


def test_json_serializability():
    scene = PerceptionEngine().perceive(np.array([[0, 1], [2, 0]]))

    assert json.loads(json.dumps(scene))["system"] == "perception_engine"
