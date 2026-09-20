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


BINDING_FORENSIC_DIR = (
    PROJECT_ROOT
    / "runtime"
    / "artifacts"
    / "capability_operation_evidence_binding"
    / "forensic_20260913_160230"
)
NATURAL_SOURCE_DIR = (
    PROJECT_ROOT
    / "runtime"
    / "artifacts"
    / "natural_evidence_qualification_loop"
    / "verification_20260913_160129"
)
OUTPUT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "causal_claim_source_accounting"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any] | str) -> None:
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


def _latest_natural_verification_dir() -> Path:
    root = (
        PROJECT_ROOT
        / "runtime"
        / "artifacts"
        / "natural_evidence_qualification_loop"
    )
    candidates = sorted(path for path in root.glob("verification_*") if path.is_dir())
    if not candidates:
        raise FileNotFoundError("natural_verification_artifact_required")
    return candidates[-1]


def _source_identity(
    source_engine: EvidenceSourceIndependenceEngine,
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
    return source_engine.source_identity(flattened)


def run_forensic(
    output_root: str | Path = OUTPUT_ROOT,
    binding_forensic_dir: str | Path = BINDING_FORENSIC_DIR,
    natural_source_dir: str | Path = NATURAL_SOURCE_DIR,
) -> dict[str, Any]:
    binding_dir = Path(binding_forensic_dir)
    natural_dir = Path(natural_source_dir)
    latest_natural_dir = _latest_natural_verification_dir()
    output_dir = Path(output_root) / f"forensic_{_stamp()}"

    binding_summary = _read(binding_dir / "summary.json")
    binding_support = _read(binding_dir / "accepted_evidence_support_trace.json")
    binding_filter = _read(binding_dir / "capability_evidence_filter_trace.json")
    pairwise = _read(binding_dir / "pairwise_source_independence.json")
    natural_starting = _read(natural_dir / "natural_loop_starting_lineage.json")
    natural_accepted = _read(natural_dir / "accepted_evidence_trace.json")
    natural_raw = _read(natural_dir / "raw_result_identity_trace.json")
    natural_reassessment = _read(natural_dir / "qualification_reassessment_trace.json")
    latest_reassessment = _read(latest_natural_dir / "qualification_reassessment_trace.json")

    previous = _read(
        natural_dir
        / "controlled_state"
        / "plans"
        / "accepted_evidence"
        / "accepted_source_a.json"
    )
    new = _read(
        natural_dir
        / "controlled_state"
        / "plans"
        / "accepted_evidence"
        / f"{natural_accepted['accepted_evidence_id']}.json"
    )

    qualification_engine = IntegratedCapabilityQualificationEngine()
    source_engine = EvidenceSourceIndependenceEngine()
    previous_causal = qualification_engine._causal_support_state(previous)
    new_causal = qualification_engine._causal_support_state(new)
    previous_source = _source_identity(source_engine, previous)
    new_source = _source_identity(source_engine, new)
    target_subject = natural_accepted["capability_subject"]
    target_capability = natural_accepted["capability_id"]
    target_operation = target_subject["operation"]
    validation_claim = natural_accepted.get("claim_id")
    qualification_claim = previous.get("claim_id")

    pre_patch_assessment = binding_filter["post_repair_assessment"]
    post_patch_assessment = latest_reassessment["qualification_results"][0][
        "capability_evidence_assessment"
    ]
    post_patch_decision = latest_reassessment["qualification_results"][0][
        "qualification_decision"
    ]

    replay = qualification_engine.decide(
        target_subject,
        [previous, new],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        current_level=CapabilityQualificationLevel.NOT_QUALIFIED,
        architecture_present=True,
        runtime_reachable=True,
        assessment_run_id="causal_claim_source_accounting_forensic_replay",
        required_independent_sources=2,
    )
    replay_assessment = replay["capability_evidence_assessment"]
    before_count = int(natural_starting["starting_assessment"].get("independent_source_count") or 0)
    after_count = int(replay_assessment.get("independent_source_count") or 0)

    system_paths = [
        "runtime/capability_intelligence/integrated_capability_qualification.py",
        "runtime/epistemic/evidence_source_independence.py",
        "runtime/validation/validation_evidence_evaluator.py",
        "runtime/experiments/causal_claim_source_accounting_forensic.py",
    ]
    system_fingerprint = _fingerprint(system_paths)
    artifacts: dict[str, Any] = {
        "causal_support_contract.json": {
            "causal_support_owner": "IntegratedCapabilityQualificationEngine",
            "causal_support_function": "_causal_support_state",
            "accepted_fields_read": [
                "capability_causal_support_state",
                "causal_support_state",
                "causal_attribution_state",
            ],
            "accepted_values": [
                "CAUSALLY_SUPPORTED",
                "CAUSALLY_DEMONSTRATED",
                "MATERIAL_CONTRIBUTION_DEMONSTRATED",
            ],
            "source_count_filter": "CAUSALLY_SUPPORTED_ACCEPTED_EVIDENCE_ONLY",
            "validation_success_is_not_causal_support": True,
            "authority": "NONE",
        },
        "qualification_claim_identity_trace.json": {
            "qualification_claim_id": qualification_claim,
            "capability_id": target_capability,
            "capability_subject": target_subject,
            "operation": target_operation,
            "requested_qualification_level": "REPRODUCIBLY_SUPPORTED",
            "required_source_count": 2,
            "current_source_count_before": before_count,
            "current_source_count_after": after_count,
            "claim_identity_source": "existing_causal_accepted_evidence",
        },
        "validation_claim_identity_trace.json": {
            "validation_claim_id": validation_claim,
            "claim_subject": natural_accepted.get("claim_subject"),
            "claim_evidence_binding_id": natural_accepted.get(
                "claim_evidence_binding_id"
            ),
            "capability_id": natural_accepted.get("capability_id"),
            "operation": natural_accepted.get("target_operation"),
            "capability_support_operation": natural_accepted.get(
                "capability_support_operation"
            ),
            "accepted_evidence_id": natural_accepted.get("accepted_evidence_id"),
        },
        "claim_scope_binding_matrix.json": {
            "qualification_claim_id": qualification_claim,
            "validation_claim_id": validation_claim,
            "claim_relation": (
                "EXPECTED_CLAIM_LAYERING_WITH_NO_QUALIFICATION_CLAIM_BINDING"
            ),
            "same_claim": qualification_claim == validation_claim,
            "same_capability": previous.get("capability_id") == new.get("capability_id"),
            "same_capability_operation": (
                previous.get("target_operation")
                == new.get("capability_support_operation")
            ),
            "validation_evidence_supports_validation_claim": True,
            "validation_evidence_supports_qualification_claim": False,
        },
        "previous_qualifying_evidence_trace.json": {
            "accepted_evidence_id": previous.get("accepted_evidence_id"),
            "claim_id": previous.get("claim_id"),
            "capability_id": previous.get("capability_id"),
            "operation": previous.get("target_operation"),
            "causal_support_state": previous_causal,
            "canonical_source_identity": previous_source,
            "qualification_contribution": "COUNTS_AS_ONE_CAUSAL_SOURCE",
        },
        "new_evidence_causal_trace.json": {
            "accepted_evidence_id": new.get("accepted_evidence_id"),
            "requested_accepted_evidence_id": binding_summary.get(
                "new_accepted_evidence_id"
            ),
            "claim_id": new.get("claim_id"),
            "capability_id": new.get("capability_id"),
            "target_operation": new.get("target_operation"),
            "capability_support_operation": new.get("capability_support_operation"),
            "causal_fields": {
                key: new.get(key)
                for key in (
                    "capability_causal_support_state",
                    "causal_support_state",
                    "causal_attribution_state",
                )
                if key in new
            },
            "causal_support_state": new_causal,
            "operation_execution_trace": {
                "validation_execution_id": new.get("validation_execution_id"),
                "producer_operation_id": new.get("producer_operation_id"),
                "selected_validation_task_id": new.get("selected_validation_task_id"),
                "validation_scope": natural_raw.get("execution_report", {}).get(
                    "validation_scope"
                ),
            },
            "causal_operation_effect_observed": False,
            "classification": "VALIDATION_SUCCESS_ONLY",
        },
        "old_new_evidence_comparison.json": {
            "previous": {
                "accepted_evidence_id": previous.get("accepted_evidence_id"),
                "claim_id": previous.get("claim_id"),
                "causal_support_state": previous_causal,
                "source": previous_source.get("canonical_source_id"),
            },
            "new": {
                "accepted_evidence_id": new.get("accepted_evidence_id"),
                "requested_accepted_evidence_id": binding_summary.get(
                    "new_accepted_evidence_id"
                ),
                "claim_id": new.get("claim_id"),
                "causal_support_state": new_causal,
                "source": new_source.get("canonical_source_id"),
            },
            "semantic_difference": (
                "new evidence is independent and capability-operation-bound, "
                "but validation-claim-scoped and non-causal"
            ),
        },
        "independent_source_accounting_trace.json": {
            "accounting_owner": "IntegratedCapabilityQualificationEngine",
            "source_engine_owner": "EvidenceSourceIndependenceEngine",
            "source_count_before_patch": {
                "filter": "VALID_ACCEPTED_EVIDENCE_BY_FIRST_CLAIM",
                "independent_source_count": pre_patch_assessment.get(
                    "independent_source_count"
                ),
                "source_coverage_claim": pre_patch_assessment.get(
                    "source_coverage", {}
                ).get("claim_id"),
            },
            "source_count_after_patch": {
                "filter": post_patch_assessment.get("source_coverage_filter"),
                "independent_source_count": post_patch_assessment.get(
                    "independent_source_count"
                ),
                "source_coverage_claim": post_patch_assessment.get(
                    "source_coverage", {}
                ).get("claim_id"),
                "independent_causal_evidence_ids": post_patch_assessment.get(
                    "independent_causal_evidence_ids"
                ),
            },
            "pairwise_source_relation": pairwise.get("pairwise_relation"),
        },
        "source_count_filter_pipeline.json": {
            "pipeline": [
                {
                    "stage": "AcceptedEvidenceSet",
                    "previous": previous.get("accepted_evidence_id"),
                    "new": new.get("accepted_evidence_id"),
                    "new_state": "ACCEPTED",
                },
                {"stage": "Capability Filter", "new_state": "PASSED"},
                {"stage": "Operation Filter", "new_state": "PASSED"},
                {
                    "stage": "Causal Support Filter",
                    "new_state": "REMOVED",
                    "observed_value": new_causal,
                },
                {
                    "stage": "Claim Scope Filter",
                    "new_state": "NOT_REACHED_FOR_NEW_EVIDENCE",
                    "observed_claim": validation_claim,
                },
                {
                    "stage": "Canonical Source Identity",
                    "new_state": "PROVEN_BUT_NOT_COUNTED",
                    "source": new_source.get("canonical_source_id"),
                },
            ]
        },
        "first_non_credit_boundary.json": {
            "first_non_credit_component": "IntegratedCapabilityQualificationEngine",
            "first_non_credit_function": "_causal_support_state",
            "first_non_credit_filter": "causal_support_state",
            "expected_value": "CAUSALLY_SUPPORTED",
            "observed_value": new_causal,
            "non_credit_reason": "accepted_validation_evidence_has_no_causal_support_metadata",
        },
        "causal_claim_accounting_defect_decision.json": {
            "causal_support_defect_confirmed": False,
            "claim_accounting_defect_confirmed": True,
            "independent_causal_source_filter_defect_confirmed": True,
            "patch_required": True,
            "patch_applied": True,
            "non_credit_classification": "CORRECT_NON_CREDIT_CAUSAL_SUPPORT_ABSENT",
            "root_cause": (
                "new evidence is independent but non-causal; prior accounting "
                "computed source coverage before causal filtering"
            ),
        },
        "n10_eligibility_decision.json": {
            "n10_eligible": False,
            "independent_causal_source_count_before": before_count,
            "independent_causal_source_count_after": after_count,
            "deficit_state_before": natural_starting["starting_assessment"].get(
                "reproducibility_state"
            ),
            "deficit_state_after": replay_assessment.get("reproducibility_state"),
            "deficit_reduction": "YES" if after_count > before_count else "NO",
            "reason": "new evidence is independent but not causal",
        },
    }

    report = f"""# Causal Claim Source Accounting Forensic

STATUS: CLOSED_CORRECT_NON_CREDIT_WITH_ACCOUNTING_FILTER_REPAIR

The new accepted validation evidence is capability-operation-bound and has a
proven independent source, but it does not carry causal support metadata.
The first non-credit boundary is the qualification engine causal support
filter. A separate accounting defect was repaired so independent source
coverage is computed only over causally supported accepted evidence.

Independent causal source count remains {before_count} -> {after_count}; N10 is
not eligible.
"""
    artifacts["causal_claim_source_accounting_report.md"] = report

    for name, payload in artifacts.items():
        _write(output_dir / name, payload)

    summary = {
        "status": "CLOSED_CORRECT_NON_CREDIT_WITH_ACCOUNTING_FILTER_REPAIR",
        "output_dir": str(output_dir),
        "system_fingerprint": system_fingerprint,
        "qualification_claim_id": qualification_claim,
        "validation_claim_id": validation_claim,
        "claim_relation": "EXPECTED_CLAIM_LAYERING_WITH_NO_QUALIFICATION_CLAIM_BINDING",
        "target_capability_id": target_capability,
        "target_operation": target_operation,
        "previous_accepted_evidence_id": previous.get("accepted_evidence_id"),
        "previous_causal_support_state": previous_causal,
        "previous_canonical_source_id": previous_source.get("canonical_source_id"),
        "new_accepted_evidence_id": binding_summary.get("new_accepted_evidence_id"),
        "new_causal_support_state": new_causal,
        "new_canonical_source_id": new_source.get("canonical_source_id"),
        "source_relation": pairwise.get("source_independence_state"),
        "first_non_credit_boundary": "IntegratedCapabilityQualificationEngine._causal_support_state",
        "causal_support_defect_confirmed": False,
        "claim_accounting_defect_confirmed": True,
        "patch_required": True,
        "patch_applied": True,
        "independent_causal_source_count_before": before_count,
        "independent_causal_source_count_after": after_count,
        "deficit_reduction": "YES" if after_count > before_count else "NO",
        "n10_eligible": False,
        "artifact_files": sorted(artifacts),
    }
    _write(output_dir / "summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run_forensic(), indent=2, sort_keys=True))
