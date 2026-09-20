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
from runtime.evidence.validation_request import (
    REQUEST_SCOPE_BY_SPONSORSHIP_SCOPE,
    ValidationRequestAuthorityEngine,
    ValidationRequestStatus,
)
from runtime.evidence.validation_sponsorship import (
    NEED_TYPE_TO_SCOPE,
    ValidationSponsorshipAuthorityEngine,
    ValidationSponsorshipScope,
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


def _request_engine(tmp_path, sponsor):
    return ValidationRequestAuthorityEngine(
        tmp_path / "requests",
        sponsorship_authority=sponsor,
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


def _active_sponsorship(
    tmp_path,
    need_type=EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value,
):
    need_engine, need_state = _active_need(tmp_path, need_type)
    sponsor = _sponsor_engine(tmp_path, need_engine)
    candidate = sponsor.candidate_from_current_need(need_state["evidence_need_id"])
    state = sponsor.decide_sponsorship(candidate)["current_state"]
    return need_engine, sponsor, state


def test_active_sponsorship_creates_pending_validation_request(tmp_path):
    _, sponsor, sponsorship_state = _active_sponsorship(tmp_path)
    requests = _request_engine(tmp_path, sponsor)

    candidate = requests.candidate_from_current_sponsorship(
        sponsorship_state["validation_sponsorship_id"]
    )
    decision = requests.decide_request(candidate)

    assert candidate["authority"] == "NONE"
    assert decision["assessment"]["authority"] == "NONE"
    assert decision["authority"] == "VALIDATION_REQUEST_AUTHORITY_ENGINE"
    assert decision["current_state"]["lifecycle_status"] == "PENDING"
    assert requests.is_validation_request_current(candidate["validation_request_id"])
    assert decision["evidence_plan_created"] is False
    assert decision["validation_schedule_created"] is False
    assert decision["validation_execution_started"] is False
    assert decision["raw_evidence_created"] is False
    assert decision["accepted_evidence_created"] is False
    assert decision["current_state"]["qualification_authority"] == "NONE"
    assert decision["current_state"]["selector_authority"] == "NONE"


def test_request_identity_is_sponsorship_and_scope_bound(tmp_path):
    _, sponsor, sponsorship_state = _active_sponsorship(tmp_path)
    requests = _request_engine(tmp_path, sponsor)
    first = requests.candidate_from_current_sponsorship(
        sponsorship_state["validation_sponsorship_id"]
    )
    same = requests.candidate_from_current_sponsorship(
        sponsorship_state["validation_sponsorship_id"]
    )
    _, causal_sponsor, causal_state = _active_sponsorship(
        tmp_path / "causal",
        EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value,
    )
    causal_requests = _request_engine(tmp_path / "causal", causal_sponsor)
    causal = causal_requests.candidate_from_current_sponsorship(
        causal_state["validation_sponsorship_id"]
    )

    assert first["validation_request_id"] == same["validation_request_id"]
    assert first["validation_request_id"] != causal["validation_request_id"]
    assert first["requested_validation_scope"] == "SOURCE_INDEPENDENCE"
    assert causal["requested_validation_scope"] == "CAUSAL_SUPPORT"


def test_missing_sponsorship_and_unauthorized_producers_are_denied(tmp_path):
    need_engine, need_state = _active_need(tmp_path)
    sponsor = _sponsor_engine(tmp_path, need_engine)
    requests = _request_engine(tmp_path, sponsor)

    missing = requests.candidate_from_current_sponsorship("missing_sponsorship")
    missing_decision = requests.decide_request(missing)
    assert missing_decision["decision"]["decision_state"] == (
        "DENIED_NO_CURRENT_VALIDATION_SPONSORSHIP"
    )

    producers = [
        "CurrentEvidenceNeedAuthorityEngine",
        "IntegratedCapabilityQualificationEngine",
        "TaskFailure",
        "TaskSuccess",
        "TrainingAssistant",
        "EvidenceGenerationEngine",
        "IntentManager",
        "GoalManager",
        "PlanningEngine",
    ]
    for producer in producers:
        candidate = requests.candidate_from_current_sponsorship(
            need_state["evidence_need_id"],
            producer=producer,
        )
        decision = requests.decide_request(candidate)
        assert decision["decision"]["decision_state"] in {
            "DENIED_WRONG_AUTHORITY",
            "DENIED_NO_CURRENT_VALIDATION_SPONSORSHIP",
        }
        assert decision["evidence_plan_created"] is False


def test_non_current_need_and_sponsorship_states_break_request_currentness(tmp_path):
    for transition in ("satisfied_need", "review_need", "revoked", "consumed", "expired"):
        need_engine, sponsor, sponsorship_state = _active_sponsorship(
            tmp_path / transition
        )
        requests = _request_engine(tmp_path / transition, sponsor)
        candidate = requests.candidate_from_current_sponsorship(
            sponsorship_state["validation_sponsorship_id"]
        )
        request_state = requests.decide_request(candidate)["current_state"]

        if transition == "satisfied_need":
            need_engine.satisfy_need(
                sponsorship_state["evidence_need_id"],
                current_support_summary={
                    "independent_source_count": 2,
                    "required_independent_sources": 2,
                },
            )
        elif transition == "review_need":
            need_engine.open_review(
                sponsorship_state["evidence_need_id"],
                review_reason="changed",
            )
        elif transition == "revoked":
            sponsor.revoke_sponsorship(
                sponsorship_state["validation_sponsorship_id"],
                revocation_reason="governance_withdrawn",
            )
        elif transition == "consumed":
            sponsor.consume_sponsorship(
                sponsorship_state["validation_sponsorship_id"],
                consumer="controlled_test",
            )
        else:
            sponsor.expire_sponsorship(
                sponsorship_state["validation_sponsorship_id"],
                expiration_reason="stale",
            )

        assert requests.is_validation_request_current(
            request_state["validation_request_id"]
        ) is False
        replay = requests.candidate_from_current_sponsorship(
            sponsorship_state["validation_sponsorship_id"]
        )
        replay_decision = requests.decide_request(replay)
        assert replay_decision["decision"]["decision_state"] == (
            "DENIED_NO_CURRENT_VALIDATION_SPONSORSHIP"
        )


def test_duplicate_plan_and_schedule_deduplication(tmp_path):
    _, sponsor, sponsorship_state = _active_sponsorship(tmp_path)
    requests = _request_engine(tmp_path, sponsor)
    candidate = requests.candidate_from_current_sponsorship(
        sponsorship_state["validation_sponsorship_id"]
    )
    first = requests.decide_request(candidate)
    second = requests.decide_request(candidate)

    assert first["decision"]["decision_state"] == "VALIDATION_REQUEST_PENDING"
    assert second["decision"]["decision_state"] == "VALIDATION_REQUEST_ALREADY_PENDING"
    assert len(requests.list_current_validation_requests()) == 1

    _, plan_sponsor, plan_sponsorship = _active_sponsorship(tmp_path / "plan")
    plan_requests = _request_engine(tmp_path / "plan", plan_sponsor)
    plan_candidate = plan_requests.candidate_from_current_sponsorship(
        plan_sponsorship["validation_sponsorship_id"],
        existing_plan_index=[{"evidence_plan_id": "plan_existing"}],
    )
    schedule_candidate = plan_requests.candidate_from_current_sponsorship(
        plan_sponsorship["validation_sponsorship_id"],
        pending_work_index=[{"schedule_id": "schedule_existing"}],
    )
    assert plan_requests.decide_request(plan_candidate)["decision"][
        "decision_state"
    ] == "PLAN_ALREADY_COVERS_REQUEST"
    assert plan_requests.decide_request(schedule_candidate)["decision"][
        "decision_state"
    ] == "VALIDATION_ALREADY_SCHEDULED"
    assert plan_requests.list_current_validation_requests() == []


def test_cross_boundary_and_fingerprint_attacks_fail_closed(tmp_path):
    _, sponsor, sponsorship_state = _active_sponsorship(tmp_path)
    requests = _request_engine(tmp_path, sponsor)
    candidate = requests.candidate_from_current_sponsorship(
        sponsorship_state["validation_sponsorship_id"]
    )
    requests.decide_request(candidate)

    for field, value in (
        ("evidence_need_id", "need_other"),
        ("validation_sponsorship_id", "sponsorship_other"),
        ("need_type", EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value),
        ("requested_validation_scope", "CAUSAL_SUPPORT"),
    ):
        attacked = json.loads(json.dumps(candidate))
        attacked[field] = value
        if field in {"evidence_need_id", "validation_sponsorship_id", "need_type"}:
            attacked["subject"][field] = value
        decision = requests.decide_request(attacked)
        assert decision["decision"]["decision_state"] in {
            "DENIED_VALIDATION_REQUEST_INTEGRITY_FAILURE",
            "DENIED_NO_CURRENT_VALIDATION_SPONSORSHIP",
            "DENIED_CROSS_BOUNDARY_REQUEST",
        }

    attacked = json.loads(json.dumps(candidate))
    attacked["subject"]["capability_id"] = "capability_other"
    attacked["candidate_fingerprint"] = "corrupt"
    assert requests.decide_request(attacked)["decision"]["decision_state"] == (
        "DENIED_VALIDATION_REQUEST_INTEGRITY_FAILURE"
    )

    assert requests.is_validation_request_current(
        candidate["validation_request_id"],
        expected_capability_id="capability_other",
    ) is False


def test_consumed_and_persistence_replay_do_not_restore_currentness(tmp_path):
    _, sponsor, sponsorship_state = _active_sponsorship(tmp_path)
    requests = _request_engine(tmp_path, sponsor)
    candidate = requests.candidate_from_current_sponsorship(
        sponsorship_state["validation_sponsorship_id"]
    )
    state = requests.decide_request(candidate)["current_state"]
    consumed = requests.consume_request(
        candidate["validation_request_id"],
        evidence_plan_id="evidence_plan_a",
        consumer="EvidencePlanAuthority",
    )
    assert consumed["current_state"]["lifecycle_status"] == (
        ValidationRequestStatus.CONSUMED_TO_EVIDENCE_PLAN.value
    )
    assert requests.is_validation_request_current(
        candidate["validation_request_id"]
    ) is False

    current_path = (
        tmp_path
        / "requests"
        / "current"
        / f"{candidate['validation_request_id']}.json"
    )
    copied = dict(state)
    copied["state_fingerprint"] = "copied_stale_fingerprint"
    current_path.write_text(json.dumps(copied), encoding="utf-8")
    restored = requests.get_current_validation_request(
        candidate["validation_request_id"]
    )

    assert restored["currentness_integrity_state"] == "INVALID"
    assert requests.is_validation_request_current(
        candidate["validation_request_id"]
    ) is False


def test_need_type_request_scope_controls_are_preserved(tmp_path):
    for need_type, sponsorship_scope in NEED_TYPE_TO_SCOPE.items():
        _, sponsor, sponsorship_state = _active_sponsorship(tmp_path / need_type, need_type)
        requests = _request_engine(tmp_path / need_type, sponsor)
        candidate = requests.candidate_from_current_sponsorship(
            sponsorship_state["validation_sponsorship_id"]
        )
        decision = requests.decide_request(candidate)

        assert candidate["requested_validation_scope"] == (
            REQUEST_SCOPE_BY_SPONSORSHIP_SCOPE[sponsorship_scope]
        )
        assert decision["current_state"]["requested_validation_scope"] == (
            REQUEST_SCOPE_BY_SPONSORSHIP_SCOPE[sponsorship_scope]
        )
        assert decision["current_state"]["evidence_need"]["validation_sponsorship_id"] == (
            sponsorship_state["validation_sponsorship_id"]
        )
        assert decision["evidence_plan_created"] is False
