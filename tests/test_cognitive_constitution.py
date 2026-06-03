from core.cognitive_constitution import (
    cognitive_constitution_layer,
)


def test_cognitive_constitution_enforces_identity_and_merge_law():

    context = {
        "identity_reasoner_report":
        {
            "identity_analyses":
            [
                {
                    "identity_status": "identity_conflict_above_limit",
                    "failure_explanation":
                    {
                        "hidden_conflicts":
                        {
                            "conflict_layers":
                            [
                                "geometric",
                                "structural",
                                "causal",
                                "existential",
                            ],
                        },
                    },
                },
            ],
        },

        "ontological_boundary_report":
        {
            "identity_boundary":
            {
                "blocked_identity_fusions": 2,
            },
        },

        "adaptive_equilibrium_report":
        {
            "resilient_identity_core":
            {
                "identity_resilience": 0.34,
            },
        },

        "judicial_cognition_report":
        {
            "epistemic_court":
            {
                "court_score": 0.32,
            },
            "ambiguity_reasoning":
            {
                "ambiguity_load": 0.76,
            },
            "semantic_legality":
            {
                "semantic_legality": 0.33,
            },
            "admissibility_filter":
            {
                "admissible": False,
            },
            "execution_gatekeeper":
            {
                "execution_permission": "sandbox_only",
            },
            "judicial_identity_supervisor":
            {
                "judicial_identity_score": 0.30,
            },
        },

        "existential_governance_report":
        {
            "adaptive_semantic_judgement":
            {
                "judgement_score": 0.35,
            },
            "semantic_legitimacy":
            {
                "legitimacy_pressure": 0.72,
            },
        },

        "concept_fusion_report":
        {
            "accepted_count": 1,
            "rejected_count": 3,
        },

        "hybrid_governance_report":
        {
            "paradigm_conflict":
            {
                "paradigm_conflict_score": 0.70,
            },
            "cognitive_fusion_stability":
            {
                "fusion_stability": 0.31,
            },
        },

        "existential_pressure_report":
        {
            "identity_strain_regulator":
            {
                "identity_strain": 0.73,
            },
            "ontological_tension_homeostasis":
            {
                "ontological_tension": 0.68,
            },
        },

        "cognitive_failure_memory":
        {
            "latest_failure":
            {
                "failure_type": "unsafe_merge",
            },
        },

        "concept_lineage_report":
        {
            "failure_records":
            [
                {"reason": "identity_conflict"},
                {"reason": "semantic_illegality"},
            ],
        },
    }

    report = cognitive_constitution_layer.run_cycle(context)
    policy = report["cognitive_constitution_policy"]

    assert report["layer"] == "cognitive_constitution"
    assert policy["enforce_identity_compatibility"] is True
    assert policy["filter_semantic_admissibility"] is True
    assert policy["block_illegal_merges"] is True
    assert policy["reduce_conflict_intensity"] is True
    assert policy["preserve_layered_identity_boundaries"] is True
    assert policy["predict_contradictions_before_commit"] is True
    assert policy["enforce_semantic_constitutional_law"] is True
    assert report["constitution_state"] == "cognitive_constitution_enforced"
    assert report["semantic_constitutional_law"]["constitutional_score"] < 0.58
