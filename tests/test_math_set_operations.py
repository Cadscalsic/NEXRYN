from core.math_reasoning.set_operations import SetOperationsEngine


def obj(object_id, cells, color=1):
    return {
        "id": object_id,
        "color": color,
        "cells": cells,
    }


def test_union_of_two_cell_sets():
    report = SetOperationsEngine().union(
        {"name": "a_cells", "items": [(0, 0), (0, 1)]},
        {"name": "b_cells", "items": [(0, 1), (1, 1)]},
    )

    assert report["result"] == [[0, 0], [0, 1], [1, 1]]
    assert report["result_size"] == 3


def test_intersection_of_two_color_sets():
    report = SetOperationsEngine().intersection(
        {"name": "input_colors", "items": [0, 1, 2, 3]},
        {"name": "output_colors", "items": [1, 2, 3, 4]},
    )

    assert report["result"] == [1, 2, 3]


def test_difference_between_input_and_output_color_sets():
    report = SetOperationsEngine().difference(
        {"name": "input_colors", "items": [0, 1, 2]},
        {"name": "output_colors", "items": [0, 2, 3]},
    )

    assert report["result"] == [1]


def test_subset_detection():
    engine = SetOperationsEngine()

    assert engine.is_subset({"items": [1, 2]}, {"items": [1, 2, 3]}) is True
    assert engine.compare_sets({"items": [1, 2]}, {"items": [1, 2, 3]})["relation"] == "subset"


def test_superset_detection():
    engine = SetOperationsEngine()

    assert engine.is_superset({"items": [1, 2, 3]}, {"items": [1, 2]}) is True
    assert engine.compare_sets({"items": [1, 2, 3]}, {"items": [1, 2]})["relation"] == "superset"


def test_disjoint_detection():
    engine = SetOperationsEngine()

    assert engine.is_disjoint({"items": [1, 2]}, {"items": [3, 4]}) is True


def test_jaccard_similarity():
    similarity = SetOperationsEngine().jaccard_similarity(
        {"items": [1, 2, 3]},
        {"items": [2, 3, 4]},
    )

    assert similarity == 0.5


def test_object_group_comparison():
    report = SetOperationsEngine().compare_object_groups(
        [obj("object_1", [(0, 0)]), obj("object_2", [(0, 1)])],
        [obj("object_2", [(0, 1)]), obj("object_3", [(0, 2)])],
    )

    assert report["added_items"] == ["object_3"]
    assert report["removed_items"] == ["object_1"]
    assert report["preserved_items"] == ["object_2"]
    assert report["relation"] == "transformed"


def test_added_cell_region_detection():
    report = SetOperationsEngine().compare_input_output_cells(
        [obj("input", [(0, 0)])],
        [obj("output", [(0, 0), (0, 1)])],
    )

    assert report["added_items"] == [[0, 1]]
    assert report["relation"] == "expanded"
    assert report["use_cases"]["added_region"] == [[0, 1]]
    assert report["use_cases"]["replication_candidates"] is True


def test_removed_cell_region_detection():
    report = SetOperationsEngine().compare_input_output_cells(
        [obj("input", [(0, 0), (0, 1)])],
        [obj("output", [(0, 0)])],
    )

    assert report["removed_items"] == [[0, 1]]
    assert report["relation"] == "reduced"
    assert report["use_cases"]["removed_region"] == [[0, 1]]


def test_preserved_cell_region_detection():
    report = SetOperationsEngine().compare_input_output_cells(
        [obj("input", [(0, 0), (0, 1)])],
        [obj("output", [(0, 1), (1, 1)])],
    )

    assert report["preserved_items"] == [[0, 1]]
    assert report["use_cases"]["preserved_region"] == [[0, 1]]


def test_color_preservation_between_input_and_output_grids():
    report = SetOperationsEngine().compare_input_output_colors(
        [[0, 1], [2, 0]],
        [[2, 1], [0, 2]],
    )

    assert report["preserved_items"] == [0, 1, 2]
    assert report["color_preservation"] is True
    assert report["color_change"] is False
