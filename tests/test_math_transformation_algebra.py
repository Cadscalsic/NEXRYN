from core.math_reasoning.transformation_algebra import TransformationAlgebraEngine


def obj(object_id, cells, color=1):
    return {
        "id": object_id,
        "color": color,
        "cells": cells,
    }


def test_identity_operator():
    engine = TransformationAlgebraEngine()
    operator = engine.infer_operator(obj("a", [(0, 0), (0, 1)], 2), obj("a_out", [(0, 0), (0, 1)], 2))

    assert operator["operator"] == "identity"
    assert engine.apply_operator(obj("a", [(0, 0)], 2), operator)["cells"] == [(0, 0)]


def test_translation_inference():
    operator = TransformationAlgebraEngine().infer_operator(
        obj("a", [(0, 0), (0, 1)], 2),
        obj("a_out", [(1, 2), (1, 3)], 2),
    )

    assert operator["operator"] == "translate"
    assert operator["parameters"] == {"delta_col": 2, "delta_row": 1}


def test_recoloring_inference():
    operator = TransformationAlgebraEngine().infer_operator(
        obj("a", [(0, 0), (0, 1)], 2),
        obj("a_out", [(0, 0), (0, 1)], 5),
    )

    assert operator["operator"] == "recolor"
    assert operator["parameters"] == {"from_color": 2, "to_color": 5}


def test_rotation_inference():
    operator = TransformationAlgebraEngine().infer_operator(
        obj("a", [(0, 0), (1, 0), (1, 1)], 2),
        obj("a_out", [(0, 0), (0, 1), (1, 0)], 2),
    )

    assert operator["operator"] == "rotate_90"


def test_flip_inference():
    operator = TransformationAlgebraEngine().infer_operator(
        obj("a", [(0, 0), (0, 2), (1, 1), (1, 2)], 2),
        obj("a_out", [(0, 0), (0, 2), (1, 0), (1, 1)], 2),
    )

    assert operator["operator"] in {"flip_horizontal", "mirror"}


def test_duplicate_detection():
    operator = TransformationAlgebraEngine().infer_operator(None, obj("new", [(0, 0)], 2))

    assert operator["operator"] == "duplicate"
    assert operator["target"] == "new"


def test_erase_detection():
    operator = TransformationAlgebraEngine().infer_operator(obj("old", [(0, 0)], 2), None)

    assert operator["operator"] == "erase"
    assert operator["source"] == "old"


def test_operator_composition():
    engine = TransformationAlgebraEngine()
    composed = engine.compose(
        {"operator": "translate", "parameters": {"delta_row": 1, "delta_col": 0}},
        {"operator": "recolor", "parameters": {"from_color": 2, "to_color": 4}},
    )

    assert composed["operator"] == "compose"
    assert [item["operator"] for item in composed["sequence"]] == ["translate", "recolor"]


def test_operator_inversion():
    inverse = TransformationAlgebraEngine().invert(
        {"operator": "translate", "parameters": {"delta_row": 1, "delta_col": 2}}
    )

    assert inverse["operator"] == "translate"
    assert inverse["parameters"] == {"delta_col": -2, "delta_row": -1}


def test_operator_equivalence():
    engine = TransformationAlgebraEngine()

    assert engine.operators_equivalent(
        {"operator": "translate", "parameters": {"delta_col": 2, "delta_row": 1}},
        {"operator": "translate", "parameters": {"delta_row": 1.0, "delta_col": 2.0}},
    )


def test_transformation_signature():
    report = TransformationAlgebraEngine().transformation_signature(
        [obj("a", [(0, 0)], 2), obj("b", [(1, 1)], 3)],
        [obj("a_out", [(0, 2)], 2), obj("b_out", [(1, 1)], 4)],
    )

    signature = report["transformation_signature"]
    assert report["system"] == "transformation_algebra_engine"
    assert signature["operator_types"] == ["recolor", "translate"]
    assert signature["preserves_shape"] is True
    assert signature["preserves_position"] is False
    assert signature["preserves_color"] is False
    assert signature["changes_object_count"] is False


def test_transformation_explanation():
    explanation = TransformationAlgebraEngine().explain_transformation(
        {"operator": "recolor", "parameters": {"from_color": 2, "to_color": 5}}
    )

    assert explanation["operator"] == "recolor"
    assert "changes from 2 to 5" in explanation["explanation"]


def test_classifies_translation_from_position_change_with_constant_count():
    algebra = TransformationAlgebraEngine().classify_transformation({
        "position_change": True,
        "object_count_constant": True,
    })

    assert algebra["primary_transformation_type"] == "translation"
    assert algebra["invariants"]["preserves_topology"] is True
    assert algebra["invariants"]["forks_identity"] is False
    assert "translation|" in algebra["algebraic_signature"]


def test_classifies_propagation_from_preserved_source_pattern():
    algebra = TransformationAlgebraEngine().classify_transformation({
        "position_change": True,
        "source_pattern_preserved": True,
    })

    assert algebra["primary_transformation_type"] == "propagation"
    assert algebra["invariants"]["preserves_shape"] is True


def test_classifies_replication_from_count_increase_and_identity_forking():
    algebra = TransformationAlgebraEngine().classify_transformation({
        "position_change": True,
        "object_count_increase": True,
        "identity_forking": True,
    })

    assert "replication" in algebra["transformation_types"]
    assert algebra["invariants"]["forks_identity"] is True
    assert algebra["invariants"]["preserves_identity"] is False


def test_classifies_growth_and_topological_growth_without_identity_leakage():
    growth = TransformationAlgebraEngine().classify_transformation({
        "topology_expansion": True,
        "identity_persistence": True,
    })
    topological_growth = TransformationAlgebraEngine().classify_transformation({
        "topology_expansion": True,
        "identity_forking": True,
    })

    assert growth["primary_transformation_type"] == "growth"
    assert growth["invariants"]["preserves_identity"] is True
    assert growth["identity_scope_leakage_detected"] is False
    assert topological_growth["primary_transformation_type"] == "topological_growth"
    assert topological_growth["invariants"]["forks_identity"] is True
