from core.ecology import (
    CognitiveEcology,
)


def test_cognitive_ecology_selects_traits_under_resource_pressure():

    ecology = CognitiveEcology()

    context = {
        "working_memory_pressure": 0.62,
        "attention_kernel_report": {
            "attention_saturation": 0.58,
        },
        "cognitive_energy_economy_report": {
            "total_energy_cost": 11.0,
        },
        "recursive_budget_market_report": {
            "base_recursion_budget": 8,
            "remaining_budget": 3,
        },
        "evolutionary_memory_report": {
            "adaptive_trait_memory": {
                "traits": [
                    {
                        "trait": "directional_motion",
                        "fitness": 0.76,
                        "observations": 5,
                        "trait_state": "adaptive_trait",
                    },
                    {
                        "trait": "unstable_symbolic_bridge",
                        "fitness": 0.18,
                        "observations": 1,
                        "trait_state": "candidate_trait",
                    },
                ],
            },
        },
    }

    report = ecology.run_cycle(
        context,
    )

    assert (
        report["resource_pressure"]["scarcity_state"]
        in [
            "constrained",
            "severe_scarcity",
        ]
    )

    assert (
        report["environmental_competition"][
            "competition_state"
        ]
        ==
        "active_competition"
    )

    assert (
        report["trait_selection"]["selected_count"]
        >=
        1
    )

    assert (
        report["trait_selection"]["suppressed_count"]
        >=
        1
    )

    assert (
        report["adaptive_fitness_landscape"][
            "average_fitness_peak"
        ]
        >
        0.0
    )
