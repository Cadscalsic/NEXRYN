from core.trust_system.adaptive_permissioning import (
    AdaptivePermissioning,
)


def test_adaptive_permissioning_prevents_defensive_paralysis():

    permissioning = AdaptivePermissioning()

    context = {
        "runtime_entropy": 0.55,
        "semantic_attestation_score": 0.30,
        "identity_attestation_score": 0.30,
        "causal_attestation_score": 0.30,
        "semantic_firewall_report": {
            "firewall_pressure": 0.7066,
            "firewall_state": "quarantine",
            "decision": "quarantine",
            "ontology_intrusion_detection": {
                "average_merge_risk": 0.62,
            },
            "identity_attack_detection": {
                "attack_score": 0.45,
            },
            "concept_sandboxing": {
                "sandbox_state": "locked",
                "sandboxed_events": [
                    {
                        "event_type": "bridge_concept",
                        "source": {
                            "first": "position_shift",
                            "second": "directional_motion",
                            "merge_risk": 0.61,
                        },
                        "sandbox_pressure": 0.7492,
                        "sandbox_policy": "quarantine_then_review",
                    },
                ],
            },
        },
    }

    report = permissioning.run_cycle(
        context,
    )

    assert report["binary_trust_replaced"] is True

    assert (
        report["trust_model"]
        ==
        "continuous_trust_spectrum"
    )

    assert report["commit_probability"] > 0.0

    assert (
        report["permission_state"]
        in [
            "evolve_safely",
            "observe_and_rehearse",
        ]
    )

    assert (
        report["graduated_commitment"][
            "commitment_tier"
        ]
        in [
            "probationary_commit",
            "sandbox_observation",
        ]
    )
