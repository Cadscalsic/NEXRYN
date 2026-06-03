from core.world_model.causal_simulator import (
    CausalWorldSimulator,
)


def test_causal_world_simulator_projects_collapse_and_identity_risk():

    simulator = CausalWorldSimulator()

    context = {
        "runtime_entropy": 0.8868,
        "semantic_cooling_system_report": {
            "cooling_strength": 0.38,
        },
        "identity_anchor_core_report": {
            "identity_drift_before": 0.4662,
        },
    }

    future = simulator.simulate_future(
        context,
        horizon=3,
    )

    counterfactuals = simulator.compare_outcomes(
        context,
    )

    collapse = simulator.estimate_collapse(
        future,
        counterfactuals,
    )

    identity = simulator.predict_identity_risk(
        context,
        counterfactuals,
    )

    report = simulator.run_cycle(
        context,
    )

    assert len(
        future["projections"]
    ) == 3

    assert counterfactuals["best_outcome"]["scenario"] in [
        "increase_cooling",
        "prefer_compiled_macros",
        "compress_recursion",
        "allow_more_exploration",
    ]

    assert collapse["collapse_probability"] > 0

    assert identity["predicted_identity_risk"] >= 0

    assert report["recommended_intervention"]
