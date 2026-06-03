from core.cognition.entropy_regulator import (
    EntropyRegulator,
)


def test_entropy_regulator_cools_mutation_storms():

    regulator = EntropyRegulator(
        storm_threshold=0.58,
    )

    context = {
        "runtime_entropy":
        0.6753,

        "identity_continuity":
        0.68,

        "evolutionary_memory_report":
        {
            "adaptive_trait_memory":
            {
                "traits":
                [
                    {
                        "id":
                        "unstable_bridge",

                        "mutation_rate":
                        0.30,
                    },
                    {
                        "id":
                        "causal_motion",

                        "mutation_rate":
                        0.18,
                    },
                ],
            },
        },
    }

    report = regulator.run_cycle(
        context,
    )

    assert report["entropy_delta_report"]["runtime_entropy"] == 0.6753
    assert (
        report["cognitive_cooling"]["cooling_state"]
        in [
            "soft_cooling",
            "hard_cooling",
        ]
    )

    regulated = report["mutation_rate_slowdown"]["regulated_traits"]

    assert len(regulated) == 2

    for trait in regulated:

        assert (
            trait["cooled_mutation_rate"]
            <
            trait["base_mutation_rate"]
        )

    assert (
        report["mutation_storm_control"]["mutation_storm_state"]
        in [
            "storm_watch",
            "storm_suppressed",
        ]
    )

    assert (
        report["stabilization_windows"]["stabilization_window"]
        in [
            "probationary_mutation_window",
            "freeze_new_mutations",
        ]
    )
