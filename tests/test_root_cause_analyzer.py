from core.causal import CausalGraph, RootCauseAnalyzer


def test_root_cause_analyzer_traces_review_requirement():
    graph = CausalGraph()
    for node in [
        "structural_transformation",
        "duplication",
        "color_reassigned",
        "color_preservation_review_required",
    ]:
        graph.add_node(node_id=node, node_type="event", name=node, confidence=0.9)
    graph.add_edge(source="structural_transformation", target="duplication", relation_type="causes", confidence=0.9, weight=0.9)
    graph.add_edge(source="duplication", target="color_reassigned", relation_type="causes", confidence=0.84, weight=0.84)
    graph.add_edge(source="color_reassigned", target="color_preservation_review_required", relation_type="invalidates", confidence=0.82, weight=0.82)

    report = RootCauseAnalyzer().analyze(
        graph,
        "color_preservation_review_required",
    )

    assert report["root_causes"] == ["structural_transformation"]
    assert report["causal_depth"] == 3
    assert report["confidence"] > 0.8
    assert report["best_causal_chain"][0] == "structural_transformation"
