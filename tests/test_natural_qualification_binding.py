import json

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    capability_id_for_subject,
)
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.evidence.current_evidence_need import CurrentEvidenceNeedAuthorityEngine
from runtime.evidence.natural_qualification_binding import (
    NaturalQualificationAssessmentBinding,
)
from runtime.evidence.natural_validation_orchestrator import (
    NaturalCanonicalValidationOrchestrator,
)
from runtime.evidence.validation_request import ValidationRequestAuthorityEngine
from runtime.evidence.validation_sponsorship import (
    ValidationSponsorshipAuthorityEngine,
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


def _subject(operation="replace_color", domain="color"):
    return {
        "capability_name": f"{operation}_capability",
        "operation": operation,
        "domain": domain,
        "context_class": "qualification",
        "evidence_scope": "capability_support",
    }


def _accepted(
    evidence_id,
    *,
    subject=None,
    source="source_a",
    causal=True,
    target=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED.value,
):
    subject = subject or _subject()
    claim_id = "claim_replace_color_support"
    capability_id = capability_id_for_subject(subject)
    return {
        "accepted_evidence_id": evidence_id,
        "evidence_acceptance_state": "ACCEPTED",
        "evidence_decision_id": f"decision_{evidence_id}",
        "accepted_evidence_current_state": {
            "current_status": "ACTIVE",
            "is_currently_accepted": True,
            "fingerprint": f"current_fingerprint_{evidence_id}",
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
        "capability_id": capability_id,
        "capability_subject": subject,
        "target_operation": subject["operation"],
        "qualification_target_level": target,
        "required_independent_sources": 2,
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
            "origin_task_execution_id": f"execution_{evidence_id}",
            "origin_task_id": f"task_{evidence_id}",
        },
        "accepted_evidence_origin": {
            "accepted_evidence_origin_state": "TASK_ORIGIN_PRESERVED",
            "origin_task_execution_id": f"execution_{evidence_id}",
            "origin_task_id": f"task_{evidence_id}",
            "origin_attempt_id": f"attempt_{evidence_id}",
            "origin_operation_id": source,
            "authority": "NONE",
            "behavioral_authority": "NONE",
        },
        "capability_causal_support_state": (
            "CAUSALLY_SUPPORTED" if causal else "OBSERVED_ONLY"
        ),
    }


def _binding(tmp_path):
    store = EvidenceAcquisitionPlanStore(tmp_path / "plans")
    return NaturalQualificationAssessmentBinding(
        evidence_plan_store=store,
        state_dir=tmp_path / "qualification_binding",
    )


def _write_curriculum(path):
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
                    "validation_objective": (
                        "observe cross-source consensus without evaluator target"
                    ),
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


def test_runtime_binding_invokes_qualification_with_governed_accepted_evidence(tmp_path):
    binding = _binding(tmp_path)

    report = binding.assess_current_accepted_evidence(
        run_id="run_binding",
        accepted_evidence=[_accepted("accepted_a")],
    )

    result = report["qualification_results"][0]
    decision = result["qualification_decision"]
    assert report["qualification_assessment_invocation_count"] == 1
    assert report["governed_accepted_evidence_only"] is True
    assert decision["capability_id"] == capability_id_for_subject(_subject())
    assert decision["decision_state"] == "PROMOTION_DENIED"
    assert "independent_reproducibility_not_established" in (
        decision["promotion_failures"]
    )
    assert result["qualification_binding"]["main_grants_qualification"] is False


def test_qualification_result_reaches_existing_orchestrator_to_plan(tmp_path):
    binding = _binding(tmp_path)
    result_report = binding.assess_current_accepted_evidence(
        run_id="run_binding",
        accepted_evidence=[_accepted("accepted_a")],
    )
    need = CurrentEvidenceNeedAuthorityEngine(tmp_path / "needs")
    sponsorship = ValidationSponsorshipAuthorityEngine(
        tmp_path / "sponsorships",
        need_authority=need,
    )
    request = ValidationRequestAuthorityEngine(
        tmp_path / "requests",
        sponsorship_authority=sponsorship,
    )
    orchestrator = NaturalCanonicalValidationOrchestrator(
        evidence_plan_store=binding.evidence_plan_store,
        need_authority=need,
        sponsorship_authority=sponsorship,
        request_authority=request,
    )

    orchestration = orchestrator.orchestrate(
        result_report["qualification_results"],
        max_new_needs=3,
    )

    assert orchestration["authority"] == "NONE"
    assert orchestration["natural_deficit_count"] == 1
    assert orchestration["natural_active_need_count"] >= 1
    assert orchestration["natural_active_sponsorship_count"] >= 1
    assert orchestration["natural_pending_request_count"] >= 1
    assert orchestration["natural_plan_created_count"] >= 1


def test_same_assessment_replay_is_idempotent(tmp_path):
    binding = _binding(tmp_path)
    evidence = [_accepted("accepted_a")]

    first = binding.assess_current_accepted_evidence(
        run_id="run_binding",
        accepted_evidence=evidence,
    )
    second = binding.assess_current_accepted_evidence(
        run_id="run_binding",
        accepted_evidence=evidence,
    )

    assert first["qualification_assessment_invocation_count"] == 1
    assert second["qualification_assessment_invocation_count"] == 1
    assert second["qualification_assessment_replay_count"] == 1
    assert second["qualification_results"][0]["qualification_binding"][
        "assessment_replay_state"
    ] == "SAME_STATE_REPLAY"


def test_changed_evidence_state_permits_reassessment(tmp_path):
    binding = _binding(tmp_path)
    first = [_accepted("accepted_a")]
    changed = [_accepted("accepted_a"), _accepted("accepted_b", source="source_b")]

    first_report = binding.assess_current_accepted_evidence(
        run_id="run_binding",
        accepted_evidence=first,
    )
    changed_report = binding.assess_current_accepted_evidence(
        run_id="run_binding",
        accepted_evidence=changed,
    )

    assert first_report["qualification_results"][0]["qualification_binding"][
        "assessment_state_fingerprint"
    ] != changed_report["qualification_results"][0]["qualification_binding"][
        "assessment_state_fingerprint"
    ]
    assert changed_report["qualification_assessment_replay_count"] == 0


def test_no_evidence_and_missing_target_do_not_create_fake_deficit(tmp_path):
    binding = _binding(tmp_path)
    missing = _accepted("accepted_without_target", target=None)

    empty = binding.assess_current_accepted_evidence(
        run_id="run_binding",
        accepted_evidence=[],
    )
    no_target = binding.assess_current_accepted_evidence(
        run_id="run_binding_2",
        accepted_evidence=[missing],
    )

    assert empty["qualification_assessment_invocation_count"] == 0
    assert empty["structured_deficit_count"] == 0
    assert no_target["qualification_assessment_invocation_count"] == 0
    assert no_target["qualification_assessment_not_applicable_count"] == 1
    assert no_target["structured_deficit_count"] == 0


def test_binding_loads_accepted_evidence_from_plan_store(tmp_path):
    binding = _binding(tmp_path)
    accepted_dir = binding.evidence_plan_store.root_path / "accepted_evidence"
    accepted_dir.mkdir(parents=True)
    payload = _accepted("accepted_persisted")
    (accepted_dir / "accepted_persisted.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    report = binding.assess_current_accepted_evidence(run_id="run_binding")

    assert report["accepted_evidence_input_count"] == 1
    assert report["qualification_assessment_invocation_count"] == 1


def test_natural_plan_to_accepted_evidence_triggers_qualification_reassessment(tmp_path):
    binding = _binding(tmp_path)
    first = binding.assess_current_accepted_evidence(
        run_id="run_binding",
        accepted_evidence=[_accepted("accepted_a")],
    )
    need = CurrentEvidenceNeedAuthorityEngine(tmp_path / "needs")
    sponsorship = ValidationSponsorshipAuthorityEngine(
        tmp_path / "sponsorships",
        need_authority=need,
    )
    request = ValidationRequestAuthorityEngine(
        tmp_path / "requests",
        sponsorship_authority=sponsorship,
    )
    orchestrator = NaturalCanonicalValidationOrchestrator(
        evidence_plan_store=binding.evidence_plan_store,
        need_authority=need,
        sponsorship_authority=sponsorship,
        request_authority=request,
    )
    orchestration = orchestrator.orchestrate(
        first["qualification_results"],
        max_new_needs=1,
    )
    plan_report = orchestration["orchestration_rows"][0]["plan_admission_report"]
    plan_id = plan_report["evidence_plan_id"]

    binding.evidence_plan_store.load_pending_plans()
    binding.evidence_plan_store.mark_consumption_pending(plan_id)
    binding.evidence_plan_store.persist_selection_from_consumption_report({
        "current_plan_id": plan_id,
        "selection_state": "WAITING_EXECUTION",
        "selected_validation_task": "elite_validation_task_31",
        "best_matching_curriculum": "Elite Validation Academy",
        "current_required_evidence": "cross_source_consensus_evidence",
        "current_target_operation": "SOURCE_INDEPENDENCE_REQUIRED",
        "current_tie_break_strategy": "cross_source_consensus",
        "selected_validation_task_metadata": {
            "curriculum_id": "elite_validation_academy",
        },
    })
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    scheduler = ValidationTaskScheduler(
        tmp_path / "plans",
        registry,
        need_authority=need,
        sponsorship_authority=sponsorship,
        request_authority=request,
    )
    schedule = scheduler.schedule_plan(plan_id)
    raw = ValidationTaskExecutionPipeline(
        tmp_path / "plans",
        registry,
        need_authority=need,
        sponsorship_authority=sponsorship,
        request_authority=request,
    ).execute_schedule(schedule["schedule_id"])
    evaluation = ValidationEvidenceEvaluator(
        tmp_path / "plans",
        registry,
    ).evaluate_plan(plan_id)

    accepted_dir = tmp_path / "plans" / "accepted_evidence"
    (accepted_dir / "accepted_a.json").write_text(
        json.dumps(_accepted("accepted_a")),
        encoding="utf-8",
    )
    reassessment = binding.assess_current_accepted_evidence(
        run_id="run_after_accepted_evidence",
    )
    accepted_path = (
        tmp_path
        / "plans"
        / "accepted_evidence"
        / f"{evaluation['accepted_evidence_id']}.json"
    )
    accepted = json.loads(accepted_path.read_text(encoding="utf-8"))

    assert schedule["scheduling_state"] == "SCHEDULED"
    assert raw["execution_state"] == "RAW_RESULT_CAPTURED"
    assert evaluation["evidence_acceptance_state"] == "ACCEPTED"
    assert accepted["capability_subject"]["operation"] == _subject()["operation"]
    assert accepted["capability_id"] == capability_id_for_subject(
        accepted["capability_subject"]
    )
    assert accepted["qualification_target_level"] == (
        CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED.value
    )
    assert reassessment["qualification_assessment_invocation_count"] == 1
    assert reassessment["qualification_assessment_replay_count"] == 0
    result = reassessment["qualification_results"][0]
    assert result["qualification_binding"]["assessment_replay_state"] == (
        "NEW_EVIDENCE_STATE"
    )
    assert result["qualification_decision"]["qualification_authority"] == (
        "INTEGRATED_CAPABILITY_QUALIFICATION_ENGINE"
    )
    assert result["qualification_decision"]["decision_state"] == "PROMOTION_DENIED"
    assert (
        result["capability_evidence_assessment"]["independent_source_count"]
        == 1
    )
    assert "independent_reproducibility_not_established" in (
        result["qualification_decision"]["promotion_failures"]
    )
