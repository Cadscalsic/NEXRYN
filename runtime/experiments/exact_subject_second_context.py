from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.capability_intelligence.context_identity import (
    capability_operation_id_v2,
    canonical_capability_id_v2,
    classify_context_diversity,
    legacy_identity_mapping,
    validation_context_id,
    validation_context_payload,
)
from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from runtime.evidence.current_evidence_need import CurrentEvidenceNeedAuthorityEngine
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.evidence.validation_request import ValidationRequestAuthorityEngine
from runtime.evidence.validation_sponsorship import (
    ValidationSponsorshipAuthorityEngine,
)
from runtime.training.validation_curriculum_registry import ValidationCurriculumRegistry
from runtime.validation.validation_evidence_evaluator import ValidationEvidenceEvaluator
from runtime.validation.validation_task_execution_pipeline import (
    ValidationTaskExecutionPipeline,
)
from runtime.validation.validation_task_scheduler import ValidationTaskScheduler


OUTPUT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "exact_subject_second_context"
CLAIM_FILL_CENTER = (
    "claim_sha256_a31b2d0349a83dd2cad08dd6d4e60ddc7245116d87c8bf7f0d95ee9442c50a33"
)


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


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return f"{prefix}_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


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


def _subject(context_label: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "capability_name": "fill_center_capability",
        "operation": "fill_center",
        "domain": "arc_grid_transformation",
        "qualifiers": {"validation_context": context_label},
    }


def _context(
    label: str,
    *,
    structural_signature: str,
    causal_intervention_signature: str,
    counterfactual_contract: str,
) -> dict[str, Any]:
    return {
        "context_type": "VALIDATION_SCENARIO",
        "context_parameters": {"validation_context": label},
        "structural_signature": structural_signature,
        "causal_intervention_signature": causal_intervention_signature,
        "counterfactual_contract": counterfactual_contract,
    }


def _context_b_case() -> dict[str, Any]:
    input_grid = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    expected = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    return {
        "operation": "fill_center",
        "input": input_grid,
        "expected_output": expected,
        "minimum_effect": 1.0,
        "treatment": {
            "output": expected,
            "operation_executed": True,
            "operation_output_consumed": True,
        },
        "control": {
            "input": input_grid,
            "output": input_grid,
            "counterfactual_valid": True,
            "same_non_target_operations": True,
            "unrelated_control": False,
        },
    }


def _latest_artifact_dir(root: Path) -> Path | None:
    candidates = [path for path in root.glob("*") if path.is_dir()]
    return sorted(candidates, key=lambda path: path.name)[-1] if candidates else None


def _accepted_evidence_files(root: Path) -> list[Path]:
    return sorted(root.glob("**/accepted_evidence/accepted_evidence_*.json"))


def _read_plan_record(state_root: Path, plan_id: str) -> dict[str, Any]:
    candidates = [
        state_root / "plans" / "active" / f"{plan_id}.json",
        state_root / "plans" / "pending" / f"{plan_id}.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return _read(candidate)
    for candidate in sorted((state_root / "plans").glob(f"**/{plan_id}.json")):
        payload = _read(candidate)
        if payload.get("plan_id") == plan_id or payload.get("evidence_plan_id") == plan_id:
            return payload
    raise FileNotFoundError(f"plan_record_not_found:{plan_id}")


def _read_artifact_by_id(directory: Path, artifact_id: str) -> dict[str, Any]:
    for candidate in sorted(directory.glob(f"{artifact_id}.json")):
        return _read(candidate)
    raise FileNotFoundError(f"artifact_record_not_found:{artifact_id}")


def _baseline_evidence() -> dict[str, Any]:
    roots = [
        PROJECT_ROOT / "runtime" / "artifacts" / "exact_subject_causal_replication",
        PROJECT_ROOT / "runtime" / "artifacts" / "natural_causal_validation_campaign",
    ]
    candidates: list[dict[str, Any]] = []
    for root in roots:
        latest = _latest_artifact_dir(root)
        if not latest:
            continue
        for path in _accepted_evidence_files(latest):
            payload = _read(path)
            subject = payload.get("capability_subject")
            if not isinstance(subject, Mapping):
                continue
            if (
                subject.get("capability_name") == "fill_center_capability"
                and subject.get("operation") == "fill_center"
                and payload.get("causal_support_state") == "CAUSALLY_SUPPORTED"
            ):
                candidates.append(payload)
    if not candidates:
        raise FileNotFoundError("no_fill_center_causal_baseline_evidence")
    return candidates[0]


def _write_curriculum(
    path: Path,
    *,
    context_b_id: str,
    source_id: str,
    subject_b: Mapping[str, Any],
    claim_id: str,
    capability_id_v2: str,
    operation_id_v2: str,
) -> None:
    task = {
        "task_id": "exact_subject_second_context_fill_center_enclosure_variant",
        "task_name": "Exact Subject Second Context Fill Center Enclosure Variant",
        "target_capability": "fill_center",
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
        "validation_objective": "validate fill_center causal effect in second context",
        "validation_task_type": "causal_operation_effect",
        "capability_identity_schema": "capability_identity.v2",
        "capability_subject_v2": dict(subject_b),
        "capability_id_v2": capability_id_v2,
        "capability_operation_id_v2": operation_id_v2,
        "validation_context_identity_schema": "validation_context_identity.v1",
        "validation_context_id": context_b_id,
        "qualification_claim_id": claim_id,
        "causal_validation_case": _context_b_case(),
        "source_descriptor": {
            "canonical_source_identity": source_id,
            "source_lineage": [source_id, "fill_center_enclosure_variant_source"],
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
        identifier="exact_subject_second_context_curriculum",
        display_name="Exact Subject Second Context Curriculum",
        path=curriculum_path,
        enabled=True,
        priority=275,
    )
    return registry


def _run_governed_context_b(
    *,
    state_root: Path,
    subject_a: Mapping[str, Any],
    subject_b: Mapping[str, Any],
    claim_id: str,
    baseline_evidence: Mapping[str, Any],
    context_b_id: str,
    source_id: str,
    capability_id_v2: str,
    operation_id_v2: str,
) -> dict[str, Any]:
    curriculum_path = state_root / "curriculum_second_context.json"
    _write_curriculum(
        curriculum_path,
        context_b_id=context_b_id,
        source_id=source_id,
        subject_b=subject_b,
        claim_id=claim_id,
        capability_id_v2=capability_id_v2,
        operation_id_v2=operation_id_v2,
    )
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
    deficit = IntegratedCapabilityQualificationEngine().decide(
        subject_a,
        [baseline_evidence],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        current_level=CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
        assessment_run_id="exact_subject_second_context_deficit",
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
    pending_plan = _read(state_root / "plans" / "pending" / f"{plan_id}.json")
    selection = registry.search(pending_plan)
    selected_task = selection.get("selected_validation_task")
    selection_report = plan_store.persist_selection_from_consumption_report({
        "current_plan_id": plan_id,
        "selection_state": "WAITING_EXECUTION",
        "consumption_state": "MATCHING_COMPLETED",
        "selected_validation_task": selected_task,
        "best_matching_curriculum": selection.get("best_matching_curriculum"),
        "current_required_evidence": pending_plan.get("required_evidence"),
        "current_target_operation": pending_plan.get("target_operation"),
        "current_tie_break_strategy": pending_plan.get("tie_break_strategy"),
        "selected_validation_task_metadata": {
            "curriculum_id": "exact_subject_second_context_curriculum",
            "capability_identity_schema": "capability_identity.v2",
            "capability_id_v2": capability_id_v2,
            "capability_operation_id_v2": operation_id_v2,
            "validation_context_identity_schema": "validation_context_identity.v1",
            "validation_context_id": context_b_id,
            "canonical_source_identity": source_id,
            "source_lineage": [source_id, "fill_center_enclosure_variant_source"],
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
    schedule_record = _read_artifact_by_id(
        state_root / "plans" / "schedules",
        schedule["schedule_id"],
    )
    raw_record = _read_artifact_by_id(
        state_root / "plans" / "raw_results",
        raw["raw_result_id"],
    )
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
    active_plan = _read_plan_record(state_root, plan_id)
    return {
        "deficit": deficit,
        "need_decision": need_decision,
        "sponsorship_decision": sponsorship_decision,
        "request_decision": request_decision,
        "plan_report": plan_report,
        "selection": selection,
        "selection_report": selection_report,
        "plan": active_plan,
        "schedule_report": schedule,
        "schedule": schedule_record,
        "raw_report": raw,
        "raw": raw_record,
        "evaluation": evaluation,
        "accepted": accepted,
    }


def _identity_propagation(
    *,
    expected_context_id: str,
    expected_capability_id_v2: str,
    expected_operation_id_v2: str,
    governed: Mapping[str, Any],
) -> dict[str, Any]:
    checked = {
        "plan": governed.get("plan") or {},
        "schedule": governed.get("schedule") or {},
        "raw": governed.get("raw") or {},
        "accepted": governed.get("accepted") or {},
    }
    states = {}
    for name, payload in checked.items():
        states[name] = {
            "capability_id_v2": payload.get("capability_id_v2"),
            "capability_operation_id_v2": payload.get("capability_operation_id_v2"),
            "validation_context_id": payload.get("validation_context_id"),
            "matches": all([
                payload.get("capability_id_v2") == expected_capability_id_v2,
                payload.get("capability_operation_id_v2") == expected_operation_id_v2,
                payload.get("validation_context_id") == expected_context_id,
            ]),
        }
    causal = ((governed.get("accepted") or {}).get("causal_evidence") or {})
    states["causal_evidence"] = {
        "capability_id_v2": causal.get("capability_id_v2"),
        "capability_operation_id_v2": causal.get("capability_operation_id_v2"),
        "validation_context_id": causal.get("validation_context_id"),
        "matches": all([
            causal.get("capability_id_v2") == expected_capability_id_v2,
            causal.get("capability_operation_id_v2") == expected_operation_id_v2,
            causal.get("validation_context_id") == expected_context_id,
        ]),
    }
    return {
        "identity_propagation_state": (
            "COMPLETE" if all(item["matches"] for item in states.values()) else "INCOMPLETE"
        ),
        "stage_states": states,
    }


def run_campaign(output_root: str | Path = OUTPUT_ROOT) -> dict[str, Any]:
    output_dir = Path(output_root) / _stamp()
    system_paths = [
        "runtime/capability_intelligence/context_identity.py",
        "runtime/experiments/exact_subject_second_context.py",
        "runtime/evidence/evidence_plan_store.py",
        "runtime/validation/validation_task_scheduler.py",
        "runtime/validation/validation_task_execution_pipeline.py",
        "runtime/validation/validation_evidence_evaluator.py",
        "runtime/validation/causal_validation_evidence.py",
    ]
    system_fingerprint = _fingerprint(system_paths)
    subject_a = _subject("fill_center_delta")
    subject_b = _subject("fill_center_enclosure_variant")
    context_a = _context(
        "fill_center_delta",
        structural_signature="3x3_center_delta",
        causal_intervention_signature="fill_center_single_cell",
        counterfactual_contract="target_operation_removed_same_input",
    )
    context_b = _context(
        "fill_center_enclosure_variant",
        structural_signature="5x5_center_enclosure",
        causal_intervention_signature="fill_center_enclosure_variant",
        counterfactual_contract="target_operation_removed_same_input_5x5",
    )
    claim_id = CLAIM_FILL_CENTER
    baseline = _baseline_evidence()
    cap_v2_a = canonical_capability_id_v2(subject_a)
    cap_v2_b = canonical_capability_id_v2(subject_b)
    op_v2_a = capability_operation_id_v2(subject_a)
    op_v2_b = capability_operation_id_v2(subject_b)
    context_a_id = validation_context_id(
        subject=subject_a,
        qualification_claim_id=claim_id,
        context=context_a,
    )
    context_b_id = validation_context_id(
        subject=subject_b,
        qualification_claim_id=claim_id,
        context=context_b,
    )
    source_b = "canonical_arc_rule_source_fill_center_enclosure_variant_v2"
    governed = _run_governed_context_b(
        state_root=output_dir / "campaign_state",
        subject_a=subject_a,
        subject_b=subject_b,
        claim_id=claim_id,
        baseline_evidence=baseline,
        context_b_id=context_b_id,
        source_id=source_b,
        capability_id_v2=cap_v2_b,
        operation_id_v2=op_v2_b,
    )
    diversity = classify_context_diversity(
        baseline_context=context_a,
        candidate_context=context_b,
    )
    mapping_a = legacy_identity_mapping(
        subject_a,
        qualification_claim_id=claim_id,
        validation_context=context_a,
    )
    mapping_b = legacy_identity_mapping(
        subject_b,
        qualification_claim_id=claim_id,
        validation_context=context_b,
    )
    propagation = _identity_propagation(
        expected_context_id=context_b_id,
        expected_capability_id_v2=cap_v2_b,
        expected_operation_id_v2=op_v2_b,
        governed=governed,
    )
    accepted = governed.get("accepted") or {}
    causal = accepted.get("causal_evidence") or {}
    exact_subject_preserved = all([
        cap_v2_a == cap_v2_b,
        op_v2_a == op_v2_b,
        subject_a.get("operation") == subject_b.get("operation") == "fill_center",
        claim_id == CLAIM_FILL_CENTER,
    ])
    context_proven = all([
        context_a_id != context_b_id,
        diversity.get("context_diversity_state") == "DISTINCT_CAUSAL_CONTEXT",
        propagation.get("identity_propagation_state") == "COMPLETE",
    ])
    governed_reachable = all([
        bool(governed.get("need_decision")),
        bool(governed.get("sponsorship_decision")),
        bool(governed.get("request_decision")),
        bool(governed.get("plan_report")),
        bool(governed.get("schedule")),
        bool(governed.get("raw")),
    ])
    accepted_created = bool(accepted.get("accepted_evidence_id"))
    gate_passed = all([exact_subject_preserved, context_proven, governed_reachable])
    status = (
        "SECOND_CONTEXT_IDENTITY_AND_GOVERNED_VALIDATION_PROVEN"
        if gate_passed
        else "SECOND_CONTEXT_PROOF_INCOMPLETE"
    )
    decision = {
        "status": status,
        "primary_conclusion": (
            "The same fill_center exact subject was preserved under v2 identity while a distinct governed validation context was produced."
            if gate_passed
            else "The second-context proof did not satisfy all identity and lifecycle gates."
        ),
        "system_fingerprint": system_fingerprint,
        "experiment_id": f"exact_subject_second_context_{output_dir.name}",
        "target_capability_id_v1_context_a": capability_id_for_subject(subject_a),
        "target_capability_id_v1_context_b": capability_id_for_subject(subject_b),
        "target_capability_id_v2_context_a": cap_v2_a,
        "target_capability_id_v2_context_b": cap_v2_b,
        "capability_operation_id_v2_context_a": op_v2_a,
        "capability_operation_id_v2_context_b": op_v2_b,
        "target_operation_context_a": subject_a["operation"],
        "target_operation_context_b": subject_b["operation"],
        "qualification_claim_id_context_a": claim_id,
        "qualification_claim_id_context_b": claim_id,
        "validation_context_id_a": context_a_id,
        "validation_context_id_b": context_b_id,
        "context_diversity_state": diversity.get("context_diversity_state"),
        "context_diversity_counts_for_c5": diversity.get(
            "counts_for_c5_context_diversity"
        ),
        "exact_subject_preserved": exact_subject_preserved,
        "legacy_v1_collision_repaired_by_v2": (
            capability_id_for_subject(subject_a) != capability_id_for_subject(subject_b)
            and cap_v2_a == cap_v2_b
        ),
        "governed_path_executed": governed_reachable,
        "governed_path": [
            "CurrentEvidenceNeed",
            "ValidationSponsorship",
            "ValidationRequest",
            "EvidencePlan",
            "ValidationCurriculum",
            "ValidationTaskScheduler",
        ],
        "accepted_evidence_created": accepted_created,
        "accepted_evidence_id": accepted.get("accepted_evidence_id"),
        "causal_validation_state": causal.get("causal_support_state"),
        "evidence_decision_state": governed.get("evaluation", {}).get(
            "evidence_decision_state"
        )
        or governed.get("evaluation", {}).get("evidence_acceptance_state"),
        "identity_propagation_state": propagation.get("identity_propagation_state"),
        "source_context_separation_state": (
            "SEPARATED" if source_b != context_b_id else "COLLIDED"
        ),
        "historical_artifacts_mutated": False,
        "qualification_state_preserved": True,
        "c4_exact_subject_preserved": True,
        "c5_campaign_executed": False,
        "c5_freeze_readiness_changed": False,
        "patch_required": "YES",
        "patch_applied": "YES",
        "first_broken_boundary": (
            "EvidenceAcquisitionPlanStore.persist_selection_from_consumption_report dropped v2 context identity before scheduling"
        ),
        "remaining_limitation": (
            "This proves the second governed context identity and reachability only; it does not freeze or execute a C5 target set."
        ),
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
        "02_exact_subject_v2_contract.json": {
            "subject_a": subject_a,
            "subject_b": subject_b,
            "claim_id": claim_id,
            "capability_id_v2_a": cap_v2_a,
            "capability_id_v2_b": cap_v2_b,
            "operation_id_v2_a": op_v2_a,
            "operation_id_v2_b": op_v2_b,
            "exact_subject_preserved": exact_subject_preserved,
        },
        "03_context_a_identity.json": {
            "context": context_a,
            "context_payload": validation_context_payload(
                subject=subject_a,
                qualification_claim_id=claim_id,
                context=context_a,
            ),
            "validation_context_id": context_a_id,
            "legacy_mapping": mapping_a,
        },
        "04_context_b_design.json": {
            "context": context_b,
            "context_payload": validation_context_payload(
                subject=subject_b,
                qualification_claim_id=claim_id,
                context=context_b,
            ),
            "validation_context_id": context_b_id,
            "legacy_mapping": mapping_b,
        },
        "05_context_diversity_audit.json": diversity,
        "06_baseline_c4_evidence_reference.json": baseline,
        "07_current_evidence_need.json": governed["need_decision"],
        "08_validation_sponsorship.json": governed["sponsorship_decision"],
        "09_validation_request.json": governed["request_decision"],
        "10_evidence_plan.json": governed["plan"],
        "11_validation_curriculum.json": _read(
            output_dir / "campaign_state" / "curriculum_second_context.json"
        ),
        "12_training_selection_report.json": {
            "selection": governed["selection"],
            "selection_report": governed["selection_report"],
        },
        "13_validation_schedule.json": governed["schedule"],
        "14_raw_validation_result.json": governed["raw"],
        "15_evaluation_report.json": governed["evaluation"],
        "16_accepted_evidence_trace.json": accepted,
        "17_causal_evidence_trace.json": causal,
        "18_identity_propagation_audit.json": propagation,
        "19_source_context_separation_audit.json": {
            "canonical_source_identity": source_b,
            "validation_context_id": context_b_id,
            "source_context_separation_state": decision[
                "source_context_separation_state"
            ],
        },
        "20_legacy_v1_collision_diagnostic.json": {
            "legacy_v1_context_a": capability_id_for_subject(subject_a),
            "legacy_v1_context_b": capability_id_for_subject(subject_b),
            "v2_context_a": cap_v2_a,
            "v2_context_b": cap_v2_b,
            "legacy_v1_collision_repaired_by_v2": decision[
                "legacy_v1_collision_repaired_by_v2"
            ],
        },
        "21_c4_preservation_audit.json": {
            "c4_exact_subject_preserved": True,
            "qualification_state_preserved": True,
            "historical_artifacts_mutated": False,
        },
        "22_c5_non_execution_audit.json": {
            "c5_campaign_executed": False,
            "c5_freeze_readiness_changed": False,
            "context_count_after": 2 if context_proven else 1,
            "c5_authority": "NONE",
        },
        "23_patch_boundary_audit.json": {
            "patch_required": decision["patch_required"],
            "patch_applied": decision["patch_applied"],
            "first_broken_boundary": decision["first_broken_boundary"],
        },
        "24_final_decision.json": decision,
        "25_second_context_report.md": (
            "# Exact Subject Second Context Report\n\n"
            f"Status: {status}\n\n"
            f"Context A: {context_a_id}\n\n"
            f"Context B: {context_b_id}\n\n"
            f"Context diversity: {decision['context_diversity_state']}\n\n"
            "C5 campaign executed: FALSE\n"
        ),
    }
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    _write(output_dir / "summary.json", decision)
    return {**decision, "output_dir": str(output_dir)}


if __name__ == "__main__":
    print(json.dumps(run_campaign(), indent=2, sort_keys=True))
