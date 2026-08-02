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
        )
        raw_path = self.raw_results_path / f"{raw_result['raw_result_id']}.json"
        try:
            prepared_schedule = {
                **started_schedule,
                "execution_state": "EXECUTION_COMPLETED_RESULT_CAPTURE_PENDING",
                "execution_completed_at": completed_at,
                "raw_result_id": raw_result["raw_result_id"],
            }
            prepared_plan = {
                **started_plan,
                "lifecycle_state": "EXECUTION_COMPLETED_RESULT_CAPTURE_PENDING",
                "execution_state": "EXECUTION_COMPLETED_RESULT_CAPTURE_PENDING",
                "execution_completed_at": completed_at,
                "raw_result_id": raw_result["raw_result_id"],
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
            {**prepared_plan, "lifecycle_state": "RAW_RESULT_CAPTURED"},
            {**prepared_schedule, "execution_state": "RAW_RESULT_CAPTURED"},
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
    ) -> dict[str, Any]:
        fingerprint = self._raw_result_fingerprint(
            schedule,
            execution_id,
            attempt_number,
        )
        raw_result_id = f"raw_validation_result_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
        return {
            "schema_version": "1.0",
            "raw_result_id": raw_result_id,
            "raw_result_fingerprint": fingerprint,
            "execution_id": execution_id,
            "schedule_id": schedule.get("schedule_id"),
            "plan_id": plan.get("plan_id"),
            "plan_fingerprint": plan.get("plan_fingerprint"),
            "schedule_fingerprint": schedule.get("schedule_fingerprint"),
            "selected_validation_task_id": schedule.get("selected_validation_task_id"),
            "selected_curriculum_id": schedule.get("selected_curriculum_id"),
            "target_candidate": schedule.get("target_candidate"),
            "target_operation": schedule.get("target_operation"),
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
            "result_state": "RAW_RESULT_CAPTURED",
            "comparison_state": "NOT_COMPARED",
            "evidence_state": "NOT_EVALUATED",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "candidate_execution_authority": "NONE",
            "constitutional_boundary": self.RAW_RESULT_BOUNDARY,
        }

    def _link_raw_result(
        self,
        plan: dict[str, Any],
        plan_path: Path,
        schedule: dict[str, Any],
        schedule_path: Path,
        raw_result: dict[str, Any],
    ) -> None:
        now = self._now()
        linked_plan = {
            **plan,
            "updated_at": now,
            "lifecycle_state": "RAW_RESULT_CAPTURED",
            "execution_state": "RAW_RESULT_CAPTURED",
            "execution_id": raw_result.get("execution_id"),
            "raw_result_id": raw_result.get("raw_result_id"),
            "raw_result_fingerprint": raw_result.get("raw_result_fingerprint"),
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
            "raw_result_fingerprint": raw_result.get("raw_result_fingerprint"),
            "execution_state": "RAW_RESULT_CAPTURED",
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
        return {
            **base,
            **self._schedule_identity(schedule),
            "execution_id": raw_result.get("execution_id"),
            "raw_result_id": raw_result.get("raw_result_id"),
            "raw_result_fingerprint": raw_result.get("raw_result_fingerprint"),
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
            "execution_state": "RAW_RESULT_CAPTURED",
            "execution_attempt_count": int(raw_result.get("attempt_number", 1) or 1),
            "runner_id": raw_result.get("runner_id"),
            "runner_status": raw_result.get("runner_status"),
            "executed_task_count": 1,
            "executed_case_count": len(raw_result.get("case_outputs") or []),
            "execution_duration": raw_result.get("execution_duration"),
            "raw_result_captured": True,
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
            "next_consumer": "VALIDATION_EVIDENCE_EVALUATOR",
        }

    def _base_report(self, schedule_id: str | None) -> dict[str, Any]:
        return {
            "system": "validation_task_execution_pipeline",
            "responsible_component": "VALIDATION_EXECUTION_PIPELINE",
            "schedule_id": self._term(schedule_id),
            "plan_id": "Not Available",
            "execution_id": "Not Available",
            "raw_result_id": "Not Available",
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
        execution_id: str,
        attempt_number: int,
    ) -> str:
        payload = {
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
