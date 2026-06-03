from core.natural_selection import (
    CognitiveNaturalSelection,
)


def test_natural_selection_suppresses_weak_accumulated_traits():

    selection = CognitiveNaturalSelection()

    traits = [
        {
            "id": "directional_motion",
            "niche": "spatial_causal_reasoning",
            "fitness": 0.72,
            "inheritance_strength": 0.68,
            "semantic_alignment": 0.70,
            "stability_score": 0.68,
            "mutation_rate": 0.08,
            "trait_state": "candidate",
            "survival_history": [
                {
                    "constructive_score": 0.70,
                },
            ],
        },
    ]

    traits.extend([
        {
            "id": f"weak_bridge_{index}",
            "niche": "semantic_remapping",
            "fitness": 0.12,
            "inheritance_strength": 0.14,
            "semantic_alignment": 0.18,
            "stability_score": 0.20,
            "mutation_rate": 0.26,
            "trait_state": "candidate",
            "survival_history": [
                {
                    "constructive_score": 0.10,
                },
                {
                    "constructive_score": 0.12,
                },
                {
                    "constructive_score": 0.08,
                },
            ],
        }
        for index in range(3)
    ])

    context = {
        "runtime_entropy": 0.857,
        "cognitive_ecology_report": {
            "ecological_pressure_score": 0.72,
        },
        "evolutionary_memory_report": {
            "adaptive_trait_memory": {
                "traits": traits,
            },
        },
    }

    report = selection.run_cycle(
        context,
    )

    assert report["trait_competition_matrix"]

    first = report["trait_competition_matrix"][0]

    for key in [
        "competition_score",
        "resource_pressure",
        "dominance_pressure",
        "semantic_territory",
        "adaptive_advantage",
    ]:

        assert key in first

    costs = first["resource_costs"]

    for key in [
        "energy_cost",
        "memory_cost",
        "attention_cost",
        "execution_cost",
        "maintenance_cost",
    ]:

        assert key in costs

    assert (
        report["suppressed_count"]
        +
        report["extinct_count"]
        >=
        1
    )

    assert report["selection_actions"]

    assert (
        report["selection_state"]
        in [
            "active_natural_selection",
            "extinction_wave",
        ]
    )

    assert (
        report["trait_speciation"]["species_count"]
        >=
        1
    )
