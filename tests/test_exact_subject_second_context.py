from __future__ import annotations

import json

from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.experiments.exact_subject_second_context import _identity_propagation


def test_selection_metadata_persists_v2_context_identity_before_scheduling(tmp_path):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    plan_id = "evidence_plan_context_identity"
    pending = tmp_path / "pending" / f"{plan_id}.json"
    pending.parent.mkdir(parents=True, exist_ok=True)
    pending.write_text(
        json.dumps({
            "plan_id": plan_id,
            "lifecycle_state": "CONSUMPTION_PENDING",
            "consumption_state": "CONSUMPTION_PENDING",
            "required_evidence": "independent_replication_evidence",
            "required_evidence_category": "INDEPENDENT_REPLICATION",
            "target_candidate": "capability_legacy",
            "target_operation": "fill_center",
            "tie_break_strategy": "deterministic_priority",
            "history": [],
        }),
        encoding="utf-8",
    )

    report = store.persist_selection_from_consumption_report({
        "current_plan_id": plan_id,
        "selection_state": "WAITING_EXECUTION",
        "selected_validation_task": "task_second_context",
        "best_matching_curriculum": "curriculum_second_context",
        "selected_validation_task_metadata": {
            "curriculum_id": "curriculum_second_context",
            "capability_identity_schema": "capability_identity.v2",
            "capability_id_v2": "capability_v2_exact",
            "capability_operation_id_v2": "capability_operation_v2_exact",
            "validation_context_identity_schema": "validation_context_identity.v1",
            "validation_context_id": "validation_context_second",
            "canonical_source_identity": "source_second",
            "source_lineage": ["source_second", "context_source"],
        },
    })

    updated = json.loads(pending.read_text(encoding="utf-8"))

    assert report["lifecycle_update_persisted"] is True
    assert updated["capability_id_v2"] == "capability_v2_exact"
    assert updated["capability_operation_id_v2"] == "capability_operation_v2_exact"
    assert updated["validation_context_id"] == "validation_context_second"
    assert updated["canonical_source_identity"] == "source_second"
    assert updated["source_lineage"] == ["source_second", "context_source"]


def test_identity_propagation_requires_all_durable_stages_to_match():
    matching = {
        "capability_id_v2": "capability_v2_exact",
        "capability_operation_id_v2": "capability_operation_v2_exact",
        "validation_context_id": "validation_context_second",
    }
    governed = {
        "plan": dict(matching),
        "schedule": dict(matching),
        "raw": dict(matching),
        "accepted": {
            **matching,
            "causal_evidence": dict(matching),
        },
    }

    audit = _identity_propagation(
        expected_context_id="validation_context_second",
        expected_capability_id_v2="capability_v2_exact",
        expected_operation_id_v2="capability_operation_v2_exact",
        governed=governed,
    )

    assert audit["identity_propagation_state"] == "COMPLETE"


def test_identity_propagation_fails_when_causal_trace_drops_context():
    matching = {
        "capability_id_v2": "capability_v2_exact",
        "capability_operation_id_v2": "capability_operation_v2_exact",
        "validation_context_id": "validation_context_second",
    }
    governed = {
        "plan": dict(matching),
        "schedule": dict(matching),
        "raw": dict(matching),
        "accepted": {
            **matching,
            "causal_evidence": {
                "capability_id_v2": "capability_v2_exact",
                "capability_operation_id_v2": "capability_operation_v2_exact",
            },
        },
    }

    audit = _identity_propagation(
        expected_context_id="validation_context_second",
        expected_capability_id_v2="capability_v2_exact",
        expected_operation_id_v2="capability_operation_v2_exact",
        governed=governed,
    )

    assert audit["identity_propagation_state"] == "INCOMPLETE"
    assert audit["stage_states"]["causal_evidence"]["matches"] is False
