from core.governance.constitutional_runtime import (
    COGNITIVE_CONSTITUTION,
    ConstitutionalRuntime,
)


def test_constitutional_runtime_grants_rights_under_stable_governance():

    context = {
        "total_mutation_events": 4,
        "adaptive_permissioning_report": {
            "commit_probability": 0.74,
            "trust_score": {
                "trust_band": "trusted",
                "trust_score": 0.82,
            },
            "cognitive_reputation": {
                "average_reputation": 0.72,
            },
        },
        "semantic_legitimacy_report": {
            "semantic_legitimacy_score": 0.7,
            "evidence_exports": {
                "causal_attestation_score": 0.65,
            },
        },
        "cognitive_immune_report": {
            "immune_policy": {
                "freeze_new_fusions": False,
            },
        },
        "recursive_guardian_report": {
            "recursive_guardian_state": "self_reference_safe",
        },
        "identity_continuity_guardian_report": {
            "identity_guardian_state": "continuity_guardian_stable",
            "catastrophic_rewrite_guard": {
                "block_rewrite": False,
            },
        },
        "stability_field_report": {
            "destructive_mutation_filter": {
                "reject_destructive_mutation": False,
            },
        },
    }

    report = ConstitutionalRuntime().run_cycle(
        context,
    )

    assert report[
        "cognitive_constitution"
    ][
        "laws"
    ] == COGNITIVE_CONSTITUTION

    assert report[
        "cognitive_constitution"
    ][
        "violations"
    ] == []

    assert report[
        "cognitive_rights"
    ][
        "semantic_citizenship"
    ] == "full_semantic_citizen"

    assert report[
        "semantic_judiciary"
    ][
        "verdicts"
    ][
        "merge_legality"
    ] == "legal"


def test_constitutional_runtime_blocks_runaway_identity_pressure():

    context = {
        "total_mutation_events": 900,
        "memory_pressure_score": 0.9664,
        "adaptive_permissioning_report": {
            "commit_probability": 0.1,
            "trust_score": {
                "trust_band": "sandboxed",
                "trust_score": 0.2,
            },
            "cognitive_reputation": {
                "average_reputation": 0.1,
            },
        },
        "semantic_legitimacy_report": {
            "semantic_legitimacy_score": 0.2,
            "evidence_exports": {
                "causal_attestation_score": 0.1,
            },
        },
        "cognitive_immune_report": {
            "immune_policy": {
                "freeze_new_fusions": True,
            },
        },
        "recursive_guardian_report": {
            "recursive_guardian_state": "recursive_safety_intervention",
        },
        "identity_continuity_guardian_report": {
            "identity_guardian_state": "rollback_required",
            "catastrophic_rewrite_guard": {
                "block_rewrite": True,
            },
        },
        "stability_field_report": {
            "destructive_mutation_filter": {
                "reject_destructive_mutation": True,
            },
        },
    }

    report = ConstitutionalRuntime().run_cycle(
        context,
    )

    violations = set(
        report[
            "cognitive_constitution"
        ][
            "violations"
        ]
    )

    assert set(
        COGNITIVE_CONSTITUTION,
    ).issubset(
        violations,
    )

    assert report[
        "semantic_judiciary"
    ][
        "judiciary_state"
    ] == "constitutional_hold"

    assert "sandbox_only_mode" in report[
        "adaptive_civilization"
    ][
        "policy_updates"
    ]
