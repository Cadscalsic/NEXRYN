from core.causal import CausalGraph, MultiHopReasoner


def test_multi_hop_reasoner_discovers_ranked_causal_chain():
    graph = CausalGraph()
    for node in [
        "duplication",
        "object_count_increase",
        "identity_split",
        "topology_splitting",
        "contextual_truth_required",
    ]:
        graph.add_node(node_id=node, node_type="event", name=node, confidence=0.9)
    graph.add_edge(source="duplication", target="object_count_increase", relation_type="causes", confidence=0.9, weight=0.9)
    graph.add_edge(source="object_count_increase", target="identity_split", relation_type="causes", confidence=0.85, weight=0.85)
    graph.add_edge(source="identity_split", target="topology_splitting", relation_type="causes", confidence=0.82, weight=0.82)
    graph.add_edge(source="topology_splitting", target="contextual_truth_required", relation_type="implies", confidence=0.8, weight=0.8)

    report = MultiHopReasoner().discover(
        graph,
        "duplication",
        "contextual_truth_required",
    )

    assert report["root_cause"] == "duplication"
    assert report["depth"] == 4
    assert report["path_strength"] > 0.8
    assert report["path_confidence"] > 0.8
    assert report["causal_chain"][-1] == "contextual_truth_required"
