from copy import deepcopy

import pytest

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from runtime.validation.accepted_evidence_lifecycle import (
    AcceptedEvidenceLifecycleEngine,
    AcceptedEvidenceLifecycleStatus,
)
from tests.test_integrated_capability_qualification import _accepted, _subject


def _engine_state(tmp_path):
    engine = AcceptedEvidenceLifecycleEngine(tmp_path)
    evidence = _accepted("accepted_evidence_a")
    state = engine.initialize_current_state(evidence)
    engine.persist_current_state(state)
    return engine, evidence, state


def _trigger(evidence_id="accepted_evidence_a", **overrides):
    payload = {
        "accepted_evidence_id": evidence_id,
        "evidence_acceptance_state": "ACCEPTED",
        "source_provenance": {"source_provenance_state": "SOURCE_PROVENANCE_BOUND"},
    }
    payload.update(overrides)
    return payload


def _reviewed(tmp_path, trigger="GOVERNANCE_REVIEW_REQUIRED"):
    engine, evidence, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger=trigger,
        trigger_evidence=_trigger(state["evidence_id"]),
    )
    reviewed = engine.current_state_from_lifecycle_decision(state, review)
    engine.persist_current_state(reviewed, lifecycle_decision=review)
    return engine, evidence, state, review, reviewed


def test_positive_lifecycle_control_review_then_reaccepts(tmp_path):
    engine, evidence, state, review, reviewed = _reviewed(
        tmp_path,
        trigger="PROVENANCE_CONFLICT",
    )
    reaccept = engine.reaccept_evidence(
        reviewed,
        evidence,
        acceptance_decision_id="fresh_acceptance_decision_a",
    )
    active = engine.current_state_from_lifecycle_decision(reviewed, reaccept)
    engine.persist_current_state(active, lifecycle_decision=reaccept)

    assert review["decision_state"] == "REVIEW_OPENED"
    assert active["current_status"] == "ACTIVE"
    assert active["is_currently_accepted"] is True
    assert len(engine.get_evidence_history(state["evidence_id"])) == 3


def test_revocation_control_preserves_history_and_removes_current_authority(tmp_path):
    engine, _, state, review, reviewed = _reviewed(
        tmp_path,
        trigger="VALIDATION_RESULT_RETRACTED",
    )
    revocation = engine.revoke_evidence(
        reviewed,
        review,
        revocation_reason="source_withdrawn",
        supporting_refs=["accepted_evidence_a"],
    )
    revoked = engine.current_state_from_lifecycle_decision(reviewed, revocation)

    assert revocation["decision_state"] == "EVIDENCE_REVOKED"
    assert revoked["current_status"] == "REVOKED"
    assert revoked["is_currently_accepted"] is False
    assert state["current_status"] == "ACTIVE"


def test_invalidation_control_handles_artifact_integrity_failure(tmp_path):
    engine, _, _, review, reviewed = _reviewed(
        tmp_path,
        trigger="ARTIFACT_INTEGRITY_FAILURE",
    )
    invalidation = engine.invalidate_evidence(
        reviewed,
        review,
        invalidation_reason="artifact_fingerprint_mismatch",
        provenance_failure_refs=["fingerprint_a"],
    )
    invalidated = engine.current_state_from_lifecycle_decision(reviewed, invalidation)

    assert invalidation["decision_state"] == "EVIDENCE_INVALIDATED"
    assert invalidated["current_status"] == "INVALIDATED"
    assert invalidated["is_currently_accepted"] is False


def test_supersession_control_requires_explicit_relation(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    replacement = _accepted("accepted_evidence_b")
    replacement["supersedes_evidence_id"] = state["evidence_id"]
    supersession, replacement_state = engine.supersede_evidence(
        state,
        replacement_evidence=replacement,
        supersession_reason="fresher_validation_replaces_prior_artifact",
    )
    superseded = engine.current_state_from_lifecycle_decision(state, supersession)

    assert supersession["decision_state"] == "EVIDENCE_SUPERSEDED"
    assert superseded["current_status"] == "SUPERSEDED"
    assert superseded["superseded_by"] == "accepted_evidence_b"
    assert replacement_state["current_status"] == "ACTIVE"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda e: e.update({"evidence_acceptance_state": "RAW_RESULT"}),
        lambda e: e.pop("accepted_evidence_id"),
        lambda e: e.pop("evidence_decision_id"),
        lambda e: e.update({"claim_evidence_binding_state": "FAILED"}),
    ],
)
def test_raw_or_malformed_artifact_cannot_claim_active_state(mutation):
    evidence = _accepted("accepted_evidence_a")
    mutation(evidence)
    with pytest.raises(ValueError):
        AcceptedEvidenceLifecycleEngine().initialize_current_state(evidence)


def test_raw_result_cannot_revoke_evidence(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger="VALIDATION_RESULT_RETRACTED",
        trigger_evidence=_trigger(evidence_type="RAW_RESULT"),
    )
    assert "raw_evidence_cannot_trigger_lifecycle" in review["review_failures"]


def test_rejected_evidence_cannot_revoke_another_evidence(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger="VALIDATION_RESULT_RETRACTED",
        trigger_evidence=_trigger(evidence_acceptance_state="REJECTED"),
    )
    assert "rejected_evidence_cannot_trigger_lifecycle" in review["review_failures"]


def test_wrong_evidence_id_cannot_mutate_current_state(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger("accepted_evidence_b"),
    )
    assert "wrong_evidence_id" in review["review_failures"]


def test_missing_lifecycle_decision_id_fails_closed(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    state.pop("current_lifecycle_decision_id")
    review = engine.review_evidence(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(),
    )
    assert "lifecycle_decision_id_required" in review["review_failures"]


def test_stale_accepted_replay_cannot_restore_revoked_state(tmp_path):
    engine, evidence, state, review, reviewed = _reviewed(tmp_path)
    revocation = engine.revoke_evidence(reviewed, review, revocation_reason="withdrawn")
    revoked = engine.current_state_from_lifecycle_decision(reviewed, revocation)
    engine.persist_current_state(revoked, lifecycle_decision=revocation)

    assert engine.get_current_evidence_state(state["evidence_id"])[
        "current_status"
    ] == "REVOKED"
    assert engine.is_currently_accepted({**evidence, "current_status": "REVOKED"}) is False


def test_stale_revoked_state_does_not_override_fresh_reacceptance(tmp_path):
    engine, evidence, state, review, reviewed = _reviewed(tmp_path)
    revocation = engine.revoke_evidence(reviewed, review, revocation_reason="withdrawn")
    revoked = engine.current_state_from_lifecycle_decision(reviewed, revocation)
    reaccept = engine.reaccept_evidence(
        revoked,
        evidence,
        acceptance_decision_id="fresh_acceptance_decision",
    )
    active = engine.current_state_from_lifecycle_decision(revoked, reaccept)
    engine.persist_current_state(active, lifecycle_decision=reaccept)
    stale = deepcopy(revoked)
    stale["authority"] = "NONE"
    engine.persist_current_state(active, lifecycle_decision=reaccept)

    assert engine.get_current_evidence_state(state["evidence_id"])[
        "current_status"
    ] == "ACTIVE"
    assert stale["current_status"] == "REVOKED"


def test_cross_evidence_decision_rejected(tmp_path):
    engine, _, state, review, reviewed = _reviewed(tmp_path)
    review["evidence_id"] = "accepted_evidence_b"
    with pytest.raises(ValueError, match="wrong_evidence_id"):
        engine.current_state_from_lifecycle_decision(reviewed, review)


def test_cross_run_or_task_copy_requires_matching_evidence_authority(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    copied = deepcopy(state)
    copied["source_run_id"] = "foreign_run"
    copied["task_id"] = "foreign_task"
    copied["authority"] = "NONE"
    assert engine.get_current_evidence_state(copied["evidence_id"]) is not None
    with pytest.raises(ValueError, match="accepted_evidence_lifecycle_authority_required"):
        engine.persist_current_state(copied)


def test_persisted_state_without_authority_is_not_current(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    path = tmp_path / "accepted_evidence_current_state" / f"{state['evidence_id']}.json"
    bad = deepcopy(state)
    bad["authority"] = "NONE"
    path.write_text(__import__("json").dumps(bad), encoding="utf-8")
    assert engine.get_current_evidence_state(state["evidence_id"]) is None


def test_filesystem_timestamp_is_not_authority(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    later = deepcopy(state)
    later["current_status"] = "REVOKED"
    later["authority"] = "NONE"
    with pytest.raises(ValueError):
        engine.persist_current_state(later)


def test_newer_run_is_not_automatic_supersession(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    replacement = _accepted("accepted_evidence_b", run_id="new_run")
    supersession, _ = engine.supersede_evidence(
        state,
        replacement_evidence=replacement,
        supersession_reason="newer_run_only",
    )
    assert supersession["decision_state"] == "SUPERSESSION_DENIED"


def test_larger_task_count_is_not_stronger_authority(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(distinct_task_count=99),
    )
    assert review["decision_state"] == "REVIEW_OPENED"
    assert review["authority"]["accepted_evidence_lifecycle"] == (
        "VALIDATION_EVIDENCE_EVALUATOR"
    )


def test_duplicate_revocation_is_denied(tmp_path):
    engine, _, _, review, reviewed = _reviewed(tmp_path)
    revocation = engine.revoke_evidence(reviewed, review, revocation_reason="withdrawn")
    revoked = engine.current_state_from_lifecycle_decision(reviewed, revocation)
    duplicate = engine.revoke_evidence(revoked, review, revocation_reason="withdrawn")
    assert duplicate["decision_state"] == "REVOKED_DENIED"


def test_revocation_without_valid_trigger_is_denied(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger="QUALITY_CHANGED",
        trigger_evidence=_trigger(),
    )
    assert review["decision_state"] == "REVIEW_DENIED"


def test_restoration_requires_fresh_acceptance_decision(tmp_path):
    engine, evidence, _, review, reviewed = _reviewed(tmp_path)
    revocation = engine.revoke_evidence(reviewed, review, revocation_reason="withdrawn")
    revoked = engine.current_state_from_lifecycle_decision(reviewed, revocation)
    with pytest.raises(ValueError, match="fresh_acceptance_decision_required"):
        engine.reaccept_evidence(revoked, evidence, acceptance_decision_id="")


def test_historical_evidence_content_is_not_mutated_by_lifecycle(tmp_path):
    engine, evidence, _, review, reviewed = _reviewed(tmp_path)
    before = deepcopy(evidence)
    revocation = engine.revoke_evidence(reviewed, review, revocation_reason="withdrawn")
    engine.current_state_from_lifecycle_decision(reviewed, revocation)
    assert evidence == before


def test_source_independence_collapse_can_trigger_review(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger="SOURCE_IDENTITY_COLLAPSE",
        trigger_evidence=_trigger(),
    )
    assert review["decision_state"] == "REVIEW_OPENED"


def test_provenance_corruption_can_trigger_review(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger="PROVENANCE_CONFLICT",
        trigger_evidence=_trigger(source_provenance={}),
    )
    assert "trigger_provenance_missing" in review["review_failures"]


def test_artifact_fingerprint_mismatch_opens_review_path(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger="ARTIFACT_INTEGRITY_FAILURE",
        trigger_evidence=_trigger(artifact_fingerprint_matches=False),
    )
    assert "artifact_integrity_failure" in review["review_failures"]


def test_contradictory_evidence_opens_review(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger="CONTRADICTORY_ACCEPTED_EVIDENCE",
        trigger_evidence=_trigger(),
    )
    assert review["decision_state"] == "REVIEW_OPENED"


@pytest.mark.parametrize("status", ["UNDER_REVIEW", "REVOKED", "INVALIDATED", "SUPERSEDED"])
def test_qualification_engine_rejects_non_current_evidence(status):
    evidence = _accepted("accepted_evidence_a")
    evidence["current_status"] = status
    decision = IntegratedCapabilityQualificationEngine().decide(
        _subject(),
        [evidence],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
    )["qualification_decision"]
    assert decision["decision_state"] == "PROMOTION_DENIED"


def test_evidence_lifecycle_emits_qualification_review_trigger(tmp_path):
    engine, _, state, review, reviewed = _reviewed(tmp_path)
    revocation = engine.revoke_evidence(reviewed, review, revocation_reason="withdrawn")
    trigger = engine.qualification_review_trigger(
        revocation,
        capability_id=capability_id_for_subject(_subject()),
    )
    assert trigger["review_trigger"] == "ACCEPTED_EVIDENCE_REVOKED"
    assert trigger["qualification_authority"] == "NONE"


def test_evidence_layer_does_not_directly_demote_qualification(tmp_path):
    engine, _, _, review, reviewed = _reviewed(tmp_path)
    revocation = engine.revoke_evidence(reviewed, review, revocation_reason="withdrawn")
    assert "qualification_level" not in revocation
    assert revocation["authority"]["qualification"] == "NONE"


def test_evidence_layer_does_not_alter_truth_knowledge_budget_or_execution(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(),
    )
    assert review["authority"]["truth"] == "NONE"
    assert review["authority"]["knowledge"] == "NONE"
    assert review["authority"]["budget"] == "NONE"
    assert review["authority"]["execution"] == "NONE"


def test_supersession_without_explicit_relation_denied(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    replacement = _accepted("accepted_evidence_b")
    supersession, _ = engine.supersede_evidence(
        state,
        replacement_evidence=replacement,
        supersession_reason="implicit_newer_artifact",
    )
    assert "explicit_supersession_relation_required" in supersession[
        "supersession_failures"
    ]


def test_superseded_evidence_not_current(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    replacement = _accepted("accepted_evidence_b")
    replacement["supersedes_evidence_id"] = state["evidence_id"]
    supersession, _ = engine.supersede_evidence(
        state,
        replacement_evidence=replacement,
        supersession_reason="replacement",
    )
    superseded = engine.current_state_from_lifecycle_decision(state, supersession)
    assert superseded["is_currently_accepted"] is False


def test_corrupted_lifecycle_fingerprint_rejected(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_evidence(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(),
    )
    review["new_status"] = "REVOKED"
    with pytest.raises(ValueError, match="corrupted_lifecycle_fingerprint"):
        engine.current_state_from_lifecycle_decision(state, review)


def test_out_of_order_persistence_replay_does_not_become_authority(tmp_path):
    engine, evidence, state, review, reviewed = _reviewed(tmp_path)
    revocation = engine.revoke_evidence(reviewed, review, revocation_reason="withdrawn")
    revoked = engine.current_state_from_lifecycle_decision(reviewed, revocation)
    engine.persist_current_state(revoked, lifecycle_decision=revocation)
    old_active = engine.initialize_current_state(evidence)
    old_active["authority"] = "NONE"
    with pytest.raises(ValueError):
        engine.persist_current_state(old_active)


def test_multi_evidence_qualification_reassesses_remaining_evidence():
    first = _accepted("accepted_evidence_a", causal=True)
    second = _accepted("accepted_evidence_b", source="source_b", causal=False)
    first["current_status"] = "REVOKED"
    second["current_status"] = "ACTIVE"
    decision = IntegratedCapabilityQualificationEngine().decide(
        _subject(),
        [first, second],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
    )["qualification_decision"]
    assert decision["decision_state"] == "PROMOTION_GRANTED"
    assert decision["accepted_evidence_ids"] == ["accepted_evidence_b"]


def test_current_and_history_apis_are_separate(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    assert isinstance(engine.get_current_evidence_state(state["evidence_id"]), dict)
    assert isinstance(engine.get_evidence_history(state["evidence_id"]), list)

