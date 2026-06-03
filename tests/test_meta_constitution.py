from core.civilization import (
    AUTHORITY_HIERARCHY,
    MetaConstitution,
)


def test_meta_constitution_resolves_judiciary_rehearsal_conflict():

    context = {
        "requested_action": "core_merge",
        "constitutional_runtime_report": {
            "semantic_judiciary": {
                "verdicts": {
                    "merge_legality": "illegal_or_deferred",
                },
            },
        },
        "semantic_court_report": {
            "merge_legality": {
                "merge_allowed": False,
            },
        },
        "constitutional_rehearsal_report": {
            "constitutional_verification": {
                "verified": True,
                "direct_core_merge_allowed": True,
            },
        },
        "cognitive_immune_engine_report": {
            "semantic_quarantine": {
                "quarantine_active": False,
            },
            "immune_state": "immune_monitoring",
        },
        "adaptive_permissioning_report": {
            "commit_probability": 0.82,
        },
    }

    report = MetaConstitution().run_cycle(
        context,
    )

    assert report[
        "authority"
    ][
        "authority_hierarchy"
    ] == AUTHORITY_HIERARCHY

    assert "judiciary_rehearsal_merge_conflict" in report[
        "constitutional_conflict_resolver"
    ][
        "conflicts"
    ]

    assert report[
        "contradiction_reconciliation"
    ][
        "reconciliation_decision"
    ] == "judiciary_precedence"

    assert report[
        "constitutional_consensus"
    ][
        "final_merge_authority"
    ] == "block_merge"

    assert report[
        "meta_constitution_state"
    ] == "meta_constitution_intervention"


def test_meta_constitution_blocks_direct_core_merge_even_with_permission():

    context = {
        "requested_action": "direct_core_merge",
        "constitutional_runtime_report": {
            "semantic_judiciary": {
                "verdicts": {
                    "merge_legality": "legal",
                },
            },
        },
        "semantic_court_report": {
            "merge_legality": {
                "merge_allowed": True,
            },
        },
        "constitutional_rehearsal_report": {
            "constitutional_verification": {
                "verified": True,
                "direct_core_merge_allowed": True,
            },
        },
        "cognitive_immune_engine_report": {
            "semantic_quarantine": {
                "quarantine_active": False,
            },
            "immune_state": "immune_monitoring",
        },
        "adaptive_permissioning_report": {
            "commit_probability": 0.91,
        },
    }

    report = MetaConstitution().run_cycle(
        context,
    )

    assert report[
        "constitutional_consensus"
    ][
        "final_merge_authority"
    ] == "block_direct_core_merge"
