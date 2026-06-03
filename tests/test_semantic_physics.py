from core.cognition.semantic_physics import SemanticPhysics


def test_semantic_physics_stabilizes_anchor_rich_graph():

    context = {
        "identity_continuity": 0.82,
        "runtime_entropy": 0.22,
        "semantic_graph": {
            "concept_nodes": [
                {
                    "concept": "object_identity_preservation",
                    "compressed_concept": "object_identity_preservation",
                    "confidence": 0.96,
                    "category": "stability",
                    "semantic_class": "invariant",
                    "topology_signature": "none",
                },
                {
                    "concept": "shape_preservation",
                    "compressed_concept": "shape_preservation",
                    "confidence": 0.93,
                    "category": "stability",
                    "semantic_class": "invariant",
                    "topology_signature": "none",
                },
                {
                    "concept": "symbolic_remapping",
                    "compressed_concept": "attribute_substitution",
                    "confidence": 0.84,
                    "category": "attribute_causality",
                    "semantic_class": "symbolic",
                    "topology_signature": "none",
                },
            ],
        },
    }

    report = SemanticPhysics().run_cycle(
        context,
    )

    assert report[
        "semantic_gravity"
    ][
        "gravity_state"
    ] == "semantic_gravity_stable"

    assert report[
        "identity_inertia"
    ][
        "inertia_state"
    ] == "identity_inertia_stable"

    assert report[
        "semantic_physics_state"
    ] == "semantic_physics_stable"


def test_semantic_physics_detects_overheated_fragile_identity():

    context = {
        "identity_continuity": 0.42,
        "runtime_entropy": 0.92,
        "semantic_graph": {
            "concept_nodes": [
                {
                    "concept": f"volatile_concept_{index}",
                    "compressed_concept": f"volatile_concept_{index}",
                    "confidence": 0.42,
                    "category": "experimental",
                    "semantic_class": "mutable",
                    "topology_signature": "none",
                }
                for index in range(
                    24,
                )
            ],
        },
    }

    report = SemanticPhysics().run_cycle(
        context,
    )

    assert report[
        "entropy_diffusion"
    ][
        "entropy_diffusion_state"
    ] == "semantic_overheating"

    assert report[
        "identity_inertia"
    ][
        "inertia_state"
    ] == "identity_inertia_fragile"

    assert report[
        "physics_policy"
    ] == "stabilize_before_merge"
