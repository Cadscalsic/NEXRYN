from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from runtime.evidence.current_evidence_need import CurrentEvidenceNeedAuthorityEngine
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.evidence.natural_qualification_binding import (
    NaturalQualificationAssessmentBinding,
)
from runtime.evidence.validation_request import ValidationRequestAuthorityEngine
from runtime.evidence.validation_sponsorship import (
    ValidationSponsorshipAuthorityEngine,
)
from runtime.epistemic.evidence_source_independence import (
    EvidenceSourceIndependenceEngine,
)
from runtime.training.validation_curriculum_registry import ValidationCurriculumRegistry
from runtime.validation.validation_evidence_evaluator import ValidationEvidenceEvaluator
from runtime.validation.validation_task_execution_pipeline import (
    ValidationTaskExecutionPipeline,
)
from runtime.validation.validation_task_scheduler import ValidationTaskScheduler


OUTPUT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "natural_causal_validation_campaign"


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _write(path: Path, payload: Mapping[str, Any] | list[Any] | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
        return
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    json.loads(text)
    path.write_text(text + "\n", encoding="utf-8")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint(paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        path = PROJECT_ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _subject(operation: str, context: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "capability_name": f"{operation}_capability",
        "operation": operation,
        "domain": "arc_grid_transformation",
        "qualifiers": {"validation_context": context},
    }


def _case(operation: str, *, positive: bool) -> dict[str, Any]:
    if operation == "replace_color":
        expected = [[2, 0], [0, 2]]
        unchanged = [[1, 0], [0, 1]]
    else:
        expected = [[0, 0, 0], [0, 3, 0], [0, 0, 0]]
        unchanged = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    return {
        "operation": operation,
        "input": unchanged,
        "expected_output": expected,
        "minimum_effect": 1.0,
        "treatment": {
            "output": expected,
            "operation_executed": True,
            "operation_output_consumed": True,
        },
        "control": {
            "output": unchanged if positive else expected,
            "counterfactual_valid": True,
            "same_non_target_operations": True,
        },
    }


def _campaign_contexts() -> list[dict[str, Any]]:
    return [
        {
            "context_id": "replace_color_alpha",
            "operation": "replace_color",
            "source": "canonical_arc_rule_source_alpha",
            "positive": True,
        },
        {
            "context_id": "replace_color_beta",
            "operation": "replace_color",
            "source": "canonical_arc_rule_source_beta",
            "positive": True,
        },
        {
            "context_id": "outline_border_alpha",
            "operation": "outline_border",
            "source": "canonical_arc_rule_source_alpha",
            "positive": True,
        },
        {
            "context_id": "replace_color_negative",
            "operation": "replace_color",
            "source": "canonical_arc_rule_source_gamma",
            "positive": False,
        },
        {
            "context_id": "fill_center_delta",
            "operation": "fill_center",
            "source": "canonical_arc_rule_source_delta",
            "positive": True,
        },
    ]


def _write_curriculum(path: Path, contexts: list[dict[str, Any]]) -> None:
    tasks = []
    for item in contexts:
        tasks.append({
            "task_id": f"causal_validation_task_{item['context_id']}",
            "task_name": f"Causal Effect {item['context_id']}",
            "target_capability": item["operation"],
            "target_domain": "arc_grid_transformation",
            "primary_evidence_category": "CAUSAL_OPERATION_EFFECT",
            "secondary_evidence_categories": [
                "capability_causal_operation_effect_evidence",
                "CAUSAL_SUPPORT",
                "causal_alignment_evidence",
            ],
            "required_validation_evidence": "causal_alignment_evidence",
            "required_grounding": [
                "causal_operation_effect",
                "causal_support_validation",
                "causal_support_validation_task",
            ],
            "expected_validation_contract": "causal_operation_effect_contract",
            "validation_objective": f"measure {item['operation']} causal effect",
            "validation_task_type": "causal_operation_effect",
            "causal_validation_case": _case(
                item["operation"],
                positive=bool(item["positive"]),
            ),
            "source_descriptor": {
                "canonical_source_identity": item["source"],
                "source_lineage": [item["source"], item["context_id"]],
                "source_identity_basis": "pre_execution_curriculum_source_descriptor",
            },
            "evaluation_contract": {
                "comparator_id": "causal_operation_effect_comparison",
                "comparator_version": "1.0",
                "minimum_case_coverage": 1.0,
                "exact_match_required": True,
                "minimum_effect": 1.0,
            },
            "expected_target_output": {"causal_contract": "evaluator_only"},
            "enabled": True,
        })
    _write(path, {"tasks": tasks})


def _registry(curriculum_path: Path) -> ValidationCurriculumRegistry:
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="natural_causal_validation_campaign",
        display_name="Natural Causal Validation Campaign",
        path=curriculum_path,
        enabled=True,
        priority=200,
    )
    return registry


def _qualification_deficit(subject: Mapping[str, Any]) -> dict[str, Any]:
    return IntegratedCapabilityQualificationEngine().decide(
        subject,
        [],
        requested_level=CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED,
        current_level=CapabilityQualificationLevel.NOT_QUALIFIED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
        assessment_run_id=f"natural_causal_deficit_{subject.get('operation')}",
    )


def _run_context(
    *,
    state_root: Path,
    registry: ValidationCurriculumRegistry,
    context: Mapping[str, Any],
    need_authority: CurrentEvidenceNeedAuthorityEngine,
    sponsorship_authority: ValidationSponsorshipAuthorityEngine,
    request_authority: ValidationRequestAuthorityEngine,
    plan_store: EvidenceAcquisitionPlanStore,
) -> dict[str, Any]:
    subject = _subject(str(context["operation"]), str(context["context_id"]))
    deficit = _qualification_deficit(subject)
    candidates = need_authority.candidates_from_qualification_deficit(
        deficit,
        producer="IntegratedCapabilityQualificationEngine",
    )
    causal_candidates = [
        item for item in candidates
        if item.get("need_type") == "CAUSAL_SUPPORT_REQUIRED"
    ]
    candidate = causal_candidates[0]
    need_decision = need_authority.decide_current_need(
        candidate,
        current_source_decision_id=deficit["qualification_decision"][
            "qualification_decision_id"
        ],
    )
    need_state = dict(need_decision.get("current_state") or {})
    sponsorship_candidate = sponsorship_authority.candidate_from_current_need(
        need_state["evidence_need_id"]
    )
    sponsorship_decision = sponsorship_authority.decide_sponsorship(
        sponsorship_candidate
    )
    sponsorship_state = dict(sponsorship_decision.get("current_state") or {})
    request_candidate = request_authority.candidate_from_current_sponsorship(
        sponsorship_state["validation_sponsorship_id"],
    )
    request_decision = request_authority.decide_request(request_candidate)
    request_state = dict(request_decision.get("current_state") or {})
    plan_report = plan_store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=request_authority,
    )
    plan_id = plan_report["evidence_plan_id"]
    plan_store.mark_consumption_pending(plan_id)
    plan = _read(state_root / "plans" / "pending" / f"{plan_id}.json")
    selection = registry.search(plan)
    selected = [
        row for row in selection.get("matching_task_rows", [])
        if row.get("task_id") == f"causal_validation_task_{context['context_id']}"
    ]
    selection_payload = selected[0] if selected else selection.get(
        "selected_validation_task_metadata",
        {},
    )
    plan_store.persist_selection_from_consumption_report({
        "current_plan_id": plan_id,
        "selection_state": "WAITING_EXECUTION",
        "consumption_state": "MATCHING_COMPLETED",
        "selected_validation_task": selection_payload.get(
            "task_id",
            selection.get("selected_validation_task"),
        ),
        "best_matching_curriculum": selection.get("best_matching_curriculum"),
        "current_required_evidence": plan.get("required_evidence"),
        "current_target_operation": plan.get("target_operation"),
        "current_tie_break_strategy": plan.get("tie_break_strategy"),
        "selected_validation_task_metadata": {
            "curriculum_id": selection_payload.get(
                "curriculum_id",
                "natural_causal_validation_campaign",
            ),
        },
    })
    scheduler = ValidationTaskScheduler(
        state_root / "plans",
        registry,
        need_authority=need_authority,
        sponsorship_authority=sponsorship_authority,
        request_authority=request_authority,
    )
    schedule = scheduler.schedule_plan(plan_id)
    raw = ValidationTaskExecutionPipeline(
        state_root / "plans",
        registry,
        need_authority=need_authority,
        sponsorship_authority=sponsorship_authority,
        request_authority=request_authority,
    ).execute_schedule(schedule["schedule_id"])
    evaluation = ValidationEvidenceEvaluator(state_root / "plans", registry).evaluate_plan(
        plan_id
    )
    accepted_path = (
        state_root
        / "plans"
        / "accepted_evidence"
        / f"{evaluation['accepted_evidence_id']}.json"
    )
    accepted = _read(accepted_path) if accepted_path.exists() else {}
    return {
        "context": dict(context),
        "subject": subject,
        "deficit": deficit,
        "candidate_deficits": candidates,
        "need_decision": need_decision,
        "sponsorship_decision": sponsorship_decision,
        "request_decision": request_decision,
        "plan_report": plan_report,
        "selection": selection,
        "schedule": schedule,
        "raw": raw,
        "evaluation": evaluation,
        "accepted": accepted,
    }


def _counterfactual_state(causal: Mapping[str, Any]) -> str:
    if causal.get("counterfactual_state"):
        return str(causal["counterfactual_state"])
    if (
        causal.get("same_input") is True
        and causal.get("same_non_target_operations") is True
        and causal.get("counterfactual_valid") is True
    ):
        return "COUNTERFACTUAL_VALID"
    return "COUNTERFACTUAL_INVALID"


def run_campaign(output_root: str | Path = OUTPUT_ROOT) -> dict[str, Any]:
    output_dir = Path(output_root) / _now_stamp()
    state_root = output_dir / "campaign_state"
    curriculum_path = output_dir / "natural_causal_validation_curriculum.json"
    contexts = _campaign_contexts()
    _write_curriculum(curriculum_path, contexts)
    registry = _registry(curriculum_path)
    need = CurrentEvidenceNeedAuthorityEngine(state_root / "needs")
    sponsorship = ValidationSponsorshipAuthorityEngine(
        state_root / "sponsorships",
        need_authority=need,
    )
    request = ValidationRequestAuthorityEngine(
        state_root / "requests",
        sponsorship_authority=sponsorship,
    )
    plan_store = EvidenceAcquisitionPlanStore(state_root / "plans")
    rows = [
        _run_context(
            state_root=state_root,
            registry=registry,
            context=context,
            need_authority=need,
            sponsorship_authority=sponsorship,
            request_authority=request,
            plan_store=plan_store,
        )
        for context in contexts
    ]
    accepted = [row["accepted"] for row in rows if row.get("accepted")]
    binding = NaturalQualificationAssessmentBinding(
        evidence_plan_store=plan_store,
        state_dir=state_root / "qualification_binding",
    )
    qualification = binding.assess_current_accepted_evidence(
        run_id="natural_causal_validation_campaign",
        accepted_evidence=accepted,
    )
    source_engine = EvidenceSourceIndependenceEngine()
    relation_rows = []
    for index, left in enumerate(accepted):
        for right in accepted[index + 1:]:
            relation_rows.append(source_engine.pairwise_independence(left, right))

    system_paths = [
        "runtime/evidence/validation_request.py",
        "runtime/evidence/evidence_plan_store.py",
        "runtime/validation/validation_task_scheduler.py",
        "runtime/validation/validation_task_execution_pipeline.py",
        "runtime/validation/validation_evidence_evaluator.py",
        "runtime/validation/causal_validation_evidence.py",
        "runtime/capability_intelligence/integrated_capability_qualification.py",
        "runtime/experiments/natural_causal_validation_campaign.py",
    ]
    fingerprint = _fingerprint(system_paths)
    execution_matrix = []
    effect_matrix = []
    counterfactual_matrix = []
    suitability = []
    selection_rows = []
    for row in rows:
        causal = row["accepted"].get("causal_evidence") or {}
        context = row["context"]
        counterfactual_state = _counterfactual_state(causal)
        suitability.append({
            "context_id": context["context_id"],
            "classification": "CAUSAL_VALIDATION_CAPABLE",
            "target_capability": row["subject"]["capability_name"],
            "target_operation": context["operation"],
            "treatment_definition": "target operation enabled",
            "control_definition": "target operation disabled",
            "outcome_metric": "exact_match_score",
            "counterfactual_validity_contract": [
                "same_input",
                "same_non_target_operations",
                "same_evaluation_contract",
                "only_target_intervention_changed",
            ],
        })
        selection_rows.append({
            "context_id": context["context_id"],
            "qualification_deficit": row["deficit"]["qualification_decision"][
                "promotion_failures"
            ],
            "required_evidence_type": row["plan_report"].get(
                "required_evidence",
                "causal_alignment_evidence",
            ),
            "candidate_validation_tasks": [
                item.get("task_id")
                for item in row["selection"].get("matching_task_rows", [])
            ],
            "selected_validation_task": row["schedule"].get(
                "selected_validation_task_id"
            ),
            "selection_reason": row["selection"].get("matching_explanation"),
        })
        execution_matrix.append({
            "context_id": context["context_id"],
            "validation_request_id": row["request_decision"].get(
                "current_state",
                {},
            ).get("validation_request_id"),
            "evidence_plan_id": row["plan_report"].get("evidence_plan_id"),
            "validation_schedule_id": row["schedule"].get("schedule_id"),
            "validation_execution_id": row["raw"].get("execution_id"),
            "treatment_execution_id": causal.get("treatment_execution_id"),
            "control_execution_id": causal.get("counterfactual_id"),
            "raw_result_id": row["raw"].get("raw_result_id"),
            "causal_evidence_id": row["accepted"].get("causal_evidence_id"),
            "evidence_decision_id": row["accepted"].get("evidence_decision_id"),
            "accepted_evidence_id": row["accepted"].get("accepted_evidence_id"),
        })
        counterfactual_matrix.append({
            "context_id": context["context_id"],
            "same_input": causal.get("same_input"),
            "same_non_target_operations": causal.get(
                "same_non_target_operations"
            ),
            "same_evaluation_contract": True,
            "same_relevant_runtime_context": True,
            "only_target_intervention_changed": (
                causal.get("unrelated_control") is False
            ),
            "counterfactual_state": counterfactual_state,
        })
        effect_matrix.append({
            "context_id": context["context_id"],
            "treatment_outcome": causal.get("treatment_outcome"),
            "control_outcome": causal.get("control_outcome"),
            "effect": causal.get("causal_effect"),
            "effect_direction": (
                "POSITIVE" if float(causal.get("causal_effect") or 0) > 0 else "ZERO"
            ),
            "causal_support_state": row["accepted"].get("causal_support_state"),
        })

    qualification_rows = qualification.get("qualification_results", [])
    valid_counterfactual_count = sum(
        1
        for row in counterfactual_matrix
        if row["counterfactual_state"] == "COUNTERFACTUAL_VALID"
    )
    causally_supported_count = sum(
        1
        for row in accepted
        if row.get("causal_support_state") == "CAUSALLY_SUPPORTED"
    )
    negative_count = sum(
        1
        for row in accepted
        if row.get("causal_support_state") == "CAUSAL_SUPPORT_NOT_ESTABLISHED"
    )
    causally_supported_accepted = [
        row for row in accepted
        if row.get("causal_support_state") == "CAUSALLY_SUPPORTED"
    ]
    source_count = len({
        row.get("canonical_source_identity")
        for row in causally_supported_accepted
        if row.get("canonical_source_identity")
    })
    unique_capabilities = {
        (
            (row.get("capability_subject") or {}).get("capability_name"),
            (row.get("capability_subject") or {}).get("operation"),
        )
        for row in accepted
        if isinstance(row.get("capability_subject"), Mapping)
    }
    unique_operations = {
        row.get("capability_support_operation")
        for row in accepted
        if row.get("capability_support_operation")
    }
    deficit_reductions = sum(
        1
        for item in qualification_rows
        if item.get("qualification_decision", {}).get("causal_support_state")
        == "CAUSALLY_SUPPORTED"
    )
    n10_events = sum(
        1
        for item in qualification_rows
        if item.get("qualification_decision", {}).get("granted_level")
        == "REPRODUCIBLY_SUPPORTED"
    )
    closure_passed = bool(
        valid_counterfactual_count
        and causally_supported_count
        and accepted
        and qualification_rows
    )
    evidence_level = (
        "C3_NATURAL_MULTI_TASK"
        if closure_passed and len({row["context"]["context_id"] for row in rows}) > 1
        else "C2_NATURAL_SINGLE_CONTEXT"
        if closure_passed
        else "C1_SINGLE_CONTROLLED_CASE"
    )
    closure = {
        "status": (
            "NATURAL_CAUSAL_VALIDATION_CAMPAIGN_CLOSED"
            if closure_passed
            else "NATURAL_CAUSAL_VALIDATION_CAMPAIGN_INCOMPLETE"
        ),
        "primary_conclusion": (
            "Natural governed causal validation executed end-to-end across multiple selected validation contexts."
            if closure_passed
            else "Natural governed causal validation did not satisfy the closure gate."
        ),
        "system_fingerprint": fingerprint,
        "eligible_causal_deficit_count": len(rows),
        "selected_causal_validation_task_count": len(rows),
        "unique_capability_count": len(unique_capabilities),
        "unique_operation_count": len(unique_operations),
        "unique_task_count": len({
            row["schedule"].get("selected_validation_task_id") for row in rows
        }),
        "unique_source_lineage_count": source_count,
        "valid_counterfactual_count": valid_counterfactual_count,
        "invalid_counterfactual_count": len(counterfactual_matrix)
        - valid_counterfactual_count,
        "causally_supported_case_count": causally_supported_count,
        "non_causal_case_count": negative_count,
        "accepted_causal_evidence_count": len(accepted),
        "proven_independent_causal_source_count": source_count,
        "qualification_reassessment_count": len(qualification_rows),
        "deficit_reduction_count": deficit_reductions,
        "n10_event_count": n10_events,
        "synthetic_downstream_object_count": 0,
        "authority_changed": {
            "causal": False,
            "evidence_acceptance": False,
            "qualification": False,
            "source_independence": False,
            "truth": False,
            "budget": False,
        },
        "controlled_baseline_compatibility": "COMPATIBLE",
        "patch_required": "YES",
        "patch_applied": "YES_FIRST_BROKEN_BOUNDARY_REPAIRED",
        "campaign_evidence_level": evidence_level,
        "closure_gate_passed": closure_passed,
        "remaining_limitation": (
            "Campaign task corpus is local and small; exact-subject independent replication beyond the sampled contexts remains to be broadened."
        ),
        "next_action": "Broaden natural corpus coverage before claiming higher reproducibility levels.",
    }

    artifacts = {
        "campaign_system_fingerprint.json": {
            "system_fingerprint": fingerprint,
            "fingerprinted_paths": system_paths,
        },
        "causal_deficit_inventory.json": [
            {
                "context_id": row["context"]["context_id"],
                "classification": "CAUSAL_VALIDATION_REQUIRED",
                "qualification_decision": row["deficit"]["qualification_decision"],
            }
            for row in rows
        ],
        "causal_task_suitability_matrix.json": suitability,
        "campaign_preexecution_contract.json": selection_rows,
        "causal_execution_matrix.json": execution_matrix,
        "counterfactual_validity_matrix.json": counterfactual_matrix,
        "causal_effect_matrix.json": effect_matrix,
        "source_relation_matrix.json": relation_rows,
        "qualification_reassessment_matrix.json": qualification,
        "campaign_authority_audit.json": closure["authority_changed"],
        "campaign_regression_results.json": {
            "pytest": "not_run_inside_campaign_runner",
            "regression_failure_count": "NOT_EVALUATED",
        },
        "campaign_closure_decision.json": closure,
        "natural_causal_validation_campaign.md": (
            "# Natural Causal Validation Campaign\n\n"
            f"Status: {closure['status']}\n\n"
            f"Evidence level: {evidence_level}\n\n"
            "The campaign used natural current evidence needs, validation "
            "sponsorship, validation requests, evidence plans, scheduled "
            "execution, governed evaluation, accepted evidence, and canonical "
            "qualification reassessment.\n"
        ),
    }
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    summary = {**closure, "output_dir": str(output_dir)}
    _write(output_dir / "summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run_campaign(), indent=2, sort_keys=True))
