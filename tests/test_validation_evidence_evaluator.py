import json
from pathlib import Path

import pytest

from runtime.claim_identity import (
    ClaimEvidenceBindingError,
    build_claim_evidence_binding,
    candidate_operation_claim_subject,
    derive_claim_id,
)
from runtime.epistemic import EvidenceSourceIndependenceEngine
from runtime.epistemic.accepted_evidence_assessment import (
    AcceptedEvidenceEpistemicAssessmentEngine,
)
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.training.elite_curriculum_validator import (
    ELITE_VALIDATION_ACADEMY_PATH,
)
from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
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
    }
    plan.update(overrides)
    return plan


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
        },
    }
    report.update(overrides)
    return report


def _expected_output():
    return {
        "task_id": "elite_validation_task_31",
        "execution_scope": "SCHEDULED_VALIDATION_TASK_ONLY",
        "reference_visible_to_runner": False,
    }


def _write_curriculum(
    path: Path,
    *,
    comparator_id="manifest_observation_comparison",
    exact_required=True,
    expected=None,
    include_evaluation_contract=True,
):
    task = {
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
        "validation_objective": (
            "observe cross-source consensus without evaluator target"
        ),
        "expected_target_output": expected
        if expected is not None else _expected_output(),
        "enabled": True,
    }
    if include_evaluation_contract:
        task["evaluation_contract"] = {
            "comparator_id": comparator_id,
            "comparator_version": "1.0",
            "minimum_case_coverage": 1.0,
            "exact_match_required": exact_required,
        }
    path.write_text(
        json.dumps({"tasks": [task]}),
        encoding="utf-8",
    )


def _registry(curriculum_path):
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="elite_validation_academy",
        display_name="Elite Validation Academy",
        path=curriculum_path,
        enabled=True,
    )
    return registry


def _captured_result(tmp_path, registry):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan())
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )
    schedule = ValidationTaskScheduler(tmp_path, registry).schedule_plan(
        persisted["evidence_plan_id"]
    )
    raw = ValidationTaskExecutionPipeline(tmp_path, registry).execute_schedule(
        schedule["schedule_id"]
    )
    return persisted, schedule, raw


def _accepted_result(tmp_path, registry, **plan_overrides):
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan(**plan_overrides))
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report(
        _consumption_report(persisted["evidence_plan_id"])
    )
    schedule = ValidationTaskScheduler(tmp_path, registry).schedule_plan(
        persisted["evidence_plan_id"]
    )
    raw = ValidationTaskExecutionPipeline(tmp_path, registry).execute_schedule(
        schedule["schedule_id"]
    )
    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )
    plan = _read_json(tmp_path / "pending" / f"{persisted['evidence_plan_id']}.json")
    decision = _read_json(
        tmp_path / "evidence_decisions" / f"{report['evidence_decision_id']}.json"
    )
    accepted = _read_json(
        tmp_path / "accepted_evidence" / f"{report['accepted_evidence_id']}.json"
    )
    return {
        "persisted": persisted,
        "plan": plan,
        "schedule": schedule,
        "raw": raw,
        "report": report,
        "decision": decision,
        "accepted": accepted,
    }


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_raw_result_captured_evaluates_to_accepted_without_arena_authority(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, raw = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evaluation_admission_state"] == (
        "ADMITTED_TO_VALIDATION_EVIDENCE_EVALUATION"
    )
    assert report["evaluation_contract_id"].startswith(
        "validation_evidence_evaluation_contract_"
    )
    assert report["sealed_reference_resolved"] is True
    assert report["target_reference_forwarded_to_solver"] is False
    assert report["sealed_reference_opened_by_evaluator"] is True
    assert report["sealed_reference_forwarded_to_solver"] is False
    assert report["comparison_state"] == "COMPARISON_COMPLETED"
    assert report["comparable_result_available"] is True
    assert report["exact_match_rate"] == 1.0
    assert report["evidence_admissibility_state"] == "ADMISSIBLE"
    assert report["evidence_sufficiency_state"] == "SUFFICIENT"
    assert report["evidence_direction"] == "SUPPORTING"
    assert report["evidence_acceptance_state"] == "ACCEPTED"
    assert report["evidence_accepted"] is True
    assert report["accepted_evidence_artifact_created"] is True
    assert report["arena_evidence_admission_invoked"] is False
    assert report["arena_reentry_invoked"] is False
    assert report["candidate_score_changed"] is False
    assert report["candidate_ranking_changed"] is False
    assert report["tie_resolved"] is False
    assert report["winner_selected"] is False
    assert report["truth_authority"] == "NONE"
    assert report["trust_authority"] == "NONE"
    assert report["graduation_authority"] == "NONE"
    assert report["candidate_execution_authority"] == "NONE"
    assert report["next_consumer"] == "FUTURE_ARENA_EVIDENCE_ADMISSION_GATE"

    plan = _read_json(
        tmp_path / "pending" / f"{persisted['evidence_plan_id']}.json"
    )
    comparable = _read_json(
        tmp_path / "comparable_results" / f"{report['comparable_result_id']}.json"
    )
    decision = _read_json(
        tmp_path / "evidence_decisions" / f"{report['evidence_decision_id']}.json"
    )
    accepted = _read_json(
        tmp_path / "accepted_evidence" / f"{report['accepted_evidence_id']}.json"
    )
    assert plan["lifecycle_state"] == "EVIDENCE_ACCEPTED"
    assert plan["boot_recovery_route"] == (
        "EVIDENCE_ACCEPTED_TO_ARENA_EVIDENCE_ADMISSION_GATE"
    )
    assert comparable["raw_result_id"] == raw["raw_result_id"]
    assert "candidate_score_delta" not in comparable
    assert decision["evidence_acceptance_state"] == "ACCEPTED"
    assert accepted["evidence_state"] == "EVIDENCE_ACCEPTED"


def test_accepted_evidence_binds_to_canonical_claim_without_authority(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)

    result = _accepted_result(tmp_path, registry)
    plan = result["plan"]
    decision = result["decision"]
    accepted = result["accepted"]
    report = result["report"]

    expected_subject = candidate_operation_claim_subject(
        subject_ref="semantic_program:replace_color",
        operation="replace_color",
    )
    expected_claim_id = derive_claim_id(expected_subject)
    assert plan["claim_id"] == expected_claim_id
    assert result["schedule"]["claim_id"] == expected_claim_id
    assert result["raw"]["claim_id"] == expected_claim_id
    assert decision["claim_id"] == expected_claim_id
    assert accepted["claim_id"] == expected_claim_id
    assert accepted["claim_evidence_binding_state"] == "BOUND"
    assert accepted["claim_evidence_binding"]["claim_id"] == expected_claim_id
    assert report["claim_evidence_binding_id"] == accepted["claim_evidence_binding_id"]
    assert accepted["claim_evidence_binding_authority"] == "OBSERVATION_ONLY"
    assert accepted["claim_evidence_binding_behavioral_authority"] == "NONE"
    assert accepted["claim_evidence_binding"]["authority"] == {
        "truth": "NONE",
        "trust": "NONE",
        "graduation": "NONE",
        "execution": "NONE",
    }
    assert accepted["truth_authority"] == "NONE"
    assert accepted["trust_authority"] == "NONE"
    assert accepted["graduation_authority"] == "NONE"
    assert accepted["candidate_execution_authority"] == "NONE"


def test_fresh_raw_result_contains_producer_provenance(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)

    _, _, raw = _captured_result(tmp_path, registry)

    assert raw["producer_component_id"] == "VALIDATION_TASK_EXECUTION_PIPELINE"
    assert raw["producer_source_type"] == "scheduled_validation_task"
    assert raw["producer_operation_id"] == raw["execution_id"]
    assert raw["validation_attempt_id"].startswith("validation_attempt_")
    assert raw["canonical_raw_result_id"] == raw["raw_result_id"]
    assert raw["raw_result_identity_fingerprint"]


def test_fresh_accepted_evidence_preserves_native_source_provenance(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)

    result = _accepted_result(tmp_path, registry)
    accepted = result["accepted"]
    raw = result["raw"]
    provenance = accepted["source_provenance"]

    assert provenance["source_provenance_state"] == "SOURCE_PROVENANCE_BOUND"
    assert provenance["producer_component_id"] == (
        "VALIDATION_TASK_EXECUTION_PIPELINE"
    )
    assert provenance["producer_source_type"] == "scheduled_validation_task"
    assert provenance["producer_operation_id"] == raw["producer_operation_id"]
    assert provenance["validation_attempt_id"] == raw["validation_attempt_id"]
    assert provenance["raw_validation_result_id"] == raw["raw_result_id"]
    assert accepted["producer_operation_id"] == raw["producer_operation_id"]
    assert accepted["source_provenance_fingerprint"] == (
        provenance["source_provenance_fingerprint"]
    )
    assert accepted["accepted_evidence_origin_state"] == "TASK_ORIGIN_PRESERVED"
    assert accepted["accepted_evidence_origin"]["raw_evidence_id"] == (
        raw["raw_result_id"]
    )
    assert accepted["origin_task_execution_id"] == raw["origin_task_execution_id"]
    assert accepted["origin_run_id"] == raw["origin_run_id"]
    assert accepted["origin_task_id"] == raw["origin_task_id"]
    assert accepted["origin_lineage_fingerprint"] == (
        raw["origin_lineage_fingerprint"]
    )
    assert accepted["accepted_evidence_origin"]["authority"] == "NONE"
    assert accepted["truth_authority"] == "NONE"
    assert provenance["truth_authority"] == "NONE"


def test_accepted_evidence_does_not_invent_upstream_provenance(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)

    result = _accepted_result(tmp_path, registry)
    accepted = result["accepted"]
    raw = result["raw"]

    assert accepted["producer_operation_id"] == raw["producer_operation_id"]
    assert accepted["producer_component_id"] == raw["producer_component_id"]
    assert accepted["producer_source_type"] == raw["producer_source_type"]
    assert accepted["source_provenance"]["run_id"] == raw["run_id"]
    assert accepted["source_provenance"]["task_id"] == raw["task_id"]


def test_fresh_claim_source_coverage_consumes_accepted_provenance(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)

    result = _accepted_result(tmp_path, registry)
    accepted = result["accepted"]
    coverage = EvidenceSourceIndependenceEngine().source_coverage(
        [accepted],
        claim_id=accepted["claim_id"],
    )

    assert coverage["current_proven_independent_source_count"] == 1
    assert coverage["source_identities"]
    assert coverage["truth_authority"] == "NONE"


def test_historical_accepted_evidence_without_envelope_remains_readable():
    historical = {
        "accepted_evidence_id": "accepted_historical",
        "claim_id": "claim_historical",
        "source_run_id": "run_historical",
        "selected_validation_task_id": "task_historical",
        "evidence_direction": "SUPPORTING",
    }

    identity = EvidenceSourceIndependenceEngine().source_identity(historical)

    assert identity["source_identity_state"] == "PARTIAL"
    assert identity["source_identity_reason"] == (
        "only_weak_or_partial_source_fields_present"
    )


def test_same_semantic_claim_is_stable_across_distinct_runs_and_evidence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)

    first = _accepted_result(tmp_path / "first", registry, source_run_id="run_alpha")
    second = _accepted_result(tmp_path / "second", registry, source_run_id="run_beta")

    assert first["accepted"]["claim_id"] == second["accepted"]["claim_id"]
    assert first["plan"]["plan_id"] != second["plan"]["plan_id"]
    assert first["accepted"]["accepted_evidence_id"] != (
        second["accepted"]["accepted_evidence_id"]
    )
    assert first["accepted"]["claim_evidence_binding_id"] != (
        second["accepted"]["claim_evidence_binding_id"]
    )


def test_claim_evidence_binding_is_idempotent_for_same_evidence_pair(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    result = _accepted_result(tmp_path, registry)

    first = build_claim_evidence_binding(
        claim_subject=result["accepted"]["claim_subject"],
        evidence_plan=result["plan"],
        evidence_decision=result["decision"],
        accepted_evidence=result["accepted"],
    )
    second = build_claim_evidence_binding(
        claim_subject=result["accepted"]["claim_subject"],
        evidence_plan=result["plan"],
        evidence_decision=result["decision"],
        accepted_evidence=result["accepted"],
    )

    assert first["claim_evidence_binding_id"] == second["claim_evidence_binding_id"]
    assert first["claim_evidence_binding_fingerprint"] == (
        second["claim_evidence_binding_fingerprint"]
    )


def test_wrong_claim_binding_is_rejected(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    result = _accepted_result(tmp_path, registry)
    wrong_subject = candidate_operation_claim_subject(
        subject_ref="semantic_program:wrong_candidate",
        operation="replace_color",
    )

    with pytest.raises(ClaimEvidenceBindingError):
        build_claim_evidence_binding(
            claim_subject=wrong_subject,
            evidence_plan=result["plan"],
            evidence_decision=result["decision"],
            accepted_evidence=result["accepted"],
        )


def test_reprocessing_reuses_comparable_decision_and_accepted_evidence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, _ = _captured_result(tmp_path, registry)
    evaluator = ValidationEvidenceEvaluator(tmp_path, registry)

    first = evaluator.evaluate_plan(persisted["evidence_plan_id"])
    second = evaluator.evaluate_plan(persisted["evidence_plan_id"])

    assert second["comparable_result_creation_result"] == (
        "REUSED_EXISTING_COMPARABLE_RESULT"
    )
    assert second["evidence_decision_creation_result"] == (
        "REUSED_EXISTING_EVIDENCE_DECISION"
    )
    assert second["accepted_evidence_creation_result"] == (
        "REUSED_EXISTING_ACCEPTED_EVIDENCE"
    )
    assert first["comparable_result_id"] == second["comparable_result_id"]
    assert first["evidence_decision_id"] == second["evidence_decision_id"]
    assert len(list((tmp_path / "comparable_results").glob("*.json"))) == 1
    assert len(list((tmp_path / "evidence_decisions").glob("*.json"))) == 1
    assert len(list((tmp_path / "accepted_evidence").glob("*.json"))) == 1


def test_wrong_prediction_is_accepted_as_contradicting_evidence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum, exact_required=False, expected={"different": True})
    registry = _registry(curriculum)
    persisted, _, _ = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evidence_acceptance_state"] == "ACCEPTED"
    assert report["evidence_direction"] == "CONTRADICTING"
    assert report["evidence_accepted"] is True


def test_valid_but_incomplete_evidence_becomes_insufficient(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(
        curriculum,
        expected=[{"output": _expected_output()}, {"output": {"case": 2}}],
    )
    registry = _registry(curriculum)
    persisted, _, _ = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evidence_acceptance_state"] == "INSUFFICIENT"
    assert report["evidence_admissibility_state"] == "ADMISSIBLE"
    assert report["evidence_sufficiency_state"] == "INSUFFICIENT"
    assert report["accepted_evidence_artifact_created"] is False
    assert report["evidence_accepted"] is False
    assert list((tmp_path / "accepted_evidence").glob("*.json")) == []


def test_target_leakage_rejects_evidence_without_arena_penalty(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, raw = _captured_result(tmp_path, registry)
    raw_path = tmp_path / "raw_results" / f"{raw['raw_result_id']}.json"
    raw_record = _read_json(raw_path)
    raw_record["runner_trace_reference"]["target_reference_forwarded_to_solver"] = True
    raw_path.write_text(json.dumps(raw_record, indent=2), encoding="utf-8")

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evaluation_admission_state"] == "BLOCKED_TARGET_LEAKAGE_RISK"
    assert report["comparison_invoked"] is False
    assert report["evidence_accepted"] is False
    assert report["arena_reentry_invoked"] is False


def test_missing_contract_or_unsupported_comparator_blocks_evaluation(tmp_path):
    unsupported = tmp_path / "unsupported.json"
    _write_curriculum(unsupported, comparator_id="subjective_llm_judge")
    registry = _registry(unsupported)
    persisted, _, _ = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evaluation_admission_state"] == "BLOCKED_UNSUPPORTED_COMPARATOR"
    assert report["comparison_invoked"] is False
    assert report["evidence_accepted"] is False


def test_manifest_task_without_explicit_contract_derives_safe_contract(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum, include_evaluation_contract=False)
    registry = _registry(curriculum)
    persisted, _, _ = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evaluation_admission_state"] == (
        "ADMITTED_TO_VALIDATION_EVIDENCE_EVALUATION"
    )
    assert report["comparison_state"] == "COMPARISON_COMPLETED"
    assert report["evidence_acceptance_state"] == "ACCEPTED"
    comparable = _read_json(
        tmp_path / "comparable_results" / f"{report['comparable_result_id']}.json"
    )
    assert comparable["evaluation_contract_source"] == (
        "derived_from_expected_target_output"
    )


def test_default_academy_task_31_declares_machine_readable_contract(tmp_path):
    registry = ValidationCurriculumRegistry()
    registry.register_default_academy(ELITE_VALIDATION_ACADEMY_PATH)
    persisted, _, _ = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evaluation_admission_state"] == (
        "ADMITTED_TO_VALIDATION_EVIDENCE_EVALUATION"
    )
    assert report["evaluation_contract_id"].startswith(
        "validation_evidence_evaluation_contract_"
    )
    assert report["comparison_state"] == "COMPARISON_COMPLETED"
    assert report["evidence_decision_id"].startswith("evidence_decision_")
    assert report["evidence_acceptance_state"] in {
        "ACCEPTED",
        "INSUFFICIENT",
        "REJECTED",
    }
    assert report["truth_authority"] == "NONE"
    assert report["trust_authority"] == "NONE"
    assert report["graduation_authority"] == "NONE"
    assert report["candidate_execution_authority"] == "NONE"

    second = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )
    plan = _read_json(
        tmp_path / "pending" / f"{persisted['evidence_plan_id']}.json"
    )

    assert plan["evidence_decision_id"] == report["evidence_decision_id"]
    assert plan["evidence_state"] == f"EVIDENCE_{report['evidence_acceptance_state']}"
    assert second["evidence_decision_id"] == report["evidence_decision_id"]
    assert second["evidence_decision_creation_result"] == (
        "REUSED_EXISTING_EVIDENCE_DECISION"
    )


def test_boot_recovery_routes_terminal_evidence_to_future_consumer(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, _ = _captured_result(tmp_path, registry)
    ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    loaded = EvidenceAcquisitionPlanStore(tmp_path).load_pending_plans()

    assert loaded["pending_evidence_acquisition_plans"] == []
    assert len(loaded["terminal_evidence_plans"]) == 1
    assert loaded["boot_recovery_route"] == (
        "EVIDENCE_ACCEPTED_TO_ARENA_EVIDENCE_ADMISSION_GATE"
    )
    assert loaded["evidence_plan_lifecycle_state"] == "EVIDENCE_ACCEPTED"


def test_governed_acceptance_records_contract_and_decision_binding(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)

    result = _accepted_result(tmp_path, registry)

    assert result["decision"]["governed_acceptance_contract_state"] == "SATISFIED"
    assert result["decision"]["accepted_evidence_id"] == (
        result["accepted"]["accepted_evidence_id"]
    )
    assert result["accepted"]["accepted_evidence_requires_authoritative_decision"] is True
    assert result["accepted"]["claim_evidence_binding_state"] == "BOUND"


def test_missing_claim_id_fails_closed_before_acceptance(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, schedule, raw = _captured_result(tmp_path, registry)
    for directory, identity in (
        ("pending", persisted["evidence_plan_id"]),
        ("schedules", schedule["schedule_id"]),
        ("raw_results", raw["raw_result_id"]),
    ):
        path = tmp_path / directory / f"{identity}.json"
        record = _read_json(path)
        record.pop("claim_id", None)
        record.pop("claim_subject", None)
        path.write_text(json.dumps(record), encoding="utf-8")

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evidence_acceptance_state"] == "REJECTED"
    assert report["governed_acceptance_contract_state"] == "FAILED_CLOSED"
    assert "missing_claim_id" in report["governed_acceptance_contract_failures"]
    assert report["accepted_evidence_artifact_created"] is False


def test_claim_mismatch_fails_closed_before_acceptance(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, raw = _captured_result(tmp_path, registry)
    raw_path = tmp_path / "raw_results" / f"{raw['raw_result_id']}.json"
    raw_record = _read_json(raw_path)
    raw_record["claim_id"] = "claim_mismatch"
    raw_path.write_text(json.dumps(raw_record), encoding="utf-8")

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evidence_acceptance_state"] == "REJECTED"
    assert "claim_id_mismatch" in report["governed_acceptance_contract_failures"]
    assert list((tmp_path / "accepted_evidence").glob("*.json")) == []


def test_missing_evidence_decision_id_cannot_create_accepted_evidence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    result = _accepted_result(tmp_path, registry)
    decision = dict(result["decision"])
    decision["evidence_decision_id"] = None

    with pytest.raises(ValueError):
        ValidationEvidenceEvaluator(tmp_path, registry)._accepted_evidence_artifact(
            result["plan"],
            result["schedule"],
            result["raw"],
            _read_json(
                tmp_path
                / "comparable_results"
                / f"{result['report']['comparable_result_id']}.json"
            ),
            decision,
        )


def test_rejected_decision_cannot_create_accepted_evidence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    result = _accepted_result(tmp_path, registry)
    decision = dict(result["decision"], evidence_acceptance_state="REJECTED")

    with pytest.raises(ValueError):
        ValidationEvidenceEvaluator(tmp_path, registry)._accepted_evidence_artifact(
            result["plan"], result["schedule"], result["raw"], {}, decision
        )


def test_insufficient_decision_does_not_create_accepted_evidence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(
        curriculum,
        expected=[{"output": _expected_output()}, {"output": {"missing": True}}],
    )
    registry = _registry(curriculum)
    persisted, _, _ = _captured_result(tmp_path, registry)

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evidence_acceptance_state"] == "INSUFFICIENT"
    assert report["accepted_evidence_artifact_created"] is False


def test_raw_result_without_decision_is_not_accepted(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    _captured_result(tmp_path, registry)

    assert not (tmp_path / "accepted_evidence").exists()


def test_high_score_without_decision_is_not_acceptance(tmp_path):
    raw_artifact = {
        "raw_result_id": "raw_high_score",
        "score": 1.0,
        "evidence_acceptance_state": "NOT_EVALUATED",
    }

    assessment = AcceptedEvidenceEpistemicAssessmentEngine().assess([raw_artifact])

    assert assessment["bound_accepted_evidence_count"] == 0
    assert assessment["epistemic_assessment_state"] == "NO_BOUND_ACCEPTED_EVIDENCE"


def test_persisted_artifact_without_acceptance_authority_fails_closed():
    persisted = {
        "accepted_evidence_id": "accepted_without_authority",
        "claim_id": "claim_a",
        "evidence_acceptance_state": "ACCEPTED",
    }

    assessment = AcceptedEvidenceEpistemicAssessmentEngine().assess([persisted])

    assert assessment["bound_accepted_evidence_count"] == 0
    assert assessment["historical_unbound_evidence"][0]["classification"] == (
        "HISTORICAL_PRE_E1_UNBOUND"
    )


def test_historical_artifact_presented_as_current_run_is_distinguished():
    historical = {
        "accepted_evidence_id": "accepted_historical",
        "claim_id": "claim_a",
        "evidence_acceptance_state": "ACCEPTED",
        "historical_acceptance_state": "LEGACY_PRE_CONTRACT_ACCEPTED_EVIDENCE",
    }

    assessment = AcceptedEvidenceEpistemicAssessmentEngine().assess(
        [historical],
        assessment_run_id="current_run",
    )

    assert assessment["bound_accepted_evidence_count"] == 0
    assert assessment["historical_unbound_evidence"]


def test_duplicate_accepted_artifact_does_not_increase_source_independence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    result = _accepted_result(tmp_path, registry)
    duplicate = dict(result["accepted"], accepted_evidence_id="accepted_copy")

    coverage = EvidenceSourceIndependenceEngine().source_coverage(
        [result["accepted"], duplicate],
        claim_id=result["accepted"]["claim_id"],
    )

    assert coverage["current_proven_independent_source_count"] == 1
    assert coverage["duplicate_supporting_evidence_count"] == 1


def test_same_source_across_multiple_runs_does_not_inflate_independence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    first = _accepted_result(tmp_path / "first", registry, source_run_id="run_a")
    second = _accepted_result(tmp_path / "second", registry, source_run_id="run_b")
    second["accepted"]["source_provenance"]["producer_operation_id"] = (
        first["accepted"]["source_provenance"]["producer_operation_id"]
    )

    coverage = EvidenceSourceIndependenceEngine().source_coverage(
        [first["accepted"], second["accepted"]],
        claim_id=first["accepted"]["claim_id"],
    )

    assert coverage["current_proven_independent_source_count"] == 1


def test_same_source_across_multiple_tasks_does_not_inflate_independence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    result = _accepted_result(tmp_path, registry)
    same_source_new_task = dict(result["accepted"], accepted_evidence_id="accepted_task_b")
    same_source_new_task["source_provenance"] = dict(result["accepted"]["source_provenance"])
    same_source_new_task["source_provenance"]["task_id"] = "different_task"

    coverage = EvidenceSourceIndependenceEngine().source_coverage(
        [result["accepted"], same_source_new_task],
        claim_id=result["accepted"]["claim_id"],
    )

    assert coverage["current_proven_independent_source_count"] == 1


def test_different_artifact_ids_from_same_source_do_not_inflate_independence(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    result = _accepted_result(tmp_path, registry)
    alternate = dict(result["accepted"], accepted_evidence_id="accepted_alternate")

    coverage = EvidenceSourceIndependenceEngine().source_coverage(
        [result["accepted"], alternate],
        claim_id=result["accepted"]["claim_id"],
    )

    assert coverage["current_proven_independent_source_count"] == 1


def test_broken_provenance_lineage_fails_closed_before_acceptance(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, raw = _captured_result(tmp_path, registry)
    raw_path = tmp_path / "raw_results" / f"{raw['raw_result_id']}.json"
    raw_record = _read_json(raw_path)
    raw_record.pop("producer_operation_id", None)
    raw_record["RAW_VALIDATION_RESULT_ENVELOPE"].pop("producer_operation_id", None)
    raw_path.write_text(json.dumps(raw_record), encoding="utf-8")

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evidence_acceptance_state"] == "REJECTED"
    assert "source_provenance_not_bound" in report["governed_acceptance_contract_failures"]


def test_missing_source_identity_fails_closed_before_acceptance(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, raw = _captured_result(tmp_path, registry)
    raw_path = tmp_path / "raw_results" / f"{raw['raw_result_id']}.json"
    raw_record = _read_json(raw_path)
    raw_record.pop("producer_component_id", None)
    raw_record["RAW_VALIDATION_RESULT_ENVELOPE"].pop("producer_component_id", None)
    raw_path.write_text(json.dumps(raw_record), encoding="utf-8")

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evidence_acceptance_state"] == "REJECTED"
    assert "source_provenance_not_bound" in report["governed_acceptance_contract_failures"]


def test_invalid_current_run_binding_fails_closed(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    persisted, _, raw = _captured_result(tmp_path, registry)
    raw_path = tmp_path / "raw_results" / f"{raw['raw_result_id']}.json"
    raw_record = _read_json(raw_path)
    raw_record["RAW_VALIDATION_RESULT_ENVELOPE"]["binding_integrity_state"] = (
        "CONFLICTED"
    )
    raw_path.write_text(json.dumps(raw_record), encoding="utf-8")

    report = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )

    assert report["evaluation_admission_state"] == (
        "BLOCKED_RAW_VALIDATION_BINDING_CONFLICTED"
    )
    assert report["evidence_accepted"] is False


def test_downstream_consumer_rejects_raw_result_bypass(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    _, _, raw = _captured_result(tmp_path, registry)

    assessment = AcceptedEvidenceEpistemicAssessmentEngine().assess([raw])

    assert assessment["bound_accepted_evidence_count"] == 0
    assert assessment["epistemic_assessment_state"] == "NO_BOUND_ACCEPTED_EVIDENCE"


def test_accepted_evidence_attempting_direct_truth_commitment_is_not_truth(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    result = _accepted_result(tmp_path, registry)
    forged = dict(result["accepted"], truth_authority="FORGED")

    assessment = AcceptedEvidenceEpistemicAssessmentEngine().assess([forged])

    assert assessment["accepted_evidence_is_not_truth"] is True
    assert assessment["authority"]["truth_commitment"] == "NONE"
