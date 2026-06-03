from core.cognition.identity_reasoner import (
    IdentityReasoner,
)


def test_identity_reasoner_explains_conflict_and_repair_plan():

    reasoner = IdentityReasoner()

    object_size = {
        "concept":
        "object_size",

        "identity":
        {
            "structural_identity":
            [
                "object",
                "size",
            ],

            "causal_identity":
            "spatial_expansion",

            "archetypal_identity":
            "object_spatial_magnitude",
        },
    }

    color_parity = {
        "concept":
        "color_parity",

        "identity":
        {
            "structural_identity":
            [
                "color",
                "parity",
            ],

            "causal_identity":
            "symbolic_recoloring",

            "archetypal_identity":
            "symbolic_surface_rule",
        },
    }

    failure = reasoner.explain_identity_failure(
        object_size,
        color_parity,
    )

    repair = reasoner.generate_identity_repair_plan(
        failure,
    )

    stability = reasoner.predict_merge_stability(
        object_size,
        color_parity,
    )

    assert failure["failure_state"] == "identity_failure_explained"
    assert "structural_signature_conflict" in failure["failure_reasons"]
    assert "causal_role_conflict" in failure["failure_reasons"]
    assert repair["repair_state"] == "repair_required"
    assert stability["merge_state"] == "unstable_merge"


def test_identity_reasoner_accepts_repairable_overlap():

    reasoner = IdentityReasoner()

    hybrid = {
        "concept":
        "hybrid_object_size",

        "identity":
        {
            "structural_identity":
            [
                "object",
                "size",
                "mixed_signature",
            ],

            "causal_identity":
            [
                "spatial_expansion",
                "object_scale_change",
            ],

            "archetypal_identity":
            "object_spatial_magnitude",
        },
    }

    structural = {
        "concept":
        "structural_object_size",

        "identity":
        {
            "structural_identity":
            [
                "object",
                "size",
                "structural_signature",
            ],

            "causal_identity":
            [
                "spatial_expansion",
                "object_scale_change",
            ],

            "archetypal_identity":
            "object_spatial_magnitude",
        },
    }

    coherence = reasoner.compute_identity_coherence(
        hybrid,
        structural,
    )

    stability = reasoner.predict_merge_stability(
        hybrid,
        structural,
    )

    assert coherence["identity_coherence"] > 0.55
    assert stability["merge_state"] in [
        "stable_merge",
        "repair_before_merge",
    ]


def test_identity_reasoner_explains_unsafe_strategy_merge_memory():

    reasoner = IdentityReasoner()

    context = {
        "cognitive_failure_memory":
        {
            "latest_failure":
            {
                "contradiction_type":
                "unsafe_merge",

                "collapse_source":
                "object_translation::structural_object_translation",

                "ontology_damage":
                0.5,

                "recovery_action":
                "block_merge",
            },
        },
    }

    report = reasoner.run_cycle(
        context,
    )

    assert report["observed_concept_count"] == 2
    assert report["identity_analyses"]

    analysis = report["identity_analyses"][0]

    reasons = analysis["failure_explanation"]["failure_reasons"]
    repair_actions = analysis["repair_plan"]["repair_actions"]

    assert "unsafe_merge_memory" in reasons
    assert "specialization_boundary_conflict" in reasons
    assert "block_merge_until_failure_memory_clears" in repair_actions
    assert "track_parent_strategy_as_lineage_not_identity_merge" in repair_actions
