from core.causal.causal_graph_engine_v2 import CausalGraphEngineV2


def test_causal_graph_engine_v2_validates_required_multi_hop_path(tmp_path):
    engine = CausalGraphEngineV2(
        graph_path=tmp_path / "causal_graph.json",
    )
    engine.add_edge(
        "duplication",
        "structure_preservation",
        confidence=0.89,
        support_count=80,
        stability=0.88,
    )
    engine.add_edge(
        "structure_preservation",
        "shape_preservation",
        confidence=0.90,
        support_count=80,
        stability=0.89,
    )

    report = engine.validate_candidate(
        "shape_preservation",
        required_path=[
            "duplication",
            "structure_preservation",
            "shape_preservation",
        ],
    )
    explanation = engine.generate_explanation(
        "shape_preservation",
        cause="duplication",
    )

    assert report["causal_support"] is True
    assert report["alignment_score"] >= 0.85
    assert report["best_path"]["nodes"] == [
        "duplication",
        "structure_preservation",
        "shape_preservation",
    ]
    assert explanation["why"][-1] == "observed in 80 tasks"


def test_causal_graph_engine_v2_counterfactuals_conflicts_and_persistence(
    tmp_path,
):
    graph_path = tmp_path / "causal_graph.json"
    engine = CausalGraphEngineV2(graph_path=graph_path)
    engine.add_edge(
        "duplication",
        "object_count_increase",
        confidence=0.86,
        support_count=30,
    )
    engine.add_edge(
        "object_count_increase",
        "identity_split",
        confidence=0.82,
        support_count=20,
    )
    engine.add_edge(
        "duplication",
        "NOT object_count_increase",
        confidence=0.70,
    )

    counterfactual = engine.counterfactual_analysis("duplication")
    conflicts = engine.detect_conflicts()
    reloaded = CausalGraphEngineV2(graph_path=graph_path)

    assert counterfactual["counterfactual_impact_score"] > 0.0
    assert "object_count_increase" in (
        counterfactual["causal_support_lost"]
        + counterfactual["causal_support_weakened"]
    )
    assert conflicts["conflict_count"] == 1
    assert len(reloaded.graph.edges) == 3
