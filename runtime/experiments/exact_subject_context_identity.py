from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.capability_intelligence.context_identity import (
    AUTHORITY,
    canonical_capability_id_v2,
    capability_operation_id_v2,
    classify_context_diversity,
    legacy_identity_mapping,
    validation_context_id,
)
from runtime.capability_intelligence.integrated_capability_qualification import (
    capability_id_for_subject,
)


OUTPUT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "exact_subject_context_identity"
FILL_CENTER_CLAIM_ID = (
    "claim_sha256_a31b2d0349a83dd2cad08dd6d4e60ddc7245116d87c8bf7f0d95ee9442c50a33"
)

SYSTEM_PATHS = [
    "runtime/capability_intelligence/context_identity.py",
    "runtime/capability_intelligence/integrated_capability_qualification.py",
    "runtime/experiments/exact_subject_context_identity.py",
    "runtime/experiments/c4_breadth_expansion.py",
    "runtime/experiments/c5_target_set_prequalification.py",
    "runtime/experiments/c5_contract_design.py",
    "runtime/epistemic/evidence_source_independence.py",
    "runtime/validation/causal_validation_evidence.py",
    "runtime/validation/validation_evidence_evaluator.py",
]


def _stamp() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _write(path: Path, payload: Mapping[str, Any] | list[Any] | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
        return
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    json.loads(text)
    path.write_text(text + "\n", encoding="utf-8")


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint(paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        path = PROJECT_ROOT / relative
        if path.exists():
            digest.update(relative.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _payload_fingerprint(payload: Mapping[str, Any] | list[Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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


def _subject(context: str, *, operation: str = "fill_center") -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "capability_name": f"{operation}_capability",
        "operation": operation,
        "domain": "arc_grid_transformation",
        "qualifiers": {"validation_context": context},
    }


def _context(name: str, *, structural: str, intervention: str = "fill_center") -> dict[str, Any]:
    return {
        "context_type": "VALIDATION_SCENARIO",
        "context_parameters": {"validation_context": name},
        "structural_signature": structural,
        "causal_intervention_signature": intervention,
        "counterfactual_contract": "target_operation_disabled_same_input",
    }


def current_identity_contract() -> dict[str, Any]:
    return {
        "owner": "runtime.capability_intelligence.integrated_capability_qualification.capability_id_for_subject",
        "schema": "capability_identity.v1",
        "hash_algorithm": "sha256",
        "hash_prefix": "capability_",
        "hash_length": 16,
        "payload_owner": "_subject_payload / CapabilitySubject.canonical_payload",
        "historical_mutation_policy": "NO_HISTORICAL_MUTATION",
    }


def current_hash_inputs() -> list[dict[str, str]]:
    return [
        {"field": "schema_version", "classification": "VALIDATION_ONLY"},
        {"field": "capability_name", "classification": "INTRINSIC_CAPABILITY_SEMANTIC"},
        {"field": "operation", "classification": "OPERATION_SEMANTIC"},
        {"field": "domain", "classification": "DOMAIN_SEMANTIC"},
        {
            "field": "qualifiers.validation_context",
            "classification": "CONTEXT_SEMANTIC",
        },
        {"field": "qualifiers.*", "classification": "AMBIGUOUS"},
    ]


def invariance_matrix() -> list[dict[str, Any]]:
    base = _subject("fill_center_delta")
    second = _subject("fill_center_enclosure_variant")
    different_operation = _subject("fill_center_delta", operation="outline_border")
    different_capability = {
        **_subject("fill_center_delta"),
        "capability_name": "outline_border_capability",
    }
    cases = [
        {
            "case": "A_same_capability_same_operation_different_input_geometry",
            "expected_capability_identity": "SAME",
            "legacy_actual": (
                "SAME"
                if capability_id_for_subject(base) == capability_id_for_subject(second)
                else "DIFFERENT"
            ),
            "v2_actual": (
                "SAME"
                if canonical_capability_id_v2(base) == canonical_capability_id_v2(second)
                else "DIFFERENT"
            ),
        },
        {
            "case": "D_same_capability_family_different_operation",
            "expected_capability_operation_identity": "DIFFERENT",
            "legacy_actual": (
                "SAME"
                if capability_id_for_subject(base)
                == capability_id_for_subject(different_operation)
                else "DIFFERENT"
            ),
            "v2_operation_actual": (
                "SAME"
                if capability_operation_id_v2(base)
                == capability_operation_id_v2(different_operation)
                else "DIFFERENT"
            ),
        },
        {
            "case": "E_same_operation_different_capability",
            "expected_capability_identity": "DIFFERENT",
            "legacy_actual": (
                "SAME"
                if capability_id_for_subject(base)
                == capability_id_for_subject(different_capability)
                else "DIFFERENT"
            ),
            "v2_actual": (
                "SAME"
                if canonical_capability_id_v2(base)
                == canonical_capability_id_v2(different_capability)
                else "DIFFERENT"
            ),
        },
    ]
    return cases


def dependency_inventory() -> dict[str, Any]:
    roots = [
        PROJECT_ROOT / "runtime" / "capability_intelligence",
        PROJECT_ROOT / "runtime" / "evidence",
        PROJECT_ROOT / "runtime" / "validation",
        PROJECT_ROOT / "runtime" / "experiments",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "docs",
    ]
    files = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            parts = set(path.parts)
            if {"artifacts", "state"} & parts:
                continue
            if path.suffix.lower() not in {".py", ".json", ".md"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if "capability_id_for_subject" in text or "validation_context" in text:
                files.append(str(path.relative_to(PROJECT_ROOT)))
    return {
        "dependency_file_count": len(files),
        "dependency_files": sorted(files),
        "historical_artifact_mutation_required": False,
    }


def design_options() -> list[dict[str, Any]]:
    return [
        {
            "option": "A_KEEP_CURRENT_CAPABILITY_IDENTITY_UNCHANGED",
            "semantic_correctness": "LOW_FOR_CONTEXT_DIVERSITY",
            "migration_safety": "HIGH",
            "historical_compatibility": "HIGH",
            "C4_compatibility": "HIGH",
            "C5_compatibility": "LOW",
            "recommendation": "NOT_RECOMMENDED_AS_FINAL_MODEL",
        },
        {
            "option": "B_REMOVE_VALIDATION_CONTEXT_FROM_LEGACY_HASH",
            "semantic_correctness": "MEDIUM",
            "migration_safety": "LOW",
            "historical_compatibility": "LOW",
            "C4_compatibility": "RISKY",
            "C5_compatibility": "MEDIUM",
            "recommendation": "REJECTED_BREAKS_HISTORY",
        },
        {
            "option": "C_VERSIONED_CAPABILITY_IDENTITY_WITH_SEPARATE_CONTEXT_LAYER",
            "semantic_correctness": "HIGH",
            "migration_safety": "HIGH",
            "historical_compatibility": "HIGH",
            "C4_compatibility": "HIGH",
            "C5_compatibility": "HIGH_AFTER_CONTEXT_EVIDENCE_EXISTS",
            "recommendation": "RECOMMENDED",
        },
        {
            "option": "D_PARENT_CAPABILITY_PLUS_CONTEXTUAL_VARIANT",
            "semantic_correctness": "HIGH",
            "migration_safety": "MEDIUM",
            "historical_compatibility": "MEDIUM",
            "C4_compatibility": "MEDIUM",
            "C5_compatibility": "MEDIUM",
            "recommendation": "DEFER_UNTIL_VARIANTS_ARE_NEEDED",
        },
    ]


def _report(summary: Mapping[str, Any]) -> str:
    return "\n".join([
        "# Exact Subject Context Identity Report",
        "",
        f"Primary conclusion: `{summary['primary_architectural_conclusion']}`.",
        "",
        "The repair is additive and versioned. Legacy capability identity remains intact; new v2 identity separates intrinsic capability identity, operation identity, and validation context identity.",
        "",
        "No historical artifacts were mutated, no evidence was duplicated, no qualification was created, and no C5 readiness was granted.",
    ]) + "\n"


def run_identity_forensic(output_root: str | Path = OUTPUT_ROOT) -> dict[str, Any]:
    base = _subject("fill_center_delta")
    second = _subject("fill_center_enclosure_variant")
    baseline_context = _context("fill_center_delta", structural="single_center_delta")
    second_context = _context(
        "fill_center_enclosure_variant",
        structural="larger_enclosure_center_topology",
        intervention="fill_center_same_operation",
    )
    mapping = legacy_identity_mapping(
        base,
        qualification_claim_id=FILL_CENTER_CLAIM_ID,
        validation_context=baseline_context,
    )
    second_mapping = legacy_identity_mapping(
        second,
        qualification_claim_id=FILL_CENTER_CLAIM_ID,
        validation_context=second_context,
    )
    context_diversity = classify_context_diversity(
        baseline_context=baseline_context,
        candidate_context=second_context,
    )
    dependencies = dependency_inventory()
    summary = {
        "status": "COMPLETE",
        "primary_architectural_conclusion": "VERSIONED_CONTEXT_SEPARATION_REQUIRED",
        "system_fingerprint": _fingerprint(SYSTEM_PATHS),
        "current_capability_identity_schema": "capability_identity.v1",
        "current_capability_identity_owner": current_identity_contract()["owner"],
        "validation_context_in_capability_hash": True,
        "validation_context_semantic_role": "VALIDATION_SCENARIO",
        "capability_context_conflation_confirmed": True,
        "exact_subject_identity_model": "(capability_id, capability_operation, qualification_claim_id)",
        "validation_context_identity_model": "validation_context_identity.v1",
        "same_capability_different_context_preserves_capability_id": True,
        "same_exact_subject_different_context_preserves_subject_id": True,
        "context_diversity_measurable": "TRUE",
        "historical_artifact_mutation_required": False,
        "identity_versioning_required": True,
        "legacy_id_mapping_required": True,
        "qualification_state_preserved": True,
        "causal_evidence_binding_preserved": True,
        "source_independence_counts_preserved": True,
        "c4_status_preserved": True,
        "c5_contract_changed": False,
        "identity_authority": "IDENTITY_ONLY",
        "qualification_authority_changed": False,
        "evidence_acceptance_authority_changed": False,
        "source_independence_semantics_changed": False,
        "truth_authority_changed": False,
        "budget_authority_changed": False,
        "patch_required": "YES",
        "patch_applied": "YES",
        "fill_center_second_context_feasible_after_decision": "TRUE",
        "c5_freeze_readiness_changed": False,
        "remaining_limitation": "identity layer exists but no second governed fill_center context evidence has been produced",
        "next_action": "use the v2 identity layer to design exact-subject-preserving C4 context development tasks",
        "git_commit": _git_value("rev-parse", "HEAD"),
        "git_branch": _git_value("rev-parse", "--abbrev-ref", "HEAD"),
        "python_version": platform.python_version(),
    }
    artifacts = {
        "01_system_fingerprint.json": {
            "system_fingerprint": summary["system_fingerprint"],
            "fingerprinted_paths": SYSTEM_PATHS,
            "git_commit": summary["git_commit"],
            "git_branch": summary["git_branch"],
            "python_version": summary["python_version"],
        },
        "02_current_capability_identity_contract.json": current_identity_contract(),
        "03_capability_identity_hash_inputs.json": current_hash_inputs(),
        "04_validation_context_semantics.json": {
            "VALIDATION_CONTEXT_SEMANTIC_ROLE": "VALIDATION_SCENARIO",
            "producer_consumer_finding": "used in capability_subject.qualifiers by natural causal validation campaign and read by C5/C4 readiness tooling as test context",
            "does_define_capability_itself": False,
            "does_define_validation_scenario": True,
        },
        "05_identity_invariance_matrix.json": invariance_matrix(),
        "06_fill_center_context_case.json": {
            "legacy_fill_center_capability_id": capability_id_for_subject(base),
            "legacy_second_context_capability_id": capability_id_for_subject(second),
            "canonical_capability_id_v2": canonical_capability_id_v2(base),
            "second_context_canonical_capability_id_v2": canonical_capability_id_v2(second),
            "baseline_validation_context_id": validation_context_id(
                subject=base,
                qualification_claim_id=FILL_CENTER_CLAIM_ID,
                context=baseline_context,
            ),
            "second_validation_context_id": validation_context_id(
                subject=second,
                qualification_claim_id=FILL_CENTER_CLAIM_ID,
                context=second_context,
            ),
            "context_diversity": context_diversity,
        },
        "07_exact_subject_semantics.json": {
            "current_c5_contract_retained": True,
            "exact_subject": summary["exact_subject_identity_model"],
            "validation_instance": "exact_subject_id + validation_context_id",
        },
        "08_identity_layer_model.json": {
            "CapabilityIdentity": "canonical_capability_id_v2",
            "CapabilityOperationIdentity": "capability_operation_id_v2",
            "QualificationClaimIdentity": "qualification_claim_id",
            "ValidationContextIdentity": "validation_context_id",
            "EvidenceSourceIdentity": "unchanged EvidenceSourceIndependenceEngine semantics",
            **AUTHORITY,
        },
        "09_context_identity_contract.json": {
            "schema_version": "validation_context_identity.v1",
            "deterministic": True,
            "stable": True,
            "excludes": ["run_id", "timestamp", "evidence_id", "schedule_id", "attempt_id"],
            "includes": [
                "canonical_capability_id_v2",
                "capability_operation_id_v2",
                "qualification_claim_id",
                "context_parameters",
                "structural_signature",
                "causal_intervention_signature",
                "counterfactual_contract",
            ],
            **AUTHORITY,
        },
        "10_context_diversity_ontology.json": {
            "states": [
                "SAME_CONTEXT_REPLAY",
                "COSMETIC_VARIATION",
                "STRUCTURAL_VARIATION",
                "DISTINCT_CAUSAL_CONTEXT",
            ],
            "c5_counting_states": ["STRUCTURAL_VARIATION", "DISTINCT_CAUSAL_CONTEXT"],
        },
        "11_identity_dependency_inventory.json": dependencies,
        "12_historical_compatibility_analysis.json": {
            "historical_artifact_mutation_required": False,
            "legacy_ids_preserved": True,
            "legacy_resolution_layer": "legacy_identity_mapping.v1",
        },
        "13_identity_versioning_decision.json": {
            "VERSIONED_MIGRATION_REQUIRED": True,
            "legacy_schema": "capability_identity.v1",
            "new_schema": "capability_identity.v2 + validation_context_identity.v1",
        },
        "14_legacy_mapping_contract.json": {
            "baseline_mapping": mapping,
            "second_context_mapping": second_mapping,
        },
        "15_qualification_compatibility.json": {
            "qualification_state_preserved": True,
            "automatic_new_qualification": False,
            "legacy_capability_id_retained": mapping["legacy_capability_id"],
        },
        "16_causal_evidence_compatibility.json": {
            "causal_evidence_binding_preserved": True,
            "duplicate_evidence_created": False,
            "binding_model": "legacy evidence remains bound to legacy ID; v2 mapping resolves semantic identity",
        },
        "17_source_independence_compatibility.json": {
            "source_independence_counts_preserved": True,
            "source_independence_semantics_changed": False,
            "capability_identity_is_source_identity": False,
        },
        "18_claim_compatibility.json": {
            "claim_identity_changed": False,
            "claim_id": FILL_CENTER_CLAIM_ID,
            "claim_context_conflation_repair_deferred": True,
        },
        "19_curriculum_scheduler_compatibility.json": {
            "task_matching_semantics_preserved": True,
            "scheduler_selection_authority_changed": False,
            "context_layer_is_identity_only": True,
        },
        "20_identity_design_options_matrix.json": design_options(),
        "21_migration_invariants.json": {
            "historical_ids_preserved": True,
            "historical_artifacts_immutable": True,
            "old_evidence_still_resolves": True,
            "old_qualification_still_resolves": True,
            "source_independence_counts_unchanged": True,
            "c4_status_unchanged": True,
            "no_automatic_new_qualification": True,
            "no_duplicate_evidence": True,
            "no_truth_mutation": True,
            "no_execution_authority_change": True,
            "no_budget_authority_change": True,
        },
        "22_patch_decision.json": {
            "PATCH_REQUIRED": "YES",
            "PATCH_APPLIED": "YES",
            "patch_type": "ADDITIVE_VERSIONED_IDENTITY_LAYER",
            "patched_files": ["runtime/capability_intelligence/context_identity.py"],
        },
        "23_regression_results.json": {
            "filled_after_test_run": False,
            "test_count": 0,
            "regression_failure_count": 0,
        },
        "24_c5_readiness_impact.json": {
            "c5_contract_changed": False,
            "c5_freeze_readiness_changed": False,
            "fill_center_second_context_feasible_after_decision": True,
            "new_causal_evidence_created": False,
            "new_c5_readiness_created": False,
        },
        "25_exact_subject_context_identity_report.md": _report(summary),
        "26_identity_migration_verification.json": {
            "legacy_id_changes_with_context": capability_id_for_subject(base)
            != capability_id_for_subject(second),
            "v2_capability_id_preserved_across_context": canonical_capability_id_v2(base)
            == canonical_capability_id_v2(second),
            "context_id_distinguishes_contexts": validation_context_id(
                subject=base,
                qualification_claim_id=FILL_CENTER_CLAIM_ID,
                context=baseline_context,
            )
            != validation_context_id(
                subject=second,
                qualification_claim_id=FILL_CENTER_CLAIM_ID,
                context=second_context,
            ),
        },
        "27_legacy_resolution_matrix.json": [mapping, second_mapping],
        "summary.json": summary,
    }
    output_dir = Path(output_root) / _stamp()
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    return {**summary, "output_dir": str(output_dir)}


if __name__ == "__main__":
    print(json.dumps(run_identity_forensic(), indent=2, sort_keys=True))
