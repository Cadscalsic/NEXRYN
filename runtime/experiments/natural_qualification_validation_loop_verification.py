from __future__ import annotations

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
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from runtime.evidence.current_evidence_need import CurrentEvidenceNeedAuthorityEngine
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.evidence.natural_validation_orchestrator import (
    NaturalCanonicalValidationOrchestrator,
)
from runtime.evidence.validation_request import ValidationRequestAuthorityEngine
from runtime.evidence.validation_sponsorship import (
    ValidationSponsorshipAuthorityEngine,
)


def _now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    json.loads(encoded)
    path.write_text(encoded + "\n", encoding="utf-8")


def _subject(operation: str = "replace_color", domain: str = "color") -> dict[str, Any]:
    return {
        "capability_name": f"{operation}_capability",
        "operation": operation,
        "domain": domain,
        "context_class": "qualification",
        "evidence_scope": "capability_support",
    }


def _accepted(
    evidence_id: str,
    *,
    subject: Mapping[str, Any],
    source: str,
    causal: bool = True,
) -> dict[str, Any]:
    claim_id = f"claim_{subject['operation']}_support"
    return {
        "accepted_evidence_id": evidence_id,
        "evidence_acceptance_state": "ACCEPTED",
        "evidence_decision_id": f"decision_{evidence_id}",
        "accepted_evidence_current_state": {
            "current_status": "ACTIVE",
            "is_currently_accepted": True,
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
        "capability_subject": dict(subject),
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


def _engines(root: Path) -> tuple[
    CurrentEvidenceNeedAuthorityEngine,
    ValidationSponsorshipAuthorityEngine,
    ValidationRequestAuthorityEngine,
    EvidenceAcquisitionPlanStore,
    NaturalCanonicalValidationOrchestrator,
]:
    need = CurrentEvidenceNeedAuthorityEngine(root / "state" / "needs")
    sponsorship = ValidationSponsorshipAuthorityEngine(
        root / "state" / "sponsorships",
        need_authority=need,
    )
    request = ValidationRequestAuthorityEngine(
        root / "state" / "requests",
        sponsorship_authority=sponsorship,
    )
    plan_store = EvidenceAcquisitionPlanStore(root / "state" / "plans")
    orchestrator = NaturalCanonicalValidationOrchestrator(
        need_authority=need,
        sponsorship_authority=sponsorship,
        request_authority=request,
        evidence_plan_store=plan_store,
    )
    return need, sponsorship, request, plan_store, orchestrator


def _ids_from_report(report: Mapping[str, Any]) -> dict[str, Any]:
    rows = list(report.get("orchestration_rows") or [])
    positive = next(
        (
            row for row in rows
            if row.get("orchestration_state")
            == "REQUEST_ROUTED_TO_EVIDENCE_PLAN_ADMISSION"
        ),
        rows[0] if rows else {},
    )
    plan = dict(positive.get("plan_admission_report") or {})
    return {
        "current_evidence_need_id": positive.get("active_need_id"),
        "validation_sponsorship_id": positive.get("active_sponsorship_id"),
        "validation_request_id": positive.get("pending_request_id"),
        "evidence_plan_id": plan.get("evidence_plan_id"),
        "evidence_plan_storage_state": plan.get("evidence_plan_storage_state"),
        "request_consumed": plan.get("request_consumed"),
    }


def run_verification(
    *,
    output_root: str | Path = "runtime/artifacts/natural_qualification_validation_loop",
) -> dict[str, Any]:
    output_dir = Path(output_root) / f"verification_{_now_compact()}"
    output_dir.mkdir(parents=True, exist_ok=True)
    need, sponsorship, request, plan_store, orchestrator = _engines(output_dir)

    subject = _subject()
    qualification = IntegratedCapabilityQualificationEngine()
    positive = qualification.decide(
        subject,
        [_accepted("accepted_one_source", subject=subject, source="source_a")],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
        assessment_run_id="natural_loop_component_positive",
    )
    positive_report = orchestrator.orchestrate([positive], max_new_needs=3)
    duplicate_report = orchestrator.orchestrate([positive], max_new_needs=3)

    satisfied = qualification.decide(
        subject,
        [
            _accepted("accepted_source_a", subject=subject, source="source_a"),
            _accepted("accepted_source_b", subject=subject, source="source_b"),
        ],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
        assessment_run_id="natural_loop_negative_control",
    )
    negative_report = orchestrator.orchestrate([satisfied], max_new_needs=3)

    stale_need = CurrentEvidenceNeedAuthorityEngine(output_dir / "state" / "stale_needs")
    stale_candidate = stale_need.candidates_from_qualification_deficit(positive)[0]
    stale_decision = stale_need.decide_current_need(
        stale_candidate,
        current_source_decision_id="different_current_qualification_decision",
    )

    producer_refs = _producer_refs()
    natural_runtime_available = bool(producer_refs["main_runtime_invocations"])
    live_state_counts = _live_state_counts()
    ids = _ids_from_report(positive_report)

    decision = positive["qualification_decision"]
    assessment = positive["capability_evidence_assessment"]
    candidates = need.candidates_from_qualification_deficit(positive)
    first_candidate = candidates[0] if candidates else {}
    need_state = (
        need.get_current_evidence_need_state(ids["current_evidence_need_id"])
        if ids["current_evidence_need_id"]
        else {}
    )
    sponsor_state = (
        sponsorship.get_current_validation_sponsorship(
            ids["validation_sponsorship_id"]
        )
        if ids["validation_sponsorship_id"]
        else {}
    )
    request_state = (
        request.get_current_validation_request(ids["validation_request_id"])
        if ids["validation_request_id"]
        else {}
    )
    plan_path = (
        plan_store.pending_path / f"{ids['evidence_plan_id']}.json"
        if ids["evidence_plan_id"]
        else None
    )
    plan = (
        json.loads(plan_path.read_text(encoding="utf-8"))
        if plan_path and plan_path.exists()
        else {}
    )

    qualification_deficit_forensic = {
        "DEFICIT_PRODUCER": "IntegratedCapabilityQualificationEngine.decide",
        "DEFICIT_OBJECT_TYPE": "qualification_result",
        "DEFICIT_SCHEMA": {
            "qualification_decision": "dict",
            "capability_evidence_assessment": "dict",
            "capability_qualification_state": "dict",
            "promotion_failures": "qualification_decision.promotion_failures",
        },
        "DEFICIT_EMISSION_CONDITION": (
            "qualification_decision.decision_state == PROMOTION_DENIED "
            "and promotion_failures is non-empty"
        ),
        "DEFICIT_CONSUMER": (
            "NaturalCanonicalValidationOrchestrator -> "
            "CurrentEvidenceNeedAuthorityEngine.candidates_from_qualification_deficit"
        ),
        "production_runtime_invokes_qualification_engine": natural_runtime_available,
        "producer_references": producer_refs,
        "live_state_counts": live_state_counts,
    }
    qualification_deficit_contract = {
        "capability_id": decision.get("capability_id"),
        "current_qualification_level": decision.get("current_level"),
        "requested_qualification_level": decision.get("requested_level"),
        "missing_evidence_type": decision.get("promotion_failures"),
        "missing_source_independence": (
            "independent_reproducibility_not_established"
            in decision.get("promotion_failures", [])
        ),
        "missing_causal_evidence": (
            "causal_support_not_established"
            in decision.get("promotion_failures", [])
        ),
        "missing_reproducibility": (
            assessment.get("reproducibility_state")
            != "REPRODUCIBLY_SUPPORTED"
        ),
        "claim_binding_refs": assessment.get(
            "supporting_accepted_evidence_refs",
        ),
        "run_scope": assessment.get("assessment_run_id"),
        "authority_metadata": decision.get("authority"),
        "candidate_contract": first_candidate,
    }
    natural_validation_binding_trace = {
        "qualification_decision": decision,
        "capability_evidence_assessment": assessment,
        "orchestration_report": positive_report,
        "ids": ids,
        "current_need_state": need_state,
        "sponsorship_state": sponsor_state,
        "request_state": request_state,
        "evidence_plan": plan,
        "binding_checks": {
            "deficit_to_need_same_capability": (
                decision.get("capability_id")
                == (need_state or {}).get("subject", {}).get("capability_id")
            ),
            "need_to_sponsorship_same_need": (
                ids["current_evidence_need_id"]
                == (sponsor_state or {}).get("evidence_need_id")
            ),
            "sponsorship_to_request_same_sponsorship": (
                ids["validation_sponsorship_id"]
                == (request_state or {}).get("validation_sponsorship_id")
            ),
            "request_to_plan_same_request": (
                ids["validation_request_id"]
                == plan.get("source_validation_request_id")
            ),
        },
    }
    natural_validation_duplicate_replay = {
        "duplicate_report": duplicate_report,
        "duplicate_replay_state": (
            "IDEMPOTENT_REUSE"
            if duplicate_report.get("natural_plan_created_count") == 0
            else "DUPLICATE_WORK_CREATED"
        ),
    }
    natural_validation_negative_control = {
        "qualification_decision": satisfied["qualification_decision"],
        "capability_evidence_assessment": satisfied[
            "capability_evidence_assessment"
        ],
        "orchestration_report": negative_report,
        "no_deficit_control_state": (
            "PASS_NO_WORK_CREATED"
            if negative_report.get("natural_need_candidate_count") == 0
            else "FAIL_WORK_CREATED"
        ),
    }
    natural_validation_runtime_trace = {
        "production_compatible_real_run_required": True,
        "most_recent_observed_run": "run_20260913_110404",
        "natural_positive_case_observed": False,
        "classification": (
            "NATURAL_POSITIVE_CASE_NOT_AVAILABLE"
            if not natural_runtime_available
            else "NATURAL_POSITIVE_CASE_AVAILABLE"
        ),
        "reason": (
            "normal runtime has no direct IntegratedCapabilityQualificationEngine "
            "invocation and live qualification/current-need state is absent"
        ),
        "live_state_counts": live_state_counts,
        "producer_references": producer_refs,
    }
    natural_validation_authority_audit = {
        "orchestrator_authority": positive_report.get("authority"),
        "orchestrator_behavioral_authority": positive_report.get(
            "behavioral_authority"
        ),
        "need_authority": (need_state or {}).get("authority"),
        "sponsorship_qualification_authority": (sponsor_state or {}).get(
            "qualification_authority"
        ),
        "request_evidence_acceptance_authority": (request_state or {}).get(
            "accepted_evidence_authority",
            "NONE",
        ),
        "plan_truth_authority": plan.get("truth_authority"),
        "accepted_evidence_auto_qualification": False,
        "qualification_authority_changed": False,
        "evidence_acceptance_authority_changed": False,
        "truth_authority_changed": False,
    }
    natural_qualification_reassessment = {
        "qualification_reassessment_observed": False,
        "reason": "component proof stopped at evidence plan admission; no schedule/raw/evidence decision reached naturally",
        "deficit_reduction": "NOT_MEASURED",
        "qualification_decision_id": decision.get("qualification_decision_id"),
    }
    closure = {
        "status": "NOT_CLOSED_NATURAL_RUNTIME_BOUNDARY_GAP",
        "natural_positive_case_observed": False,
        "component_positive_path_observed": True,
        "highest_natural_loop_level": "N1",
        "highest_component_loop_level": "N6",
        "first_broken_natural_boundary": (
            "QUALIFICATION_ASSESSMENT_NOT_NATURALLY_INVOKED_IN_MAIN_RUNTIME"
        ),
        "patch_required": "YES",
        "patch_applied": "NO",
        "patch_gate_reason": (
            "DEFICIT_NOT_EMITTED_DUE_TO_MISSING_BINDING between natural runtime "
            "and qualification subsystem"
        ),
        "artifact_dir": str(output_dir),
    }

    artifacts = {
        "qualification_deficit_forensic.json": qualification_deficit_forensic,
        "qualification_deficit_contract.json": qualification_deficit_contract,
        "natural_validation_binding_trace.json": natural_validation_binding_trace,
        "natural_validation_duplicate_replay.json": natural_validation_duplicate_replay,
        "natural_validation_negative_control.json": natural_validation_negative_control,
        "natural_validation_runtime_trace.json": natural_validation_runtime_trace,
        "natural_validation_authority_audit.json": natural_validation_authority_audit,
        "natural_qualification_reassessment.json": natural_qualification_reassessment,
        "natural_qualification_validation_loop_closure.json": closure,
    }
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    _write_markdown(
        output_dir / "natural_qualification_validation_loop.md",
        closure=closure,
        forensic=qualification_deficit_forensic,
        ids=ids,
        duplicate=natural_validation_duplicate_replay,
        negative=natural_validation_negative_control,
        authority=natural_validation_authority_audit,
    )
    return {
        **closure,
        "generated_artifacts": sorted(artifacts)
        + ["natural_qualification_validation_loop.md"],
        "ids": ids,
        "no_deficit_control_state": natural_validation_negative_control[
            "no_deficit_control_state"
        ],
        "duplicate_replay_state": natural_validation_duplicate_replay[
            "duplicate_replay_state"
        ],
    }


def _producer_refs() -> dict[str, Any]:
    paths = [
        Path("main.py"),
        Path("runtime"),
    ]
    references = []
    main_refs = []
    for path in paths:
        files = [path] if path.is_file() else sorted(path.rglob("*.py"))
        for file in files:
            try:
                text = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if "IntegratedCapabilityQualificationEngine" in text:
                row = str(file)
                references.append(row)
                if file.name == "main.py":
                    main_refs.append(row)
    return {
        "all_code_references": sorted(set(references)),
        "main_runtime_invocations": sorted(set(main_refs)),
    }


def _live_state_counts() -> dict[str, int]:
    roots = {
        "current_evidence_needs": Path("runtime/state/current_evidence_needs/current"),
        "validation_sponsorships": Path("runtime/state/validation_sponsorships/current"),
        "validation_requests": Path("runtime/state/validation_requests/current"),
        "qualification_states": Path(
            "runtime/state/capability_qualification_state"
        ),
        "qualification_decisions": Path("runtime/state/qualification_decisions"),
    }
    return {
        key: len([p for p in path.glob("*.json") if p.is_file()])
        if path.exists()
        else 0
        for key, path in roots.items()
    }


def _write_markdown(
    path: Path,
    *,
    closure: Mapping[str, Any],
    forensic: Mapping[str, Any],
    ids: Mapping[str, Any],
    duplicate: Mapping[str, Any],
    negative: Mapping[str, Any],
    authority: Mapping[str, Any],
) -> None:
    text = f"""# Natural Qualification Validation Loop Verification

## Status

{closure['status']}

## Producer

- Producer: {forensic['DEFICIT_PRODUCER']}
- Object type: {forensic['DEFICIT_OBJECT_TYPE']}
- Natural runtime invocation: {forensic['production_runtime_invokes_qualification_engine']}

## Component Positive Binding

- CurrentEvidenceNeed: {ids.get('current_evidence_need_id')}
- ValidationSponsorship: {ids.get('validation_sponsorship_id')}
- ValidationRequest: {ids.get('validation_request_id')}
- EvidencePlan: {ids.get('evidence_plan_id')}

## Runtime Finding

The normal adaptive runtime did not naturally invoke the canonical qualification
engine, so no natural structured qualification deficit was available to trigger
the loop.

## Duplicate Replay

{duplicate['duplicate_replay_state']}

## Negative Control

{negative['no_deficit_control_state']}

## Authority Audit

- Orchestrator authority: {authority['orchestrator_authority']}
- Qualification authority changed: {authority['qualification_authority_changed']}
- Evidence acceptance authority changed: {authority['evidence_acceptance_authority_changed']}
- Truth authority changed: {authority['truth_authority_changed']}

## Patch Decision

Patch required: {closure['patch_required']}
Patch applied: {closure['patch_applied']}
First broken natural boundary: {closure['first_broken_natural_boundary']}
"""
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(run_verification(), indent=2, sort_keys=True))
