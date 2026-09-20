import json

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from runtime.evidence.current_evidence_need import (
    CurrentEvidenceNeedAuthorityEngine,
    DeficitSignalType,
    EvidenceNeedType,
)
from runtime.evidence.validation_sponsorship import (
    NEED_TYPE_TO_SCOPE,
    ValidationSponsorshipAuthorityEngine,
    ValidationSponsorshipScope,
    ValidationSponsorshipStatus,
)


def _subject(operation="replace_color", domain="color"):
    return {
        "capability_name": f"{operation}_capability",
        "operation": operation,
        "domain": domain,
        "context_class": "qualification",
        "evidence_scope": "capability_support",
    }


def _accepted(evidence_id, *, source="source_a", causal=True, claim_id="claim_a"):
    subject = _subject()
    return {
        "accepted_evidence_id": evidence_id,
        "evidence_acceptance_state": "ACCEPTED",
        "accepted_evidence_current_state": {
            "current_status": "ACTIVE",
            "is_currently_accepted": True,
        },
        "claim_id": claim_id,
        "claim_evidence_binding_state": "BOUND",
        "claim_evidence_binding": {
            "claim_id": claim_id,
            "accepted_evidence_id": evidence_id,
        },
        "claim_subject": {
            "kind": "candidate_operation",
            "operation": subject["operation"],
        },
        "capability_id": capability_id_for_subject(subject),
        "target_operation": subject["operation"],
        "evidence_direction": "SUPPORTING",
        "producer_operation_id": source,
        "producer_component_id": "validation_task_execution_pipeline",
        "producer_source_type": "scheduled_validation_task",
        "source_lineage": [source],
        "source_run_id": f"run_{source}",
        "selected_validation_task_id": f"task_{source}",
        "source_provenance": {
            "source_provenance_state": "SOURCE_PROVENANCE_BOUND",
            "producer_operation_id": source,
            "producer_component_id": "validation_task_execution_pipeline",
            "producer_source_type": "scheduled_validation_task",
            "source_lineage": [source],
            "run_id": f"run_{source}",
            "task_id": f"task_{source}",
            "raw_validation_result_id": f"raw_{evidence_id}",
            "origin_task_execution_id": f"execution_{evidence_id}",
            "origin_run_id": f"run_{source}",
            "origin_task_id": f"task_{source}",
            "origin_attempt_id": f"attempt_{evidence_id}",
            "origin_operation_id": source,
            "origin_lineage_fingerprint": f"origin_fp_{evidence_id}",
        },
        "accepted_evidence_origin": {
            "accepted_evidence_origin_state": "TASK_ORIGIN_PRESERVED",
            "raw_evidence_id": f"raw_{evidence_id}",
            "raw_result_id": f"raw_{evidence_id}",
            "origin_task_execution_id": f"execution_{evidence_id}",
            "origin_run_id": f"run_{source}",
            "origin_task_id": f"task_{source}",
            "origin_attempt_id": f"attempt_{evidence_id}",
            "origin_operation_id": source,
            "origin_lineage_fingerprint": f"origin_fp_{evidence_id}",
            "authority": "NONE",
            "behavioral_authority": "NONE",
        },
        "accepted_evidence_origin_state": "TASK_ORIGIN_PRESERVED",
        "capability_causal_support_state": (
            "CAUSALLY_SUPPORTED" if causal else "OBSERVED_ONLY"
        ),
    }


def _qualification(evidence):
    return IntegratedCapabilityQualificationEngine().decide(
        _subject(),
        evidence,
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
    )


def _need_engine(tmp_path):
    return CurrentEvidenceNeedAuthorityEngine(tmp_path / "needs")


def _sponsor_engine(tmp_path, need_engine):
    return ValidationSponsorshipAuthorityEngine(
        tmp_path / "sponsorships",
        need_authority=need_engine,
    )


def _active_need(tmp_path, need_type=EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value):
    need_engine = _need_engine(tmp_path)
    result = _qualification([_accepted("evidence_a", source="source_a", causal=True)])
    try:
        candidate = need_engine.candidate_from_qualification_deficit(
            result,
            need_type=need_type,
        )
    except Exception:
        qd = result["qualification_decision"]
        subject = qd["capability_subject"]
        candidate = need_engine.propose_candidate(
            subject={
                "target_type": "capability",
                "capability_id": qd["capability_id"],
                "qualification_subject_id": qd["capability_id"],
                "domain": subject.get("domain"),
                "context_class": "qualification",
                "evidence_scope": "capability_support",
            },
            need_type=need_type,
            deficit_signal_type=DeficitSignalType.REVALIDATION_DEFICIT.value,
            source_deficit_refs=[
                {
                    "source_decision_id": qd["qualification_decision_id"],
                    "source_authority": qd["qualification_authority"],
                    "source_failure": "controlled_revalidation_required",
                }
            ],
            current_support_summary={"revalidation_state": "REVALIDATION_REQUIRED"},
            proposal_reason="controlled_revalidation_required",
            producer="CurrentEvidenceNeedAuthorityEngine",
            provenance={
                "source": "controlled_need_fixture",
                "source_deficit_current": True,
            },
        )
    decision = need_engine.decide_current_need(candidate)
    return need_engine, decision["current_state"]


def test_active_current_need_creates_active_validation_sponsorship(tmp_path):
    need_engine, need_state = _active_need(tmp_path)
    sponsor = _sponsor_engine(tmp_path, need_engine)

    candidate = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
    decision = sponsor.decide_sponsorship(candidate)

    assert candidate["authority"] == "NONE"
    assert decision["assessment"]["authority"] == "NONE"
    assert decision["authority"] == "VALIDATION_SPONSORSHIP_AUTHORITY_ENGINE"
    assert decision["current_state"]["lifecycle_status"] == "ACTIVE"
    assert sponsor.is_validation_sponsorship_current(
        candidate["validation_sponsorship_id"]
    )
    assert decision["validation_request_created"] is False
    assert decision["evidence_plan_created"] is False
    assert decision["validation_schedule_created"] is False
    assert decision["raw_evidence_created"] is False
    assert decision["accepted_evidence_created"] is False


def test_sponsorship_identity_is_semantic_and_scope_bound(tmp_path):
    need_engine, need_state = _active_need(tmp_path)
    sponsor = _sponsor_engine(tmp_path, need_engine)

    first = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
    same = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
    causal_need_engine, causal_state = _active_need(
        tmp_path / "causal",
        EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value,
    )
    causal_sponsor = _sponsor_engine(tmp_path / "causal", causal_need_engine)
    causal = causal_sponsor.candidate_from_current_need(
        causal_state["evidence_need_id"]
    )

    assert first["validation_sponsorship_id"] == same["validation_sponsorship_id"]
    assert first["validation_sponsorship_id"] != causal["validation_sponsorship_id"]
    assert first["requested_validation_scope"] == (
        ValidationSponsorshipScope.INDEPENDENT_SOURCE_VALIDATION.value
    )
    assert causal["requested_validation_scope"] == (
        ValidationSponsorshipScope.CAUSAL_SUPPORT_VALIDATION.value
    )


def test_non_active_need_states_cannot_sponsor(tmp_path):
    need_engine, need_state = _active_need(tmp_path)
    sponsor = _sponsor_engine(tmp_path, need_engine)
    active_candidate = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
    active = sponsor.decide_sponsorship(active_candidate)

    need_engine.satisfy_need(
        need_state["evidence_need_id"],
        current_support_summary={
            "independent_source_count": 2,
            "required_independent_sources": 2,
        },
    )
    denied = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
    decision = sponsor.decide_sponsorship(denied)

    assert decision["decision"]["decision_state"] == "DENIED_NEED_NOT_CURRENT"
    assert sponsor.is_validation_sponsorship_current(
        active["current_state"]["validation_sponsorship_id"]
    ) is False


def test_under_review_invalidated_superseded_need_breaks_sponsorship(tmp_path):
    for transition in ("review", "invalidate", "supersede", "revalidate"):
        need_engine, need_state = _active_need(tmp_path / transition)
        sponsor = _sponsor_engine(tmp_path / transition, need_engine)
        candidate = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
        state = sponsor.decide_sponsorship(candidate)["current_state"]
        if transition == "review":
            need_engine.open_review(need_state["evidence_need_id"], review_reason="changed")
        elif transition == "invalidate":
            need_engine.invalidate_need(
                need_state["evidence_need_id"],
                invalidation_reason="invalid",
            )
        elif transition == "supersede":
            need_engine.supersede_need(
                need_state["evidence_need_id"],
                replacement_evidence_need_id="replacement_need",
                supersession_reason="changed",
            )
        else:
            need_engine.require_revalidation(
                need_state["evidence_need_id"],
                revalidation_reason="support_lost",
            )
        assert sponsor.is_validation_sponsorship_current(
            state["validation_sponsorship_id"]
        ) is False


def test_duplicate_sponsorship_and_consumed_replay_are_not_current(tmp_path):
    need_engine, need_state = _active_need(tmp_path)
    sponsor = _sponsor_engine(tmp_path, need_engine)
    candidate = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
    first = sponsor.decide_sponsorship(candidate)
    second = sponsor.decide_sponsorship(candidate)
    assert second["decision"]["decision_state"] == "CURRENT_SPONSORSHIP_ALREADY_ACTIVE"
    assert len(sponsor.list_current_validation_sponsorships()) == 1

    consumed = sponsor.consume_sponsorship(
        candidate["validation_sponsorship_id"],
        consumer="controlled_test",
    )

    assert consumed["current_state"]["lifecycle_status"] == "CONSUMED"
    assert sponsor.is_validation_sponsorship_current(
        candidate["validation_sponsorship_id"]
    ) is False


def test_current_plan_and_pending_work_dedup_deny_redundant_sponsorship(tmp_path):
    need_engine, need_state = _active_need(tmp_path)
    sponsor = _sponsor_engine(tmp_path, need_engine)
    plan_candidate = sponsor.candidate_from_current_need(
        need_state["evidence_need_id"],
        existing_plan_index=[{"plan_id": "plan_existing"}],
    )
    pending_candidate = sponsor.candidate_from_current_need(
        need_state["evidence_need_id"],
        pending_work_index=[{"validation_request_id": "request_existing"}],
    )

    plan = sponsor.decide_sponsorship(plan_candidate)
    pending = sponsor.decide_sponsorship(pending_candidate)

    assert plan["decision"]["decision_state"] == "PLAN_ALREADY_COVERS_NEED"
    assert pending["decision"]["decision_state"] == (
        "PENDING_WORK_ALREADY_COVERS_NEED"
    )
    assert sponsor.list_current_validation_sponsorships() == []


def test_cross_type_capability_claim_and_scope_attacks_fail_closed(tmp_path):
    need_engine, need_state = _active_need(tmp_path)
    sponsor = _sponsor_engine(tmp_path, need_engine)
    candidate = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
    sponsor.decide_sponsorship(candidate)
    subject = candidate["subject"]

    assert sponsor.is_validation_sponsorship_current(
        candidate["validation_sponsorship_id"],
        expected_capability_id=subject["capability_id"],
        expected_need_type=subject["need_type"],
        expected_validation_scope=subject["validation_scope"],
    )
    assert sponsor.is_validation_sponsorship_current(
        candidate["validation_sponsorship_id"],
        expected_capability_id="capability_other",
    ) is False
    assert sponsor.is_validation_sponsorship_current(
        candidate["validation_sponsorship_id"],
        expected_need_type=EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value,
    ) is False
    assert sponsor.is_validation_sponsorship_current(
        candidate["validation_sponsorship_id"],
        expected_validation_scope=ValidationSponsorshipScope.CAUSAL_SUPPORT_VALIDATION.value,
    ) is False
    assert sponsor.is_validation_sponsorship_current(
        candidate["validation_sponsorship_id"],
        expected_claim_id="claim_other",
    ) is False


def test_invalid_scope_and_fingerprint_corruption_fail_closed(tmp_path):
    need_engine, need_state = _active_need(tmp_path)
    sponsor = _sponsor_engine(tmp_path, need_engine)
    invalid_scope = sponsor.candidate_from_current_need(
        need_state["evidence_need_id"],
        validation_scope=ValidationSponsorshipScope.CAUSAL_SUPPORT_VALIDATION.value,
    )
    invalid_decision = sponsor.decide_sponsorship(invalid_scope)
    assert invalid_decision["decision"]["decision_state"] == (
        "DENIED_INVALID_VALIDATION_SCOPE"
    )

    candidate = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
    candidate["subject"]["capability_id"] = "capability_tampered"
    corrupted = sponsor.decide_sponsorship(candidate)
    assert corrupted["decision"]["decision_state"] == (
        "DENIED_SPONSORSHIP_INTEGRITY_FAILURE"
    )


def test_copied_sponsorship_and_persistence_do_not_restore_currentness(tmp_path):
    need_engine, need_state = _active_need(tmp_path)
    sponsor = _sponsor_engine(tmp_path, need_engine)
    candidate = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
    active = sponsor.decide_sponsorship(candidate)["current_state"]
    sponsor.revoke_sponsorship(
        candidate["validation_sponsorship_id"],
        revocation_reason="governance_withdrawn",
    )
    current_path = (
        tmp_path
        / "sponsorships"
        / "current"
        / f"{candidate['validation_sponsorship_id']}.json"
    )
    copied = dict(active)
    copied["state_fingerprint"] = "copied_stale_fingerprint"
    current_path.write_text(json.dumps(copied), encoding="utf-8")

    state = sponsor.get_current_validation_sponsorship(
        candidate["validation_sponsorship_id"]
    )
    assert state["currentness_integrity_state"] == "INVALID"
    assert sponsor.is_validation_sponsorship_current(
        candidate["validation_sponsorship_id"]
    ) is False


def test_need_type_scope_controls_are_explicit(tmp_path):
    for need_type, scope in NEED_TYPE_TO_SCOPE.items():
        need_engine, need_state = _active_need(tmp_path / need_type, need_type)
        sponsor = _sponsor_engine(tmp_path / need_type, need_engine)
        candidate = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
        decision = sponsor.decide_sponsorship(candidate)
        assert candidate["requested_validation_scope"] == scope
        assert decision["current_state"]["validation_scope"] == scope
        assert decision["evidence_plan_created"] is False


def test_unauthorized_direct_bypass_attacks_fail_closed(tmp_path):
    need_engine, need_state = _active_need(tmp_path)
    sponsor = _sponsor_engine(tmp_path, need_engine)
    producers = [
        "TaskFailure",
        "TaskSuccess",
        "TrainingAssistant",
        "EvidenceGenerationEngine",
        "IntegratedCapabilityQualificationEngine",
        "IntentManager",
        "GoalManager",
        "PlanningEngine",
    ]

    for producer in producers:
        candidate = sponsor.candidate_from_current_need(
            need_state["evidence_need_id"],
            producer=producer,
        )
        decision = sponsor.decide_sponsorship(candidate)
        assert decision["decision"]["decision_state"] == "DENIED_WRONG_AUTHORITY"
        assert decision["evidence_plan_created"] is False
        assert decision["raw_evidence_created"] is False


def test_missing_need_task_success_and_failure_do_not_create_sponsorship(tmp_path):
    sponsor = _sponsor_engine(tmp_path, _need_engine(tmp_path))
    missing = sponsor.candidate_from_current_need("missing_need")
    decision = sponsor.decide_sponsorship(missing)

    assert decision["decision"]["decision_state"] == "DENIED_NEED_NOT_CURRENT"
    assert decision["validation_request_created"] is False
    assert decision["evidence_plan_created"] is False
    assert decision["raw_evidence_created"] is False
    assert decision["accepted_evidence_created"] is False
