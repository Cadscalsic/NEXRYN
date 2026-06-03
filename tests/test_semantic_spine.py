from core.cognition.semantic_field_dynamics import (
    SemanticFieldDynamics,
)
from core.cognition.semantic_spine import (
    SemanticSpine,
)


def test_field_dynamics_exports_tensor_and_attractor_basin():

    context = {
        "identity_continuity": 0.54,
        "stability_field_report": {
            "semantic_drift": {
                "semantic_drift": 0.7559,
            },
        },
        "semantic_physics_report": {
            "semantic_gravity": {
                "gravity_strength": 0.46,
                "gravity_wells": [
                    "object_identity_preservation",
                ],
            },
            "entropy_diffusion": {
                "runtime_entropy": 0.8,
            },
            "identity_inertia": {
                "identity_inertia": 0.42,
            },
            "cognitive_mass": {
                "average_cognitive_mass": 0.5,
            },
            "semantic_orbital_stability": {
                "orbital_score": 0.4,
            },
        },
    }

    report = SemanticFieldDynamics().run_cycle(
        context,
    )

    assert "identity_tensor_continuity" in report
    assert "attractor_basin_stabilization" in report

    assert report[
        "identity_tensor_continuity"
    ][
        "tensor_continuity_state"
    ] == "identity_tensor_tearing"

    assert report[
        "attractor_basin_stabilization"
    ][
        "basin_state"
    ] == "basin_stabilization_required"


def test_semantic_spine_requests_repair_under_high_drift():

    context = {
        "semantic_field_dynamics_report": {
            "semantic_gravity_fields": {
                "field_pull": 0.3,
                "anchor_targets": [
                    "object_identity_preservation",
                ],
                "gravity_field_state": "anchor_field_weak",
            },
            "identity_tensor_continuity": {
                "tensor_continuity": 0.38,
                "tensor_continuity_state": "identity_tensor_tearing",
            },
            "drift_diffusion_equations": {
                "diffusion_rate": 0.69,
            },
            "topological_semantic_elasticity": {
                "elasticity": 0.37,
                "adaptation_without_collapse": False,
                "elasticity_state": "topological_elasticity_brittle",
            },
            "attractor_basin_stabilization": {
                "basin_strength": 0.35,
                "attractor_targets": [
                    "object_identity_preservation",
                ],
                "basin_state": "basin_stabilization_required",
            },
            "entropy_cooling_mechanics": {
                "cooling_intensity": 0.72,
                "projected_entropy": 0.63,
            },
        },
    }

    report = SemanticSpine().run_cycle(
        context,
    )

    assert report[
        "semantic_spine_state"
    ] == "semantic_spine_repairing"

    assert report[
        "spine_policy"
    ] == "repair_semantic_spine_before_governance_expansion"


def test_semantic_spine_requires_confirmed_recovery_cycles():

    spine = SemanticSpine()

    spine.regulate_recovery(
        True,
    )

    first = spine.regulate_recovery(
        False,
    )

    second = spine.regulate_recovery(
        False,
    )

    third = spine.regulate_recovery(
        False,
    )

    assert first["semantic_spine_state"] == "semantic_spine_recovering"
    assert second["semantic_spine_state"] == "semantic_spine_recovering"
    assert third["semantic_spine_state"] == "semantic_spine_stable"
