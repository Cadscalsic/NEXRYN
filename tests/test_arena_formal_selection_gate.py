import json
import sys
from pathlib import Path

from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.validation.arena_evidence_admission_gate import (
    ArenaEvidenceAdmissionGate,
)
from runtime.validation.arena_formal_selection_gate import (
    ArenaFormalSelectionGate,
)

sys.path.append(str(Path(__file__).parent))
from test_arena_evidence_admission_gate import (
    _accepted_plan,
    _read_json,
    _registry,
    _write_curriculum,
)


def _proposal_plan(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted = _accepted_plan(tmp_path, registry)
    admission = ArenaEvidenceAdmissionGate(tmp_path).admit_plan(
        persisted["evidence_plan_id"]
    )
    assert admission["redeliberation_outcome"] == "DECISION_PROPOSAL_AVAILABLE"
    return persisted


def test_decision_proposal_ratifies_without_execution_authority(tmp_path):
    persisted = _proposal_plan(tmp_path)

    report = ArenaFormalSelectionGate(tmp_path).review_plan(
        persisted["evidence_plan_id"]
    )

    assert report["formal_selection_admission_state"] == (
        "ADMITTED_TO_FORMAL_SELECTION_REVIEW"
    )
    assert report["formal_selection_review_started"] is True
    assert report["formal_selection_review_completed"] is True
    assert report["formal_selection_outcome"] == "RATIFIED"
    assert report["proposal_ratified"] is True
    assert report["proposal_rejected"] is False
    assert report["proposal_deferred"] is False
    assert report["tie_resolved"] is True
    assert report["winner_selected"] is True
    assert report["selected_candidate"] == "semantic_program:replace_color"
    assert report["selection_basis"] == "RATIFIED_DECISION_PROPOSAL"
    assert report["candidate_execution_authority"] == "NONE"
    assert report["candidate_execution_started"] is False
    assert report["truth_authority"] == "NONE"
    assert report["trust_authority"] == "NONE"
    assert report["graduation_authority"] == "NONE"
    assert report["next_consumer"] == (
        "FUTURE_SELECTED_CANDIDATE_EXECUTION_ADMISSION_GATE"
    )

    plan = _read_json(
        tmp_path / "pending" / f"{persisted['evidence_plan_id']}.json"
    )
    assert plan["lifecycle_state"] == "RATIFIED"
    assert plan["winner_selected"] is True
    assert plan["candidate_execution_authority"] == "NONE"
    assert len(list((tmp_path / "formal_selection_decisions").glob("*.json"))) == 1
    assert len(list((tmp_path / "arena_selection_snapshots").glob("*.json"))) == 1
    assert len(list((tmp_path / "decision_proposal_dispositions").glob("*.json"))) == 1


def test_reprocessing_reuses_formal_selection_records(tmp_path):
    persisted = _proposal_plan(tmp_path)
    gate = ArenaFormalSelectionGate(tmp_path)

    first = gate.review_plan(persisted["evidence_plan_id"])
    second = gate.review_plan(persisted["evidence_plan_id"])

    assert first["formal_selection_decision_id"] == second[
        "formal_selection_decision_id"
    ]
    assert second["formal_selection_decision_creation_result"] == (
        "REUSED_EXISTING_FORMAL_SELECTION_DECISION"
    )
    assert second["arena_selection_snapshot_creation_result"] == (
        "REUSED_EXISTING_ARENA_SELECTION_SNAPSHOT"
    )
    assert len(list((tmp_path / "formal_selection_decisions").glob("*.json"))) == 1


def test_nonproposal_redeliberation_does_not_invoke_formal_selection(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted = _accepted_plan(tmp_path, registry)
    accepted_path = next((tmp_path / "accepted_evidence").glob("*.json"))
    accepted = _read_json(accepted_path)
    accepted["originating_arena_snapshot"]["candidate_rows"] = [
        {
            "candidate_id": "semantic_program:replace_color",
            "source": "semantic_to_transformation_compiler",
            "operation": "replace_color",
            "baseline_score": 0.5,
            "eligible_for_proposal": True,
        },
        {
            "candidate_id": "program_generation:duplicate_object",
            "source": "program_generation",
            "operation": "duplicate_object",
            "baseline_score": 0.55,
            "eligible_for_proposal": True,
        },
    ]
    accepted_path.write_text(json.dumps(accepted, indent=2), encoding="utf-8")
    admission = ArenaEvidenceAdmissionGate(tmp_path).admit_plan(
        persisted["evidence_plan_id"]
    )
    assert admission["redeliberation_outcome"] == "TIE_PERSISTS"

    report = ArenaFormalSelectionGate(tmp_path).review_plan(
        persisted["evidence_plan_id"]
    )

    assert report["formal_selection_admission_state"] == (
        "BLOCKED_INVALID_REDELIBERATION_OUTCOME"
    )
    assert report["formal_selection_invoked"] is False
    assert report["winner_selected"] is False
    assert report["selected_candidate"] == "NONE"


def test_missing_decision_proposal_blocks_without_winner(tmp_path):
    persisted = _proposal_plan(tmp_path)
    proposal_path = next((tmp_path / "decision_proposals").glob("*.json"))
    proposal_path.unlink()

    report = ArenaFormalSelectionGate(tmp_path).review_plan(
        persisted["evidence_plan_id"]
    )

    assert report["formal_selection_admission_state"] == (
        "BLOCKED_MISSING_DECISION_PROPOSAL"
    )
    assert report["winner_selected"] is False
    assert report["candidate_execution_authority"] == "NONE"


def test_candidate_fingerprint_mismatch_blocks_selection(tmp_path):
    persisted = _proposal_plan(tmp_path)
    proposal_path = next((tmp_path / "decision_proposals").glob("*.json"))
    proposal = _read_json(proposal_path)
    proposal["proposed_candidate_fingerprint"] = "bad-fingerprint"
    proposal_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")

    report = ArenaFormalSelectionGate(tmp_path).review_plan(
        persisted["evidence_plan_id"]
    )

    assert report["formal_selection_admission_state"] == (
        "BLOCKED_CANDIDATE_FINGERPRINT_MISMATCH"
    )
    assert report["tie_resolved"] is False
    assert report["winner_selected"] is False
    assert report["selected_candidate"] == "NONE"


def test_revoked_or_vetoed_proposal_is_not_ratified(tmp_path):
    persisted = _proposal_plan(tmp_path)
    proposal_path = next((tmp_path / "decision_proposals").glob("*.json"))
    proposal = _read_json(proposal_path)
    proposal["proposal_constitutional_veto_state"] = "VETOED"
    proposal_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")

    report = ArenaFormalSelectionGate(tmp_path).review_plan(
        persisted["evidence_plan_id"]
    )

    assert report["formal_selection_outcome"] == "REJECTED"
    assert report["constitutional_veto_state"] == "VETOED"
    assert report["proposal_rejected"] is True
    assert report["winner_selected"] is False
    assert report["candidate_execution_authority"] == "NONE"


def test_boot_recovery_routes_ratified_to_future_execution_gate(tmp_path):
    persisted = _proposal_plan(tmp_path)
    ArenaFormalSelectionGate(tmp_path).review_plan(persisted["evidence_plan_id"])

    loaded = EvidenceAcquisitionPlanStore(tmp_path).load_pending_plans()

    assert loaded["terminal_evidence_plan_count"] == 1
    assert loaded["evidence_plan_lifecycle_state"] == "RATIFIED"
    assert loaded["boot_recovery_route"] == (
        "RATIFIED_TO_FUTURE_SELECTED_CANDIDATE_EXECUTION_ADMISSION_GATE"
    )
