import json
from pathlib import Path

from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.evidence.validation_request import ValidationRequestAuthorityEngine
from tests.test_validation_request_authority import _active_sponsorship


def _chain(tmp_path):
    need_engine, sponsor, sponsorship_state = _active_sponsorship(tmp_path)
    requests = ValidationRequestAuthorityEngine(
        tmp_path / "requests",
        sponsorship_authority=sponsor,
    )
    request_candidate = requests.candidate_from_current_sponsorship(
        sponsorship_state["validation_sponsorship_id"]
    )
    request_state = requests.decide_request(request_candidate)["current_state"]
    store = EvidenceAcquisitionPlanStore(tmp_path / "plans")
    return need_engine, sponsor, requests, store, sponsorship_state, request_state


def test_pending_validation_request_admits_evidence_plan_and_then_consumes_request(tmp_path):
    _, _, requests, store, sponsorship_state, request_state = _chain(tmp_path)

    assessment = store.assess_validation_request_admission(
        request_state["validation_request_id"],
        request_authority=requests,
    )
    report = store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=requests,
    )

    assert assessment["authority"] == "NONE"
    assert assessment["plan_authority"] == "EVIDENCE_ACQUISITION_PLAN_STORE"
    assert report["evidence_plan_storage_state"] == "NEW_PLAN_PERSISTED"
    assert report["evidence_plan_created"] is True
    assert report["request_consumed"] is True
    assert requests.is_validation_request_current(
        request_state["validation_request_id"]
    ) is False
    assert report["source_validation_sponsorship_id"] == (
        sponsorship_state["validation_sponsorship_id"]
    )
    assert report["source_evidence_need_id"] == sponsorship_state["evidence_need_id"]
    assert report["validation_schedule_created"] is False
    assert report["validation_execution_started"] is False
    assert report["raw_evidence_created"] is False
    assert report["accepted_evidence_created"] is False

    plan_path = Path(report["evidence_plan_storage_path"])
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["source_validation_request_id"] == request_state["validation_request_id"]
    assert plan["source_validation_request_decision_id"] == (
        request_state["current_decision_id"]
    )
    assert plan["source_validation_sponsorship_id"] == (
        sponsorship_state["validation_sponsorship_id"]
    )
    assert plan["source_evidence_need_id"] == sponsorship_state["evidence_need_id"]
    assert plan["plan_id"] != request_state["validation_request_id"]
    assert plan["plan_authority"] == "EVIDENCE_ACQUISITION_PLAN_STORE"
    assert plan["execution_authority"] == "NONE"


def test_no_stale_or_consumed_request_can_create_plan(tmp_path):
    _, _, requests, store, _, request_state = _chain(tmp_path)
    store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=requests,
    )

    replay = store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=requests,
    )
    missing = store.admit_validation_request_to_plan(
        "missing_validation_request",
        request_authority=requests,
    )

    assert replay["evidence_plan_storage_state"] == (
        "DENIED_NO_CURRENT_VALIDATION_REQUEST"
    )
    assert replay["request_consumed"] is False
    assert missing["evidence_plan_storage_state"] == (
        "DENIED_NO_CURRENT_VALIDATION_REQUEST"
    )
    assert missing["evidence_plan_created"] is False


def test_satisfied_need_and_revoked_sponsorship_deny_preplan(tmp_path):
    need_engine, sponsor, requests, store, sponsorship_state, request_state = _chain(
        tmp_path / "need"
    )
    need_engine.satisfy_need(
        sponsorship_state["evidence_need_id"],
        current_support_summary={
            "independent_source_count": 2,
            "required_independent_sources": 2,
        },
    )
    need_denied = store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=requests,
    )

    _, sponsor2, requests2, store2, sponsorship_state2, request_state2 = _chain(
        tmp_path / "sponsorship"
    )
    sponsor2.revoke_sponsorship(
        sponsorship_state2["validation_sponsorship_id"],
        revocation_reason="governance_withdrawn",
    )
    sponsor_denied = store2.admit_validation_request_to_plan(
        request_state2["validation_request_id"],
        request_authority=requests2,
    )

    assert need_denied["evidence_plan_storage_state"] == (
        "DENIED_NO_CURRENT_VALIDATION_REQUEST"
    )
    assert sponsor_denied["evidence_plan_storage_state"] == (
        "DENIED_NO_CURRENT_VALIDATION_REQUEST"
    )
    assert requests.is_validation_request_current(
        request_state["validation_request_id"]
    ) is False
    assert requests2.is_validation_request_current(
        request_state2["validation_request_id"]
    ) is False


def test_existing_plan_reuse_consumes_request_without_duplicate_plan(tmp_path):
    _, _, requests, store, _, request_state = _chain(tmp_path)
    request = requests.get_current_validation_request(
        request_state["validation_request_id"]
    )
    existing = store.persist_plan(store.plan_from_validation_request(request))
    report = store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=requests,
    )

    assert existing["evidence_plan_storage_state"] == "NEW_PLAN_PERSISTED"
    assert report["evidence_plan_storage_state"] == "EQUIVALENT_PENDING_PLAN_REUSED"
    assert report["evidence_plan_created"] is False
    assert report["request_consumed"] is True
    assert report["evidence_plan_id"] == existing["evidence_plan_id"]
    assert len(list((tmp_path / "plans" / "pending").glob("*.json"))) == 1


def test_orphaned_historical_plan_does_not_block_current_request(tmp_path):
    _, _, requests, store, _, request_state = _chain(tmp_path)
    request = requests.get_current_validation_request(
        request_state["validation_request_id"]
    )
    orphan = store.normalize_plan(store.plan_from_validation_request(request))
    archive = tmp_path / "plans" / "archive"
    archive.mkdir(parents=True)
    (archive / f"{orphan['plan_id']}.json").write_text(
        json.dumps({**orphan, "lifecycle_state": "ARCHIVED"}),
        encoding="utf-8",
    )

    report = store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=requests,
    )

    assert report["evidence_plan_storage_state"] == "NEW_PLAN_PERSISTED"
    assert report["request_consumed"] is True


def test_plan_persistence_failure_does_not_consume_request(tmp_path, monkeypatch):
    _, _, requests, store, _, request_state = _chain(tmp_path)

    def fail_persist(raw_plan):
        return {
            "evidence_plan_storage_state": "PLAN_REJECTED_INVALID",
            "evidence_plan_persisted": False,
            "evidence_plan_id": "failed_plan",
            "plan_persistence_failure_reason": "simulated_failure",
        }

    monkeypatch.setattr(store, "persist_plan", fail_persist)
    report = store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=requests,
    )

    assert report["evidence_plan_storage_state"] == "PLAN_REJECTED_INVALID"
    assert report["request_consumed"] is False
    assert requests.is_validation_request_current(
        request_state["validation_request_id"]
    ) is True


def test_schedule_and_governance_blocks_deny_without_consumption(tmp_path):
    _, _, requests, store, _, request_state = _chain(tmp_path)

    scheduled = store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=requests,
        active_schedule_index=[{"schedule_id": "schedule_existing"}],
    )
    blocked = store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=requests,
        governance_blocks=["operator_hold"],
    )

    assert scheduled["evidence_plan_storage_state"] == "VALIDATION_ALREADY_SCHEDULED"
    assert blocked["evidence_plan_storage_state"] == "DENIED_GOVERNANCE_BLOCK"
    assert scheduled["request_consumed"] is False
    assert blocked["request_consumed"] is False
    assert requests.is_validation_request_current(
        request_state["validation_request_id"]
    ) is True
