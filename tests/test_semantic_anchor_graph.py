from core.identity.continuity_guardian import (
    IdentityContinuityGuardian,
)

from core.identity.semantic_anchor_graph import (
    SemanticAnchorGraph,
)

from core.memory.compression import (
    MemoryCompressionLayer,
)


def test_semantic_anchor_graph_links_identity_memory_and_survival():

    graph = SemanticAnchorGraph()

    context = {
        "identity_continuity":
        0.736,

        "identity_stability_report":
        {
            "identity_spine_state":
            "identity_spine_reinforced",

            "identity_anchor":
            {
                "anchor_strength":
                0.6779,
            },

            "continuity_verifier":
            {
                "continuity_score":
                0.736,

                "graph_consistency":
                0.69,

                "anchor_strength":
                0.6779,
            },

            "self_consistency_graph":
            {
                "consistency_score":
                0.69,
            },

            "causal_memory":
            {
                "recorded_event_count":
                5,

                "recent_events":
                [
                    {
                        "event_type":
                        "mutation",
                    },
                ],
            },
        },

        "adaptive_permissioning_report":
        {
            "cognitive_reputation":
            {
                "average_reputation":
                0.42,

                "reputation_state":
                "forming",
            },
        },

        "evolutionary_memory_report":
        {
            "adaptive_trait_memory":
            {
                "traits":
                [
                    {
                        "id":
                        "causal_bridge",

                        "fitness":
                        0.62,
                    },
                ],
            },
        },

        "memory_compression_report":
        {
            "compression_ratio":
            0.142,
        },
    }

    report = graph.run_cycle(
        context,
    )

    for anchor_id in [
        "identity",
        "memory",
        "causality",
        "semantic_consistency",
        "reputation",
        "survival_history",
    ]:

        assert anchor_id in report["anchors"]

    assert report["edges"]
    assert (
        report["identity_stability"]["identity_stability"]
        >
        0.45
    )
    assert (
        report["core_semantic_preservation"][
            "protected_semantic_anchors"
        ]
    )


def test_guardian_blocks_rewrite_when_semantic_anchor_graph_fragments():

    guardian = IdentityContinuityGuardian()

    context = {
        "identity_continuity":
        0.31,

        "identity_stability_report":
        {
            "stable_snapshot":
            {
                "identity_drift":
                0.1,
            },

            "identity_spine_state":
            "identity_repair_required",

            "identity_diff":
            {
                "identity_shift":
                0.58,
            },

            "continuity_verifier":
            {
                "continuity_score":
                0.31,

                "graph_consistency":
                0.18,

                "anchor_strength":
                0.22,
            },

            "identity_anchor":
            {
                "anchor_strength":
                0.22,
            },

            "self_consistency_graph":
            {
                "consistency_score":
                0.18,
            },

            "causal_memory":
            {
                "recent_events":
                [],
            },
        },

        "memory_compression_report":
        {
            "compression_ratio":
            0.142,
        },
    }

    report = guardian.run_cycle(
        context,
    )

    assert (
        report["semantic_anchor_graph"][
            "semantic_anchor_state"
        ]
        ==
        "semantic_reconstruction_required"
    )
    assert (
        report["catastrophic_rewrite_guard"][
            "block_rewrite"
        ]
        is True
    )
    assert report["rollback"]["rollback_required"] is True


def test_memory_compression_protects_semantic_anchor_graph():

    layer = MemoryCompressionLayer()

    context = {
        "identity_continuity":
        0.72,

        "identity_stability_report":
        {
            "continuity_verifier":
            {
                "continuity_score":
                0.72,
            },
        },

        "identity_continuity_guardian_report":
        {
            "semantic_anchor_graph":
            {
                "semantic_anchor_state":
                "semantic_reconstruction_required",
            },
        },
    }

    report = layer.run_cycle(
        context,
    )

    reduction = report["identity_preserving_reduction"]

    assert "semantic_anchor_graph" in reduction["protected_memory_keys"]
    assert reduction["reduction_policy"] == "preserve_identity_full"


def test_reputation_anchor_uses_concept_reputation_not_survival_only():

    graph = SemanticAnchorGraph()

    context = {
        "identity_continuity":
        0.70,

        "identity_stability_report":
        {
            "continuity_verifier":
            {
                "continuity_score":
                0.70,

                "graph_consistency":
                0.68,

                "anchor_strength":
                0.66,
            },

            "identity_anchor":
            {
                "anchor_strength":
                0.66,
            },

            "self_consistency_graph":
            {
                "consistency_score":
                0.68,
            },

            "causal_memory":
            {
                "recent_events":
                [
                    {
                        "event_type":
                        "validated_concept",
                    },
                ],
            },
        },

        "concept_reputation_engine_report":
        {
            "reputation_state":
            "epistemically_forming",

            "concept_reputations":
            [
                {
                    "concept":
                    "causal_color_mapping",

                    "reputation":
                    0.74,

                    "contradiction_history":
                    0.05,

                    "failure_propagation_score":
                    0.08,
                },
            ],
        },

        "evolutionary_memory_report":
        {
            "adaptive_trait_memory":
            {
                "traits":
                [
                    {
                        "id":
                        "survived_but_untrusted_trait",

                        "fitness":
                        0.95,
                    },
                ],
            },
        },
    }

    report = graph.run_cycle(
        context,
    )

    reputation = report["anchors"]["reputation"]

    assert reputation["strength"] > 0.68

    assert (
        reputation["semantic_state"]["anchor_source"]
        ==
        "concept_reputation_engine"
    )

    assert (
        reputation["semantic_state"]["survival_is_not_truth"]
        is True
    )


def test_reputation_anchor_does_not_trust_survival_without_evidence():

    graph = SemanticAnchorGraph()

    context = {
        "identity_continuity":
        0.70,

        "identity_stability_report":
        {
            "continuity_verifier":
            {
                "continuity_score":
                0.70,
            },
        },

        "evolutionary_memory_report":
        {
            "adaptive_trait_memory":
            {
                "traits":
                [
                    {
                        "id":
                        "survived_but_unvalidated",

                        "fitness":
                        0.98,
                    },
                ],
            },
        },
    }

    report = graph.run_cycle(
        context,
    )

    reputation = report["anchors"]["reputation"]

    assert reputation["strength"] == 0.0

    assert (
        reputation["semantic_state"]["anchor_source"]
        ==
        "missing_epistemic_evidence"
    )

    assert (
        "reseed_reputation_from_epistemic_history"
        in report["identity_reconstruction"][
            "reconstruction_plan"
        ]
    )


def test_semantic_anchor_graph_uses_hysteresis_for_small_stability_dip():

    graph = SemanticAnchorGraph()

    stable = graph._regulate_stability_state(
        0.74,
        "stable_semantic_spine",
    )

    buffered = graph._regulate_stability_state(
        0.70,
        "fragile_semantic_spine",
    )

    assert stable["stability_state"] == "stable_semantic_spine"
    assert buffered["stability_state"] == "stable_semantic_spine"
    assert buffered["stability_transition"] == "stable_hysteresis_hold"


def test_semantic_anchor_graph_normalizes_string_truth_commitments():

    graph = SemanticAnchorGraph()

    report = graph.run_cycle({
        "identity_continuity":
        0.70,

        "truth_commitments":
        [
            "shape_preservation",
            "color_preservation",
        ],
    })

    anchor = report["anchors"]["constitutional_truth"]
    validation = report["concept_schema_validation"][
        "truth_commitments"
    ]

    assert anchor["semantic_state"]["commitment_count"] == 2
    assert anchor["semantic_state"]["concepts"] == [
        "shape_preservation",
        "color_preservation",
    ]
    assert validation["coerced_string_count"] == 2
    assert validation["rejected_count"] == 0
