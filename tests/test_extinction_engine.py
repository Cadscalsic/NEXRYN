from core.extinction_engine import (
    ExtinctionEngine,
)


def test_extinction_engine_kills_persistent_decaying_traits():

    engine = ExtinctionEngine(
        decay_threshold=1,
        suppressed_threshold=1,
    )

    weak_trait = {
        "id":
        "stale_bridge_trait",

        "niche":
        "semantic_remapping",

        "fitness":
        0.08,

        "stability_score":
        0.12,

        "mutation_rate":
        0.32,

        "trait_state":
        "decaying",

        "survival_history":
        [
            {
                "constructive_score":
                0.05,
            },
            {
                "constructive_score":
                0.06,
            },
        ],
    }

    context = {
        "cognitive_natural_selection_report":
        {
            "selected_traits":
            [],

            "decaying_traits":
            [
                weak_trait,
            ],

            "suppressed_traits":
            [],

            "extinct_traits":
            [],
        },
    }

    first_report = engine.run_cycle(
        context,
    )

    assert first_report["suppressed_count"] == 1
    assert first_report["extinct_count"] == 0
    assert first_report["selection_actions"][0]["action"] == "suppress_trait"

    second_report = engine.run_cycle(
        context,
    )

    assert second_report["decay_counters"]["stale_bridge_trait"] == 2
    assert second_report["extinct_count"] == 1
    assert second_report["selection_actions"][0]["action"] == "delete_trait"
    assert second_report["archived_traits"]

    reclaimed = second_report["resource_reclamation_totals"]

    assert reclaimed["memory"] > 0
    assert reclaimed["attention"] > 0
    assert reclaimed["mutation_cycles"] > 0
    assert reclaimed["evaluation_bandwidth"] > 0
    assert second_report["graveyard_pressure"]["pressure_score"] > 0
    assert second_report["graveyard_pressure"]["pressure_state"] in [
        "graveyard_pressure_elevated",
        "graveyard_pressure_high",
        "graveyard_pressure_critical",
    ]
    assert second_report["extinction_state"] == "extinction_wave"
