from core.cognition.stability_field import (
    StabilityField,
)


def test_stability_field_computes_identity_pressure_components():

    field = StabilityField()

    context = {
        "runtime_entropy":
        0.6753,

        "cognitive_natural_selection_report":
        {
            "decaying_count":
            2,

            "suppressed_count":
            1,
        },

        "extinction_engine_report":
        {
            "extinct_count":
            1,
        },

        "concept_fusion_report":
        {
            "fused_concepts":
            [
                {},
            ],

            "rejected_fusions":
            [
                {},
            ],
        },

        "memory_compression_report":
        {
            "compression_ratio":
            0.142,
        },

        "identity_continuity_guardian_report":
        {
            "semantic_anchor_graph":
            {
                "drift_clusters":
                {
                    "drift_cluster_count":
                    2,
                },
            },
        },

        "identity_stability_report":
        {
            "causal_memory":
            {
                "recent_events":
                [
                    {},
                    {},
                ],
            },
        },
    }

    pressure = field.compute_identity_pressure(
        context,
    )

    assert pressure["identity_pressure"] > 0.2
    assert pressure["mutation_overload"] > 0
    assert pressure["abstraction_overload"] > 0
    assert pressure["memory_compression_stress"] > 0.8
    assert pressure["causal_fragmentation"] > 0


def test_stability_field_rejects_destructive_mutation_under_fragmentation():

    field = StabilityField()

    context = {
        "runtime_entropy":
        0.9,

        "cognitive_natural_selection_report":
        {
            "decaying_count":
            5,

            "suppressed_count":
            4,
        },

        "extinction_engine_report":
        {
            "extinct_count":
            4,
        },

        "concept_fusion_report":
        {
            "fused_concepts":
            [
                {},
                {},
                {},
            ],

            "rejected_fusions":
            [
                {},
                {},
                {},
                {},
            ],
        },

        "memory_compression_report":
        {
            "compression_ratio":
            0.10,
        },

        "identity_continuity_guardian_report":
        {
            "semantic_anchor_graph":
            {
                "identity_stability":
                {
                    "identity_stability":
                    0.22,
                },

                "drift_clusters":
                {
                    "drift_cluster_count":
                    5,
                },
            },
        },

        "cognitive_homeostasis_report":
        {
            "identity_anchors":
            {
                "anchor_strength":
                0.20,
            },

            "semantic_drift_detection":
            {
                "semantic_drift":
                0.76,
            },
        },

        "identity_stability_report":
        {
            "causal_memory":
            {
                "recent_events":
                [],
            },
        },
    }

    report = field.run_cycle(
        context,
    )

    assert (
        report["destructive_mutation_filter"][
            "reject_destructive_mutation"
        ]
        is True
    )
    assert report["stability_field_state"] == "immune_rejection_active"
    assert "identity_spine" in report["core_semantic_preservation"]["semantic_locks"]
