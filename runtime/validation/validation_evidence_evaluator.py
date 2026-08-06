from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
)


class ValidationEvidenceEvaluator:
    """Compares captured validation results and records governed evidence state."""

    BOUNDARY = (
        "VALIDATION_EVIDENCE_EVALUATION_CONTRACT_MAY_AUTHORIZE_COMPARISON_AND_EVIDENCE_CLASSIFICATION_FOR_ONE_DURABLE_RAW_RESULT_BUT_CANNOT_MUTATE_THE_ARENA_OR_GRANT_TRUTH_TRUST_GRADUATION_COMPILATION_EXECUTION_OR_DEPLOYMENT_AUTHORITY"
    )
    ACCEPTANCE_DISTINCTION = (
        "EVIDENCE_ACCEPTANCE_DESCRIBES_THE_ADMISSIBILITY_AND_SUFFICIENCY_OF_THE_OBSERVATION_NOT_WHETHER_THE_OBSERVATION_FAVORS_THE_TARGET_CANDIDATE"
    )
    AUTHORITY = "VALIDATION_EVIDENCE_EVALUATOR"
    SCOPE = "CAPTURED_RAW_RESULT_AND_SEALED_REFERENCE_ONLY"
    POLICY_VERSION = "1.0"
    DEFAULT_COMPARATOR_VERSION = "1.0"

    SUPPORTED_COMPARATORS = {
        "exact_structured_output_comparison",
        "exact_grid_comparison",
        "structured_symbolic_output_comparison",
        "manifest_observation_comparison",
    }

    def __init__(
        self,
        root_path: str | os.PathLike[str] = (
            "runtime/state/evidence_acquisition_plans"
        ),
        curriculum_registry: ValidationCurriculumRegistry | None = None,
    ):
        self.root_path = Path(root_path)
        self.pending_path = self.root_path / "pending"
        self.schedules_path = self.root_path / "schedules"
        self.raw_results_path = self.root_path / "raw_results"
        self.evaluation_contracts_path = self.root_path / "evaluation_contracts"
        self.comparable_results_path = self.root_path / "comparable_results"
        self.evidence_decisions_path = self.root_path / "evidence_decisions"
        self.accepted_evidence_path = self.root_path / "accepted_evidence"
        self.curriculum_registry = (
            curriculum_registry or ValidationCurriculumRegistry()
        )

    def evaluate_captured_results(self) -> dict[str, Any]:
        self._initialize()
        reports = []
        for plan_path in self._plan_files(self.pending_path):
            plan, error = self._read_json(plan_path)
            if error or not isinstance(plan, dict):
                continue
            if plan.get("lifecycle_state") in {
                "RAW_RESULT_CAPTURED",
                "COMPARISON_STARTED",
                "COMPARISON_COMPLETED",
            }:
                reports.append(self.evaluate_plan(plan.get("plan_id")))
            elif plan.get("lifecycle_state") in {
                "EVIDENCE_ACCEPTED",
                "EVIDENCE_INSUFFICIENT",
                "EVIDENCE_REJECTED",
            }:
                reports.append(self.evaluate_plan(plan.get("plan_id")))
        terminal = [
            report for report in reports
            if report.get("evidence_acceptance_state")
            in {"ACCEPTED", "INSUFFICIENT", "REJECTED"}
        ]
        current = terminal[0] if terminal else reports[0] if reports else {}
        return {
            "system": "validation_evidence_evaluator",
            "responsible_component": "VALIDATION_EVIDENCE_EVALUATOR",
            "evaluation_attempted": bool(reports),
            "evaluated_result_count": len(terminal),
            "evaluation_reports": reports,
            **self._public_projection(current),
        }

    def evaluate_plan(self, plan_id: str | None) -> dict[str, Any]:
        self._initialize()
        base = self._base_report(plan_id)
        plan, plan_path, plan_error = self._load_plan(plan_id)
        if plan_error or not plan or not plan_path:
            return self._blocked(
                base,
                "BLOCKED_INVALID_PLAN_STATE",
                plan_error or "plan_not_found",
                "plan_load",
                "restore_evidence_plan_before_evaluation",
            )
        existing = self._existing_terminal_decision(plan)
        if existing:
            comparable = self._existing_comparable_result(plan) or {}
            accepted = self._existing_accepted_evidence(existing) or {}
            return self._terminal_report(
                base,
                plan,
                comparable,
                existing,
                accepted,
                comparable_result_creation_result=(
                    "REUSED_EXISTING_COMPARABLE_RESULT"
                    if comparable else "NOT_AVAILABLE"
                ),
                evidence_decision_creation_result=(
                    "REUSED_EXISTING_EVIDENCE_DECISION"
                ),
                accepted_evidence_creation_result=(
                    "REUSED_EXISTING_ACCEPTED_EVIDENCE"
                    if accepted else "NOT_APPLICABLE"
                ),
            )

        admission = self._admission(plan, plan_path)
        if admission["evaluation_admission_state"] != (
            "ADMITTED_TO_VALIDATION_EVIDENCE_EVALUATION"
        ):
            return {**base, **admission}

        schedule = admission["schedule"]
        schedule_path = admission["schedule_path"]
        raw_result = admission["raw_result"]
        raw_path = admission["raw_path"]
        task = admission["task"]
        contract = admission["evaluation_contract"]
        contract_path = admission["evaluation_contract_path"]
        sealed_reference = admission["sealed_reference"]
        comparison_id = self._comparison_id(
            plan,
            schedule,
            raw_result,
            sealed_reference,
            contract,
        )
        comparison_started_at = self._now()
        try:
            started = {
                **plan,
                "updated_at": comparison_started_at,
                "lifecycle_state": "COMPARISON_STARTED",
                "evidence_state": "EVIDENCE_EVALUATION_REVIEW",
                "comparison_state": "COMPARISON_STARTED",
                "comparison_invoked": True,
                "comparison_id": comparison_id,
                "evaluation_contract_id": contract.get("evaluation_contract_id"),
                "evaluation_contract_fingerprint": contract.get(
                    "evaluation_contract_fingerprint"
                ),
                "comparison_started_at": comparison_started_at,
                "active_evaluation_lease": True,
                "evidence_evaluation_authority": self.AUTHORITY,
                "evidence_evaluation_scope": self.SCOPE,
                "arena_evidence_admission_authority": "NONE",
                "arena_decision_authority": "NONE",
                "candidate_execution_authority": "NONE",
                "truth_authority": "NONE",
                "trust_authority": "NONE",
                "graduation_authority": "NONE",
            }
            self._atomic_write(plan_path, started)
            self._atomic_write(contract_path, {
                **contract,
                "review_state": "EVALUATION_REVIEW_STARTED",
                "review_started_at": comparison_started_at,
            })
        except (OSError, TypeError, ValueError) as error:
            return self._blocked(
                {**base, **self._identity(plan, schedule, raw_result)},
                "BLOCKED_EVALUATION_STATE_PERSISTENCE_FAILURE",
                str(error),
                "evaluation_start_persistence",
                "retry_evaluation_start_before_reference_access",
            )

        started_clock = time.perf_counter()
        try:
            comparable = self._compare(
                started,
                schedule,
                raw_result,
                task,
                contract,
                sealed_reference,
                comparison_id,
                comparison_started_at,
            )
        except Exception as error:  # pragma: no cover - defensive boundary
            failure = self._comparison_failure_record(
                started,
                schedule,
                raw_result,
                contract,
                comparison_id,
                comparison_started_at,
                str(error),
            )
            self._persist_comparison_failure(plan_path, failure)
            return {
                **base,
                **self._identity(started, schedule, raw_result),
                "evaluation_admission_evaluated": True,
                "evaluation_admission_state": (
                    "ADMITTED_TO_VALIDATION_EVIDENCE_EVALUATION"
                ),
                "evaluation_admission_reason": (
                    "evidence_evaluation_contract_satisfied"
                ),
                "comparison_invoked": True,
                "comparison_started": True,
                "comparison_completed": False,
                "comparison_state": "COMPARISON_FAILED",
                "comparable_result_available": False,
                "evidence_evaluation_invoked": False,
                "evidence_state": "NOT_EVALUATED",
                "evidence_accepted": False,
                "arena_reentry_invoked": False,
            }
        comparable["comparison_duration"] = round(
            time.perf_counter() - started_clock,
            6,
        )
        comparable_path = (
            self.comparable_results_path
            / f"{comparable['comparable_result_id']}.json"
        )
        try:
            self._atomic_write(comparable_path, comparable)
            compared_plan = {
                **started,
                "updated_at": self._now(),
                "lifecycle_state": "COMPARISON_COMPLETED",
                "comparison_state": "COMPARISON_COMPLETED",
                "comparable_result_id": comparable["comparable_result_id"],
                "comparable_result_fingerprint": comparable[
                    "comparable_result_fingerprint"
                ],
                "evidence_state": "NOT_YET_DECIDED",
            }
            self._atomic_write(plan_path, compared_plan)
        except (OSError, TypeError, ValueError) as error:
            return {
                **base,
                **self._identity(started, schedule, raw_result),
                "evaluation_admission_evaluated": True,
                "evaluation_admission_state": (
                    "ADMITTED_TO_VALIDATION_EVIDENCE_EVALUATION"
                ),
                "evaluation_admission_reason": (
                    "evidence_evaluation_contract_satisfied"
                ),
                "comparison_invoked": True,
                "comparison_started": True,
                "comparison_completed": False,
                "comparison_state": "COMPARISON_FAILED",
                "comparison_failure_reason": str(error),
                "comparable_result_available": False,
                "evidence_evaluation_invoked": False,
                "evidence_state": "NOT_EVALUATED",
                "evidence_accepted": False,
                "arena_reentry_invoked": False,
            }

        decision = self._evidence_decision(
            compared_plan,
            schedule,
            raw_result,
            comparable,
            contract,
        )
        decision_path = (
            self.evidence_decisions_path
            / f"{decision['evidence_decision_id']}.json"
        )
        terminal = decision["evidence_acceptance_state"]
        accepted_artifact: dict[str, Any] = {}
        try:
            self._atomic_write(decision_path, decision)
            if terminal == "ACCEPTED":
                accepted_artifact = self._accepted_evidence_artifact(
                    compared_plan,
                    schedule,
                    raw_result,
                    comparable,
                    decision,
                )
                self._atomic_write(
                    self.accepted_evidence_path
                    / f"{accepted_artifact['accepted_evidence_id']}.json",
                    accepted_artifact,
                )
            final_plan = self._terminal_plan_record(
                compared_plan,
                comparable,
                decision,
                accepted_artifact,
            )
            self._atomic_write(plan_path, final_plan)
            self._link_schedule_and_raw_result(
                schedule,
                schedule_path,
                raw_result,
                raw_path,
                comparable,
                decision,
                accepted_artifact,
            )
        except (OSError, TypeError, ValueError) as error:
            return {
                **base,
                **self._identity(compared_plan, schedule, raw_result),
                "evaluation_admission_evaluated": True,
                "evaluation_admission_state": (
                    "ADMITTED_TO_VALIDATION_EVIDENCE_EVALUATION"
                ),
                "evaluation_admission_reason": (
                    "evidence_evaluation_contract_satisfied"
                ),
                "comparison_invoked": True,
                "comparison_started": True,
                "comparison_completed": True,
                "comparison_state": "COMPARISON_COMPLETED",
                "comparable_result_available": True,
                "evidence_evaluation_invoked": True,
                "evidence_decision_recorded": False,
                "evidence_state": "NOT_YET_DECIDED",
                "evidence_accepted": False,
                "evidence_decision_creation_result": (
                    "EVIDENCE_DECISION_PERSISTENCE_FAILED"
                ),
                "evaluation_failure_reason": str(error),
                "arena_reentry_invoked": False,
            }

        return self._terminal_report(
            base,
            {**compared_plan, "lifecycle_state": f"EVIDENCE_{terminal}"},
            comparable,
            decision,
            accepted_artifact,
            comparable_result_creation_result="CREATED_NEW_COMPARABLE_RESULT",
            evidence_decision_creation_result="CREATED_NEW_EVIDENCE_DECISION",
            accepted_evidence_creation_result=(
                "CREATED_NEW_ACCEPTED_EVIDENCE"
                if terminal == "ACCEPTED"
                else "NOT_APPLICABLE"
            ),
        )

    def _admission(
        self,
        plan: dict[str, Any],
        plan_path: Path,
    ) -> dict[str, Any]:
        if plan.get("lifecycle_state") != "RAW_RESULT_CAPTURED":
            return self._admission_block(
                "BLOCKED_INVALID_PLAN_STATE",
                f"expected_RAW_RESULT_CAPTURED_observed_{plan.get('lifecycle_state')}",
                "plan_lifecycle",
                "restore_raw_result_captured_state_before_evaluation",
            )
        if plan.get("active_evaluation_lease") is True:
            return self._admission_block(
                "BLOCKED_ACTIVE_EVALUATION",
                "active_evaluation_lease_present",
                "evaluation_lease",
                "recover_or_clear_evaluation_lease",
            )
        for field in (
            "truth_authority",
            "trust_authority",
            "graduation_authority",
            "candidate_execution_authority",
        ):
            if plan.get(field) != "NONE":
                return self._admission_block(
                    "BLOCKED_CONSTITUTIONAL_VIOLATION",
                    f"{field}_not_none",
                    "authority_validation",
                    "restore_constitutional_authority_boundaries",
                )
        schedule, schedule_path, schedule_error = self._load_schedule(
            plan.get("schedule_id")
        )
        if schedule_error or not schedule or not schedule_path:
            return self._admission_block(
                "BLOCKED_MISSING_SCHEDULE",
                schedule_error or "schedule_not_found",
                "schedule_load",
                "restore_linked_schedule",
            )
        raw_result, raw_path, raw_error = self._load_raw_result(
            plan.get("raw_result_id")
        )
        if raw_error or not raw_result or not raw_path:
            return self._admission_block(
                "BLOCKED_MISSING_RAW_RESULT",
                raw_error or "raw_result_not_found",
                "raw_result_load",
                "restore_linked_raw_result",
            )
        alignment = self._alignment_failures(plan, schedule, raw_result)
        if alignment:
            return self._admission_block(
                "BLOCKED_RECORD_ALIGNMENT_FAILURE",
                ",".join(alignment),
                "record_alignment",
                "repair_plan_schedule_raw_result_alignment",
            )
        envelope = (
            raw_result.get("RAW_VALIDATION_RESULT_ENVELOPE")
            or raw_result.get("raw_validation_result_envelope")
            or {}
        )
        if not isinstance(envelope, dict) or not envelope:
            return self._admission_block(
                "BLOCKED_RAW_VALIDATION_PROVENANCE_UNBOUND",
                "RAW_VALIDATION_IDENTITY_INPUT_UNAVAILABLE",
                "raw_validation_result_provenance",
                "repair_raw_validation_result_identity_without_evidence_evaluation",
            )
        if envelope.get("binding_integrity_state") != "BOUND":
            return self._admission_block(
                "BLOCKED_RAW_VALIDATION_BINDING_CONFLICTED",
                envelope.get("structural_ineligibility_reason")
                or "RAW_RESULT_BINDING_CONFLICTED",
                "raw_validation_result_binding",
                "repair_raw_validation_result_binding_without_evidence_evaluation",
            )
        if envelope.get("downstream_structural_eligibility") != "STRUCTURALLY_ELIGIBLE":
            return self._admission_block(
                "BLOCKED_RAW_VALIDATION_STRUCTURALLY_INELIGIBLE",
                envelope.get("structural_ineligibility_reason")
                or "RAW_RESULT_STRUCTURALLY_INELIGIBLE",
                "raw_validation_result_structural_eligibility",
                "do_not_evaluate_raw_result_until_identity_and_provenance_are_bound",
            )
        if raw_result.get("result_state") != "RAW_RESULT_CAPTURED":
            return self._admission_block(
                "BLOCKED_INVALID_RAW_RESULT_STATE",
                f"observed_{raw_result.get('result_state')}",
                "raw_result_state",
                "restore_raw_result_capture_record",
            )
        if raw_result.get("evidence_acceptance_state") in {
            "ACCEPTED",
            "INSUFFICIENT",
            "REJECTED",
        }:
            return self._admission_block(
                "BLOCKED_EXISTING_TERMINAL_DECISION",
                "raw_result_already_has_terminal_decision",
                "terminal_decision_guard",
                "reuse_existing_evidence_decision",
            )
        if raw_result.get("predicted_output") is None:
            return self._admission_block(
                "BLOCKED_MISSING_PREDICTION",
                "predicted_output_missing",
                "prediction_payload",
                "recover_raw_result_prediction_payload",
            )
        if (
            raw_result.get("runner_trace_reference", {}).get(
                "target_reference_forwarded_to_solver"
            )
            is True
        ):
            return self._admission_block(
                "BLOCKED_TARGET_LEAKAGE_RISK",
                "execution_trace_reports_target_forwarded_to_solver",
                "target_leakage_prevention",
                "reject_or_reexecute_without_target_leakage",
            )
        lookup = self.curriculum_registry.find_task(
            plan.get("selected_validation_task_id"),
            plan.get("selected_curriculum_id"),
        )
        if not lookup.get("found"):
            return {
                **self._identity(plan, schedule, raw_result),
                **self._admission_block(
                "BLOCKED_MISSING_EVALUATION_CONTRACT",
                "validation_task_not_found",
                "task_resolution",
                "restore_validation_curriculum",
                ),
            }
        task = lookup.get("task") or {}
        raw_task = task.get("raw_task") or {}
        contract = self._evaluation_contract(raw_task)
        if not contract:
            return {
                **self._identity(plan, schedule, raw_result),
                **self._admission_block(
                "BLOCKED_MISSING_EVALUATION_CONTRACT",
                "evaluation_contract_missing",
                "evaluation_contract_resolution",
                "add_explicit_validation_evaluation_contract",
                ),
            }
        comparator_id = self._term(contract.get("comparator_id"))
        if comparator_id not in self.SUPPORTED_COMPARATORS:
            return self._admission_block(
                "BLOCKED_UNSUPPORTED_COMPARATOR",
                f"unsupported_comparator_{comparator_id}",
                "comparator_resolution",
                "register_supported_deterministic_comparator",
            )
        sealed_reference = self._sealed_reference(raw_task, contract)
        if sealed_reference.get("expected_output") is None:
            return self._admission_block(
                "BLOCKED_MISSING_SEALED_REFERENCE",
                "expected_output_missing",
                "sealed_reference_resolution",
                "restore_evaluator_only_reference",
            )
        if not sealed_reference.get("sealed_reference_fingerprint"):
            return self._admission_block(
                "BLOCKED_REFERENCE_INTEGRITY_FAILURE",
                "sealed_reference_fingerprint_missing",
                "sealed_reference_integrity",
                "rebuild_sealed_reference_metadata",
            )
        for field in (
            "required_evidence",
            "required_evidence_category",
            "target_candidate",
            "target_operation",
        ):
            if self._term(plan.get(field)) == "Not Available":
                return self._admission_block(
                    "BLOCKED_INVALID_PLAN_STATE",
                    f"missing_{field}",
                    "evidence_plan_payload",
                    "repair_evidence_plan_payload",
                )
        evaluation_contract = self._evaluation_contract_record(
            plan,
            schedule,
            raw_result,
            task,
            contract,
            sealed_reference,
        )
        existing_contract = self._existing_evaluation_contract(evaluation_contract)
        evaluation_contract = existing_contract or evaluation_contract
        contract_path = (
            self.evaluation_contracts_path
            / f"{evaluation_contract['evaluation_contract_id']}.json"
        )
        try:
            if not existing_contract:
                self._atomic_write(contract_path, evaluation_contract)
        except (OSError, TypeError, ValueError):
            return {
                **self._identity(plan, schedule, raw_result),
                **self._admission_block(
                    "DEFERRED_VALIDATION_EVIDENCE_EVALUATION",
                    "evaluation_contract_persistence_unavailable",
                    "evaluation_contract_persistence",
                    "retry_evaluation_contract_persistence",
                ),
            }
        return {
            "evaluation_admission_state": (
                "ADMITTED_TO_VALIDATION_EVIDENCE_EVALUATION"
            ),
            "evaluation_admission_reason": "evidence_evaluation_contract_satisfied",
            "blocked_stage": "none",
            "responsible_component": "VALIDATION_EVIDENCE_EVALUATOR",
            "recommended_action": "compare_raw_result_with_sealed_reference",
            "plan": plan,
            "plan_path": plan_path,
            "schedule": schedule,
            "schedule_path": schedule_path,
            "raw_result": raw_result,
            "raw_path": raw_path,
            "task": task,
            "evaluation_contract": evaluation_contract,
            "evaluation_contract_path": contract_path,
            "sealed_reference": sealed_reference,
        }

    def _compare(
        self,
        plan: dict[str, Any],
        schedule: dict[str, Any],
        raw_result: dict[str, Any],
        task: dict[str, Any],
        contract: dict[str, Any],
        sealed_reference: dict[str, Any],
        comparison_id: str,
        comparison_started_at: str,
    ) -> dict[str, Any]:
        predicted_cases = raw_result.get("case_outputs") or []
        expected_cases = self._expected_cases(sealed_reference)
        case_results = []
        exact_matches = 0
        invalid_cases = 0
        for index in range(max(len(predicted_cases), len(expected_cases))):
            predicted_available = index < len(predicted_cases)
            expected_available = index < len(expected_cases)
            predicted = (
                predicted_cases[index].get("output")
                if predicted_available
                and isinstance(predicted_cases[index], dict)
                else None
            )
            expected = expected_cases[index] if expected_available else None
            schema_valid = predicted_available and expected_available
            exact_match = schema_valid and predicted == expected
            if exact_match:
                exact_matches += 1
            if not schema_valid:
                invalid_cases += 1
            case_results.append({
                "case_index": index,
                "case_id": (
                    predicted_cases[index].get("case_id")
                    if predicted_available
                    and isinstance(predicted_cases[index], dict)
                    else f"missing_prediction_{index}"
                ),
                "prediction_present": predicted_available,
                "reference_present": expected_available,
                "prediction_schema_valid": predicted_available,
                "reference_schema_valid": expected_available,
                "exact_match": exact_match,
                "comparison_status": "COMPARED" if schema_valid else "INCOMPLETE",
            })
        expected_count = len(expected_cases)
        predicted_count = len(predicted_cases)
        compared_count = sum(
            1
            for row in case_results
            if row.get("prediction_present") and row.get("reference_present")
        )
        exact_match_rate = round(
            exact_matches / max(compared_count, 1),
            4,
        )
        case_coverage = round(
            compared_count / max(expected_count, 1),
            4,
        )
        fingerprint = self._comparable_fingerprint(
            plan,
            schedule,
            raw_result,
            sealed_reference,
            contract,
        )
        return {
            "schema_version": "1.0",
            "comparable_result_id": (
                f"comparable_result_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
            ),
            "comparable_result_fingerprint": fingerprint,
            "comparison_id": comparison_id,
            **self._identity(plan, schedule, raw_result),
            "comparator_id": contract.get("comparator_id"),
            "comparator_version": contract.get(
                "comparator_version",
                self.DEFAULT_COMPARATOR_VERSION,
            ),
            "evaluation_contract_id": contract.get("evaluation_contract_id"),
            "evaluation_contract_fingerprint": contract.get(
                "evaluation_contract_fingerprint",
                self._contract_fingerprint(contract),
            ),
            "evaluation_contract_source": contract.get(
                "contract_source",
                "explicit_evaluation_contract",
            ),
            "sealed_reference_id": sealed_reference.get("sealed_reference_id"),
            "sealed_reference_fingerprint": sealed_reference.get(
                "sealed_reference_fingerprint"
            ),
            "sealed_reference_resolved": sealed_reference.get(
                "sealed_reference_resolved",
                True,
            ),
            "reference_integrity_state": sealed_reference.get(
                "reference_integrity_state",
                "VERIFIED",
            ),
            "target_reference_forwarded_to_solver": False,
            "sealed_reference_opened_by_evaluator": True,
            "sealed_reference_forwarded_to_solver": False,
            "comparison_started_at": comparison_started_at,
            "comparison_completed_at": self._now(),
            "comparison_duration": 0,
            "predicted_output_schema_valid": raw_result.get("predicted_output")
            is not None,
            "reference_output_schema_valid": expected_count > 0,
            "expected_case_count": expected_count,
            "predicted_case_count": predicted_count,
            "case_count": expected_count,
            "compared_case_count": compared_count,
            "valid_case_count": compared_count,
            "invalid_case_count": invalid_cases,
            "case_coverage": case_coverage,
            "case_comparison_results": case_results,
            "exact_match_count": exact_matches,
            "exact_match_rate": exact_match_rate,
            "comparator_defined_measurements": {
                "exact_match_rate": exact_match_rate,
                "case_coverage": case_coverage,
            },
            "grounding_measurements": {
                "required_evidence": plan.get("required_evidence"),
                "target_candidate": plan.get("target_candidate"),
                "target_operation": plan.get("target_operation"),
            },
            "structural_measurements": {
                "missing_output_count": max(expected_count - predicted_count, 0),
                "extra_output_count": max(predicted_count - expected_count, 0),
            },
            "comparison_status": "SUCCESS",
            "comparison_state": "COMPARISON_COMPLETED",
            "runtime_error": None,
            "evidence_state": "NOT_YET_DECIDED",
            "arena_reentry_invoked": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_compilation_authority": "NONE",
            "deployment_authority": "NONE",
        }

    def _evidence_decision(
        self,
        plan: dict[str, Any],
        schedule: dict[str, Any],
        raw_result: dict[str, Any],
        comparable: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        leakage = raw_result.get("runner_trace_reference", {}).get(
            "target_reference_forwarded_to_solver"
        ) is True
        attribution_ok = (
            self._term(plan.get("target_candidate")) != "Not Available"
            and self._term(plan.get("target_operation")) != "Not Available"
        )
        contamination_ok = not leakage
        admissible = attribution_ok and contamination_ok
        minimum_case_coverage = float(contract.get("minimum_case_coverage", 1.0))
        exact_required = bool(contract.get("exact_match_required", False))
        sufficient = (
            comparable.get("case_coverage", 0.0) >= minimum_case_coverage
            and comparable.get("compared_case_count", 0) > 0
        )
        if exact_required:
            sufficient = sufficient and comparable.get("exact_match_rate") == 1.0
        if not admissible:
            acceptance = "REJECTED"
            sufficiency_state = "NOT_EVALUATED"
        elif sufficient:
            acceptance = "ACCEPTED"
            sufficiency_state = "SUFFICIENT"
        else:
            acceptance = "INSUFFICIENT"
            sufficiency_state = "INSUFFICIENT"
        if leakage:
            direction = "NOT_DETERMINED"
            direction_reason = "target_leakage_or_reference_integrity_failure"
        elif comparable.get("exact_match_rate") == 1.0:
            direction = "SUPPORTING"
            direction_reason = "all_compared_cases_exact_match"
        elif comparable.get("compared_case_count", 0) > 0:
            direction = "CONTRADICTING"
            direction_reason = "compared_result_differs_from_reference"
        else:
            direction = "INCONCLUSIVE"
            direction_reason = "no_comparable_cases"
        fingerprint = self._decision_fingerprint(
            plan,
            schedule,
            raw_result,
            comparable,
            contract,
        )
        reason = (
            "evidence_contract_satisfied"
            if acceptance == "ACCEPTED"
            else "validation_result_does_not_fully_satisfy_required_evidence_contract"
            if acceptance == "INSUFFICIENT"
            else "target_leakage_or_reference_integrity_failure"
            if leakage
            else "evidence_admissibility_failed"
        )
        return {
            "schema_version": "1.0",
            "evidence_decision_id": (
                f"evidence_decision_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
            ),
            "evidence_decision_fingerprint": fingerprint,
            "evaluation_contract_id": contract.get("evaluation_contract_id"),
            "evaluation_contract_fingerprint": contract.get(
                "evaluation_contract_fingerprint",
                self._contract_fingerprint(contract),
            ),
            "comparable_result_id": comparable.get("comparable_result_id"),
            "comparable_result_fingerprint": comparable.get(
                "comparable_result_fingerprint"
            ),
            **self._identity(plan, schedule, raw_result),
            "evidence_evaluation_authority": self.AUTHORITY,
            "evidence_evaluation_scope": self.SCOPE,
            "evidence_admissibility_evaluated": True,
            "evidence_admissibility_state": (
                "ADMISSIBLE" if admissible else "INADMISSIBLE"
            ),
            "evidence_admissibility_reason": (
                "provenance_alignment_reference_integrity_and_attribution_clear"
                if admissible
                else "target_leakage_or_reference_integrity_failure"
                if leakage
                else "candidate_or_operation_attribution_missing"
            ),
            "evidence_sufficiency_evaluated": True,
            "evidence_sufficiency_state": sufficiency_state,
            "evidence_sufficiency_reason": (
                "minimum_case_coverage_and_contract_requirements_satisfied"
                if sufficiency_state == "SUFFICIENT"
                else "not_evaluated_for_inadmissible_evidence"
                if sufficiency_state == "NOT_EVALUATED"
                else "case_coverage_or_exact_match_requirement_not_satisfied"
            ),
            "evidence_direction_calculated": True,
            "evidence_direction": direction,
            "evidence_direction_reason": direction_reason,
            "evidence_acceptance_state": acceptance,
            "evidence_evaluation_outcome": f"EVIDENCE_{acceptance}",
            "evidence_acceptance_reason": reason,
            "outcome_reason": reason,
            "evidence_decision_recorded": True,
            "evidence_contamination_state": (
                "CLEAR" if contamination_ok else "CONTAMINATED"
            ),
            "independent_validation_state": "INDEPENDENT_RAW_RESULT",
            "candidate_attribution_state": (
                "ATTRIBUTED" if attribution_ok else "MISSING_ATTRIBUTION"
            ),
            "operation_attribution_state": (
                "ATTRIBUTED"
                if self._term(plan.get("target_operation")) != "Not Available"
                else "MISSING_ATTRIBUTION"
            ),
            "duplicate_evidence_detected": bool(
                self._existing_decision_by_fingerprint(fingerprint)
            ),
            "accepted_evidence_artifact_created": acceptance == "ACCEPTED",
            "evidence_accepted": acceptance == "ACCEPTED",
            "arena_evidence_admission_invoked": False,
            "arena_reentry_invoked": False,
            "candidate_score_changed": False,
            "candidate_ranking_changed": False,
            "tie_resolved": False,
            "winner_selected": False,
            "truth_granted": False,
            "trust_granted": False,
            "graduation_granted": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_compilation_authority": "NONE",
            "deployment_authority": "NONE",
            "constitutional_boundary": self.BOUNDARY,
            "constitutional_distinction": self.ACCEPTANCE_DISTINCTION,
            "next_consumer": self._next_consumer(acceptance),
            "created_at": self._now(),
        }

    def _accepted_evidence_artifact(
        self,
        plan: dict[str, Any],
        schedule: dict[str, Any],
        raw_result: dict[str, Any],
        comparable: dict[str, Any],
        decision: dict[str, Any],
    ) -> dict[str, Any]:
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "decision": decision.get("evidence_decision_fingerprint"),
                    "plan": plan.get("plan_id"),
                    "raw_result": raw_result.get("raw_result_id"),
                },
                sort_keys=True,
                ensure_ascii=True,
            ).encode("utf-8")
        ).hexdigest()
        return {
            "schema_version": "1.0",
            "accepted_evidence_id": (
                f"accepted_evidence_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
            ),
            "accepted_evidence_fingerprint": fingerprint,
            "acceptance_authority": self.AUTHORITY,
            "acceptance_scope": "EVIDENCE_RECORDING_ONLY",
            **self._identity(plan, schedule, raw_result),
            "comparable_result_id": comparable.get("comparable_result_id"),
            "evidence_decision_id": decision.get("evidence_decision_id"),
            "originating_arena_id": plan.get(
                "originating_arena_id",
                "arena_current_deliberation",
            ),
            "originating_arena_snapshot_id": plan.get(
                "originating_arena_snapshot_id",
                f"arena_snapshot_{hashlib.sha1(str(plan.get('plan_id')).encode()).hexdigest()[:12]}",
            ),
            "originating_arena_snapshot": self._originating_arena_snapshot(plan),
            "evidence_direction": decision.get("evidence_direction"),
            "evidence_acceptance_state": "ACCEPTED",
            "evidence_state": "EVIDENCE_ACCEPTED",
            "arena_admission_state": "NOT_EVALUATED",
            "arena_consumed": False,
            "arena_evidence_admission_invoked": False,
            "arena_reentry_invoked": False,
            "candidate_score_changed": False,
            "candidate_ranking_changed": False,
            "tie_resolved": False,
            "winner_selected": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_compilation_authority": "NONE",
            "deployment_authority": "NONE",
            "next_consumer": "FUTURE_ARENA_EVIDENCE_ADMISSION_GATE",
            "constitutional_boundary": self.BOUNDARY,
            "created_at": self._now(),
        }

    def _originating_arena_snapshot(self, plan: dict[str, Any]) -> dict[str, Any]:
        target = plan.get("target_candidate")
        operation = plan.get("target_operation")
        target_fingerprint = self._fingerprint({
            "candidate_id": target,
            "operation": operation,
        })
        candidates = plan.get("originating_arena_candidates")
        if not isinstance(candidates, list) or not candidates:
            candidates = [{
                "candidate_id": target,
                "candidate_fingerprint": target_fingerprint,
                "source": plan.get("source_candidate_id", "validation_target"),
                "operation": operation,
                "baseline_score": float(plan.get("target_candidate_score", 0.5) or 0.5),
                "eligible_for_proposal": True,
            }]
        normalized = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            row = dict(candidate)
            row.setdefault("candidate_id", target)
            row.setdefault("operation", operation)
            row.setdefault("baseline_score", 0.5)
            row.setdefault("eligible_for_proposal", True)
            row.setdefault(
                "candidate_fingerprint",
                self._fingerprint({
                    "candidate_id": row.get("candidate_id"),
                    "operation": row.get("operation"),
                }),
            )
            normalized.append(row)
        snapshot = {
            "arena_id": plan.get("originating_arena_id", "arena_current_deliberation"),
            "arena_state": "TIE_REQUIRES_REVIEW",
            "selected_candidate": "NONE",
            "winner_selected": False,
            "execution_mode": "BLOCKED",
            "cross_source_consensus_state": "NO_CROSS_SOURCE_CONSENSUS",
            "candidate_rows": normalized,
            "target_candidate": target,
            "target_candidate_fingerprint": target_fingerprint,
            "target_operation": operation,
            "tie_break_strategy": plan.get("tie_break_strategy"),
        }
        snapshot["originating_arena_snapshot_fingerprint"] = self._fingerprint(
            snapshot
        )
        return snapshot

    def _terminal_plan_record(
        self,
        plan: dict[str, Any],
        comparable: dict[str, Any],
        decision: dict[str, Any],
        accepted: dict[str, Any],
    ) -> dict[str, Any]:
        terminal = decision.get("evidence_acceptance_state")
        route = {
            "ACCEPTED": "EVIDENCE_ACCEPTED_TO_ARENA_EVIDENCE_ADMISSION_GATE",
            "INSUFFICIENT": "EVIDENCE_INSUFFICIENT_TO_EVIDENCE_REMEDIATION_PLANNER",
            "REJECTED": "EVIDENCE_REJECTED_TO_EVIDENCE_REVIEW_OR_REPLAN",
        }.get(terminal, "EVIDENCE_EVALUATION_REVIEW")
        return {
            **plan,
            "updated_at": self._now(),
            "lifecycle_state": f"EVIDENCE_{terminal}",
            "evidence_state": f"EVIDENCE_{terminal}",
            "comparison_state": "COMPARISON_COMPLETED",
            "comparison_id": comparable.get("comparison_id"),
            "comparable_result_id": comparable.get("comparable_result_id"),
            "comparable_result_fingerprint": comparable.get(
                "comparable_result_fingerprint"
            ),
            "evidence_decision_id": decision.get("evidence_decision_id"),
            "evidence_decision_fingerprint": decision.get(
                "evidence_decision_fingerprint"
            ),
            "accepted_evidence_id": accepted.get("accepted_evidence_id"),
            "evidence_acceptance_state": terminal,
            "evidence_evaluation_outcome": f"EVIDENCE_{terminal}",
            "validation_evidence_evaluation_state": (
                "VALIDATION_EVIDENCE_EVALUATION_COMPLETED"
            ),
            "evidence_accepted": terminal == "ACCEPTED",
            "active_evaluation_lease": False,
            "boot_recovery_route": route,
            "arena_evidence_admission_invoked": False,
            "arena_reentry_invoked": False,
            "candidate_score_changed": False,
            "candidate_ranking_changed": False,
            "tie_resolved": False,
            "winner_selected": False,
            "candidate_execution_authority": "NONE",
            "candidate_compilation_authority": "NONE",
            "deployment_authority": "NONE",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
        }

    def _terminal_report(
        self,
        base: dict[str, Any],
        plan: dict[str, Any],
        comparable: dict[str, Any],
        decision: dict[str, Any],
        accepted: dict[str, Any],
        *,
        comparable_result_creation_result: str,
        evidence_decision_creation_result: str,
        accepted_evidence_creation_result: str,
    ) -> dict[str, Any]:
        terminal = decision.get("evidence_acceptance_state", "NOT_EVALUATED")
        return {
            **base,
            **self._identity(plan, {}, {}),
            "schedule_id": decision.get("schedule_id", plan.get("schedule_id")),
            "execution_id": decision.get("execution_id", plan.get("execution_id")),
            "raw_result_id": decision.get("raw_result_id", plan.get("raw_result_id")),
            "comparable_result_id": comparable.get("comparable_result_id"),
            "evidence_decision_id": decision.get("evidence_decision_id"),
            "accepted_evidence_id": accepted.get("accepted_evidence_id"),
            "evaluation_contract_id": decision.get("evaluation_contract_id"),
            "evaluation_contract_fingerprint": decision.get(
                "evaluation_contract_fingerprint"
            ),
            "selected_validation_task_id": decision.get(
                "selected_validation_task_id",
                plan.get("selected_validation_task_id"),
            ),
            "selected_curriculum_id": decision.get(
                "selected_curriculum_id",
                plan.get("selected_curriculum_id"),
            ),
            "target_candidate": decision.get("target_candidate"),
            "target_operation": decision.get("target_operation"),
            "required_evidence": decision.get("required_evidence"),
            "required_evidence_category": decision.get(
                "required_evidence_category"
            ),
            "tie_break_strategy": decision.get("tie_break_strategy"),
            "evaluation_admission_evaluated": True,
            "evaluation_admission_state": (
                "ADMITTED_TO_VALIDATION_EVIDENCE_EVALUATION"
            ),
            "evaluation_admission_reason": "evidence_evaluation_contract_satisfied",
            "evidence_evaluation_authority": self.AUTHORITY,
            "evidence_evaluation_scope": self.SCOPE,
            "sealed_reference_available": True,
            "sealed_reference_id": comparable.get("sealed_reference_id"),
            "sealed_reference_fingerprint": comparable.get(
                "sealed_reference_fingerprint"
            ),
            "sealed_reference_resolved": comparable.get(
                "sealed_reference_resolved",
                True,
            ),
            "sealed_reference_opened_by_evaluator": True,
            "sealed_reference_forwarded_to_solver": False,
            "target_reference_forwarded_to_solver": False,
            "sealed_reference_forwarded_to_candidate": False,
            "sealed_reference_forwarded_to_training": False,
            "sealed_reference_used_for_repair": False,
            "sealed_reference_used_for_resynthesis": False,
            "reference_integrity_state": "VERIFIED",
            "comparison_invoked": True,
            "comparison_started": True,
            "comparison_completed": True,
            "comparison_state": "COMPARISON_COMPLETED",
            "comparator_id": comparable.get("comparator_id"),
            "comparator_version": comparable.get("comparator_version"),
            "comparator_resolved": bool(comparable.get("comparator_id")),
            "comparable_result_available": True,
            "comparable_result_creation_result": comparable_result_creation_result,
            "expected_case_count": comparable.get("expected_case_count"),
            "compared_case_count": comparable.get("compared_case_count"),
            "case_coverage": comparable.get("case_coverage"),
            "exact_match_count": comparable.get("exact_match_count"),
            "exact_match_rate": comparable.get("exact_match_rate"),
            "exact_match": comparable.get("exact_match_rate") == 1.0,
            "accuracy": comparable.get("exact_match_rate"),
            "difference_count": (
                (comparable.get("compared_case_count") or 0)
                - (comparable.get("exact_match_count") or 0)
            ),
            "shape_compatibility_state": (
                "COMPATIBLE"
                if comparable.get("invalid_case_count", 0) == 0
                else "INCOMPATIBLE"
            ),
            "comparator_measurement_summary": comparable.get(
                "comparator_defined_measurements"
            ),
            "grounding_measurement_summary": comparable.get(
                "grounding_measurements"
            ),
            "evidence_evaluation_invoked": True,
            "evidence_admissibility_evaluated": True,
            "evidence_admissibility_state": decision.get(
                "evidence_admissibility_state"
            ),
            "evidence_admissibility_reason": decision.get(
                "evidence_admissibility_reason"
            ),
            "evidence_sufficiency_evaluated": True,
            "evidence_sufficiency_state": decision.get("evidence_sufficiency_state"),
            "evidence_sufficiency_reason": decision.get(
                "evidence_sufficiency_reason"
            ),
            "evidence_direction_calculated": True,
            "evidence_direction": decision.get("evidence_direction"),
            "evidence_direction_reason": decision.get("evidence_direction_reason"),
            "evidence_acceptance_state": terminal,
            "evidence_evaluation_outcome": decision.get(
                "evidence_evaluation_outcome",
                f"EVIDENCE_{terminal}",
            ),
            "evidence_acceptance_reason": decision.get("evidence_acceptance_reason"),
            "outcome_reason": decision.get("outcome_reason"),
            "evidence_decision_recorded": True,
            "evidence_decision_creation_result": evidence_decision_creation_result,
            "evidence_contamination_state": decision.get(
                "evidence_contamination_state"
            ),
            "independent_validation_state": decision.get(
                "independent_validation_state"
            ),
            "candidate_attribution_state": decision.get(
                "candidate_attribution_state"
            ),
            "operation_attribution_state": decision.get(
                "operation_attribution_state"
            ),
            "duplicate_evidence_detected": decision.get(
                "duplicate_evidence_detected",
                False,
            ),
            "accepted_evidence_artifact_created": bool(accepted),
            "accepted_evidence_creation_result": accepted_evidence_creation_result,
            "evidence_accepted": terminal == "ACCEPTED",
            "arena_evidence_admission_invoked": False,
            "arena_reentry_invoked": False,
            "candidate_score_changed": False,
            "candidate_ranking_changed": False,
            "tie_resolved": False,
            "winner_selected": False,
            "truth_granted": False,
            "trust_granted": False,
            "graduation_granted": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_compilation_authority": "NONE",
            "deployment_authority": "NONE",
            "next_consumer": self._next_consumer(terminal),
            "constitutional_boundary": self.BOUNDARY,
        }

    def _evaluation_contract_record(
        self,
        plan: dict[str, Any],
        schedule: dict[str, Any],
        raw_result: dict[str, Any],
        task: dict[str, Any],
        contract: dict[str, Any],
        sealed_reference: dict[str, Any],
    ) -> dict[str, Any]:
        identity = self._identity(plan, schedule, raw_result)
        fingerprint_payload = {
            **identity,
            "sealed_reference_fingerprint": sealed_reference.get(
                "sealed_reference_fingerprint"
            ),
            "comparator_id": contract.get("comparator_id"),
            "comparator_version": contract.get("comparator_version"),
            "metric_id": contract.get("metric_id", "exact_match_rate"),
            "metric_version": contract.get("metric_version", "1.0"),
            "acceptance_threshold": contract.get("acceptance_threshold", 1.0),
            "exact_match_required": contract.get("exact_match_required", False),
            "evaluation_policy_version": self.POLICY_VERSION,
        }
        fingerprint = self._fingerprint(fingerprint_payload)
        target_candidate = plan.get("target_candidate")
        return {
            "schema_version": "1.0",
            "evaluation_contract_id": (
                f"validation_evidence_evaluation_contract_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
            ),
            "evaluation_contract_fingerprint": fingerprint,
            "evaluation_contract_version": "1.0",
            "evaluation_policy_id": "governed_raw_validation_result_evaluation",
            "evaluation_policy_version": self.POLICY_VERSION,
            "evidence_plan_id": plan.get("plan_id"),
            "validation_schedule_id": schedule.get("schedule_id"),
            "validation_execution_id": raw_result.get("execution_id"),
            "raw_validation_result_id": (
                raw_result.get("raw_validation_result_id")
                or raw_result.get("raw_result_id")
            ),
            "raw_validation_result_fingerprint": raw_result.get(
                "raw_result_fingerprint"
            ),
            "originating_arena_id": plan.get(
                "originating_arena_id",
                "arena_current_deliberation",
            ),
            "originating_arena_version": plan.get("originating_arena_version", "1.0"),
            "baseline_arena_snapshot_id": plan.get(
                "originating_arena_snapshot_id",
                "Not Available",
            ),
            "target_candidate_id": target_candidate,
            "target_candidate_fingerprint": plan.get(
                "target_candidate_fingerprint",
                self._fingerprint({
                    "candidate_id": target_candidate,
                    "operation": plan.get("target_operation"),
                }),
            ),
            "target_candidate_source": plan.get(
                "source_candidate_id",
                raw_result.get("target_candidate"),
            ),
            "target_operation": plan.get("target_operation"),
            "required_evidence": plan.get("required_evidence"),
            "required_validation_task": plan.get("required_validation_task"),
            "scheduled_validation_task_id": schedule.get(
                "selected_validation_task_id"
            ),
            "sealed_reference_id": sealed_reference.get("sealed_reference_id"),
            "sealed_reference_fingerprint": sealed_reference.get(
                "sealed_reference_fingerprint"
            ),
            "sealed_reference_source": sealed_reference.get(
                "sealed_reference_source"
            ),
            "comparator_id": contract.get("comparator_id"),
            "comparator_version": contract.get(
                "comparator_version",
                self.DEFAULT_COMPARATOR_VERSION,
            ),
            "metric_id": contract.get("metric_id", "exact_match_rate"),
            "metric_version": contract.get("metric_version", "1.0"),
            "acceptance_threshold": contract.get("acceptance_threshold", 1.0),
            "minimum_case_coverage": contract.get("minimum_case_coverage", 1.0),
            "exact_match_required": contract.get("exact_match_required", False),
            "candidate_attribution_requirements": {
                "target_candidate_required": True,
                "target_candidate_fingerprint_required": False,
            },
            "operation_attribution_requirements": {
                "target_operation_required": True,
            },
            "contamination_policy_id": "sealed_reference_solver_isolation",
            "evidence_sufficiency_policy_id": "minimum_case_coverage_and_exact_match",
            "evidence_direction_policy_id": "comparison_result_direction_policy",
            "contract_source": contract.get(
                "contract_source",
                "explicit_evaluation_contract",
            ),
            "review_state": "EVALUATION_CONTRACT_CREATED",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_compilation_authority": "NONE",
            "deployment_authority": "NONE",
            "created_at": self._now(),
            "constitutional_boundary": (
                "VALIDATION_EVIDENCE_EVALUATION_CONTRACT_MAY_AUTHORIZE_COMPARISON_AND_EVIDENCE_CLASSIFICATION_FOR_ONE_DURABLE_RAW_RESULT_BUT_CANNOT_MUTATE_THE_ARENA_OR_GRANT_TRUTH_TRUST_GRADUATION_COMPILATION_EXECUTION_OR_DEPLOYMENT_AUTHORITY"
            ),
        }

    def _link_schedule_and_raw_result(
        self,
        schedule: dict[str, Any],
        schedule_path: Path,
        raw_result: dict[str, Any],
        raw_path: Path,
        comparable: dict[str, Any],
        decision: dict[str, Any],
        accepted: dict[str, Any],
    ) -> None:
        terminal = decision.get("evidence_acceptance_state")
        common = {
            "comparison_state": "COMPARISON_COMPLETED",
            "evaluation_contract_id": decision.get("evaluation_contract_id"),
            "evaluation_contract_fingerprint": decision.get(
                "evaluation_contract_fingerprint"
            ),
            "comparable_result_id": comparable.get("comparable_result_id"),
            "evidence_decision_id": decision.get("evidence_decision_id"),
            "accepted_evidence_id": accepted.get("accepted_evidence_id"),
            "evidence_acceptance_state": terminal,
            "evidence_state": f"EVIDENCE_{terminal}",
            "evidence_accepted": terminal == "ACCEPTED",
            "arena_reentry_invoked": False,
            "candidate_score_changed": False,
            "candidate_ranking_changed": False,
            "tie_resolved": False,
            "winner_selected": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_compilation_authority": "NONE",
            "deployment_authority": "NONE",
        }
        self._atomic_write(schedule_path, {**schedule, **common})
        self._atomic_write(raw_path, {**raw_result, **common})

    def _alignment_failures(
        self,
        plan: dict[str, Any],
        schedule: dict[str, Any],
        raw_result: dict[str, Any],
    ) -> list[str]:
        failures = []
        for key in ("plan_id", "schedule_id", "execution_id", "raw_result_id"):
            expected = plan.get(key)
            observed = raw_result.get(key)
            if key == "raw_result_id":
                observed = raw_result.get("raw_result_id")
            if expected and observed and expected != observed:
                failures.append(f"{key}_plan_raw_mismatch")
        if schedule.get("plan_id") != plan.get("plan_id"):
            failures.append("schedule_plan_id_mismatch")
        if schedule.get("schedule_id") != plan.get("schedule_id"):
            failures.append("schedule_id_mismatch")
        if raw_result.get("schedule_id") != schedule.get("schedule_id"):
            failures.append("raw_schedule_id_mismatch")
        if raw_result.get("execution_id") != plan.get("execution_id"):
            failures.append("execution_id_mismatch")
        if raw_result.get("selected_validation_task_id") != plan.get(
            "selected_validation_task_id"
        ):
            failures.append("task_id_mismatch")
        if raw_result.get("selected_curriculum_id") != plan.get(
            "selected_curriculum_id"
        ):
            failures.append("curriculum_id_mismatch")
        return failures

    def _evaluation_contract(self, raw_task: dict[str, Any]) -> dict[str, Any]:
        contract = raw_task.get("evaluation_contract")
        if isinstance(contract, dict):
            result = dict(contract)
        elif raw_task.get("comparator_id"):
            result = {
                "comparator_id": raw_task.get("comparator_id"),
                "comparator_version": raw_task.get(
                    "comparator_version",
                self.DEFAULT_COMPARATOR_VERSION,
                ),
            }
        elif raw_task.get("expected_target_output") is not None:
            result = {
                "comparator_id": "manifest_observation_comparison",
                "comparator_version": self.DEFAULT_COMPARATOR_VERSION,
                "minimum_case_coverage": 1.0,
                "exact_match_required": True,
                "contract_source": "derived_from_expected_target_output",
            }
        elif raw_task.get("expected_case_outputs") is not None:
            result = {
                "comparator_id": "manifest_observation_comparison",
                "comparator_version": self.DEFAULT_COMPARATOR_VERSION,
                "minimum_case_coverage": 1.0,
                "exact_match_required": True,
                "contract_source": "derived_from_expected_case_outputs",
            }
        else:
            return {}
        result.setdefault("comparator_version", self.DEFAULT_COMPARATOR_VERSION)
        result.setdefault("minimum_case_coverage", 1.0)
        result.setdefault("exact_match_required", False)
        return result

    def _sealed_reference(
        self,
        raw_task: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        expected = raw_task.get("expected_case_outputs")
        if expected is None:
            expected = raw_task.get("expected_target_output")
        if expected is None:
            expected = raw_task.get("required_ground_truth")
        payload = {
            "selected_validation_task_id": raw_task.get("task_id"),
            "expected_output": expected,
            "evaluation_contract": contract,
        }
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest() if expected is not None else None
        return {
            **payload,
            "sealed_reference_id": (
                f"sealed_reference_{hashlib.sha1(str(fingerprint).encode()).hexdigest()[:12]}"
                if fingerprint else "Not Available"
            ),
            "sealed_reference_fingerprint": fingerprint,
            "sealed_reference_source": "validation_task_expected_output",
            "sealed_reference_resolved": expected is not None,
            "sealed_reference_available": expected is not None,
            "sealed_reference_access_authority": self.AUTHORITY,
            "sealed_reference_access_scope": "EVALUATION_ONLY",
            "reference_access_authority": "VALIDATION_EVIDENCE_EVALUATOR_ONLY",
            "reference_integrity_state": (
                "VERIFIED" if fingerprint else "MISSING"
            ),
            "target_reference_forwarded_to_solver": False,
        }

    def _expected_cases(self, sealed_reference: dict[str, Any]) -> list[Any]:
        expected = sealed_reference.get("expected_output")
        if isinstance(expected, list) and all(
            isinstance(item, dict) and "output" in item for item in expected
        ):
            return [item.get("output") for item in expected]
        return [expected]

    def _comparison_failure_record(
        self,
        plan: dict[str, Any],
        schedule: dict[str, Any],
        raw_result: dict[str, Any],
        contract: dict[str, Any],
        comparison_id: str,
        started_at: str,
        error: str,
    ) -> dict[str, Any]:
        return {
            "comparison_id": comparison_id,
            **self._identity(plan, schedule, raw_result),
            "comparator_id": contract.get("comparator_id"),
            "comparison_state": "COMPARISON_FAILED",
            "comparison_failure_reason": error,
            "comparison_started_at": started_at,
            "comparison_failed_at": self._now(),
            "evidence_state": "NOT_EVALUATED",
            "evidence_accepted": False,
            "arena_reentry_invoked": False,
            "arena_evidence_admission_invoked": False,
            "candidate_score_changed": False,
            "candidate_ranking_changed": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_compilation_authority": "NONE",
            "deployment_authority": "NONE",
        }

    def _persist_comparison_failure(
        self,
        plan_path: Path,
        failure: dict[str, Any],
    ) -> None:
        plan, _ = self._read_json(plan_path)
        if isinstance(plan, dict):
            plan.update({
                "lifecycle_state": "COMPARISON_FAILED",
                "comparison_state": "COMPARISON_FAILED",
                "comparison_failure": failure,
                "active_evaluation_lease": False,
                "evidence_state": "NOT_EVALUATED",
            })
            self._atomic_write(plan_path, plan)

    def _existing_terminal_decision(
        self,
        plan: dict[str, Any],
    ) -> dict[str, Any] | None:
        decision_id = plan.get("evidence_decision_id")
        if decision_id:
            path = self.evidence_decisions_path / f"{decision_id}.json"
            decision, error = self._read_json(path)
            if not error and isinstance(decision, dict):
                return decision
        for path in self._plan_files(self.evidence_decisions_path):
            decision, error = self._read_json(path)
            if error or not isinstance(decision, dict):
                continue
            if decision.get("plan_id") == plan.get("plan_id"):
                return decision
        return None

    def _existing_comparable_result(
        self,
        plan: dict[str, Any],
    ) -> dict[str, Any] | None:
        comparable_id = plan.get("comparable_result_id")
        if comparable_id:
            path = self.comparable_results_path / f"{comparable_id}.json"
            comparable, error = self._read_json(path)
            if not error and isinstance(comparable, dict):
                return comparable
        for path in self._plan_files(self.comparable_results_path):
            comparable, error = self._read_json(path)
            if error or not isinstance(comparable, dict):
                continue
            if comparable.get("plan_id") == plan.get("plan_id"):
                return comparable
        return None

    def _existing_accepted_evidence(
        self,
        decision: dict[str, Any],
    ) -> dict[str, Any] | None:
        accepted_id = decision.get("accepted_evidence_id")
        if accepted_id:
            path = self.accepted_evidence_path / f"{accepted_id}.json"
            accepted, error = self._read_json(path)
            if not error and isinstance(accepted, dict):
                return accepted
        for path in self._plan_files(self.accepted_evidence_path):
            accepted, error = self._read_json(path)
            if error or not isinstance(accepted, dict):
                continue
            if accepted.get("evidence_decision_id") == decision.get(
                "evidence_decision_id"
            ):
                return accepted
        return None

    def _existing_decision_by_fingerprint(
        self,
        fingerprint: str,
    ) -> dict[str, Any] | None:
        for path in self._plan_files(self.evidence_decisions_path):
            decision, error = self._read_json(path)
            if error or not isinstance(decision, dict):
                continue
            if decision.get("evidence_decision_fingerprint") == fingerprint:
                return decision
        return None

    def _existing_evaluation_contract(
        self,
        contract: dict[str, Any],
    ) -> dict[str, Any] | None:
        fingerprint = contract.get("evaluation_contract_fingerprint")
        if self._term(fingerprint) == "Not Available":
            return None
        contract_id = contract.get("evaluation_contract_id")
        if self._term(contract_id) != "Not Available":
            path = self.evaluation_contracts_path / f"{contract_id}.json"
            existing, error = self._read_json(path)
            if (
                not error
                and isinstance(existing, dict)
                and existing.get("evaluation_contract_fingerprint") == fingerprint
            ):
                return existing
        for path in self._plan_files(self.evaluation_contracts_path):
            existing, error = self._read_json(path)
            if error or not isinstance(existing, dict):
                continue
            if existing.get("evaluation_contract_fingerprint") == fingerprint:
                return existing
        return None

    def _identity(
        self,
        plan: dict[str, Any],
        schedule: dict[str, Any],
        raw_result: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "plan_id": plan.get("plan_id", "Not Available"),
            "plan_fingerprint": plan.get("plan_fingerprint", "Not Available"),
            "schedule_id": schedule.get("schedule_id", plan.get("schedule_id")),
            "schedule_fingerprint": schedule.get(
                "schedule_fingerprint",
                plan.get("schedule_fingerprint"),
            ),
            "execution_id": raw_result.get(
                "execution_id",
                plan.get("execution_id"),
            ),
            "raw_result_id": raw_result.get(
                "raw_result_id",
                plan.get("raw_result_id"),
            ),
            "raw_result_fingerprint": raw_result.get(
                "raw_result_fingerprint",
                plan.get("raw_result_fingerprint"),
            ),
            "selected_validation_task_id": plan.get(
                "selected_validation_task_id",
                raw_result.get("selected_validation_task_id"),
            ),
            "selected_curriculum_id": plan.get(
                "selected_curriculum_id",
                raw_result.get("selected_curriculum_id"),
            ),
            "target_candidate": plan.get("target_candidate"),
            "target_operation": plan.get("target_operation"),
            "required_evidence": plan.get("required_evidence"),
            "required_evidence_category": plan.get("required_evidence_category"),
            "tie_break_strategy": plan.get("tie_break_strategy"),
        }

    def _base_report(self, plan_id: str | None) -> dict[str, Any]:
        return {
            "system": "validation_evidence_evaluator",
            "responsible_component": "VALIDATION_EVIDENCE_EVALUATOR",
            "plan_id": self._term(plan_id),
            "schedule_id": "Not Available",
            "execution_id": "Not Available",
            "raw_result_id": "Not Available",
            "evaluation_contract_id": "Not Available",
            "evaluation_contract_fingerprint": "Not Available",
            "comparable_result_id": "Not Available",
            "evidence_decision_id": "Not Available",
            "accepted_evidence_id": "Not Available",
            "evaluation_admission_evaluated": False,
            "evaluation_admission_state": "NOT_EVALUATED",
            "evaluation_admission_reason": "not_evaluated",
            "evidence_evaluation_authority": "NONE",
            "evidence_evaluation_scope": "Not Available",
            "sealed_reference_available": False,
            "sealed_reference_id": "Not Available",
            "sealed_reference_fingerprint": "Not Available",
            "sealed_reference_resolved": False,
            "sealed_reference_opened_by_evaluator": False,
            "sealed_reference_forwarded_to_solver": False,
            "target_reference_forwarded_to_solver": False,
            "reference_integrity_state": "NOT_EVALUATED",
            "comparison_invoked": False,
            "comparison_started": False,
            "comparison_completed": False,
            "comparison_state": "NOT_COMPARED",
            "comparator_id": "Not Available",
            "comparator_version": "Not Available",
            "comparator_resolved": False,
            "comparable_result_available": False,
            "comparable_result_creation_result": "NOT_ATTEMPTED",
            "expected_case_count": 0,
            "compared_case_count": 0,
            "case_coverage": 0.0,
            "exact_match_count": 0,
            "exact_match_rate": 0.0,
            "exact_match": False,
            "accuracy": 0.0,
            "difference_count": 0,
            "shape_compatibility_state": "NOT_EVALUATED",
            "evidence_evaluation_invoked": False,
            "evidence_admissibility_evaluated": False,
            "evidence_admissibility_state": "NOT_EVALUATED",
            "evidence_sufficiency_evaluated": False,
            "evidence_sufficiency_state": "NOT_EVALUATED",
            "evidence_direction_calculated": False,
            "evidence_direction": "NOT_DETERMINED",
            "evidence_acceptance_state": "NOT_EVALUATED",
            "evidence_evaluation_outcome": "NOT_EVALUATED",
            "outcome_reason": "not_evaluated",
            "evidence_decision_recorded": False,
            "evidence_decision_creation_result": "NOT_ATTEMPTED",
            "accepted_evidence_artifact_created": False,
            "accepted_evidence_creation_result": "NOT_APPLICABLE",
            "evidence_accepted": False,
            "arena_evidence_admission_invoked": False,
            "arena_reentry_invoked": False,
            "candidate_score_changed": False,
            "candidate_ranking_changed": False,
            "tie_resolved": False,
            "winner_selected": False,
            "truth_granted": False,
            "trust_granted": False,
            "graduation_granted": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_compilation_authority": "NONE",
            "deployment_authority": "NONE",
            "next_consumer": "Not Available",
            "constitutional_boundary": self.BOUNDARY,
        }

    def _blocked(
        self,
        base: dict[str, Any],
        state: str,
        reason: str,
        stage: str,
        action: str,
    ) -> dict[str, Any]:
        return {
            **base,
            "evaluation_admission_evaluated": True,
            "evaluation_admission_state": state,
            "evaluation_admission_reason": reason,
            "blocked_stage": stage,
            "responsible_component": "VALIDATION_EVIDENCE_EVALUATOR",
            "recommended_action": action,
            "comparison_invoked": False,
            "comparison_started": False,
            "comparison_completed": False,
            "comparable_result_available": False,
            "evidence_evaluation_invoked": False,
            "evidence_decision_recorded": False,
            "evidence_accepted": False,
            "arena_reentry_invoked": False,
        }

    def _admission_block(
        self,
        state: str,
        reason: str,
        stage: str,
        action: str,
    ) -> dict[str, Any]:
        return {
            "evaluation_admission_evaluated": True,
            "evaluation_admission_state": state,
            "evaluation_admission_reason": reason,
            "blocked_stage": stage,
            "responsible_component": "VALIDATION_EVIDENCE_EVALUATOR",
            "recommended_action": action,
            "comparison_invoked": False,
            "evidence_evaluation_invoked": False,
            "arena_reentry_invoked": False,
            "arena_evidence_admission_invoked": False,
            "candidate_score_changed": False,
            "candidate_ranking_changed": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_compilation_authority": "NONE",
            "deployment_authority": "NONE",
        }

    def _public_projection(self, report: dict[str, Any]) -> dict[str, Any]:
        base = self._base_report(report.get("plan_id"))
        return {**base, **report} if report else base

    def _next_consumer(self, state: str) -> str:
        if state == "ACCEPTED":
            return "FUTURE_ARENA_EVIDENCE_ADMISSION_GATE"
        if state == "INSUFFICIENT":
            return "EVIDENCE_REMEDIATION_PLANNER"
        if state == "REJECTED":
            return "EVIDENCE_REVIEW_OR_REPLAN"
        return "VALIDATION_EVIDENCE_EVALUATOR"

    def _comparison_id(
        self,
        plan: dict[str, Any],
        schedule: dict[str, Any],
        raw_result: dict[str, Any],
        sealed_reference: dict[str, Any],
        contract: dict[str, Any],
    ) -> str:
        seed = self._comparable_fingerprint(
            plan,
            schedule,
            raw_result,
            sealed_reference,
            contract,
        )
        return f"validation_comparison_{hashlib.sha1(seed.encode()).hexdigest()[:12]}"

    def _comparable_fingerprint(
        self,
        plan: dict[str, Any],
        schedule: dict[str, Any],
        raw_result: dict[str, Any],
        sealed_reference: dict[str, Any],
        contract: dict[str, Any],
    ) -> str:
        return self._fingerprint({
            **self._identity(plan, schedule, raw_result),
            "sealed_reference_fingerprint": sealed_reference.get(
                "sealed_reference_fingerprint"
            ),
            "comparator_id": contract.get("comparator_id"),
            "comparator_version": contract.get("comparator_version"),
            "evaluation_contract_fingerprint": contract.get(
                "evaluation_contract_fingerprint",
                self._contract_fingerprint(contract),
            ),
            "evaluation_policy_version": self.POLICY_VERSION,
        })

    def _decision_fingerprint(
        self,
        plan: dict[str, Any],
        schedule: dict[str, Any],
        raw_result: dict[str, Any],
        comparable: dict[str, Any],
        contract: dict[str, Any],
    ) -> str:
        return self._fingerprint({
            **self._identity(plan, schedule, raw_result),
            "comparable_result_fingerprint": comparable.get(
                "comparable_result_fingerprint"
            ),
            "evaluation_contract_fingerprint": contract.get(
                "evaluation_contract_fingerprint",
                self._contract_fingerprint(contract),
            ),
            "evaluation_policy_version": self.POLICY_VERSION,
        })

    def _contract_fingerprint(self, contract: dict[str, Any]) -> str:
        return self._fingerprint(contract)

    def _fingerprint(self, payload: dict[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest()

    def _load_plan(
        self,
        plan_id: str | None,
    ) -> tuple[dict[str, Any] | None, Path | None, str | None]:
        if self._term(plan_id) == "Not Available":
            return None, None, "missing_plan_id"
        path = self.pending_path / f"{plan_id}.json"
        plan, error = self._read_json(path)
        if error or not isinstance(plan, dict):
            return None, None, error or "plan_not_mapping"
        return plan, path, None

    def _load_schedule(
        self,
        schedule_id: str | None,
    ) -> tuple[dict[str, Any] | None, Path | None, str | None]:
        if self._term(schedule_id) == "Not Available":
            return None, None, "missing_schedule_id"
        path = self.schedules_path / f"{schedule_id}.json"
        schedule, error = self._read_json(path)
        if error or not isinstance(schedule, dict):
            return None, None, error or "schedule_not_mapping"
        return schedule, path, None

    def _load_raw_result(
        self,
        raw_result_id: str | None,
    ) -> tuple[dict[str, Any] | None, Path | None, str | None]:
        if self._term(raw_result_id) == "Not Available":
            return None, None, "missing_raw_result_id"
        path = self.raw_results_path / f"{raw_result_id}.json"
        raw_result, error = self._read_json(path)
        if error or not isinstance(raw_result, dict):
            return None, None, error or "raw_result_not_mapping"
        return raw_result, path, None

    def _initialize(self) -> None:
        self.pending_path.mkdir(parents=True, exist_ok=True)
        self.schedules_path.mkdir(parents=True, exist_ok=True)
        self.raw_results_path.mkdir(parents=True, exist_ok=True)
        self.evaluation_contracts_path.mkdir(parents=True, exist_ok=True)
        self.comparable_results_path.mkdir(parents=True, exist_ok=True)
        self.evidence_decisions_path.mkdir(parents=True, exist_ok=True)
        self.accepted_evidence_path.mkdir(parents=True, exist_ok=True)

    def _plan_files(self, directory: Path) -> list[Path]:
        if not directory.exists():
            return []
        return sorted(
            path for path in directory.glob("*.json")
            if not path.name.endswith(".tmp")
        )

    def _read_json(self, path: Path) -> tuple[Any, str | None]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
            return None, str(error)
        return payload, None

    def _atomic_write(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True)
        json.loads(encoded)
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        with temporary.open("w", encoding="utf-8") as file:
            file.write(encoded)
            file.write("\n")
            file.flush()
            try:
                os.fsync(file.fileno())
            except OSError:
                pass
        temporary.replace(path)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _term(self, value: Any) -> str:
        text = str(value or "").strip()
        return text if text else "Not Available"
