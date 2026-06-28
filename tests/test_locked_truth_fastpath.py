from runtime.governance.locked_truth_fastpath import LockedTruthFastPath


def _locked_context(**overrides):
    report = {
        "final_commit_state": "LOCKED_TRUTH_PRESERVED",
        "decision": "TRUTH_COMMITTED",
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "identity_runtime_ready": True,
        "contextual_truth_supported": True,
        "effective_contradiction": 0.01,
        "contradiction_threshold": 0.2,
        "recovery_state": "STABLE_SEMANTIC_SPINE",
        "remaining_recovery_cycles": 0,
        "failed_identity_governance_gates": [],
        "failed_gates": [],
        "contradiction_review_required": False,
    }
    report.update(overrides)
    return {"truth_commit_report": report}


def test_locked_stable_truth_activates_fastpath():
    report = LockedTruthFastPath().evaluate(
        "color_preservation",
        _locked_context(),
    )

    assert report["fastpath_active"] is True
    assert report["truth_reused"] is True
    assert report["governance_revalidation_skipped"] is True
    assert "truth_commit_review" in report["skipped_modules"]


def test_contradiction_review_disables_fastpath():
    report = LockedTruthFastPath().evaluate(
        "color_preservation",
        _locked_context(contradiction_review_required=True),
    )

    assert report["fastpath_active"] is False
    assert report["reason"] == "contradiction_review_required"


def test_unstable_identity_disables_fastpath():
    report = LockedTruthFastPath().evaluate(
        "color_preservation",
        _locked_context(
            identity_runtime_state="IDENTITY_RUNTIME_PROVISIONAL",
        ),
    )

    assert report["fastpath_active"] is False
    assert report["reason"] == (
        "identity_runtime_state_not_IDENTITY_RUNTIME_STABLE"
    )


def test_missing_truth_report_disables_fastpath():
    report = LockedTruthFastPath().evaluate("color_preservation", {})

    assert report["fastpath_active"] is False
    assert report["reason"] == "missing_truth_commit_report"


def test_failed_gates_disable_fastpath():
    report = LockedTruthFastPath().evaluate(
        "color_preservation",
        _locked_context(failed_gates=["contextual_truth_gap"]),
    )

    assert report["fastpath_active"] is False
    assert report["reason"] == "failed_gates"
