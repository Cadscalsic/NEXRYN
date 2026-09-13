from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from runtime.evidence.current_evidence_need import CurrentEvidenceNeedAuthorityEngine
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.evidence.natural_validation_orchestrator import (
    NaturalCanonicalValidationOrchestrator,
)
from runtime.evidence.validation_request import ValidationRequestAuthorityEngine
from runtime.evidence.validation_sponsorship import (
    ValidationSponsorshipAuthorityEngine,
)


def _subject(operation="replace_color", domain="color"):
    return {
        "capability_name": f"{operation}_capability",
        "operation": operation,
        "domain": domain,
        "context_class": "qualification",
        "evidence_scope": "capability_support",
    }


def _accepted(evidence_id, *, subject=None, source="source_a", causal=True):
    subject = subject or _subject()
    return {
        "accepted_evidence_id": evidence_id,
        "evidence_acceptance_state": "ACCEPTED",
        "evidence_decision_id": f"decision_{evidence_id}",
        "accepted_evidence_current_state": {
            "current_status": "ACTIVE",
            "is_currently_accepted": True,
        },
        "claim_id": "claim_replace_color",
        "claim_evidence_binding_state": "BOUND",
        "claim_evidence_binding": {
            "claim_id": "claim_replace_color",
            "accepted_evidence_id": evidence_id,
        },
        "claim_subject": {
            "kind": "candidate_operation",
            "operation": subject["operation"],
        },
        "capability_id": capability_id_for_subject(subject),
        "capability_subject": subject,
        "canonical_source_identity": source,
        "producer_operation_id": source,
        "producer_component_id": "validation_task_execution_pipeline",
        "producer_source_type": "scheduled_validation_task",
        "source_lineage": [source],
        "source_provenance": {
            "source_provenance_state": "SOURCE_PROVENANCE_BOUND",
            "canonical_source_identity": source,
            "producer_operation_id": source,
            "producer_component_id": "validation_task_execution_pipeline",
            "producer_source_type": "scheduled_validation_task",
            "source_lineage": [source],
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


def _qualification_deficit():
    subject = _subject()
    return IntegratedCapabilityQualificationEngine().decide(
        subject,
        [_accepted("evidence_a", subject=subject, source="source_a")],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
    )


def _orchestrator(tmp_path):
    need = CurrentEvidenceNeedAuthorityEngine(tmp_path / "needs")
    sponsorship = ValidationSponsorshipAuthorityEngine(
        tmp_path / "sponsorships",
        need_authority=need,
    )
    request = ValidationRequestAuthorityEngine(
        tmp_path / "requests",
        sponsorship_authority=sponsorship,
    )
    store = EvidenceAcquisitionPlanStore(tmp_path / "plans")
    return NaturalCanonicalValidationOrchestrator(
        need_authority=need,
        sponsorship_authority=sponsorship,
        request_authority=request,
        evidence_plan_store=store,
    )


def test_natural_qualification_deficit_reaches_canonical_plan_admission(tmp_path):
    orchestrator = _orchestrator(tmp_path)

    report = orchestrator.orchestrate([_qualification_deficit()], max_new_needs=1)

    assert report["authority"] == "NONE"
    assert report["natural_deficit_count"] == 1
    assert report["natural_need_candidate_count"] == 1
    assert report["natural_active_need_count"] == 1
    assert report["natural_active_sponsorship_count"] == 1
    assert report["natural_pending_request_count"] == 1
    assert report["natural_plan_created_count"] == 1
    row = report["orchestration_rows"][0]
    assert row["orchestration_state"] == "REQUEST_ROUTED_TO_EVIDENCE_PLAN_ADMISSION"
    assert row["plan_admission_report"]["request_consumed"] is True
    assert report["raw_evidence_created_directly"] is False
    assert report["accepted_evidence_created_directly"] is False
    assert report["realized_yield_selector_consumption"] is False


def test_replayed_deficit_reuses_current_need_and_blocks_duplicate_plan(tmp_path):
    orchestrator = _orchestrator(tmp_path)
    deficit = _qualification_deficit()

    first = orchestrator.orchestrate([deficit], max_new_needs=1)
    second = orchestrator.orchestrate([deficit], max_new_needs=1)

    assert first["natural_plan_created_count"] == 1
    assert second["natural_active_need_ids"] == first["natural_active_need_ids"]
    assert second["natural_plan_created_count"] == 0
    row = second["orchestration_rows"][0]
    assert row["need_decision_state"] == "CURRENT_NEED_ALREADY_ACTIVE"
    assert row["orchestration_state"] == "REQUEST_NOT_PENDING_PLAN_BLOCKED"
    assert row["request_decision_state"] == "PLAN_ALREADY_COVERS_REQUEST"


def test_no_deficit_does_not_create_natural_need(tmp_path):
    subject = _subject()
    qualified = IntegratedCapabilityQualificationEngine().decide(
        subject,
        [
            _accepted("evidence_a", subject=subject, source="source_a"),
            _accepted("evidence_b", subject=subject, source="source_b"),
        ],
        requested_level=CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
    )

    report = _orchestrator(tmp_path).orchestrate([qualified], max_new_needs=1)

    assert report["natural_deficit_count"] == 0
    assert report["natural_need_candidate_count"] == 0
    assert report["natural_active_need_count"] == 0
    assert report["natural_pending_request_count"] == 0
    assert report["orchestration_rows"][0]["eligibility_state"] == (
        "INELIGIBLE_NO_CURRENT_PROMOTION_DEFICIT"
    )


def test_component_binding_preserves_capability_and_requirement(tmp_path):
    orchestrator = _orchestrator(tmp_path)
    deficit = _qualification_deficit()

    report = orchestrator.orchestrate([deficit], max_new_needs=1)
    row = report["orchestration_rows"][0]
    plan = row["plan_admission_report"]

    assert row["active_need_id"]
    assert row["active_sponsorship_id"]
    assert row["pending_request_id"]
    assert plan["source_evidence_need_id"] == row["active_need_id"]
    assert plan["source_validation_sponsorship_id"] == row["active_sponsorship_id"]
    assert plan["source_validation_request_id"] == row["pending_request_id"]


def test_historical_deficit_cannot_masquerade_as_current(tmp_path):
    orchestrator = _orchestrator(tmp_path)
    deficit = _qualification_deficit()
    candidate = orchestrator.need_authority.candidates_from_qualification_deficit(
        deficit
    )[0]

    decision = orchestrator.need_authority.decide_current_need(
        candidate,
        current_source_decision_id="different_current_qualification_decision",
    )

    assert decision["decision"]["decision_state"] == "DENIED_STALE_DEFICIT"
    assert decision["current_state"]["lifecycle_status"] == "INVALIDATED"
    assert decision["validation_sponsorship_created"] is False
    assert decision["evidence_plan_created"] is False


def test_authority_isolation_preserved_through_plan_admission(tmp_path):
    orchestrator = _orchestrator(tmp_path)

    report = orchestrator.orchestrate([_qualification_deficit()], max_new_needs=1)
    row = report["orchestration_rows"][0]
    need = orchestrator.need_authority.get_current_evidence_need_state(
        row["active_need_id"]
    )
    sponsorship = (
        orchestrator.sponsorship_authority.get_current_validation_sponsorship(
            row["active_sponsorship_id"]
        )
    )
    plan_report = row["plan_admission_report"]

    assert report["authority"] == "NONE"
    assert report["behavioral_authority"] == "NONE"
    assert need["authority"] == "CURRENT_EVIDENCE_NEED_AUTHORITY_ENGINE"
    assert sponsorship["qualification_authority"] == "NONE"
    assert plan_report["accepted_evidence_created"] is False
    assert plan_report["raw_evidence_created"] is False
