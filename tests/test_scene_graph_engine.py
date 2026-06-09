import json

from core.causal.dependency_graph_engine import DependencyGraphEngine
from core.perception import SceneGraphEngine


def test_scene_graph_engine_builds_object_nodes():
    graph = SceneGraphEngine().build_scene_graph([[1, 0, 2]])

    assert graph["system"] == "scene_graph_engine"
    assert set(graph["nodes"]) == {"obj_1", "obj_2"}
    assert graph["summary"]["object_level_ready"] is True


def test_scene_graph_engine_indexes_relations():
    graph = SceneGraphEngine().build_scene_graph([[1, 0, 2]])

    assert "left_of" in graph["relation_index"]
    assert graph["adjacency"]["obj_1"]


def test_scene_graph_engine_reports_central_and_isolated_objects():
    graph = SceneGraphEngine().build_scene_graph([[1, 0, 2]])

    assert graph["summary"]["central_objects"]
    assert graph["summary"]["isolated_objects"] == []


def test_scene_graph_engine_extracts_dependency_evidence():
    graph = SceneGraphEngine().build_scene_graph([[1, 0, 2]])
    targets = {item["target"] for item in graph["dependency_evidence"]}

    assert "object_count:2" in targets
    assert "relation:left_of" in targets
    assert any(target.startswith("shape_signature:") for target in targets)


def test_scene_graph_engine_compares_object_events():
    comparison = SceneGraphEngine().compare_scene_graphs(
        [[1, 0, 0]],
        [[0, 1, 0]],
    )

    events = {event["event"] for event in comparison["object_events"]}

    assert "object_moved" in events
    assert comparison["summary"]["object_count_delta"] == 0


def test_scene_graph_engine_detects_possible_split():
    comparison = SceneGraphEngine().compare_scene_graphs(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    events = {event["event"] for event in comparison["object_events"]}

    assert "object_split_possible" in events
    assert comparison["summary"]["object_count_delta"] == 1


def test_scene_graph_engine_carries_identity_tracking_report():
    comparison = SceneGraphEngine().compare_scene_graphs(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )
    targets = {
        evidence["target"]
        for evidence in comparison["dependency_evidence"]
    }

    assert comparison["identity_report"]["identity_state"] == "IDENTITY_SPLIT"
    assert comparison["summary"]["identity_behavior"] == "identity_split"
    assert "identity_split" in targets
    assert "lineage_continuity" in targets


def test_scene_graph_engine_carries_color_analysis_report():
    comparison = SceneGraphEngine().compare_scene_graphs(
        [[1, 0, 0]],
        [[2, 0, 0]],
    )
    targets = {
        evidence["target"]
        for evidence in comparison["dependency_evidence"]
    }

    assert comparison["color_report"]["color_behavior"] == "color_reassigned"
    assert comparison["summary"]["color_behavior"] == "color_reassigned"
    assert "color_behavior:color_reassigned" in targets
    assert "color_mapping_rule" in targets


def test_scene_graph_engine_output_is_json_serializable():
    graph = SceneGraphEngine().build_scene_graph([[1, 2]])

    assert json.loads(json.dumps(graph))["system"] == "scene_graph_engine"


def test_scene_graph_dependency_evidence_feeds_dependency_graph(tmp_path):
    evidence_report = SceneGraphEngine().build_dependency_evidence(
        [[1, 0, 2]],
        source="duplication",
    )
    dependency_engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )

    dependency_engine.ingest_dependencies(
        evidence_report["dependency_evidence"],
    )
    coherence = dependency_engine.validate_dependency_coherence(
        "duplication",
        required_dependencies=["object_count:2", "relation:left_of"],
    )

    assert coherence["dependency_coherence"] >= 0.80
    assert coherence["missing_dependencies"] == []
