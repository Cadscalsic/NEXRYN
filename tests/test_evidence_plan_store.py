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


def _consumption_report(plan_id, **overrides):
    report = {
        "current_plan_id": plan_id,
        "selection_state": "WAITING_EXECUTION",
        "consumption_state": "MATCHING_COMPLETED",
        "selected_validation_task": "elite_validation_task_31",
        "best_matching_curriculum": "Elite Validation Academy",
        "matching_score": 118.0,
        "matching_explanation": "primary_required_evidence_match",
        "current_required_evidence": "cross_source_consensus_evidence",
        "current_target_operation": "replace_color",
        "current_tie_break_strategy": "cross_source_consensus",
        "selected_validation_task_metadata": {
            "curriculum_id": "elite_validation_academy",
            "validation_contract": "select_cross_source_tie_break_validation_task",
        },
    }
    report.update(overrides)
    return report


def test_selection_lifecycle_is_persisted_atomically_without_new_plan(tmp_path):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan())
    delivery = store.mark_consumption_pending(persisted["evidence_plan_id"])

    sync = store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )

    assert sync["lifecycle_update_attempted"] is True
    assert sync["lifecycle_update_persisted"] is True
    assert sync["evidence_plan_id"] == persisted["evidence_plan_id"]
    assert sync["evidence_plan_fingerprint"] == persisted["evidence_plan_fingerprint"]
    assert sync["persisted_lifecycle_state"] == "WAITING_EXECUTION"
    assert sync["persisted_selected_validation_task"] == "elite_validation_task_31"
    assert sync["execution_state"] == "NOT_SCHEDULED"
    assert sync["execution_authority"] == "NONE"
    assert len(list((tmp_path / "pending").glob("*.json"))) == 1

    stored_plan = json.loads(
        Path(delivery["evidence_plan_storage_path"]).read_text(encoding="utf-8")
    )
    assert stored_plan["lifecycle_state"] == "WAITING_EXECUTION"
    assert stored_plan["consumption_state"] == "MATCHING_COMPLETED"
    assert stored_plan["selected_validation_task_id"] == "elite_validation_task_31"
    assert stored_plan["selected_curriculum_id"] == "elite_validation_academy"
    assert stored_plan["matching_score"] == 118.0
    assert stored_plan["execution_state"] == "NOT_SCHEDULED"
    assert stored_plan["truth_authority"] == "NONE"
    assert stored_plan["trust_authority"] == "NONE"
    assert stored_plan["graduation_authority"] == "NONE"
    assert stored_plan["execution_authority"] == "NONE"


def test_waiting_execution_plan_restores_without_curriculum_reconsumption(tmp_path):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan())
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )

    loaded = EvidenceAcquisitionPlanStore(tmp_path).load_pending_plans()

    assert loaded["evidence_plans_loaded_at_boot"] == 1
    assert loaded["pending_evidence_plan_count"] == 0
    assert loaded["boot_recovery_route"] == (
        "WAITING_EXECUTION_TO_VALIDATION_SCHEDULER"
    )
    assert loaded["evidence_plan_lifecycle_state"] == "WAITING_EXECUTION"
    assert loaded["persisted_selected_validation_task"] == "elite_validation_task_31"
    assert loaded["execution_state"] == "NOT_SCHEDULED"
    assert loaded["pending_evidence_acquisition_plans"] == []
    assert len(loaded["waiting_execution_evidence_plans"]) == 1

    delivered = EvidenceAcquisitionPlanStore(
        tmp_path
    ).deliver_pending_plans_to_training_assistant(
        loaded["pending_evidence_acquisition_plans"]
    )
    assert delivered["evidence_plans_delivered_to_training_assistant"] == 0
    assert delivered["training_assistant_plan_available"] is False


def test_selection_lifecycle_failure_preserves_previous_plan(tmp_path, monkeypatch):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan())
    delivery = store.mark_consumption_pending(persisted["evidence_plan_id"])
    before = Path(delivery["evidence_plan_storage_path"]).read_text(
        encoding="utf-8"
    )

    def fail_write(path, payload):
        raise OSError("simulated_atomic_write_failure")

    monkeypatch.setattr(store, "_atomic_write", fail_write)
    sync = store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )

    assert sync["lifecycle_update_attempted"] is True
    assert sync["lifecycle_update_persisted"] is False
    assert sync["evidence_plan_storage_state"] == "PLAN_SELECTION_UPDATE_FAILED"
    assert "simulated_atomic_write_failure" in sync["plan_persistence_failure_reason"]
    after = Path(delivery["evidence_plan_storage_path"]).read_text(
        encoding="utf-8"
    )
    assert after == before
    stored_plan = json.loads(after)
    assert stored_plan["lifecycle_state"] == "CONSUMPTION_PENDING"


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
