from core.evolution.recovery_engine import (
    TraitRecoveryEngine,
)


def test_trait_recovery_engine_resurrects_wrongful_extinction_candidate():

    recovery = TraitRecoveryEngine(
        recovery_threshold=0.45,
    )

    extinct_trait = {
        "id":
        "causal_bridge_trait",

        "niche":
        "causal_reasoning",

        "fitness":
        0.42,

        "semantic_alignment":
        0.82,

        "stability_score":
        0.74,

        "mutation_rate":
        0.24,

        "trait_state":
        "extinct",
    }

    context = {
        "runtime_entropy":
        0.34,

        "cognitive_ecology_report":
        {
            "ecological_pressure_score":
            0.82,
        },

        "semantic_legitimacy_report":
        {
            "semantic_legitimacy_score":
            0.78,
        },

        "cognitive_homeostasis_report":
        {
            "identity_stabilization":
            {
                "identity_stability":
                0.86,
            },
        },

        "extinction_engine_report":
        {
            "extinction_archive":
            [
                {
                    "trait_id":
                    "causal_bridge_trait",

                    "reason":
                    "extinct_after_persistent_decay",

                    "trait_snapshot":
                    extinct_trait,
                },
            ],
        },
    }

    report = recovery.run_cycle(
        context,
    )

    assert report["monitored_count"] == 1
    assert report["recovered_count"] == 1
    assert report["recovered_traits"][0]["trait_state"] == "emerging"
    assert (
        report["recovered_traits"][0]["recovery_status"]
        ==
        "probationary_resurrection"
    )
    assert (
        report["recovered_traits"][0]["mutation_rate"]
        <
        extinct_trait["mutation_rate"]
    )
    assert report["recovery_state"] == "resurrection_active"
