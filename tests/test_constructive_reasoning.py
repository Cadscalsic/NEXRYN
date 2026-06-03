from core.constructive_reasoning.adaptive_discovery import (
    AdaptiveDiscovery,
)

from core.semantic_legitimacy.semantic_legitimacy import (
    SemanticLegitimacyEngine,
)


def test_constructive_reasoning_finds_value_when_rehearsal_is_ambiguous():

    context = {
        "causal_rehearsal_report": {
            "mutation_simulator": {
                "simulations": [
                    {
                        "simulation_id": "mutation_rehearsal:1",
                        "candidate_type": "bridge_concept",
                        "source": {
                            "first": "position_shift",
                            "second": "directional_motion",
                            "baseline_utility": 0.28,
                        },
                        "predicted_entropy_delta": 0.38,
                        "predicted_identity_delta": 0.34,
                        "predicted_utility": 0.49,
                        "causal_alignment": 0.78,
                        "novelty": 0.82,
                        "simulation_state": "ambiguous",
                    },
                ],
            },
            "future_state_projection": {
                "future_stability": 0.58,
                "average_predicted_utility": 0.49,
                "average_entropy_delta": 0.38,
            },
            "identity_forecaster": {
                "identity_continuity": 0.64,
            },
        },
    }

    discovery = AdaptiveDiscovery()
    legitimacy = SemanticLegitimacyEngine()

    context["constructive_reasoning_report"] = (
        discovery.run_cycle(context)
    )

    report = legitimacy.run_cycle(
        context,
    )

    assert (
        context["constructive_reasoning_report"][
            "discovery_state"
        ]
        in [
            "constructive_cognition_found",
            "promising_cognition_detected",
        ]
    )

    assert (
        report["constructive_mutation_detection"][
            "constructive_signal"
        ]
        >
        0.0
    )

    assert (
        report["constructive_mutation_detection"][
            "constructive_mutations"
        ]
        !=
        []
    )

    assert (
        report["evidence_exports"][
            "constructive_value_score"
        ]
        >
        0.0
    )
