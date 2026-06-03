from core.sandbox.evolution_sandbox import (
    EvolutionSimulationSandbox,
)


def test_evolution_sandbox_simulates_parallel_futures_before_commit():

    sandbox = EvolutionSimulationSandbox()

    context = {
        "runtime_entropy":
        0.42,

        "entropy_regulator_report":
        {
            "cognitive_cooling":
            {
                "cooling_factor":
                0.78,
            },

            "mutation_storm_control":
            {
                "storm_pressure":
                0.31,
            },
        },

        "identity_continuity_guardian_report":
        {
            "state_transition":
            {
                "current_state":
                {
                    "identity_continuity":
                    0.82,
                },
            },

            "catastrophic_rewrite_guard":
            {
                "block_rewrite":
                False,
            },
        },

        "trait_recovery_report":
        {
            "recovered_traits":
            [
                {
                    "id":
                    "causal_bridge_trait",

                    "fitness":
                    0.68,

                    "mutation_rate":
                    0.16,

                    "trait_state":
                    "emerging",
                },
            ],
        },
    }

    report = sandbox.run_cycle(
        context,
    )

    assert report["simulated_branch_count"] == 3
    assert report["parallel_futures"]
    assert report["best_future"]["commit_probability"] > 0
    assert (
        report["sandbox_commit_gate"]
        in [
            "allow_candidate_commit",
            "simulation_only",
        ]
    )

    for future in report["parallel_futures"]:

        assert "forecast" in future
        assert "collapse_prediction" in future
        assert "sandbox_decision" in future


def test_evolution_sandbox_predicts_collapse_under_identity_guard():

    sandbox = EvolutionSimulationSandbox()

    context = {
        "runtime_entropy":
        0.88,

        "entropy_regulator_report":
        {
            "cognitive_cooling":
            {
                "cooling_factor":
                0.32,
            },

            "mutation_storm_control":
            {
                "storm_pressure":
                0.84,
            },
        },

        "identity_continuity_guardian_report":
        {
            "state_transition":
            {
                "current_state":
                {
                    "identity_continuity":
                    0.38,
                },
            },

            "catastrophic_rewrite_guard":
            {
                "block_rewrite":
                True,
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
                        "unstable_growth_trait",

                        "fitness":
                        0.18,

                        "mutation_rate":
                        0.42,

                        "trait_state":
                        "candidate",
                    },
                ],
            },
        },
    }

    report = sandbox.run_cycle(
        context,
    )

    assert report["collapse_predictions"]
    assert report["sandbox_state"] == "collapse_predicted"
