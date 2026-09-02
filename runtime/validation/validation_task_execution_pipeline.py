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
from runtime.validation.raw_result_lifecycle_applicability import (
    APPLICABLE,
    raw_result_lifecycle_applicability_evaluator,
)


class ValidationTaskExecutionPipeline:
    """Executes one scheduled validation task and captures an unevaluated result."""

    BOUNDARY = (
        "VALIDATION_EXECUTION_AUTHORITY_IS_SCOPED_TO_THE_SCHEDULED_SANDBOX_TASK_AND_DOES_NOT_AUTHORIZE_CANDIDATE_EXECUTION_OR_EVIDENCE_ACCEPTANCE"
    )
    RAW_RESULT_BOUNDARY = (
        "RAW_VALIDATION_TASK_OUTPUT_IS_AN_UNEVALUATED_OBSERVATION_AND_MUST_NOT_BE_TREATED_AS_EVIDENCE_BEFORE_EXPLICIT_EVALUATION"
    )
    RUNNER_ID = "governed_validation_manifest_runner"
    RUNNER_VERSION = "1.0"
    EXECUTION_SCOPE = "SCHEDULED_VALIDATION_TASK_ONLY"

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
        self.curriculum_registry = (
            curriculum_registry or ValidationCurriculumRegistry()
        )

    def execute_scheduled_plans(self) -> dict[str, Any]:
        self._initialize()
        reports = []
        for schedule_path in self._plan_files(self.schedules_path):
            schedule, error = self._read_json(schedule_path)
            if error or not isinstance(schedule, dict):
                continue
            if schedule.get("execution_state") == "RAW_RESULT_CAPTURED":
                reports.append(self.execute_schedule(schedule.get("schedule_id")))
            elif schedule.get("scheduling_state") == "SCHEDULED":
                reports.append(self.execute_schedule(schedule.get("schedule_id")))
        successful = [
            report for report in reports
            if report.get("execution_state") == "RAW_RESULT_CAPTURED"
        ]
        current = successful[0] if successful else reports[0] if reports else {}
        return {
            "system": "validation_task_execution_pipeline",
            "responsible_component": "VALIDATION_EXECUTION_PIPELINE",
            "execution_attempted": bool(reports),
            "executed_task_count": int(current.get("executed_task_count", 0) or 0),
            "execution_reports": reports,
            **self._public_projection(current),
        }

    def execute_schedule(self, schedule_id: str | None) -> dict[str, Any]:
        self._initialize()
        base = self._base_report(schedule_id)
        schedule, schedule_path, schedule_error = self._load_schedule(schedule_id)
        if schedule_error or not schedule or not schedule_path:
            return self._blocked(
                base,
                "BLOCKED_INVALID_SCHEDULE_STATE",
                schedule_error or "schedule_not_found",
                "schedule_load",
                "restore_or_recreate_validation_schedule",
            )
        existing_raw = self._existing_raw_result(schedule)
        if existing_raw:
            plan, plan_path, _ = self._load_plan(schedule.get("plan_id"))
            if plan and plan_path:
                self._link_raw_result(plan, plan_path, schedule, schedule_path, existing_raw)
            return self._success_report(
                base,
                plan or {},
                schedule,
                existing_raw,
                "REUSED_EXISTING_RAW_RESULT",
                invoked=False,
            )

        admission = self._admission(schedule)
        if admission["execution_admission_state"] != "ADMITTED":
            return {**base, **admission, **self._schedule_identity(schedule)}

        plan = admission["plan"]
        plan_path = admission["plan_path"]
        task = admission["task"]
        execution_id = self._execution_id(schedule)
        attempt_number = int(schedule.get("attempt_count", 0) or 0) + 1
        started_at = self._now()
        try:
            started_plan = {
                **plan,
                "updated_at": started_at,
                "lifecycle_state": "EXECUTION_STARTED",
                "execution_state": "EXECUTION_STARTED",
                "execution_invoked": True,
                "execution_id": execution_id,
                "execution_attempt_count": attempt_number,
                "execution_started_at": started_at,
                "active_execution_lease": True,
                "validation_execution_authority": (
                    "VALIDATION_EXECUTION_PIPELINE"
                ),
                "validation_execution_scope": self.EXECUTION_SCOPE,
                "candidate_execution_authority": "NONE",
                "truth_authority": "NONE",
                "trust_authority": "NONE",
                "graduation_authority": "NONE",
            }
            started_schedule = {
                **schedule,
                "execution_state": "EXECUTION_STARTED",
                "execution_invoked": True,
                "execution_id": execution_id,
                "attempt_count": attempt_number,
                "execution_started_at": started_at,
                "active_execution_lease": True,
                "validation_execution_authority": (
                    "VALIDATION_EXECUTION_PIPELINE"
                ),
                "validation_execution_scope": self.EXECUTION_SCOPE,
                "candidate_execution_authority": "NONE",
            }
            self._atomic_write(plan_path, started_plan)
            self._atomic_write(schedule_path, started_schedule)
        except (OSError, TypeError, ValueError) as error:
            return self._blocked(
                {**base, **self._schedule_identity(schedule)},
                "BLOCKED_EXECUTION_STATE_PERSISTENCE_FAILURE",
                str(error),
                "execution_start_persistence",
                "retry_execution_start_persistence_before_runner_invocation",
            )

        started_clock = time.perf_counter()
        try:
            runner_output = self._run_task(task, started_schedule, started_plan)
            runner_status = "COMPLETED"
            runtime_error = None
        except Exception as error:  # pragma: no cover - defensive boundary
            runner_output = None
            runner_status = "FAILED"
            runtime_error = str(error)
        completed_at = self._now()
        duration = round(time.perf_counter() - started_clock, 6)
        if runner_status != "COMPLETED":
            failure = self._execution_failure_record(
                started_schedule,
                started_plan,
                execution_id,
                attempt_number,
                started_at,
                completed_at,
                runtime_error or "runner_exception",
            )
            self._persist_execution_failure(plan_path, schedule_path, failure)
            return {
                **base,
                **self._schedule_identity(started_schedule),
                "execution_admission_evaluated": True,
                "execution_admission_state": "ADMITTED",
                "execution_admission_reason": "execution_contract_satisfied",
                "execution_invoked": True,
                "execution_started": True,
                "execution_completed": False,
                "execution_state": "EXECUTION_FAILED",
                "runtime_error_available": True,
                "raw_result_captured": False,
                "raw_result_creation_result": "EXECUTION_FAILED",
                "evidence_state": "NOT_EVALUATED",
            }

        applicability_report = self._producer_applicability_report(
            started_schedule,
            started_plan,
            execution_id,
            attempt_number,
            completed_at,
        )
        raw_result = self._raw_result_record(
            started_schedule,
            started_plan,
            task,
            runner_output,
            execution_id,
            attempt_number,
            started_at,
            completed_at,
            duration,
            applicability_report,
        )
        raw_identity = raw_result.get("raw_result_id")
        if self._term(raw_identity) == "Not Available":
            raw_identity = raw_result.get("validation_attempt_id") or execution_id
        raw_path = self.raw_results_path / f"{raw_identity}.json"
        try:
            prepared_schedule = {
                **started_schedule,
                "execution_state": "EXECUTION_COMPLETED_RESULT_CAPTURE_PENDING",
                "execution_completed_at": completed_at,
                "raw_result_id": raw_result.get("raw_result_id"),
                "raw_validation_result_id": raw_result.get(
                    "raw_validation_result_id"
                ),
            }
            prepared_plan = {
                **started_plan,
                "lifecycle_state": "EXECUTION_COMPLETED_RESULT_CAPTURE_PENDING",
                "execution_state": "EXECUTION_COMPLETED_RESULT_CAPTURE_PENDING",
                "execution_completed_at": completed_at,
                "raw_result_id": raw_result.get("raw_result_id"),
                "raw_validation_result_id": raw_result.get(
                    "raw_validation_result_id"
                ),
            }
            self._atomic_write(schedule_path, prepared_schedule)
            self._atomic_write(plan_path, prepared_plan)
            self._atomic_write(raw_path, raw_result)
            self._link_raw_result(
                prepared_plan,
                plan_path,
                prepared_schedule,
                schedule_path,
                raw_result,
            )
        except (OSError, TypeError, ValueError) as error:
            return {
                **base,
                **self._schedule_identity(started_schedule),
                "execution_admission_evaluated": True,
                "execution_admission_state": "ADMITTED",
                "execution_admission_reason": "execution_contract_satisfied",
                "execution_invoked": True,
                "execution_started": True,
                "execution_completed": True,
                "execution_state": "EXECUTION_COMPLETED_RESULT_CAPTURE_PENDING",
                "raw_result_captured": False,
                "raw_result_creation_result": "RAW_RESULT_CAPTURE_FAILED",
                "raw_result_persistence_state": "RESULT_CAPTURE_PERSISTENCE_FAILED",
                "runtime_error_available": True,
                "execution_admission_reason_detail": str(error),
                "evidence_state": "NOT_EVALUATED",
            }

        return self._success_report(
            base,
            {
                **prepared_plan,
                "lifecycle_state": raw_result.get(
                    "result_state",
                    "RAW_RESULT_CAPTURED",
                ),
            },
            {
                **prepared_schedule,
                "execution_state": raw_result.get(
                    "result_state",
                    "RAW_RESULT_CAPTURED",
                ),
            },
            raw_result,
            "CREATED_NEW_RAW_RESULT",
            invoked=True,
        )

    def _admission(self, schedule: dict[str, Any]) -> dict[str, Any]:
        if schedule.get("scheduling_state") != "SCHEDULED":
            return self._admission_block(
                "BLOCKED_INVALID_SCHEDULE_STATE",
                f"expected_SCHEDULED_observed_{schedule.get('scheduling_state')}",
                "schedule_state",
                "restore_scheduled_state_before_execution",
            )
        if schedule.get("scheduling_admission_state") != "ADMITTED":
            return self._admission_block(
                "BLOCKED_SCHEDULING_NOT_ADMITTED",
                "scheduling_admission_state_not_admitted",
                "schedule_admission",
                "rerun_governed_scheduling_admission",
            )
        if schedule.get("candidate_execution_authority") not in (None, "NONE"):
            return self._admission_block(
                "BLOCKED_CONSTITUTIONAL_VIOLATION",
                "candidate_execution_authority_not_none",
                "authority_validation",
                "restore_candidate_execution_authority_none",
            )
        plan, plan_path, plan_error = self._load_plan(schedule.get("plan_id"))
        if plan_error or not plan or not plan_path:
            return self._admission_block(
                "BLOCKED_PLAN_SCHEDULE_MISMATCH",
                plan_error or "linked_plan_not_found",
                "plan_schedule_alignment",
                "restore_linked_evidence_plan",
            )
        if plan.get("plan_id") != schedule.get("plan_id"):
            return self._admission_block(
                "BLOCKED_PLAN_SCHEDULE_MISMATCH",
                "plan_id_mismatch",
                "plan_schedule_alignment",
                "repair_plan_schedule_link",
            )
        if plan.get("selected_validation_task_id") != schedule.get(
            "selected_validation_task_id"
        ):
            return self._admission_block(
                "BLOCKED_PLAN_SCHEDULE_MISMATCH",
                "selected_task_mismatch",
                "plan_schedule_alignment",
                "repair_plan_schedule_task_identity",
            )
        lookup = self.curriculum_registry.find_task(
            schedule.get("selected_validation_task_id"),
            schedule.get("selected_curriculum_id"),
        )
        if not lookup.get("found"):
            return self._admission_block(
                "BLOCKED_TASK_NOT_FOUND",
                "scheduled_task_not_found",
                "scheduled_task_resolution",
                "restore_curriculum_or_reschedule",
            )
        if not lookup.get("enabled"):
            return self._admission_block(
                "BLOCKED_TASK_DISABLED",
                "scheduled_task_disabled",
                "scheduled_task_resolution",
                "enable_task_or_reschedule",
            )
        task = lookup.get("task") or {}
        raw_task = task.get("raw_task") or {}
        if not task.get("task_id") or not raw_task:
            return self._admission_block(
                "BLOCKED_INVALID_TASK_SCHEMA",
                "task_schema_missing_raw_task",
                "task_schema_validation",
                "repair_validation_task_schema",
            )
        if raw_task.get("requires_target_for_prediction") is True:
            return self._admission_block(
                "BLOCKED_TARGET_LEAKAGE_RISK",
                "runner_requires_target_reference",
                "target_leakage_prevention",
                "use_target_sealed_runner_payload",
            )
        if raw_task.get("unsupported_task_type") is True:
            return self._admission_block(
                "BLOCKED_UNSUPPORTED_TASK_TYPE",
                "unsupported_validation_task_type",
                "runner_support",
                "implement_supported_validation_runner",
            )
        if not self._materialize_payload(task, schedule, plan).get(
            "runner_input_payload"
        ):
            return self._admission_block(
                "BLOCKED_NON_EXECUTABLE_TASK_PAYLOAD",
                "runner_input_payload_empty",
                "payload_materialization",
                "repair_validation_task_payload",
            )
        if self._existing_raw_result(schedule):
            return self._admission_block(
                "BLOCKED_EXISTING_RAW_RESULT",
                "raw_result_already_exists",
                "idempotency_guard",
                "reuse_existing_raw_result",
            )
        if schedule.get("active_execution_lease") is True:
            return self._admission_block(
                "BLOCKED_ACTIVE_EXECUTION",
                "active_execution_lease_present",
                "execution_lease",
                "inspect_active_execution_before_retry",
            )
        if int(schedule.get("attempt_count", 0) or 0) >= 1:
            return self._admission_block(
                "BLOCKED_ATTEMPT_LIMIT",
                "attempt_limit_reached",
                "attempt_policy",
                "perform_execution_recovery_review",
            )
        return {
            "execution_admission_state": "ADMITTED",
            "execution_admission_reason": "execution_contract_satisfied",
            "blocked_stage": "none",
            "responsible_component": "VALIDATION_EXECUTION_PIPELINE",
            "recommended_action": "invoke_scheduled_validation_task_runner",
            "plan": plan,
            "plan_path": plan_path,
            "task": task,
            "payload": self._materialize_payload(task, schedule, plan),
        }

    def _run_task(
        self,
        task: dict[str, Any],
        schedule: dict[str, Any],
        plan: dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._materialize_payload(task, schedule, plan)
        runner_input = payload["runner_input_payload"]
        return {
            "predicted_output": {
                "runner_output_type": "validation_task_manifest_observation",
                "task_id": runner_input["task_id"],
                "target_operation": runner_input["target_operation"],
                "required_evidence": runner_input["required_evidence"],
                "reasoning_patterns": runner_input.get("reasoning_patterns", []),
            },
            "case_outputs": [{
                "case_id": "manifest_case_0",
                "output": {
                    "task_id": runner_input["task_id"],
                    "execution_scope": self.EXECUTION_SCOPE,
                    "reference_visible_to_runner": False,
                },
            }],
            "runner_trace_reference": {
                "runner_id": self.RUNNER_ID,
                "target_reference_forwarded_to_solver": False,
            },
        }

    def _materialize_payload(
        self,
        task: dict[str, Any],
        schedule: dict[str, Any],
        plan: dict[str, Any],
    ) -> dict[str, Any]:
        raw_task = task.get("raw_task") or {}
        runner_input = {
            "task_id": task.get("task_id"),
            "task_name": task.get("task_name"),
            "selected_curriculum_id": schedule.get("selected_curriculum_id"),
            "required_evidence": schedule.get("required_evidence"),
            "required_evidence_category": schedule.get("required_evidence_category"),
            "target_candidate": schedule.get("target_candidate"),
            "target_operation": schedule.get("target_operation"),
            "tie_break_strategy": schedule.get("tie_break_strategy"),
            "supported_domains": task.get("supported_domains") or [],
            "supported_operations": task.get("supported_operations") or [],
            "supported_evidence": task.get("supported_evidence") or [],
            "reasoning_patterns": task.get("reasoning_patterns") or [],
            "execution_budget": {"max_cases": 1, "mode": "SANDBOX_VALIDATION"},
            "validation_objective": raw_task.get("validation_objective"),
        }
        sealed_reference = {
            "expected_target_output": raw_task.get("expected_target_output"),
            "ground_truth_reference": raw_task.get("required_ground_truth"),
            "evaluator_only_metadata": {
                "expected_validation_contract": raw_task.get(
                    "expected_validation_contract"
                ),
            },
        }
        return {
            "runner_input_payload": runner_input,
            "sealed_reference_payload": sealed_reference,
            "target_reference_forwarded_to_solver": False,
        }

    def _raw_result_record(
        self,
        schedule: dict[str, Any],
        plan: dict[str, Any],
        task: dict[str, Any],
        runner_output: dict[str, Any],
        execution_id: str,
        attempt_number: int,
        started_at: str,
        completed_at: str,
        duration: float,
        applicability_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        runner_output = runner_output if isinstance(runner_output, dict) else {}
        applicability_report = (
            applicability_report if isinstance(applicability_report, dict) else {}
        )
        raw_result_applicable = (
            applicability_report.get("raw_result_applicability_state")
            == APPLICABLE
            and applicability_report.get("raw_result_applicability_finalized")
            is True
        )
        fingerprint = self._raw_result_fingerprint(
            schedule,
            plan,
            execution_id,
            attempt_number,
        )
        missing_inputs = self._raw_identity_missing_inputs(
            schedule,
            plan,
            execution_id,
        )
        validation_attempt_id = self._validation_attempt_id(
            schedule,
            execution_id,
            attempt_number,
        )
        expected_artifact_id = self._expected_artifact_id(
            schedule,
            plan,
            task,
            validation_attempt_id,
        )
        payload_present = (
            runner_output.get("predicted_output") is not None
            or bool(runner_output.get("case_outputs"))
        )
        empty_valid = (
            payload_present is False
            and runner_output.get("empty_output_valid") is True
        )
        if payload_present:
            artifact_state = "ARTIFACT_CAPTURED"
            payload_state = "PAYLOAD_CAPTURED"
            result_state = "RAW_RESULT_CAPTURED"
            structural_eligibility = "STRUCTURALLY_ELIGIBLE"
            ineligibility_reason = "NONE"
            failure_cause = None
        elif empty_valid:
            artifact_state = "ARTIFACT_EMPTY_VALID_OUTPUT"
            payload_state = "EMPTY_VALID_OUTPUT"
            result_state = "RAW_RESULT_EMPTY_VALID_OUTPUT_CAPTURED"
            structural_eligibility = "STRUCTURALLY_ELIGIBLE"
            ineligibility_reason = "NONE"
            failure_cause = None
        else:
            artifact_state = "ARTIFACT_MISSING"
            payload_state = "PAYLOAD_MISSING"
            result_state = "RAW_RESULT_ARTIFACT_MISSING"
            structural_eligibility = "STRUCTURALLY_INELIGIBLE"
            ineligibility_reason = "ARTIFACT_MISSING"
            failure_cause = "expected_artifact_missing"
        raw_result_id = None
        identity_state = "RAW_RESULT_IDENTIFIED"
        identity_issuance_count = 0
        identity_created_at = None
        identity_issuable = artifact_state in {
            "ARTIFACT_CAPTURED",
            "ARTIFACT_EMPTY_VALID_OUTPUT",
        } and raw_result_applicable
        if not identity_issuable:
            identity_state = (
                "RAW_RESULT_ARTIFACT_MISSING_IDENTITY_NOT_ISSUABLE"
                if artifact_state == "ARTIFACT_MISSING"
                else "RAW_RESULT_APPLICABILITY_NOT_FINALIZED_IDENTITY_NOT_ISSUABLE"
            )
            raw_result_id = None
        elif missing_inputs:
            identity_state = "RAW_VALIDATION_IDENTITY_INPUT_UNAVAILABLE"
            raw_result_id = None
            structural_eligibility = "STRUCTURALLY_INELIGIBLE"
            ineligibility_reason = "RAW_VALIDATION_IDENTITY_INPUT_UNAVAILABLE"
            if result_state == "RAW_RESULT_CAPTURED":
                result_state = "RAW_RESULT_ENVELOPE_INCOMPLETE"
        else:
            identity_created_at = self._now()
            raw_result_id = self._raw_result_occurrence_id(
                schedule=schedule,
                plan=plan,
                execution_id=execution_id,
                validation_attempt_id=validation_attempt_id,
                attempt_number=attempt_number,
            )
            identity_issuance_count = 1
        produced_artifact_id = (
            self._produced_artifact_id(runner_output, validation_attempt_id)
            if payload_present or empty_valid
            else None
        )
        captured_artifact_id = produced_artifact_id if artifact_state in {
            "ARTIFACT_CAPTURED",
            "ARTIFACT_EMPTY_VALID_OUTPUT",
        } else None
        envelope = self._raw_result_envelope(
            raw_result_id=raw_result_id,
            fingerprint=fingerprint,
            schedule=schedule,
            plan=plan,
            task=task,
            execution_id=execution_id,
            validation_attempt_id=validation_attempt_id,
            expected_artifact_id=expected_artifact_id,
            produced_artifact_id=produced_artifact_id,
            captured_artifact_id=captured_artifact_id,
            artifact_state=artifact_state,
            payload_state=payload_state,
            result_state=result_state,
            identity_state=identity_state,
            structural_eligibility=structural_eligibility,
            ineligibility_reason=ineligibility_reason,
            failure_cause=failure_cause,
            missing_inputs=missing_inputs,
            identity_created_at=identity_created_at,
        )
        identity_fingerprint = (
            self._raw_result_identity_fingerprint(envelope)
            if raw_result_id else None
        )
        if identity_fingerprint:
            envelope["immutable_identity_fingerprint"] = identity_fingerprint
            envelope["raw_result_identity_fingerprint"] = identity_fingerprint
        return {
            "schema_version": "1.0",
            "raw_validation_result_schema_version": "1.0",
            "raw_result_identity_schema_version": "1.0",
            "raw_result_id": raw_result_id,
            "raw_validation_result_id": raw_result_id,
            "canonical_raw_result_id": raw_result_id,
            "raw_result_identity_state": self._raw_result_identity_state(
                raw_result_id,
                artifact_state,
            ),
            "raw_result_identity_reason": (
                "RAW_RESULT_IDENTITY_ISSUED_AT_PRODUCER_BOUNDARY"
                if raw_result_id else (
                    "RAW_RESULT_ARTIFACT_MISSING_IDENTITY_NOT_ISSUABLE"
                    if not identity_issuable else "RAW_RESULT_IDENTITY_INPUT_UNAVAILABLE"
                )
            ),
            "raw_result_identity_issuance_count": identity_issuance_count,
            "raw_result_identity_binding_state": (
                "RAW_RESULT_IDENTITY_BOUND_TO_ARTIFACT"
                if raw_result_id else "RAW_RESULT_IDENTITY_NOT_BOUND"
            ),
            "raw_result_identity_integrity_state": (
                "RAW_RESULT_IDENTITY_INTACT"
                if raw_result_id else (
                    "NOT_EVALUATED_ARTIFACT_MISSING"
                    if not identity_issuable else "RAW_RESULT_IDENTITY_MISSING"
                )
            ),
            "raw_result_identity_conflict_count": 0 if raw_result_id else len(missing_inputs),
            "identity_schema_version": "1.0",
            "identity_issued_at": identity_created_at,
            "identity_evaluation_source": "validation_task_execution_pipeline",
            "immutable_identity_fingerprint": identity_fingerprint,
            "raw_result_identity_fingerprint": identity_fingerprint,
            "raw_result_fingerprint": fingerprint,
            "raw_validation_result_fingerprint": fingerprint,
            "raw_validation_result_envelope": envelope,
            "RAW_VALIDATION_RESULT_ENVELOPE": envelope,
            "run_id": plan.get("source_run_id"),
            "batch_id": plan.get("batch_id") or schedule.get("batch_id"),
            "task_id": plan.get("source_task_id"),
            "execution_plan_id": (
                plan.get("execution_plan_id")
                or schedule.get("execution_plan_id")
                or plan.get("plan_id")
            ),
            "execution_node_id": (
                plan.get("execution_node_id")
                or schedule.get("execution_node_id")
                or "VALIDATION_TASK_EXECUTION_PIPELINE"
            ),
            "executor_id": self.RUNNER_ID,
            "executor_invocation_id": execution_id,
            "producer_operation_id": envelope.get("producer_operation_id"),
            "producer_component_id": envelope.get("producer_component_id"),
            "producer_source_type": envelope.get("producer_source_type"),
            "producer_operation_type": envelope.get("producer_source_type"),
            "validation_attempt_id": validation_attempt_id,
            "expected_artifact_id": expected_artifact_id,
            "produced_artifact_id": produced_artifact_id,
            "captured_artifact_id": captured_artifact_id,
            "artifact_state": artifact_state,
            "payload_state": payload_state,
            "provenance_state": envelope["provenance_state"],
            "binding_integrity_state": envelope["binding_integrity_state"],
            "raw_result_finalized": envelope["finalized_state"],
            "raw_result_immutable": envelope["immutable_state"],
            "downstream_structural_eligibility": structural_eligibility,
            "structural_ineligibility_reason": ineligibility_reason,
            "execution_id": execution_id,
            "schedule_id": schedule.get("schedule_id"),
            "plan_id": plan.get("plan_id"),
            "plan_fingerprint": plan.get("plan_fingerprint"),
            "schedule_fingerprint": schedule.get("schedule_fingerprint"),
            "selected_validation_task_id": schedule.get("selected_validation_task_id"),
            "selected_curriculum_id": schedule.get("selected_curriculum_id"),
            "target_candidate": schedule.get("target_candidate"),
            "target_operation": schedule.get("target_operation"),
            "claim_id": schedule.get("claim_id") or plan.get("claim_id"),
            "claim_subject": schedule.get("claim_subject") or plan.get("claim_subject"),
            "claim_subject_owner": (
                schedule.get("claim_subject_owner")
                or plan.get("claim_subject_owner")
            ),
            "claim_evidence_binding_authority": (
                schedule.get("claim_evidence_binding_authority")
                or plan.get("claim_evidence_binding_authority")
            ),
            "claim_evidence_binding_behavioral_authority": (
                schedule.get("claim_evidence_binding_behavioral_authority")
                or plan.get("claim_evidence_binding_behavioral_authority")
            ),
            "claim_evidence_binding_state": (
                schedule.get("claim_evidence_binding_state")
                or plan.get("claim_evidence_binding_state")
            ),
            "tie_break_strategy": schedule.get("tie_break_strategy"),
            "required_evidence": schedule.get("required_evidence"),
            "required_evidence_category": schedule.get("required_evidence_category"),
            "runner_id": self.RUNNER_ID,
            "runner_version": self.RUNNER_VERSION,
            "execution_mode": "SANDBOX_VALIDATION",
            "execution_scope": self.EXECUTION_SCOPE,
            "attempt_number": attempt_number,
            "execution_started_at": started_at,
            "execution_completed_at": completed_at,
            "execution_duration": duration,
            "runner_status": "COMPLETED",
            "predicted_output": runner_output.get("predicted_output"),
            "case_outputs": runner_output.get("case_outputs") or [],
            "runner_trace_reference": runner_output.get("runner_trace_reference"),
            "runtime_error": None,
            "resource_usage": {"executed_case_count": 1},
            "raw_result_created_at": self._now(),
            "raw_result_identity_lifecycle_transitions": self._raw_result_identity_transitions(
                applicability_report=applicability_report,
                run_id=plan.get("source_run_id"),
                execution_plan_id=(
                    plan.get("execution_plan_id")
                    or schedule.get("execution_plan_id")
                    or plan.get("plan_id")
                ),
                task_id=plan.get("source_task_id"),
                producer_operation_id=execution_id,
                validation_attempt_id=validation_attempt_id,
                raw_result_id=raw_result_id,
                source_timestamp=identity_created_at or completed_at,
            ),
            "raw_result_applicability_report": applicability_report,
            "RAW_RESULT_APPLICABILITY_REPORT": applicability_report,
            "raw_result_applicability_state": applicability_report.get(
                "raw_result_applicability_state",
            ),
            "raw_result_applicability_finalized": applicability_report.get(
                "raw_result_applicability_finalized",
                False,
            ),
            "producer_obligation_boundary_crossed": raw_result_applicable,
            "result_state": result_state,
            "comparison_state": "NOT_COMPARED",
            "evidence_state": "NOT_EVALUATED",
            "evidence_evaluation_invoked": False,
            "evidence_record_id": None,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "candidate_execution_authority": "NONE",
            "constitutional_boundary": self.RAW_RESULT_BOUNDARY,
            "failure_cause": failure_cause,
        }

    def _raw_identity_missing_inputs(
        self,
        schedule: dict[str, Any],
        plan: dict[str, Any],
        execution_id: str,
    ) -> list[str]:
        required = {
            "run_id": plan.get("source_run_id"),
            "task_id": plan.get("source_task_id"),
            "execution_plan_id": (
                plan.get("execution_plan_id")
                or schedule.get("execution_plan_id")
                or plan.get("plan_id")
            ),
            "schedule_id": schedule.get("schedule_id"),
            "executor_invocation_id": execution_id,
        }
        return [
            key for key, value in required.items()
            if self._term(value) == "Not Available"
        ]

    def _validation_attempt_id(
        self,
        schedule: dict[str, Any],
        execution_id: str,
        attempt_number: int,
    ) -> str:
        return self._scoped_id(
            "validation_attempt",
            {
                "schedule_id": schedule.get("schedule_id"),
                "execution_id": execution_id,
                "attempt_number": attempt_number,
            },
        )

    def _expected_artifact_id(
        self,
        schedule: dict[str, Any],
        plan: dict[str, Any],
        task: dict[str, Any],
        validation_attempt_id: str,
    ) -> str:
        raw_task = task.get("raw_task") if isinstance(task, dict) else {}
        return self._scoped_id(
            "expected_artifact",
            {
                "validation_attempt_id": validation_attempt_id,
                "required_evidence": schedule.get("required_evidence"),
                "target_operation": schedule.get("target_operation"),
                "validation_contract": (raw_task or {}).get(
                    "expected_validation_contract"
                ),
                "plan_id": plan.get("plan_id"),
            },
        )

    def _produced_artifact_id(
        self,
        runner_output: dict[str, Any],
        validation_attempt_id: str,
    ) -> str:
        return self._scoped_id(
            "captured_artifact",
            {
                "validation_attempt_id": validation_attempt_id,
                "predicted_output": runner_output.get("predicted_output"),
                "case_outputs": runner_output.get("case_outputs") or [],
                "empty_output_valid": runner_output.get("empty_output_valid"),
            },
        )

    def _raw_result_occurrence_id(
        self,
        *,
        schedule: dict[str, Any],
        plan: dict[str, Any],
        execution_id: str,
        validation_attempt_id: str,
        attempt_number: int,
    ) -> str:
        return self._scoped_id(
            "raw_validation_result",
            {
                "identity_schema_version": "1.0",
                "run_id": plan.get("source_run_id"),
                "execution_plan_id": (
                    plan.get("execution_plan_id")
                    or schedule.get("execution_plan_id")
                    or plan.get("plan_id")
                ),
                "task_id": plan.get("source_task_id"),
                "producer_operation_id": execution_id,
                "validation_attempt_id": validation_attempt_id,
                "schedule_id": schedule.get("schedule_id"),
                "attempt_number": attempt_number,
                "producer_type": "scheduled_validation_execution",
            },
        )

    def _raw_result_identity_fingerprint(
        self,
        envelope: dict[str, Any],
    ) -> str:
        return self._scoped_id(
            "raw_result_identity_fingerprint",
            {
                "identity_schema_version": envelope.get("identity_schema_version"),
                "raw_validation_result_id": envelope.get("raw_validation_result_id"),
                "run_id": envelope.get("run_id"),
                "execution_plan_id": envelope.get("execution_plan_id"),
                "task_id": envelope.get("task_id"),
                "producer_operation_id": envelope.get("executor_invocation_id"),
                "validation_attempt_id": envelope.get("validation_attempt_id"),
                "producer_type": envelope.get("producer_source_type"),
            },
        )

    def _raw_result_identity_state(
        self,
        raw_result_id: str | None,
        artifact_state: str | None,
    ) -> str:
        if raw_result_id:
            return "APPLICABLE_ARTIFACT_PRESENT_IDENTITY_BOUND"
        if artifact_state == "ARTIFACT_MISSING":
            return "APPLICABLE_ARTIFACT_MISSING_IDENTITY_NOT_ISSUABLE"
        return "APPLICABLE_ARTIFACT_PRESENT_IDENTITY_MISSING"

    def evaluate_raw_result_identity_integrity(
        self,
        raw_result: dict[str, Any] | None,
        *,
        run_id: str | None,
        execution_plan_id: str | None,
        observed_results: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        raw_result = raw_result if isinstance(raw_result, dict) else {}
        envelope = (
            raw_result.get("RAW_VALIDATION_RESULT_ENVELOPE")
            or raw_result.get("raw_validation_result_envelope")
            or {}
        )
        envelope = envelope if isinstance(envelope, dict) else {}
        canonical_id = (
            raw_result.get("canonical_raw_result_id")
            or raw_result.get("raw_validation_result_id")
            or raw_result.get("raw_result_id")
        )
        conflicts = []
        if self._term(canonical_id) == "Not Available":
            conflicts.append("canonical_raw_result_id_missing")
        if envelope:
            envelope_id = (
                envelope.get("canonical_raw_result_id")
                or envelope.get("raw_validation_result_id")
            )
            if envelope_id != canonical_id:
                conflicts.append("envelope_identity_mismatch")
        if raw_result.get("run_id") != run_id:
            conflicts.append("previous_or_foreign_run_identity")
        if raw_result.get("execution_plan_id") != execution_plan_id:
            conflicts.append("execution_plan_identity_mismatch")
        expected_fingerprint = (
            self._raw_result_identity_fingerprint(envelope)
            if envelope and canonical_id
            else None
        )
        if (
            expected_fingerprint
            and raw_result.get("immutable_identity_fingerprint")
            != expected_fingerprint
        ):
            conflicts.append("immutable_identity_fingerprint_mismatch")
        for observed in observed_results or []:
            if not isinstance(observed, dict) or observed is raw_result:
                continue
            observed_id = (
                observed.get("canonical_raw_result_id")
                or observed.get("raw_validation_result_id")
                or observed.get("raw_result_id")
            )
            if observed_id == canonical_id and (
                observed.get("validation_attempt_id")
                != raw_result.get("validation_attempt_id")
                or observed.get("producer_operation_id")
                != raw_result.get("producer_operation_id")
                or observed.get("executor_invocation_id")
                != raw_result.get("executor_invocation_id")
            ):
                conflicts.append("identity_collision_between_attempts")
                break
        state = (
            "RAW_RESULT_IDENTITY_INTACT"
            if not conflicts
            else "RAW_RESULT_IDENTITY_CONFLICT_DETECTED"
        )
        return {
            "raw_result_identity_integrity_state": state,
            "raw_result_identity_conflict_count": len(conflicts),
            "raw_result_identity_conflicts": conflicts,
            "canonical_raw_result_id": canonical_id,
            "immutable_identity_fingerprint": raw_result.get(
                "immutable_identity_fingerprint",
            ),
            "recomputed_immutable_identity_fingerprint": expected_fingerprint,
            "identity_rewritten": False,
            "identity_evaluation_source": "validation_task_execution_pipeline",
        }

    def _raw_result_identity_transitions(
        self,
        *,
        applicability_report: dict[str, Any] | None = None,
        run_id: str | None,
        execution_plan_id: str | None,
        task_id: str | None,
        producer_operation_id: str | None,
        validation_attempt_id: str | None,
        raw_result_id: str | None,
        source_timestamp: str,
    ) -> list[dict[str, Any]]:
        base = {
            "run_id": run_id,
            "execution_plan_id": execution_plan_id,
            "task_id": task_id,
            "producer_operation_id": producer_operation_id,
            "validation_attempt_id": validation_attempt_id,
            "raw_result_id": raw_result_id,
            "source_stage": "validation_task_execution_pipeline",
            "source_timestamp": source_timestamp,
            "is_current_run": True,
        }
        applicability_report = (
            applicability_report if isinstance(applicability_report, dict) else {}
        )
        applicability_finalized = []
        for transition in (
            applicability_report.get("raw_result_applicability_lifecycle_transitions")
            or applicability_report.get("lifecycle_transitions")
            or []
        ):
            if (
                isinstance(transition, dict)
                and transition.get("transition_name")
                == "RAW_RESULT_APPLICABILITY_FINALIZED"
            ):
                applicability_finalized.append({
                    **base,
                    "transition_name": "RAW_RESULT_APPLICABILITY_FINALIZED",
                    "source_stage": transition.get(
                        "source_stage",
                        "raw_result_lifecycle_applicability_evaluator",
                    ),
                    "source_timestamp": transition.get(
                        "source_timestamp",
                        source_timestamp,
                    ),
                    "sequence_index": 1,
                })
                break
        names = [
            "PRODUCER_OBLIGATION_BOUNDARY_CROSSED",
            "RAW_RESULT_MATERIALIZED",
            "RAW_RESULT_IDENTITY_ISSUANCE_REQUESTED",
            "RAW_RESULT_IDENTITY_ISSUED",
            "RAW_RESULT_IDENTITY_BOUND_TO_ARTIFACT",
            "RAW_RESULT_IDENTITY_PROPAGATED",
            "RAW_RESULT_IDENTITY_INTEGRITY_EVALUATED",
        ]
        offset = 1 if applicability_finalized else 0
        return applicability_finalized + [
            {**base, "transition_name": name, "sequence_index": index + offset}
            for index, name in enumerate(names, start=1)
        ]

    def _producer_applicability_report(
        self,
        schedule: dict[str, Any],
        plan: dict[str, Any],
        execution_id: str,
        attempt_number: int,
        source_timestamp: str,
    ) -> dict[str, Any]:
        validation_attempt_id = self._validation_attempt_id(
            schedule,
            execution_id,
            attempt_number,
        )
        execution_plan_id = (
            plan.get("execution_plan_id")
            or schedule.get("execution_plan_id")
            or plan.get("plan_id")
        )
        return raw_result_lifecycle_applicability_evaluator.evaluate(
            run_id=plan.get("source_run_id"),
            execution_plan_id=execution_plan_id,
            task_id=plan.get("source_task_id"),
            validation_task_execution_report={
                "run_id": plan.get("source_run_id"),
                "execution_plan_id": execution_plan_id,
                "task_id": plan.get("source_task_id"),
                "execution_id": execution_id,
                "producer_operation_id": execution_id,
                "validation_attempt_id": validation_attempt_id,
                "execution_admission_state": "ADMITTED",
                "execution_started": True,
                "execution_invoked": True,
                "current_run_producer_activation": True,
                "execution_state": "EXECUTION_COMPLETED_RESULT_CAPTURE_PENDING",
            },
            validation_scheduling_report=schedule,
            source_timestamp=source_timestamp,
        )

    def _raw_result_envelope(
        self,
        *,
        raw_result_id: str | None,
        fingerprint: str,
        schedule: dict[str, Any],
        plan: dict[str, Any],
        task: dict[str, Any],
        execution_id: str,
        validation_attempt_id: str,
        expected_artifact_id: str,
        produced_artifact_id: str | None,
        captured_artifact_id: str | None,
        artifact_state: str,
        payload_state: str,
        result_state: str,
        identity_state: str,
        structural_eligibility: str,
        ineligibility_reason: str,
        failure_cause: str | None,
        missing_inputs: list[str],
        identity_created_at: str | None,
    ) -> dict[str, Any]:
        run_id = plan.get("source_run_id")
        task_id = plan.get("source_task_id")
        producer_component_id = "VALIDATION_TASK_EXECUTION_PIPELINE"
        producer_source_type = "scheduled_validation_task"
        type_conflicts = []
        if task_id in {
            producer_component_id,
            "semantic_to_transformation_compiler_0",
        }:
            type_conflicts.append("task_id_contains_producer_identity")
        provenance_state = (
            "RAW_RESULT_PROVENANCE_BOUND"
            if not missing_inputs and not type_conflicts
            else "RAW_RESULT_PROVENANCE_UNBOUND"
        )
        binding_state = "BOUND" if provenance_state == "RAW_RESULT_PROVENANCE_BOUND" else "CONFLICTED"
        if type_conflicts:
            identity_state = "RAW_VALIDATION_IDENTITY_TYPE_CONFLICT"
            structural_eligibility = "STRUCTURALLY_INELIGIBLE"
            ineligibility_reason = "RAW_VALIDATION_IDENTITY_TYPE_CONFLICT"
        envelope = {
            "schema_version": "1.0",
            "raw_validation_result_schema_version": "1.0",
            "identity_schema_version": "1.0",
            "raw_validation_result_id": raw_result_id,
            "canonical_raw_result_id": raw_result_id,
            "raw_validation_result_state": result_state,
            "raw_validation_result_identity_state": (
                identity_state
                if raw_result_id
                else "RAW_VALIDATION_RESULT_ID_NOT_ISSUED"
            ),
            "run_id": run_id,
            "batch_id": plan.get("batch_id") or schedule.get("batch_id"),
            "task_id": task_id,
            "execution_plan_id": (
                plan.get("execution_plan_id")
                or schedule.get("execution_plan_id")
                or plan.get("plan_id")
            ),
            "execution_node_id": (
                plan.get("execution_node_id")
                or schedule.get("execution_node_id")
                or "VALIDATION_TASK_EXECUTION_PIPELINE"
            ),
            "activation_request_id": plan.get("activation_request_id"),
            "dependency_operation_id": plan.get("dependency_operation_id"),
            "dependency_link_id": plan.get("dependency_link_id"),
            "dependency_chain_id": plan.get("dependency_chain_id"),
            "executor_id": self.RUNNER_ID,
            "executor_invocation_id": execution_id,
            "producer_operation_id": execution_id,
            "validation_attempt_id": validation_attempt_id,
            "producer_component_id": producer_component_id,
            "producer_source_type": producer_source_type,
            "candidate_source_id": plan.get("source_candidate_id"),
            "claim_id": schedule.get("claim_id") or plan.get("claim_id"),
            "claim_subject": schedule.get("claim_subject") or plan.get("claim_subject"),
            "claim_subject_owner": (
                schedule.get("claim_subject_owner")
                or plan.get("claim_subject_owner")
            ),
            "claim_evidence_binding_authority": (
                schedule.get("claim_evidence_binding_authority")
                or plan.get("claim_evidence_binding_authority")
            ),
            "claim_evidence_binding_behavioral_authority": (
                schedule.get("claim_evidence_binding_behavioral_authority")
                or plan.get("claim_evidence_binding_behavioral_authority")
            ),
            "claim_evidence_binding_state": (
                schedule.get("claim_evidence_binding_state")
                or plan.get("claim_evidence_binding_state")
            ),
            "expected_artifact_id": expected_artifact_id,
            "produced_artifact_id": produced_artifact_id,
            "captured_artifact_id": captured_artifact_id,
            "artifact_state": artifact_state,
            "payload_state": payload_state,
            "payload_reference": (
                captured_artifact_id if captured_artifact_id else None
            ),
            "measurement_receipt_id": plan.get("measurement_receipt_id"),
            "execution_receipt_id": plan.get("execution_receipt_id"),
            "capture_timestamp": self._now(),
            "identity_issued_at": identity_created_at,
            "raw_result_identity_state": self._raw_result_identity_state(
                raw_result_id,
                artifact_state,
            ),
            "raw_result_identity_reason": (
                "RAW_RESULT_IDENTITY_ISSUED_AT_PRODUCER_BOUNDARY"
                if raw_result_id else (
                    "RAW_RESULT_ARTIFACT_MISSING_IDENTITY_NOT_ISSUABLE"
                    if artifact_state == "ARTIFACT_MISSING"
                    else "RAW_RESULT_IDENTITY_INPUT_UNAVAILABLE"
                )
            ),
            "raw_result_identity_issuance_count": 1 if raw_result_id else 0,
            "raw_result_identity_binding_state": (
                "RAW_RESULT_IDENTITY_BOUND_TO_ARTIFACT"
                if raw_result_id else "RAW_RESULT_IDENTITY_NOT_BOUND"
            ),
            "raw_result_identity_integrity_state": (
                "RAW_RESULT_IDENTITY_INTACT"
                if raw_result_id else (
                    "NOT_EVALUATED_ARTIFACT_MISSING"
                    if artifact_state == "ARTIFACT_MISSING"
                    else "RAW_RESULT_IDENTITY_MISSING"
                )
            ),
            "raw_result_identity_conflict_count": 0 if raw_result_id else len(missing_inputs),
            "provenance_state": provenance_state,
            "binding_integrity_state": binding_state,
            "binding_conflict_count": len(missing_inputs) + len(type_conflicts),
            "binding_conflicts": missing_inputs + type_conflicts,
            "finalized_state": "RAW_RESULT_FINALIZED",
            "immutable_state": "RAW_RESULT_IMMUTABLE",
            "downstream_structural_eligibility": structural_eligibility,
            "structural_ineligibility_reason": ineligibility_reason,
            "failure_cause": failure_cause,
            "evidence_evaluation_invoked": False,
            "evidence_record_id": None,
            "raw_result_fingerprint": fingerprint,
            "constitutional_boundary": self.RAW_RESULT_BOUNDARY,
        }
        envelope["raw_validation_result_envelope_fingerprint"] = self._scoped_id(
            "raw_validation_result_envelope",
            envelope,
        )
        return envelope

    def _scoped_id(self, prefix: str, payload: Any) -> str:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        digest = hashlib.sha1(encoded.encode("utf-8")).hexdigest()[:12]
        return f"{prefix}_{digest}"

    def _link_raw_result(
        self,
        plan: dict[str, Any],
        plan_path: Path,
        schedule: dict[str, Any],
        schedule_path: Path,
        raw_result: dict[str, Any],
    ) -> None:
        now = self._now()
        envelope = raw_result.get("RAW_VALIDATION_RESULT_ENVELOPE") or raw_result.get(
            "raw_validation_result_envelope",
            {},
        )
        envelope = envelope if isinstance(envelope, dict) else {}
        linked_plan = {
            **plan,
            "updated_at": now,
            "lifecycle_state": raw_result.get("result_state", "RAW_RESULT_CAPTURED"),
            "execution_state": raw_result.get("result_state", "RAW_RESULT_CAPTURED"),
            "execution_id": raw_result.get("execution_id"),
            "raw_result_id": raw_result.get("raw_result_id"),
            "raw_validation_result_id": raw_result.get("raw_validation_result_id"),
            "canonical_raw_result_id": raw_result.get("canonical_raw_result_id"),
            "raw_result_identity_schema_version": raw_result.get(
                "raw_result_identity_schema_version",
            ),
            "identity_schema_version": raw_result.get("identity_schema_version"),
            "raw_result_identity_state": raw_result.get("raw_result_identity_state"),
            "raw_result_identity_reason": raw_result.get("raw_result_identity_reason"),
            "raw_result_identity_issuance_count": raw_result.get(
                "raw_result_identity_issuance_count",
            ),
            "raw_result_identity_binding_state": raw_result.get(
                "raw_result_identity_binding_state",
            ),
            "raw_result_identity_integrity_state": raw_result.get(
                "raw_result_identity_integrity_state",
            ),
            "raw_result_identity_conflict_count": raw_result.get(
                "raw_result_identity_conflict_count",
            ),
            "immutable_identity_fingerprint": raw_result.get(
                "immutable_identity_fingerprint",
            ),
            "raw_result_identity_lifecycle_transitions": raw_result.get(
                "raw_result_identity_lifecycle_transitions",
                [],
            ),
            "raw_result_applicability_report": raw_result.get(
                "raw_result_applicability_report",
                {},
            ),
            "RAW_RESULT_APPLICABILITY_REPORT": raw_result.get(
                "RAW_RESULT_APPLICABILITY_REPORT",
                {},
            ),
            "raw_result_applicability_state": raw_result.get(
                "raw_result_applicability_state",
            ),
            "raw_result_applicability_finalized": raw_result.get(
                "raw_result_applicability_finalized",
            ),
            "producer_obligation_boundary_crossed": raw_result.get(
                "producer_obligation_boundary_crossed",
            ),
            "producer_operation_id": raw_result.get(
                "producer_operation_id",
                envelope.get("producer_operation_id"),
            ),
            "producer_component_id": raw_result.get(
                "producer_component_id",
                envelope.get("producer_component_id"),
            ),
            "producer_source_type": raw_result.get(
                "producer_source_type",
                envelope.get("producer_source_type"),
            ),
            "producer_operation_type": raw_result.get(
                "producer_operation_type",
                envelope.get("producer_operation_type", envelope.get("producer_source_type")),
            ),
            "raw_result_fingerprint": raw_result.get("raw_result_fingerprint"),
            "RAW_VALIDATION_RESULT_ENVELOPE": raw_result.get(
                "RAW_VALIDATION_RESULT_ENVELOPE",
            ),
            "raw_validation_result_envelope": raw_result.get(
                "raw_validation_result_envelope",
            ),
            "evidence_state": "NOT_EVALUATED",
            "active_execution_lease": False,
            "boot_recovery_route": "RAW_RESULT_CAPTURED_TO_VALIDATION_EVIDENCE_EVALUATOR",
            "candidate_execution_authority": "NONE",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
        }
        linked_schedule = {
            **schedule,
            "execution_id": raw_result.get("execution_id"),
            "raw_result_id": raw_result.get("raw_result_id"),
            "raw_validation_result_id": raw_result.get("raw_validation_result_id"),
            "canonical_raw_result_id": raw_result.get("canonical_raw_result_id"),
            "raw_result_identity_schema_version": raw_result.get(
                "raw_result_identity_schema_version",
            ),
            "identity_schema_version": raw_result.get("identity_schema_version"),
            "raw_result_identity_state": raw_result.get("raw_result_identity_state"),
            "raw_result_identity_reason": raw_result.get("raw_result_identity_reason"),
            "raw_result_identity_issuance_count": raw_result.get(
                "raw_result_identity_issuance_count",
            ),
            "raw_result_identity_binding_state": raw_result.get(
                "raw_result_identity_binding_state",
            ),
            "raw_result_identity_integrity_state": raw_result.get(
                "raw_result_identity_integrity_state",
            ),
            "raw_result_identity_conflict_count": raw_result.get(
                "raw_result_identity_conflict_count",
            ),
            "immutable_identity_fingerprint": raw_result.get(
                "immutable_identity_fingerprint",
            ),
            "raw_result_identity_lifecycle_transitions": raw_result.get(
                "raw_result_identity_lifecycle_transitions",
                [],
            ),
            "raw_result_applicability_report": raw_result.get(
                "raw_result_applicability_report",
                {},
            ),
            "RAW_RESULT_APPLICABILITY_REPORT": raw_result.get(
                "RAW_RESULT_APPLICABILITY_REPORT",
                {},
            ),
            "raw_result_applicability_state": raw_result.get(
                "raw_result_applicability_state",
            ),
            "raw_result_applicability_finalized": raw_result.get(
                "raw_result_applicability_finalized",
            ),
            "producer_obligation_boundary_crossed": raw_result.get(
                "producer_obligation_boundary_crossed",
            ),
            "producer_operation_id": raw_result.get(
                "producer_operation_id",
                envelope.get("producer_operation_id"),
            ),
            "producer_component_id": raw_result.get(
                "producer_component_id",
                envelope.get("producer_component_id"),
            ),
            "producer_source_type": raw_result.get(
                "producer_source_type",
                envelope.get("producer_source_type"),
            ),
            "producer_operation_type": raw_result.get(
                "producer_operation_type",
                envelope.get(
                    "producer_operation_type",
                    envelope.get("producer_source_type"),
                ),
            ),
            "raw_result_fingerprint": raw_result.get("raw_result_fingerprint"),
            "RAW_VALIDATION_RESULT_ENVELOPE": raw_result.get(
                "RAW_VALIDATION_RESULT_ENVELOPE",
            ),
            "raw_validation_result_envelope": raw_result.get(
                "raw_validation_result_envelope",
            ),
            "execution_state": raw_result.get("result_state", "RAW_RESULT_CAPTURED"),
            "execution_invoked": True,
            "active_execution_lease": False,
            "attempt_count": int(raw_result.get("attempt_number", 1) or 1),
            "evidence_state": "NOT_EVALUATED",
            "candidate_execution_authority": "NONE",
        }
        self._atomic_write(schedule_path, linked_schedule)
        self._atomic_write(plan_path, linked_plan)

    def _success_report(
        self,
        base: dict[str, Any],
        plan: dict[str, Any],
        schedule: dict[str, Any],
        raw_result: dict[str, Any],
        result: str,
        *,
        invoked: bool,
    ) -> dict[str, Any]:
        envelope = raw_result.get("RAW_VALIDATION_RESULT_ENVELOPE") or raw_result.get(
            "raw_validation_result_envelope",
            {},
        )
        result_state = raw_result.get("result_state", "RAW_RESULT_CAPTURED")
        captured = result_state in {
            "RAW_RESULT_CAPTURED",
            "RAW_RESULT_EMPTY_VALID_OUTPUT_CAPTURED",
        }
        return {
            **base,
            **self._schedule_identity(schedule),
            "execution_id": raw_result.get("execution_id"),
            "raw_result_id": raw_result.get("raw_result_id"),
            "raw_validation_result_id": raw_result.get("raw_validation_result_id"),
            "canonical_raw_result_id": raw_result.get("canonical_raw_result_id"),
            "raw_result_identity_schema_version": raw_result.get(
                "raw_result_identity_schema_version",
            ),
            "identity_schema_version": raw_result.get("identity_schema_version"),
            "raw_result_identity_state": raw_result.get("raw_result_identity_state"),
            "raw_result_identity_reason": raw_result.get("raw_result_identity_reason"),
            "raw_result_identity_issuance_count": raw_result.get(
                "raw_result_identity_issuance_count",
            ),
            "raw_result_identity_binding_state": raw_result.get(
                "raw_result_identity_binding_state",
            ),
            "raw_result_identity_integrity_state": raw_result.get(
                "raw_result_identity_integrity_state",
            ),
            "raw_result_identity_conflict_count": raw_result.get(
                "raw_result_identity_conflict_count",
            ),
            "immutable_identity_fingerprint": raw_result.get(
                "immutable_identity_fingerprint",
            ),
            "raw_result_identity_fingerprint": raw_result.get(
                "raw_result_identity_fingerprint",
                raw_result.get("immutable_identity_fingerprint"),
            ),
            "identity_issued_at": raw_result.get("identity_issued_at"),
            "identity_evaluation_source": raw_result.get(
                "identity_evaluation_source",
            ),
            "raw_result_identity_lifecycle_transitions": raw_result.get(
                "raw_result_identity_lifecycle_transitions",
                [],
            ),
            "raw_result_applicability_report": raw_result.get(
                "raw_result_applicability_report",
                {},
            ),
            "RAW_RESULT_APPLICABILITY_REPORT": raw_result.get(
                "RAW_RESULT_APPLICABILITY_REPORT",
                {},
            ),
            "raw_result_applicability_state": raw_result.get(
                "raw_result_applicability_state",
            ),
            "raw_result_applicability_finalized": raw_result.get(
                "raw_result_applicability_finalized",
            ),
            "producer_obligation_boundary_crossed": raw_result.get(
                "producer_obligation_boundary_crossed",
            ),
            "producer_operation_id": raw_result.get(
                "producer_operation_id",
                envelope.get("producer_operation_id"),
            ),
            "producer_component_id": raw_result.get(
                "producer_component_id",
                envelope.get("producer_component_id"),
            ),
            "producer_source_type": raw_result.get(
                "producer_source_type",
                envelope.get("producer_source_type"),
            ),
            "producer_operation_type": raw_result.get(
                "producer_operation_type",
                envelope.get(
                    "producer_operation_type",
                    envelope.get("producer_source_type"),
                ),
            ),
            "raw_result_fingerprint": raw_result.get("raw_result_fingerprint"),
            "raw_validation_result_fingerprint": raw_result.get(
                "raw_validation_result_fingerprint",
            ),
            "raw_validation_result_schema_version": raw_result.get(
                "raw_validation_result_schema_version",
            ),
            "RAW_VALIDATION_RESULT_ENVELOPE": envelope,
            "raw_validation_result_envelope": envelope,
            "run_id": raw_result.get("run_id"),
            "batch_id": raw_result.get("batch_id"),
            "task_id": raw_result.get("task_id"),
            "execution_plan_id": raw_result.get("execution_plan_id"),
            "execution_node_id": raw_result.get("execution_node_id"),
            "executor_id": raw_result.get("executor_id"),
            "executor_invocation_id": raw_result.get("executor_invocation_id"),
            "validation_attempt_id": raw_result.get("validation_attempt_id"),
            "expected_artifact_id": raw_result.get("expected_artifact_id"),
            "produced_artifact_id": raw_result.get("produced_artifact_id"),
            "captured_artifact_id": raw_result.get("captured_artifact_id"),
            "artifact_state": raw_result.get("artifact_state"),
            "payload_state": raw_result.get("payload_state"),
            "provenance_state": raw_result.get("provenance_state"),
            "binding_integrity_state": raw_result.get("binding_integrity_state"),
            "downstream_structural_eligibility": raw_result.get(
                "downstream_structural_eligibility",
            ),
            "structural_ineligibility_reason": raw_result.get(
                "structural_ineligibility_reason",
            ),
            "selected_curriculum_id": schedule.get("selected_curriculum_id"),
            "execution_admission_evaluated": True,
            "execution_admission_state": "ADMITTED",
            "execution_admission_reason": "execution_contract_satisfied",
            "validation_execution_authority": "VALIDATION_EXECUTION_PIPELINE",
            "validation_execution_scope": self.EXECUTION_SCOPE,
            "candidate_execution_authority": "NONE",
            "execution_invoked": bool(invoked),
            "execution_started": True,
            "execution_completed": True,
            "execution_state": result_state,
            "execution_attempt_count": int(raw_result.get("attempt_number", 1) or 1),
            "runner_id": raw_result.get("runner_id"),
            "runner_status": raw_result.get("runner_status"),
            "executed_task_count": 1,
            "executed_case_count": len(raw_result.get("case_outputs") or []),
            "execution_duration": raw_result.get("execution_duration"),
            "raw_result_captured": captured,
            "raw_result_creation_result": result,
            "raw_result_persistence_state": "RAW_RESULT_PERSISTED",
            "predicted_output_available": raw_result.get("predicted_output") is not None,
            "runtime_error_available": raw_result.get("runtime_error") is not None,
            "target_reference_forwarded_to_solver": False,
            "prediction_target_comparison_performed": False,
            "accuracy_calculated": False,
            "match_state_calculated": False,
            "evidence_sufficiency_calculated": False,
            "comparable_result_available": False,
            "evidence_evaluation_invoked": False,
            "evidence_produced": False,
            "evidence_acceptance_evaluated": False,
            "evidence_accepted": False,
            "arena_reentry_invoked": False,
            "candidate_ranking_modified": False,
            "evidence_state": "NOT_EVALUATED",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "constitutional_boundary": self.BOUNDARY,
            "raw_result_constitutional_boundary": self.RAW_RESULT_BOUNDARY,
            "next_consumer": (
                "VALIDATION_EVIDENCE_EVALUATOR"
                if raw_result.get("downstream_structural_eligibility")
                == "STRUCTURALLY_ELIGIBLE"
                else "NONE"
            ),
        }

    def _base_report(self, schedule_id: str | None) -> dict[str, Any]:
        return {
            "system": "validation_task_execution_pipeline",
            "responsible_component": "VALIDATION_EXECUTION_PIPELINE",
            "schedule_id": self._term(schedule_id),
            "plan_id": "Not Available",
            "execution_id": "Not Available",
            "raw_result_id": "Not Available",
            "raw_validation_result_id": "Not Available",
            "canonical_raw_result_id": "Not Available",
            "raw_validation_result_schema_version": "Not Available",
            "raw_result_identity_schema_version": "Not Available",
            "identity_schema_version": "Not Available",
            "raw_result_identity_state": "NOT_EVALUATED_NOT_APPLICABLE",
            "raw_result_identity_reason": "RAW_RESULT_IDENTITY_NOT_EXPECTED",
            "raw_result_identity_issuance_count": 0,
            "raw_result_identity_binding_state": "NOT_EVALUATED_NOT_APPLICABLE",
            "raw_result_identity_integrity_state": "NOT_EVALUATED_NOT_APPLICABLE",
            "raw_result_identity_conflict_count": 0,
            "immutable_identity_fingerprint": "Not Available",
            "identity_evaluation_source": "validation_task_execution_pipeline",
            "raw_result_identity_lifecycle_transitions": [],
            "RAW_VALIDATION_RESULT_ENVELOPE": {},
            "raw_validation_result_envelope": {},
            "run_id": "Not Available",
            "batch_id": "Not Available",
            "task_id": "Not Available",
            "execution_plan_id": "Not Available",
            "execution_node_id": "Not Available",
            "executor_invocation_id": "Not Available",
            "validation_attempt_id": "Not Available",
            "expected_artifact_id": "Not Available",
            "produced_artifact_id": "Not Available",
            "captured_artifact_id": "Not Available",
            "artifact_state": "ARTIFACT_NOT_EXPECTED",
            "payload_state": "PAYLOAD_NOT_EXPECTED",
            "provenance_state": "RAW_RESULT_NOT_APPLICABLE",
            "binding_integrity_state": "NOT_APPLICABLE",
            "downstream_structural_eligibility": "STRUCTURALLY_INELIGIBLE",
            "structural_ineligibility_reason": "RAW_RESULT_NOT_APPLICABLE",
            "selected_validation_task_id": "Not Available",
            "selected_curriculum_id": "Not Available",
            "execution_admission_evaluated": False,
            "execution_admission_state": "NOT_EVALUATED",
            "execution_admission_reason": "not_evaluated",
            "validation_execution_authority": "NONE",
            "validation_execution_scope": "Not Available",
            "candidate_execution_authority": "NONE",
            "execution_invoked": False,
            "execution_started": False,
            "execution_completed": False,
            "execution_state": "NOT_STARTED",
            "execution_attempt_count": 0,
            "runner_id": self.RUNNER_ID,
            "runner_status": "NOT_STARTED",
            "executed_task_count": 0,
            "executed_case_count": 0,
            "execution_duration": 0,
            "raw_result_captured": False,
            "raw_result_creation_result": "NOT_ATTEMPTED",
            "raw_result_persistence_state": "NOT_PERSISTED",
            "raw_result_fingerprint": "Not Available",
            "predicted_output_available": False,
            "runtime_error_available": False,
            "target_reference_forwarded_to_solver": False,
            "prediction_target_comparison_performed": False,
            "accuracy_calculated": False,
            "match_state_calculated": False,
            "evidence_sufficiency_calculated": False,
            "comparable_result_available": False,
            "evidence_evaluation_invoked": False,
            "evidence_produced": False,
            "evidence_acceptance_evaluated": False,
            "evidence_accepted": False,
            "arena_reentry_invoked": False,
            "candidate_ranking_modified": False,
            "evidence_state": "NOT_EVALUATED",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "constitutional_boundary": self.BOUNDARY,
            "next_consumer": "Not Available",
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
            "execution_admission_evaluated": True,
            "execution_admission_state": state,
            "execution_admission_reason": reason,
            "blocked_stage": stage,
            "responsible_component": "VALIDATION_EXECUTION_PIPELINE",
            "recommended_action": action,
            "execution_invoked": False,
            "execution_started": False,
            "execution_completed": False,
            "raw_result_captured": False,
            "raw_result_creation_result": "EXECUTION_BLOCKED",
            "evidence_state": "NOT_EVALUATED",
        }

    def _admission_block(
        self,
        state: str,
        reason: str,
        stage: str,
        action: str,
    ) -> dict[str, Any]:
        return {
            "execution_admission_state": state,
            "execution_admission_reason": reason,
            "blocked_stage": stage,
            "responsible_component": "VALIDATION_EXECUTION_PIPELINE",
            "recommended_action": action,
        }

    def _schedule_identity(self, schedule: dict[str, Any]) -> dict[str, Any]:
        return {
            "plan_id": schedule.get("plan_id", "Not Available"),
            "plan_fingerprint": schedule.get("plan_fingerprint", "Not Available"),
            "run_id": schedule.get("source_run_id", "Not Available"),
            "batch_id": schedule.get("batch_id", "Not Available"),
            "task_id": schedule.get("source_task_id", "Not Available"),
            "execution_plan_id": schedule.get(
                "execution_plan_id",
                schedule.get("plan_id", "Not Available"),
            ),
            "schedule_id": schedule.get("schedule_id", "Not Available"),
            "schedule_fingerprint": schedule.get(
                "schedule_fingerprint",
                "Not Available",
            ),
            "selected_validation_task_id": schedule.get(
                "selected_validation_task_id",
                "Not Available",
            ),
            "selected_curriculum_id": schedule.get(
                "selected_curriculum_id",
                "Not Available",
            ),
            "required_evidence": schedule.get("required_evidence", "Not Available"),
            "required_evidence_category": schedule.get(
                "required_evidence_category",
                "Not Available",
            ),
            "target_candidate": schedule.get("target_candidate", "Not Available"),
            "target_operation": schedule.get("target_operation", "Not Available"),
            "claim_id": schedule.get("claim_id", "Not Available"),
            "claim_subject": schedule.get("claim_subject"),
            "claim_subject_owner": schedule.get("claim_subject_owner"),
            "claim_evidence_binding_authority": schedule.get(
                "claim_evidence_binding_authority"
            ),
            "claim_evidence_binding_behavioral_authority": schedule.get(
                "claim_evidence_binding_behavioral_authority"
            ),
            "claim_evidence_binding_state": schedule.get(
                "claim_evidence_binding_state"
            ),
            "tie_break_strategy": schedule.get("tie_break_strategy", "Not Available"),
        }

    def _public_projection(self, report: dict[str, Any]) -> dict[str, Any]:
        base = self._base_report(report.get("schedule_id"))
        return {**base, **report} if report else base

    def _execution_id(self, schedule: dict[str, Any]) -> str:
        seed = ":".join([
            str(schedule.get("schedule_id")),
            str(schedule.get("schedule_fingerprint")),
            self.RUNNER_VERSION,
            self.EXECUTION_SCOPE,
        ])
        return f"validation_execution_{hashlib.sha1(seed.encode()).hexdigest()[:12]}"

    def _raw_result_fingerprint(
        self,
        schedule: dict[str, Any],
        plan: dict[str, Any],
        execution_id: str,
        attempt_number: int,
    ) -> str:
        payload = {
            "source_run_id": plan.get("source_run_id"),
            "source_task_id": plan.get("source_task_id"),
            "batch_id": plan.get("batch_id") or schedule.get("batch_id"),
            "execution_plan_id": (
                plan.get("execution_plan_id")
                or schedule.get("execution_plan_id")
                or plan.get("plan_id")
            ),
            "plan_id": schedule.get("plan_id"),
            "plan_fingerprint": schedule.get("plan_fingerprint"),
            "schedule_id": schedule.get("schedule_id"),
            "schedule_fingerprint": schedule.get("schedule_fingerprint"),
            "selected_validation_task_id": schedule.get("selected_validation_task_id"),
            "attempt_number": attempt_number,
            "runner_version": self.RUNNER_VERSION,
            "execution_scope": self.EXECUTION_SCOPE,
            "execution_id": execution_id,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest()

    def _existing_raw_result(self, schedule: dict[str, Any]) -> dict[str, Any] | None:
        raw_id = schedule.get("raw_result_id")
        if raw_id:
            path = self.raw_results_path / f"{raw_id}.json"
            result, error = self._read_json(path)
            if not error and isinstance(result, dict):
                return result
        for path in self._plan_files(self.raw_results_path):
            result, error = self._read_json(path)
            if error or not isinstance(result, dict):
                continue
            if result.get("schedule_id") == schedule.get("schedule_id"):
                return result
        return None

    def _persist_execution_failure(
        self,
        plan_path: Path,
        schedule_path: Path,
        failure: dict[str, Any],
    ) -> None:
        schedule, _ = self._read_json(schedule_path)
        plan, _ = self._read_json(plan_path)
        if isinstance(schedule, dict):
            schedule.update({
                "execution_state": "EXECUTION_FAILED",
                "execution_failure": failure,
                "active_execution_lease": False,
            })
            self._atomic_write(schedule_path, schedule)
        if isinstance(plan, dict):
            plan.update({
                "lifecycle_state": "EXECUTION_FAILED",
                "execution_state": "EXECUTION_FAILED",
                "execution_failure": failure,
                "active_execution_lease": False,
                "evidence_state": "NOT_EVALUATED",
            })
            self._atomic_write(plan_path, plan)

    def _execution_failure_record(
        self,
        schedule: dict[str, Any],
        plan: dict[str, Any],
        execution_id: str,
        attempt_number: int,
        started_at: str,
        failed_at: str,
        error: str,
    ) -> dict[str, Any]:
        return {
            "execution_id": execution_id,
            "schedule_id": schedule.get("schedule_id"),
            "plan_id": plan.get("plan_id"),
            "task_id": schedule.get("selected_validation_task_id"),
            "attempt_number": attempt_number,
            "failure_type": "EXECUTION_FAILED_RUNNER_EXCEPTION",
            "failure_reason": error,
            "failed_stage": "runner_invocation",
            "runner_error": error,
            "retry_eligible": False,
            "recommended_action": "execution_failure_review",
            "execution_started_at": started_at,
            "execution_failed_at": failed_at,
            "evidence_state": "NOT_EVALUATED",
        }

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

    def _initialize(self) -> None:
        self.pending_path.mkdir(parents=True, exist_ok=True)
        self.schedules_path.mkdir(parents=True, exist_ok=True)
        self.raw_results_path.mkdir(parents=True, exist_ok=True)

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
