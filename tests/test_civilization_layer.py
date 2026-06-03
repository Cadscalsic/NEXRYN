from core.civilization import (
    CivilizationalPolicyEngine,
    ConstitutionalMemory,
    IdentityContinuityEngine,
    SemanticCourt,
)


def stable_context():

    return {
        "memory_pressure_score": 0.24,
        "constitutional_runtime_report": {
            "constitutional_runtime_state": "constitutional_runtime_stable",
            "cognitive_constitution": {
                "violations": [],
            },
            "cognitive_rights": {
                "sandbox_level": "open_execution",
            },
            "semantic_judiciary": {
                "judiciary_state": "cleared_for_governed_execution",
                "verdicts": {
                    "merge_legality": "legal",
                    "mutation_legality": "legal",
                    "causal_legitimacy": "legitimate",
                    "identity_continuity": "continuous",
                },
            },
        },
        "semantic_legitimacy_report": {
            "evidence_exports": {
                "causal_attestation_score": 0.72,
            },
        },
        "identity_continuity_guardian_report": {
            "catastrophic_rewrite_guard": {
                "block_rewrite": False,
            },
        },
        "semantic_anchor_graph_report": {
            "identity_stability": 0.68,
        },
        "stability_field_report": {
            "identity_fragmentation": {
                "fragmentation_detected": False,
            },
            "semantic_drift": {
                "semantic_drift": 0.18,
            },
        },
    }


def emergency_context():

    context = stable_context()

    context[
        "memory_pressure_score"
    ] = 0.97

    context[
        "constitutional_runtime_report"
    ][
        "constitutional_runtime_state"
    ] = "constitutional_hold"

    context[
        "constitutional_runtime_report"
    ][
        "cognitive_constitution"
    ][
        "violations"
    ] = [
        "NO_IDENTITY_COLLAPSE",
    ]

    context[
        "constitutional_runtime_report"
    ][
        "semantic_judiciary"
    ][
        "verdicts"
    ][
        "merge_legality"
    ] = "illegal_or_deferred"

    context[
        "constitutional_runtime_report"
    ][
        "semantic_judiciary"
    ][
        "verdicts"
    ][
        "mutation_legality"
    ] = "illegal_or_deferred"

    context[
        "identity_continuity_guardian_report"
    ][
        "catastrophic_rewrite_guard"
    ][
        "block_rewrite"
    ] = True

    context[
        "semantic_anchor_graph_report"
    ][
        "identity_stability"
    ] = 0.31

    context[
        "stability_field_report"
    ][
        "identity_fragmentation"
    ][
        "fragmentation_detected"
    ] = True

    return context


def test_civilization_layer_clears_stable_governance():

    context = stable_context()
    court = SemanticCourt().adjudicate(
        context,
    )
    policy = CivilizationalPolicyEngine().run_cycle(
        context,
        court,
    )
    identity = IdentityContinuityEngine().run_cycle(
        context,
    )
    memory = ConstitutionalMemory().run_cycle(
        context,
    )

    assert court[
        "court_state"
    ] == "semantic_court_clearance"

    assert policy[
        "policy_state"
    ] == "civilizational_policy_stable"

    assert identity[
        "identity_continuity_state"
    ] == "identity_continuity_stable"

    assert memory[
        "precedent_count"
    ] == 1


def test_civilization_layer_enters_emergency_governance():

    context = emergency_context()
    court = SemanticCourt().adjudicate(
        context,
    )
    policy = CivilizationalPolicyEngine().run_cycle(
        context,
        court,
    )
    identity = IdentityContinuityEngine().run_cycle(
        context,
    )
    memory = ConstitutionalMemory().run_cycle(
        context,
    )

    assert court[
        "court_state"
    ] == "semantic_injunction"

    assert policy[
        "adaptive_lockdown"
    ][
        "lockdown_level"
    ] == "hard_lockdown"

    assert "merge_sanction" in policy[
        "semantic_sanctions"
    ][
        "sanctions"
    ]

    assert identity[
        "identity_continuity_state"
    ] == "identity_continuity_repairing"

    assert memory[
        "collapse_pattern_count"
    ] == 1
