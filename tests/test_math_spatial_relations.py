from core.math_reasoning.spatial_relations import SpatialRelationsEngine


def obj(object_id, cells, color=1):
    return {
        "id": object_id,
        "color": color,
        "cells": cells,
    }


def relation_names(report, source, target):
    return {
        relation["relation"]
        for relation in report["relations"]
        if relation["source"] == source and relation["target"] == target
    }


def test_object_a_left_of_object_b():
    report = SpatialRelationsEngine().analyze([
        obj("a", [(1, 1)]),
        obj("b", [(1, 3)]),
    ])

    assert "left_of" in relation_names(report, "a", "b")
    assert "right_of" in relation_names(report, "b", "a")


def test_object_a_above_object_b():
    report = SpatialRelationsEngine().analyze([
        obj("a", [(1, 1)]),
        obj("b", [(3, 1)]),
    ])

    assert "above" in relation_names(report, "a", "b")
    assert "below" in relation_names(report, "b", "a")


def test_two_objects_aligned_in_same_row():
    report = SpatialRelationsEngine().analyze([
        obj("a", [(2, 1)]),
        obj("b", [(2, 4)]),
    ])

    assert "aligned_row" in relation_names(report, "a", "b")
    assert report["spatial_signature"]["alignment_patterns"][0]["relation"] == "aligned_row"


def test_two_objects_aligned_in_same_column():
    report = SpatialRelationsEngine().analyze([
        obj("a", [(1, 5)]),
        obj("b", [(4, 5)]),
    ])

    assert "aligned_column" in relation_names(report, "a", "b")
    assert report["spatial_signature"]["alignment_patterns"][0]["relation"] == "aligned_column"


def test_two_objects_touching():
    report = SpatialRelationsEngine().analyze([
        obj("a", [(1, 1)]),
        obj("b", [(1, 2)]),
    ])

    assert "touches" in relation_names(report, "a", "b")
    assert "adjacent_to" in relation_names(report, "a", "b")


def test_two_objects_overlapping():
    report = SpatialRelationsEngine().analyze([
        obj("a", [(1, 1), (1, 2)]),
        obj("b", [(1, 2), (1, 3)]),
    ])

    assert "overlaps" in relation_names(report, "a", "b")


def test_one_object_inside_another_bounding_box():
    report = SpatialRelationsEngine().analyze([
        obj("outer", [(0, 0), (0, 3), (3, 0), (3, 3)]),
        obj("inner", [(1, 1), (1, 2), (2, 1), (2, 2)]),
    ])

    assert "contains" in relation_names(report, "outer", "inner")
    assert "inside" in relation_names(report, "inner", "outer")


def test_shifted_by_relation_between_input_and_output_objects():
    report = SpatialRelationsEngine().analyze([
        obj("input_object", [(1, 1), (1, 2), (2, 1)]),
        obj("output_object", [(3, 4), (3, 5), (4, 4)]),
    ])

    shifted = [
        relation
        for relation in report["relations"]
        if relation["source"] == "input_object"
        and relation["target"] == "output_object"
        and relation["relation"] == "shifted_by"
    ][0]
    assert shifted["evidence"]["shift"] == {"delta_row": 2.0, "delta_col": 3.0}


def test_analyze_grid_uses_existing_arc_object_extractor():
    report = SpatialRelationsEngine().analyze_grid([[1, 0, 2]])

    assert report["objects_analyzed"] == 2
    assert "left_of" in relation_names(report, "obj_1", "obj_2")
