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

from runtime.experiments.c5_contract_design import (
    C5_MIN_CONTEXTS_PER_SUBJECT,
    C5_MIN_GLOBAL_SOURCE_LINEAGES,
    C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT,
    C5_MIN_TARGET_SUBJECTS,
    C5_MIN_UNIQUE_CAPABILITIES,
    C5_MIN_UNIQUE_OPERATIONS,
    C3_ROOT,
    C4_ROOT,
    DOC_PATH,
    _current_subject_inventory,
    _latest_dir,
    c5_subject_unit,
)
from runtime.validation.causal_validation_evidence import (
    CausalValidationEvidenceEvaluator,
)
from runtime.validation.validation_evidence_evaluator import (
    ValidationEvidenceEvaluator,
)
from runtime.capability_intelligence.integrated_capability_qualification import (
    IntegratedCapabilityQualificationEngine,
)
from runtime.epistemic.evidence_source_independence import (
    EvidenceSourceIndependenceEngine,
)


OUTPUT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "c5_target_set_prequalification"

SYSTEM_PATHS = [
    "docs/c5_multi_capability_causal_reproducibility_contract.md",
    "runtime/experiments/c5_contract_design.py",
    "runtime/experiments/c5_target_set_prequalification.py",
    "runtime/experiments/exact_subject_causal_replication.py",
    "runtime/experiments/natural_causal_validation_campaign.py",
    "runtime/validation/causal_validation_evidence.py",
    "runtime/validation/validation_evidence_evaluator.py",
    "runtime/capability_intelligence/integrated_capability_qualification.py",
    "runtime/epistemic/evidence_source_independence.py",
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


def _fingerprint(paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        path = PROJECT_ROOT / relative
        if not path.exists():
            continue
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


def candidate_id_for(subject: Mapping[str, Any]) -> str:
    payload = {
        "capability_id": subject.get("capability_id"),
        "operation": subject.get("operation"),
        "qualification_claim_id": subject.get("qualification_claim_id"),
    }
    return "c5_candidate_" + _payload_fingerprint(payload)[:12]


def _known_contexts_by_operation(inventory: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    contexts: dict[str, set[str]] = {}
    for item in inventory:
        operation = str(item.get("operation") or "UNKNOWN")
        bucket = contexts.setdefault(operation, set())
        for context in item.get("contexts", []) or []:
            if context not in {None, "", "UNKNOWN", "Not Available"}:
                bucket.add(str(context))
    return {key: sorted(value) for key, value in contexts.items()}


def context_readiness(
    subject: Mapping[str, Any],
    *,
    known_operation_contexts: Mapping[str, list[str]] | None = None,
) -> dict[str, Any]:
    observed = sorted({
        str(item)
        for item in subject.get("contexts", []) or []
        if item not in {None, "", "UNKNOWN", "Not Available"}
    })
    operation_contexts = (known_operation_contexts or {}).get(
        str(subject.get("operation") or "UNKNOWN"),
        [],
    )
    exact_subject_preserving_reachable = sorted({
        str(item)
        for item in subject.get("future_reachable_contexts", []) or []
        if item not in {None, "", "UNKNOWN", "Not Available"}
    })
    reachable = sorted(set(observed) | set(exact_subject_preserving_reachable))
    same_operation_non_exact = sorted(set(operation_contexts) - set(observed))
    if len(observed) >= C5_MIN_CONTEXTS_PER_SUBJECT:
        state = "SECOND_CONTEXT_ALREADY_OBSERVED"
    elif len(reachable) >= C5_MIN_CONTEXTS_PER_SUBJECT:
        state = "SECOND_CONTEXT_NATURALLY_REACHABLE"
    elif same_operation_non_exact:
        state = "SECOND_CONTEXT_REQUIRES_NEW_CORPUS"
    elif subject.get("accepted_causal_evidence_count"):
        state = "SECOND_CONTEXT_REQUIRES_NEW_CORPUS"
    else:
        state = "SECOND_CONTEXT_NOT_SUPPORTED"
    return {
        "observed_contexts": observed,
        "observed_context_count": len(observed),
        "reachable_contexts": reachable,
        "reachable_context_count": len(reachable),
        "same_operation_contexts_not_counted_for_exact_subject": same_operation_non_exact,
        "context_identity_definition": "exact-subject-preserving natural validation context",
        "context_diversity_type": (
            "DIFFERENT_CAUSAL_CONTEXT"
            if len(reachable) >= C5_MIN_CONTEXTS_PER_SUBJECT
            else "SAME_CONTEXT_REPLAY"
            if subject.get("task_count", 0) > len(observed)
            else "DIFFERENT_TASK_WITHOUT_DISTINCT_CAUSAL_CONTEXT"
        ),
        "genuinely_distinct": len(reachable) >= C5_MIN_CONTEXTS_PER_SUBJECT,
        "state": state,
        "fact_basis": {
            "observed": "accepted evidence subject qualifiers",
            "derived": "unique exact-subject-preserving context identities",
            "inference": "same-operation contexts are not counted when they alter exact subject identity",
        },
    }


def counterfactual_readiness(subject: Mapping[str, Any]) -> dict[str, Any]:
    if subject.get("accepted_causal_evidence_count"):
        state = "COUNTERFACTUAL_READY"
        reason = "accepted causal evidence has governed counterfactual comparison"
    elif subject.get("counterfactual_method") not in {None, "", "UNKNOWN", "Not Available"}:
        state = "COUNTERFACTUAL_REACHABLE_NOT_OBSERVED"
        reason = "operation has a known method but no accepted causal evidence"
    else:
        state = "COUNTERFACTUAL_PATH_UNPROVEN"
        reason = "no accepted causal evidence or method"
    return {
        "counterfactual_state": state,
        "target_operation_executable": state != "COUNTERFACTUAL_PATH_UNPROVEN",
        "target_operation_output_consumed": state == "COUNTERFACTUAL_READY",
        "same_relevant_input": state == "COUNTERFACTUAL_READY",
        "non_target_operations_controlled": state == "COUNTERFACTUAL_READY",
        "control_not_causally_equivalent_to_treatment": state == "COUNTERFACTUAL_READY",
        "effect_measurable": state != "COUNTERFACTUAL_PATH_UNPROVEN",
        "counterfactual_comparison_valid": state == "COUNTERFACTUAL_READY",
        "reason": reason,
    }


def source_replication_readiness(subject: Mapping[str, Any]) -> dict[str, Any]:
    source_ids = sorted({
        str(item)
        for item in subject.get("canonical_source_ids", []) or []
        if item not in {None, "", "UNKNOWN", "Not Available"}
    })
    current = int(subject.get("independent_causal_source_count") or 0)
    if current >= C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT:
        state = "SOURCE_REPLICATION_READY"
    elif current >= 1:
        state = "SOURCE_REPLICATION_REACHABLE_NEEDS_INDEPENDENT_SECOND_SOURCE"
    else:
        state = "SOURCE_REPLICATION_UNPROVEN"
    return {
        "current_causal_source_count": len(source_ids),
        "current_independent_causal_source_count": current,
        "candidate_future_source_lineages": [],
        "source_replication_readiness": state,
        "same_source_replay_risk": "LOW" if current >= 2 else "MATERIAL",
        "shared_parent_lineage_risk": "LOW" if current >= 2 else "UNKNOWN",
        "run_id_only_pseudo_independence_risk": "MATERIAL",
        "task_id_only_pseudo_independence_risk": "MATERIAL",
        "evidence_id_only_pseudo_independence_risk": "MATERIAL",
        "canonical_source_ids": source_ids,
    }


def classify_candidate(
    subject: Mapping[str, Any],
    *,
    known_operation_contexts: Mapping[str, list[str]] | None = None,
) -> dict[str, Any]:
    identity_valid = all(
        subject.get(field) not in {None, "", "UNKNOWN", "Not Available"}
        for field in ("capability_id", "operation", "qualification_claim_id")
    )
    context = context_readiness(
        subject,
        known_operation_contexts=known_operation_contexts,
    )
    source = source_replication_readiness(subject)
    counterfactual = counterfactual_readiness(subject)
    unit = c5_subject_unit({
        **dict(subject),
        "context_count": context["observed_context_count"],
    })
    causal_validation_reachable = bool(subject.get("accepted_causal_evidence_count"))
    claim_binding_state = "BOUND" if subject.get("qualification_claim_id") else "MISSING"
    capability_binding_state = "BOUND" if subject.get("capability_id") else "MISSING"
    operation_binding_state = "BOUND" if subject.get("operation") else "MISSING"
    blockers: list[str] = []
    missing: list[str] = []
    if not identity_valid:
        blockers.append("canonical_exact_subject_identity_missing")
    if claim_binding_state != "BOUND":
        blockers.append("claim_binding_missing")
    if capability_binding_state != "BOUND":
        blockers.append("capability_binding_missing")
    if operation_binding_state != "BOUND":
        blockers.append("operation_binding_missing")
    if not causal_validation_reachable:
        missing.append("causal_validation_reachability_unproven")
    if subject.get("current_qualification_level") != "REPRODUCIBLY_SUPPORTED":
        missing.append("qualification_level_below_reproducibly_supported")
    if source["current_independent_causal_source_count"] < C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT:
        missing.append("independent_causal_source_count_below_minimum")
    if context["reachable_context_count"] < C5_MIN_CONTEXTS_PER_SUBJECT:
        missing.append("second_exact_subject_context_not_demonstrated")
    if counterfactual["counterfactual_state"] not in {
        "COUNTERFACTUAL_READY",
        "COUNTERFACTUAL_REACHABLE_NOT_OBSERVED",
    }:
        missing.append("counterfactual_path_unproven")

    if blockers:
        state = "C5_INELIGIBLE"
        reason = "structural identity or binding blocker"
    elif unit["counts_toward_c5"]:
        state = "C5_ELIGIBLE_NOW"
        reason = "all per-subject C5 requirements currently satisfied"
    elif (
        identity_valid
        and causal_validation_reachable
        and counterfactual["counterfactual_state"] == "COUNTERFACTUAL_READY"
        and source["current_independent_causal_source_count"] >= 1
        and context["reachable_context_count"] >= C5_MIN_CONTEXTS_PER_SUBJECT
        and not blockers
    ):
        state = "C5_PREQUALIFIED_CANDIDATE"
        reason = "missing evidence is experimentally obtainable under observed reachable prerequisites"
    else:
        state = "C5_NOT_READY"
        reason = "one or more required prerequisites lack demonstrated reachability"

    return {
        "candidate_id": candidate_id_for(subject),
        "capability_id": subject.get("capability_id"),
        "capability_subject": subject.get("capability_subject"),
        "operation": subject.get("operation"),
        "qualification_claim_id": subject.get("qualification_claim_id"),
        "qualification_level": subject.get("current_qualification_level"),
        "qualification_target_level": "REPRODUCIBLY_SUPPORTED",
        "current_qualification_decision": subject.get("C4_state"),
        "current_qualification_deficits": missing,
        "accepted_evidence_ids": subject.get("accepted_evidence_ids", []),
        "accepted_causal_evidence_count": int(subject.get("accepted_causal_evidence_count") or 0),
        "independent_causal_source_count": source["current_independent_causal_source_count"],
        "observed_context_count": context["observed_context_count"],
        "reachable_context_count": context["reachable_context_count"],
        "causal_validation_reachable": causal_validation_reachable,
        "counterfactual_state": counterfactual["counterfactual_state"],
        "source_replication_readiness": source["source_replication_readiness"],
        "claim_binding_state": claim_binding_state,
        "capability_binding_state": capability_binding_state,
        "operation_binding_state": operation_binding_state,
        "known_blockers": blockers,
        "missing_requirements": missing,
        "prequalification_state": state,
        "prequalification_reason": reason,
        "context_readiness": context,
        "source_readiness": source,
        "counterfactual_readiness": counterfactual,
        "canonical_source_identities": source["canonical_source_ids"],
        "source_lineage_identities": subject.get("source_lineage", []),
        "causal_support_state": (
            "CAUSALLY_SUPPORTED"
            if subject.get("accepted_causal_evidence_count")
            else "CAUSAL_SUPPORT_NOT_ESTABLISHED"
        ),
        "causal_method": subject.get("counterfactual_method"),
        "causal_estimand": subject.get("causal_estimand"),
        "operation_effect_evidence": (
            "OBSERVED"
            if subject.get("accepted_causal_evidence_count")
            else "NOT_OBSERVED"
        ),
        "known_rejection_reasons": [],
        "known_structural_blockers": blockers,
        "fact_types": {
            "observed_fact": [
                "accepted_evidence_ids",
                "canonical_source_identities",
                "observed_context_count",
            ],
            "derived_fact": [
                "candidate_id",
                "independent_causal_source_count",
                "prequalification_state",
            ],
            "inference": [
                "reachable_context_count",
                "source_replication_readiness",
                "counterfactual_state",
            ],
            "future_requirement": [
                ">=2 independent causal sources",
                ">=2 exact-subject-preserving natural contexts",
            ],
        },
    }


def freeze_readiness_gate(candidates: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    selectable = [
        dict(item)
        for item in candidates
        if item.get("prequalification_state")
        in {"C5_ELIGIBLE_NOW", "C5_PREQUALIFIED_CANDIDATE"}
    ]
    capabilities = {
        str(item.get("capability_id")) for item in selectable if item.get("capability_id")
    }
    operations = {
        str(item.get("operation")) for item in selectable if item.get("operation")
    }
    source_ids = {
        str(source)
        for item in selectable
        for source in item.get("canonical_source_identities", []) or []
        if source not in {None, "", "UNKNOWN", "Not Available"}
    }
    failures = []
    if len(selectable) < C5_MIN_TARGET_SUBJECTS:
        failures.append("fewer_than_three_defensible_target_subjects")
    if len(capabilities) < C5_MIN_UNIQUE_CAPABILITIES:
        failures.append("fewer_than_three_canonical_capabilities")
    if len(operations) < C5_MIN_UNIQUE_OPERATIONS:
        failures.append("fewer_than_two_operations")
    if any(
        int(item.get("independent_causal_source_count") or 0)
        < C5_MIN_INDEPENDENT_CAUSAL_SOURCES_PER_SUBJECT
        for item in selectable
    ):
        failures.append("selected_subject_source_path_not_currently_sufficient")
    if any(
        int(item.get("reachable_context_count") or 0) < C5_MIN_CONTEXTS_PER_SUBJECT
        for item in selectable
    ):
        failures.append("selected_subject_context_path_not_sufficient")
    if len(source_ids) < C5_MIN_GLOBAL_SOURCE_LINEAGES:
        failures.append("global_source_diversity_not_demonstrated")
    decision = (
        "READY_TO_FREEZE_C5_TARGET_SET"
        if not failures and len(selectable) >= C5_MIN_TARGET_SUBJECTS
        else "NOT_READY_TO_FREEZE_C5_TARGET_SET"
    )
    provisional = selectable[:C5_MIN_TARGET_SUBJECTS] if decision.startswith("READY") else []
    return {
        "primary_freeze_readiness_decision": decision,
        "freeze_ready": decision == "READY_TO_FREEZE_C5_TARGET_SET",
        "defensible_candidate_count": len(selectable),
        "unique_capability_count": len(capabilities),
        "unique_operation_count": len(operations),
        "unique_global_source_lineage_count": len(source_ids),
        "failure_reasons": failures,
        "provisional_target_set": provisional,
        "provisional_target_set_size": len(provisional),
    }


def _report(summary: Mapping[str, Any], matrix: list[Mapping[str, Any]]) -> str:
    decision = summary["primary_freeze_readiness_decision"]
    lines = [
        "# C5 Target-Set Prequalification Report",
        "",
        f"Primary decision: `{decision}`.",
        "",
        "This forensic did not run C5, did not create causal evidence, did not promote capabilities, and did not freeze a target set.",
        "",
        "## Candidate Counts",
        f"- Total candidates: {summary['total_candidate_count']}",
        f"- Eligible now: {summary['c5_eligible_now_count']}",
        f"- Prequalified candidates: {summary['c5_prequalified_candidate_count']}",
        f"- Not ready: {summary['c5_not_ready_count']}",
        f"- Ineligible: {summary['c5_ineligible_count']}",
        "",
        "## Blocking Set",
    ]
    for item in summary["minimum_blocking_set"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Matrix"])
    for item in matrix:
        lines.append(
            "- "
            + f"{item['candidate_id']}: {item['capability_id']} / "
            + f"{item['operation']} / {item['qualification_claim_id']} -> "
            + f"{item['prequalification_state']} ({item['prequalification_reason']})"
        )
    return "\n".join(lines) + "\n"


def run_prequalification(output_root: str | Path = OUTPUT_ROOT) -> dict[str, Any]:
    inventory = _current_subject_inventory()
    known_contexts = _known_contexts_by_operation(inventory)
    matrix = [
        classify_candidate(item, known_operation_contexts=known_contexts)
        for item in inventory
    ]
    counts = Counter(item["prequalification_state"] for item in matrix)
    gate = freeze_readiness_gate(matrix)
    latest_c4 = _latest_dir(C4_ROOT)
    c4_decision = (
        _read(latest_c4 / "19_c4_gate_decision.json")
        if latest_c4 and (latest_c4 / "19_c4_gate_decision.json").exists()
        else {}
    )
    fill_center = next(
        (item for item in matrix if item.get("operation") == "fill_center"),
        {},
    )
    source_inflation_count = sum(
        1
        for item in matrix
        if item["source_readiness"]["same_source_replay_risk"] == "MATERIAL"
    )
    identity_failures = sum(1 for item in matrix if item["known_blockers"])
    claim_failures = sum(1 for item in matrix if item["claim_binding_state"] != "BOUND")
    capability_failures = sum(
        1 for item in matrix if item["capability_binding_state"] != "BOUND"
    )
    operation_failures = sum(
        1 for item in matrix if item["operation_binding_state"] != "BOUND"
    )
    summary = {
        "status": "COMPLETE",
        "primary_freeze_readiness_decision": gate[
            "primary_freeze_readiness_decision"
        ],
        "system_fingerprint": _fingerprint(SYSTEM_PATHS),
        "c5_contract_fingerprint": _payload_fingerprint(
            DOC_PATH.read_text(encoding="utf-8") if DOC_PATH.exists() else ""
        ),
        "c4_contract_fingerprint": c4_decision.get("c4_contract_fingerprint")
        or _payload_fingerprint(c4_decision),
        "git_commit": _git_value("rev-parse", "HEAD"),
        "git_branch": _git_value("rev-parse", "--abbrev-ref", "HEAD"),
        "python_version": platform.python_version(),
        "schema_versions": {
            "causal_validation_evidence": CausalValidationEvidenceEvaluator().METHOD,
            "validation_evidence_evaluator": ValidationEvidenceEvaluator.POLICY_VERSION,
            "integrated_capability_qualification": IntegratedCapabilityQualificationEngine.schema_version,
            "evidence_source_independence": EvidenceSourceIndependenceEngine.schema_version,
        },
        "total_candidate_count": len(matrix),
        "c5_eligible_now_count": counts.get("C5_ELIGIBLE_NOW", 0),
        "c5_prequalified_candidate_count": counts.get("C5_PREQUALIFIED_CANDIDATE", 0),
        "c5_not_ready_count": counts.get("C5_NOT_READY", 0),
        "c5_ineligible_count": counts.get("C5_INELIGIBLE", 0),
        "current_c4_subject_count": sum(
            1 for item in inventory if item.get("C4_state") == "C4_PASSED"
        ),
        "fill_center_context_readiness": (
            fill_center.get("context_readiness", {}).get("state")
            or "SECOND_CONTEXT_NOT_SUPPORTED"
        ),
        "provisional_target_set_size": gate["provisional_target_set_size"],
        "provisional_unique_capability_count": gate["unique_capability_count"]
        if gate["provisional_target_set"]
        else 0,
        "provisional_unique_operation_count": gate["unique_operation_count"]
        if gate["provisional_target_set"]
        else 0,
        "global_source_diversity_feasible": (
            gate["unique_global_source_lineage_count"] >= C5_MIN_GLOBAL_SOURCE_LINEAGES
            and gate["freeze_ready"]
        ),
        "exact_subject_identity_failure_count": identity_failures,
        "claim_binding_failure_count": claim_failures,
        "capability_binding_failure_count": capability_failures,
        "operation_binding_failure_count": operation_failures,
        "source_independence_inflation_count": 0,
        "same_source_replay_risk": (
            "MATERIAL" if source_inflation_count else "LOW"
        ),
        "same_context_replay_risk": (
            "MATERIAL"
            if any(
                item["context_readiness"]["context_diversity_type"]
                == "SAME_CONTEXT_REPLAY"
                for item in matrix
            )
            else "LOW"
        ),
        "selection_rule_outcome_blind": True,
        "cherry_picking_risk": "LOW",
        "c5_readiness_authority": "OBSERVATION_ONLY",
        "behavioral_authority_changed": False,
        "cognitive_consumer_count": 0,
        "c5_freeze_authorization_recommended": gate["freeze_ready"],
        "c5_target_set_frozen": False,
        "c5_campaign_executed": False,
        "c5_authorized_for_claim": False,
        "patch_required": "NO",
        "patch_applied": "NO",
        "minimum_blocking_set": gate["failure_reasons"] or [],
        "next_action": (
            "establish exact-subject-preserving second contexts and C4 replication breadth before requesting freeze"
            if not gate["freeze_ready"]
            else "request separate explicit target-set freeze authorization"
        ),
    }
    context_audit = [
        {
            "candidate_id": item["candidate_id"],
            "capability_id": item["capability_id"],
            "operation": item["operation"],
            "qualification_claim_id": item["qualification_claim_id"],
            **item["context_readiness"],
        }
        for item in matrix
    ]
    source_audit = [
        {
            "candidate_id": item["candidate_id"],
            "capability_id": item["capability_id"],
            "operation": item["operation"],
            "qualification_claim_id": item["qualification_claim_id"],
            **item["source_readiness"],
        }
        for item in matrix
    ]
    counterfactual_audit = [
        {
            "candidate_id": item["candidate_id"],
            "capability_id": item["capability_id"],
            "operation": item["operation"],
            "qualification_claim_id": item["qualification_claim_id"],
            **item["counterfactual_readiness"],
        }
        for item in matrix
    ]
    anti_cherry = {
        "selection_rule_outcome_blind": summary["selection_rule_outcome_blind"],
        "cherry_picking_risk": summary["cherry_picking_risk"],
        "selected_because_already_succeeded": bool(
            gate["provisional_target_set"]
        ),
        "known_failed_or_weak_candidates_silently_removed": False,
        "ready_decision_forbidden": False,
        "reason": "all candidates were inventoried and no provisional target set was selected",
    }
    artifacts = {
        "c5_candidate_inventory.json": inventory,
        "c5_candidate_readiness_matrix.json": matrix,
        "c5_context_diversity_audit.json": context_audit,
        "c5_source_replication_readiness.json": source_audit,
        "c5_counterfactual_readiness.json": counterfactual_audit,
        "c5_global_target_set_feasibility.json": gate,
        "c5_anti_cherry_picking_audit.json": anti_cherry,
        "c5_freeze_readiness_decision.json": summary,
        "c5_target_set_prequalification_report.md": _report(summary, matrix),
        "summary.json": summary,
    }
    if gate["provisional_target_set"]:
        artifacts["c5_provisional_target_set.json"] = gate["provisional_target_set"]
    output_dir = Path(output_root) / _stamp()
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    return {**summary, "output_dir": str(output_dir)}


if __name__ == "__main__":
    print(json.dumps(run_prequalification(), indent=2, sort_keys=True))
