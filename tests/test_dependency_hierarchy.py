from core.causal import DependencyHierarchy


def test_dependency_hierarchy_tracks_ancestors_and_descendants():
    hierarchy = DependencyHierarchy()
    hierarchy.add_dependency("object_integrity", "shape_preservation")
    hierarchy.add_dependency("scene_integrity", "object_integrity")

    assert hierarchy.ancestors("shape_preservation") == [
        "object_integrity",
        "scene_integrity",
    ]
    assert "shape_preservation" in hierarchy.descendants("scene_integrity")
    assert hierarchy.chain_for("shape_preservation") == [
        "scene_integrity",
        "object_integrity",
        "shape_preservation",
    ]
