from core.hybrid_governance import (
    hybrid_governance_architecture,
)


def test_hybrid_governance_guards_cross_paradigm_fusion():

    context = {
        "meta_selection_report":
        {
            "dominant_reasoning": "hybrid_reasoning",
            "candidate_modes":
            [
                "symbolic",
                "spatial",
                "causal",
                "hybrid",
            ],
        },

        "ontological_boundary_report":
        {
            "identity_boundary":
            {
                "blocked_identity_fusions": 2,
            },
            "existential_fatigue":
            {
                "ontological_fatigue": 0.58,
            },
        },

        "concept_fusion_report":
        {
            "rejected_count": 2,
        },

        "existential_pressure_report":
        {
            "managed_pressure": 0.55,
            "merge_pressure_balancer":
            {
                "merge_pressure": 0.58,
            },
        },

        "adaptive_equilibrium_report":
        {
            "resilient_identity_core":
            {
                "identity_resilience": 0.42,
            },
            "contextual_topology_regulator":
            {
                "contextual_topology_flexibility": 0.38,
            },
            "drift_assimilation":
            {
                "assimilated_drift": 0.36,
            },
        },
    }

    report = hybrid_governance_architecture.run_cycle(
        context,
    )

    policy = report["hybrid_governance_policy"]

    assert report["layer"] == "cross_paradigm_coexistence_governance"
    assert policy["require_cross_paradigm_attestation"] is True
    assert policy["sandbox_hybrid_fusion"] is True
    assert policy["route_multimodal_semantics"] is True
    assert policy["preserve_parallel_paradigms"] is True
    assert policy["regulate_structural_translation"] is True
    assert report["adaptive_paradigm_firewall"]["firewall_actions"]
    assert report["cognitive_fusion_stability"]["fusion_state"] == "hybrid_fusion_unstable"
