from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.capability_intelligence.integrated_capability_qualification import (
    capability_id_for_subject,
)
from runtime.experiments.c5_target_set_prequalification import (
    C5_MIN_CONTEXTS_PER_SUBJECT,
    C5_MIN_GLOBAL_SOURCE_LINEAGES,
    C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT,
    C5_MIN_TARGET_SUBJECTS,
    C5_MIN_UNIQUE_CAPABILITIES,
    C5_MIN_UNIQUE_OPERATIONS,
    run_prequalification,
)


PREQUALIFICATION_DIR = (
    PROJECT_ROOT
    / "runtime"
    / "artifacts"
    / "c5_target_set_prequalification"
    / "20260914_182743"
)
OUTPUT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "c4_breadth_expansion"

SYSTEM_PATHS = [
    "runtime/experiments/c4_breadth_expansion.py",
    "runtime/experiments/c5_target_set_prequalification.py",
    "runtime/experiments/c5_contract_design.py",
    "runtime/experiments/exact_subject_causal_replication.py",
    "runtime/experiments/natural_causal_validation_campaign.py",
    "runtime/capability_intelligence/integrated_capability_qualification.py",
    "runtime/epistemic/evidence_source_independence.py",
    "runtime/validation/causal_validation_evidence.py",
    "runtime/validation/validation_evidence_evaluator.py",
]


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any] | list[Any] | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
        return
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    json.loads(text)
    path.write_text(text + "\n", encoding="utf-8")


def _fingerprint(paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        path = PROJECT_ROOT / relative
        if path.exists():
            digest.update(relative.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _payload_fingerprint(payload: Mapping[str, Any]) -> str:
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


def context_identity_contract() -> dict[str, Any]:
    return {
        "contract": "exact_subject_preserving_context.v1",
        "exact_subject_identity": [
            "capability_id",
            "capability_operation",
            "qualification_claim_id",
        ],
        "allowed_context_variation": [
            "input_structure",
            "object_arrangement",
            "grid_geometry",
            "instance_parameters",
            "task_instance",
            "structural_configuration",
            "causal_challenge_context",
        ],
        "forbidden_context_variation": [
            "capability_id_change",
            "target_operation_change",
            "qualification_claim_semantics_change",
            "new_run_only",
            "new_evidence_id_only",
            "cosmetic_input_variation",
            "different_operation",
            "different_capability",
        ],
        "current_architectural_finding": (
            "capability_id_for_subject hashes qualifiers, including validation_context; "
            "therefore context variation inside capability_subject.qualifiers can change "
            "canonical capability identity unless a separate exact-subject-preserving "
            "context layer is introduced."
        ),
    }


def context_fingerprint(context: Mapping[str, Any]) -> str:
    payload = {
        "operation": context.get("operation"),
        "geometry": context.get("geometry"),
        "object_topology": context.get("object_topology"),
        "causal_challenge": context.get("causal_challenge"),
        "treatment": context.get("treatment"),
        "control": context.get("control"),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def classify_context_candidate(
    existing: Mapping[str, Any],
    proposed: Mapping[str, Any],
) -> dict[str, Any]:
    existing_subject = existing.get("capability_subject") or {}
    proposed_subject = proposed.get("capability_subject") or {}
    existing_id = existing.get("capability_id")
    computed_proposed_id = capability_id_for_subject(proposed_subject)
    semantic_existing = context_fingerprint({
        "operation": existing.get("operation"),
        "geometry": existing.get("observed_context_count"),
        "object_topology": existing_subject.get("qualifiers", {}).get(
            "validation_context"
        ),
        "causal_challenge": existing.get("operation"),
        "treatment": existing.get("causal_method"),
        "control": existing.get("causal_estimand"),
    })
    semantic_proposed = context_fingerprint(proposed)
    failures = []
    if computed_proposed_id != existing_id:
        failures.append("capability_id_not_preserved")
    if proposed.get("operation") != existing.get("operation"):
        failures.append("operation_not_preserved")
    if semantic_existing == semantic_proposed:
        failures.append("same_context_replay")
    if proposed.get("causal_variation") == "cosmetic":
        failures.append("cosmetic_variation_only")
    state = "DISTINCT_CAUSAL_CONTEXT" if not failures else "REJECTED"
    reason = "accepted_context_candidate" if not failures else ";".join(failures)
    return {
        "candidate_id": existing.get("candidate_id"),
        "proposed_context_id": proposed.get("context_id"),
        "semantic_context_fingerprint": semantic_proposed,
        "computed_proposed_capability_id": computed_proposed_id,
        "expected_capability_id": existing_id,
        "classification": state,
        "rejection_reasons": failures,
        "reason": reason,
    }


def development_priority(matrix: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in matrix:
        missing = list(item.get("missing_requirements", []))
        score = 0
        if item.get("capability_binding_state") == "BOUND":
            score += 3
        if item.get("claim_binding_state") == "BOUND":
            score += 3
        if item.get("operation_binding_state") == "BOUND":
            score += 3
        if item.get("causal_validation_reachable"):
            score += 3
        if item.get("counterfactual_state") == "COUNTERFACTUAL_READY":
            score += 3
        score += min(int(item.get("independent_causal_source_count") or 0), 2) * 2
        score += min(int(item.get("observed_context_count") or 0), 2)
        if item.get("operation") in {"outline_border", "fill_center"}:
            score += 1
        rows.append({
            "candidate_id": item.get("candidate_id"),
            "capability_id": item.get("capability_id"),
            "operation": item.get("operation"),
            "qualification_claim_id": item.get("qualification_claim_id"),
            "development_priority_score": score,
            "missing_requirements": missing,
            "rationale": (
                "ranked by identity/binding completeness, causal reachability, "
                "counterfactual readiness, existing source count, observed context count, "
                "and operation/capability breadth contribution"
            ),
        })
    return sorted(
        rows,
        key=lambda item: (-item["development_priority_score"], item["operation"]),
    )


def source_replication_readiness(matrix: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in matrix:
        count = int(item.get("independent_causal_source_count") or 0)
        if count >= C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT:
            state = "ALREADY_AVAILABLE"
        elif item.get("causal_validation_reachable"):
            state = "REQUIRES_NEW_VALIDATION_CONTEXT"
        else:
            state = "SOURCE_LINEAGE_NOT_CURRENTLY_AVAILABLE"
        rows.append({
            "candidate_id": item.get("candidate_id"),
            "capability_id": item.get("capability_id"),
            "operation": item.get("operation"),
            "current_independent_source_count": count,
            "second_source_readiness": state,
            "source_provenance_requirement": (
                "canonical source lineage must be independent of task/run/evidence/schedule/attempt ids"
            ),
        })
    return rows


def capability_breadth(matrix: list[Mapping[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in matrix:
        grouped[str(item.get("capability_id"))].append({
            "candidate_id": item.get("candidate_id"),
            "operation": item.get("operation"),
            "qualification_claim_id": item.get("qualification_claim_id"),
            "state": item.get("prequalification_state"),
        })
    plausible = {
        key: value
        for key, value in grouped.items()
        if key not in {"None", "", "UNKNOWN", "Not Available"}
    }
    return {
        "capability_id_to_candidate_exact_subjects": plausible,
        "plausible_capability_family_count": len(plausible),
        "capability_breadth_corpus_gap": len(plausible) < C5_MIN_UNIQUE_CAPABILITIES,
    }


def operation_breadth(matrix: list[Mapping[str, Any]]) -> dict[str, Any]:
    operations = sorted({
        str(item.get("operation"))
        for item in matrix
        if item.get("operation") not in {None, "", "UNKNOWN", "Not Available"}
    })
    return {
        "operations": operations,
        "unique_operation_count": len(operations),
        "operation_breadth_feasible_in_inventory": len(operations)
        >= C5_MIN_UNIQUE_OPERATIONS,
    }


def before_after_matrix(
    before: list[Mapping[str, Any]],
    after: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    after_by_id = {item.get("candidate_id"): item for item in after}
    rows = []
    for item in before:
        updated = after_by_id.get(item.get("candidate_id"), item)
        rows.append({
            "candidate_id": item.get("candidate_id"),
            "before_state": item.get("prequalification_state"),
            "after_state": updated.get("prequalification_state"),
            "new_contexts": [],
            "new_sources": [],
            "new_causal_evidence": [],
            "C4_change": "NO_CHANGE",
            "remaining_blockers": updated.get("missing_requirements", []),
        })
    return rows


def _proposed_contexts(matrix: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in matrix:
        if item.get("operation") == "fill_center":
            rows.append({
                "candidate_id": item.get("candidate_id"),
                "context_id": "fill_center_enclosure_variant_candidate",
                "operation": "fill_center",
                "geometry": "larger_odd_grid_with_single_center_cell",
                "object_topology": "closed_enclosure_with_empty_center",
                "causal_challenge": "same fill_center operation on different enclosure geometry",
                "treatment": "center cell filled by target operation",
                "control": "same grid with target operation disabled",
                "causal_variation": "structural",
                "capability_subject": {
                    **dict(item.get("capability_subject") or {}),
                    "qualifiers": {"validation_context": "fill_center_enclosure_variant"},
                },
            })
    return rows


def _report(summary: Mapping[str, Any], priority: list[Mapping[str, Any]]) -> str:
    lines = [
        "# C4 Breadth Expansion Report",
        "",
        f"Primary conclusion: `{summary['primary_conclusion']}`.",
        "",
        "No C5 target set was frozen and no C5 campaign was executed.",
        "",
        "## Development Priority",
    ]
    for index, item in enumerate(priority, start=1):
        lines.append(
            f"{index}. {item['candidate_id']} / {item['operation']} / "
            f"{item['capability_id']} score={item['development_priority_score']}"
        )
    lines.extend([
        "",
        "## Stop Reason",
        str(summary["stop_reason"]),
    ])
    return "\n".join(lines) + "\n"


def run_breadth_expansion(
    *,
    prequalification_dir: str | Path = PREQUALIFICATION_DIR,
    output_root: str | Path = OUTPUT_ROOT,
) -> dict[str, Any]:
    preq = Path(prequalification_dir)
    starting_summary = _read(preq / "summary.json")
    starting_matrix = _read(preq / "c5_candidate_readiness_matrix.json")
    contract = context_identity_contract()
    priority = development_priority(starting_matrix)
    proposed = _proposed_contexts(starting_matrix)
    duplicate_audit = []
    by_id = {item.get("candidate_id"): item for item in starting_matrix}
    for item in proposed:
        duplicate_audit.append(classify_context_candidate(by_id[item["candidate_id"]], item))
    accepted_contexts = [
        item for item in duplicate_audit if item.get("classification") == "DISTINCT_CAUSAL_CONTEXT"
    ]
    outline = next(
        (item for item in starting_matrix if item.get("operation") == "outline_border"),
        {},
    )
    replace = [
        item for item in starting_matrix if item.get("operation") == "replace_color"
    ]
    source_matrix = source_replication_readiness(starting_matrix)
    cap_breadth = capability_breadth(starting_matrix)
    op_breadth = operation_breadth(starting_matrix)
    reassessment_root = Path(output_root) / "_readiness_reassessment_tmp"
    reassessment = run_prequalification(output_root=reassessment_root)
    after_matrix = _read(Path(reassessment["output_dir"]) / "c5_candidate_readiness_matrix.json")
    comparison = before_after_matrix(starting_matrix, after_matrix)
    global_sources = sorted({
        str(source)
        for item in starting_matrix
        for source in item.get("canonical_source_identities", []) or []
        if source not in {None, "", "UNKNOWN", "Not Available"}
    })
    stop_reason = (
        "EXACT_SUBJECT_CONTEXT_MODEL_REQUIRED_BEFORE_NEW_CONTEXT_CAN_PRESERVE_CAPABILITY_ID"
    )
    summary = {
        "status": "COMPLETE",
        "primary_conclusion": (
            "C4_BREADTH_NOT_EXPANDED_STRUCTURAL_CONTEXT_IDENTITY_LIMITATION_FOUND"
        ),
        "system_fingerprint": _fingerprint(SYSTEM_PATHS),
        "git_commit": _git_value("rev-parse", "HEAD"),
        "git_branch": _git_value("rev-parse", "--abbrev-ref", "HEAD"),
        "python_version": platform.python_version(),
        "starting_c4_subject_count": starting_summary.get("current_c4_subject_count"),
        "starting_c5_eligible_count": starting_summary.get("c5_eligible_now_count"),
        "starting_c5_prequalified_count": starting_summary.get(
            "c5_prequalified_candidate_count"
        ),
        "total_candidate_count": len(starting_matrix),
        "fill_center_context_state_before": starting_summary.get(
            "fill_center_context_readiness"
        ),
        "fill_center_context_state_after": starting_summary.get(
            "fill_center_context_readiness"
        ),
        "new_context_candidate_count": len(proposed),
        "new_context_accepted_count": len(accepted_contexts),
        "duplicate_context_rejected_count": len(duplicate_audit)
        - len(accepted_contexts),
        "c4_development_attempt_count": 0,
        "causally_supported_new_evidence_count": 0,
        "new_independent_source_count": 0,
        "new_c4_subject_count": 0,
        "final_c4_subject_count": starting_summary.get("current_c4_subject_count"),
        "final_c5_eligible_count": reassessment.get("c5_eligible_now_count"),
        "final_c5_prequalified_count": reassessment.get(
            "c5_prequalified_candidate_count"
        ),
        "final_unique_capability_count": cap_breadth[
            "plausible_capability_family_count"
        ],
        "final_unique_operation_count": op_breadth["unique_operation_count"],
        "current_global_source_lineage_count": len(global_sources),
        "potential_global_source_lineage_count": len(global_sources),
        "global_source_diversity_feasible": len(global_sources)
        >= C5_MIN_GLOBAL_SOURCE_LINEAGES,
        "c5_freeze_readiness": reassessment["primary_freeze_readiness_decision"],
        "freeze_authorization_recommended": reassessment[
            "c5_freeze_authorization_recommended"
        ],
        "c5_target_set_frozen": False,
        "c5_campaign_executed": False,
        "c5_authorized_for_claim": False,
        "c5_development_tool_authority": "NONE",
        "c5_readiness_authority": "OBSERVATION_ONLY",
        "causal_authority_changed": False,
        "evidence_acceptance_authority_changed": False,
        "qualification_authority_changed": False,
        "source_independence_semantics_changed": False,
        "truth_authority_changed": False,
        "budget_authority_changed": False,
        "patch_required": "YES",
        "patch_applied": "NO",
        "stop_reason": stop_reason,
        "remaining_limitation": (
            "context diversity cannot currently be developed without risking "
            "capability_id mutation because validation_context is inside hashed qualifiers"
        ),
        "next_action": (
            "design an exact-subject-preserving context layer before creating C4 breadth tasks"
        ),
    }
    artifacts = {
        "01_system_fingerprint.json": {
            "system_fingerprint": summary["system_fingerprint"],
            "fingerprinted_paths": SYSTEM_PATHS,
            "git_commit": summary["git_commit"],
            "git_branch": summary["git_branch"],
            "python_version": summary["python_version"],
        },
        "02_starting_candidate_matrix.json": starting_matrix,
        "03_development_priority_matrix.json": priority,
        "04_context_identity_contract.json": contract,
        "05_fill_center_second_context_forensic.json": {
            "state_before": summary["fill_center_context_state_before"],
            "state_after": summary["fill_center_context_state_after"],
            "proposed_contexts": proposed,
            "duplicate_audit": duplicate_audit,
            "result": "NO_CONTEXT_CREATED_CAPABILITY_ID_NOT_PRESERVED_BY_CURRENT_MODEL",
        },
        "06_outline_border_readiness.json": {
            "candidate": outline,
            "OUTLINE_BORDER_C4_READINESS": "NEEDS_SECOND_CONTEXT",
            "also_needs": ["NEEDS_SECOND_SOURCE"],
        },
        "07_replace_color_subject_analysis.json": {
            "subjects": replace,
            "merge_decision": "DO_NOT_MERGE_DISTINCT_EXACT_SUBJECTS",
            "negative_case_preserved": True,
        },
        "08_context_development_matrix.json": proposed,
        "09_source_replication_readiness.json": source_matrix,
        "10_new_context_duplicate_audit.json": duplicate_audit,
        "11_c4_development_attempts.json": [],
        "12_causal_evidence_results.json": [],
        "13_source_lineage_matrix.json": {
            "current_global_source_lineages": global_sources,
            "potential_global_source_lineages": global_sources,
        },
        "14_c4_subject_status_after.json": {
            "starting_c4_subject_count": summary["starting_c4_subject_count"],
            "final_c4_subject_count": summary["final_c4_subject_count"],
            "new_c4_subject_count": summary["new_c4_subject_count"],
        },
        "15_c5_prequalification_reassessment.json": {
            "summary": reassessment,
            "before_after_matrix": comparison,
        },
        "16_global_source_diversity.json": {
            "current_global_source_lineage_count": len(global_sources),
            "potential_global_source_lineage_count": len(global_sources),
            "global_source_diversity_feasible": summary[
                "global_source_diversity_feasible"
            ],
        },
        "17_authority_audit.json": {
            "c5_development_tool_authority": "NONE",
            "c5_readiness_authority": "OBSERVATION_ONLY",
            "causal_authority_changed": False,
            "evidence_acceptance_authority_changed": False,
            "qualification_authority_changed": False,
            "source_independence_semantics_changed": False,
            "truth_authority_changed": False,
            "budget_authority_changed": False,
            "cognitive_runtime_consumer_count": 0,
        },
        "18_regression_results.json": {
            "filled_after_test_run": False,
            "test_count": 0,
            "regression_failure_count": 0,
        },
        "19_stop_decision.json": {
            "stop_reason": stop_reason,
            "development_stop_rule": "E_next_progress_step_requires_separate_architectural_feature",
        },
        "20_c4_breadth_expansion_report.md": _report(summary, priority),
    }
    output_dir = Path(output_root) / _stamp()
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    _write(output_dir / "summary.json", summary)
    return {**summary, "output_dir": str(output_dir)}


if __name__ == "__main__":
    print(json.dumps(run_breadth_expansion(), indent=2, sort_keys=True))
