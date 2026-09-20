from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


OUTPUT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "c5_contract_design"
C3_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "natural_causal_validation_campaign"
C4_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "exact_subject_causal_replication"
DOC_PATH = PROJECT_ROOT / "docs" / "c5_multi_capability_causal_reproducibility_contract.md"

C5_MIN_TARGET_SUBJECTS = 3
C5_MIN_UNIQUE_CAPABILITIES = 3
C5_MIN_UNIQUE_OPERATIONS = 2
C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT = 2
C5_MIN_GLOBAL_SOURCE_LINEAGES = 3
C5_MIN_CONTEXTS_PER_SUBJECT = 2


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


def _latest_dir(root: Path) -> Path | None:
    candidates = [path for path in root.glob("*") if path.is_dir()]
    return sorted(candidates, key=lambda path: path.name)[-1] if candidates else None


def _fingerprint(paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        path = PROJECT_ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def exact_subject_key(evidence: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(evidence.get("capability_id") or "UNKNOWN"),
        str(
            evidence.get("capability_support_operation")
            or evidence.get("target_operation")
            or "UNKNOWN"
        ),
        str(evidence.get("claim_id") or "UNKNOWN"),
    )


def c5_subject_unit(
    subject: Mapping[str, Any],
    *,
    min_sources: int = C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT,
    min_contexts: int = C5_MIN_CONTEXTS_PER_SUBJECT,
) -> dict[str, Any]:
    return {
        "exact_subject_key": [
            subject.get("capability_id"),
            subject.get("operation"),
            subject.get("qualification_claim_id"),
        ],
        "c5_unit_type": "C4_QUALIFIED_EXACT_SUBJECT",
        "c4_gate_passed": bool(subject.get("C4_state") == "C4_PASSED"),
        "qualification_level_sufficient": (
            subject.get("current_qualification_level") == "REPRODUCIBLY_SUPPORTED"
        ),
        "independent_source_count_sufficient": int(
            subject.get("independent_causal_source_count") or 0
        )
        >= min_sources,
        "context_count_sufficient": int(subject.get("context_count") or 0)
        >= min_contexts,
        "counts_toward_c5": (
            subject.get("C4_state") == "C4_PASSED"
            and subject.get("current_qualification_level") == "REPRODUCIBLY_SUPPORTED"
            and int(subject.get("independent_causal_source_count") or 0)
            >= min_sources
            and int(subject.get("context_count") or 0) >= min_contexts
        ),
    }


def c5_gate(
    *,
    target_set_frozen: bool,
    contract_mutation_count: int,
    subjects: Iterable[Mapping[str, Any]],
    source_independence_inflation_count: int,
    synthetic_downstream_object_count: int,
    authority_violation_count: int,
    dropped_failed_subject_count: int = 0,
    min_subjects: int = C5_MIN_TARGET_SUBJECTS,
    min_capabilities: int = C5_MIN_UNIQUE_CAPABILITIES,
    min_operations: int = C5_MIN_UNIQUE_OPERATIONS,
    min_global_sources: int = C5_MIN_GLOBAL_SOURCE_LINEAGES,
    min_contexts: int = C5_MIN_CONTEXTS_PER_SUBJECT,
) -> dict[str, Any]:
    rows = [dict(item) for item in subjects]
    units = [c5_subject_unit(item) for item in rows]
    qualifying = [
        item for item, unit in zip(rows, units)
        if unit["counts_toward_c5"]
    ]
    unique_capabilities = {
        str(item.get("capability_id"))
        for item in qualifying
        if item.get("capability_id")
    }
    unique_operations = {
        str(item.get("operation"))
        for item in qualifying
        if item.get("operation")
    }
    source_lineages = {
        str(source)
        for item in qualifying
        for source in item.get("canonical_source_ids", []) or []
        if source not in {None, "", "UNKNOWN", "Not Available"}
    }
    failed_subjects = [
        item for item, unit in zip(rows, units)
        if not unit["counts_toward_c5"]
    ]
    failures = []
    if not target_set_frozen:
        failures.append("target_set_not_frozen")
    if contract_mutation_count:
        failures.append("contract_mutated")
    if len(rows) < min_subjects:
        failures.append("target_subject_count_below_minimum")
    if len(qualifying) != len(rows):
        failures.append("target_set_not_fully_replicated")
    if len(unique_capabilities) < min_capabilities:
        failures.append("unique_capability_count_below_minimum")
    if len(unique_operations) < min_operations:
        failures.append("unique_operation_count_below_minimum")
    if len(source_lineages) < min_global_sources:
        failures.append("global_source_lineage_count_below_minimum")
    if any(int(item.get("context_count") or 0) < min_contexts for item in rows):
        failures.append("subject_context_count_below_minimum")
    if source_independence_inflation_count:
        failures.append("source_independence_inflation")
    if synthetic_downstream_object_count:
        failures.append("synthetic_downstream_objects_present")
    if authority_violation_count:
        failures.append("authority_violation")
    if dropped_failed_subject_count:
        failures.append("failed_subject_removed_after_freeze")
    return {
        "c5_pass": not failures,
        "failure_reasons": failures,
        "target_subject_count": len(rows),
        "replicated_subject_count": len(qualifying),
        "failed_subject_count": len(failed_subjects),
        "unique_capability_count": len(unique_capabilities),
        "unique_operation_count": len(unique_operations),
        "unique_global_source_lineage_count": len(source_lineages),
        "subject_units": units,
    }


def _accepted_evidence_from(path: Path) -> list[dict[str, Any]]:
    directory = path / "campaign_state" / "plans" / "accepted_evidence"
    if not directory.exists():
        return []
    return [
        _read(item) for item in sorted(directory.glob("*.json"))
        if item.is_file()
    ]


def _current_subject_inventory() -> list[dict[str, Any]]:
    latest_c3 = _latest_dir(C3_ROOT)
    latest_c4 = _latest_dir(C4_ROOT)
    rows = []
    for source_artifact, evidence_rows in (
        (latest_c3, _accepted_evidence_from(latest_c3) if latest_c3 else []),
        (latest_c4, _accepted_evidence_from(latest_c4) if latest_c4 else []),
    ):
        for evidence in evidence_rows:
            subject = evidence.get("capability_subject")
            if not isinstance(subject, Mapping):
                continue
            key = exact_subject_key(evidence)
            causal = evidence.get("causal_evidence") or {}
            rows.append({
                "source_artifact": str(source_artifact),
                "capability_id": key[0],
                "capability_subject": dict(subject),
                "operation": key[1],
                "qualification_claim_id": key[2],
                "accepted_evidence_id": evidence.get("accepted_evidence_id"),
                "causal_evidence_id": evidence.get("causal_evidence_id"),
                "causal_support_state": evidence.get("causal_support_state"),
                "canonical_source_identity": evidence.get(
                    "canonical_source_identity"
                ),
                "source_lineage": evidence.get("source_lineage") or [],
                "task_id": evidence.get("selected_validation_task_id"),
                "context": (subject.get("qualifiers") or {}).get(
                    "validation_context"
                ),
                "domain": subject.get("domain"),
                "counterfactual_method": causal.get(
                    "method",
                    "CONTROLLED_TRANSFORMATION_EFFECT",
                ),
                "causal_estimand": "treatment_score - control_score",
                "evidence_origin": evidence.get("accepted_evidence_origin"),
            })
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (
            row["capability_id"],
            row["operation"],
            row["qualification_claim_id"],
        )
        entry = grouped.setdefault(key, {
            "capability_id": key[0],
            "capability_subject": row["capability_subject"],
            "operation": key[1],
            "qualification_claim_id": key[2],
            "current_qualification_level": "NOT_QUALIFIED",
            "C4_state": "C4_NOT_PROVEN",
            "accepted_causal_evidence_count": 0,
            "independent_causal_source_count": 0,
            "task_count": 0,
            "context_count": 0,
            "source_lineage_count": 0,
            "domain_category": row["domain"],
            "counterfactual_method": row["counterfactual_method"],
            "causal_estimand": row["causal_estimand"],
            "evidence_origin": [],
            "accepted_evidence_ids": [],
            "canonical_source_ids": [],
            "task_ids": [],
            "contexts": [],
        })
        if row["causal_support_state"] == "CAUSALLY_SUPPORTED":
            entry["accepted_causal_evidence_count"] += 1
            entry["accepted_evidence_ids"].append(row["accepted_evidence_id"])
            entry["canonical_source_ids"].append(row["canonical_source_identity"])
            entry["task_ids"].append(row["task_id"])
            entry["contexts"].append(row["context"])
            entry["evidence_origin"].append(row["evidence_origin"])
    latest_c4 = _latest_dir(C4_ROOT)
    c4_decision = (
        _read(latest_c4 / "19_c4_gate_decision.json")
        if latest_c4 and (latest_c4 / "19_c4_gate_decision.json").exists()
        else {}
    )
    for entry in grouped.values():
        entry["independent_causal_source_count"] = len({
            item for item in entry["canonical_source_ids"]
            if item not in {None, "", "UNKNOWN", "Not Available"}
        })
        entry["task_count"] = len(set(filter(None, entry["task_ids"])))
        entry["context_count"] = len(set(filter(None, entry["contexts"])))
        entry["source_lineage_count"] = entry["independent_causal_source_count"]
        if (
            c4_decision.get("c4_gate_passed")
            and entry["capability_id"] == c4_decision.get("target_capability_id")
            and entry["operation"] == c4_decision.get("target_operation")
            and entry["qualification_claim_id"]
            == c4_decision.get("qualification_claim_id")
        ):
            entry["current_qualification_level"] = "REPRODUCIBLY_SUPPORTED"
            entry["C4_state"] = "C4_PASSED"
            entry["independent_causal_source_count"] = int(
                c4_decision.get("independent_causal_source_count_after") or 0
            )
        elif entry["accepted_causal_evidence_count"] > 0:
            entry["current_qualification_level"] = "CAUSALLY_DEMONSTRATED"
            entry["C4_state"] = "C4_NOT_PASSED_INSUFFICIENT_SOURCES"
    return sorted(
        grouped.values(),
        key=lambda item: (
            item["C4_state"] != "C4_PASSED",
            item["operation"],
            item["qualification_claim_id"],
        ),
    )


def _eligibility_matrix(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in inventory:
        unit = c5_subject_unit(item)
        causal_task_available = item["accepted_causal_evidence_count"] > 0
        counterfactual_available = item["counterfactual_method"] != "UNKNOWN"
        source_quality = (
            "PROVEN"
            if item["independent_causal_source_count"] > 0
            else "INSUFFICIENT"
        )
        reasons = []
        if not unit["c4_gate_passed"]:
            reasons.append("subject_not_c4_qualified")
        if not unit["qualification_level_sufficient"]:
            reasons.append("qualification_level_below_reproducibly_supported")
        if not unit["independent_source_count_sufficient"]:
            reasons.append("independent_source_count_below_minimum")
        if not unit["context_count_sufficient"]:
            reasons.append("context_count_below_minimum")
        if not causal_task_available:
            reasons.append("no_causal_task_evidence")
        if not counterfactual_available:
            reasons.append("counterfactual_unavailable")
        if source_quality != "PROVEN":
            reasons.append("source_provenance_insufficient")
        rows.append({
            "capability_id": item["capability_id"],
            "operation": item["operation"],
            "qualification_claim_id": item["qualification_claim_id"],
            "current_qualification_level": item["current_qualification_level"],
            "C4_state": item["C4_state"],
            "independent_causal_source_count": item[
                "independent_causal_source_count"
            ],
            "causal_task_availability": causal_task_available,
            "counterfactual_availability": counterfactual_available,
            "source_provenance_quality": source_quality,
            "context_diversity": item["context_count"],
            "C5_candidate_eligible": unit["counts_toward_c5"],
            "ineligibility_reason": reasons or ["eligible_c4_subject"],
        })
    return rows


def _contract_markdown() -> str:
    return """# C5 Multi-Capability Causal Reproducibility Contract

## Purpose
C5 defines a bounded study-grade claim that independently replicated causal validation is demonstrated across multiple exact capability-operation subjects.

## Scope
C5 is not a runtime promotion mechanism and does not execute a campaign. It defines the future contract only.

## Hierarchy
- C1: controlled causal path.
- C2: natural single-context causal validation.
- C3: natural multi-task causal validation.
- C4: exact-subject independent causal replication.
- C5: multi-subject causal reproducibility.

## Exact Subject
`ExactSubject = (capability_id, capability_operation, qualification_claim_id)`.
This preserves the C4 identity model.

## Evidence Unit
The atomic C5 evidence unit is one exact subject with C4 passed. Artifacts, tasks, sources, runs, and scores are not C5 units.

## Distinctness
Subject distinctness is exact-subject distinctness. Capability distinctness is canonical `capability_id`. If one capability has multiple operations, those are multiple subjects but one capability unless the canonical capability identity differs.

## Thresholds
Future C5 requires a frozen target set with at least 3 exact subjects, at least 3 canonical capability IDs, at least 2 distinct operations, and at least 2 proven independent causal sources per subject.

## Source Rules
Each subject must independently satisfy C4. Global source diversity is additionally required as a concentration guard: at least 3 unique canonical source lineages across the campaign and no source-independence inflation.

## Context Rules
Each subject should have at least 2 validation contexts. This is a C5 contract requirement for the future campaign, but it cannot replace source independence.

## Domain Rules
C5 is multi-capability, not multi-domain. Cross-domain generalization is a future contract, not part of C5.

## Causal Rules
Subjects may use operation-appropriate causal estimands under a shared causal-support ontology. Identical instrumentation is not required; valid counterfactuals and governed causal support are required.

## Qualification Rules
Every counted subject must be `REPRODUCIBLY_SUPPORTED` through existing governed qualification. Causally demonstrated but non-reproducible subjects do not count.

## Target Set Rules
The C5 target subject set must be pre-registered before execution. Failed subjects cannot be removed after outcomes are known except for audited contract invalidity, identity corruption, proven architectural unreachability, or eligibility misclassification.

## Failure Semantics
Allowed outcomes are `C5_MULTI_CAPABILITY_REPRODUCIBILITY_PROVEN`, `C4_ONLY_INSUFFICIENT_SUBJECT_BREADTH`, `C4_ONLY_SUBJECT_REPLICATION_MIXED`, `C4_ONLY_SOURCE_DIVERSITY_INSUFFICIENT`, `C4_ONLY_TARGET_SET_NOT_FULLY_REPLICATED`, `ARCHITECTURAL_INTEGRATION_DEFECT_FOUND`, and `CONTRACT_INVALIDATED`.

## Authority
Per-subject qualification remains owned by `IntegratedCapabilityQualificationEngine`. C5 aggregate authority is `OBSERVATION_ONLY` and must not mutate runtime capability state.

## Forbidden Inferences
C5 does not imply general intelligence, broad generalization, learning, transfer, truth completeness, production safety, or execution authority.

## Future Protocol
Freeze the C5 contract, freeze the target set, run natural validation campaigns without synthetic downstream object creation, assess each subject against C4, apply negative controls, and aggregate only over C4-qualified exact subjects.
"""


def run_design(output_root: str | Path = OUTPUT_ROOT) -> dict[str, Any]:
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc_text = _contract_markdown()
    _write(DOC_PATH, doc_text)
    system_paths = [
        "runtime/experiments/c5_contract_design.py",
        "docs/c5_multi_capability_causal_reproducibility_contract.md",
        "runtime/experiments/exact_subject_causal_replication.py",
        "runtime/capability_intelligence/integrated_capability_qualification.py",
        "runtime/epistemic/evidence_source_independence.py",
    ]
    system_fingerprint = _fingerprint(system_paths)
    inventory = _current_subject_inventory()
    eligibility = _eligibility_matrix(inventory)
    c4_subjects = [
        item for item in inventory if item["C4_state"] == "C4_PASSED"
    ]
    c5_eligible_subjects = [
        item for item in c4_subjects if c5_subject_unit(item)["counts_toward_c5"]
    ]
    source_counts = Counter(
        source
        for item in inventory
        for source in item.get("canonical_source_ids", [])
        if source not in {None, "", "UNKNOWN", "Not Available"}
    )
    gate_contract = {
        "c5_gate_formalized": (
            "target_set_frozen AND contract_mutation_count == 0 AND "
            "target_subject_count >= 3 AND replicated_subject_count == target_subject_count "
            "AND unique_capability_count >= 3 AND unique_operation_count >= 2 "
            "AND every target subject C4_GATE_PASSED == TRUE "
            "AND global_source_lineage_count >= 3 "
            "AND every target subject context_count >= 2 "
            "AND source_independence_inflation_count == 0 "
            "AND synthetic_downstream_object_count == 0 "
            "AND authority_violation_count == 0 "
            "AND dropped_failed_subject_count == 0"
        ),
        "minimum_target_subject_count": C5_MIN_TARGET_SUBJECTS,
        "minimum_unique_capability_count": C5_MIN_UNIQUE_CAPABILITIES,
        "minimum_unique_operation_count": C5_MIN_UNIQUE_OPERATIONS,
        "minimum_independent_causal_sources_per_subject": (
            C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT
        ),
        "minimum_global_source_lineage_count": C5_MIN_GLOBAL_SOURCE_LINEAGES,
        "minimum_contexts_per_subject": C5_MIN_CONTEXTS_PER_SUBJECT,
        "c5_contract_mutation_count_requirement": 0,
    }
    readiness = {
        "status": "C5_CONTRACT_DEFINED_NOT_EXECUTED",
        "current_c4_subject_count": len(c4_subjects),
        "current_c5_eligible_subject_count": len(c5_eligible_subjects),
        "current_c5_readiness": "NOT_READY_INSUFFICIENT_SUBJECT_BREADTH",
        "c5_authorized_for_claim": False,
        "reason": "only one current C4-qualified exact subject; future frozen target set required",
    }
    output_dir = Path(output_root) / _stamp()
    artifacts = {
        "c5_system_fingerprint.json": {
            "system_fingerprint": system_fingerprint,
            "fingerprinted_paths": system_paths,
        },
        "c5_current_subject_inventory.json": inventory,
        "c5_current_c4_subjects.json": c4_subjects,
        "c5_subject_eligibility_matrix.json": eligibility,
        "c5_source_diversity_analysis.json": {
            "global_source_lineage_counts": dict(source_counts),
            "unique_global_source_lineage_count": len(source_counts),
            "max_source_share": (
                max(source_counts.values()) / sum(source_counts.values())
                if source_counts else 0.0
            ),
            "global_source_diversity_required": True,
            "minimum_global_source_lineage_count": C5_MIN_GLOBAL_SOURCE_LINEAGES,
        },
        "c5_context_diversity_analysis.json": {
            "minimum_contexts_per_subject": C5_MIN_CONTEXTS_PER_SUBJECT,
            "context_diversity_required": True,
            "subject_context_counts": [
                {
                    "capability_id": item["capability_id"],
                    "operation": item["operation"],
                    "qualification_claim_id": item["qualification_claim_id"],
                    "context_count": item["context_count"],
                }
                for item in inventory
            ],
        },
        "c5_contract_options_matrix.json": [
            {
                "model": "MODEL_A",
                "description": "multiple capabilities; operation diversity optional",
                "decision": "REJECTED_TOO_WEAK_FOR_OPERATIONAL_BREADTH",
            },
            {
                "model": "MODEL_B",
                "description": "multiple capability-operation subjects with operation diversity",
                "decision": "SELECTED",
            },
            {
                "model": "MODEL_C",
                "description": "multiple cognitive families required",
                "decision": "DEFER_TO_FUTURE_CROSS_DOMAIN_LEVEL",
            },
        ],
        "c5_threshold_rationale.json": {
            "minimum_target_subject_count": C5_MIN_TARGET_SUBJECTS,
            "rationale": "three is the smallest non-binary breadth test and prevents a single pair from defining architectural reproducibility",
            "minimum_unique_capability_count": C5_MIN_UNIQUE_CAPABILITIES,
            "minimum_unique_operation_count": C5_MIN_UNIQUE_OPERATIONS,
            "per_subject_sources": C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT,
        },
        "c5_target_set_recommendation.json": {
            "recommended_target_subject_count": C5_MIN_TARGET_SUBJECTS,
            "recommended_unique_capability_count": C5_MIN_UNIQUE_CAPABILITIES,
            "recommended_unique_operation_count": C5_MIN_UNIQUE_OPERATIONS,
            "minimum_independent_causal_sources_per_subject": (
                C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT
            ),
            "minimum_context_requirement": C5_MIN_CONTEXTS_PER_SUBJECT,
            "required_source_provenance_quality": "PROVEN",
            "current_corpus_supports_recommendation": False,
        },
        "c5_gate_contract.json": gate_contract,
        "c5_negative_control_spec.json": {
            "controls": [
                "same_subject_replicated_twice_but_no_second_capability",
                "multiple_subjects_but_only_one_has_C4",
                "same_upstream_source_families_across_all_subjects",
                "wrong_operation_evidence",
                "wrong_claim_evidence",
                "independent_but_non_causal_evidence",
                "causal_but_dependent_evidence",
                "post_hoc_target_selection",
                "subject_dropped_after_failure",
                "task_count_inflation",
                "run_count_inflation",
                "artifact_count_inflation",
            ],
            "expected_result": "C5_FAILS",
        },
        "c5_authority_contract.json": {
            "per_subject_authority": "IntegratedCapabilityQualificationEngine",
            "c5_aggregate_authority": "OBSERVATION_ONLY",
            "runtime_state_mutation_allowed": False,
            "truth_authority": "NONE",
            "execution_authority": "NONE",
            "budget_authority": "NONE",
        },
        "c5_readiness_decision.json": readiness,
        "c5_multi_capability_causal_reproducibility_contract.md": doc_text,
    }
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    summary = {
        **readiness,
        "system_fingerprint": system_fingerprint,
        "output_dir": str(output_dir),
        "c5_definition": (
            "study-grade multi-subject causal reproducibility over C4-qualified exact subjects"
        ),
        "c5_evidence_unit": "one C4-qualified exact subject",
        "minimum_target_subject_count": C5_MIN_TARGET_SUBJECTS,
        "minimum_unique_capability_count": C5_MIN_UNIQUE_CAPABILITIES,
        "minimum_unique_operation_count": C5_MIN_UNIQUE_OPERATIONS,
        "minimum_independent_causal_sources_per_subject": (
            C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT
        ),
        "minimum_global_source_lineage_count": C5_MIN_GLOBAL_SOURCE_LINEAGES,
        "patch_required": "NO",
        "patch_applied": "NO",
    }
    _write(output_dir / "summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run_design(), indent=2, sort_keys=True))
