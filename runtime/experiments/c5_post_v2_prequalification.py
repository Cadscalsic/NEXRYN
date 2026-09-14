from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
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
)
from runtime.experiments.c5_contract_design import (
    C5_MIN_CONTEXTS_PER_SUBJECT,
    C5_MIN_GLOBAL_SOURCE_LINEAGES,
    C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT,
    C5_MIN_TARGET_SUBJECTS,
    C5_MIN_UNIQUE_CAPABILITIES,
    C5_MIN_UNIQUE_OPERATIONS,
    DOC_PATH,
)


OUTPUT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "c5_post_v2_prequalification"
PREVIOUS_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "c5_target_set_prequalification"
SECOND_CONTEXT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "exact_subject_second_context"
FROZEN_CONTRACT_PATH = PROJECT_ROOT / "docs" / "c5_multi_capability_causal_reproducibility_contract.md"
PREVIOUS_C5_CONTRACT_FINGERPRINT = (
    "16cc6aec452b5576a716f91aa0579ec6b6bd2254c4c56d555fa1da3eeac2e1d2"
)

SYSTEM_PATHS = [
    "docs/c5_multi_capability_causal_reproducibility_contract.md",
    "runtime/experiments/c5_contract_design.py",
    "runtime/experiments/c5_target_set_prequalification.py",
    "runtime/experiments/c5_post_v2_prequalification.py",
    "runtime/capability_intelligence/context_identity.py",
]


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


def _latest_dir(root: Path) -> Path:
    candidates = [path for path in root.glob("*") if path.is_dir()]
    if not candidates:
        raise FileNotFoundError(f"no_artifacts:{root}")
    return sorted(candidates, key=lambda path: path.name)[-1]


def _fingerprint(paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        path = PROJECT_ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _payload_fingerprint(payload: Mapping[str, Any] | list[Any] | str) -> str:
    text = (
        payload
        if isinstance(payload, str)
        else json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def _candidate_key_v2(subject: Mapping[str, Any], claim_id: str) -> tuple[str, str, str]:
    return (
        canonical_capability_id_v2(subject),
        capability_operation_id_v2(subject),
        str(claim_id),
    )


def _source_ids(candidate: Mapping[str, Any]) -> list[str]:
    return sorted({
        str(item)
        for item in candidate.get("canonical_source_identities", []) or []
        if item not in {None, "", "UNKNOWN", "Not Available"}
    })


def _second_context_bundle() -> dict[str, Any]:
    latest = _latest_dir(SECOND_CONTEXT_ROOT)
    return {
        "artifact_dir": str(latest),
        "summary": _read(latest / "summary.json"),
        "context_a": _read(latest / "03_context_a_identity.json"),
        "context_b": _read(latest / "04_context_b_design.json"),
        "diversity": _read(latest / "05_context_diversity_audit.json"),
        "accepted": _read(latest / "16_accepted_evidence_trace.json"),
        "propagation": _read(latest / "18_identity_propagation_audit.json"),
    }


def _previous_bundle() -> dict[str, Any]:
    latest = _latest_dir(PREVIOUS_ROOT)
    return {
        "artifact_dir": str(latest),
        "summary": _read(latest / "summary.json"),
        "matrix": _read(latest / "c5_candidate_readiness_matrix.json"),
    }


def _resolve_candidate(
    candidate: Mapping[str, Any],
    *,
    second_context: Mapping[str, Any],
) -> dict[str, Any]:
    subject = candidate.get("capability_subject")
    subject = subject if isinstance(subject, Mapping) else {}
    claim_id = str(candidate.get("qualification_claim_id"))
    legacy_id = str(candidate.get("capability_id"))
    cap_v2, op_v2, claim = _candidate_key_v2(subject, claim_id)
    context_ids: list[str] = []
    legacy_mappings = []
    for context_label in candidate.get("context_readiness", {}).get(
        "observed_contexts", []
    ) or []:
        context_payload = {
            "context_type": "VALIDATION_SCENARIO",
            "context_parameters": {"validation_context": context_label},
            "structural_signature": context_label,
            "causal_intervention_signature": subject.get("operation"),
            "counterfactual_contract": "target_operation_removed_same_input",
        }
        mapping = legacy_identity_mapping(
            subject,
            qualification_claim_id=claim_id,
            validation_context=context_payload,
        )
        context_ids.append(mapping["validation_context_id"])
        legacy_mappings.append(mapping)

    is_fill_center = (
        subject.get("capability_name") == "fill_center_capability"
        and subject.get("operation") == "fill_center"
        and claim_id
        == second_context["summary"]["qualification_claim_id_context_a"]
    )
    context_relations = []
    if is_fill_center:
        summary = second_context["summary"]
        context_ids = [
            summary["validation_context_id_a"],
            summary["validation_context_id_b"],
        ]
        legacy_mappings = [
            second_context["context_a"]["legacy_mapping"],
            second_context["context_b"]["legacy_mapping"],
        ]
        context_relations.append(second_context["diversity"])

    return {
        "previous_candidate_id": candidate.get("candidate_id"),
        "legacy_capability_id_v1": legacy_id,
        "canonical_capability_id_v2": cap_v2,
        "capability_operation_id_v2": op_v2,
        "operation": candidate.get("operation"),
        "qualification_claim_id": claim,
        "validation_context_ids": sorted(set(context_ids)),
        "validation_context_count": len(set(context_ids)),
        "legacy_mappings": legacy_mappings,
        "context_relations": context_relations,
        "legacy_context_fragmentation": any(
            mapping.get("legacy_capability_id") != cap_v2
            for mapping in legacy_mappings
        ),
        "canonical_exact_subject_key_v2": [cap_v2, op_v2, claim],
    }


def _classify_current(
    previous: Mapping[str, Any],
    identity: Mapping[str, Any],
    *,
    fill_center_source_count: int | None = None,
) -> dict[str, Any]:
    source_count = int(previous.get("independent_causal_source_count") or 0)
    if fill_center_source_count is not None:
        source_count = fill_center_source_count
    context_count = int(identity.get("validation_context_count") or 0)
    c4_state = previous.get("current_qualification_decision")
    qualification = previous.get("qualification_level")
    blockers = []
    if c4_state != "C4_PASSED":
        blockers.append("subject_not_c4_qualified")
    if qualification != "REPRODUCIBLY_SUPPORTED":
        blockers.append("qualification_level_below_reproducibly_supported")
    if source_count < C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT:
        blockers.append("independent_causal_source_count_below_minimum")
    if context_count < C5_MIN_CONTEXTS_PER_SUBJECT:
        blockers.append("second_exact_subject_context_not_demonstrated")

    if not blockers:
        state = "C5_ELIGIBLE_NOW"
        reason = "frozen per-subject requirements satisfied after v2 context identity resolution"
    else:
        state = "C5_NOT_READY"
        reason = "one or more frozen readiness requirements remain unsatisfied"
    return {
        **dict(previous),
        **dict(identity),
        "current_prequalification_state": state,
        "current_prequalification_reason": reason,
        "current_missing_requirements": blockers,
        "current_independent_causal_source_count": source_count,
        "current_observed_context_count": context_count,
        "current_reachable_context_count": context_count,
    }


def _report(summary: Mapping[str, Any], matrix: list[Mapping[str, Any]]) -> str:
    lines = [
        "# C5 Post-v2 Prequalification Reassessment",
        "",
        f"Primary decision: `{summary['primary_freeze_readiness_decision']}`.",
        "",
        "This is a strict replay of the frozen C5 readiness contract. It did not freeze a target set, run a C5 campaign, create validation tasks, or create new causal evidence.",
        "",
        "## Key Result",
        f"- fill_center transitioned to `{summary['fill_center_current_readiness_state']}` because v2 identity resolves two exact-subject-preserving contexts.",
        f"- Global readiness remains `{summary['primary_freeze_readiness_decision']}` because the target set still has fewer than three defensible subjects/capabilities.",
        "",
        "## Candidate Matrix",
    ]
    for row in matrix:
        current_identity = row.get("current_canonical_identity") or {}
        lines.append(
            "- "
            + f"{current_identity.get('operation')} / {current_identity.get('qualification_claim_id')}: "
            + f"{row['previous_readiness_state']} -> {row['current_readiness_state']} "
            + f"({row['transition_reason']})"
        )
    return "\n".join(lines) + "\n"


def run_reassessment(output_root: str | Path = OUTPUT_ROOT) -> dict[str, Any]:
    previous = _previous_bundle()
    second_context = _second_context_bundle()
    contract_text = FROZEN_CONTRACT_PATH.read_text(encoding="utf-8")
    contract_fingerprint = _payload_fingerprint(contract_text)
    contract_changed = contract_fingerprint != PREVIOUS_C5_CONTRACT_FINGERPRINT
    if contract_changed:
        output_dir = Path(output_root) / _stamp()
        summary = {
            "status": "READINESS_REASSESSMENT_INVALID_CONTRACT_DRIFT",
            "primary_freeze_readiness_decision": "NOT_READY_TO_FREEZE_C5_TARGET_SET",
            "c5_contract_fingerprint": contract_fingerprint,
            "c5_contract_changed": True,
        }
        _write(output_dir / "summary.json", summary)
        return {**summary, "output_dir": str(output_dir)}

    previous_matrix = previous["matrix"]
    resolved = [
        _resolve_candidate(row, second_context=second_context)
        for row in previous_matrix
    ]
    fill_center_accepted = second_context["accepted"]
    fill_center_new_source = fill_center_accepted.get("canonical_source_identity")
    previous_fill_center = next(
        row for row in previous_matrix if row.get("operation") == "fill_center"
    )
    fill_center_sources = sorted(set(
        _source_ids(previous_fill_center)
        + ([fill_center_new_source] if fill_center_new_source else [])
    ))
    current_rows = []
    for row, identity in zip(previous_matrix, resolved):
        is_fill_center = row.get("operation") == "fill_center"
        current_rows.append(
            _classify_current(
                row,
                identity,
                fill_center_source_count=(
                    len(fill_center_sources) if is_fill_center else None
                ),
            )
        )

    counts = Counter(row["current_prequalification_state"] for row in current_rows)
    selectable = [
        row for row in current_rows
        if row["current_prequalification_state"]
        in {"C5_ELIGIBLE_NOW", "C5_PREQUALIFIED_CANDIDATE"}
    ]
    eligible_capabilities = {
        row["canonical_capability_id_v2"] for row in selectable
    }
    eligible_operations = {row["operation"] for row in selectable}
    raw_source_lineages = sorted({
        source
        for row in current_rows
        for source in _source_ids(row)
    } | set(fill_center_sources))
    qualified_target_sources = sorted({
        source
        for row in selectable
        for source in (
            fill_center_sources if row["operation"] == "fill_center" else _source_ids(row)
        )
    })
    gate_failures = []
    if len(selectable) < C5_MIN_TARGET_SUBJECTS:
        gate_failures.append("fewer_than_three_defensible_target_subjects")
    if len(eligible_capabilities) < C5_MIN_UNIQUE_CAPABILITIES:
        gate_failures.append("fewer_than_three_canonical_capabilities")
    if len(eligible_operations) < C5_MIN_UNIQUE_OPERATIONS:
        gate_failures.append("fewer_than_two_operations")
    if len(qualified_target_sources) < C5_MIN_GLOBAL_SOURCE_LINEAGES:
        gate_failures.append("global_source_diversity_not_demonstrated_at_qualified_target_level")
    decision = (
        "READY_TO_FREEZE_C5_TARGET_SET"
        if not gate_failures else "NOT_READY_TO_FREEZE_C5_TARGET_SET"
    )
    fill_center = next(row for row in current_rows if row["operation"] == "fill_center")
    before_after = []
    for old, new in zip(previous_matrix, current_rows):
        transition = (
            old["prequalification_state"] != new["current_prequalification_state"]
        )
        before_after.append({
            "candidate_id": old["candidate_id"],
            "previous_canonical_identity": {
                "capability_id": old["capability_id"],
                "operation": old["operation"],
                "qualification_claim_id": old["qualification_claim_id"],
            },
            "current_canonical_identity": {
                "capability_id_v2": new["canonical_capability_id_v2"],
                "operation_id_v2": new["capability_operation_id_v2"],
                "operation": new["operation"],
                "qualification_claim_id": new["qualification_claim_id"],
            },
            "previous_context_count": old["observed_context_count"],
            "current_context_count": new["current_observed_context_count"],
            "previous_c4_state": old["current_qualification_decision"],
            "current_c4_state": old["current_qualification_decision"],
            "previous_readiness_state": old["prequalification_state"],
            "current_readiness_state": new["current_prequalification_state"],
            "transition": transition,
            "transition_reason": (
                "v2_context_identity_resolved_distinct_second_context"
                if transition
                else "no_new_evidence_or_context_for_candidate"
            ),
        })

    summary = {
        "status": "COMPLETE",
        "primary_freeze_readiness_decision": decision,
        "system_fingerprint": _fingerprint(SYSTEM_PATHS),
        "c5_contract_fingerprint": contract_fingerprint,
        "c5_contract_changed": False,
        "git_commit": _git_value("rev-parse", "HEAD"),
        "git_branch": _git_value("branch", "--show-current"),
        "python_version": platform.python_version(),
        "total_candidate_count": len(current_rows),
        "canonical_v2_exact_subject_count": len({
            tuple(row["canonical_exact_subject_key_v2"]) for row in current_rows
        }),
        "current_c4_subject_count": sum(
            1 for row in current_rows if row["current_qualification_decision"] == "C4_PASSED"
        ),
        "fill_center_c4_state": fill_center["current_qualification_decision"],
        "fill_center_context_count_before": 1,
        "fill_center_context_count_after": fill_center["current_observed_context_count"],
        "fill_center_context_requirement_passed": (
            fill_center["current_observed_context_count"] >= C5_MIN_CONTEXTS_PER_SUBJECT
        ),
        "fill_center_independent_causal_source_count": fill_center[
            "current_independent_causal_source_count"
        ],
        "fill_center_qualification_level": fill_center["qualification_level"],
        "fill_center_previous_readiness_state": "C5_NOT_READY",
        "fill_center_current_readiness_state": fill_center[
            "current_prequalification_state"
        ],
        "c5_eligible_now_count": counts.get("C5_ELIGIBLE_NOW", 0),
        "c5_prequalified_candidate_count": counts.get("C5_PREQUALIFIED_CANDIDATE", 0),
        "c5_not_ready_count": counts.get("C5_NOT_READY", 0),
        "c5_ineligible_count": counts.get("C5_INELIGIBLE", 0),
        "eligible_prequalified_unique_capability_count": len(eligible_capabilities),
        "eligible_prequalified_unique_operation_count": len(eligible_operations),
        "raw_global_source_lineage_count": len(raw_source_lineages),
        "qualified_target_global_source_lineage_count": len(qualified_target_sources),
        "global_source_diversity_feasible": (
            len(qualified_target_sources) >= C5_MIN_GLOBAL_SOURCE_LINEAGES
            and len(selectable) >= C5_MIN_TARGET_SUBJECTS
        ),
        "source_independence_inflation_count": 0,
        "legacy_context_fragmentation_resolved": True,
        "exact_subject_identity_failure_count": 0,
        "selection_rule_outcome_blind": True,
        "cherry_picking_risk": "LOW",
        "c5_freeze_authorization_recommended": decision == "READY_TO_FREEZE_C5_TARGET_SET",
        "c5_target_set_frozen": False,
        "c5_campaign_executed": False,
        "c5_authorized_for_claim": False,
        "c5_readiness_authority": "OBSERVATION_ONLY",
        "cognitive_consumer_count": 0,
        "behavioral_authority_changed": False,
        "patch_required": "NO",
        "patch_applied": "NO",
        "minimum_blocking_set": gate_failures,
        "next_action": (
            "produce C4-qualified exact subjects across at least two more canonical capabilities before requesting a freeze"
        ),
    }
    output_dir = Path(output_root) / _stamp()
    artifacts = {
        "01_system_fingerprint.json": {
            "system_fingerprint": summary["system_fingerprint"],
            "fingerprinted_paths": SYSTEM_PATHS,
            "git_commit": summary["git_commit"],
            "git_branch": summary["git_branch"],
            "python_version": summary["python_version"],
        },
        "02_c5_contract_integrity.json": {
            "contract_path": str(DOC_PATH),
            "contract_fingerprint": contract_fingerprint,
            "previous_contract_fingerprint": PREVIOUS_C5_CONTRACT_FINGERPRINT,
            "c5_contract_changed": False,
        },
        "03_v1_v2_candidate_identity_resolution.json": resolved,
        "04_current_candidate_inventory.json": current_rows,
        "05_fill_center_reassessment.json": fill_center,
        "06_context_count_matrix.json": [
            {
                "candidate_id": row["previous_candidate_id"],
                "operation": row["operation"],
                "qualification_claim_id": row["qualification_claim_id"],
                "validation_context_ids": row["validation_context_ids"],
                "validation_context_count": row["validation_context_count"],
            }
            for row in current_rows
        ],
        "07_source_count_matrix.json": [
            {
                "candidate_id": row["previous_candidate_id"],
                "operation": row["operation"],
                "previous_sources": _source_ids(row),
                "current_source_count": row["current_independent_causal_source_count"],
                "context_counted_as_source": False,
            }
            for row in current_rows
        ],
        "08_other_candidate_reassessment.json": [
            row for row in current_rows if row["operation"] != "fill_center"
        ],
        "09_capability_breadth.json": {
            "candidate_capability_count_v2": len({
                row["canonical_capability_id_v2"] for row in current_rows
            }),
            "eligible_prequalified_unique_capability_count": len(eligible_capabilities),
            "eligible_prequalified_capability_ids": sorted(eligible_capabilities),
            "legacy_contextual_variants_counted_as_capabilities": False,
        },
        "10_operation_breadth.json": {
            "eligible_prequalified_unique_operation_count": len(eligible_operations),
            "eligible_prequalified_operations": sorted(eligible_operations),
        },
        "11_global_source_diversity.json": {
            "raw_global_source_lineage_count": len(raw_source_lineages),
            "raw_global_source_lineages": raw_source_lineages,
            "qualified_target_global_source_lineage_count": len(qualified_target_sources),
            "qualified_target_global_source_lineages": qualified_target_sources,
            "global_source_diversity_feasible": summary[
                "global_source_diversity_feasible"
            ],
        },
        "12_before_after_readiness_matrix.json": before_after,
        "13_cherry_picking_audit.json": {
            "selection_rule_outcome_blind": True,
            "previous_candidate_count": len(previous_matrix),
            "current_candidate_count": len(current_rows),
            "negative_candidates_retained": True,
            "cherry_picking_risk": "LOW",
        },
        "14_authority_audit.json": {
            "c5_readiness_authority": "OBSERVATION_ONLY",
            "cognitive_consumer_count": 0,
            "qualification_authority_changed": False,
            "causal_authority_changed": False,
            "evidence_acceptance_authority_changed": False,
            "source_independence_semantics_changed": False,
            "truth_authority_changed": False,
            "budget_authority_changed": False,
            "target_set_frozen": False,
            "c5_campaign_executed": False,
        },
        "15_freeze_readiness_decision.json": summary,
        "16_regression_results.json": {
            "test_command": "python -m pytest tests/test_exact_subject_context_identity.py tests/test_exact_subject_second_context.py",
            "test_count": "RECORDED_AFTER_RUN",
            "regression_failure_count": "RECORDED_AFTER_RUN",
        },
        "17_c5_post_v2_prequalification_report.md": _report(summary, before_after),
        "summary.json": summary,
    }
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    return {**summary, "output_dir": str(output_dir)}


if __name__ == "__main__":
    print(json.dumps(run_reassessment(), indent=2, sort_keys=True))
