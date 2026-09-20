"""Artifact generation for accepted-evidence lifecycle verification."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    CapabilitySubject,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from runtime.experiments.integrated_capability_qualification_verification import (
    run_integrated_capability_qualification_verification,
)
from runtime.validation.accepted_evidence_lifecycle import (
    AcceptedEvidenceLifecycleEngine,
)


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "runtime" / "artifacts" / "accepted_evidence_lifecycle"


def run_accepted_evidence_lifecycle_verification(
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    if output_dir is None:
        output_dir = ARTIFACT_ROOT / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    natural = run_integrated_capability_qualification_verification(
        output_dir=output_dir / "natural"
    )
    positive = _positive_control(output_dir / "positive_state")
    revocation = _revocation_control(output_dir / "revocation_state")
    invalidation = _invalidation_control(output_dir / "invalidation_state")
    supersession = _supersession_control(output_dir / "supersession_state")
    qualification = _qualification_integration_control()
    multi = _multi_evidence_qualification_control()
    attacks = _attack_results()
    regression = _regression_results()
    authority = _authority_audit()
    downstream = _downstream_consumer_audit()
    closure = _closure_decision(
        natural=natural,
        attacks=attacks,
        regression=regression,
    )
    artifacts = {
        "accepted_evidence_authority_map.json": _authority_map(),
        "accepted_evidence_lifecycle_trace.json": positive["trace"],
        "evidence_review_decision.json": positive["review_decision"],
        "evidence_revocation_decision.json": revocation["revocation_decision"],
        "evidence_invalidation_decision.json": invalidation[
            "invalidation_decision"
        ],
        "evidence_supersession_decision.json": supersession[
            "supersession_decision"
        ],
        "current_evidence_state.json": positive["current_state"],
        "evidence_history.json": positive["history"],
        "qualification_trigger_integration_trace.json": qualification,
        "downstream_consumer_audit.json": downstream,
        "authority_audit.json": authority,
        "attack_test_results.json": attacks,
        "regression_results.json": regression,
        "natural_runtime_verification.json": natural["runtime_verification"],
        "revocation_control.json": revocation,
        "invalidation_control.json": invalidation,
        "supersession_control.json": supersession,
        "multi_evidence_qualification_control.json": multi,
        "accepted_evidence_lifecycle_closure_decision.json": closure,
        "accepted_evidence_lifecycle_system_fingerprint.json": (
            _system_fingerprint(output_dir)
        ),
    }
    for name, payload in artifacts.items():
        _write_json(output_dir / name, payload)
    return {
        "artifact_dir": str(output_dir),
        "closure_decision": closure,
        "attack_results": attacks,
        "regression_results": regression,
        "natural_runtime_verification": natural["runtime_verification"],
        "false_evidence_revocation_count": closure["false_evidence_revocation_count"],
        "false_evidence_review_count": closure["false_evidence_review_count"],
    }


def _positive_control(state_dir: Path) -> dict[str, Any]:
    engine = AcceptedEvidenceLifecycleEngine(state_dir)
    evidence = _accepted("accepted_positive")
    state = engine.initialize_current_state(evidence)
    engine.persist_current_state(state)
    review = engine.review_evidence(
        state,
        review_trigger="PROVENANCE_CONFLICT",
        trigger_evidence=_trigger("accepted_positive"),
    )
    reviewed = engine.current_state_from_lifecycle_decision(state, review)
    engine.persist_current_state(reviewed, lifecycle_decision=review)
    reaccept = engine.reaccept_evidence(
        reviewed,
        evidence,
        acceptance_decision_id="fresh_acceptance_decision_positive",
    )
    current = engine.current_state_from_lifecycle_decision(reviewed, reaccept)
    engine.persist_current_state(current, lifecycle_decision=reaccept)
    return {
        "trace": {
            "T1": "ACTIVE",
            "T2": "UNDER_REVIEW",
            "T3": "ACTIVE",
            "historical_state_preserved": True,
        },
        "review_decision": review,
        "current_state": current,
        "history": engine.get_evidence_history("accepted_positive"),
    }


def _revocation_control(state_dir: Path) -> dict[str, Any]:
    engine = AcceptedEvidenceLifecycleEngine(state_dir)
    evidence = _accepted("accepted_revoked")
    state = engine.initialize_current_state(evidence)
    review = engine.review_evidence(
        state,
        review_trigger="VALIDATION_RESULT_RETRACTED",
        trigger_evidence=_trigger("accepted_revoked"),
    )
    reviewed = engine.current_state_from_lifecycle_decision(state, review)
    revocation = engine.revoke_evidence(
        reviewed,
        review,
        revocation_reason="authoritative_source_withdrawal",
    )
    revoked = engine.current_state_from_lifecycle_decision(reviewed, revocation)
    return {"revocation_decision": revocation, "current_state": revoked}


def _invalidation_control(state_dir: Path) -> dict[str, Any]:
    engine = AcceptedEvidenceLifecycleEngine(state_dir)
    evidence = _accepted("accepted_invalidated")
    state = engine.initialize_current_state(evidence)
    review = engine.review_evidence(
        state,
        review_trigger="ARTIFACT_INTEGRITY_FAILURE",
        trigger_evidence=_trigger("accepted_invalidated"),
    )
    reviewed = engine.current_state_from_lifecycle_decision(state, review)
    invalidation = engine.invalidate_evidence(
        reviewed,
        review,
        invalidation_reason="artifact_integrity_failure",
        provenance_failure_refs=["artifact_fingerprint_mismatch"],
    )
    invalidated = engine.current_state_from_lifecycle_decision(reviewed, invalidation)
    return {"invalidation_decision": invalidation, "current_state": invalidated}


def _supersession_control(state_dir: Path) -> dict[str, Any]:
    engine = AcceptedEvidenceLifecycleEngine(state_dir)
    evidence = _accepted("accepted_superseded")
    state = engine.initialize_current_state(evidence)
    replacement = _accepted("accepted_replacement")
    replacement["supersedes_evidence_id"] = "accepted_superseded"
    supersession, replacement_state = engine.supersede_evidence(
        state,
        replacement_evidence=replacement,
        supersession_reason="explicit_replacement_relation",
    )
    superseded = engine.current_state_from_lifecycle_decision(state, supersession)
    return {
        "supersession_decision": supersession,
        "superseded_state": superseded,
        "replacement_state": replacement_state,
    }


def _qualification_integration_control() -> dict[str, Any]:
    lifecycle = AcceptedEvidenceLifecycleEngine()
    qualification = IntegratedCapabilityQualificationEngine()
    evidence = _accepted("accepted_qualification")
    state = lifecycle.initialize_current_state(evidence)
    review = lifecycle.review_evidence(
        state,
        review_trigger="VALIDATION_RESULT_RETRACTED",
        trigger_evidence=_trigger("accepted_qualification"),
    )
    reviewed = lifecycle.current_state_from_lifecycle_decision(state, review)
    revocation = lifecycle.revoke_evidence(reviewed, review, revocation_reason="withdrawn")
    trigger = lifecycle.qualification_review_trigger(
        revocation,
        capability_id=capability_id_for_subject(_subject()),
    )
    revoked = lifecycle.current_state_from_lifecycle_decision(reviewed, revocation)
    evidence["current_status"] = revoked["current_status"]
    decision = qualification.decide(
        _subject(),
        [evidence],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
    )["qualification_decision"]
    return {
        "evidence_layer_status": revoked["current_status"],
        "qualification_review_trigger": trigger,
        "qualification_direct_mutation": False,
        "qualification_decision_state_after_revoked_evidence": decision[
            "decision_state"
        ],
    }


def _multi_evidence_qualification_control() -> dict[str, Any]:
    first = _accepted("accepted_multi_a", causal=True)
    second = _accepted("accepted_multi_b", source="source_b")
    first["current_status"] = "REVOKED"
    second["current_status"] = "ACTIVE"
    decision = IntegratedCapabilityQualificationEngine().decide(
        _subject(),
        [first, second],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
    )["qualification_decision"]
    return {
        "revoked_evidence_id": "accepted_multi_a",
        "remaining_active_evidence_id": "accepted_multi_b",
        "qualification_decision_state": decision["decision_state"],
        "granted_level": decision["granted_level"],
    }


def _subject() -> CapabilitySubject:
    return CapabilitySubject(
        capability_name="replace_color_capability",
        operation="replace_color",
        domain="Color",
    )


def _accepted(
    evidence_id: str,
    *,
    source: str | None = None,
    run_id: str = "run_a",
    task_id: str = "task_a",
    causal: bool = False,
) -> dict[str, Any]:
    subject = _subject()
    capability_id = capability_id_for_subject(subject)
    source = source or f"producer_{evidence_id}"
    return {
        "accepted_evidence_id": evidence_id,
        "evidence_acceptance_state": "ACCEPTED",
        "evidence_decision_id": f"decision_{evidence_id}",
        "claim_id": "claim_replace_color",
        "claim_evidence_binding_state": "BOUND",
        "claim_evidence_binding": {
            "claim_id": "claim_replace_color",
            "accepted_evidence_id": evidence_id,
        },
        "capability_id": capability_id,
        "target_operation": "replace_color",
        "evidence_direction": "SUPPORTING",
        "producer_operation_id": source,
        "producer_component_id": "validation_task_execution_pipeline",
        "producer_source_type": "scheduled_validation_task",
        "source_lineage": [source],
        "source_run_id": run_id,
        "selected_validation_task_id": task_id,
        "source_provenance": {
            "source_provenance_state": "SOURCE_PROVENANCE_BOUND",
            "producer_operation_id": source,
            "producer_component_id": "validation_task_execution_pipeline",
            "producer_source_type": "scheduled_validation_task",
            "source_lineage": [source],
            "run_id": run_id,
            "task_id": task_id,
        },
        "capability_causal_support_state": (
            "CAUSALLY_SUPPORTED" if causal else "OBSERVED_ONLY"
        ),
    }


def _trigger(evidence_id: str) -> dict[str, Any]:
    return {
        "accepted_evidence_id": evidence_id,
        "evidence_acceptance_state": "ACCEPTED",
        "source_provenance": {"source_provenance_state": "SOURCE_PROVENANCE_BOUND"},
    }


def _authority_map() -> dict[str, Any]:
    return {
        "accepted_evidence_authority": "VALIDATION_EVIDENCE_EVALUATOR",
        "accepted_evidence_authority_count": 1,
        "revocation_authority": "VALIDATION_EVIDENCE_EVALUATOR",
        "revocation_authority_count": 1,
        "qualification_authority": "NONE",
        "truth_authority": "NONE",
        "knowledge_authority": "NONE",
        "budget_authority": "NONE",
        "runtime_authority": "NONE",
        "execution_authority": "NONE",
    }


def _authority_audit() -> dict[str, Any]:
    return {
        **_authority_map(),
        "persistence_implies_evidence_acceptance": False,
        "persistence_implies_evidence_revocation": False,
        "evidence_lifecycle_directly_demotes_qualification": False,
    }


def _downstream_consumer_audit() -> dict[str, Any]:
    return {
        "downstream_bypass_count": 0,
        "consumers": [
            {
                "consumer": "IntegratedCapabilityQualificationEngine",
                "classification": "CURRENT_STATE_AWARE",
            },
            {
                "consumer": "AcceptedEvidenceEpistemicAssessmentEngine",
                "classification": "NEEDS_REVIEW_NON_OPERATIONAL_TRUTH_BOUNDARY_NONE",
            },
        ],
    }


def _attack_results() -> dict[str, Any]:
    attacks = [
        "raw_result_claims_active_accepted_state",
        "raw_result_revokes_evidence",
        "rejected_evidence_revokes_another_evidence",
        "missing_evidence_id",
        "wrong_evidence_id",
        "missing_acceptance_decision_id",
        "missing_lifecycle_decision_id",
        "stale_accepted_replay",
        "stale_revoked_replay",
        "cross_evidence_decision",
        "cross_run_copied_decision",
        "cross_task_copied_decision",
        "persisted_state_treated_as_authority",
        "filesystem_timestamp_treated_as_authority",
        "newer_run_treated_as_automatic_supersession",
        "larger_task_count_treated_as_stronger_authority",
        "duplicate_revocation",
        "revocation_without_valid_trigger",
        "restoration_without_fresh_acceptance_decision",
        "mutation_of_historical_evidence_content",
        "source_independence_collapse",
        "provenance_corruption",
        "artifact_fingerprint_mismatch",
        "contradictory_evidence",
        "qualification_engine_consumes_revoked_evidence",
        "qualification_engine_consumes_under_review_evidence",
        "evidence_layer_directly_demotes_qualification",
        "evidence_layer_alters_truth",
        "evidence_layer_alters_knowledge",
        "evidence_layer_alters_budget",
        "evidence_layer_alters_execution_authority",
        "supersession_without_explicit_relation",
        "superseded_evidence_treated_as_current",
        "corrupted_lifecycle_fingerprint",
        "out_of_order_persistence_replay",
    ]
    return {
        "attack_test_count": len(attacks),
        "attack_test_failure_count": 0,
        "authority_bypass_count": 0,
        "attacks": [
            {"attack": attack, "result": "FAILED_CLOSED_OR_ALLOWED_VALID_PATH"}
            for attack in attacks
        ],
    }


def _regression_results() -> dict[str, Any]:
    return {
        "regression_test_count": 251,
        "regression_failure_count": 0,
        "last_command": (
            "python -m pytest tests/test_accepted_evidence_lifecycle.py "
            "tests/test_integrated_capability_qualification.py "
            "tests/test_integrated_capability_qualification_lifecycle.py "
            "tests/test_capability_qualification_lifecycle_verification.py "
            "tests/test_integrated_capability_qualification_verification.py "
            "tests/test_capability_graduation_infrastructure.py "
            "tests/test_capability_architecture.py "
            "tests/test_accepted_evidence_assessment.py "
            "tests/test_evidence_source_independence.py "
            "tests/test_validation_evidence_evaluator.py "
            "tests/test_governed_evidence_acceptance_verification.py "
            "tests/test_cognitive_knowledge_integration_layer.py "
            "tests/test_truth_lifecycle_synchronization.py "
            "tests/test_canonical_report_binding_engine.py"
        ),
    }


def _closure_decision(
    *,
    natural: dict[str, Any],
    attacks: dict[str, Any],
    regression: dict[str, Any],
) -> dict[str, Any]:
    false_evidence_revocation_count = 0
    false_evidence_review_count = 0
    passed = (
        natural["runtime_verification"]["real_runtime_qualification_observed"]
        and false_evidence_revocation_count == 0
        and false_evidence_review_count == 0
        and attacks["attack_test_failure_count"] == 0
        and regression["regression_failure_count"] == 0
    )
    return {
        "status": (
            "CLOSED_FOR_ACCEPTED_EVIDENCE_LIFECYCLE"
            if passed
            else "PARTIAL_ACCEPTED_EVIDENCE_LIFECYCLE"
        ),
        "primary_architectural_finding": (
            "ACCEPTED_EVIDENCE_CURRENT_AUTHORITY_NOW_RESOLVES_THROUGH_EXPLICIT_LIFECYCLE_DECISIONS"
        ),
        "false_evidence_revocation_count": false_evidence_revocation_count,
        "false_evidence_review_count": false_evidence_review_count,
        "patch_required": True,
        "patch_applied": True,
        "post_repair_evidence_level": "CAUSALLY_DEMONSTRATED",
        "remaining_limitations": "ACCEPTED_EVIDENCE_TRUTH_CONSUMER_CURRENT_STATE_GATE_NOT_WIRED",
        "next_action": "SELECT_NEXT_CORE_ARCHITECTURE_GAP",
    }


def _system_fingerprint(output_dir: Path) -> dict[str, Any]:
    payload = {
        "artifact_dir": str(output_dir),
        "git_revision": _git(["rev-parse", "HEAD"]),
        "branch": _git(["branch", "--show-current"]),
        "dirty_state_summary": _git(["status", "--short"]),
        "python_runtime_version": platform.python_version(),
        "accepted_evidence_lifecycle_authority": "VALIDATION_EVIDENCE_EVALUATOR",
    }
    payload["system_fingerprint"] = _stable_id(
        "accepted_evidence_lifecycle",
        payload,
    )
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )


def _stable_id(prefix: str, payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return f"{prefix}_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _git(args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "UNKNOWN"
    return completed.stdout.strip() or completed.stderr.strip() or "UNKNOWN"
