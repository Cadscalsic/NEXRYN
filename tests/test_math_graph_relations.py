from core.math_reasoning.graph_relations import GraphRelationsEngine
from core.math_reasoning.spatial_relations import SpatialRelationsEngine


def obj(object_id, col, color=1):
    return {
        "id": object_id,
        "color": color,
        "cells": [(0, col)],
    }


def one_relation(source, target, relation):
    return {
        "relations": [
            {
                "source": source,
                "target": target,
                "relation": relation,
                "confidence": 1.0,
            }
        ]
    }


def build_manual_graph(objects, relations):
    return GraphRelationsEngine().build_graph(objects, {"relations": relations})


def test_build_graph_from_two_objects_and_one_spatial_relation():
    engine = GraphRelationsEngine()
    graph = engine.build_graph(
        [obj("object_1", 0, color=2), obj("object_2", 2, color=3)],
        one_relation("object_1", "object_2", "left_of"),
    )

    assert graph["system"] == "graph_relations_engine"
    assert graph["node_count"] == 2
    assert graph["edge_count"] == 1
    assert graph["nodes"][0]["attributes"]["color"] == 2
    assert graph["edges"][0]["relation"] == "left_of"
    assert graph["graph_signature"]["relation_types"] == ["left_of"]


def test_detect_connected_components():
    graph = build_manual_graph(
        [obj("a", 0), obj("b", 1), obj("c", 5)],
        [{"source": "a", "target": "b", "relation": "touches"}],
    )

    assert GraphRelationsEngine().connected_components(graph) == [["a", "b"], ["c"]]
    assert graph["graph_signature"]["connected_components"] == 2


def test_detect_neighbors():
    graph = build_manual_graph(
        [obj("a", 0), obj("b", 1), obj("c", 2)],
        [
            {"source": "a", "target": "b", "relation": "left_of"},
            {"source": "c", "target": "a", "relation": "right_of"},
        ],
    )

    assert GraphRelationsEngine().neighbors(graph, "a") == ["b", "c"]


def test_detect_shortest_path():
    graph = build_manual_graph(
        [obj("a", 0), obj("b", 1), obj("c", 2)],
        [
            {"source": "a", "target": "b", "relation": "left_of"},
            {"source": "b", "target": "c", "relation": "left_of"},
        ],
    )
    engine = GraphRelationsEngine()

    assert engine.shortest_path(graph, "a", "c") == ["a", "b", "c"]
    assert [step["relation"] for step in engine.relation_path(graph, "a", "c")] == [
        "left_of",
        "left_of",
    ]


def test_detect_added_node_between_input_and_output_graph():
    engine = GraphRelationsEngine()
    graph_a = build_manual_graph([obj("a", 0)], [])
    graph_b = build_manual_graph(
        [obj("a", 0), obj("b", 2)],
        [{"source": "a", "target": "b", "relation": "left_of"}],
    )

    comparison = engine.compare_graphs(graph_a, graph_b)["comparison"]
    assert comparison["added_nodes"] == ["b"]
    assert comparison["node_count_change"] == 1


def test_detect_removed_node():
    engine = GraphRelationsEngine()
    graph_a = build_manual_graph(
        [obj("a", 0), obj("b", 2)],
        [{"source": "a", "target": "b", "relation": "left_of"}],
    )
    graph_b = build_manual_graph([obj("a", 0)], [])

    comparison = engine.compare_graphs(graph_a, graph_b)["comparison"]
    assert comparison["removed_nodes"] == ["b"]
    assert comparison["node_count_change"] == -1


def test_detect_preserved_edge():
    engine = GraphRelationsEngine()
    graph_a = build_manual_graph(
        [obj("a", 0), obj("b", 2)],
        [{"source": "a", "target": "b", "relation": "left_of"}],
    )
    graph_b = build_manual_graph(
        [obj("a", 0), obj("b", 2)],
        [{"source": "a", "target": "b", "relation": "left_of"}],
    )

    comparison = engine.compare_graphs(graph_a, graph_b)["comparison"]
    assert comparison["preserved_edges"] == [
        {"source": "a", "target": "b", "relation": "left_of", "directed": True}
    ]


def test_detect_changed_relation():
    engine = GraphRelationsEngine()
    graph_a = build_manual_graph(
        [obj("a", 0), obj("b", 2)],
        [{"source": "a", "target": "b", "relation": "left_of"}],
    )
    graph_b = build_manual_graph(
        [obj("a", 0), obj("b", 2)],
        [{"source": "a", "target": "b", "relation": "above"}],
    )

    changes = engine.detect_relation_change(graph_a, graph_b)
    assert changes == [
        {
            "source": "a",
            "target": "b",
            "from_relations": ["left_of"],
            "to_relations": ["above"],
            "removed_relations": ["left_of"],
            "added_relations": ["above"],
        }
    ]


def test_detect_graph_growth():
    engine = GraphRelationsEngine()
    graph_a = build_manual_graph([obj("a", 0)], [])
    graph_b = build_manual_graph(
        [obj("a", 0), obj("b", 1)],
        [{"source": "a", "target": "b", "relation": "touches"}],
    )

    growth = engine.detect_graph_growth(graph_a, graph_b)
    assert growth["grew"] is True
    assert growth["node_growth"] == 1
    assert growth["edge_growth"] == 1


def test_detect_graph_preservation():
    engine = GraphRelationsEngine()
    graph_a = build_manual_graph(
        [obj("a", 0), obj("b", 1)],
        [{"source": "a", "target": "b", "relation": "touches"}],
    )
    graph_b = build_manual_graph(
        [obj("a", 0), obj("b", 1), obj("c", 3)],
        [
            {"source": "a", "target": "b", "relation": "touches"},
            {"source": "b", "target": "c", "relation": "left_of"},
        ],
    )

    preservation = engine.detect_graph_preservation(graph_a, graph_b)
    assert preservation["node_preservation_ratio"] == 1.0
    assert preservation["edge_preservation_ratio"] == 1.0


def test_build_graph_integrates_with_spatial_relations_engine():
    objects = [obj("a", 0), obj("b", 2)]
    spatial_report = SpatialRelationsEngine().analyze(objects)
    graph = GraphRelationsEngine().build_graph(objects, spatial_report)

    assert "left_of" in GraphRelationsEngine().relation_types(graph)
