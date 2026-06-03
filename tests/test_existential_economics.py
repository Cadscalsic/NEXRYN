from core.existential_economics import (
    cognitive_existential_economics,
)


def test_existential_economics_prices_the_cost_of_being_a_self():

    context = {
        "identity_continuity_guardian_report":
        {
            "identity_continuity": 0.34,
            "drift_clusters":
            {
                "drift_cluster_count": 3,
            },
        },

        "ontological_boundary_report":
        {
            "identity_boundary":
            {
                "blocked_identity_fusions": 2,
            },
            "invariant_boundary":
            {
                "protected_invariants":
                [
                    {"invariant_id": "causal_continuity"},
                    {"invariant_id": "identity_continuity"},
                    {"invariant_id": "constitutional_truth"},
                    {"invariant_id": "semantic_spine"},
                ],
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
            "topology_integrity_guard":
            {
                "topology_state": "topology_integrity_guard_active",
            },
            "existential_fatigue":
            {
                "identity_stress": 0.48,
            },
        },

        "concept_fusion_report":
        {
            "rejected_count": 2,
        },

        "evolutionary_graveyard_report":
        {
            "graveyard_pressure":
            {
                "pressure_score": 0.65,
            },
        },

        "cognitive_energy_economy_report":
        {
            "total_energy_cost": 0.66,
        },

        "memory_pressure_score": 0.72,

        "semantic_spine_report":
        {
            "spine_integrity": 0.28,
            "semantic_elastic_topology":
            {
                "elasticity": 0.22,
            },
        },

        "stability_field_report":
        {
            "semantic_drift":
            {
                "semantic_drift": 0.62,
            },
            "cognitive_pressure":
            {
                "abstraction_overload": 0.58,
            },
        },

        "semantic_abstractions":
        [
            "object_size",
            "color_symmetry",
            "topology_relation",
        ],
    }

    report = cognitive_existential_economics.run_cycle(
        context,
    )

    policy = report["economic_policy"]

    assert report["layer"] == "cost_of_being_a_self"
    assert report["total_existential_cost"] >= 0.48
    assert policy["price_identity_before_evolution"] is True
    assert policy["reduce_merge_frequency"] is True
    assert policy["defer_noncritical_abstractions"] is True
    assert policy["reserve_continuity_budget"] is True
    assert report["existential_homeostasis"]["homeostasis_actions"]
