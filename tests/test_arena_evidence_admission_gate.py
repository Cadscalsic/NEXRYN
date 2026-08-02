import json
from pathlib import Path

from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
)
from runtime.validation.arena_evidence_admission_gate import (
    ArenaEvidenceAdmissionGate,
)
from runtime.validation.validation_evidence_evaluator import (
    ValidationEvidenceEvaluator,
)
from runtime.validation.validation_task_execution_pipeline import (
    ValidationTaskExecutionPipeline,
)
from runtime.validation.validation_task_scheduler import ValidationTaskScheduler


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
        "originating_arena_id": "arena_tie_1",
        "originating_arena_candidates": [
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
                "baseline_score": 0.49,
                "eligible_for_proposal": True,
            },
        ],
    }
    plan.update(overrides)
    return plan


def _consumption_report(plan_id):
    return {
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
        },
    }


def _write_curriculum(path: Path):
    path.write_text(
        json.dumps({
            "tasks": [
                {
                    "task_id": "elite_validation_task_31",
                    "task_name": "Cross Source Consensus",
                    "target_capability": "replace_color",
                    "target_domain": "Color",
                    "primary_evidence_category": "CROSS_SOURCE_CONSENSUS",
                    "secondary_evidence_categories": [
                        "cross_source_consensus_evidence"
                    ],
                    "required_validation_evidence": (
                        "cross_source_consensus_evidence"
                    ),
                    "required_grounding": [
                        "cross_source_consensus",
                        "select_cross_source_tie_break_validation_task",
                    ],
                    "expected_validation_contract": (
                        "select_cross_source_tie_break_validation_task"
                    ),
                    "validation_objective": "observe consensus",
                    "expected_target_output": {
                        "task_id": "elite_validation_task_31",
                        "execution_scope": "SCHEDULED_VALIDATION_TASK_ONLY",
                        "reference_visible_to_runner": False,
                    },
                    "evaluation_contract": {
                        "comparator_id": "manifest_observation_comparison",
                        "comparator_version": "1.0",
                        "minimum_case_coverage": 1.0,
                        "exact_match_required": True,
                    },
                    "enabled": True,
                }
            ]
        }),
        encoding="utf-8",
    )


def _registry(path):
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="elite_validation_academy",
        display_name="Elite Validation Academy",
        path=path,
        enabled=True,
    )
    return registry


def _accepted_plan(tmp_path, registry, **plan_overrides):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan(**plan_overrides))
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )
    schedule = ValidationTaskScheduler(tmp_path, registry).schedule_plan(
        persisted["evidence_plan_id"]
    )
    ValidationTaskExecutionPipeline(tmp_path, registry).execute_schedule(
        schedule["schedule_id"]
    )
    ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )
    return persisted


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_accepted_evidence_admits_and_redeliberates_without_selecting_winner(
    tmp_path,
):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted = _accepted_plan(tmp_path, registry)

    report = ArenaEvidenceAdmissionGate(tmp_path).admit_plan(
        persisted["evidence_plan_id"]
    )

    assert report["arena_admission_state"] == "ADMITTED"
    assert report["arena_evidence_admitted"] is True
    assert report["arena_evidence_consumed"] is True
    assert report["redeliberation_completed"] is True
    assert report["candidate_evidence_profiles_rebuilt"] is True
    assert report["candidate_scores_recomputed"] is True
    assert report["validation_evidence_counted_as_candidate_source"] is False
    assert report["redeliberation_outcome"] == "DECISION_PROPOSAL_AVAILABLE"
    assert report["decision_proposal_available"] is True
    assert report["formal_selection_invoked"] is False
    assert report["tie_resolved"] is False
    assert report["winner_selected"] is False
    assert report["selected_candidate"] == "NONE"
    assert report["candidate_execution_authority"] == "NONE"
    assert report["truth_authority"] == "NONE"
    assert report["trust_authority"] == "NONE"
    assert report["graduation_authority"] == "NONE"
    assert report["next_consumer"] == "ARENA_FORMAL_SELECTION_GATE"

    plan = _read_json(
        tmp_path / "pending" / f"{persisted['evidence_plan_id']}.json"
    )
    admission = _read_json(
        tmp_path
        / "arena_evidence_admissions"
        / f"{report['arena_evidence_admission_id']}.json"
    )
    ledger = _read_json(
        tmp_path
        / "arena_evidence_ledger"
        / f"{report['arena_evidence_ledger_entry_id']}.json"
    )
    snapshot = _read_json(
        tmp_path
        / "arena_redeliberations"
        / f"{report['redeliberation_snapshot_id']}.json"
    )
    accepted = _read_json(
        tmp_path
        / "accepted_evidence"
        / f"{report['accepted_evidence_id']}.json"
    )
    assert plan["lifecycle_state"] == "ARENA_REDELIBERATION_COMPLETED"
    assert admission["winner_selected"] is False
    assert ledger["cross_source_consensus_eligibility"] == "NOT_A_CANDIDATE_SOURCE"
    assert snapshot["selected_candidate"] == "NONE"
    assert accepted["arena_admission_state"] == "NOT_EVALUATED"
    assert accepted["arena_consumed"] is False


def test_reprocessing_reuses_admission_ledger_and_redeliberation(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted = _accepted_plan(tmp_path, registry)
    gate = ArenaEvidenceAdmissionGate(tmp_path)

    first = gate.admit_plan(persisted["evidence_plan_id"])
    second = gate.admit_plan(persisted["evidence_plan_id"])

    assert second["arena_admission_record_creation_result"] == (
        "REUSED_EXISTING_ARENA_ADMISSION"
    )
    assert second["arena_evidence_ledger_creation_result"] == (
        "REUSED_EXISTING_ARENA_LEDGER_ENTRY"
    )
    assert second["redeliberation_snapshot_creation_result"] == (
        "REUSED_EXISTING_REDELIBERATION_SNAPSHOT"
    )
    assert first["arena_evidence_admission_id"] == second[
        "arena_evidence_admission_id"
    ]
    assert len(list((tmp_path / "arena_evidence_admissions").glob("*.json"))) == 1
    assert len(list((tmp_path / "arena_redeliberations").glob("*.json"))) == 1


def test_nonaccepted_or_missing_arena_blocks_admission(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted = _accepted_plan(tmp_path, registry)

    decision_path = next((tmp_path / "evidence_decisions").glob("*.json"))
    decision = _read_json(decision_path)
    decision["evidence_acceptance_state"] = "INSUFFICIENT"
    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")

    blocked = ArenaEvidenceAdmissionGate(tmp_path).admit_plan(
        persisted["evidence_plan_id"]
    )
    assert blocked["arena_admission_state"] == "BLOCKED_EVIDENCE_NOT_ACCEPTED"
    assert blocked["arena_evidence_admitted"] is False
    assert blocked["redeliberation_invoked"] is False

    decision["evidence_acceptance_state"] = "ACCEPTED"
    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    accepted_path = next((tmp_path / "accepted_evidence").glob("*.json"))
    accepted = _read_json(accepted_path)
    accepted.pop("originating_arena_snapshot")
    accepted_path.write_text(json.dumps(accepted, indent=2), encoding="utf-8")
    missing_arena = ArenaEvidenceAdmissionGate(tmp_path).admit_plan(
        persisted["evidence_plan_id"]
    )
    assert missing_arena["arena_admission_state"] == (
        "BLOCKED_MISSING_ORIGINATING_ARENA"
    )


def test_tie_persists_without_forced_resolution(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted = _accepted_plan(
        tmp_path,
        registry,
    )
    accepted_path = next((tmp_path / "accepted_evidence").glob("*.json"))
    accepted = _read_json(accepted_path)
    snapshot = accepted["originating_arena_snapshot"]
    snapshot["candidate_rows"] = [
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
    accepted["originating_arena_snapshot"] = snapshot
    accepted_path.write_text(json.dumps(accepted, indent=2), encoding="utf-8")

    report = ArenaEvidenceAdmissionGate(tmp_path).admit_plan(
        persisted["evidence_plan_id"]
    )

    assert report["redeliberation_outcome"] == "TIE_PERSISTS"
    assert report["decision_proposal_available"] is False
    assert report["winner_selected"] is False
    assert report["selected_candidate"] == "NONE"


def test_boot_recovery_routes_redeliberation_to_future_consumer(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted = _accepted_plan(tmp_path, registry)
    ArenaEvidenceAdmissionGate(tmp_path).admit_plan(persisted["evidence_plan_id"])

    loaded = EvidenceAcquisitionPlanStore(tmp_path).load_pending_plans()

    assert loaded["pending_evidence_acquisition_plans"] == []
    assert len(loaded["terminal_evidence_plans"]) == 1
    assert loaded["evidence_plan_lifecycle_state"] == (
        "ARENA_REDELIBERATION_COMPLETED"
    )
    assert loaded["boot_recovery_route"] == (
        "DECISION_PROPOSAL_TO_ARENA_FORMAL_SELECTION_GATE"
    )
