from core.judicial_cognition import (
    judicial_cognitive_runtime,
)


def test_judicial_cognition_routes_ambiguous_claims_to_sandbox():

    context = {
        "existential_governance_report":
        {
            "epistemic_validation":
            {
                "epistemic_confidence": 0.36,
            },
            "adaptive_semantic_judgement":
            {
                "judgement_score": 0.34,
            },
            "trust_weighted_reasoning":
            {
                "reasoning_weight": 0.31,
            },
            "semantic_legitimacy":
            {
                "legitimacy_pressure": 0.66,
            },
        },

        "hybrid_governance_report":
        {
            "paradigm_conflict":
            {
                "paradigm_conflict_score": 0.58,
            },
        },

        "recursive_reflective_report":
        {
            "propagation_topology_monitor":
            {
                "topology_risk": 0.66,
            },
            "topology_prediction":
            {
                "predicted_growth_risk": 0.62,
            },
        },

        "semantic_physics_report":
        {
            "causal_integrity": 0.36,
        },

        "ambiguity_score": 0.72,
    }

    report = judicial_cognitive_runtime.run_cycle(
        context,
    )

    policy = report["judicial_policy"]

    assert report["layer"] == "judicial_cognition"
    assert policy["require_epistemic_hearing"] is True
    assert policy["route_ambiguity_to_sandbox"] is True
    assert policy["sandbox_reasoning"] is True
    assert policy["require_topology_judgement"] is True
    assert policy["validate_semantic_legality"] is True
    assert policy["require_causal_permission"] is True
    assert policy["block_or_sandbox_execution"] is True
    assert policy["filter_admissibility"] is True
    assert report["execution_gatekeeper"]["execution_permission"] in [
        "blocked",
        "sandbox_only",
    ]
    assert report["judicial_identity_supervisor"]["judicial_actions"]
