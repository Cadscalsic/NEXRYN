from core.adaptive_equilibrium import (
    adaptive_equilibrium_architecture,
)


def test_adaptive_equilibrium_balances_recovery_with_bounded_adaptation():

    context = {
        "existential_pressure_report":
        {
            "managed_pressure": 0.54,
            "pressure_policy":
            {
                "activate_self_damping": True,
                "release_cognitive_pressure": True,
            },
            "drift_absorption":
            {
                "absorption_need": 0.46,
            },
            "identity_strain_regulator":
            {
                "identity_strain": 0.52,
            },
            "resonance_stability_control":
            {
                "resonance_risk": 0.45,
            },
        },

        "existential_homeostasis_report":
        {
            "existential_homeostasis_score": 0.48,
            "semantic_equilibrium":
            {
                "semantic_equilibrium": 0.44,
            },
            "continuity_equilibrium":
            {
                "continuity_equilibrium": 0.51,
            },
            "identity_homeostasis":
            {
                "identity_balance": 0.47,
            },
        },

        "existential_economics_report":
        {
            "drift_cost":
            {
                "drift_cost": 0.44,
            },
            "abstraction_overhead":
            {
                "abstraction_overhead": 0.62,
            },
        },

        "semantic_spine_report":
        {
            "semantic_elastic_topology":
            {
                "elasticity": 0.54,
            },
        },

        "ontological_boundary_report":
        {
            "topology_integrity_guard":
            {
                "topology_stable": True,
            },
        },

        "concept_lifecycle_report":
        {
            "failure_propagation_score": 0.48,
        },
    }

    report = adaptive_equilibrium_architecture.run_cycle(
        context,
    )

    policy = report["adaptive_equilibrium_policy"]

    assert report["layer"] == "continuous_evolutionary_equilibrium"
    assert policy["run_adaptive_stability_cycles"] is True
    assert policy["assimilate_safe_drift"] is True
    assert policy["allow_limited_topology_adaptation"] is True
    assert policy["constrain_abstraction_growth"] is True
    assert policy["activate_equilibrium_recovery"] is True
    assert report["cognitive_recovery_engine"]["recovery_actions"]
    assert report["adaptive_equilibrium_state"] == "adaptive_equilibrium_recovery_active"
