from core.dependency import DependencyGraphBuilder


def test_dependency_graph_builder_orders_duplication_chain():
    report = DependencyGraphBuilder().build_from_grids(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    assert report["operation"] == "duplication"
    assert report["identity_continuity_report"]["continuity_state"] == (
        "OBJECT_IDENTITY_SPLIT"
    )
    assert report["dependency_chain"] == [
        "duplication",
        "identity_split",
        "object_count_increase",
        "topology_splitting",
    ]
    assert report["chain_complete"] is True
    assert [
        (item["source"], item["target"])
        for item in report["dependency_evidence"]
        if item["dependency_type"] == "causal_dependency"
    ] == [
        ("duplication", "identity_split"),
        ("identity_split", "object_count_increase"),
        ("object_count_increase", "topology_splitting"),
    ]


def test_dependency_graph_builder_adds_color_reassignment_when_present():
    report = DependencyGraphBuilder().build_from_grids(
        [[1, 0, 0]],
        [[2, 0, 2]],
    )

    assert report["dependency_chain"] == [
        "duplication",
        "identity_split",
        "object_count_increase",
        "topology_splitting",
        "color_reassigned",
    ]
    assert report["color_report"]["color_behavior"] == "color_reassigned"
    assert report["object_identities"]
    assert any(
        item["target"] == "object_continuity:OBJECT_IDENTITY_SPLIT"
        for item in report["dependency_evidence"]
    )


def test_dependency_graph_builder_orders_merge_chain():
    report = DependencyGraphBuilder().build_from_grids(
        [[1, 0, 1]],
        [[1]],
    )

    assert report["operation"] == "object_convergence"
    assert report["dependency_chain"] == [
        "object_convergence",
        "identity_merged",
        "object_count_decrease",
        "topology_compaction",
    ]
    assert report["object_scene_graph"]["summary"]["has_identity_merge"] is True
    assert report["identity_continuity_report"]["identity_merged"] is True


def test_dependency_graph_builder_orders_creation_chain():
    report = DependencyGraphBuilder().build_from_grids(
        [],
        [[1]],
    )

    assert report["operation"] == "object_appearance"
    assert report["dependency_chain"] == [
        "object_appearance",
        "identity_created",
        "object_count_increase",
        "scene_expansion",
    ]
    assert report["identity_continuity_report"]["identity_created"] is True


def test_dependency_graph_builder_orders_destruction_chain():
    report = DependencyGraphBuilder().build_from_grids(
        [[1]],
        [],
    )

    assert report["operation"] == "object_disappearance"
    assert report["dependency_chain"] == [
        "object_disappearance",
        "identity_destroyed",
        "object_count_decrease",
        "scene_contraction",
    ]
    assert report["identity_continuity_report"]["identity_destroyed"] is True


def test_dependency_graph_builder_adds_preservation_change_for_recolor():
    report = DependencyGraphBuilder().build_from_grids(
        [[1]],
        [[2]],
        source="attribute_transformation",
    )

    assert report["dependency_chain"] == [
        "attribute_transformation",
        "identity_preserved",
        "attribute_or_position_change",
        "color_reassigned",
    ]
