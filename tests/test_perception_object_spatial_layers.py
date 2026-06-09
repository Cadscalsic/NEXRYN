from core.perception import (
    ColorAnalyzer,
    IdentityTracker,
    ObjectExtractor,
    SceneGraphEngine,
    ShapeAnalyzer,
    SpatialRelationEngine,
)


def test_object_extractor_returns_shape_analysis():
    objects = ObjectExtractor().extract_objects([
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ])

    assert len(objects) == 1
    assert objects[0]["holes"] == 1
    assert objects[0]["shape_analysis"]["density"] < 1.0
    assert objects[0]["canonical_shape_signature"]


def test_shape_analyzer_canonical_signature_is_translation_stable():
    analyzer = ShapeAnalyzer()

    first = analyzer.canonical_signature([(0, 0), (0, 1), (1, 0)])
    shifted = analyzer.canonical_signature([(4, 5), (4, 6), (5, 5)])

    assert first == shifted


def test_spatial_relation_engine_reports_placement_vector():
    objects = ObjectExtractor().extract_objects([[1, 0, 1]])
    vector = SpatialRelationEngine().placement_vector(objects[0], objects[1])

    assert vector["delta_row"] == 0.0
    assert vector["delta_col"] == 2.0
    assert vector["axis"] == "horizontal"
    assert vector["direction"] == "right"


def test_scene_graph_added_object_carries_source_and_placement():
    comparison = SceneGraphEngine().compare_scene_graphs(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )
    added = [
        event
        for event in comparison["object_events"]
        if event["event"] == "object_added"
    ][0]

    assert added["source_candidate"] == "obj_1"
    assert added["placement_vector"]["delta_col"] == 2.0
    assert added["placement_vector"]["direction"] == "right"


def test_identity_tracker_reports_duplication_as_identity_split():
    report = IdentityTracker().track_identity(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    targets = {
        evidence["target"]
        for evidence in report["dependency_evidence"]
    }

    assert report["identity_state"] == "IDENTITY_SPLIT"
    assert report["identity_behavior"] == "identity_split"
    assert report["split_events"][0]["input_object"] == "obj_1"
    assert "identity_split" in targets
    assert "lineage_continuity" in targets
    assert any(target.startswith("identity_runtime:") for target in targets)
    assert "identity_runtime_gate:identity_continuity_above_limit" in targets


def test_color_analyzer_reports_recolor_mapping():
    report = ColorAnalyzer().compare_grids(
        [[1, 0, 0]],
        [[2, 0, 0]],
    )
    targets = {
        evidence["target"]
        for evidence in report["dependency_evidence"]
    }

    assert report["color_behavior"] == "color_reassigned"
    assert report["color_mappings"][0]["mapping"] == "1->2"
    assert "color_behavior:color_reassigned" in targets
    assert "color_mapping_rule" in targets
    assert "recolor_condition" in targets
