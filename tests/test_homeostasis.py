from core.homeostasis import (
    CognitiveHomeostasis,
    TRAIT_STATES,
)


def test_homeostasis_governs_mutation_pressure_under_entropy():

    homeostasis = CognitiveHomeostasis()

    context = {
        "runtime_entropy": 0.857,
        "trust_band": "sandboxed",
        "identity_continuity": 0.71,
        "identity_stability_report": {
            "continuity_verifier": {
                "continuity_score": 0.71,
            },
            "causal_memory": {
                "recent_events": [
                    {
                        "event": {
                            "event_type": "mutation",
                        },
                    },
                ],
            },
        },
        "semantic_firewall_report": {
            "ontology_intrusion_detection": {
                "average_merge_risk": 0.74,
            },
        },
        "cognitive_ecology_report": {
            "ecological_pressure_score": 0.68,
        },
        "evolutionary_memory_report": {
            "mutation_lineage": {
                "survived_count": 2,
                "collapsed_count": 1,
            },
            "adaptive_trait_memory": {
                "traits": [
                    {
                        "id": "directional_motion",
                        "mutation_rate": 0.22,
                        "trait_state": "candidate",
                    },
                    {
                        "id": "unstable_symbolic_bridge",
                        "mutation_rate": 0.24,
                        "trait_state": "emerging",
                    },
                ],
            },
        },
    }

    report = homeostasis.run_cycle(
        context,
    )

    assert report["entropy_regulation"]["entropy_state"] == "explosive"
    assert report["evolutionary_balance"]["trait_states"] == TRAIT_STATES

    regulated = report["mutation_governor"]["regulated_traits"]

    assert regulated

    for trait in regulated:

        assert (
            trait["effective_mutation_rate"]
            <
            trait["base_mutation_rate"]
        )

    assert (
        report["mutation_governor"][
            "mutation_governor_state"
        ]
        ==
        "runaway_mutation_suppressed"
    )

    assert (
        report["identity_anchors"]["anchor_state"]
        in [
            "collapse_resistant",
            "reinforcing",
        ]
    )
