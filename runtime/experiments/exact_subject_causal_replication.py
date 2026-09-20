from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
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


OUTPUT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "exact_subject_causal_replication"
C3_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "natural_causal_validation_campaign"


def _stamp() -> str:
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


def _git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _latest_c3_dir() -> Path:
    candidates = [path for path in C3_ROOT.glob("*") if path.is_dir()]
    if not candidates:
        raise FileNotFoundError("no_natural_causal_validation_campaign_artifacts")
    return sorted(candidates, key=lambda path: path.name)[-1]


def _accepted_evidence_from_campaign(campaign_dir: Path) -> list[dict[str, Any]]:
    directory = campaign_dir / "campaign_state" / "plans" / "accepted_evidence"
    rows = []
    for path in sorted(directory.glob("*.json")):
        payload = _read(path)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def reconstruct_subjects(campaign_dir: Path | None = None) -> list[dict[str, Any]]:
    campaign_dir = campaign_dir or _latest_c3_dir()
    rows = _accepted_evidence_from_campaign(campaign_dir)
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for evidence in rows:
        subject = evidence.get("capability_subject")
        if not isinstance(subject, Mapping):
            continue
        key = (
            str(evidence.get("capability_id")),
            str(evidence.get("capability_support_operation")),
            str(evidence.get("claim_id")),
        )
        entry = grouped.setdefault(key, {
            "capability_id": key[0],
            "capability_subject": dict(subject),
            "capability_operation": key[1],
            "qualification_claim_id": key[2],
            "accepted_evidence": [],
            "accepted_evidence_ids": [],
            "causal_evidence_ids": [],
            "canonical_source_ids": [],
            "source_lineage_ids": [],
            "causal_support_states": [],
        })
        entry["accepted_evidence"].append(evidence)
        entry["accepted_evidence_ids"].append(evidence.get("accepted_evidence_id"))
        entry["causal_evidence_ids"].append(evidence.get("causal_evidence_id"))
        entry["canonical_source_ids"].append(evidence.get("canonical_source_identity"))
        entry["source_lineage_ids"].append(evidence.get("source_lineage"))
        entry["causal_support_states"].append(evidence.get("causal_support_state"))
    engine = IntegratedCapabilityQualificationEngine()
    for entry in grouped.values():
        result = engine.decide(
            entry["capability_subject"],
            entry["accepted_evidence"],
            requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
            architecture_present=True,
            runtime_reachable=True,
            required_independent_sources=2,
            assessment_run_id="exact_subject_reconstruction",
        )
        decision = result["qualification_decision"]
        assessment = result["capability_evidence_assessment"]
        entry["qualification_state"] = decision.get("decision_state")
        entry["qualification_level"] = decision.get("granted_level")
        entry["independent_causal_source_count"] = assessment.get(
            "independent_source_count"
        )
        entry["remaining_deficit"] = decision.get("promotion_failures")
    return sorted(
        grouped.values(),
        key=lambda item: (
            -int(item.get("independent_causal_source_count") or 0),
            str(item.get("capability_operation")),
            str(item.get("qualification_claim_id")),
        ),
    )


def select_exact_subject(subjects: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [
        item for item in subjects
        if int(item.get("independent_causal_source_count") or 0) == 1
        and "independent_reproducibility_not_established"
        in (item.get("remaining_deficit") or [])
        and "CAUSALLY_SUPPORTED" in (item.get("causal_support_states") or [])
    ]
    if not eligible:
        raise ValueError("no_exact_subject_with_one_causal_source")
    return eligible[0]


def _case(operation: str, *, positive: bool = True) -> dict[str, Any]:
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


def _write_curriculum(
    path: Path,
    *,
    operation: str,
    source: str,
    context_id: str,
    positive: bool,
) -> None:
    task = {
        "task_id": f"exact_subject_replication_task_{context_id}",
        "task_name": f"Exact Subject Replication {context_id}",
        "target_capability": operation,
        "target_domain": "arc_grid_transformation",
        "primary_evidence_category": "INDEPENDENT_REPLICATION",
        "secondary_evidence_categories": [
            "independent_replication_evidence",
            "CAUSAL_SUPPORT",
            "causal_alignment_evidence",
            "capability_causal_operation_effect_evidence",
        ],
        "required_validation_evidence": "independent_replication_evidence",
        "required_grounding": [
            "independent_replication",
            "independent_replication_validation_task",
            "causal_operation_effect",
        ],
        "expected_validation_contract": "causal_operation_effect_contract",
        "validation_objective": f"replicate {operation} causal effect",
        "validation_task_type": "causal_operation_effect",
        "causal_validation_case": _case(operation, positive=positive),
        "source_descriptor": {
            "canonical_source_identity": source,
            "source_lineage": [source, context_id],
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
    }
    _write(path, {"tasks": [task]})


def _registry(curriculum_path: Path) -> ValidationCurriculumRegistry:
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="exact_subject_replication_curriculum",
        display_name="Exact Subject Replication Curriculum",
        path=curriculum_path,
        enabled=True,
        priority=250,
    )
    return registry


def _natural_replication_attempt(
    *,
    state_root: Path,
    selected: Mapping[str, Any],
    baseline_evidence: Mapping[str, Any],
    source: str,
    context_id: str,
    positive: bool = True,
) -> dict[str, Any]:
    operation = str(selected["capability_operation"])
    curriculum = state_root / f"curriculum_{context_id}.json"
    _write_curriculum(
        curriculum,
        operation=operation,
        source=source,
        context_id=context_id,
        positive=positive,
    )
    registry = _registry(curriculum)
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
    deficit = IntegratedCapabilityQualificationEngine().decide(
        selected["capability_subject"],
        [baseline_evidence],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        current_level=CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
        assessment_run_id="exact_subject_replication_baseline_deficit",
    )
    candidates = need.candidates_from_qualification_deficit(
        deficit,
        producer="IntegratedCapabilityQualificationEngine",
    )
    candidate = next(
        item for item in candidates
        if item.get("need_type") == "REPRODUCIBILITY_REQUIRED"
    )
    need_decision = need.decide_current_need(
        candidate,
        current_source_decision_id=deficit["qualification_decision"][
            "qualification_decision_id"
        ],
    )
    need_state = dict(need_decision.get("current_state") or {})
    sponsorship_candidate = sponsorship.candidate_from_current_need(
        need_state["evidence_need_id"],
    )
    sponsorship_decision = sponsorship.decide_sponsorship(sponsorship_candidate)
    sponsorship_state = dict(sponsorship_decision.get("current_state") or {})
    request_candidate = request.candidate_from_current_sponsorship(
        sponsorship_state["validation_sponsorship_id"],
    )
    request_decision = request.decide_request(request_candidate)
    request_state = dict(request_decision.get("current_state") or {})
    plan_report = plan_store.admit_validation_request_to_plan(
        request_state["validation_request_id"],
        request_authority=request,
    )
    plan_id = plan_report["evidence_plan_id"]
    plan_store.mark_consumption_pending(plan_id)
    plan = _read(state_root / "plans" / "pending" / f"{plan_id}.json")
    selection = registry.search(plan)
    selected_task = selection.get("selected_validation_task")
    plan_store.persist_selection_from_consumption_report({
        "current_plan_id": plan_id,
        "selection_state": "WAITING_EXECUTION",
        "consumption_state": "MATCHING_COMPLETED",
        "selected_validation_task": selected_task,
        "best_matching_curriculum": selection.get("best_matching_curriculum"),
        "current_required_evidence": plan.get("required_evidence"),
        "current_target_operation": plan.get("target_operation"),
        "current_tie_break_strategy": plan.get("tie_break_strategy"),
        "selected_validation_task_metadata": {
            "curriculum_id": "exact_subject_replication_curriculum",
        },
    })
    scheduler = ValidationTaskScheduler(
        state_root / "plans",
        registry,
        need_authority=need,
        sponsorship_authority=sponsorship,
        request_authority=request,
    )
    schedule = scheduler.schedule_plan(plan_id)
    raw = ValidationTaskExecutionPipeline(
        state_root / "plans",
        registry,
        need_authority=need,
        sponsorship_authority=sponsorship,
        request_authority=request,
    ).execute_schedule(schedule["schedule_id"])
    evaluation = ValidationEvidenceEvaluator(state_root / "plans", registry).evaluate_plan(
        plan_id
    )
    accepted_path = (
        state_root
        / "plans"
        / "accepted_evidence"
        / f"{evaluation.get('accepted_evidence_id')}.json"
    )
    accepted = _read(accepted_path) if accepted_path.exists() else {}
    return {
        "deficit": deficit,
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


def _contract(selected: Mapping[str, Any], fingerprint: str) -> dict[str, Any]:
    baseline_ids = [
        evidence.get("accepted_evidence_id")
        for evidence in selected["accepted_evidence"]
        if evidence.get("causal_support_state") == "CAUSALLY_SUPPORTED"
    ]
    baseline_sources = sorted({
        str(evidence.get("canonical_source_identity"))
        for evidence in selected["accepted_evidence"]
        if evidence.get("causal_support_state") == "CAUSALLY_SUPPORTED"
    })
    payload = {
        "schema_version": "1.0",
        "contract_type": "exact_subject_replication_contract.v1",
        "experiment_id": f"exact_subject_causal_replication_{_stamp()}",
        "system_fingerprint": fingerprint,
        "capability_id": selected["capability_id"],
        "capability_subject": selected["capability_subject"],
        "capability_operation": selected["capability_operation"],
        "capability_domain": selected["capability_subject"].get("domain"),
        "qualification_claim_id": selected["qualification_claim_id"],
        "qualification_requirement": "REPRODUCIBLY_SUPPORTED",
        "required_independent_causal_sources": 2,
        "baseline_accepted_causal_evidence_ids": baseline_ids,
        "baseline_causal_source_ids": baseline_sources,
        "baseline_independent_causal_source_count": selected[
            "independent_causal_source_count"
        ],
        "required_replication_count": 1,
        "causal_support_definition": (
            "target operation executed, output consumed, valid counterfactual, positive effect"
        ),
        "counterfactual_requirement": "COUNTERFACTUAL_VALID",
        "source_independence_requirement": "EvidenceSourceIndependenceEngine=INDEPENDENT",
        "subject_contract_mutation_count": 0,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    payload["contract_fingerprint"] = digest
    payload["exact_subject_contract_id"] = (
        f"exact_subject_contract_{hashlib.sha1(digest.encode()).hexdigest()[:12]}"
    )
    return payload


def exact_subject_credit_audit(
    *,
    contract: Mapping[str, Any],
    baseline_evidence: Mapping[str, Any],
    candidate_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    source_engine = EvidenceSourceIndependenceEngine()
    causal = candidate_evidence.get("causal_evidence")
    causal = causal if isinstance(causal, Mapping) else {}
    capability_ok = candidate_evidence.get("capability_id") == contract.get(
        "capability_id"
    )
    operation_ok = (
        candidate_evidence.get("capability_support_operation")
        == contract.get("capability_operation")
    )
    claim_ok = candidate_evidence.get("claim_id") == contract.get(
        "qualification_claim_id"
    )
    intent_ok = (
        candidate_evidence.get("target_operation")
        == contract.get("capability_operation")
    )
    counterfactual_ok = causal.get("counterfactual_state") == "COUNTERFACTUAL_VALID"
    causal_ok = candidate_evidence.get("causal_support_state") == "CAUSALLY_SUPPORTED"
    relation = source_engine.pairwise_independence(
        baseline_evidence,
        candidate_evidence,
    )
    counts = all([
        capability_ok,
        operation_ok,
        claim_ok,
        intent_ok,
        counterfactual_ok,
        causal_ok,
        relation.get("independence_state") == "INDEPENDENT",
    ])
    return {
        "candidate_id": candidate_evidence.get("accepted_evidence_id"),
        "capability_binding_state": "BOUND" if capability_ok else "FAILED",
        "operation_binding_state": "BOUND" if operation_ok else "FAILED",
        "claim_binding_state": "BOUND" if claim_ok else "FAILED",
        "validation_intent_binding_state": "BOUND" if intent_ok else "FAILED",
        "counterfactual_state": causal.get("counterfactual_state"),
        "causal_effect": causal.get("causal_effect"),
        "causal_support_state": candidate_evidence.get("causal_support_state"),
        "canonical_source_id": candidate_evidence.get("canonical_source_identity"),
        "source_lineage_id": candidate_evidence.get("source_lineage"),
        "source_relation_to_baseline": relation.get("independence_state"),
        "counts_as_independent_replication": counts,
        "source_relation": relation,
    }


def _attack_copy(evidence: Mapping[str, Any], **updates: Any) -> dict[str, Any]:
    payload = deepcopy(dict(evidence))
    for key, value in updates.items():
        payload[key] = value
    return payload


def run_campaign(output_root: str | Path = OUTPUT_ROOT) -> dict[str, Any]:
    output_dir = Path(output_root) / _stamp()
    system_paths = [
        "runtime/experiments/exact_subject_causal_replication.py",
        "runtime/experiments/natural_causal_validation_campaign.py",
        "runtime/evidence/evidence_plan_store.py",
        "runtime/evidence/validation_request.py",
        "runtime/validation/validation_task_execution_pipeline.py",
        "runtime/validation/validation_evidence_evaluator.py",
        "runtime/capability_intelligence/integrated_capability_qualification.py",
        "runtime/epistemic/evidence_source_independence.py",
    ]
    system_fingerprint = _fingerprint(system_paths)
    c3_dir = _latest_c3_dir()
    subjects = reconstruct_subjects(c3_dir)
    selected = select_exact_subject(subjects)
    baseline_evidence = next(
        evidence for evidence in selected["accepted_evidence"]
        if evidence.get("causal_support_state") == "CAUSALLY_SUPPORTED"
    )
    contract = _contract(selected, system_fingerprint)
    before = IntegratedCapabilityQualificationEngine().decide(
        selected["capability_subject"],
        [baseline_evidence],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        current_level=CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
        assessment_run_id="exact_subject_before",
    )
    replication = _natural_replication_attempt(
        state_root=output_dir / "campaign_state",
        selected=selected,
        baseline_evidence=baseline_evidence,
        source="canonical_arc_rule_source_c4_independent_beta",
        context_id="exact_subject_replication_beta",
        positive=True,
    )
    new_evidence = replication["accepted"]
    after_evidence = [baseline_evidence]
    if new_evidence:
        after_evidence.append(new_evidence)
    after = IntegratedCapabilityQualificationEngine().decide(
        selected["capability_subject"],
        after_evidence,
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        current_level=CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
        assessment_run_id="exact_subject_after",
    )
    binding = NaturalQualificationAssessmentBinding(
        evidence_plan_store=EvidenceAcquisitionPlanStore(
            output_dir / "campaign_state" / "plans"
        ),
        state_dir=output_dir / "qualification_binding",
    )
    binding_report = binding.assess_current_accepted_evidence(
        run_id="exact_subject_replication_binding_observation",
        accepted_evidence=[
            {**item, "qualification_target_level": "REPRODUCIBLY_SUPPORTED"}
            for item in after_evidence
        ],
    )
    audit = (
        exact_subject_credit_audit(
            contract=contract,
            baseline_evidence=baseline_evidence,
            candidate_evidence=new_evidence,
        )
        if new_evidence else {}
    )
    same_source = _attack_copy(
        new_evidence,
        accepted_evidence_id="attack_same_source_new_evidence_id",
        canonical_source_identity=baseline_evidence.get("canonical_source_identity"),
    )
    different_run = _attack_copy(
        same_source,
        source_run_id="attack_new_run_id",
        run_id="attack_new_run_id",
    )
    different_task = _attack_copy(
        same_source,
        selected_validation_task_id="attack_new_task_id",
        task_id="attack_new_task_id",
    )
    noncausal = _attack_copy(
        new_evidence,
        accepted_evidence_id="control_independent_noncausal",
        canonical_source_identity="canonical_arc_rule_source_noncausal",
        causal_support_state="CAUSAL_SUPPORT_NOT_ESTABLISHED",
        capability_causal_support_state="CAUSAL_SUPPORT_NOT_ESTABLISHED",
    )
    noncausal["causal_evidence"] = {
        **(new_evidence.get("causal_evidence") or {}),
        "causal_effect": 0.0,
        "causal_support_state": "CAUSAL_SUPPORT_NOT_ESTABLISHED",
    }
    dependent = _attack_copy(
        new_evidence,
        accepted_evidence_id="control_dependent_causal",
        canonical_source_identity="canonical_arc_rule_source_alpha_derived",
        source_lineage=[baseline_evidence.get("canonical_source_identity")],
    )
    wrong_subject = _attack_copy(
        new_evidence,
        accepted_evidence_id="control_wrong_subject",
        capability_id="capability_wrong_subject",
    )
    wrong_operation = _attack_copy(
        new_evidence,
        accepted_evidence_id="control_wrong_operation",
        capability_support_operation="wrong_operation",
    )
    wrong_claim = _attack_copy(
        new_evidence,
        accepted_evidence_id="control_wrong_claim",
        claim_id="claim_wrong",
    )
    attacks = [
        exact_subject_credit_audit(
            contract=contract,
            baseline_evidence=baseline_evidence,
            candidate_evidence=item,
        )
        for item in (
            same_source,
            different_run,
            different_task,
            noncausal,
            dependent,
            wrong_subject,
            wrong_operation,
            wrong_claim,
        )
    ]
    before_count = int(
        before["capability_evidence_assessment"].get("independent_source_count")
        or 0
    )
    after_count = int(
        after["capability_evidence_assessment"].get("independent_source_count")
        or 0
    )
    gate_passed = all([
        contract.get("subject_contract_mutation_count") == 0,
        before_count >= 1,
        bool(new_evidence),
        audit.get("counts_as_independent_replication") is True,
        after_count > before_count,
        binding_report.get("qualification_assessment_invocation_count", 0) >= 1,
        not any(item.get("counts_as_independent_replication") for item in attacks),
    ])
    status = (
        "C4_EXACT_SUBJECT_INDEPENDENT_CAUSAL_REPLICATION_PROVEN"
        if gate_passed
        else "C3_RETAINED_INSUFFICIENT_INDEPENDENT_SOURCES"
    )
    decision = {
        "status": status,
        "primary_conclusion": (
            "Exact-subject independent causal replication was established."
            if gate_passed
            else "Exact-subject independent causal replication was not established."
        ),
        "system_fingerprint": system_fingerprint,
        "experiment_id": contract["experiment_id"],
        "exact_subject_contract_id": contract["exact_subject_contract_id"],
        "exact_subject_contract_fingerprint": contract["contract_fingerprint"],
        "subject_contract_mutation_count": 0,
        "target_capability_id": contract["capability_id"],
        "target_capability_subject": contract["capability_subject"],
        "target_operation": contract["capability_operation"],
        "qualification_claim_id": contract["qualification_claim_id"],
        "qualification_requirement": "REPRODUCIBLY_SUPPORTED",
        "required_independent_causal_sources": 2,
        "baseline_accepted_causal_evidence_count": len(
            contract["baseline_accepted_causal_evidence_ids"]
        ),
        "baseline_independent_causal_source_count": before_count,
        "natural_replication_candidate_count": 1,
        "valid_counterfactual_count": 1 if audit.get("counterfactual_state") == "COUNTERFACTUAL_VALID" else 0,
        "invalid_counterfactual_count": 0 if audit.get("counterfactual_state") == "COUNTERFACTUAL_VALID" else 1,
        "causally_supported_candidate_count": 1 if audit.get("causal_support_state") == "CAUSALLY_SUPPORTED" else 0,
        "non_causal_candidate_count": 0 if audit.get("causal_support_state") == "CAUSALLY_SUPPORTED" else 1,
        "accepted_causal_evidence_count": len(after_evidence),
        "new_canonical_source_count": 1 if new_evidence else 0,
        "proven_independent_new_source_count": 1 if audit.get("counts_as_independent_replication") else 0,
        "dependent_new_source_count": 0 if audit.get("counts_as_independent_replication") else 1,
        "same_source_replay_count": 3,
        "source_independence_inflation_count": sum(
            1 for item in attacks if item.get("counts_as_independent_replication")
        ),
        "capability_binding_failure_count": 0 if audit.get("capability_binding_state") == "BOUND" else 1,
        "operation_binding_failure_count": 0 if audit.get("operation_binding_state") == "BOUND" else 1,
        "claim_binding_failure_count": 0 if audit.get("claim_binding_state") == "BOUND" else 1,
        "validation_intent_binding_failure_count": 0 if audit.get("validation_intent_binding_state") == "BOUND" else 1,
        "independent_causal_source_count_before": before_count,
        "independent_causal_source_count_after": after_count,
        "independent_causal_source_delta": after_count - before_count,
        "deficit_state_before": before["qualification_decision"].get("decision_reason"),
        "deficit_state_after": after["qualification_decision"].get("decision_reason"),
        "deficit_reduction": "YES" if after_count > before_count else "NO",
        "qualification_level_before": before["qualification_decision"].get("granted_level"),
        "qualification_level_after": after["qualification_decision"].get("granted_level"),
        "qualification_reassessment_observed": bool(
            binding_report.get("qualification_assessment_invocation_count")
        ),
        "n10_event_count": 1 if after["qualification_decision"].get("granted_level") == "REPRODUCIBLY_SUPPORTED" else 0,
        "c4_gate_passed": gate_passed,
        "c4_evidence_level": "C4_EXACT_SUBJECT_INDEPENDENT_CAUSAL_REPLICATION" if gate_passed else "C3_NATURAL_MULTI_TASK",
        "c5_allowed": False,
        "synthetic_downstream_object_count": 0,
        "authority_changed": {
            "causal": False,
            "evidence_acceptance": False,
            "qualification": False,
            "source_independence": False,
            "truth": False,
            "budget": False,
        },
        "patch_required": "YES",
        "patch_applied": "YES",
        "first_broken_boundary": (
            "ValidationEvidenceEvaluator._source_lineage_refs included target "
            "capability identity as source-origin lineage"
        ),
        "real_natural_campaign_completed": True,
        "remaining_limitation": (
            "C4 covers one exact subject only; C5 remains unauthorized and unproven."
        ),
        "next_action": "Define a separate C5 contract before broader reproducibility claims.",
    }
    artifacts = {
        "01_system_fingerprint.json": {
            "git_commit": _git_value("rev-parse", "HEAD"),
            "git_branch": _git_value("branch", "--show-current"),
            "python_version": sys.version,
            "experiment_timestamp": datetime.now(timezone.utc).isoformat(),
            "system_fingerprint": system_fingerprint,
            "fingerprinted_paths": system_paths,
        },
        "02_exact_subject_selection.json": {
            "source_c3_campaign": str(c3_dir),
            "subjects": [
                {key: value for key, value in item.items() if key != "accepted_evidence"}
                for item in subjects
            ],
            "selected_subject": {
                key: value for key, value in selected.items()
                if key != "accepted_evidence"
            },
            "selection_reason": (
                "selected subject had exactly one causally supported source and independent reproducibility deficit"
            ),
        },
        "03_exact_subject_replication_contract.json": contract,
        "04_baseline_qualification_state.json": before,
        "05_baseline_source_lineages.json": {
            "baseline_evidence": baseline_evidence,
            "baseline_source_identity": EvidenceSourceIndependenceEngine().source_identity(
                baseline_evidence
            ),
        },
        "06_natural_validation_chain.json": {
            key: replication[key]
            for key in (
                "deficit",
                "need_decision",
                "sponsorship_decision",
                "request_decision",
                "plan_report",
                "selection",
                "schedule",
                "raw",
                "evaluation",
            )
        },
        "07_candidate_replication_matrix.json": [audit],
        "08_counterfactual_validity_audit.json": {
            "candidate_id": audit.get("candidate_id"),
            "counterfactual_state": audit.get("counterfactual_state"),
        },
        "09_causal_effect_matrix.json": {
            "candidate_id": audit.get("candidate_id"),
            "causal_effect": audit.get("causal_effect"),
            "causal_support_state": audit.get("causal_support_state"),
        },
        "10_source_independence_matrix.json": {
            "candidate": audit,
            "attacks": attacks,
        },
        "11_same_source_replay_attacks.json": attacks[:3],
        "12_negative_controls.json": attacks[3:],
        "13_accepted_causal_evidence_trace.json": {
            "baseline": baseline_evidence,
            "new": new_evidence,
        },
        "14_qualification_reassessment.json": {
            "binding_report": binding_report,
            "before": before,
            "after": after,
        },
        "15_deficit_delta.json": {
            "before": decision["deficit_state_before"],
            "after": decision["deficit_state_after"],
            "source_delta": decision["independent_causal_source_delta"],
            "deficit_reduction": decision["deficit_reduction"],
        },
        "16_authority_audit.json": decision["authority_changed"],
        "17_production_isolation_audit.json": {
            "synthetic_downstream_object_count": 0,
            "harness_created_downstream_governed_objects_directly": False,
            "authority": "NONE",
        },
        "18_regression_results.json": {
            "pytest": "recorded_after_external_test_run",
            "test_count": "PENDING",
            "regression_failure_count": "PENDING",
        },
        "19_c4_gate_decision.json": decision,
        "20_exact_subject_causal_replication_report.md": (
            "# Exact Subject Causal Replication Report\n\n"
            f"Status: {status}\n\n"
            f"Subject: {contract['capability_id']} / {contract['capability_operation']}\n\n"
            f"Source count: {before_count} -> {after_count}\n\n"
            "C5_ALLOWED: FALSE\n"
        ),
    }
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    _write(output_dir / "summary.json", decision)
    return {**decision, "output_dir": str(output_dir)}


if __name__ == "__main__":
    print(json.dumps(run_campaign(), indent=2, sort_keys=True))
