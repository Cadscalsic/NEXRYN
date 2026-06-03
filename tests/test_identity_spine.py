from core.identity.identity_stability_core import (
    IdentityStabilityCore,
)


def test_identity_spine_reinforces_fragile_continuity():

    identity = IdentityStabilityCore()

    context = {
        "identity_continuity": 0.6037,
        "identity_core_report": {
            "identity_drift": 0.31,
            "continuity_state": "watched",
            "behavior_shift": {
                "shift_detected": False,
            },
        },
        "causal_rehearsal_report": {
            "identity_forecaster": {
                "identity_continuity": 0.6037,
                "forecast_state": "continuity_fragile",
            },
        },
        "semantic_firewall_report": {
            "concept_sandboxing": {
                "sandboxed_events": [
                    {
                        "event_type": "mutation",
                        "source": {
                            "mutation_type": "semantic_bridge",
                        },
                        "sandbox_policy": "quarantine_then_review",
                    },
                ],
            },
        },
        "executive_mode": "balanced_reasoning",
        "selected_actions": [
            "reason",
        ],
    }

    report = identity.run_cycle(
        context,
    )

    assert (
        report["identity_spine_state"]
        ==
        "identity_spine_reinforced"
    )

    assert (
        report["identity_anchor"]["anchor_state"]
        ==
        "reinforced"
    )

    assert (
        report["continuity_verifier"][
            "verification_state"
        ]
        ==
        "fragile_verified"
    )

    assert (
        "fragile_identity_forecast"
        in report["continuity_verifier"][
            "violations"
        ]
    )

    assert (
        "protected_cognition_laws"
        in report["self_consistency_graph"][
            "nodes"
        ]
    )

    assert (
        report["causal_memory"][
            "recorded_event_count"
        ]
        ==
        1
    )
