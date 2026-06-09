from core.causal import SceneCausalGraphBuilder


def edge_targets(report, source):
    return {
        edge["target"]
        for edge in report["causal_graph"]["edges"]
        if edge["source"] == source
    }


def test_scene_causal_graph_builder_creates_duplication_spine():
    report = SceneCausalGraphBuilder().build_from_grids(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    assert report["operation"] == "duplication"
    assert report["best_causal_chain"] == [
        "shape_preservation",
        "object_identity_preservation",
        "topology_preservation",
        "scene_graph_construction",
        "duplication",
    ]
    assert "object_count_increase" in edge_targets(report, "duplication")
    assert "placement:right" in edge_targets(report, "duplication")
    assert report["causal_graph_alignment_hint"]["alignment_ready"] is True
    assert report["causal_graph_alignment_hint"]["alignment_score"] >= 0.80


def test_scene_causal_graph_builder_orders_duplication_effect_chain():
    report = SceneCausalGraphBuilder().build_from_grids(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    assert report["best_operation_causal_chain"] == [
        "duplication",
        "object_count_increase",
        "identity_split",
        "topology_splitting",
        "shape_preservation",
    ]


def test_scene_causal_graph_builder_creates_expand_object_outcomes():
    report = SceneCausalGraphBuilder().build_from_grids(
        [[1, 0, 0]],
        [[1, 1, 0]],
    )

    assert report["operation"] == "expand_object"
    assert report["best_causal_chain"][-1] == "expand_object"
    assert "object_size_increase" in edge_targets(report, "expand_object")
    assert "boundary_growth" in edge_targets(report, "expand_object")
