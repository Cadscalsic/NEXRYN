from core.perception import IdentityTransitionKind, ObjectTracker
from core.scene_graph import GraphReasoner, RelationExtractor, SceneGraphBuilder
from core.world_model import PlacementReasoner


def test_object_tracker_localizes_added_duplicate():
    tracking = ObjectTracker().track(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    added = tracking["added_objects"][0]

    assert tracking["localized_change_count"] == 1
    assert added["event"] == "object_added"
    assert added["source_candidate"] == "obj_1"
    assert added["placement_vector"]["delta_col"] == 2.0


def test_object_tracker_preserves_identity_through_color_change():
    tracking = ObjectTracker().track(
        [[1, 0, 0]],
        [[2, 0, 0]],
    )

    match = tracking["matches"][0]

    assert tracking["identity_continuity_state"] == "IDENTITY_CONTINUITY_STABLE"
    assert match["identity_state"] == "identity_preserved_color_changed"
    assert match["color_changed"] is True
    assert tracking["removed_objects"] == []
    assert tracking["added_objects"] == []
    assert tracking["identity_runtime_state"] == "IDENTITY_RUNTIME_STABLE"
    assert tracking["identity_runtime_gates"]["identity_stable"] is True
    assert tracking["identity_runtime_gates"]["semantic_spine_stable"] is True
    assert tracking["identity_runtime"]["tracks"][0]["stable"] is True
    assert tracking["input_tracked_objects"][0]["object_id"] == "obj_1"
    assert tracking["output_tracked_objects"][0]["color"] == 2
    assert tracking["identity_transitions"][0]["source"] == "obj_1"
    assert tracking["identity_transitions"][0]["target"] == "obj_1"
    assert tracking["identity_transitions"][0]["transition_type"] == "color_changed"
    assert tracking["identity_transitions"][0]["transition_kind"] == (
        IdentityTransitionKind.PRESERVED.value
    )
    assert tracking["object_identities"][0]["source_id"] == "obj_1"
    assert tracking["object_identities"][0]["target_id"] == "obj_1"
    assert tracking["object_identities"][0]["transition"] == "color_changed"
    assert tracking["object_identities"][0]["identity_transition"] == (
        IdentityTransitionKind.PRESERVED.value
    )
    assert tracking["object_identities"][0]["continuity_score"] >= 0.80


def test_object_tracker_marks_split_runtime_as_provisional():
    tracking = ObjectTracker().track(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    gates = tracking["identity_runtime_gates"]

    assert tracking["identity_runtime_state"] == "IDENTITY_RUNTIME_PROVISIONAL"
    assert gates["identity_continuity_above_limit"] is True
    assert gates["identity_stable"] is False
    assert tracking["identity_runtime"]["untracked_output_count"] == 1
    split_transition = [
        transition
        for transition in tracking["identity_transitions"]
        if transition["transition_type"] == "identity_split"
    ][0]
    split_identity = [
        identity
        for identity in tracking["object_identities"]
        if identity["transition"] == "identity_split"
    ][0]
    assert split_transition["source"] == "obj_1"
    assert split_transition["targets"] == ["obj_1", "obj_2"]
    assert split_transition["identity_transition"] == IdentityTransitionKind.SPLIT.value
    assert split_identity["source_id"] == "obj_1"
    assert split_identity["targets"] == ["obj_1", "obj_2"]
    assert split_identity["transition_kind"] == IdentityTransitionKind.SPLIT.value
    assert split_identity["continuity_score"] >= 0.80


def test_object_tracker_marks_created_identity():
    tracking = ObjectTracker().track(
        [],
        [[1]],
    )

    created = tracking["identity_transitions"][0]

    assert created["transition_type"] == "created"
    assert created["target"] == "obj_1"
    assert created["identity_transition"] == IdentityTransitionKind.CREATED.value
    assert tracking["added_objects"][0]["identity_transition"] == (
        IdentityTransitionKind.CREATED.value
    )


def test_object_tracker_marks_destroyed_identity():
    tracking = ObjectTracker().track(
        [[1]],
        [],
    )

    destroyed = tracking["identity_transitions"][0]

    assert destroyed["transition_type"] == "removed"
    assert destroyed["source"] == "obj_1"
    assert destroyed["identity_transition"] == IdentityTransitionKind.DESTROYED.value
    assert tracking["removed_objects"][0]["identity_transition"] == (
        IdentityTransitionKind.DESTROYED.value
    )


def test_object_tracker_marks_merged_identity():
    tracking = ObjectTracker().track(
        [[1, 0, 1]],
        [[1]],
    )

    merged = [
        transition
        for transition in tracking["identity_transitions"]
        if transition["identity_transition"] == IdentityTransitionKind.MERGED.value
    ][0]

    assert merged["transition_type"] == "identity_merged"
    assert merged["target"] == "obj_1"
    assert set(merged["evidence"]["sources"]) == {"obj_1", "obj_2"}
    assert tracking["removed_objects"][0]["identity_transition"] == (
        IdentityTransitionKind.MERGED.value
    )


def test_object_tracker_preserves_identity_through_size_growth():
    tracking = ObjectTracker().track(
        [[1, 0, 0]],
        [[1, 1, 0]],
    )

    match = tracking["matches"][0]

    assert tracking["identity_continuity"] >= 0.68
    assert match["identity_state"] == "identity_preserved_size_changed"
    assert match["size_changed"] is True
    assert tracking["removed_objects"] == []


def test_scene_graph_builder_indexes_spatial_relations():
    extracted = RelationExtractor().extract_from_grid([[1, 0, 1]])
    graph = SceneGraphBuilder().build_from_objects(
        extracted["objects"],
        extracted["relations"],
    )

    assert graph["summary"]["object_count"] == 2
    assert graph["summary"]["has_spatial_relations"] is True
    assert "left_of" in graph["relation_index"]
    assert "same_canonical_shape" in graph["relation_index"]


def test_scene_graph_builder_indexes_identity_split_relations():
    graph = SceneGraphBuilder().build_comparison(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    assert graph["summary"]["has_identity_split"] is True
    assert "identity_split" in graph["relation_index"]
    assert "IdentitySplit" in graph["identity_transition_index"]
    assert {
        "subject": "obj_1",
        "predicate": "identity_split",
        "object": "obj_1",
        "confidence": graph["relation_index"]["identity_split"][0]["confidence"],
        "evidence_type": "object_identity_transition",
    } in graph["relation_triples"]
    assert graph["object_identities"][0]["source_id"] == "obj_1"


def test_scene_graph_builder_indexes_identity_merge_kind():
    graph = SceneGraphBuilder().build_comparison(
        [[1, 0, 1]],
        [[1]],
    )

    assert graph["summary"]["has_identity_merge"] is True
    assert "IdentityMerged" in graph["identity_transition_index"]


def test_graph_reasoner_emits_placement_dependency_evidence():
    report = GraphReasoner().reason_about_placement(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    targets = {
        evidence["target"]
        for evidence in report["dependency_evidence"]
    }

    assert report["localized_prediction_ready"] is True
    assert "placement:right" in targets
    assert "scene_graph_alignment" in targets


def test_graph_reasoner_emits_identity_continuity_dependency_evidence():
    report = GraphReasoner().reason_about_placement(
        [[1, 0, 0]],
        [[1, 1, 0]],
        operation="expand_object",
    )

    targets = {
        evidence["target"]
        for evidence in report["dependency_evidence"]
    }

    assert any(target.startswith("identity_continuity:") for target in targets)



def test_placement_reasoner_repairs_localized_mismatch():
    report = PlacementReasoner().reason(
        [[1, 0, 0]],
        [[1, 0, 1]],
        position_rule={
            "operation": "duplicate_object",
            "source_object": "obj_1",
            "placement_vector": {"delta_row": 0, "delta_col": 1},
            "confidence": 0.72,
        },
        search_radius=1,
    )

    assert report["position_mismatch"]["failure_type"] == (
        "localized_prediction_mismatch"
    )
    assert report["placement_state"] == "PLACEMENT_REPAIRED_BY_COUNTERFACTUAL"
    assert report["recommended_position_rule"]["placement_vector"]["delta_col"] == 2
