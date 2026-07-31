import json
from pathlib import Path

from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore


def _plan(**overrides):
    plan = {
        "source_run_id": "run_20260730_074151",
        "source_task_id": "task-localized-remap",
        "source_candidate_id": "semantic_program:replace_color",
        "source_operation": "replace_color",
        "evidence_acquisition_state": "EVIDENCE_ACQUISITION_PLAN_READY",
        "evidence_acquisition_trigger": (
            "TIE_CONFIRMED_AFTER_ACCEPTED_SANDBOX_PROBE"
        ),
        "required_evidence_category": "CROSS_SOURCE_CONSENSUS",
        "required_evidence": "cross_source_consensus_evidence",
        "required_validation_task": (
            "select_cross_source_tie_break_validation_task"
        ),
        "tie_break_strategy": "cross_source_consensus",
        "expected_tie_break_impact": "HIGH",
        "target_candidate": "semantic_program:replace_color",
        "target_operation": "replace_color",
        "governed_reentry_action": (
            "reenter_arena_after_required_evidence_without_truth_grant"
        ),
    }
    plan.update(overrides)
    return plan


def test_valid_plan_normalization_and_stable_identity(tmp_path):
    store = EvidenceAcquisitionPlanStore(tmp_path)

    first = store.normalize_plan(_plan())
    second = store.normalize_plan(_plan())

    assert first["schema_version"] == "1.0"
    assert first["plan_id"] == second["plan_id"]
    assert first["plan_fingerprint"] == second["plan_fingerprint"]
    assert first["lifecycle_state"] == "PENDING_NEXT_RUN"
    assert first["consumption_state"] == "NOT_CONSUMED"
    assert first["truth_authority"] == "NONE"
    assert first["trust_authority"] == "NONE"
    assert first["graduation_authority"] == "NONE"
    assert first["execution_authority"] == "NONE"
    assert first["constitutional_boundary"] == (
        "EVIDENCE_ACQUISITION_PLAN_IS_A_GOVERNED_REQUEST_FOR_VALIDATION_NOT_EVIDENCE"
    )


def test_atomic_persistence_and_recovery_after_restart(tmp_path):
    first_store = EvidenceAcquisitionPlanStore(tmp_path)
    persist = first_store.persist_plan(_plan())

    assert persist["evidence_plan_persisted"] is True
    assert persist["evidence_plan_storage_state"] == "NEW_PLAN_PERSISTED"
    assert Path(persist["evidence_plan_storage_path"]).exists()

    second_store = EvidenceAcquisitionPlanStore(tmp_path)
    loaded = second_store.load_pending_plans()

    assert loaded["evidence_plans_loaded_at_boot"] == 1
    assert loaded["pending_evidence_plan_count"] == 1
    plan = loaded["pending_evidence_acquisition_plans"][0]
    assert plan["plan_id"] == persist["evidence_plan_id"]
    assert plan["lifecycle_state"] == "LOADED_AT_BOOT"


def test_duplicate_plan_prevention_reuses_equivalent_pending_plan(tmp_path):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    first = store.persist_plan(_plan())
    second = store.persist_plan(_plan(source_run_id="run_20260731_010101"))

    assert first["evidence_plan_persisted"] is True
    assert second["evidence_plan_persisted"] is False
    assert second["evidence_plan_storage_state"] == (
        "EQUIVALENT_PENDING_PLAN_REUSED"
    )
    assert second["equivalent_pending_plan_found"] is True
    assert second["duplicate_persistence_prevented"] is True
    assert second["evidence_plan_id"] == first["evidence_plan_id"]
    assert len(list((tmp_path / "pending").glob("*.json"))) == 1


def test_corrupted_pending_plan_is_quarantined(tmp_path):
    pending = tmp_path / "pending"
    pending.mkdir(parents=True)
    corrupted = pending / "bad.json"
    corrupted.write_text("{not-json", encoding="utf-8")

    report = EvidenceAcquisitionPlanStore(tmp_path).load_pending_plans()

    assert report["evidence_plans_loaded_at_boot"] == 0
    assert report["quarantined_plan_count"] == 1
    assert not corrupted.exists()
    assert list((tmp_path / "invalid").glob("bad*.json"))


def test_unsupported_schema_and_missing_required_field_are_rejected(tmp_path):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    unsupported = store.normalize_plan(_plan())
    unsupported["schema_version"] = "2.0"
    assert "unsupported_schema_version" in store.validate_plan(unsupported)

    missing = store.persist_plan(_plan(required_evidence=""))
    assert missing["evidence_plan_storage_state"] == "PLAN_REJECTED_INVALID"
    assert "missing_required_fields:required_evidence" in (
        missing["plan_persistence_failure_reason"]
    )
    assert list((tmp_path / "invalid").glob("*.json"))


def test_delivery_and_consumption_pending_do_not_mark_consumed(tmp_path):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan())
    loaded = EvidenceAcquisitionPlanStore(tmp_path).load_pending_plans()
    assert loaded["pending_evidence_acquisition_plans"][0][
        "lifecycle_state"
    ] == "LOADED_AT_BOOT"

    delivery = store.mark_consumption_pending(persisted["evidence_plan_id"])

    assert delivery["training_assistant_plan_available"] is True
    assert delivery["current_run_consumption_expected"] is True
    assert delivery["next_run_consumption_required"] is False
    assert delivery["evidence_plan_lifecycle_state"] == "CONSUMPTION_PENDING"
    stored_plan = json.loads(
        Path(delivery["evidence_plan_storage_path"]).read_text(encoding="utf-8")
    )
    assert stored_plan["consumption_state"] == "CONSUMPTION_PENDING"
    assert stored_plan["consumption_state"] != "CONSUMED"


def test_priority_ordering_is_deterministic(tmp_path):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    low = store.persist_plan(_plan(
        source_task_id="task-low",
        expected_tie_break_impact="MEDIUM",
        required_evidence_category="INDEPENDENT_GOVERNED_VALIDATION",
        required_evidence="repeatable_independent_validation_evidence",
        required_validation_task="select_independent_tie_break_validation_task",
        tie_break_strategy="independent_repeat_validation",
    ))
    high = store.persist_plan(_plan(source_task_id="task-high"))

    loaded = EvidenceAcquisitionPlanStore(tmp_path).load_pending_plans()
    ids = [plan["plan_id"] for plan in loaded["pending_evidence_acquisition_plans"]]

    assert ids[0] == high["evidence_plan_id"]
    assert low["evidence_plan_id"] in ids
