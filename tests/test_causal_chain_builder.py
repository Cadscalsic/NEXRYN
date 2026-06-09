from core.causal import CausalChainBuilder, CausalGraph


def test_causal_chain_builder_generates_direct_indirect_and_branching_chains():
    graph = CausalGraph()
    for node in ["duplication", "object_count_increase", "identity_split"]:
        graph.add_node(node_id=node, node_type="event", name=node, confidence=0.9)
    graph.add_edge(source="duplication", target="object_count_increase", relation_type="causes", confidence=0.9, weight=0.9)
    graph.add_edge(source="object_count_increase", target="identity_split", relation_type="causes", confidence=0.85, weight=0.85)
    graph.add_edge(source="duplication", target="identity_split", relation_type="may_cause" if False else "causes", confidence=0.6, weight=0.6)

    report = CausalChainBuilder().build(
        graph,
        sources=["duplication"],
        targets=["identity_split"],
    )

    assert report["direct_chains"]
    assert report["indirect_chains"]
    assert report["branching_chains"][0]["source"] == "duplication"
