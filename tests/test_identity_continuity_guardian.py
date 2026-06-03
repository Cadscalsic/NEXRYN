from core.identity.continuity_guardian import (
    IdentityContinuityGuardian,
)


def test_identity_continuity_guardian_blocks_catastrophic_rewrite():

    guardian = IdentityContinuityGuardian()

    stable_context = {
        "identity_continuity":
        0.82,

        "identity_stability_report":
        {
            "stable_snapshot":
            {
                "identity_drift":
                0.08,
            },

            "continuity_verifier":
            {
                "continuity_score":
                0.82,
            },

            "identity_diff":
            {
                "identity_shift":
                0.08,
            },
        },

        "cognitive_homeostasis_report":
        {
            "semantic_drift_detection":
            {
                "semantic_drift":
                0.12,
            },
        },
    }

    guardian.run_cycle(
        stable_context,
    )

    unsafe_context = {
        "identity_continuity":
        0.41,

        "identity_stability_report":
        {
            "stable_snapshot":
            {
                "identity_drift":
                0.08,
            },

            "continuity_verifier":
            {
                "continuity_score":
                0.41,
            },

            "identity_diff":
            {
                "identity_shift":
                0.70,
            },
        },

        "cognitive_homeostasis_report":
        {
            "semantic_drift_detection":
            {
                "semantic_drift":
                0.72,
            },
        },

        "cognitive_natural_selection_report":
        {
            "extinct_count":
            3,

            "suppressed_count":
            2,
        },
    }

    report = guardian.run_cycle(
        unsafe_context,
    )

    assert (
        report["catastrophic_rewrite_guard"][
            "block_rewrite"
        ]
        is True
    )
    assert report["rollback"]["rollback_required"] is True
    assert (
        "restore_stable_identity_snapshot"
        in report["rollback"]["rollback_actions"]
    )
    assert report["identity_guardian_state"] == "rollback_required"
