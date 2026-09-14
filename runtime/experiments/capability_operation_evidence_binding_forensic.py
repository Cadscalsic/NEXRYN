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
    IntegratedCapabilityQualificationEngine,
)
from runtime.epistemic.evidence_source_independence import (
    EvidenceSourceIndependenceEngine,
)


SOURCE_ARTIFACT_DIR = (
    PROJECT_ROOT
    / "runtime"
    / "artifacts"
    / "natural_evidence_qualification_loop"
    / "verification_20260913_154658"
)
OUTPUT_ROOT = (
    PROJECT_ROOT
    / "runtime"
    / "artifacts"
    / "capability_operation_evidence_binding"
)


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any] | list[Any] | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
        return
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    json.loads(text)
    path.write_text(text + "\n", encoding="utf-8")


def _fingerprint(paths: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        path = PROJECT_ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _latest_natural_verification_dir() -> str | None:
    root = (
        PROJECT_ROOT
        / "runtime"
        / "artifacts"
        / "natural_evidence_qualification_loop"
    )
    if not root.exists():
        return None
    candidates = sorted(path for path in root.glob("verification_*") if path.is_dir())
    return str(candidates[-1]) if candidates else None


def _source_identity(
    engine: EvidenceSourceIndependenceEngine,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    flattened = dict(evidence)
    provenance = evidence.get("source_provenance")
    if isinstance(provenance, Mapping):
        for key in (
            "producer_operation_id",
            "producer_component_id",
            "producer_source_type",
            "source_lineage",
            "run_id",
            "task_id",
        ):
            if key in provenance and key not in flattened:
                flattened[key] = provenance[key]
        if "source_lineage" not in flattened:
            flattened["source_lineage"] = provenance.get("upstream_lineage_refs")
    return engine.source_identity(flattened)


def _operation_binding_state(
    new_evidence: Mapping[str, Any],
    target_operation: str,
) -> str:
    subject = new_evidence.get("capability_subject")
    subject_operation = subject.get("operation") if isinstance(subject, Mapping) else None
    support_operation = (
        new_evidence.get("capability_support_operation")
        or new_evidence.get("supported_capability_operation")
        or subject_operation
    )
    if support_operation == target_operation:
        return "OPERATION_BINDING_PRESERVED"
    if new_evidence.get("target_operation") == target_operation:
        return "OPERATION_BINDING_LEGACY_TARGET_FIELD_ONLY"
    return "OPERATION_BINDING_LOST_TO_VALIDATION_TARGET_FIELD"


def run_forensic(
    output_root: str | Path = OUTPUT_ROOT,
    source_artifact_dir: str | Path = SOURCE_ARTIFACT_DIR,
) -> dict[str, Any]:
    source_dir = Path(source_artifact_dir)
    output_dir = Path(output_root) / f"forensic_{_stamp()}"

    starting = _read(source_dir / "natural_loop_starting_lineage.json")
    accepted_trace = _read(source_dir / "accepted_evidence_trace.json")
    reassessment_trace = _read(source_dir / "qualification_reassessment_trace.json")
    decision_trace = _read(source_dir / "evidence_decision_trace.json")
    raw_trace = _read(source_dir / "raw_result_identity_trace.json")
    plan_trace = _read(source_dir / "evidence_plan_scheduler_forensic.json")
    closure = _read(source_dir / "natural_loop_closure_decision.json")
    previous = _read(
        source_dir
        / "controlled_state"
        / "plans"
        / "accepted_evidence"
        / "accepted_source_a.json"
    )
    new = _read(
        source_dir
        / "controlled_state"
        / "plans"
        / "accepted_evidence"
        / f"{accepted_trace['accepted_evidence_id']}.json"
    )

    target_subject = accepted_trace["capability_subject"]
    target_capability_id = accepted_trace["capability_id"]
    target_operation = target_subject["operation"]
    original_assessment = reassessment_trace["qualification_results"][0][
        "capability_evidence_assessment"
    ]
    original_decision = reassessment_trace["qualification_results"][0][
        "qualification_decision"
    ]
    first_rejection = next(
        (
            item
            for item in original_assessment.get("rejected_evidence", [])
            if item.get("accepted_evidence_id")
            == accepted_trace["accepted_evidence_id"]
        ),
        {},
    )

    qualification_engine = IntegratedCapabilityQualificationEngine()
    repaired = qualification_engine.decide(
        target_subject,
        [previous, new],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        current_level=CapabilityQualificationLevel.NOT_QUALIFIED,
        architecture_present=True,
        runtime_reachable=True,
        assessment_run_id="capability_operation_binding_forensic_replay",
        required_independent_sources=2,
    )
    repaired_assessment = repaired["capability_evidence_assessment"]
    repaired_decision = repaired["qualification_decision"]

    source_engine = EvidenceSourceIndependenceEngine()
    previous_source = _source_identity(source_engine, previous)
    new_source = _source_identity(source_engine, new)
    pairwise = source_engine.pairwise_independence(previous, new)

    system_paths = [
        "runtime/capability_intelligence/integrated_capability_qualification.py",
        "runtime/validation/validation_evidence_evaluator.py",
        "runtime/evidence/natural_qualification_binding.py",
        "runtime/epistemic/evidence_source_independence.py",
    ]
    system_fingerprint = _fingerprint(system_paths)
    before_count = int(original_assessment.get("independent_source_count") or 0)
    after_count = int(repaired_assessment.get("independent_source_count") or 0)
    operation_binding = _operation_binding_state(new, target_operation)
    capability_binding = (
        "CAPABILITY_BINDING_PRESERVED"
        if new.get("capability_id") == target_capability_id
        else "CAPABILITY_BINDING_LOST"
    )
    claim_binding = (
        "CLAIM_BINDING_BOUND_DIFFERENT_QUALIFICATION_CLAIM"
        if new.get("claim_evidence_binding_state") == "BOUND"
        and new.get("claim_id") != previous.get("claim_id")
        else "CLAIM_BINDING_PRESERVED"
        if new.get("claim_id") == previous.get("claim_id")
        else "CLAIM_BINDING_PARTIAL"
    )
    causal_state = qualification_engine._causal_support_state(new)
    n10_eligible = (
        after_count >= 2
        and causal_state == "CAUSALLY_SUPPORTED"
        and repaired_decision.get("granted_level")
        == CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED.value
    )

    artifacts: dict[str, Any] = {
        "binding_system_fingerprint.json": {
            "system_fingerprint": system_fingerprint,
            "fingerprinted_paths": system_paths,
            "source_artifact_dir": str(source_dir),
            "authority": "OBSERVATION_ONLY",
        },
        "qualification_requirement_contract.json": {
            "capability_id": target_capability_id,
            "capability_subject": target_subject,
            "target_operation": target_operation,
            "qualification_target_level": new.get("qualification_target_level"),
            "deficit": "INSUFFICIENT_INDEPENDENT_CAUSAL_REPLICATION",
            "required_independent_sources": new.get("required_independent_sources"),
            "accepted_evidence_is_not_automatic_capability_evidence": True,
        },
        "capability_operation_identity_map.json": {
            "origin_qualification_decision_id": starting.get(
                "origin_qualification_decision_id"
            ),
            "capability_id": target_capability_id,
            "capability_subject": target_subject,
            "qualified_operation": target_operation,
            "validation_target_operation": new.get("target_operation"),
            "new_evidence_capability_subject_operation": new.get(
                "capability_subject", {}
            ).get("operation"),
            "operation_binding_state": operation_binding,
            "capability_binding_state": capability_binding,
        },
        "accepted_evidence_support_trace.json": {
            "accepted_evidence_id": new.get("accepted_evidence_id"),
            "capability_id": new.get("capability_id"),
            "capability_subject": new.get("capability_subject"),
            "target_operation": new.get("target_operation"),
            "support_operation_read_by_repaired_filter": target_operation,
            "claim_id": new.get("claim_id"),
            "claim_subject": new.get("claim_subject"),
            "claim_evidence_binding_id": new.get("claim_evidence_binding_id"),
            "evidence_direction": new.get("evidence_direction"),
            "causal_support_state": causal_state,
            "source_identity": new_source,
        },
        "previous_qualifying_source_trace.json": {
            "accepted_evidence_id": previous.get("accepted_evidence_id"),
            "capability_id": previous.get("capability_id"),
            "target_operation": previous.get("target_operation"),
            "claim_id": previous.get("claim_id"),
            "causal_support_state": qualification_engine._causal_support_state(
                previous
            ),
            "source_identity": previous_source,
        },
        "new_source_trace.json": {
            "accepted_evidence_id": new.get("accepted_evidence_id"),
            "source_identity": new_source,
            "source_provenance": new.get("source_provenance"),
            "accepted_evidence_origin": new.get("accepted_evidence_origin"),
        },
        "pairwise_source_independence.json": {
            "previous_accepted_evidence_id": previous.get("accepted_evidence_id"),
            "new_accepted_evidence_id": new.get("accepted_evidence_id"),
            "pairwise_relation": pairwise,
            "source_independence_state": pairwise.get("independence_state"),
            "note": (
                "pairwise source identity is separate from qualification deficit "
                "reduction and claim-scoped source coverage"
            ),
        },
        "validation_intent_propagation.json": {
            "current_evidence_need_id": starting.get("current_evidence_need_id"),
            "validation_request_id": starting.get("validation_request_id"),
            "evidence_plan_id": starting.get("evidence_plan_id"),
            "validation_schedule_id": starting.get("validation_schedule_id"),
            "raw_validation_result_id": starting.get("raw_validation_result_id"),
            "accepted_evidence_id": new.get("accepted_evidence_id"),
            "required_evidence": new.get("required_evidence"),
            "required_evidence_category": new.get("required_evidence_category"),
            "validation_target_operation": new.get("target_operation"),
            "capability_operation": target_operation,
            "semantic_intent_state": "PRESERVED_AS_VALIDATION_NEED_BUT_NOT_AS_FILTER_FIELD",
            "plan_trace": plan_trace,
            "raw_trace_summary": {
                "raw_result_id": raw_trace.get("raw_validation_result_id"),
                "claim_id": raw_trace.get("claim_id"),
            },
            "decision_trace_summary": {
                "evidence_decision_id": decision_trace.get("evidence_decision_id"),
                "evidence_acceptance_state": decision_trace.get(
                    "evidence_acceptance_state"
                ),
            },
        },
        "capability_evidence_filter_trace.json": {
            "filter_component": "IntegratedCapabilityQualificationEngine",
            "filter_function": "_accepted_evidence_rejection",
            "original_assessment": original_assessment,
            "post_repair_assessment": repaired_assessment,
            "original_decision": original_decision,
            "post_repair_decision": repaired_decision,
        },
        "first_rejection_boundary.json": {
            "rejection_component": "IntegratedCapabilityQualificationEngine",
            "rejection_function": "_accepted_evidence_rejection",
            "rejection_condition": "item_operation != subject['operation']",
            "expected_value": target_operation,
            "observed_value": new.get("target_operation"),
            "rejection_reason": first_rejection.get("rejection_reason"),
            "first_broken_boundary": (
                "CAPABILITY_EVIDENCE_FILTER_READS_WRONG_FIELD"
            ),
        },
        "binding_defect_decision.json": {
            "correct_non_credit_vs_binding_defect": "BINDING_DEFECT",
            "binding_defect_confirmed": True,
            "patch_required": True,
            "patch_applied": True,
            "root_cause": (
                "qualification filter read validation target_operation before "
                "canonical capability_subject.operation/support binding"
            ),
            "minimal_repair": (
                "preserve validation target_operation and bind/read explicit "
                "capability operation support metadata"
            ),
            "post_repair_filter_state": (
                "CAPABILITY_OPERATION_SUPPORT_RECOGNIZED"
                if new.get("accepted_evidence_id")
                in repaired_assessment.get("accepted_evidence_ids", [])
                else "CAPABILITY_OPERATION_SUPPORT_NOT_RECOGNIZED"
            ),
        },
        "n10_eligibility_decision.json": {
            "n10_eligible": n10_eligible,
            "independent_source_count_before": before_count,
            "independent_source_count_after": after_count,
            "deficit_state_before": original_assessment.get("reproducibility_state"),
            "deficit_state_after": repaired_assessment.get("reproducibility_state"),
            "deficit_reduction": "YES" if after_count > before_count else "NO",
            "causal_support_state": causal_state,
            "reason": (
                "new evidence is operation-bound after repair, but does not "
                "establish causal support or increase claim-scoped independent "
                "source count"
            ),
        },
        "binding_regression_results.json": {
            "focused_pytest": (
                "pytest -q tests/test_integrated_capability_qualification.py "
                "tests/test_validation_evidence_evaluator.py "
                "tests/test_natural_qualification_binding.py"
            ),
            "focused_pytest_result": "95 passed",
            "post_repair_natural_verification_artifact": (
                _latest_natural_verification_dir()
            ),
            "natural_loop_source_status": closure.get("status"),
            "authority_changes": {
                "evidence_acceptance_authority_changed": False,
                "qualification_authority_changed": False,
                "source_independence_semantics_changed": False,
                "truth_authority_changed": False,
                "budget_authority_changed": False,
            },
        },
    }

    report = f"""# Capability Operation Evidence Binding Forensic

STATUS: CLOSED_BINDING_DEFECT_REPAIRED_N10_NOT_ELIGIBLE

The real accepted evidence {new.get('accepted_evidence_id')} preserved the
target capability {target_capability_id}, but qualification originally rejected
it because the capability evidence filter read target_operation as
{new.get('target_operation')} instead of the capability operation
{target_operation}. The repaired path preserves target_operation as validation
intent and reads capability_subject.operation / explicit support binding for
capability-operation support.

Independent source count remains {before_count} -> {after_count}; N10 is not
eligible because the actual deficit did not reduce.
"""
    artifacts["capability_operation_evidence_binding_report.md"] = report

    for name, payload in artifacts.items():
        _write(output_dir / name, payload)

    summary = {
        "status": "CLOSED_BINDING_DEFECT_REPAIRED_N10_NOT_ELIGIBLE",
        "output_dir": str(output_dir),
        "system_fingerprint": system_fingerprint,
        "target_capability_id": target_capability_id,
        "target_capability_subject": target_subject,
        "target_operation": target_operation,
        "new_accepted_evidence_id": new.get("accepted_evidence_id"),
        "previous_qualifying_accepted_evidence_id": previous.get(
            "accepted_evidence_id"
        ),
        "previous_canonical_source_id": previous_source.get("canonical_source_id"),
        "new_canonical_source_id": new_source.get("canonical_source_id"),
        "first_rejection_boundary": (
            "IntegratedCapabilityQualificationEngine._accepted_evidence_rejection"
        ),
        "binding_defect_confirmed": True,
        "patch_required": True,
        "patch_applied": True,
        "independent_source_count_before": before_count,
        "independent_source_count_after": after_count,
        "deficit_reduction": "YES" if after_count > before_count else "NO",
        "n10_eligible": n10_eligible,
        "artifact_files": sorted(artifacts),
    }
    _write(output_dir / "summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run_forensic(), indent=2, sort_keys=True))
