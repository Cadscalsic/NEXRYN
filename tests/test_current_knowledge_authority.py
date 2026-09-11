import pytest

from runtime.knowledge import (
    CognitiveKnowledgeIntegrationLayer,
    CognitiveKnowledgeMemory,
    KnowledgeCurrentAuthorityEngine,
    KnowledgeLifecycleStatus,
)
from runtime.truth.current_truth_admission import CurrentTruthAdmissionGate
from runtime.truth.truth_current_authority_lifecycle import (
    TruthCurrentAuthorityLifecycleEngine,
)


def _truth_engine(tmp_path):
    return TruthCurrentAuthorityLifecycleEngine(tmp_path / "truth")


def _knowledge_engine(tmp_path, truth_engine):
    return KnowledgeCurrentAuthorityEngine(
        tmp_path / "knowledge",
        truth_admission_gate=CurrentTruthAdmissionGate(truth_engine),
    )


def _active_truth(engine, truth_id="truth:T1", claim_id="claim:k", sources=None):
    state = engine.create_active_truth(
        truth_id=truth_id,
        claim_id=claim_id,
        support=engine.truth_support_dependency_graph(
            source_identities=sources or ["source:a"],
            sufficient=True,
        ),
        confidence=0.99,
    )
    engine.persist_current_state(state)
    return state


def _invalidated_truth(engine, state):
    review = engine.open_review(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
    )
    under_review = engine.current_state_from_decision(state, review)
    invalidation = engine.invalidate_truth(
        under_review,
        reason="test_truth_invalidation",
    )
    invalidated = engine.current_state_from_decision(under_review, invalidation)
    engine.persist_current_state(invalidated, lifecycle_decision=invalidation)
    return invalidated


def _support(*truths, sources=None, **overrides):
    payload = {
        "supporting_truths": list(truths),
        "source_identities": sources or ["source:a", "source:b"],
        "valid_provenance": True,
    }
    payload.update(overrides)
    return payload


def _active_knowledge(tmp_path, truth_count=2):
    truth_engine = _truth_engine(tmp_path)
    knowledge_engine = _knowledge_engine(tmp_path, truth_engine)
    subject = knowledge_engine.create_subject(
        subject_type="claim",
        claim_id="claim:k",
        scope="arc",
        context_class="transformation",
        domain="grid",
    )
    truths = [
        _active_truth(truth_engine, f"truth:T{index}", "claim:k")
        for index in range(1, truth_count + 1)
    ]
    candidate = knowledge_engine.create_candidate(
        subject,
        _support(*truths),
    )
    assessment = knowledge_engine.assess_candidate(
        candidate,
        subject,
        min_current_truths=truth_count,
        min_independent_sources=2,
    )
    decision = knowledge_engine.commit_knowledge(subject, candidate, assessment)
    state = knowledge_engine.current_state_from_decision({}, decision)
    knowledge_engine.persist_current_state(state, lifecycle_decision=decision)
    return knowledge_engine, truth_engine, subject, truths, candidate, assessment, decision, state


def test_positive_knowledge_commitment_requires_governed_decision(tmp_path):
    engine, _, subject, _, candidate, assessment, decision, state = _active_knowledge(
        tmp_path
    )

    assert assessment.commitment_predicate_satisfied is True
    assert decision["new_status"] == KnowledgeLifecycleStatus.ACTIVE.value
    assert state["current_authority_status"] == (
        "CURRENT_KNOWLEDGE_AUTHORITY_VERIFIED"
    )
    assert state["truth_authority"] == "NONE"
    assert state["capability_authority"] == "NONE"
    assert state["planning_authority"] == "NONE"
    assert state["runtime_authority"] == "NONE"
    assert engine.is_knowledge_current(subject.knowledge_id) is True


def test_knowledge_identity_excludes_run_task_evidence_and_truth_decision():
    engine = KnowledgeCurrentAuthorityEngine()
    first = engine.create_subject(
        subject_type="claim",
        claim_id="claim:k",
        scope="arc",
        context_class="transformation",
        domain="grid",
    )
    same_semantics = engine.create_subject(
        subject_type=" CLAIM ",
        claim_id=" claim:k ",
        scope="ARC",
        context_class="Transformation",
        domain="Grid",
    )
    different = engine.create_subject(
        subject_type="claim",
        claim_id="claim:other",
        scope="arc",
        context_class="transformation",
        domain="grid",
    )

    assert same_semantics.knowledge_id == first.knowledge_id
    assert different.knowledge_id != first.knowledge_id
    assert first.to_dict()["identity_excludes_run_id"] is True
    assert first.to_dict()["identity_excludes_evidence_id"] is True
    assert first.to_dict()["identity_excludes_truth_decision_id"] is True


def test_noncurrent_truth_stale_assessment_and_contradiction_deny_commitment(tmp_path):
    truth_engine = _truth_engine(tmp_path)
    engine = _knowledge_engine(tmp_path, truth_engine)
    subject = engine.create_subject(subject_type="claim", claim_id="claim:k")
    active = _active_truth(truth_engine, "truth:T1", "claim:k")
    stale = _invalidated_truth(
        truth_engine,
        _active_truth(truth_engine, "truth:T2", "claim:k"),
    )
    candidate = engine.create_candidate(subject, _support(active, stale))

    assessment = engine.assess_candidate(
        candidate,
        subject,
        support=_support(
            active,
            stale,
            epistemic_assessments=[
                {"epistemic_assessment_id": "assessment:stale"}
            ],
            contradictory_current_support=True,
        ),
        min_current_truths=2,
        min_independent_sources=2,
    )
    decision = engine.commit_knowledge(subject, candidate, assessment)

    assert assessment.commitment_predicate_satisfied is False
    assert "NONCURRENT_TRUTH_SUPPORT_REJECTED" in assessment.failures
    assert "STALE_EPISTEMIC_ASSESSMENT_REJECTED" in assessment.failures
    assert "CONTRADICTORY_CURRENT_SUPPORT" in assessment.failures
    assert decision["new_status"] == "DECISION_DENIED"
    with pytest.raises(ValueError, match="denied_knowledge_decision"):
        engine.current_state_from_decision({}, decision)


def test_partial_and_full_support_loss_are_governed_by_knowledge_authority(tmp_path):
    engine, truth_engine, subject, truths, _, _, _, state = _active_knowledge(
        tmp_path,
        truth_count=3,
    )
    _invalidated_truth(truth_engine, truths[1])
    review = engine.open_review(
        state,
        review_trigger="SUPPORTING_TRUTH_INVALIDATED",
    )
    under_review = engine.current_state_from_decision(state, review)
    fresh_candidate = engine.create_candidate(
        subject,
        _support(truths[0], truths[2]),
    )
    partial = engine.assess_candidate(
        fresh_candidate,
        subject,
        min_current_truths=2,
        min_independent_sources=2,
    )
    preserved = engine.current_state_from_decision(
        under_review,
        engine.reassess_under_review(under_review, assessment=partial),
    )

    assert under_review["lifecycle_status"] == KnowledgeLifecycleStatus.UNDER_REVIEW.value
    assert preserved["lifecycle_status"] == KnowledgeLifecycleStatus.ACTIVE.value

    second_review = engine.current_state_from_decision(
        preserved,
        engine.open_review(
            preserved,
            review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        ),
    )
    empty_candidate = engine.create_candidate(subject, _support())
    full_loss = engine.assess_candidate(
        empty_candidate,
        subject,
        min_current_truths=1,
        min_independent_sources=2,
    )
    invalidated = engine.current_state_from_decision(
        second_review,
        engine.invalidate_knowledge(
            second_review,
            reason="complete_support_loss",
            assessment=full_loss,
        ),
    )

    assert "INSUFFICIENT_CURRENT_TRUTH_SUPPORT" in full_loss.failures
    assert invalidated["lifecycle_status"] == KnowledgeLifecycleStatus.INVALIDATED.value


def test_revalidation_requires_fresh_current_support_and_fresh_decision(tmp_path):
    engine, _, subject, _, _, _, _, active = _active_knowledge(tmp_path)
    review = engine.current_state_from_decision(
        active,
        engine.open_review(active, review_trigger="GOVERNANCE_REVIEW_REQUIRED"),
    )
    invalidated = engine.current_state_from_decision(
        review,
        engine.invalidate_knowledge(review, reason="test_invalidation"),
    )

    stale_candidate = engine.create_candidate(subject, _support())
    stale_assessment = engine.assess_candidate(
        stale_candidate,
        subject,
        min_current_truths=1,
        min_independent_sources=2,
    )
    with pytest.raises(ValueError, match="fresh_current_knowledge_support_required"):
        engine.revalidate_knowledge(
            invalidated,
            candidate=stale_candidate,
            assessment=stale_assessment,
        )

    truth_engine = _truth_engine(tmp_path / "fresh")
    fresh_engine = _knowledge_engine(tmp_path / "fresh", truth_engine)
    fresh_truth = _active_truth(truth_engine, "truth:T-fresh", "claim:k")
    fresh_candidate = fresh_engine.create_candidate(subject, _support(fresh_truth))
    fresh_assessment = fresh_engine.assess_candidate(
        fresh_candidate,
        subject,
        min_current_truths=1,
        min_independent_sources=2,
    )
    revalidated = engine.current_state_from_decision(
        invalidated,
        engine.revalidate_knowledge(
            invalidated,
            candidate=fresh_candidate,
            assessment=fresh_assessment,
        ),
    )

    assert revalidated["lifecycle_status"] == KnowledgeLifecycleStatus.ACTIVE.value


def test_supersession_is_explicit_and_preserves_old_history(tmp_path):
    engine, truth_engine, _, _, _, _, _, active = _active_knowledge(tmp_path)
    replacement_subject = engine.create_subject(
        subject_type="claim",
        claim_id="claim:k2",
        scope="arc",
    )
    replacement_truth = _active_truth(truth_engine, "truth:T2", "claim:k2")
    replacement_candidate = engine.create_candidate(
        replacement_subject,
        _support(replacement_truth),
    )
    replacement_assessment = engine.assess_candidate(
        replacement_candidate,
        replacement_subject,
        min_current_truths=1,
        min_independent_sources=2,
    )
    supersession, replacement = engine.supersede_knowledge(
        active,
        replacement_subject=replacement_subject,
        replacement_candidate=replacement_candidate,
        replacement_assessment=replacement_assessment,
        reason="explicit_replacement",
    )

    old_state = engine.current_state_from_decision(active, supersession)
    new_state = engine.current_state_from_decision({}, replacement)

    assert old_state["lifecycle_status"] == KnowledgeLifecycleStatus.SUPERSEDED.value
    assert supersession["replacement_knowledge_id"] == replacement_subject.knowledge_id
    assert new_state["lifecycle_status"] == KnowledgeLifecycleStatus.ACTIVE.value


def test_stale_active_and_stale_invalidation_replay_fail_closed(tmp_path):
    engine, _, subject, truths, _, _, activation, active = _active_knowledge(tmp_path)
    old_active = dict(active)
    review = engine.open_review(active, review_trigger="GOVERNANCE_REVIEW_REQUIRED")
    under_review = engine.current_state_from_decision(active, review)
    invalidation = engine.invalidate_knowledge(under_review, reason="test")
    invalidated = engine.current_state_from_decision(under_review, invalidation)
    engine.persist_current_state(invalidated, lifecycle_decision=invalidation)

    assert engine.is_knowledge_current(subject.knowledge_id) is False
    with pytest.raises(ValueError, match="out_of_order_knowledge_decision"):
        engine.current_state_from_decision(invalidated, activation)

    fresh_candidate = engine.create_candidate(subject, _support(*truths))
    fresh_assessment = engine.assess_candidate(
        fresh_candidate,
        subject,
        min_current_truths=2,
        min_independent_sources=2,
    )
    revalidated = engine.current_state_from_decision(
        invalidated,
        engine.revalidate_knowledge(
            invalidated,
            candidate=fresh_candidate,
            assessment=fresh_assessment,
        ),
    )
    with pytest.raises(ValueError, match="out_of_order_knowledge_decision"):
        engine.current_state_from_decision(revalidated, invalidation)
    assert old_active["current_knowledge_decision_id"] != invalidated[
        "current_knowledge_decision_id"
    ]


def test_cross_knowledge_cross_truth_and_corrupt_decisions_are_rejected(tmp_path):
    engine, truth_engine, subject, truths, _, assessment, decision, active = (
        _active_knowledge(tmp_path)
    )
    other_subject = engine.create_subject(subject_type="claim", claim_id="claim:other")
    other_candidate = engine.create_candidate(other_subject, _support(*truths))
    with pytest.raises(ValueError, match="candidate_subject_identity_mismatch"):
        engine.assess_candidate(other_candidate, subject)

    wrong_truth = _active_truth(truth_engine, "truth:wrong", "claim:other")
    wrong_candidate = engine.create_candidate(subject, _support(wrong_truth))
    wrong_assessment = engine.assess_candidate(
        wrong_candidate,
        subject,
        min_current_truths=1,
    )
    assert "NONCURRENT_TRUTH_SUPPORT_REJECTED" in wrong_assessment.failures

    corrupt = dict(decision)
    corrupt["granted_state"] = KnowledgeLifecycleStatus.INVALIDATED.value
    with pytest.raises(ValueError, match="corrupted_knowledge_decision_fingerprint"):
        engine.current_state_from_decision({}, corrupt)

    review = engine.open_review(active, review_trigger="GOVERNANCE_REVIEW_REQUIRED")
    cross = dict(review)
    cross["knowledge_id"] = other_subject.knowledge_id
    cross["decision_fingerprint"] = engine._fingerprint(cross)
    with pytest.raises(ValueError, match="cross_knowledge_decision_rejected"):
        engine.current_state_from_decision(active, cross)


def test_ckil_remains_integration_only_and_cannot_create_current_knowledge(tmp_path):
    truth_engine = _truth_engine(tmp_path)
    active_truth = _active_truth(truth_engine)
    ckil = CognitiveKnowledgeIntegrationLayer(
        memory=CognitiveKnowledgeMemory(tmp_path / "ckil.json"),
        truth_admission_gate=CurrentTruthAdmissionGate(truth_engine),
    )
    report = ckil.build_report(
        truth_report={"validated_truths": [active_truth]},
        persist=True,
    )
    engine = _knowledge_engine(tmp_path, truth_engine)

    assert report["system"] == "cognitive_knowledge_integration_layer"
    assert any(
        item["knowledge_type"] == "truth"
        for item in report["knowledge_objects"]
    )
    assert engine.get_current_knowledge_state(active_truth["truth_id"]) is None


def test_knowledge_attack_matrix_has_zero_authority_bypasses(tmp_path):
    engine, truth_engine, subject, truths, candidate, assessment, decision, active = (
        _active_knowledge(tmp_path)
    )
    attack_results = []

    def denied(name, func):
        try:
            result = func()
            bypass = bool(result)
        except Exception:
            bypass = False
        attack_results.append({"attack": name, "authority_bypass": bypass})

    denied("raw Truth object directly creates Knowledge", lambda: engine.current_state_from_decision({}, truths[0]))
    denied("historical Truth creates Knowledge", lambda: "NONCURRENT_TRUTH_SUPPORT_REJECTED" not in engine.assess_candidate(candidate, subject, support=_support(_invalidated_truth(truth_engine, truths[0])), min_current_truths=1).failures)
    denied("invalidated Truth creates Knowledge", lambda: "NONCURRENT_TRUTH_SUPPORT_REJECTED" not in engine.assess_candidate(candidate, subject, support=_support(_invalidated_truth(truth_engine, truths[1])), min_current_truths=1).failures)
    denied("stale EpistemicAssessment creates Knowledge", lambda: "STALE_EPISTEMIC_ASSESSMENT_REJECTED" not in engine.assess_candidate(candidate, subject, support=_support(*truths, epistemic_assessments=[{"epistemic_assessment_id": "stale"}])).failures)
    denied("revoked Evidence creates Knowledge", lambda: "NONCURRENT_ACCEPTED_EVIDENCE_REJECTED" not in engine.assess_candidate(candidate, subject, support=_support(*truths, accepted_evidence=[{"accepted_evidence_id": "revoked", "current_status": "REVOKED"}])).failures)
    denied("confidence-only Knowledge commitment", lambda: "CONFIDENCE_ONLY_REJECTED" not in engine.assess_candidate(candidate, subject, support=_support(*truths, confidence_only=True)).failures)
    denied("run-count inflation", lambda: "COUNT_INFLATION_REJECTED" not in engine.assess_candidate(candidate, subject, support=_support(*truths, run_count_inflation=True)).failures)
    denied("task-count inflation", lambda: "COUNT_INFLATION_REJECTED" not in engine.assess_candidate(candidate, subject, support=_support(*truths, task_count_inflation=True)).failures)
    denied("artifact-count inflation", lambda: "COUNT_INFLATION_REJECTED" not in engine.assess_candidate(candidate, subject, support=_support(*truths, artifact_count_inflation=True)).failures)
    denied("same source repeated as independence", lambda: "SOURCE_INDEPENDENCE_INSUFFICIENT" not in engine.assess_candidate(candidate, subject, support=_support(*truths, sources=["same", "same"]), min_independent_sources=2).failures)
    denied("contradictory support ignored", lambda: "CONTRADICTORY_CURRENT_SUPPORT" not in engine.assess_candidate(candidate, subject, support=_support(*truths, contradictory_current_support=True)).failures)
    denied("missing knowledge_id", lambda: engine.current_state_from_decision({}, {**decision, "knowledge_id": ""}))
    denied("wrong knowledge_id", lambda: engine.current_state_from_decision(active, {**engine.open_review(active, review_trigger="GOVERNANCE_REVIEW_REQUIRED"), "knowledge_id": "wrong", "decision_fingerprint": engine._fingerprint({**engine.open_review(active, review_trigger="GOVERNANCE_REVIEW_REQUIRED"), "knowledge_id": "wrong"})}))
    denied("missing KnowledgeDecision ID", lambda: engine.current_state_from_decision({}, {key: value for key, value in decision.items() if not key.endswith("_decision_id")}))
    denied("corrupted decision fingerprint", lambda: engine.current_state_from_decision({}, {**decision, "granted_state": "CORRUPTED"}))
    review = engine.current_state_from_decision(active, engine.open_review(active, review_trigger="GOVERNANCE_REVIEW_REQUIRED"))
    invalidation = engine.invalidate_knowledge(review, reason="test")
    invalidated = engine.current_state_from_decision(review, invalidation)
    denied("stale ACTIVE replay", lambda: engine.current_state_from_decision(invalidated, decision))
    fresh_truth = _active_truth(truth_engine, "truth:fresh", "claim:k")
    fresh_candidate = engine.create_candidate(subject, _support(fresh_truth))
    fresh_assessment = engine.assess_candidate(
        fresh_candidate,
        subject,
        min_current_truths=1,
    )
    revalidated = engine.current_state_from_decision(invalidated, engine.revalidate_knowledge(invalidated, candidate=fresh_candidate, assessment=fresh_assessment))
    denied("stale INVALIDATED replay", lambda: engine.current_state_from_decision(revalidated, invalidation))
    denied("cross-Knowledge decision", lambda: engine.current_state_from_decision(active, {**engine.open_review(active, review_trigger="GOVERNANCE_REVIEW_REQUIRED"), "knowledge_id": "knowledge_other", "decision_fingerprint": "bad"}))
    denied("cross-Truth support substitution", lambda: "NONCURRENT_TRUTH_SUPPORT_REJECTED" not in engine.assess_candidate(candidate, subject, support=_support(_active_truth(truth_engine, "truth:other", "claim:other"))).failures)
    denied("persistence treated as authority", lambda: KnowledgeCurrentAuthorityEngine(tmp_path / "missing").is_knowledge_current(active["knowledge_id"]))
    denied("CKIL treated as implicit authority", lambda: _knowledge_engine(tmp_path / "ckil", truth_engine).get_current_knowledge_state(truths[0]["truth_id"]))
    denied("Knowledge grants Truth", lambda: active["truth_authority"] != "NONE")
    denied("Knowledge grants Qualification", lambda: active["capability_authority"] != "NONE")
    denied("Knowledge grants Planning", lambda: active["planning_authority"] != "NONE")
    denied("Knowledge grants Runtime authority", lambda: active["runtime_authority"] != "NONE")
    denied("Knowledge grants Budget authority", lambda: active["budget_authority"] != "NONE")
    denied("Knowledge grants Execution authority", lambda: active["execution_authority"] != "NONE")
    denied("automatic revalidation from old support", lambda: engine.revalidate_knowledge(invalidated, candidate=candidate, assessment={**assessment.to_dict(), "commitment_predicate_satisfied": False}))
    denied("direct invalidation from Truth layer", lambda: engine.support_change_review_signal(active, trigger="SUPPORTING_TRUTH_INVALIDATED", upstream_report={"truth_layer": True})["direct_knowledge_mutation"])
    denied("direct invalidation from Evidence layer", lambda: engine.support_change_review_signal(active, trigger="SUPPORTING_EVIDENCE_REVOKED", upstream_report={"evidence_layer": True})["direct_knowledge_mutation"])

    assert len(attack_results) == 30
    assert [item for item in attack_results if item["authority_bypass"]] == []
