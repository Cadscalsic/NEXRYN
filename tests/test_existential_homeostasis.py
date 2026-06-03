from core.existential_homeostasis import (
    existential_homeostasis_system,
)


def test_existential_homeostasis_runs_long_term_recovery_cycles():

    context = {
        "existential_economics_report":
        {
            "total_existential_cost": 0.66,
            "cognitive_resource_pressure":
            {
                "pressure_score": 0.61,
            },
            "drift_cost":
            {
                "drift_cost": 0.52,
            },
            "continuity_resource_allocation":
            {
                "continuity_allocation": 0.58,
            },
            "identity_cost":
            {
                "identity_maintenance_cost": 0.56,
            },
        },

        "ontological_boundary_report":
        {
            "existential_fatigue":
            {
                "ontological_fatigue": 0.62,
            },
            "invariant_survival":
            {
                "rehabilitated_invariants":
                [
                    {
                        "invariant_id": "topology_preservation",
                    },
                ],
            },
        },

        "evolutionary_graveyard_report":
        {
            "graveyard_pressure":
            {
                "pressure_score": 0.63,
            },
        },

        "semantic_spine_report":
        {
            "spine_integrity": 0.33,
            "semantic_gravity":
            {
                "gravity_strength": 0.22,
            },
        },

        "stability_field_report":
        {
            "semantic_drift":
            {
                "semantic_drift": 0.64,
            },
        },

        "identity_continuity_guardian_report":
        {
            "identity_continuity": 0.36,
        },
    }

    report = existential_homeostasis_system.run_cycle(
        context,
    )

    policy = report["homeostasis_policy"]

    assert report["layer"] == "long_term_evolutionary_homeostasis"
    assert policy["prioritize_stability_cycles"] is True
    assert policy["increase_semantic_gravity"] is True
    assert policy["run_drift_recovery"] is True
    assert policy["recycle_critical_invariants"] is True
    assert report["evolutionary_recovery_cycles"]["recovery_cycle_count"] >= 2
    assert report["adaptive_self_preservation"]["self_preservation_actions"]
    assert report["existential_homeostasis_state"] == "existential_homeostasis_repairing"
