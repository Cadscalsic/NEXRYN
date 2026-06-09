from core.causal import CausalGraph, DependencyTracker


def test_graph_node_creation():
    graph = CausalGraph()

    node = graph.add_node(
        node_id="concept:color_preservation",
        node_type="concept",
        name="color_preservation",
        confidence=0.9,
        metadata={"source": "test"},
        evidence_count=2,
    )

    assert node.node_id == "concept:color_preservation"
    assert node.node_type == "concept"
    assert node.confidence == 0.9
    assert graph.export_graph()["nodes"][0]["evidence_count"] == 2


def test_graph_edge_creation():
    graph = CausalGraph()
    graph.ensure_context("color_behavior", "unchanged")
    graph.ensure_concept("color_preservation")

    edge = graph.add_edge(
        source="context:color_behavior:unchanged",
        target="concept:color_preservation",
        relation_type="supports",
        weight=0.8,
        confidence=0.9,
        evidence=[{"task": "task_a"}],
    )

    assert edge.relation_type == "supports"
    assert edge.weight == 0.8
    assert edge.confidence == 0.9
    assert graph.incoming("concept:color_preservation")[0] is edge


def test_dependency_tracking_handles_context_dependent_truth():
    graph = CausalGraph()
    tracker = DependencyTracker()

    dependencies = tracker.attach_dependencies(
        graph,
        "color_preservation",
        {"color_behavior": "color_reassigned"},
    )

    assert dependencies[0]["requires_review"] is True
    assert dependencies[0]["supported"] is False
    assert dependencies[0]["relation"] == "context_requires"
    assert graph.incoming(
        "concept:color_preservation",
        relation_type="context_requires",
    )
