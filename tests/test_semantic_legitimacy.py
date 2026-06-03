from core.rehearsal.causal_rehearsal import (
    CausalRehearsal,
)

from core.semantic_legitimacy.semantic_legitimacy import (
    SemanticLegitimacyEngine,
)

from core.trust_system.adaptive_permissioning import (
    AdaptivePermissioning,
)


def test_semantic_legitimacy_distinguishes_novelty_from_threat():

    context = {
        "runtime_entropy": 0.52,
        "controlled_safe_novelty_report": {
            "novelty_release_budget": 0.45,
        },
        "semantic_firewall_report": {
            "firewall_pressure": 0.7066,
            "firewall_state": "quarantine",
            "decision": "quarantine",
            "ontology_intrusion_detection": {
                "average_merge_risk": 0.62,
            },
            "identity_attack_detection": {
                "attack_score": 0.30,
            },
            "concept_sandboxing": {
                "sandbox_state": "locked",
                "sandboxed_events": [
                    {
                        "event_type": "bridge_concept",
                        "source": {
                            "first": "position_shift",
                            "second": "directional_motion",
                            "merge_risk": 0.36,
                            "novelty": 0.78,
                            "causal_alignment": 0.82,
                        },
                        "sandbox_pressure": 0.7492,
                        "sandbox_policy": "quarantine_then_review",
                    },
                ],
            },
        },
    }

    rehearsal = CausalRehearsal()
    legitimacy = SemanticLegitimacyEngine()
    permissioning = AdaptivePermissioning()

    context["causal_rehearsal_report"] = rehearsal.run_cycle(
        context,
    )

    context["semantic_legitimacy_report"] = legitimacy.run_cycle(
        context,
    )

    report = permissioning.run_cycle(
        context,
    )

    assert (
        context["causal_rehearsal_report"][
            "rehearsal_state"
        ]
        ==
        "constructive_evolution_rehearsed"
    )

    assert (
        context["semantic_legitimacy_report"][
            "legitimacy_state"
        ]
        ==
        "legitimate"
    )

    assert report["commit_probability"] >= 0.35

    assert (
        report["cognitive_reputation"][
            "average_reputation"
        ]
        >
        0.049
    )

    assert (
        report["cognitive_reputation"][
            "reputation_state"
        ]
        in [
            "forming",
            "established",
        ]
    )
