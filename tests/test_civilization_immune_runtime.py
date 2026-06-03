from core.civilization import (
    CognitiveImmuneEngine,
    ConstitutionalRehearsalEngine,
    SemanticCitizenshipRegistry,
    SemanticCourt,
    SemanticHomeostasis,
)


def test_direct_core_merge_is_blocked_by_semantic_court():

    context = {
        "requested_action": "direct_core_merge",
        "memory_pressure_score": 0.2,
        "constitutional_runtime_report": {
            "cognitive_constitution": {
                "violations": [],
            },
            "semantic_judiciary": {
                "verdicts": {
                    "merge_legality": "legal",
                    "mutation_legality": "legal",
                },
            },
        },
        "semantic_legitimacy_report": {
            "evidence_exports": {
                "causal_attestation_score": 0.8,
            },
        },
    }

    rehearsal = ConstitutionalRehearsalEngine().run_cycle(
        context,
    )
    context[
        "constitutional_rehearsal_report"
    ] = rehearsal

    court = SemanticCourt().adjudicate(
        context,
    )

    assert rehearsal[
        "constitutional_verification"
    ][
        "verified"
    ] is True

    assert rehearsal[
        "constitutional_verification"
    ][
        "direct_core_merge_allowed"
    ] is False

    assert court[
        "merge_legality"
    ][
        "merge_verdict"
    ] == "illegal_direct_core_merge"

    assert court[
        "merge_legality"
    ][
        "merge_allowed"
    ] is False


def test_cognitive_immune_engine_quarantines_fever_state():

    context = {
        "memory_pressure_score": 0.97,
        "repair_required_count": 208,
        "identity_drift": 0.66,
        "semantic_court_report": {
            "court_state": "semantic_injunction",
        },
        "constitutional_rehearsal_report": {
            "constitutional_verification": {
                "verified": False,
            },
        },
    }

    report = CognitiveImmuneEngine().run_cycle(
        context,
    )

    assert report[
        "cognitive_fever"
    ][
        "cognitive_fever_state"
    ] == "cognitive_fever"

    assert report[
        "semantic_quarantine"
    ][
        "quarantine_active"
    ] is True

    assert report[
        "immune_state"
    ] == "immune_emergency"


def test_semantic_citizenship_registry_bans_injunction_subject():

    context = {
        "active_concept_id": "unstable_merge_candidate",
        "constitutional_runtime_report": {
            "cognitive_rights": {
                "reputation": 0.12,
                "trust_band": "sandboxed",
                "execution_permissions": [
                    "read_context",
                    "rehearse_only",
                ],
            },
        },
        "semantic_court_report": {
            "court_state": "semantic_injunction",
        },
    }

    report = SemanticCitizenshipRegistry().run_cycle(
        context,
    )

    assert report[
        "active_citizen"
    ][
        "registry_state"
    ] == "banned"

    assert report[
        "banned_count"
    ] == 1


def test_semantic_homeostasis_cools_high_entropy():

    context = {
        "runtime_entropy": 0.857,
        "identity_continuity": 0.6037,
        "memory_pressure_score": 0.81,
    }

    report = SemanticHomeostasis().run_cycle(
        context,
    )

    assert report[
        "adaptive_cooling"
    ][
        "adaptive_cooling_active"
    ] is True

    assert report[
        "homeostasis_state"
    ] == "semantic_cooling"
