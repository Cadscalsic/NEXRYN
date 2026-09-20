import json

import pytest

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from runtime.evidence.current_evidence_need import (
    CurrentEvidenceNeedAuthorityEngine,
    DeficitSignalType,
    EvidenceNeedLifecycleStatus,
    EvidenceNeedSubject,
    EvidenceNeedType,
)


def _subject(operation="replace_color", domain="color"):
    return {
        "capability_name": f"{operation}_capability",
        "operation": operation,
        "domain": domain,
        "context_class": "qualification",
        "evidence_scope": "capability_support",
    }


def _accepted(
    evidence_id,
    *,
    source="source_a",
    causal=False,
    capability_subject=None,
    claim_id="claim_replace_color",
):
    capability_subject = capability_subject or _subject()
    capability_id = capability_id_for_subject(capability_subject)
    return {
        "accepted_evidence_id": evidence_id,
        "evidence_acceptance_state": "ACCEPTED",
        "accepted_evidence_current_state": {
            "current_status": "ACTIVE",
            "is_currently_accepted": True,
        },
        "claim_id": claim_id,
        "claim_subject": {
            "kind": "candidate_operation",
            "operation": capability_subject["operation"],
        },
        "capability_id": capability_id,
        "capability_subject": capability_subject,
        "canonical_source_identity": source,
        "source_provenance": {
            "source_provenance_state": "SOURCE_PROVENANCE_BOUND",
            "canonical_source_identity": source,
        },
        "capability_causal_support_state": (
            "CAUSALLY_SUPPORTED" if causal else "OBSERVED_ONLY"
        ),
        "accepted_evidence_origin": {
            "accepted_evidence_origin_state": "TASK_ORIGIN_PRESERVED",
            "origin_task_execution_id": f"execution_{evidence_id}",
            "origin_task_id": f"task_{evidence_id}",
        },
    }


def _qualification_result(
    *,
    accepted=None,
    requested=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
    subject=None,
    architecture_present=True,
    runtime_reachable=True,
    required_independent_sources=2,
):
    subject = subject or _subject()
    return IntegratedCapabilityQualificationEngine().decide(
        subject,
        accepted or [],
        requested_level=requested,
        architecture_present=architecture_present,
        runtime_reachable=runtime_reachable,
        required_independent_sources=required_independent_sources,
    )


def _engine(tmp_path):
    return CurrentEvidenceNeedAuthorityEngine(tmp_path / "needs")


def _open_candidate(
    engine,
    result,
    need_type=EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value,
):
    return engine.candidate_from_qualification_deficit(
        result,
        need_type=need_type,
    )


def test_positive_qualification_deficit_creates_active_current_need(tmp_path):
    engine = _engine(tmp_path)
    result = _qualification_result(
        accepted=[_accepted("evidence_a", source="source_a", causal=True)]
    )

    candidate = _open_candidate(engine, result)
    decision = engine.decide_current_need(candidate)
    state = decision["current_state"]

    assert candidate["authority"] == "NONE"
    assert decision["assessment"]["authority"] == "NONE"
    assert decision["authority"] == "CURRENT_EVIDENCE_NEED_AUTHORITY_ENGINE"
    assert state["lifecycle_status"] == EvidenceNeedLifecycleStatus.ACTIVE.value
    assert engine.is_evidence_need_current(candidate["evidence_need_id"]) is True
    assert decision["validation_sponsorship_created"] is False
    assert decision["evidence_plan_created"] is False
    assert decision["raw_evidence_created"] is False
    assert decision["accepted_evidence_created"] is False


def test_need_identity_is_semantic_and_stable(tmp_path):
    engine = _engine(tmp_path)
    first = EvidenceNeedSubject.from_mapping({
        "target_type": "capability",
        "capability_id": "capability_a",
        "qualification_subject_id": "subject_a",
        "domain": "color",
        "context_class": "qualification",
        "evidence_scope": "capability_support",
    })
    same = {**first.to_dict(), "run_id": "run_ignored", "task_id": "task_ignored"}
    source_need = engine.evidence_need_id(
        first,
        EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value,
    )
    same_need = engine.evidence_need_id(
        same,
        EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value,
    )
    causal_need = engine.evidence_need_id(
        first,
        EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value,
    )
    other_capability = engine.evidence_need_id(
        {**first.to_dict(), "capability_id": "capability_b"},
        EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value,
    )

    assert source_need == same_need
    assert source_need != causal_need
    assert source_need != other_capability


def test_multiple_simultaneous_need_types_remain_distinct(tmp_path):
    engine = _engine(tmp_path)
    result = _qualification_result(accepted=[_accepted("evidence_a")])

    candidates = engine.candidates_from_qualification_deficit(result)
    types = {candidate["need_type"] for candidate in candidates}
    source = _open_candidate(
        engine,
        result,
        EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value,
    )
    causal = _open_candidate(
        engine,
        result,
        EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value,
    )
    source_state = engine.decide_current_need(source)["current_state"]
    causal_state = engine.decide_current_need(causal)["current_state"]
    engine.satisfy_need(
        source["evidence_need_id"],
        current_support_summary={
            "independent_source_count": 2,
            "required_independent_sources": 2,
        },
    )

    assert EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value in types
    assert EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value in types
    assert source["evidence_need_id"] != causal["evidence_need_id"]
    assert source_state["lifecycle_status"] == "ACTIVE"
    assert causal_state["lifecycle_status"] == "ACTIVE"
    assert engine.is_evidence_need_current(source["evidence_need_id"]) is False
    assert engine.is_evidence_need_current(causal["evidence_need_id"]) is True


def test_satisfaction_control_and_support_loss_requires_fresh_decision(tmp_path):
    engine = _engine(tmp_path)
    result = _qualification_result(
        accepted=[_accepted("evidence_a", source="source_a", causal=True)]
    )
    candidate = _open_candidate(engine, result)
    engine.decide_current_need(candidate)

    satisfied = engine.satisfy_need(
        candidate["evidence_need_id"],
        current_support_summary={
            "independent_source_count": 2,
            "required_independent_sources": 2,
        },
    )
    revalidation = engine.require_revalidation(
        candidate["evidence_need_id"],
        revalidation_reason="supporting_evidence_revoked",
        supporting_refs=["accepted_evidence_a"],
    )

    assert satisfied["current_state"]["lifecycle_status"] == "SATISFIED"
    assert engine.is_evidence_need_current(candidate["evidence_need_id"]) is False
    assert revalidation["current_state"]["lifecycle_status"] == (
        "REVALIDATION_REQUIRED"
    )
    assert engine.is_evidence_need_current(candidate["evidence_need_id"]) is False


def test_non_authoritative_support_cannot_satisfy_need(tmp_path):
    engine = _engine(tmp_path)
    result = _qualification_result(
        accepted=[_accepted("evidence_a", source="source_a", causal=True)]
    )
    candidate = _open_candidate(engine, result)
    engine.decide_current_need(candidate)

    denied = engine.satisfy_need(
        candidate["evidence_need_id"],
        current_support_summary={
            "task_count": 99,
            "run_count": 99,
            "artifact_count": 99,
            "independent_source_count": 1,
            "required_independent_sources": 2,
        },
    )

    assert denied["decision"]["decision_state"] == (
        "DENIED_NO_AUTHORITATIVE_SUPPORT_TRANSITION"
    )
    assert engine.is_evidence_need_current(candidate["evidence_need_id"]) is True


def test_stale_deficit_replay_is_denied(tmp_path):
    engine = _engine(tmp_path)
    result = _qualification_result(accepted=[_accepted("evidence_a")])
    candidate = _open_candidate(
        engine,
        result,
        EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value,
    )
    candidate["provenance"]["source_deficit_current"] = False
    candidate["candidate_fingerprint"] = engine._fingerprint_payload_for_test(
        candidate
    ) if hasattr(engine, "_fingerprint_payload_for_test") else candidate[
        "candidate_fingerprint"
    ]

    decision = engine.decide_current_need(candidate)

    assert decision["decision"]["decision_state"] in {
        "DENIED_STALE_DEFICIT",
        "DENIED_DECISION_INTEGRITY_FAILURE",
    }
    assert engine.is_evidence_need_current(candidate["evidence_need_id"]) is False


def test_stale_active_replay_and_copied_state_do_not_restore_currentness(tmp_path):
    engine = _engine(tmp_path)
    result = _qualification_result(
        accepted=[_accepted("evidence_a", source="source_a", causal=True)]
    )
    candidate = _open_candidate(engine, result)
    active = engine.decide_current_need(candidate)["current_state"]
    engine.satisfy_need(
        candidate["evidence_need_id"],
        current_support_summary={
            "independent_source_count": 2,
            "required_independent_sources": 2,
        },
    )
    current_path = tmp_path / "needs" / "current" / f"{candidate['evidence_need_id']}.json"
    copied = dict(active)
    copied["lifecycle_status"] = "ACTIVE"
    copied["state_fingerprint"] = "copied_stale_fingerprint"
    current_path.write_text(json.dumps(copied), encoding="utf-8")

    state = engine.get_current_evidence_need_state(candidate["evidence_need_id"])

    assert state["currentness_integrity_state"] == "INVALID"
    assert engine.is_evidence_need_current(candidate["evidence_need_id"]) is False


def test_cross_capability_cross_claim_and_cross_need_type_protection(tmp_path):
    engine = _engine(tmp_path)
    result = _qualification_result(
        accepted=[_accepted("evidence_a", source="source_a", causal=True)]
    )
    candidate = _open_candidate(engine, result)
    engine.decide_current_need(candidate)
    subject = candidate["subject"]

    assert engine.is_evidence_need_current(
        candidate["evidence_need_id"],
        expected_capability_id=subject["capability_id"],
        expected_need_type=EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value,
    )
    assert engine.is_evidence_need_current(
        candidate["evidence_need_id"],
        expected_capability_id="capability_other",
    ) is False
    assert engine.is_evidence_need_current(
        candidate["evidence_need_id"],
        expected_need_type=EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value,
    ) is False
    assert engine.is_evidence_need_current(
        candidate["evidence_need_id"],
        expected_claim_id="claim_other",
    ) is False


def test_missing_subject_label_only_and_unauthorized_sources_fail_closed(tmp_path):
    engine = _engine(tmp_path)
    label_only = {
        "target_type": "capability",
        "capability_id": "",
        "domain": "rotation causal reproducibility",
    }

    with pytest.raises(Exception):
        EvidenceNeedSubject.from_mapping(label_only)

    unauthorized = engine.propose_candidate(
        subject={
            "target_type": "capability",
            "capability_id": "capability_a",
            "domain": "rotation",
            "context_class": "training_score",
            "evidence_scope": "capability_support",
        },
        need_type=EvidenceNeedType.GENERAL_SUPPORT_REQUIRED.value,
        deficit_signal_type=DeficitSignalType.NOT_ELIGIBLE_FOR_NEED_PROPOSAL.value,
        source_deficit_refs=[],
        proposal_reason="task_failure",
        producer="TrainingAssistant",
    )
    decision = engine.decide_current_need(unauthorized)

    assert decision["decision"]["decision_state"] in {
        "DENIED_UNAUTHORIZED_NEED_PRODUCER",
        "DENIED_NO_GOVERNED_DEFICIT_SOURCE",
    }
    assert decision["validation_sponsorship_created"] is False
    assert decision["evidence_plan_created"] is False


@pytest.mark.parametrize(
    "producer,reason",
    [
        ("TaskFailure", "task_failed"),
        ("TaskSuccess", "task_succeeded"),
        ("TrainingAssistant", "selection_priority"),
        ("EvidenceGenerationEngine", "generation_required"),
        ("IntentManager", "intent_objective"),
        ("GoalManager", "goal_objective"),
        ("PlanningEngine", "plan_objective"),
    ],
)
def test_unauthorized_creation_attacks_fail_closed(tmp_path, producer, reason):
    engine = _engine(tmp_path)
    candidate = engine.propose_candidate(
        subject={
            "target_type": "capability",
            "capability_id": "capability_attack",
            "domain": "attack",
            "context_class": "attack",
            "evidence_scope": "capability_support",
        },
        need_type=EvidenceNeedType.GENERAL_SUPPORT_REQUIRED.value,
        deficit_signal_type=DeficitSignalType.GENERAL_SUPPORT_DEFICIT.value,
        source_deficit_refs=[{"source_decision_id": "attack_source"}],
        proposal_reason=reason,
        producer=producer,
    )

    decision = engine.decide_current_need(candidate)

    assert decision["decision"]["decision_state"] == (
        "DENIED_UNAUTHORIZED_NEED_PRODUCER"
    )
    assert engine.is_evidence_need_current(candidate["evidence_need_id"]) is False


def test_causal_and_reproducibility_need_satisfaction_use_typed_support(tmp_path):
    engine = _engine(tmp_path)
    result = _qualification_result(accepted=[_accepted("evidence_a")])
    causal = _open_candidate(
        engine,
        result,
        EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value,
    )
    reproducibility = _open_candidate(
        engine,
        result,
        EvidenceNeedType.REPRODUCIBILITY_REQUIRED.value,
    )
    engine.decide_current_need(causal)
    engine.decide_current_need(reproducibility)

    non_causal = engine.satisfy_need(
        causal["evidence_need_id"],
        current_support_summary={"valid_accepted_evidence_count": 4},
    )
    same_source = engine.satisfy_need(
        reproducibility["evidence_need_id"],
        current_support_summary={
            "causal_support_state": "CAUSALLY_SUPPORTED",
            "independent_source_count": 1,
            "required_independent_sources": 2,
        },
    )
    causal_ok = engine.satisfy_need(
        causal["evidence_need_id"],
        current_support_summary={"causal_support_state": "CAUSALLY_SUPPORTED"},
    )
    reproduction_ok = engine.satisfy_need(
        reproducibility["evidence_need_id"],
        current_support_summary={
            "causal_support_state": "CAUSALLY_SUPPORTED",
            "independent_source_count": 2,
            "required_independent_sources": 2,
        },
    )

    assert non_causal["decision"]["decision_state"] == (
        "DENIED_NO_AUTHORITATIVE_SUPPORT_TRANSITION"
    )
    assert same_source["decision"]["decision_state"] == (
        "DENIED_NO_AUTHORITATIVE_SUPPORT_TRANSITION"
    )
    assert causal_ok["current_state"]["lifecycle_status"] == "SATISFIED"
    assert reproduction_ok["current_state"]["lifecycle_status"] == "SATISFIED"


def test_invalidation_review_supersession_and_inventory(tmp_path):
    engine = _engine(tmp_path)
    result = _qualification_result(
        accepted=[_accepted("evidence_a", source="source_a", causal=True)]
    )
    candidate = _open_candidate(engine, result)
    engine.decide_current_need(candidate)
    review = engine.open_review(candidate["evidence_need_id"], review_reason="changed")
    assert review["current_state"]["lifecycle_status"] == "UNDER_REVIEW"
    assert engine.list_current_evidence_needs() == []

    candidate2 = _open_candidate(engine, result)
    engine.decide_current_need(candidate2)
    invalid = engine.invalidate_need(
        candidate["evidence_need_id"],
        invalidation_reason="subject_invalid",
    )
    assert invalid["current_state"]["lifecycle_status"] == "INVALIDATED"

    engine.decide_current_need(candidate)
    replacement = "current_evidence_need_replacement"
    superseded = engine.supersede_need(
        candidate["evidence_need_id"],
        replacement_evidence_need_id=replacement,
        supersession_reason="semantic_need_changed",
    )
    assert superseded["current_state"]["lifecycle_status"] == "SUPERSEDED"
    assert engine.get_evidence_need_history(candidate["evidence_need_id"])


def test_duplicate_need_proposal_reuses_active_authority(tmp_path):
    engine = _engine(tmp_path)
    result = _qualification_result(
        accepted=[_accepted("evidence_a", source="source_a", causal=True)]
    )
    candidate = _open_candidate(engine, result)
    first = engine.decide_current_need(candidate)
    second = engine.decide_current_need(candidate)

    assert first["current_state"]["evidence_need_id"] == (
        second["current_state"]["evidence_need_id"]
    )
    assert second["decision"]["decision_state"] == "CURRENT_NEED_ALREADY_ACTIVE"
    assert len(engine.list_current_evidence_needs()) == 1


def test_persistence_roundtrip_preserves_pointer_and_fingerprints(tmp_path):
    engine = _engine(tmp_path)
    result = _qualification_result(
        accepted=[_accepted("evidence_a", source="source_a", causal=True)]
    )
    candidate = _open_candidate(engine, result)
    engine.decide_current_need(candidate)

    reloaded = CurrentEvidenceNeedAuthorityEngine(tmp_path / "needs")
    state = reloaded.get_current_evidence_need_state(candidate["evidence_need_id"])
    decision_file = next((tmp_path / "needs" / "decisions").glob("*.json"))
    decision = json.loads(decision_file.read_text(encoding="utf-8"))
    decision["need_type"] = EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value
    decision_file.write_text(json.dumps(decision), encoding="utf-8")

    assert state["currentness_integrity_state"] == "VALID"
    assert reloaded.is_evidence_need_current(candidate["evidence_need_id"]) is True
    assert reloaded.get_current_evidence_need_state(
        candidate["evidence_need_id"]
    )["current_decision_id"] == state["current_decision_id"]
