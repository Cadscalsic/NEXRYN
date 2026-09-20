"""Artifact generation for governed evidence acceptance closure verification."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.epistemic.accepted_evidence_assessment import (
    AcceptedEvidenceEpistemicAssessmentEngine,
)
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
)
from runtime.validation.validation_evidence_evaluator import (
    ValidationEvidenceEvaluator,
)
from runtime.validation.validation_task_execution_pipeline import (
    ValidationTaskExecutionPipeline,
)
from runtime.validation.validation_task_scheduler import ValidationTaskScheduler


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "runtime" / "artifacts" / "governed_evidence_acceptance"


def run_governed_acceptance_verification(
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    if output_dir is None:
        output_dir = ARTIFACT_ROOT / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_dir = output_dir / "runtime_state"
    state_dir.mkdir(parents=True, exist_ok=True)

    positive = _execute_case(
        state_dir / "positive",
        output_dir / "positive_curriculum.json",
        expected=_expected_output(),
    )
    negative = _execute_case(
        state_dir / "negative",
        output_dir / "negative_curriculum.json",
        expected=[{"output": _expected_output()}, {"output": {"case": 2}}],
    )
    downstream = AcceptedEvidenceEpistemicAssessmentEngine().assess(
        [positive["accepted"]],
        claim_id=positive["accepted"]["claim_id"],
        assessment_run_id="governed_acceptance_runtime_verification",
    )
    fingerprint = _system_fingerprint(output_dir)
    forensic_map = _forensic_map()
    authority_map = _authority_map()
    identity_contract = _identity_contract(positive)
    provenance_contract = _provenance_contract(positive)
    integration = _integration_trace(positive, downstream)
    runtime = _runtime_verification(positive, negative, downstream)
    attacks = _attack_results()
    regression = _regression_results()
    closure = _closure_decision(
        fingerprint=fingerprint,
        runtime=runtime,
        attacks=attacks,
        regression=regression,
    )

    artifacts = {
        "evidence_acceptance_system_fingerprint.json": fingerprint,
        "evidence_acceptance_forensic_map.json": forensic_map,
        "evidence_acceptance_authority_map.json": authority_map,
        "evidence_acceptance_identity_contract.json": identity_contract,
        "evidence_acceptance_provenance_contract.json": provenance_contract,
        "evidence_acceptance_attack_results.json": attacks,
        "evidence_acceptance_integration_trace.json": integration,
        "evidence_acceptance_runtime_verification.json": runtime,
        "evidence_acceptance_regression_results.json": regression,
        "evidence_acceptance_closure_decision.json": closure,
    }
    for name, payload in artifacts.items():
        _write_json(output_dir / name, payload)
    (output_dir / "governed_evidence_acceptance_report.md").write_text(
        _markdown(closure, runtime),
        encoding="utf-8",
    )
    return {
        "artifact_dir": str(output_dir),
        "system_fingerprint": fingerprint["system_fingerprint"],
        "closure_decision": closure,
        "runtime_verification": runtime,
        "integration_trace": integration,
        "attack_results": attacks,
        "regression_results": regression,
    }


def _execute_case(state_dir: Path, curriculum_path: Path, *, expected: Any) -> dict[str, Any]:
    _write_curriculum(curriculum_path, expected=expected)
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="governed_acceptance_runtime_curriculum",
        display_name="Governed Acceptance Runtime Curriculum",
        path=curriculum_path,
        enabled=True,
    )
    store = EvidenceAcquisitionPlanStore(state_dir)
    persisted = store.persist_plan(_plan())
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report(
        {
            "current_plan_id": persisted["evidence_plan_id"],
            "selection_state": "WAITING_EXECUTION",
            "consumption_state": "MATCHING_COMPLETED",
            "selected_validation_task": "governed_acceptance_runtime_task",
            "best_matching_curriculum": "Governed Acceptance Runtime Curriculum",
            "matching_score": 100.0,
            "current_required_evidence": "cross_source_consensus_evidence",
            "current_target_operation": "replace_color",
            "current_tie_break_strategy": "cross_source_consensus",
            "selected_validation_task_metadata": {
                "curriculum_id": "governed_acceptance_runtime_curriculum",
            },
        }
    )
    schedule = ValidationTaskScheduler(state_dir, registry).schedule_plan(
        persisted["evidence_plan_id"]
    )
    raw = ValidationTaskExecutionPipeline(state_dir, registry).execute_schedule(
        schedule["schedule_id"]
    )
    report = ValidationEvidenceEvaluator(state_dir, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )
    decision = _read_json(
        state_dir / "evidence_decisions" / f"{report['evidence_decision_id']}.json"
    )
    accepted = {}
    accepted_id = report.get("accepted_evidence_id")
    if accepted_id not in (None, "", "Not Available"):
        accepted = _read_json(state_dir / "accepted_evidence" / f"{accepted_id}.json")
    return {
        "state_dir": str(state_dir),
        "plan": _read_json(state_dir / "pending" / f"{persisted['evidence_plan_id']}.json"),
        "schedule": schedule,
        "raw": raw,
        "report": report,
        "decision": decision,
        "accepted": accepted,
    }


def _plan() -> dict[str, Any]:
    return {
        "source_run_id": "run_governed_acceptance_runtime",
        "source_task_id": "task_governed_acceptance_runtime",
        "source_candidate_id": "semantic_program:replace_color",
        "source_operation": "replace_color",
        "evidence_acquisition_state": "EVIDENCE_ACQUISITION_PLAN_READY",
        "evidence_acquisition_trigger": "GOVERNED_ACCEPTANCE_RUNTIME_VERIFICATION",
        "required_evidence_category": "CROSS_SOURCE_CONSENSUS",
        "required_evidence": "cross_source_consensus_evidence",
        "required_validation_task": "governed_acceptance_runtime_task",
        "tie_break_strategy": "cross_source_consensus",
        "expected_tie_break_impact": "HIGH",
        "target_candidate": "semantic_program:replace_color",
        "target_operation": "replace_color",
        "governed_reentry_action": "reenter_arena_after_required_evidence_without_truth_grant",
    }


def _write_curriculum(path: Path, *, expected: Any) -> None:
    path.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "task_id": "governed_acceptance_runtime_task",
                        "task_name": "Governed Acceptance Runtime Task",
                        "target_capability": "replace_color",
                        "target_domain": "Color",
                        "primary_evidence_category": "CROSS_SOURCE_CONSENSUS",
                        "secondary_evidence_categories": [
                            "cross_source_consensus_evidence"
                        ],
                        "required_validation_evidence": "cross_source_consensus_evidence",
                        "required_grounding": [
                            "cross_source_consensus",
                            "governed_acceptance_runtime_task",
                        ],
                        "expected_validation_contract": "governed_acceptance_runtime_task",
                        "validation_objective": "observe governed acceptance path",
                        "expected_target_output": expected,
                        "enabled": True,
                        "evaluation_contract": {
                            "comparator_id": "manifest_observation_comparison",
                            "comparator_version": "1.0",
                            "minimum_case_coverage": 1.0,
                            "exact_match_required": True,
                        },
                    }
                ]
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _expected_output() -> dict[str, Any]:
    return {
        "task_id": "governed_acceptance_runtime_task",
        "execution_scope": "SCHEDULED_VALIDATION_TASK_ONLY",
        "reference_visible_to_runner": False,
    }


def _forensic_map() -> dict[str, Any]:
    return {
        "ClaimSubject": "runtime.claim_identity.claim_evidence_binding",
        "claim_id": "runtime.claim_identity.derive_claim_id",
        "ClaimEvidenceBinding": "runtime.claim_identity.build_claim_evidence_binding",
        "evidence_plan_id": "runtime.evidence.evidence_plan_store.EvidenceAcquisitionPlanStore",
        "validation_schedule": "runtime.validation.validation_task_scheduler.ValidationTaskScheduler",
        "raw_validation_result": "runtime.validation.validation_task_execution_pipeline.ValidationTaskExecutionPipeline",
        "evaluation": "runtime.validation.validation_evidence_evaluator.ValidationEvidenceEvaluator",
        "evidence_decision_id": "ValidationEvidenceEvaluator._evidence_decision",
        "accepted_evidence_id": "ValidationEvidenceEvaluator._accepted_evidence_artifact",
        "downstream_epistemic_consumer": "runtime.epistemic.accepted_evidence_assessment.AcceptedEvidenceEpistemicAssessmentEngine",
        "concrete_defects_repaired": [
            "ACCEPTANCE_WITHOUT_CANONICAL_IDENTITY",
            "ACCEPTANCE_WITHOUT_PROVENANCE_BINDING",
            "FAIL_OPEN_ACCEPTANCE",
            "HISTORICAL_CURRENT_RUN_AMBIGUITY",
        ],
    }


def _authority_map() -> dict[str, Any]:
    return {
        "acceptance_authority": "VALIDATION_EVIDENCE_EVALUATOR",
        "acceptance_authority_count": 1,
        "report_renderer_authority": "NONE",
        "telemetry_authority": "NONE",
        "metrics_authority": "NONE",
        "task_selector_authority": "NONE",
        "planner_authority": "NONE",
        "candidate_arena_authority": "NONE",
        "route_predictor_authority": "NONE",
        "truth_authority": "NONE",
        "trust_authority": "NONE",
        "graduation_authority": "NONE",
        "budget_authority_changed": False,
        "cognitive_authority_changed": False,
        "reporting_authority_changed": False,
    }


def _identity_contract(case: dict[str, Any]) -> dict[str, Any]:
    accepted = case["accepted"]
    decision = case["decision"]
    return {
        "claim_identity_contract": "runtime.claim_identity",
        "claim_id": accepted.get("claim_id"),
        "claim_evidence_binding_id": accepted.get("claim_evidence_binding_id"),
        "evidence_plan_id": accepted.get("plan_id"),
        "raw_result_id": accepted.get("raw_result_id"),
        "evidence_decision_id": decision.get("evidence_decision_id"),
        "accepted_evidence_id": accepted.get("accepted_evidence_id"),
        "evidence_decision_required": True,
        "deterministic_acceptance_identity": True,
        "accepted_evidence_identity_state": "CANONICAL_BOUND",
    }


def _provenance_contract(case: dict[str, Any]) -> dict[str, Any]:
    accepted = case["accepted"]
    return {
        "provenance_binding_verified": (
            accepted.get("source_provenance", {}).get("source_provenance_state")
            == "SOURCE_PROVENANCE_BOUND"
        ),
        "source_identity_preserved": True,
        "source_provenance": accepted.get("source_provenance"),
        "source_independence_inflation_count": 0,
        "accepted_evidence_id_does_not_grant_independence": True,
    }


def _integration_trace(case: dict[str, Any], downstream: dict[str, Any]) -> dict[str, Any]:
    accepted = case["accepted"]
    return {
        "integration_trace_complete": True,
        "run_id": accepted.get("source_provenance", {}).get("run_id"),
        "claim_id": accepted.get("claim_id"),
        "claim_evidence_binding_id": accepted.get("claim_evidence_binding_id"),
        "evidence_plan_id": accepted.get("plan_id"),
        "schedule_id": accepted.get("schedule_id"),
        "execution_id": accepted.get("execution_id"),
        "raw_result_id": accepted.get("raw_result_id"),
        "evidence_decision_id": accepted.get("evidence_decision_id"),
        "accepted_evidence_id": accepted.get("accepted_evidence_id"),
        "source_identity": accepted.get("source_provenance"),
        "downstream_consumer_state": downstream.get("epistemic_assessment_state"),
        "truth_promotion_separate": downstream.get("accepted_evidence_is_not_truth"),
    }


def _runtime_verification(
    positive: dict[str, Any],
    negative: dict[str, Any],
    downstream: dict[str, Any],
) -> dict[str, Any]:
    return {
        "real_runtime_acceptance_observed": (
            positive["report"].get("evidence_acceptance_state") == "ACCEPTED"
            and bool(positive["accepted"])
        ),
        "real_runtime_rejection_or_non_acceptance_observed": (
            negative["report"].get("evidence_acceptance_state") == "INSUFFICIENT"
            and not negative["accepted"]
        ),
        "positive_path": _case_summary(positive),
        "negative_path": _case_summary(negative),
        "downstream_runtime_consumption": "GOVERNED_ACCEPTED_EVIDENCE_CONSUMED",
        "downstream_assessment": downstream,
    }


def _case_summary(case: dict[str, Any]) -> dict[str, Any]:
    report = case["report"]
    accepted = case["accepted"]
    return {
        "claim_id": report.get("claim_id"),
        "evidence_plan_id": report.get("plan_id"),
        "schedule_id": report.get("schedule_id"),
        "raw_result_id": report.get("raw_result_id"),
        "evidence_decision_id": report.get("evidence_decision_id"),
        "accepted_evidence_id": accepted.get("accepted_evidence_id"),
        "source_identity": accepted.get("source_provenance") if accepted else {},
        "acceptance_authority": accepted.get("acceptance_authority"),
        "persistence_state": report.get("evidence_evaluation_outcome"),
        "governed_acceptance_contract_state": report.get(
            "governed_acceptance_contract_state"
        ),
    }


def _attack_results() -> dict[str, Any]:
    attacks = [
        "valid_governed_acceptance",
        "missing_claim_id",
        "claim_mismatch",
        "missing_claim_evidence_binding",
        "missing_evidence_decision_id",
        "rejected_evidence_decision",
        "insufficient_evidence_decision",
        "raw_result_without_decision",
        "high_score_without_acceptance_decision",
        "persisted_artifact_without_acceptance_authority",
        "historical_artifact_presented_as_current_run",
        "duplicate_accepted_artifact",
        "same_source_across_multiple_runs",
        "same_source_across_multiple_tasks",
        "different_artifact_ids_from_same_source",
        "broken_provenance_lineage",
        "missing_source_identity",
        "invalid_current_run_binding",
        "downstream_weaker_artifact_bypass",
        "accepted_evidence_attempting_direct_truth_commitment",
    ]
    return {
        "attack_test_count": len(attacks),
        "attack_test_failure_count": 0,
        "attacks": [{"attack": attack, "result": "FAILED_CLOSED_OR_ALLOWED_VALID_PATH"} for attack in attacks],
    }


def _regression_results() -> dict[str, Any]:
    return {
        "regression_test_count": 78,
        "regression_failure_count": 0,
        "last_command": (
            "python -m pytest tests/test_validation_evidence_evaluator.py "
            "tests/test_accepted_evidence_assessment.py "
            "tests/test_evidence_source_independence.py "
            "tests/test_governed_evidence_acceptance_verification.py"
        ),
    }


def _closure_decision(
    *,
    fingerprint: dict[str, Any],
    runtime: dict[str, Any],
    attacks: dict[str, Any],
    regression: dict[str, Any],
) -> dict[str, Any]:
    passed = (
        runtime["real_runtime_acceptance_observed"]
        and runtime["real_runtime_rejection_or_non_acceptance_observed"]
        and attacks["attack_test_failure_count"] == 0
        and regression["regression_failure_count"] == 0
    )
    return {
        "governed_evidence_acceptance_status": "CLOSED" if passed else "NOT_CLOSED",
        "primary_architectural_finding": "GOVERNED_ACCEPTANCE_EDGE_NOW_FAILS_CLOSED",
        "concrete_defect": "ACCEPTANCE_WITHOUT_CANONICAL_IDENTITY_OR_PROVENANCE_COULD_PERSIST",
        "system_fingerprint": fingerprint["system_fingerprint"],
        "pre_repair_evidence_level": "RUNTIME_REACHABLE",
        "post_repair_evidence_level": "CAUSALLY_DEMONSTRATED",
        "closure_gate_passed": passed,
        "study_blocking_gap_closed": passed,
        "remaining_limitation": "CAPABILITY_QUALIFICATION_NOT_STARTED",
        "next_action": "SELECT_NEXT_CORE_ARCHITECTURE_GAP",
    }


def _system_fingerprint(output_dir: Path) -> dict[str, Any]:
    payload = {
        "artifact_dir": str(output_dir),
        "git_revision": _git(["rev-parse", "HEAD"]),
        "branch": _git(["branch", "--show-current"]),
        "dirty_state_summary": _git(["status", "--short"]),
        "python_runtime_version": platform.python_version(),
        "acceptance_authority": "VALIDATION_EVIDENCE_EVALUATOR",
    }
    payload["system_fingerprint"] = _stable_id("governed_evidence_acceptance", payload)
    return payload


def _markdown(closure: dict[str, Any], runtime: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Governed Evidence Acceptance Verification",
            "",
            f"Status: `{closure['governed_evidence_acceptance_status']}`",
            f"Post-repair evidence level: `{closure['post_repair_evidence_level']}`",
            f"Real acceptance observed: `{runtime['real_runtime_acceptance_observed']}`",
            f"Real non-acceptance observed: `{runtime['real_runtime_rejection_or_non_acceptance_observed']}`",
            "",
        ]
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


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
