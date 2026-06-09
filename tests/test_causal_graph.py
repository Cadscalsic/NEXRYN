from core.causal import CausalGraph


def build_sample_graph():
    graph = CausalGraph()
    graph.add_node(node_id="structural_transformation", node_type="event", name="structural_transformation", confidence=0.9)
    graph.add_node(node_id="duplication", node_type="transformation", name="duplication", confidence=0.9)
    graph.add_node(node_id="object_count_increase", node_type="event", name="object_count_increase", confidence=0.85)
    graph.add_node(node_id="identity_split", node_type="event", name="identity_split", confidence=0.82)
    graph.add_node(node_id="contextual_truth_required", node_type="truth", name="contextual_truth_required", confidence=0.8)
    graph.add_edge(source="structural_transformation", target="duplication", relation_type="causes", confidence=0.9, weight=0.9)
    graph.add_edge(source="duplication", target="object_count_increase", relation_type="causes", confidence=0.86, weight=0.86)
    graph.add_edge(source="object_count_increase", target="identity_split", relation_type="causes", confidence=0.82, weight=0.82)
    graph.add_edge(source="identity_split", target="contextual_truth_required", relation_type="implies", confidence=0.8, weight=0.8)
    return graph


def test_causal_graph_traversal_and_strength():
    graph = build_sample_graph()

    assert graph.find_root_causes("contextual_truth_required")[0]["node_id"] == (
        "structural_transformation"
    )
    assert graph.find_leaf_effects("structural_transformation")[0]["node_id"] == (
        "contextual_truth_required"
    )
    assert graph.detect_cycles() == []
    assert graph.compute_graph_strength() > 0.8


def test_causal_graph_remove_node_and_edge():
    graph = build_sample_graph()

    removed = graph.remove_edge("duplication", "object_count_increase")
    assert len(removed) == 1
    assert graph.find_path("structural_transformation", "contextual_truth_required") == []

    node = graph.remove_node("identity_split")
    assert node.node_id == "identity_split"
    assert "identity_split" not in graph.nodes
