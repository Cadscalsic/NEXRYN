import pytest

from runtime.truth import (
    TruthCurrentAuthorityLifecycleEngine,
    TruthLifecycleStatus,
)


def _support(*, sufficient=True, contradictory=False, source="PROVEN", causal="CURRENT"):
    return {
        "accepted_evidence_ids": ["E1", "E2", "E3"] if sufficient else [],
        "epistemic_assessment_ids": ["A1"],
        "truth_candidate_ids": ["TC1"],
        "source_identities": ["S1", "S2", "S3"] if source == "PROVEN" else ["S1"],
        "causal_support_refs": ["C1"] if causal == "CURRENT" else [],
        "current_support_sufficient": sufficient,
        "source_independence_state": source,
        "causal_support_state": causal,
        "contradictory_current_support": contradictory,
    }


def _active(engine, truth_id="truth:T1", claim_id="claim:T1", support=None):
    state = engine.create_active_truth(
        truth_id=truth_id,
        claim_id=claim_id,
        truth_candidate_id="truth_candidate:T1",
        support=support or _support(),
        confidence=0.91,
    )
    return state


def test_active_truth_current_state_and_history_round_trip(tmp_path):
    engine = TruthCurrentAuthorityLifecycleEngine(tmp_path)
    state = _active(engine)
    engine.persist_current_state(state)

    loaded = engine.get_current_truth_state("truth:T1")

    assert loaded["lifecycle_status"] == TruthLifecycleStatus.ACTIVE.value
    assert engine.is_truth_current("truth:T1") is True
    assert engine.get_truth_history("truth:T1")[0]["current_state"]["truth_id"] == (
        "truth:T1"
    )


def test_stale_support_signal_opens_review_without_direct_invalidation(tmp_path):
    engine = TruthCurrentAuthorityLifecycleEngine(tmp_path)
    active = _active(engine)
    signal = engine.support_change_review_signal(
        active,
        trigger="SUPPORTING_EPISTEMIC_ASSESSMENT_STALE",
        upstream_report={"assessment_current_state": "STALE_EPISTEMIC_ASSESSMENT"},
    )
    review = signal["truth_review_decision"]
    reviewed = engine.current_state_from_decision(active, review)

    assert signal["direct_truth_mutation"] is False
    assert reviewed["lifecycle_status"] == TruthLifecycleStatus.UNDER_REVIEW.value
    assert reviewed["truth_under_review"] is True
    assert reviewed["truth_invalidated"] is False


def test_full_support_loss_requires_review_then_authoritative_invalidation(tmp_path):
    engine = TruthCurrentAuthorityLifecycleEngine(tmp_path)
    active = _active(engine)
    review = engine.open_review(
        active,
        review_trigger="SUPPORTING_EVIDENCE_REVOKED",
        support_signal={"revoked_evidence_ids": ["E1", "E2", "E3"]},
    )
    reviewed = engine.current_state_from_decision(active, review)
    invalidation = engine.invalidate_truth(
        reviewed,
        reason="all_current_support_lost",
        current_support=_support(sufficient=False),
    )
    invalidated = engine.current_state_from_decision(reviewed, invalidation)

    assert invalidated["lifecycle_status"] == TruthLifecycleStatus.INVALIDATED.value
    assert invalidated["truth_invalidated"] is True
    assert invalidated["current_authority_status"] == "NO_CURRENT_ACTIVE_TRUTH_AUTHORITY"


def test_partial_support_loss_can_restore_active_after_reassessment(tmp_path):
    engine = TruthCurrentAuthorityLifecycleEngine(tmp_path)
    active = _active(engine)
    review = engine.open_review(
        active,
        review_trigger="SUPPORTING_EVIDENCE_REVOKED",
        support_signal={"revoked_evidence_ids": ["E2"]},
    )
    reviewed = engine.current_state_from_decision(active, review)
    reassessment = engine.reassess_under_review(
        reviewed,
        current_support={
            **_support(sufficient=True),
            "accepted_evidence_ids": ["E1", "E3"],
        },
    )
    restored = engine.current_state_from_decision(reviewed, reassessment)

    assert restored["lifecycle_status"] == TruthLifecycleStatus.ACTIVE.value
    assert restored["support_dependency_graph"]["accepted_evidence_ids"] == [
        "E1",
        "E3",
    ]


def test_revalidation_requires_fresh_current_support_and_decision(tmp_path):
    engine = TruthCurrentAuthorityLifecycleEngine(tmp_path)
    active = _active(engine)
    reviewed = engine.current_state_from_decision(
        active,
        engine.open_review(active, review_trigger="GOVERNANCE_REVIEW_REQUIRED"),
    )
    invalidated = engine.current_state_from_decision(
        reviewed,
        engine.invalidate_truth(reviewed, reason="support_lost"),
    )

    with pytest.raises(ValueError, match="fresh_current_truth_support_required"):
        engine.revalidate_truth(
            invalidated,
            current_support=_support(sufficient=False),
        )

    revalidation = engine.revalidate_truth(
        invalidated,
        current_support=_support(sufficient=True),
    )
    restored = engine.current_state_from_decision(invalidated, revalidation)

    assert restored["lifecycle_status"] == TruthLifecycleStatus.ACTIVE.value


def test_supersession_is_explicit_and_preserves_history(tmp_path):
    engine = TruthCurrentAuthorityLifecycleEngine(tmp_path)
    active = _active(engine)
    supersession, replacement = engine.supersede_truth(
        active,
        replacement_truth_id="truth:T2",
        replacement_claim_id="claim:T2",
        reason="explicit_replacement_relation",
        replacement_support=_support(),
    )
    superseded = engine.current_state_from_decision(active, supersession)
    engine.persist_current_state(superseded, lifecycle_decision=supersession)
    engine.persist_current_state(replacement)

    assert superseded["lifecycle_status"] == TruthLifecycleStatus.SUPERSEDED.value
    assert replacement["lifecycle_status"] == TruthLifecycleStatus.ACTIVE.value
    assert engine.get_truth_history("truth:T1")


def test_stale_truth_replay_and_out_of_order_decisions_fail_closed(tmp_path):
    engine = TruthCurrentAuthorityLifecycleEngine(tmp_path)
    active = _active(engine)
    old_active = dict(active)
    engine.persist_current_state(active)
    reviewed = engine.current_state_from_decision(
        active,
        engine.open_review(active, review_trigger="GOVERNANCE_REVIEW_REQUIRED"),
    )
    invalidated = engine.current_state_from_decision(
        reviewed,
        engine.invalidate_truth(reviewed, reason="support_lost"),
    )
    engine.persist_current_state(invalidated)
    stale_path = tmp_path / "current_truth_state" / "truth:T1.json"
    stale_path.write_text(__import__("json").dumps(old_active), encoding="utf-8")

    assert engine.get_current_truth_state("truth:T1") is None
    with pytest.raises(ValueError, match="out_of_order_truth_decision_rejected"):
        engine.current_state_from_decision(
            invalidated,
            engine.invalidate_truth(reviewed, reason="stale_invalidation_replay"),
        )


def test_cross_truth_claim_and_corrupted_decisions_fail_closed(tmp_path):
    engine = TruthCurrentAuthorityLifecycleEngine(tmp_path)
    active = _active(engine)
    review = engine.open_review(active, review_trigger="GOVERNANCE_REVIEW_REQUIRED")
    wrong_truth = dict(review)
    wrong_truth["truth_id"] = "truth:other"
    wrong_truth["decision_fingerprint"] = engine._fingerprint(wrong_truth)
    wrong_claim = dict(review)
    wrong_claim["claim_id"] = "claim:other"
    wrong_claim["decision_fingerprint"] = engine._fingerprint(wrong_claim)
    corrupted = dict(review)
    corrupted["decision_fingerprint"] = "corrupted"

    with pytest.raises(ValueError, match="cross_truth_decision_rejected"):
        engine.current_state_from_decision(active, wrong_truth)
    with pytest.raises(ValueError, match="cross_claim_decision_rejected"):
        engine.current_state_from_decision(active, wrong_claim)
    with pytest.raises(ValueError, match="corrupted_truth_decision_fingerprint"):
        engine.current_state_from_decision(active, corrupted)


def test_source_causal_and_contradiction_triggers_open_review(tmp_path):
    engine = TruthCurrentAuthorityLifecycleEngine(tmp_path)
    active = _active(engine)

    for trigger in (
        "SOURCE_INDEPENDENCE_COLLAPSED",
        "CAUSAL_SUPPORT_WITHDRAWN",
        "CONTRADICTORY_CURRENT_SUPPORT",
    ):
        review = engine.open_review(
            active,
            review_trigger=trigger,
            support_signal={"trigger": trigger},
        )
        assert review["review_trigger"] == trigger
        assert review["authority"]["truth_current_authority"] == engine.authority
        assert review["authority"]["knowledge"] == "NONE"
