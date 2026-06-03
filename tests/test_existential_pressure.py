from core.existential_pressure import (
    existential_pressure_management,
)


def test_existential_pressure_management_damps_and_releases_pressure():

    context = {
        "existential_economics_report":
        {
            "total_existential_cost": 0.68,
            "cognitive_resource_pressure":
            {
                "pressure_score": 0.64,
            },
            "merge_cost":
            {
                "merge_cost": 0.58,
            },
            "drift_cost":
            {
                "drift_cost": 0.56,
            },
            "identity_cost":
            {
                "identity_maintenance_cost": 0.62,
            },
        },

        "existential_homeostasis_report":
        {
            "existential_homeostasis_score": 0.38,
        },

        "ontological_boundary_report":
        {
            "existential_fatigue":
            {
                "ontological_fatigue": 0.66,
            },
            "identity_boundary":
            {
                "blocked_identity_fusions": 2,
            },
        },

        "evolutionary_graveyard_report":
        {
            "graveyard_pressure":
            {
                "pressure_score": 0.61,
            },
        },

        "memory_pressure_score": 0.58,

        "semantic_spine_report":
        {
            "spine_integrity": 0.34,
        },

        "concept_fusion_report":
        {
            "rejected_count": 2,
        },

        "identity_continuity_guardian_report":
        {
            "identity_continuity": 0.35,
        },
    }

    report = existential_pressure_management.run_cycle(
        context,
    )

    policy = report["pressure_policy"]

    assert report["layer"] == "existential_pressure_management_layer"
    assert report["pressure_accumulation"]["accumulated_pressure"] >= 0.50
    assert policy["activate_self_damping"] is True
    assert policy["release_cognitive_pressure"] is True
    assert policy["throttle_identity_sensitive_merges"] is True
    assert policy["absorb_semantic_drift"] is True
    assert policy["regulate_identity_strain"] is True
    assert report["managed_pressure"] < report["pressure_accumulation"]["accumulated_pressure"]
    assert report["pressure_management_state"] == "existential_pressure_management_active"
