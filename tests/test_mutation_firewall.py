from core.cognition.mutation_firewall import (
    MutationFirewall,
)

from core.evolutionary_memory.adaptive_trait_memory import (
    AdaptiveTraitMemory,
)


def test_mutation_firewall_deduplicates_fusion_events():

    firewall = MutationFirewall()

    mutation = {
        "type":
        "fusion",

        "fusion_stability":
        0.473123,

        "primitive":
        "preserve_size",
    }

    assert firewall.allow(
        "object_size",
        mutation,
    )

    assert not firewall.allow(
        "object_size",
        {
            "type":
            "fusion",

            "fusion_stability":
            0.4731,

            "primitive":
            "preserve_size",
        },
    )


def test_adaptive_trait_memory_blocks_repeated_survival_rehearsal():

    memory = AdaptiveTraitMemory()

    archive_report = {
        "archived_patterns":
        [
            {
                "survival_state":
                "survived_rehearsal",

                "constructive_score":
                0.71,

                "identity_continuity":
                0.82,

                "mutation":
                {
                    "candidate_type":
                    "bridge_concept",

                    "source":
                    {
                        "second":
                        "dedupe_survival_trait",

                        "causal_alignment":
                        0.76,
                    },
                },
            },
        ],
    }

    first = memory.update(
        archive_report,
    )

    second = memory.update(
        archive_report,
    )

    assert first["traits"][0]["observations"] == 1
    assert second["traits"][0]["observations"] == 1
    assert len(
        second["traits"][0]["survival_history"]
    ) == 1
