from core.memory.compression import (
    MemoryCompressionLayer,
)


def test_memory_compression_preserves_identity_while_reducing_logs():

    layer = MemoryCompressionLayer(
        max_items_per_trace=3,
    )

    traits = [
        {
            "id":
            f"trait_{index}",

            "niche":
            "semantic_reasoning",

            "fitness":
            0.1 + index * 0.05,

            "semantic_alignment":
            0.4 + index * 0.03,

            "trait_state":
            "candidate",
        }
        for index in range(8)
    ]

    context = {
        "identity_continuity":
        0.64,

        "identity_stability_report":
        {
            "continuity_verifier":
            {
                "continuity_score":
                0.64,
            },

            "causal_memory":
            {
                "recent_events":
                [
                    {
                        "event_type":
                        "mutation",

                        "importance":
                        0.3 + index * 0.05,
                    }
                    for index in range(7)
                ],
            },
        },

        "evolutionary_memory_report":
        {
            "adaptive_trait_memory":
            {
                "traits":
                traits,
            },
        },

        "extinction_engine_report":
        {
            "extinction_archive":
            [
                {
                    "trait_id":
                    f"dead_{index}",

                    "reason":
                    "extinct_after_persistent_decay",

                    "importance":
                    0.2 + index * 0.1,
                }
                for index in range(6)
            ],
        },
    }

    report = layer.run_cycle(
        context,
    )

    assert report["original_item_count"] > report["retained_item_count"]
    assert report["compression_ratio"] < 1.0
    assert (
        report["identity_preserving_reduction"][
            "reduction_policy"
        ]
        ==
        "compress_non_identity_memory"
    )
    assert (
        "continuity_verifier"
        in report["identity_preserving_reduction"][
            "protected_memory_keys"
        ]
    )
