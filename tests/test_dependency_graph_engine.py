from core.causal.dependency_graph_engine import DependencyGraphEngine


def test_dependency_graph_engine_validates_reinforced_dependencies(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )
    dependencies = [
        {
            "source": "symmetry_reasoning",
            "target": "symmetry_evidence",
            "relation": "depends_on",
            "confidence": 0.90,
            "dependency_type": "semantic_dependency",
            "required": True,
            "supported": True,
            "transfer_success": True,
        },
        {
            "source": "symmetry_reasoning",
            "target": "axis_detection",
            "relation": "depends_on",
            "confidence": 0.88,
            "dependency_type": "structural_dependency",
            "required": True,
            "supported": True,
            "transfer_success": True,
        },
        {
            "source": "symmetry_reasoning",
            "target": "relational_balance",
            "relation": "depends_on",
            "confidence": 0.86,
            "dependency_type": "semantic_dependency",
            "required": True,
            "supported": True,
            "transfer_success": True,
        },
    ]
    engine.ingest_dependencies(dependencies)
    for _index in range(4):
        for dependency in dependencies:
            engine.add_dependency(**dependency)

    report = engine.validate_dependency_coherence(
        "symmetry_reasoning",
        required_dependencies=[
            "symmetry_evidence",
            "axis_detection",
            "relational_balance",
        ],
    )

    assert report["dependency_coherence"] >= 0.80
    assert report["status"] == "DEPENDENCY_GRAPH_VALIDATED"
    assert report["recommended_action"] == "USE_FOR_TRUTH_PROMOTION"
    assert report["missing_dependencies"] == []


def test_dependency_graph_engine_reports_missing_dependencies(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )
    engine.add_dependency(
        "color_preservation",
        "color_behavior",
        confidence=0.85,
        dependency_type="contextual_dependency",
    )

    report = engine.validate_dependency_coherence(
        "color_preservation",
        required_dependencies=[
            "color_behavior",
            "color_mapping_rule",
            "recolor_condition",
        ],
    )

    assert report["dependency_coherence"] < 0.80
    assert "color_mapping_rule" in report["missing_dependencies"]
    assert report["recommended_action"] == "COLLECT_DEPENDENCY_EVIDENCE"


def test_dependency_graph_engine_persists_graph(tmp_path):
    graph_path = tmp_path / "dependency_graph.json"
    engine = DependencyGraphEngine(graph_path=graph_path)
    engine.add_dependency(
        "duplication",
        "object_count_increase",
        confidence=0.87,
        dependency_type="causal_dependency",
    )

    reloaded = DependencyGraphEngine(graph_path=graph_path)
    paths = reloaded.find_dependency_paths("duplication")

    assert len(reloaded.graph.edges) == 1
    assert paths["best_path"]["nodes"] == [
        "duplication",
        "object_count_increase",
    ]
