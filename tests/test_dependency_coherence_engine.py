from core.causal import CausalGraph, DependencyCoherenceEngine


def test_dependency_coherence_engine_validates_strong_dependencies():
    graph = CausalGraph()
    graph.ensure_context("color_behavior", "unchanged")
    graph.ensure_concept("color_preservation")
    graph.add_edge(
        source="context:color_behavior:unchanged",
        target="concept:color_preservation",
        relation_type="depends_on",
        confidence=0.9,
        weight=0.9,
    )

    report = DependencyCoherenceEngine().evaluate(
        dependencies=[{
            "dependency": "color_behavior",
            "supported": True,
            "requires_review": False,
            "context_value": "unchanged",
        }],
        graph=graph,
        concept="color_preservation",
    )

    assert report["dependency_coherence"] > 0.8
    assert report["dependency_risk"] == "LOW"
    assert report["recommended_action"] == "USE_FOR_TRUTH_PROMOTION"


def test_dependency_coherence_engine_identifies_missing_links():
    report = DependencyCoherenceEngine().evaluate(
        dependencies=[{
            "dependency": "topology_behavior",
            "supported": False,
            "requires_review": True,
            "context_value": None,
        }],
        concept="topology_preservation",
    )

    assert report["dependency_coherence"] < 0.8
    assert report["dependency_risk"] == "HIGH"
    assert report["recommended_action"] == "COLLECT_EVIDENCE"
    assert report["missing_dependencies"]


def test_dependency_coherence_engine_rewards_typed_process_semantics():
    report = DependencyCoherenceEngine().evaluate(
        dependencies=[
            {
                "dependency": "object_identity_preservation",
                "relation": "requires",
                "supported": True,
                "requires_review": False,
                "context_value": "validated",
                "confidence": 0.91,
            },
            {
                "dependency": "topology_expansion",
                "relation": "creates",
                "supported": True,
                "requires_review": False,
                "context_value": "observed",
                "confidence": 0.90,
            },
            {
                "dependency": "shape_preservation",
                "relation": "preserves",
                "supported": True,
                "requires_review": False,
                "context_value": "stable",
                "confidence": 0.89,
            },
        ],
        concept="growth",
    )

    assert report["dependency_coherence"] >= 0.80
    assert report["relation_semantics_score"] >= 0.95
    assert report["coherence_ready"] is True


def test_dependency_coherence_engine_keeps_generic_edges_weaker():
    report = DependencyCoherenceEngine().evaluate(
        dependencies=[
            {
                "dependency": "object_identity_preservation",
                "relation": "supports",
                "supported": True,
                "requires_review": False,
                "context_value": "observed",
                "confidence": 0.68,
            },
            {
                "dependency": "topology_expansion",
                "supported": True,
                "requires_review": False,
                "context_value": "observed",
                "confidence": 0.66,
            },
        ],
        concept="growth",
    )

    assert report["dependency_coherence"] < 0.80
    assert report["coherence_ready"] is False
