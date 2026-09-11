from runtime.governance.locked_truth_fastpath import LockedTruthFastPath
from runtime.truth.current_truth_admission import CurrentTruthAdmissionGate
from runtime.truth.truth_current_authority_lifecycle import (
    TruthCurrentAuthorityLifecycleEngine,
)


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


def test_locked_stable_truth_activates_fastpath(tmp_path):
    engine = TruthCurrentAuthorityLifecycleEngine(tmp_path)
    state = engine.create_active_truth(
        truth_id="truth:color_preservation",
        claim_id="claim:color_preservation",
    )
    engine.persist_current_state(state)
    report = LockedTruthFastPath().evaluate(
        "color_preservation",
        _locked_context(**state),
    )

    report = LockedTruthFastPath(
        admission_gate=CurrentTruthAdmissionGate(engine)
    ).evaluate("color_preservation", _locked_context(**state))

    assert report["fastpath_active"] is True
    assert report["truth_reused"] is True
    assert report["governance_revalidation_skipped"] is True
    assert "truth_commit_review" in report["skipped_modules"]


def test_contradiction_review_disables_fastpath():
    report = {
        "truth_id": "truth:legacy",
        "current_truth_decision_id": "old",
        "claim_id": "claim:legacy",
    }
    report = LockedTruthFastPath().evaluate(
        "color_preservation",
        _locked_context(**report, contradiction_review_required=True),
    )

    assert report["fastpath_active"] is False
    assert report["reason"] == "DENIED_TRUTH_CURRENT_AUTHORITY_UNVERIFIED"


def test_unstable_identity_disables_fastpath():
    engine = TruthCurrentAuthorityLifecycleEngine()
    state = engine.create_active_truth(
        truth_id="truth:color_preservation",
        claim_id="claim:color_preservation",
    )
    report = LockedTruthFastPath(
        admission_gate=CurrentTruthAdmissionGate(_MemoryCurrentStateEngine(state))
    ).evaluate(
        "color_preservation",
        _locked_context(
            **state,
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
    engine = TruthCurrentAuthorityLifecycleEngine()
    state = engine.create_active_truth(
        truth_id="truth:color_preservation",
        claim_id="claim:color_preservation",
    )
    report = LockedTruthFastPath(
        admission_gate=CurrentTruthAdmissionGate(_MemoryCurrentStateEngine(state))
    ).evaluate(
        "color_preservation",
        _locked_context(**state, failed_gates=["contextual_truth_gap"]),
    )

    assert report["fastpath_active"] is False
    assert report["reason"] == "failed_gates"


class _MemoryCurrentStateEngine:
    authority = "TRUTH_CURRENT_AUTHORITY"

    def __init__(self, state):
        self.state = state

    def get_current_truth_state(self, truth_id):
        if truth_id == self.state["truth_id"]:
            return dict(self.state)
        return None
