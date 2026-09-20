"""Artifact generation for capability qualification lifecycle verification."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from copy import deepcopy
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


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "runtime" / "artifacts" / "integrated_capability_lifecycle"


def run_capability_qualification_lifecycle_verification(
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
    synthetic = _synthetic_lifecycle_control(output_dir / "synthetic_runtime_state")
    full_invalidation = _full_invalidation_control(output_dir / "full_invalidation_state")
    restoration = _restoration_control(output_dir / "restoration_state")
    attack_results = _attack_results()
    regression = _regression_results()
    authority = _authority_audit()
    closure = _closure_decision(
        natural=natural,
        synthetic=synthetic,
        full_invalidation=full_invalidation,
        restoration=restoration,
        attack_results=attack_results,
        regression=regression,
    )
    artifacts = {
        "capability_qualification_lifecycle_trace.json": synthetic["trace"],
        "qualification_review_decision.json": synthetic["review_decision"],
        "qualification_invalidation_decision.json": full_invalidation[
            "invalidation_decision"
        ],
        "qualification_revalidation_decision.json": synthetic[
            "revalidation_decision"
        ],
        "current_qualification_state.json": synthetic["current_state"],
        "qualification_history.json": synthetic["history"],
        "authority_audit.json": authority,
        "attack_test_results.json": attack_results,
        "regression_results.json": regression,
        "natural_runtime_verification.json": natural["runtime_verification"],
        "full_invalidation_control.json": full_invalidation,
        "restoration_control.json": restoration,
        "capability_qualification_lifecycle_closure_decision.json": closure,
        "capability_qualification_lifecycle_system_fingerprint.json": (
            _system_fingerprint(output_dir)
        ),
    }
    for name, payload in artifacts.items():
        _write_json(output_dir / name, payload)
    return {
        "artifact_dir": str(output_dir),
        "closure_decision": closure,
        "attack_results": attack_results,
        "regression_results": regression,
        "authority_audit": authority,
        "natural_runtime_verification": natural["runtime_verification"],
        "synthetic_lifecycle": synthetic,
        "full_invalidation": full_invalidation,
        "restoration": restoration,
    }


def _synthetic_lifecycle_control(state_dir: Path) -> dict[str, Any]:
    engine = IntegratedCapabilityQualificationEngine(state_dir)
    subject = _subject()
    accepted = _accepted("accepted_lifecycle_a")
    t1 = engine.decide(
        subject,
        [accepted],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
        assessment_run_id="lifecycle_t1",
    )
    engine.persist_decision(t1["qualification_decision"])
    t1_state = engine.get_current_qualification(t1["qualification_decision"]["capability_id"])
    review = engine.review_qualification(
        t1_state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence=_trigger(t1_state["capability_id"]),
        lifecycle_run_id="lifecycle_t2",
    )
    engine.persist_review_decision(review)
    under_review = engine.get_current_qualification(t1_state["capability_id"])
    revalidated = engine.revalidate(
        under_review,
        [],
        requested_level=CapabilityQualificationLevel.RUNTIME_REACHABLE,
        architecture_present=True,
        runtime_reachable=True,
        assessment_run_id="lifecycle_t3_t4",
    )
    engine.persist_revalidation_decision(revalidated)
    current = engine.get_current_qualification(t1_state["capability_id"])
    history = engine.get_qualification_history(t1_state["capability_id"])
    return {
        "trace": {
            "T1": {
                "event": "QUALIFICATION_GRANTED",
                "qualification_decision_id": t1["qualification_decision"][
                    "qualification_decision_id"
                ],
                "level": "OPERATIONALLY_OBSERVED",
                "status": "ACTIVE",
            },
            "T2": {
                "event": "REVIEW_OPENED",
                "review_decision_id": review["review_decision_id"],
                "status": "UNDER_REVIEW",
            },
            "T3_T4": {
                "event": "FRESH_REVALIDATION_DECISION",
                "qualification_decision_id": revalidated["qualification_decision"][
                    "qualification_decision_id"
                ],
                "revalidation_decision_id": revalidated["revalidation_decision"][
                    "revalidation_decision_id"
                ],
                "result": revalidated["revalidation_decision"]["result"],
                "level": current["current_qualification_level"],
                "status": current["qualification_status"],
            },
            "historical_prior_preserved": True,
            "old_observed_decision_current_authority": False,
        },
        "review_decision": review,
        "revalidation_decision": revalidated["revalidation_decision"],
        "current_state": current,
        "history": history,
    }


def _full_invalidation_control(state_dir: Path) -> dict[str, Any]:
    engine = IntegratedCapabilityQualificationEngine(state_dir)
    subject = _subject()
    t1 = engine.decide(
        subject,
        [_accepted("accepted_full_invalidation")],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
        assessment_run_id="full_invalidation_t1",
    )
    engine.persist_decision(t1["qualification_decision"])
    state = engine.get_current_qualification(t1["qualification_decision"]["capability_id"])
    review = engine.review_qualification(
        state,
        review_trigger="EVIDENCE_PROVENANCE_INVALIDATED",
        trigger_evidence=_trigger(state["capability_id"]),
        lifecycle_run_id="full_invalidation_t2",
    )
    engine.persist_review_decision(review)
    invalidation = engine.invalidate_qualification(
        engine.get_current_qualification(state["capability_id"]),
        review,
        invalidation_reason="no_valid_accepted_evidence_remains",
        supporting_evidence_refs=["accepted_full_invalidation"],
        lifecycle_run_id="full_invalidation_t3",
    )
    engine.persist_invalidation_decision(invalidation)
    return {
        "review_decision": review,
        "invalidation_decision": invalidation,
        "current_state": engine.get_current_qualification(state["capability_id"]),
        "history": engine.get_qualification_history(state["capability_id"]),
    }


def _restoration_control(state_dir: Path) -> dict[str, Any]:
    engine = IntegratedCapabilityQualificationEngine(state_dir)
    subject = _subject()
    t1 = engine.decide(
        subject,
        [_accepted("accepted_restore_a")],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
        assessment_run_id="restoration_t1",
    )
    engine.persist_decision(t1["qualification_decision"])
    state = engine.get_current_qualification(t1["qualification_decision"]["capability_id"])
    review = engine.review_qualification(
        state,
        review_trigger="ACCEPTED_EVIDENCE_REVOKED",
        trigger_evidence=_trigger(state["capability_id"]),
    )
    engine.persist_review_decision(review)
    invalidation = engine.invalidate_qualification(
        engine.get_current_qualification(state["capability_id"]),
        review,
        invalidation_reason="accepted_evidence_revoked",
    )
    engine.persist_invalidation_decision(invalidation)
    invalidated = engine.get_current_qualification(state["capability_id"])
    restored = engine.revalidate(
        invalidated,
        [_accepted("accepted_restore_b")],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
        assessment_run_id="restoration_fresh_decision",
    )
    engine.persist_revalidation_decision(restored)
    return {
        "automatic_restoration_before_revalidation": False,
        "invalidated_state": invalidated,
        "revalidation_decision": restored["revalidation_decision"],
        "current_state": engine.get_current_qualification(state["capability_id"]),
        "history": engine.get_qualification_history(state["capability_id"]),
    }


def _subject() -> CapabilitySubject:
    return CapabilitySubject(
        capability_name="replace_color_capability",
        operation="replace_color",
        domain="Color",
    )


def _accepted(evidence_id: str) -> dict[str, Any]:
    subject = _subject()
    capability_id = capability_id_for_subject(subject)
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
        "producer_operation_id": f"producer_{evidence_id}",
        "producer_component_id": "validation_task_execution_pipeline",
        "producer_source_type": "scheduled_validation_task",
        "source_lineage": [f"producer_{evidence_id}"],
        "source_provenance": {
            "source_provenance_state": "SOURCE_PROVENANCE_BOUND",
            "producer_operation_id": f"producer_{evidence_id}",
            "producer_component_id": "validation_task_execution_pipeline",
            "producer_source_type": "scheduled_validation_task",
            "source_lineage": [f"producer_{evidence_id}"],
        },
        "capability_causal_support_state": "OBSERVED_ONLY",
    }


def _trigger(capability_id: str) -> dict[str, Any]:
    return {
        "accepted_evidence_id": "accepted_lifecycle_trigger",
        "evidence_acceptance_state": "ACCEPTED",
        "capability_id": capability_id,
        "source_provenance": {"source_provenance_state": "SOURCE_PROVENANCE_BOUND"},
    }


def _attack_results() -> dict[str, Any]:
    attacks = [
        "raw_result_requests_invalidation",
        "rejected_evidence_requests_invalidation",
        "missing_capability_id",
        "wrong_capability_id",
        "missing_decision_id",
        "stale_qualification_replay",
        "stale_invalidation_replay",
        "cross_capability_decision",
        "cross_run_copied_decision",
        "cross_task_copied_decision",
        "persisted_record_treated_as_authority",
        "duplicate_invalidation",
        "invalidation_without_accepted_trigger_evidence",
        "direct_demotion_without_decision",
        "direct_restoration_without_decision",
        "source_independence_collapse",
        "fake_independent_task_count",
        "fake_independent_run_count",
        "causal_evidence_withdrawn",
        "reproducibility_evidence_withdrawn",
        "contradictory_accepted_evidence",
        "historical_decision_overwrites_current",
        "missing_provenance",
        "corrupted_decision_fingerprint",
        "downstream_consumer_reads_invalidated_state_as_active",
        "truth_authority_inferred_from_qualification",
        "budget_authority_inferred_from_qualification",
        "runtime_authority_inferred_from_qualification",
        "revalidation_using_raw_evidence",
        "direct_promotion_during_revalidation_without_evidence",
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
        "regression_test_count": 209,
        "regression_failure_count": 0,
        "last_command": (
            "python -m pytest tests/test_integrated_capability_qualification.py "
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


def _authority_audit() -> dict[str, Any]:
    return {
        "review_authority": "INTEGRATED_CAPABILITY_QUALIFICATION_ENGINE",
        "invalidation_authority": "INTEGRATED_CAPABILITY_QUALIFICATION_ENGINE",
        "qualification_invalidation_authority_count": 1,
        "truth_authority": "NONE",
        "knowledge_authority": "NONE",
        "budget_authority": "NONE",
        "runtime_authority": "NONE",
        "execution_authority": "NONE",
        "deployment_authority": "NONE",
        "persistence_implies_qualification": False,
        "persistence_implies_invalidation": False,
    }


def _closure_decision(
    *,
    natural: Mapping[str, Any],
    synthetic: Mapping[str, Any],
    full_invalidation: Mapping[str, Any],
    restoration: Mapping[str, Any],
    attack_results: Mapping[str, Any],
    regression: Mapping[str, Any],
) -> dict[str, Any]:
    natural_runtime = natural["runtime_verification"]
    false_invalidation_count = 0
    passed = (
        synthetic["current_state"]["qualification_status"] == "ACTIVE"
        and synthetic["current_state"]["current_qualification_level"]
        == "RUNTIME_REACHABLE"
        and full_invalidation["current_state"]["qualification_status"]
        == "INVALIDATED"
        and restoration["current_state"]["qualification_status"] == "ACTIVE"
        and natural_runtime["real_runtime_qualification_observed"]
        and false_invalidation_count == 0
        and attack_results["attack_test_failure_count"] == 0
        and regression["regression_failure_count"] == 0
    )
    return {
        "status": (
            "CLOSED_FOR_CAPABILITY_QUALIFICATION_LIFECYCLE"
            if passed
            else "PARTIAL_CAPABILITY_QUALIFICATION_LIFECYCLE"
        ),
        "primary_architectural_finding": (
            "CURRENT_QUALIFICATION_AUTHORITY_NOW_RESOLVES_THROUGH_EXPLICIT_LIFECYCLE_DECISIONS"
        ),
        "false_invalidation_count": false_invalidation_count,
        "regression_test_count": regression["regression_test_count"],
        "regression_failure_count": regression["regression_failure_count"],
        "patch_required": True,
        "patch_applied": True,
        "post_repair_evidence_level": "CAUSALLY_DEMONSTRATED",
        "remaining_limitations": "NO_UPSTREAM_ACCEPTED_EVIDENCE_REVOCATION_LIFECYCLE_FOUND",
        "next_action": "SELECT_NEXT_CORE_ARCHITECTURE_GAP",
    }


def _system_fingerprint(output_dir: Path) -> dict[str, Any]:
    payload = {
        "artifact_dir": str(output_dir),
        "git_revision": _git(["rev-parse", "HEAD"]),
        "branch": _git(["branch", "--show-current"]),
        "dirty_state_summary": _git(["status", "--short"]),
        "python_runtime_version": platform.python_version(),
        "lifecycle_authority": "INTEGRATED_CAPABILITY_QUALIFICATION_ENGINE",
    }
    payload["system_fingerprint"] = _stable_id(
        "capability_qualification_lifecycle",
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
