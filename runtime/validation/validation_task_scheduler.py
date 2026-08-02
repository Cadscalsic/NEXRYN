from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
)


class ValidationTaskScheduler:
    """Governed admission and durable scheduling for selected validation tasks."""

    BOUNDARY = (
        "VALIDATION_SCHEDULE_IS_A_GOVERNED_FUTURE_EXECUTION_REQUEST_NOT_EXECUTION_OR_EVIDENCE"
    )

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
        self.curriculum_registry = (
            curriculum_registry or ValidationCurriculumRegistry()
        )

    def schedule_waiting_execution_plans(self) -> dict[str, Any]:
        self._initialize()
        reports = []
        for path in self._plan_files(self.pending_path):
            plan, error = self._read_json(path)
            if error or not isinstance(plan, dict):
                continue
            if plan.get("lifecycle_state") in {
                "WAITING_EXECUTION",
                "SCHEDULING_PREPARED",
            }:
                reports.append(self.schedule_plan(plan.get("plan_id")))
        successful = [
            report for report in reports
            if report.get("scheduling_state") == "SCHEDULED"
        ]
        current = successful[0] if successful else reports[0] if reports else {}
        return {
            "system": "validation_task_scheduler",
            "responsible_component": "VALIDATION_TASK_SCHEDULER",
            "scheduling_attempted": bool(reports),
            "scheduled_plan_count": len(successful),
            "schedule_reports": reports,
            "task_selected": bool(current.get("task_selected", False)),
            "task_scheduled": bool(current.get("task_scheduled", False)),
            "task_execution_started": False,
            "task_execution_completed": False,
            "selection_state": current.get("selection_state", "NOT_SELECTED"),
            "scheduling_admission_state": current.get(
                "scheduling_admission_state",
                "NOT_EVALUATED",
            ),
            "scheduling_admission_reason": current.get(
                "scheduling_admission_reason",
                "not_evaluated",
            ),
            "scheduling_state": current.get("scheduling_state", "NOT_SCHEDULED"),
            "schedule_id": current.get("schedule_id", "Not Available"),
            "schedule_creation_result": current.get(
                "schedule_creation_result",
                "NOT_ATTEMPTED",
            ),
            "evidence_plan_lifecycle_state": current.get(
                "evidence_plan_lifecycle_state",
                "Not Available",
            ),
            "persisted_lifecycle_state": current.get(
                "evidence_plan_lifecycle_state",
                "Not Available",
            ),
            "persisted_selected_validation_task": current.get(
                "selected_validation_task_id",
                "Not Available",
            ),
            "boot_recovery_route": current.get(
                "boot_recovery_route",
                "Not Available",
            ),
            "scheduling_authority": current.get(
                "scheduling_authority",
                "VALIDATION_SCHEDULER",
            ),
            "execution_state": current.get("execution_state", "NOT_STARTED"),
            "execution_invoked": False,
            "execution_authority": "NONE",
            "constitutional_boundary": self.BOUNDARY,
        }

    def schedule_plan(self, plan_id: str | None) -> dict[str, Any]:
        self._initialize()
        plan, path, read_error = self._load_plan(plan_id)
        base = self._base_report(plan_id)
        if read_error or not plan or not path:
            return self._blocked(
                base,
                "BLOCKED_INVALID_PLAN_STATE",
                read_error or "plan_not_found",
                "plan_load",
                "restore_or_recreate_evidence_plan",
            )
        if plan.get("lifecycle_state") == "SCHEDULED":
            existing = self._find_schedule(self.schedule_fingerprint(plan))
            if existing:
                return self._scheduled_report(
                    base,
                    plan,
                    existing,
                    "REUSED_EXISTING_SCHEDULE",
                )

        admission = self._admission(plan)
        if admission["scheduling_admission_state"] != "ADMITTED":
            return {
                **base,
                **admission,
                "plan_id": plan.get("plan_id", plan_id),
                "plan_fingerprint": plan.get(
                    "plan_fingerprint",
                    "Not Available",
                ),
                "selected_validation_task_id": plan.get(
                    "selected_validation_task_id",
                    "Not Available",
                ),
            }

        schedule = self._schedule_record(plan, admission)
        existing = self._find_schedule(schedule["schedule_fingerprint"])
        if existing:
            return self._link_existing_schedule(plan, path, existing, base)

        now = self._now()
        prepared = {
            **plan,
            "updated_at": now,
            "lifecycle_state": "SCHEDULING_PREPARED",
            "scheduling_state": "SCHEDULING_PREPARED",
            "scheduling_admission_state": "ADMITTED",
            "scheduling_admission_reason": "admission_contract_satisfied",
            "schedule_id": schedule["schedule_id"],
            "execution_state": "NOT_STARTED",
            "execution_invoked": False,
            "execution_authority": "NONE",
        }
        prepared.setdefault("history", []).append({
            "timestamp": now,
            "state": "SCHEDULING_PREPARED",
            "event": "validation_scheduling_prepared",
            "schedule_id": schedule["schedule_id"],
        })
        try:
            self._atomic_write(path, prepared)
            self._atomic_write(
                self.schedules_path / f"{schedule['schedule_id']}.json",
                schedule,
            )
            scheduled = {
                **prepared,
                "updated_at": self._now(),
                "lifecycle_state": "SCHEDULED",
                "scheduling_state": "SCHEDULED",
                "boot_recovery_route": "SCHEDULED_TO_VALIDATION_EXECUTION_PIPELINE",
            }
            scheduled.setdefault("history", []).append({
                "timestamp": scheduled["updated_at"],
                "state": "SCHEDULED",
                "event": "validation_schedule_linked_to_plan",
                "schedule_id": schedule["schedule_id"],
            })
            self._atomic_write(path, scheduled)
        except (OSError, TypeError, ValueError) as error:
            return self._blocked(
                {
                    **base,
                    "plan_id": plan.get("plan_id", plan_id),
                    "schedule_id": schedule["schedule_id"],
                },
                "BLOCKED_SCHEDULING_PERSISTENCE_FAILURE",
                str(error),
                "schedule_persistence",
                "retry_idempotent_validation_scheduling",
            )

        return self._scheduled_report(
            base,
            scheduled,
            schedule,
            "CREATED_NEW_SCHEDULE",
        )

    def _link_existing_schedule(
        self,
        plan: dict[str, Any],
        path: Path,
        schedule: dict[str, Any],
        base: dict[str, Any],
    ) -> dict[str, Any]:
        if plan.get("lifecycle_state") != "SCHEDULED":
            now = self._now()
            plan = {
                **plan,
                "updated_at": now,
                "lifecycle_state": "SCHEDULED",
                "scheduling_state": "SCHEDULED",
                "scheduling_admission_state": "ADMITTED",
                "scheduling_admission_reason": "admission_contract_satisfied",
                "schedule_id": schedule.get("schedule_id"),
                "execution_state": "NOT_STARTED",
                "execution_invoked": False,
                "execution_authority": "NONE",
                "boot_recovery_route": "SCHEDULED_TO_VALIDATION_EXECUTION_PIPELINE",
            }
            plan.setdefault("history", []).append({
                "timestamp": now,
                "state": "SCHEDULED",
                "event": "existing_validation_schedule_relinked",
                "schedule_id": schedule.get("schedule_id"),
            })
            self._atomic_write(path, plan)
        return self._scheduled_report(
            base,
            plan,
            schedule,
            "REUSED_EXISTING_SCHEDULE",
        )

    def _admission(self, plan: dict[str, Any]) -> dict[str, Any]:
        lifecycle = plan.get("lifecycle_state")
        if lifecycle not in {"WAITING_EXECUTION", "SCHEDULING_PREPARED"}:
            return self._admission_block(
                "BLOCKED_INVALID_PLAN_STATE",
                f"expected_WAITING_EXECUTION_observed_{lifecycle}",
                "plan_lifecycle",
                "restore_waiting_execution_lifecycle_before_scheduling",
            )
        if plan.get("execution_authority") != "NONE":
            return self._admission_block(
                "BLOCKED_CONSTITUTIONAL_VIOLATION",
                "execution_authority_not_none",
                "authority_validation",
                "reset_execution_authority_to_none",
            )
        for field in ("truth_authority", "trust_authority", "graduation_authority"):
            if plan.get(field) != "NONE":
                return self._admission_block(
                    "BLOCKED_CONSTITUTIONAL_VIOLATION",
                    f"{field}_not_none",
                    "authority_validation",
                    "restore_constitutional_authority_boundaries",
                )
        task_id = self._term(plan.get("selected_validation_task_id"))
        if task_id == "Not Available":
            return self._admission_block(
                "BLOCKED_MISSING_SELECTED_TASK",
                "selected_validation_task_id_missing",
                "selected_task_validation",
                "persist_selected_validation_task_before_scheduling",
            )
        lookup = self.curriculum_registry.find_task(
            task_id,
            plan.get("selected_curriculum_id"),
        )
        if not lookup.get("found"):
            return self._admission_block(
                "BLOCKED_TASK_NOT_FOUND",
                "selected_task_not_found_in_registered_curriculum",
                "curriculum_lookup",
                "restore_curriculum_or_reselect_validation_task",
            )
        if not lookup.get("enabled"):
            return self._admission_block(
                "BLOCKED_TASK_DISABLED",
                "selected_curriculum_task_disabled",
                "curriculum_lookup",
                "enable_curriculum_or_reselect_validation_task",
            )
        task = lookup.get("task") or {}
        if not task.get("task_id") or not task.get("supported_evidence"):
            return self._admission_block(
                "BLOCKED_INVALID_TASK_SCHEMA",
                "task_metadata_missing_required_fields",
                "task_schema_validation",
                "repair_validation_task_metadata",
            )
        evidence = self._norm(plan.get("required_evidence"))
        category = self._norm(plan.get("required_evidence_category"))
        task_evidence = {
            self._norm(item) for item in task.get("supported_evidence", [])
        }
        if evidence not in task_evidence or category not in task_evidence:
            return self._admission_block(
                "BLOCKED_EVIDENCE_MISMATCH",
                "selected_task_evidence_metadata_incompatible",
                "evidence_compatibility",
                "reselect_compatible_validation_task",
            )
        for field in ("target_candidate", "target_operation", "tie_break_strategy"):
            if self._term(plan.get(field)) == "Not Available":
                return self._admission_block(
                    "BLOCKED_INVALID_PLAN_STATE",
                    f"missing_{field}",
                    "scheduling_payload_materialization",
                    "repair_evidence_plan_payload",
                )
        schedule_fingerprint = self.schedule_fingerprint(plan)
        existing = self._find_schedule(schedule_fingerprint)
        if existing and existing.get("execution_state") not in {
            "NOT_STARTED",
            "NOT_SCHEDULED",
        }:
            return self._admission_block(
                "BLOCKED_ALREADY_EXECUTED",
                "schedule_execution_already_started_or_completed",
                "duplicate_execution_guard",
                "do_not_reschedule_executed_validation_task",
            )
        return {
            "scheduling_admission_state": "ADMITTED",
            "scheduling_admission_reason": "admission_contract_satisfied",
            "blocked_stage": "none",
            "responsible_component": "VALIDATION_TASK_SCHEDULER",
            "recommended_action": "persist_governed_validation_schedule",
            "selected_task_metadata": task,
            "selected_curriculum_metadata": lookup.get("curriculum") or {},
        }

    def _schedule_record(
        self,
        plan: dict[str, Any],
        admission: dict[str, Any],
    ) -> dict[str, Any]:
        fingerprint = self.schedule_fingerprint(plan)
        schedule_id = f"validation_schedule_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
        now = self._now()
        return {
            "schema_version": "1.0",
            "schedule_id": schedule_id,
            "plan_id": plan.get("plan_id"),
            "plan_fingerprint": plan.get("plan_fingerprint"),
            "selected_validation_task_id": plan.get("selected_validation_task_id"),
            "selected_curriculum_id": plan.get("selected_curriculum_id"),
            "required_evidence": plan.get("required_evidence"),
            "required_evidence_category": plan.get("required_evidence_category"),
            "target_candidate": plan.get("target_candidate"),
            "target_operation": plan.get("target_operation"),
            "tie_break_strategy": plan.get("tie_break_strategy"),
            "scheduling_authority": "VALIDATION_SCHEDULER",
            "scheduling_admission_state": "ADMITTED",
            "scheduling_admission_reason": "admission_contract_satisfied",
            "scheduling_timestamp": now,
            "scheduling_state": "SCHEDULED",
            "execution_state": "NOT_STARTED",
            "execution_invoked": False,
            "execution_authority": "NONE",
            "attempt_count": 0,
            "schedule_fingerprint": fingerprint,
            "constitutional_boundary": self.BOUNDARY,
            "selected_task_metadata": admission.get("selected_task_metadata") or {},
        }

    def schedule_fingerprint(self, plan: dict[str, Any]) -> str:
        payload = {
            "plan_id": plan.get("plan_id"),
            "plan_fingerprint": plan.get("plan_fingerprint"),
            "selected_validation_task_id": plan.get("selected_validation_task_id"),
            "required_evidence": plan.get("required_evidence"),
            "target_candidate": plan.get("target_candidate"),
            "target_operation": plan.get("target_operation"),
            "tie_break_strategy": plan.get("tie_break_strategy"),
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _base_report(self, plan_id: str | None) -> dict[str, Any]:
        return {
            "system": "validation_task_scheduler",
            "responsible_component": "VALIDATION_TASK_SCHEDULER",
            "plan_id": self._term(plan_id),
            "plan_fingerprint": "Not Available",
            "schedule_id": "Not Available",
            "task_selected": False,
            "task_scheduled": False,
            "task_execution_started": False,
            "task_execution_completed": False,
            "selected_validation_task_id": "Not Available",
            "selected_curriculum_id": "Not Available",
            "selection_state": "NOT_SELECTED",
            "scheduling_authority": "VALIDATION_SCHEDULER",
            "scheduling_admission_state": "NOT_EVALUATED",
            "scheduling_admission_reason": "not_evaluated",
            "scheduling_state": "NOT_SCHEDULED",
            "schedule_creation_result": "NOT_ATTEMPTED",
            "execution_state": "NOT_STARTED",
            "execution_invoked": False,
            "execution_authority": "NONE",
            "attempt_count": 0,
            "blocked_stage": "none",
            "recommended_action": "none",
            "constitutional_boundary": self.BOUNDARY,
            "evidence_produced": False,
            "evidence_accepted": False,
            "arena_reentry_performed": False,
            "candidate_ranking_modified": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
        }

    def _scheduled_report(
        self,
        base: dict[str, Any],
        plan: dict[str, Any],
        schedule: dict[str, Any],
        result: str,
    ) -> dict[str, Any]:
        return {
            **base,
            "plan_id": plan.get("plan_id"),
            "plan_fingerprint": plan.get("plan_fingerprint"),
            "schedule_id": schedule.get("schedule_id"),
            "schedule_fingerprint": schedule.get("schedule_fingerprint"),
            "task_selected": True,
            "task_scheduled": True,
            "task_execution_started": False,
            "task_execution_completed": False,
            "selected_validation_task_id": plan.get("selected_validation_task_id"),
            "selected_curriculum_id": plan.get("selected_curriculum_id"),
            "selection_state": "TASK_SELECTED",
            "scheduling_admission_state": "ADMITTED",
            "scheduling_admission_reason": "admission_contract_satisfied",
            "scheduling_state": "SCHEDULED",
            "schedule_creation_result": result,
            "execution_state": "NOT_STARTED",
            "execution_invoked": False,
            "execution_authority": "NONE",
            "attempt_count": int(schedule.get("attempt_count", 0) or 0),
            "boot_recovery_route": "SCHEDULED_TO_VALIDATION_EXECUTION_PIPELINE",
            "evidence_plan_lifecycle_state": "SCHEDULED",
        }

    def _blocked(
        self,
        base: dict[str, Any],
        outcome: str,
        reason: str,
        stage: str,
        action: str,
    ) -> dict[str, Any]:
        return {
            **base,
            "scheduling_admission_state": outcome,
            "scheduling_admission_reason": reason,
            "blocked_stage": stage,
            "responsible_component": "VALIDATION_TASK_SCHEDULER",
            "recommended_action": action,
            "schedule_creation_result": (
                "SCHEDULE_PERSISTENCE_FAILED"
                if outcome == "BLOCKED_SCHEDULING_PERSISTENCE_FAILURE"
                else "SCHEDULE_CREATION_BLOCKED"
            ),
            "scheduling_state": "NOT_SCHEDULED",
            "task_scheduled": False,
            "execution_state": "NOT_STARTED",
            "execution_invoked": False,
            "execution_authority": "NONE",
        }

    def _admission_block(
        self,
        outcome: str,
        reason: str,
        stage: str,
        action: str,
    ) -> dict[str, Any]:
        return {
            "scheduling_admission_state": outcome,
            "scheduling_admission_reason": reason,
            "blocked_stage": stage,
            "responsible_component": "VALIDATION_TASK_SCHEDULER",
            "recommended_action": action,
        }

    def _load_plan(
        self,
        plan_id: str | None,
    ) -> tuple[dict[str, Any] | None, Path | None, str | None]:
        if self._term(plan_id) == "Not Available":
            return None, None, "missing_plan_id"
        for directory in (self.pending_path,):
            path = directory / f"{plan_id}.json"
            plan, error = self._read_json(path)
            if error:
                continue
            if isinstance(plan, dict):
                return plan, path, None
        return None, None, "plan_not_found"

    def _find_schedule(self, fingerprint: str) -> dict[str, Any] | None:
        for path in self._plan_files(self.schedules_path):
            record, error = self._read_json(path)
            if error or not isinstance(record, dict):
                continue
            if record.get("schedule_fingerprint") == fingerprint:
                return record
        return None

    def _initialize(self) -> None:
        self.pending_path.mkdir(parents=True, exist_ok=True)
        self.schedules_path.mkdir(parents=True, exist_ok=True)

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

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower()
