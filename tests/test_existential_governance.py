from core.existential_governance import (
    existential_governance_core,
)


def test_existential_governance_guards_truth_trust_and_continuity():

    context = {
        "semantic_legitimacy_report":
        {
            "semantic_legitimacy_score": 0.34,
        },

        "adaptive_permissioning_report":
        {
            "trust_score":
            {
                "trust_score": 0.31,
            },
        },

        "ontological_boundary_report":
        {
            "invariant_boundary":
            {
                "protected_invariants":
                [
                    {"invariant_id": "causal_continuity"},
                    {"invariant_id": "identity_continuity"},
                ],
            },
        },

        "existential_pressure_report":
        {
            "managed_pressure": 0.68,
        },

        "existential_homeostasis_report":
        {
            "continuity_equilibrium":
            {
                "continuity_equilibrium": 0.42,
            },
        },

        "adaptive_equilibrium_report":
        {
            "resilient_identity_core":
            {
                "identity_resilience": 0.39,
            },
            "drift_assimilation":
            {
                "assimilated_drift": 0.18,
            },
            "propagation_stability_manager":
            {
                "failure_propagation_score": 0.55,
            },
        },

        "hybrid_governance_report":
        {
            "hybrid_governance_score": 0.41,
        },

        "recursive_reflective_report":
        {
            "recursive_reflective_score": 0.43,
        },

        "existential_economics_report":
        {
            "drift_cost":
            {
                "drift_cost": 0.58,
            },
        },

        "evolutionary_graveyard_report":
        {
            "toxic_lineages":
            {
                "unsafe_lineage": 2,
            },
            "top_causes":
            {
                "unsafe_merge": 3,
            },
        },

        "extinction_engine_report":
        {
            "extinct_count": 1,
        },
    }

    report = existential_governance_core.run_cycle(
        context,
    )

    policy = report["existential_governance_policy"]

    assert report["layer"] == "truth_survival_continuity_governance"
    assert policy["require_epistemic_attestation"] is True
    assert policy["block_survival_override_of_truth"] is True
    assert policy["route_semantics_to_legitimacy_review"] is True
    assert policy["preserve_extinction_memory"] is True
    assert policy["sandbox_low_trust_reasoning"] is True
    assert policy["contain_existential_drift"] is True
    assert policy["require_continuity_ethics_review"] is True
    assert policy["govern_graph_propagation"] is True
    assert policy["defer_semantic_commit"] is True
    assert report["persistent_identity_governor"]["identity_governance_actions"]
