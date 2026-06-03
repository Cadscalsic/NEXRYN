from core.cognition.semantic_field_dynamics import SemanticFieldDynamics


def test_semantic_field_dynamics_stabilizes_high_drift():

    context = {
        "stability_field_report": {
            "semantic_drift": {
                "semantic_drift": 0.762,
            },
        },
        "semantic_physics_report": {
            "semantic_gravity": {
                "gravity_strength": 0.41,
                "gravity_wells": [
                    "object_identity_preservation",
                    "shape_preservation",
                ],
            },
            "entropy_diffusion": {
                "runtime_entropy": 0.82,
            },
            "identity_inertia": {
                "identity_inertia": 0.44,
            },
            "cognitive_mass": {
                "average_cognitive_mass": 0.48,
            },
            "semantic_orbital_stability": {
                "orbital_score": 0.39,
            },
        },
    }

    report = SemanticFieldDynamics().run_cycle(
        context,
    )

    assert report[
        "drift_diffusion_equations"
    ][
        "drift_diffusion_state"
    ] == "drift_diffusion_high"

    assert report[
        "entropy_cooling_mechanics"
    ][
        "cooling_policy"
    ] == "progressive_cognitive_cooling"

    assert report[
        "field_policy"
    ] == "stabilize_semantic_field_before_evolution"


def test_semantic_field_dynamics_allows_stable_adaptation():

    context = {
        "stability_field_report": {
            "semantic_drift": {
                "semantic_drift": 0.18,
            },
        },
        "semantic_physics_report": {
            "semantic_gravity": {
                "gravity_strength": 0.76,
                "gravity_wells": [
                    "object_identity_preservation",
                    "topology_preservation",
                ],
            },
            "entropy_diffusion": {
                "runtime_entropy": 0.28,
            },
            "identity_inertia": {
                "identity_inertia": 0.74,
            },
            "cognitive_mass": {
                "average_cognitive_mass": 0.72,
            },
            "semantic_orbital_stability": {
                "orbital_score": 0.68,
            },
        },
    }

    report = SemanticFieldDynamics().run_cycle(
        context,
    )

    assert report[
        "semantic_gravity_fields"
    ][
        "gravity_field_state"
    ] == "anchor_field_holding"

    assert report[
        "topological_semantic_elasticity"
    ][
        "adaptation_without_collapse"
    ] is True

    assert report[
        "semantic_field_state"
    ] == "semantic_field_stable"
