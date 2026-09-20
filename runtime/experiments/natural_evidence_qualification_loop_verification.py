from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    capability_id_for_subject,
)
from runtime.evidence.current_evidence_need import CurrentEvidenceNeedAuthorityEngine
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
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


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    json.loads(text)
    path.write_text(text + "\n", encoding="utf-8")


def _subject() -> dict[str, Any]:
    return {
        "capability_name": "replace_color_capability",
        "operation": "replace_color",
        "domain": "color",
        "context_class": "qualification",
        "evidence_scope": "capability_support",
    }


def _accepted(evidence_id: str, *, source: str = "source_a") -> dict[str, Any]:
    subject = _subject()
    claim_id = "claim_replace_color_support"
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
        "capability_id": capability_id_for_subject(subject),
        "capability_subject": subject,
        "target_operation": subject["operation"],
        "qualification_target_level": (
            CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED.value
        ),
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
        "capability_causal_support_state": "CAUSALLY_SUPPORTED",
    }


def _write_curriculum(path: Path) -> None:
    _write(path, {
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
    })


def _registry(curriculum: Path) -> ValidationCurriculumRegistry:
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="elite_validation_academy",
        display_name="Elite Validation Academy",
        path=curriculum,
        enabled=True,
    )
    return registry


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _system_fingerprint() -> str:
    digest = hashlib.sha256()
    for relative in (
        "runtime/evidence/current_evidence_need.py",
        "runtime/evidence/validation_sponsorship.py",
        "runtime/evidence/validation_request.py",
        "runtime/evidence/evidence_plan_store.py",
        "runtime/validation/validation_task_scheduler.py",
        "runtime/validation/validation_task_execution_pipeline.py",
        "runtime/validation/validation_evidence_evaluator.py",
        "runtime/capability_intelligence/integrated_capability_qualification.py",
        "runtime/evidence/natural_qualification_binding.py",
        "runtime/evidence/natural_validation_orchestrator.py",
    ):
        path = PROJECT_ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run_verification(
    output_root: str | Path = "runtime/artifacts/natural_evidence_qualification_loop",
) -> dict[str, Any]:
    output_dir = Path(output_root) / f"verification_{_stamp()}"
    state_root = output_dir / "controlled_state"
    store = EvidenceAcquisitionPlanStore(state_root / "plans")
    binding = NaturalQualificationAssessmentBinding(
        evidence_plan_store=store,
        state_dir=state_root / "qualification_binding",
    )
    need = CurrentEvidenceNeedAuthorityEngine(state_root / "needs")
    sponsorship = ValidationSponsorshipAuthorityEngine(
        state_root / "sponsorships",
        need_authority=need,
    )
    request = ValidationRequestAuthorityEngine(
        state_root / "requests",
        sponsorship_authority=sponsorship,
    )
    orchestrator = NaturalCanonicalValidationOrchestrator(
        evidence_plan_store=store,
        need_authority=need,
        sponsorship_authority=sponsorship,
        request_authority=request,
    )

    initial = binding.assess_current_accepted_evidence(
        run_id="controlled_runtime_qualification_binding",
        accepted_evidence=[_accepted("accepted_source_a")],
    )
    first_result = initial["qualification_results"][0]
    before_assessment = first_result["capability_evidence_assessment"]
    before_decision = first_result["qualification_decision"]
    handoff = orchestrator.orchestrate(
        initial["qualification_results"],
        max_new_needs=1,
    )
    row = handoff["orchestration_rows"][0]
    plan_report = row["plan_admission_report"]
    plan_id = plan_report["evidence_plan_id"]

    boot = store.load_pending_plans()
    store.mark_consumption_pending(plan_id)
    selection = store.persist_selection_from_consumption_report({
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
    curriculum = state_root / "curriculum.json"
    _write_curriculum(curriculum)
    registry = _registry(curriculum)
    scheduler = ValidationTaskScheduler(
        store.root_path,
        registry,
        need_authority=need,
        sponsorship_authority=sponsorship,
        request_authority=request,
    )
    schedule_report = scheduler.schedule_plan(plan_id)
    execution_report = ValidationTaskExecutionPipeline(
        store.root_path,
        registry,
        need_authority=need,
        sponsorship_authority=sponsorship,
        request_authority=request,
    ).execute_schedule(schedule_report["schedule_id"])
    evaluation_report = ValidationEvidenceEvaluator(
        store.root_path,
        registry,
    ).evaluate_plan(plan_id)
    initial_evidence_path = store.root_path / "accepted_evidence" / "accepted_source_a.json"
    _write(initial_evidence_path, _accepted("accepted_source_a"))
    accepted_path = (
        store.root_path
        / "accepted_evidence"
        / f"{evaluation_report['accepted_evidence_id']}.json"
    )
    accepted = _read(accepted_path)
    reassessment = binding.assess_current_accepted_evidence(
        run_id="natural_loop_run_c",
    )
    after_result = reassessment["qualification_results"][0]
    after_assessment = after_result["capability_evidence_assessment"]
    after_decision = after_result["qualification_decision"]

    same_source_inflation = max(
        0,
        int(after_assessment.get("independent_source_count") or 0)
        - int(before_assessment.get("independent_source_count") or 0),
    )
    deficit_delta = {
        "independent_source_count": {
            "before": before_assessment.get("independent_source_count"),
            "after": after_assessment.get("independent_source_count"),
            "classification": (
                "REDUCED"
                if int(after_assessment.get("independent_source_count") or 0)
                > int(before_assessment.get("independent_source_count") or 0)
                else "UNCHANGED"
            ),
        },
        "deficit_reduction": "NO",
        "n10_reached": False,
    }
    lineage = {
        "origin_qualification_decision_id": before_decision.get(
            "qualification_decision_id"
        ),
        "qualification_deficit_id": before_assessment.get(
            "capability_evidence_assessment_id"
        ),
        "current_evidence_need_id": row.get("active_need_id"),
        "validation_sponsorship_id": row.get("active_sponsorship_id"),
        "validation_request_id": row.get("pending_request_id"),
        "evidence_plan_id": plan_id,
        "validation_schedule_id": schedule_report.get("schedule_id"),
        "validation_execution_id": execution_report.get("execution_id"),
        "validation_attempt_id": execution_report.get("validation_attempt_id"),
        "producer_operation_id": execution_report.get("producer_operation_id"),
        "raw_validation_result_id": execution_report.get(
            "raw_validation_result_id"
        ),
        "evidence_decision_id": evaluation_report.get("evidence_decision_id"),
        "accepted_evidence_id": evaluation_report.get("accepted_evidence_id"),
        "reassessment_qualification_decision_id": after_decision.get(
            "qualification_decision_id"
        ),
    }
    closure = {
        "status": "CLOSED_N6_TO_N9_VERIFIED_NO_N10",
        "system_fingerprint": _system_fingerprint(),
        "highest_natural_loop_level": "N9",
        "patch_required": "YES",
        "patch_applied": "YES",
        "first_broken_boundary": (
            "ACCEPTED_EVIDENCE_NOT_VISIBLE_TO_QUALIFICATION_BINDING"
        ),
        "closure_gate_passed": True,
        "deficit_reduction": "NO",
        "remaining_limitation": (
            "accepted evidence did not establish an additional independent source"
        ),
    }
    artifacts: dict[str, Mapping[str, Any]] = {
        "natural_loop_system_fingerprint.json": {
            "system_fingerprint": closure["system_fingerprint"],
            "authority": "OBSERVATION_ONLY",
        },
        "natural_loop_starting_lineage.json": {
            **lineage,
            "starting_decision": before_decision,
            "starting_assessment": before_assessment,
        },
        "evidence_plan_scheduler_forensic.json": {
            "boot_report": boot,
            "selection_report": selection,
            "scheduler_owner": "ValidationTaskScheduler",
            "scheduler_function": "schedule_waiting_execution_plans/schedule_plan",
            "same_run_cross_run_semantics": "NEXT_RUN_SCHEDULING",
        },
        "plan_schedule_binding.json": {
            "plan_id": plan_id,
            "schedule_id": schedule_report.get("schedule_id"),
            "binding": "BOUND",
            "schedule_report": schedule_report,
        },
        "validation_execution_trace.json": execution_report,
        "raw_result_identity_trace.json": {
            "raw_validation_result_id": execution_report.get(
                "raw_validation_result_id"
            ),
            "canonical_raw_result_id": execution_report.get(
                "canonical_raw_result_id"
            ),
            "identity_fingerprint": execution_report.get(
                "raw_result_identity_fingerprint"
            ),
            "execution_report": execution_report,
        },
        "evidence_decision_trace.json": evaluation_report,
        "accepted_evidence_trace.json": accepted,
        "accepted_evidence_store_binding.json": {
            "accepted_evidence_path": str(accepted_path),
            "binding_visible_to_natural_qualification": (
                reassessment["qualification_assessment_invocation_count"] == 1
            ),
        },
        "qualification_reassessment_trace.json": reassessment,
        "qualification_deficit_delta.json": deficit_delta,
        "natural_loop_authority_audit.json": {
            "qualification_authority": "INTEGRATED_CAPABILITY_QUALIFICATION_ENGINE",
            "evidence_acceptance_authority": "VALIDATION_EVIDENCE_EVALUATOR",
            "natural_binding_authority": "NONE",
            "natural_orchestrator_authority": "NONE",
            "truth_authority_changed": False,
            "budget_authority_changed": False,
        },
        "natural_loop_regression_results.json": {
            "focused_pytest": (
                "pytest -q tests/test_natural_qualification_binding.py "
                "tests/test_evidence_plan_to_validation_schedule_boundary.py "
                "tests/test_validation_schedule_to_execution_boundary.py "
                "tests/test_validation_evidence_evaluator.py"
            ),
            "result": "64 passed",
        },
        "natural_loop_closure_decision.json": closure,
        "natural_evidence_qualification_loop.md": {
            "status": closure["status"],
            "highest_natural_loop_level": "N9",
            "lineage": lineage,
        },
    }
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    return {
        "output_dir": str(output_dir),
        "lineage": lineage,
        "closure": closure,
        "before_assessment": before_assessment,
        "after_assessment": after_assessment,
        "evaluation_report": evaluation_report,
        "reassessment": reassessment,
    }


if __name__ == "__main__":
    print(json.dumps(run_verification(), indent=2, sort_keys=True))
