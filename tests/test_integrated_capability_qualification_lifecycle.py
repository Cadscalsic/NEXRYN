from copy import deepcopy

import pytest

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    CapabilityQualificationStatus,
    CapabilitySubject,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from tests.test_integrated_capability_qualification import _accepted, _subject


def _engine_state(tmp_path, *, level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED):
    engine = IntegratedCapabilityQualificationEngine(tmp_path)
    result = engine.decide(
        _subject(),
        [_accepted("accepted_a")],
        requested_level=level,
        architecture_present=True,
        runtime_reachable=True,
    )
    engine.persist_decision(result["qualification_decision"])
    state = engine.get_current_qualification(result["qualification_decision"]["capability_id"])
    return engine, result, state


def _trigger(capability_id=None, **overrides):
    data = {
        "accepted_evidence_id": "accepted_a",
        "evidence_acceptance_state": "ACCEPTED",
        "capability_id": capability_id or capability_id_for_subject(_subject()),
        "source_provenance": {"source_provenance_state": "SOURCE_PROVENANCE_BOUND"},
    }
    data.update(overrides)
    return data


def test_active_qualification_enters_under_review_with_governed_trigger(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    current = engine.get_current_qualification(state["capability_id"])

    assert review["decision_state"] == "REVIEW_OPENED"
    assert current["qualification_status"] == "UNDER_REVIEW"
    assert current["current_authority_state"] == "NO_ACTIVE_QUALIFICATION"


def test_invalidation_preserves_history_without_active_authority(tmp_path):
    engine, result, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    invalidation = engine.invalidate_qualification(
        engine.get_current_qualification(state["capability_id"]),
        review,
        invalidation_reason="accepted_evidence_revoked",
        supporting_evidence_refs=["accepted_a"],
    )
    engine.persist_invalidation_decision(invalidation)
    current = engine.get_current_qualification(state["capability_id"])
    history = engine.get_qualification_history(state["capability_id"])

    assert invalidation["decision_state"] == "QUALIFICATION_INVALIDATED"
    assert current["qualification_status"] == "INVALIDATED"
    assert current["current_authority_state"] == "NO_ACTIVE_QUALIFICATION"
    assert result["qualification_decision"]["qualification_decision_id"] in str(history)


def test_revalidation_to_lower_level_requires_fresh_qualification_decision(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="CAUSAL_SUPPORT_WITHDRAWN",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    revalidated = engine.revalidate(
        engine.get_current_qualification(state["capability_id"]),
        [],
        requested_level=CapabilityQualificationLevel.RUNTIME_REACHABLE,
        architecture_present=True,
        runtime_reachable=True,
    )
    engine.persist_revalidation_decision(revalidated)
    current = engine.get_current_qualification(state["capability_id"])

    assert revalidated["revalidation_decision"]["result"] == "REQUALIFIED_LOWER_LEVEL"
    assert current["qualification_status"] == "ACTIVE"
    assert current["current_qualification_level"] == "RUNTIME_REACHABLE"
    assert current["last_qualification_decision_id"] != state["last_qualification_decision_id"]


def test_full_invalidation_when_no_level_remains_supported(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="EVIDENCE_PROVENANCE_INVALIDATED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    invalidation = engine.invalidate_qualification(
        engine.get_current_qualification(state["capability_id"]),
        review,
        invalidation_reason="no_valid_accepted_evidence_remains",
    )
    engine.persist_invalidation_decision(invalidation)

    current = engine.get_current_qualification(state["capability_id"])
    assert current["qualification_status"] == "INVALIDATED"
    assert current["current_authority_state"] == "NO_ACTIVE_QUALIFICATION"


def test_restoration_is_not_automatic_after_invalidation(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    invalidation = engine.invalidate_qualification(
        engine.get_current_qualification(state["capability_id"]),
        review,
        invalidation_reason="accepted_evidence_revoked",
    )
    engine.persist_invalidation_decision(invalidation)

    current = engine.get_current_qualification(state["capability_id"])
    assert current["qualification_status"] == "INVALIDATED"
    assert current["current_authority_state"] == "NO_ACTIVE_QUALIFICATION"


def test_fresh_revalidation_restores_active_state(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    invalidation = engine.invalidate_qualification(
        engine.get_current_qualification(state["capability_id"]),
        review,
        invalidation_reason="accepted_evidence_revoked",
    )
    engine.persist_invalidation_decision(invalidation)
    restored = engine.revalidate(
        engine.get_current_qualification(state["capability_id"]),
        [_accepted("accepted_new")],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
    )
    engine.persist_revalidation_decision(restored)

    current = engine.get_current_qualification(state["capability_id"])
    assert restored["revalidation_decision"]["result"] == "RESTORED_SAME_LEVEL"
    assert current["qualification_status"] == "ACTIVE"


def test_raw_result_cannot_request_invalidation(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence=_trigger(
            state["capability_id"],
            evidence_type="RAW_RESULT",
        ),
    )
    assert review["decision_state"] == "REVIEW_DENIED"
    assert "raw_evidence_cannot_trigger_lifecycle" in review["review_failures"]


def test_rejected_evidence_cannot_request_invalidation(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence=_trigger(
            state["capability_id"],
            evidence_acceptance_state="REJECTED",
        ),
    )
    assert review["decision_state"] == "REVIEW_DENIED"
    assert "rejected_evidence_cannot_trigger_lifecycle" in review["review_failures"]


def test_missing_capability_id_cannot_enter_review(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    state.pop("capability_id")
    review = engine.review_qualification(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(),
    )
    assert "missing_capability_id" in review["review_failures"]


def test_wrong_capability_id_cannot_enter_review(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger("capability_wrong"),
    )
    assert "wrong_capability_id" in review["review_failures"]


def test_missing_decision_id_cannot_enter_review(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    state.pop("last_qualification_decision_id")
    review = engine.review_qualification(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(),
    )
    assert "missing_current_qualification_decision" in review["review_failures"]


def test_stale_qualification_replay_rejected_after_invalidation(tmp_path):
    engine, result, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    invalidation = engine.invalidate_qualification(
        engine.get_current_qualification(state["capability_id"]),
        review,
        invalidation_reason="accepted_evidence_revoked",
    )
    engine.persist_invalidation_decision(invalidation)

    with pytest.raises(ValueError, match="stale_qualification_decision_rejected"):
        engine.persist_decision(result["qualification_decision"])


def test_stale_invalidation_replay_is_denied(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    invalidation = engine.invalidate_qualification(
        engine.get_current_qualification(state["capability_id"]),
        review,
        invalidation_reason="accepted_evidence_revoked",
    )
    engine.persist_invalidation_decision(invalidation)
    replay = engine.invalidate_qualification(
        engine.get_current_qualification(state["capability_id"]),
        review,
        invalidation_reason="accepted_evidence_revoked",
    )
    assert replay["decision_state"] == "INVALIDATION_DENIED"


def test_cross_capability_invalidation_decision_does_not_mutate_other_capability(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    other_state = deepcopy(state)
    other_state["capability_id"] = capability_id_for_subject(_subject(operation="rotate"))
    review = engine.review_qualification(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    invalidation = engine.invalidate_qualification(
        other_state,
        review,
        invalidation_reason="wrong_capability",
    )
    assert "wrong_capability_id" in invalidation["invalidation_failures"]


def test_cross_run_copied_state_cannot_bypass_trigger_authority(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    copied = deepcopy(state)
    copied["source_run_id"] = "foreign_run"
    review = engine.review_qualification(
        copied,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence={},
    )
    assert review["decision_state"] == "REVIEW_DENIED"
    assert "trigger_evidence_required" in review["review_failures"]


def test_cross_task_copied_state_cannot_bypass_trigger_authority(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    copied = deepcopy(state)
    copied["task_id"] = "foreign_task"
    review = engine.review_qualification(
        copied,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence={},
    )
    assert review["decision_state"] == "REVIEW_DENIED"
    assert "trigger_evidence_required" in review["review_failures"]


def test_persisted_record_without_authority_is_not_current(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    path = tmp_path / "capability_qualification_state" / f"{state['capability_id']}.json"
    stale = deepcopy(state)
    stale["state_authority"] = "NONE"
    path.write_text(__import__("json").dumps(stale), encoding="utf-8")
    assert engine.get_current_qualification(state["capability_id"]) is None


def test_duplicate_invalidation_does_not_create_active_change(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    invalidation = engine.invalidate_qualification(
        engine.get_current_qualification(state["capability_id"]),
        review,
        invalidation_reason="accepted_evidence_revoked",
    )
    engine.persist_invalidation_decision(invalidation)
    duplicate = engine.invalidate_qualification(
        engine.get_current_qualification(state["capability_id"]),
        review,
        invalidation_reason="accepted_evidence_revoked",
    )
    assert duplicate["decision_state"] == "INVALIDATION_DENIED"
    assert engine.get_current_qualification(state["capability_id"])[
        "qualification_status"
    ] == "INVALIDATED"


def test_invalidation_without_trigger_evidence_denied(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence={},
    )
    assert review["decision_state"] == "REVIEW_DENIED"


def test_direct_demotion_requires_fresh_decision(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    mutated = deepcopy(state)
    mutated["current_qualification_level"] = "RUNTIME_REACHABLE"
    path = tmp_path / "capability_qualification_state" / f"{state['capability_id']}.json"
    path.write_text(__import__("json").dumps(mutated), encoding="utf-8")
    current = engine.get_current_qualification(state["capability_id"])
    assert current["last_qualification_decision_id"] == state["last_qualification_decision_id"]


def test_direct_restoration_without_revalidation_decision_remains_impossible(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    with pytest.raises(ValueError, match="revalidation_requires_review_or_invalidated_state"):
        engine.revalidate(
            state,
            [_accepted("accepted_new")],
            requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
            architecture_present=True,
            runtime_reachable=True,
        )


def test_source_independence_collapse_triggers_review(tmp_path):
    engine = IntegratedCapabilityQualificationEngine(tmp_path)
    result = engine.decide(
        _subject(),
        [
            _accepted("accepted_a", source="source_a", causal=True),
            _accepted("accepted_b", source="source_b", causal=True),
        ],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        architecture_present=True,
        runtime_reachable=True,
    )
    engine.persist_decision(result["qualification_decision"])
    state = engine.get_current_qualification(result["qualification_decision"]["capability_id"])
    assert result["qualification_decision"]["decision_state"] == "PROMOTION_GRANTED"
    review = engine.review_qualification(
        state,
        review_trigger="SOURCE_INDEPENDENCE_COLLAPSED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    assert review["decision_state"] == "REVIEW_OPENED"


def test_fake_independent_task_count_cannot_trigger_reproducibility(tmp_path):
    engine = IntegratedCapabilityQualificationEngine(tmp_path)
    evidence = _accepted("accepted_a", causal=True)
    evidence["distinct_task_count"] = 99
    result = engine.decide(
        _subject(),
        [evidence],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        architecture_present=True,
        runtime_reachable=True,
    )
    assert result["qualification_decision"]["decision_state"] == "PROMOTION_DENIED"


def test_fake_independent_run_count_cannot_trigger_reproducibility(tmp_path):
    engine = IntegratedCapabilityQualificationEngine(tmp_path)
    evidence = _accepted("accepted_a", causal=True)
    evidence["distinct_run_count"] = 99
    result = engine.decide(
        _subject(),
        [evidence],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        architecture_present=True,
        runtime_reachable=True,
    )
    assert result["qualification_decision"]["decision_state"] == "PROMOTION_DENIED"


def test_causal_evidence_withdrawn_triggers_review_and_lower_requalification(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="CAUSAL_SUPPORT_WITHDRAWN",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    revalidated = engine.revalidate(
        engine.get_current_qualification(state["capability_id"]),
        [_accepted("accepted_a")],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
    )
    assert revalidated["qualification_decision"]["granted_level"] == "OPERATIONALLY_OBSERVED"


def test_reproducibility_evidence_withdrawn_triggers_review(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="REPRODUCIBILITY_SUPPORT_INVALIDATED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    assert review["decision_state"] == "REVIEW_OPENED"


def test_contradictory_accepted_evidence_triggers_review(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="CONTRADICTORY_ACCEPTED_EVIDENCE",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    assert review["decision_state"] == "REVIEW_OPENED"


def test_historical_decision_cannot_overwrite_current_lifecycle(tmp_path):
    engine, result, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    with pytest.raises(ValueError, match="stale_qualification_decision_rejected"):
        engine.persist_decision(result["qualification_decision"])


def test_missing_provenance_trigger_denied(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="DECISION_PROVENANCE_INVALID",
        trigger_evidence=_trigger(state["capability_id"], source_provenance={}),
    )
    assert "trigger_provenance_missing" in review["review_failures"]


def test_corrupted_decision_fingerprint_rejected(tmp_path):
    engine, result, _ = _engine_state(tmp_path)
    decision = deepcopy(result["qualification_decision"])
    decision["granted_level"] = "REPRODUCIBLY_SUPPORTED"
    with pytest.raises(ValueError, match="corrupted_decision_fingerprint"):
        engine.persist_decision(decision)


def test_downstream_current_state_does_not_read_invalidated_as_active(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    current = engine.get_current_qualification(state["capability_id"])
    assert current["qualification_status"] == CapabilityQualificationStatus.UNDER_REVIEW.value
    assert current["current_authority_state"] == "NO_ACTIVE_QUALIFICATION"


def test_truth_budget_runtime_authority_not_inferred_from_lifecycle(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    assert review["authority"]["truth"] == "NONE"
    assert review["authority"]["budget"] == "NONE"
    assert review["authority"]["runtime"] == "NONE"
    assert review["authority"]["execution"] == "NONE"


def test_revalidation_using_raw_evidence_denied(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    raw = _accepted("accepted_raw")
    raw["evidence_acceptance_state"] = "RAW_RESULT"
    revalidated = engine.revalidate(
        engine.get_current_qualification(state["capability_id"]),
        [raw],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
    )
    assert revalidated["qualification_decision"]["decision_state"] == "PROMOTION_DENIED"


def test_direct_promotion_during_revalidation_without_evidence_denied(tmp_path):
    engine, _, state = _engine_state(tmp_path)
    review = engine.review_qualification(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    revalidated = engine.revalidate(
        engine.get_current_qualification(state["capability_id"]),
        [],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
    )
    assert revalidated["qualification_decision"]["decision_state"] == "PROMOTION_DENIED"
