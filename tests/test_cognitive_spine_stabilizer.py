from core.civilization.identity_continuity_engine import (
    IdentityContinuityEngine,
)
from core.identity.cognitive_spine_stabilizer import (
    CognitiveSpineStabilizer,
)


def test_cognitive_spine_stabilizer_detects_fragile_spine():

    context = {
        "semantic_anchor_graph_report": {
            "anchor_strength": 0.31,
        },
        "identity_continuity": 0.58,
        "stability_field_report": {
            "semantic_drift": {
                "semantic_drift": 0.762,
            },
        },
        "semantic_field_dynamics_report": {
            "semantic_gravity_fields": {
                "field_pull": 0.22,
            },
            "topological_semantic_elasticity": {
                "elasticity": 0.31,
            },
            "semantic_inertia_tensors": {
                "inertia_tensor_strength": 0.29,
            },
            "field_policy": "stabilize_semantic_field_before_evolution",
        },
    }

    report = CognitiveSpineStabilizer().run_cycle(
        context,
    )

    assert report[
        "cognitive_spine_state"
    ] == "cognitive_spine_fragile"

    assert "rebuild_semantic_anchor_graph" in report[
        "spine_repair_protocol"
    ][
        "repair_actions"
    ]

    assert "restore_causal_identity_ligaments" in report[
        "spine_repair_protocol"
    ][
        "repair_actions"
    ]


def test_identity_continuity_engine_uses_spine_stabilizer():

    context = {
        "semantic_anchor_graph_report": {
            "anchor_strength": 0.5,
        },
        "cognitive_spine_stabilizer_report": {
            "spine_stability": 0.64,
            "anchor_reinforcement": {
                "reinforced_anchor_strength": 0.62,
            },
        },
        "identity_continuity_guardian_report": {
            "catastrophic_rewrite_guard": {
                "block_rewrite": False,
            },
        },
        "stability_field_report": {
            "identity_fragmentation": {
                "fragmentation_detected": False,
            },
            "semantic_drift": {
                "semantic_drift": 0.18,
            },
        },
    }

    report = IdentityContinuityEngine().run_cycle(
        context,
    )

    assert report[
        "cognitive_spine"
    ][
        "spine_state"
    ] == "cognitive_spine_protected"

    assert report[
        "identity_continuity_state"
    ] == "identity_continuity_stable"
