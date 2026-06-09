from core.dependency import DependencyGraphEngine
from core.perception import SceneGraphEngine


def test_object_centric_dependency_graph_ingests_scene_evidence(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )

    report = engine.ingest_scene_graph(
        [[1, 0, 2]],
        source="duplication",
    )
    coherence = engine.validate_dependency_coherence(
        "duplication",
        required_dependencies=["object_count:2", "relation:left_of"],
    )

    assert report["mode"] == "object_centric"
    assert report["ingested_dependencies"] > 0
    assert coherence["dependency_coherence"] >= 0.80
    assert coherence["missing_dependencies"] == []


def test_object_centric_dependency_graph_accepts_scene_graph_dict(tmp_path):
    scene_graph = SceneGraphEngine().build_scene_graph([[1, 0, 2]])
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )

    report = engine.validate_scene_dependency_coherence(
        "color_preservation",
        grid_or_scene_graph=scene_graph,
        required_dependencies=["object_count:2", "relation:same_size"],
    )

    assert report["mode"] == "object_centric"
    assert report["dependency_coherence"] >= 0.80
    assert report["object_level_evidence"] is True


def test_object_centric_dependency_graph_ingests_split_events(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )

    report = engine.ingest_scene_comparison(
        [[1, 0, 0]],
        [[1, 0, 1]],
        source="duplication",
    )
    coherence = engine.validate_dependency_coherence(
        "duplication",
        required_dependencies=["object_event:object_split_possible"],
    )

    event_names = {event["event"] for event in report["object_events"]}

    assert "object_split_possible" in event_names
    assert coherence["dependency_coherence"] >= 0.80


def test_object_centric_dependency_graph_ingests_identity_tracking(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )

    report = engine.build_identity_dependency_report(
        [[1, 0, 0]],
        [[1, 0, 1]],
        required_dependencies=[
            "identity_behavior:identity_split",
            "identity_split",
            "lineage_continuity",
        ],
    )

    targets = {
        item["target"]
        for item in report["ingest"]["dependency_evidence"]
    }

    assert report["mode"] == "identity_tracking"
    assert "identity_split" in targets
    assert "lineage_continuity" in targets
    assert report["coherence"]["dependency_coherence"] >= 0.80
    assert report["coherence"]["missing_dependencies"] == []


def test_object_centric_dependency_graph_ingests_color_analysis(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )

    report = engine.build_color_dependency_report(
        [[1, 0, 0]],
        [[2, 0, 0]],
        required_dependencies=[
            "color_behavior:color_reassigned",
            "color_mapping_rule",
            "recolor_condition",
        ],
    )

    targets = {
        item["target"]
        for item in report["ingest"]["dependency_evidence"]
    }

    assert report["mode"] == "color_analysis"
    assert "color_behavior:color_reassigned" in targets
    assert "color_mapping_rule" in targets
    assert "recolor_condition" in targets
    assert report["coherence"]["dependency_coherence"] >= 0.80
    assert report["coherence"]["missing_dependencies"] == []


def test_object_centric_dependency_graph_builds_ordered_chain(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )

    report = engine.build_dependency_chain_report(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    assert report["dependency_chain"] == [
        "duplication",
        "identity_split",
        "object_count_increase",
        "topology_splitting",
    ]
    assert report["chain_complete"] is True
    assert report["paths"]["best_path"]["nodes"] == report["dependency_chain"]
    assert report["coherence"]["dependency_coherence"] >= 0.80


def test_object_centric_dependency_graph_ingests_placement_reasoning(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )

    report = engine.build_placement_dependency_report(
        [[1, 0, 0]],
        [[1, 0, 1]],
        source="duplicate_object",
        position_rule={
            "operation": "duplicate_object",
            "source_object": "obj_1",
            "placement_vector": {"delta_row": 0, "delta_col": 1},
            "confidence": 0.72,
        },
        required_dependencies=[
            "placement:right",
            "failure_cause:localized_prediction_mismatch",
            "counterfactual:localized_mismatch_resolved",
            "operation:duplicate_object",
        ],
    )

    targets = {
        item["target"]
        for item in report["ingest"]["dependency_evidence"]
    }

    assert report["mode"] == "placement_reasoning"
    assert "placement:right" in targets
    assert "failure_cause:localized_prediction_mismatch" in targets
    assert "counterfactual:localized_mismatch_resolved" in targets
    assert report["coherence"]["dependency_coherence"] >= 0.80
    assert report["coherence"]["missing_dependencies"] == []
