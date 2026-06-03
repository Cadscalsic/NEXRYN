from core.evolutionary_memory import (
    CognitiveTrait,
    EvolutionaryMemory,
)


def test_evolutionary_memory_tracks_surviving_beneficial_mutations():

    memory = EvolutionaryMemory()

    context = {
        "identity_stability_report": {
            "identity_spine_state": "identity_spine_stable",
            "continuity_verifier": {
                "continuity_score": 0.74,
            },
        },
        "constructive_reasoning_report": {
            "constructive_assessments": [
                {
                    "simulation": {
                        "candidate_type": "bridge_concept",
                        "source": {
                            "first": "position_shift",
                            "second": "directional_motion",
                        },
                        "predicted_identity_delta": 0.24,
                        "predicted_entropy_delta": 0.30,
                        "predicted_utility": 0.66,
                    },
                    "constructive_signal": {
                        "constructive_state": "constructive",
                        "constructive_score": 0.68,
                    },
                    "constructive_score": 0.68,
                },
            ],
        },
    }

    report = memory.run_cycle(
        context,
    )

    assert report["heredity_state"] == "adaptive_heredity_forming"

    assert (
        report["mutation_lineage"]["survived_count"]
        ==
        1
    )

    assert (
        report["beneficial_pattern_archive"][
            "archive_size"
        ]
        ==
        1
    )

    assert (
        report["cognitive_genealogy"][
            "genealogy_size"
        ]
        ==
        1
    )

    assert (
        report["adaptive_trait_memory"][
            "trait_count"
        ]
        ==
        1
    )

    trait = report["adaptive_trait_memory"]["traits"][0]

    for key in [
        "id",
        "niche",
        "fitness",
        "mutation_rate",
        "inheritance_strength",
        "stability_score",
        "semantic_alignment",
        "survival_history",
    ]:

        assert key in trait

    assert isinstance(
        memory.adaptive_trait_memory.traits[
            "directional_motion"
        ],
        CognitiveTrait,
    )

    assert (
        report["evolutionary_pressure"][
            "selection_state"
        ]
        in [
            "promote_lineage",
            "continue_rehearsal",
        ]
    )
