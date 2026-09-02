from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.claim_identity import ClaimIdentityError, claim_identity_for_evidence_plan


class EvidenceAcquisitionPlanStore:
    """Durable orchestration state for evidence acquisition plans."""

    SCHEMA_VERSION = "1.0"
    BOUNDARY = (
        "EVIDENCE_ACQUISITION_PLAN_IS_A_GOVERNED_REQUEST_FOR_VALIDATION_NOT_EVIDENCE"
    )
    AUTHORITY_BOUNDARY = (
        "EVIDENCE_PLAN_DOES_NOT_GRANT_TRUTH_TRUST_GRADUATION_OR_EXECUTION_AUTHORITY"
    )
    REQUIRED_FIELDS = {
        "plan_id",
        "plan_fingerprint",
        "source_run_id",
        "source_task_id",
        "required_evidence",
        "required_validation_task",
        "tie_break_strategy",
        "target_candidate",
        "target_operation",
        "governed_reentry_action",
    }
    TERMINAL_DIRS = {"resolved", "superseded", "invalid", "archive"}

    def __init__(
        self,
        root_path: str | os.PathLike[str] = (
            "runtime/state/evidence_acquisition_plans"
        ),
    ):
        self.root_path = Path(root_path)
        self.pending_path = self.root_path / "pending"
        self.active_path = self.root_path / "active"
        self.resolved_path = self.root_path / "resolved"
        self.superseded_path = self.root_path / "superseded"
        self.invalid_path = self.root_path / "invalid"
        self.archive_path = self.root_path / "archive"
        self._loaded_this_run: set[str] = set()
        self.last_report: dict[str, Any] = self._empty_report()

    def _empty_report(self) -> dict[str, Any]:
        return {
            "system": "evidence_acquisition_plan_store",
            "evidence_plan_store_state": "NOT_INITIALIZED",
            "evidence_plan_boot_load_state": "NOT_LOADED",
            "evidence_plan_persistence_attempted": False,
            "evidence_plan_persisted": False,
            "evidence_plan_id": "Not Available",
            "evidence_plan_fingerprint": "Not Available",
            "evidence_plan_lifecycle_state": "Not Available",
            "evidence_plan_storage_state": "Not Available",
            "evidence_plan_storage_path": str(self.root_path),
            "equivalent_pending_plan_found": False,
            "duplicate_persistence_prevented": False,
            "pending_evidence_plan_count": 0,
            "evidence_plans_loaded_at_boot": 0,
            "evidence_plans_delivered_to_training_assistant": 0,
            "training_assistant_plan_available": False,
            "current_run_consumption_expected": False,
            "next_run_consumption_required": False,
            "current_run_consumption_failure": False,
            "plan_persistence_failure_reason": "none",
            "plan_schema_version": self.SCHEMA_VERSION,
            "plan_constitutional_boundary": self.BOUNDARY,
            "plan_creation_result": "Not Available",
            "lifecycle_update_attempted": False,
            "lifecycle_update_persisted": False,
            "persisted_lifecycle_state": "Not Available",
            "persisted_selected_validation_task": "Not Available",
            "boot_recovery_route": "Not Available",
            "execution_state": "Not Available",
            "execution_authority": "NONE",
        }

    def initialize(self) -> dict[str, Any]:
        for path in (
            self.pending_path,
            self.active_path,
            self.resolved_path,
            self.superseded_path,
            self.invalid_path,
            self.archive_path,
        ):
            path.mkdir(parents=True, exist_ok=True)
        self._quarantine_temporary_files()
        self.last_report = {
            **self._empty_report(),
            "evidence_plan_store_state": "READY",
            "evidence_plan_storage_state": "DIRECTORIES_READY",
            "pending_evidence_plan_count": len(self._plan_files(self.pending_path)),
        }
        return dict(self.last_report)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _term(self, value: Any) -> str:
        text = str(value or "").strip()
        return text if text else "Not Available"

    def _slug(self, value: Any) -> str:
        return (
            str(value or "unknown")
            .strip()
            .replace(" ", "_")
            .replace(":", "_")
            .replace("/", "_")
            .replace("\\", "_")
        )

    def _fingerprint_fields(self, plan: dict[str, Any]) -> dict[str, Any]:
        return {
            "required_evidence": plan.get("required_evidence"),
            "required_validation_task": plan.get("required_validation_task"),
            "tie_break_strategy": plan.get("tie_break_strategy"),
            "target_candidate": plan.get("target_candidate"),
            "target_operation": plan.get("target_operation"),
            "source_task_id": plan.get("source_task_id"),
            "governed_reentry_action": plan.get("governed_reentry_action"),
        }

    def fingerprint_for(self, plan: dict[str, Any]) -> str:
        normalized = self._fingerprint_fields(plan)
        payload = json.dumps(normalized, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _plan_id(self, plan: dict[str, Any], fingerprint: str) -> str:
        source_run = self._slug(plan.get("source_run_id"))
        candidate = self._slug(
            plan.get("target_candidate") or plan.get("source_task_id")
        )
        digest = hashlib.sha1(
            f"{source_run}:{candidate}:{fingerprint}".encode("utf-8")
        ).hexdigest()[:10]
        return f"evidence_plan_{source_run}_{digest}"

    def normalize_plan(self, raw_plan: dict[str, Any]) -> dict[str, Any]:
        raw_plan = raw_plan if isinstance(raw_plan, dict) else {}
        now = self._now()
        plan = {
            "schema_version": self.SCHEMA_VERSION,
            "created_at": raw_plan.get("created_at") or now,
            "updated_at": now,
            "source_run_id": self._term(raw_plan.get("source_run_id")),
            "source_task_id": self._term(raw_plan.get("source_task_id")),
            "source_candidate_id": self._term(
                raw_plan.get("source_candidate_id")
                or raw_plan.get("target_candidate")
                or raw_plan.get("evidence_acquisition_target_candidate")
            ),
            "source_operation": self._term(
                raw_plan.get("source_operation")
                or raw_plan.get("target_operation")
                or raw_plan.get("evidence_acquisition_target_operation")
            ),
            "source_stage": "evidence_acquisition",
            "evidence_acquisition_state": self._term(
                raw_plan.get("evidence_acquisition_state")
            ),
            "evidence_acquisition_trigger": self._term(
                raw_plan.get("evidence_acquisition_trigger")
            ),
            "required_evidence_category": self._term(
                raw_plan.get("required_evidence_category")
                or raw_plan.get("evidence_acquisition_required_category")
            ),
            "required_evidence": self._term(
                raw_plan.get("required_evidence")
                or raw_plan.get("evidence_acquisition_required_evidence")
            ),
            "required_validation_task": self._term(
                raw_plan.get("required_validation_task")
                or raw_plan.get("evidence_acquisition_validation_task")
            ),
            "tie_break_strategy": self._term(
                raw_plan.get("tie_break_strategy")
                or raw_plan.get("evidence_acquisition_tie_break_strategy")
            ),
            "expected_tie_break_impact": self._term(
                raw_plan.get("expected_tie_break_impact")
                or raw_plan.get("evidence_acquisition_expected_tie_break_impact")
            ),
            "target_candidate": self._term(
                raw_plan.get("target_candidate")
                or raw_plan.get("evidence_acquisition_target_candidate")
            ),
            "target_operation": self._term(
                raw_plan.get("target_operation")
                or raw_plan.get("evidence_acquisition_target_operation")
            ),
            "governed_reentry_action": self._term(
                raw_plan.get("governed_reentry_action")
                or raw_plan.get("evidence_acquisition_governed_reentry_action")
            ),
            "authority": {
                "truth": "NONE",
                "trust": "NONE",
                "graduation": "NONE",
                "execution": "NONE",
            },
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "execution_authority": "NONE",
            "constitutional_boundary": self.BOUNDARY,
            "authority_boundary": self.AUTHORITY_BOUNDARY,
            "lifecycle_state": "PENDING_NEXT_RUN",
            "consumption_state": "NOT_CONSUMED",
            "delivery_attempt_count": int(
                raw_plan.get("delivery_attempt_count", 0) or 0
            ),
            "consumption_attempt_count": int(
                raw_plan.get("consumption_attempt_count", 0) or 0
            ),
            "observation_count": int(raw_plan.get("observation_count", 0) or 0),
            "eligible_from_run": "NEXT_RUNTIME",
            "expires_after_runs": raw_plan.get("expires_after_runs"),
            "supersedes_plan_id": raw_plan.get("supersedes_plan_id"),
            "priority": self._priority(raw_plan),
            "history": list(raw_plan.get("history") or []),
        }
        fingerprint = self.fingerprint_for(plan)
        plan["plan_fingerprint"] = fingerprint
        plan["plan_id"] = raw_plan.get("plan_id") or self._plan_id(plan, fingerprint)
        try:
            plan.update(claim_identity_for_evidence_plan(plan))
            plan["claim_evidence_binding_state"] = "CLAIM_IDENTIFIED_NOT_EVIDENCE_BOUND"
        except ClaimIdentityError as exc:
            plan["claim_evidence_binding_state"] = "CLAIM_SUBJECT_NOT_DERIVABLE"
            plan["claim_identity_failure_reason"] = str(exc)
        plan["history"].append({
            "timestamp": now,
            "state": "NORMALIZED",
            "event": "plan_normalized",
        })
        return plan

    def _priority(self, plan: dict[str, Any]) -> int:
        impact = str(
            plan.get("expected_tie_break_impact")
            or plan.get("evidence_acquisition_expected_tie_break_impact")
            or ""
        ).upper()
        category = str(
            plan.get("required_evidence_category")
            or plan.get("evidence_acquisition_required_category")
            or ""
        ).upper()
        score = 10
        if impact == "HIGH":
            score += 40
        elif impact == "MEDIUM":
            score += 20
        if "CROSS_SOURCE" in category:
            score += 15
        if "GOVERNED" in category:
            score += 10
        return score

    def validate_plan(self, plan: dict[str, Any]) -> list[str]:
        failures = []
        if plan.get("schema_version") != self.SCHEMA_VERSION:
            failures.append("unsupported_schema_version")
        missing = [
            field for field in sorted(self.REQUIRED_FIELDS)
            if plan.get(field) in (None, "", "Not Available")
        ]
        if missing:
            failures.append("missing_required_fields:" + ",".join(missing))
        for field in (
            "truth_authority",
            "trust_authority",
            "graduation_authority",
            "execution_authority",
        ):
            if plan.get(field) != "NONE":
                failures.append(f"invalid_authority_field:{field}")
        if plan.get("constitutional_boundary") != self.BOUNDARY:
            failures.append("invalid_constitutional_boundary")
        return failures

    def _plan_files(self, directory: Path) -> list[Path]:
        if not directory.exists():
            return []
        return sorted(
            path for path in directory.glob("*.json")
            if not path.name.endswith(".tmp")
        )

    def _read_plan(self, path: Path) -> tuple[dict[str, Any] | None, str | None]:
        try:
            plan = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
            return None, str(error)
        if not isinstance(plan, dict):
            return None, "plan_not_mapping"
        return plan, None

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

    def _move(self, source: Path, target_dir: Path, reason: str) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        if target.exists():
            target = target_dir / f"{source.stem}_{hashlib.sha1(reason.encode()).hexdigest()[:8]}{source.suffix}"
        try:
            source.replace(target)
        except OSError:
            shutil.move(str(source), str(target))
        return target

    def _quarantine_temporary_files(self) -> None:
        if not self.root_path.exists():
            return
        self.invalid_path.mkdir(parents=True, exist_ok=True)
        for path in self.root_path.rglob("*.tmp"):
            if path.is_file():
                self._move(path, self.invalid_path, "stale_temporary_file")

    def _find_equivalent_unresolved(
        self,
        fingerprint: str,
    ) -> tuple[dict[str, Any] | None, Path | None]:
        for directory in (self.pending_path, self.active_path):
            for path in self._plan_files(directory):
                plan, error = self._read_plan(path)
                if error or not plan:
                    continue
                if plan.get("plan_fingerprint") == fingerprint:
                    return plan, path
        return None, None

    def persist_plan(
        self,
        raw_plan: dict[str, Any],
        *,
        source_run_id: str | None = None,
        source_task_id: str | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        enriched = dict(raw_plan or {})
        if source_run_id and not enriched.get("source_run_id"):
            enriched["source_run_id"] = source_run_id
        if source_task_id and not enriched.get("source_task_id"):
            enriched["source_task_id"] = source_task_id
        plan = self.normalize_plan(enriched)
        failures = self.validate_plan(plan)
        report = {
            **self._empty_report(),
            "evidence_plan_store_state": "READY",
            "evidence_plan_persistence_attempted": True,
            "evidence_plan_id": plan.get("plan_id"),
            "evidence_plan_fingerprint": plan.get("plan_fingerprint"),
            "evidence_plan_lifecycle_state": plan.get("lifecycle_state"),
            "evidence_plan_storage_path": str(
                self.pending_path / f"{plan['plan_id']}.json"
            ),
            "plan_schema_version": plan.get("schema_version"),
            "plan_constitutional_boundary": plan.get("constitutional_boundary"),
            "current_run_consumption_expected": False,
            "next_run_consumption_required": True,
            "current_run_consumption_failure": False,
        }
        if failures:
            plan["lifecycle_state"] = "INVALID"
            plan["invalid_reasons"] = failures
            invalid_path = self.invalid_path / f"{plan['plan_id']}.json"
            self._atomic_write(invalid_path, plan)
            self.last_report = {
                **report,
                "evidence_plan_storage_state": "PLAN_REJECTED_INVALID",
                "plan_persistence_failure_reason": ";".join(failures),
                "evidence_plan_lifecycle_state": "INVALID",
            }
            return dict(self.last_report)
        existing, path = self._find_equivalent_unresolved(
            plan["plan_fingerprint"]
        )
        if existing:
            existing["updated_at"] = self._now()
            existing["observation_count"] = int(
                existing.get("observation_count", 0) or 0
            ) + 1
            existing.setdefault("history", []).append({
                "timestamp": existing["updated_at"],
                "state": existing.get("lifecycle_state"),
                "event": "equivalent_plan_observed",
                "source_run_id": plan.get("source_run_id"),
            })
            if path:
                self._atomic_write(path, existing)
            self.last_report = {
                **report,
                "evidence_plan_persisted": False,
                "evidence_plan_id": existing.get("plan_id"),
                "evidence_plan_fingerprint": existing.get("plan_fingerprint"),
                "evidence_plan_lifecycle_state": existing.get("lifecycle_state"),
                "evidence_plan_storage_state": (
                    "EQUIVALENT_PENDING_PLAN_REUSED"
                ),
                "plan_creation_result": "REUSED_EXISTING_PLAN",
                "evidence_plan_storage_path": str(path),
                "equivalent_pending_plan_found": True,
                "duplicate_persistence_prevented": True,
                "pending_evidence_plan_count": len(
                    self._plan_files(self.pending_path)
                ),
            }
            return dict(self.last_report)
        now = self._now()
        plan["updated_at"] = now
        plan["history"].append({
            "timestamp": now,
            "state": "PERSISTED",
            "event": "plan_persisted_atomically",
        })
        path = self.pending_path / f"{plan['plan_id']}.json"
        self._atomic_write(path, plan)
        self.last_report = {
            **report,
            "evidence_plan_persisted": True,
            "evidence_plan_lifecycle_state": "PENDING_NEXT_RUN",
            "evidence_plan_storage_state": "NEW_PLAN_PERSISTED",
            "plan_creation_result": "NEW_PLAN_PERSISTED",
            "pending_evidence_plan_count": len(self._plan_files(self.pending_path)),
        }
        return dict(self.last_report)

    def load_pending_plans(self) -> dict[str, Any]:
        self.initialize()
        valid = []
        quarantined = []
        seen: dict[str, Path] = {}
        for path in self._plan_files(self.pending_path):
            plan, error = self._read_plan(path)
            if error or not plan:
                quarantined.append({
                    "path": str(path),
                    "reason": error or "plan_unreadable",
                })
                self._move(path, self.invalid_path, "corrupted_pending_plan")
                continue
            failures = self.validate_plan(plan)
            fingerprint = plan.get("plan_fingerprint")
            if failures:
                plan["lifecycle_state"] = "INVALID"
                plan["invalid_reasons"] = failures
                self._atomic_write(path, plan)
                quarantined.append({"path": str(path), "reason": failures})
                self._move(path, self.invalid_path, "invalid_pending_plan")
                continue
            if fingerprint in seen:
                plan["lifecycle_state"] = "SUPERSEDED"
                plan["supersedes_plan_id"] = None
                self._atomic_write(path, plan)
                self._move(path, self.superseded_path, "duplicate_fingerprint")
                continue
            seen[fingerprint] = path
            if plan["plan_id"] in self._loaded_this_run:
                continue
            if plan.get("lifecycle_state") in {
                "WAITING_EXECUTION",
                "SCHEDULING_PREPARED",
            }:
                plan["boot_recovery_route"] = (
                    "SCHEDULING_PREPARED_TO_SCHEDULING_RECOVERY"
                    if plan.get("lifecycle_state") == "SCHEDULING_PREPARED"
                    else "WAITING_EXECUTION_TO_VALIDATION_SCHEDULER"
                )
                plan["execution_state"] = (
                    plan.get("execution_state") or "NOT_SCHEDULED"
                )
                plan["execution_authority"] = "NONE"
                plan["updated_at"] = self._now()
                plan.setdefault("history", []).append({
                    "timestamp": plan["updated_at"],
                    "state": "WAITING_EXECUTION",
                    "event": "waiting_execution_plan_restored_at_boot",
                })
                self._atomic_write(path, plan)
                valid.append(plan)
                self._loaded_this_run.add(plan["plan_id"])
                continue
            if plan.get("lifecycle_state") == "SCHEDULED":
                plan["boot_recovery_route"] = (
                    "SCHEDULED_TO_VALIDATION_EXECUTION_PIPELINE"
                )
                plan["execution_state"] = plan.get("execution_state") or "NOT_STARTED"
                plan["execution_invoked"] = bool(plan.get("execution_invoked", False))
                plan["execution_authority"] = "NONE"
                plan["updated_at"] = self._now()
                plan.setdefault("history", []).append({
                    "timestamp": plan["updated_at"],
                    "state": "SCHEDULED",
                    "event": "scheduled_plan_restored_at_boot",
                })
                self._atomic_write(path, plan)
                valid.append(plan)
                self._loaded_this_run.add(plan["plan_id"])
                continue
            if plan.get("lifecycle_state") == "RAW_RESULT_CAPTURED":
                plan["boot_recovery_route"] = (
                    "RAW_RESULT_CAPTURED_TO_VALIDATION_EVIDENCE_EVALUATOR"
                )
                plan["execution_state"] = "RAW_RESULT_CAPTURED"
                plan["evidence_state"] = "NOT_EVALUATED"
                plan["execution_authority"] = "NONE"
                plan["updated_at"] = self._now()
                plan.setdefault("history", []).append({
                    "timestamp": plan["updated_at"],
                    "state": "RAW_RESULT_CAPTURED",
                    "event": "raw_result_captured_plan_restored_at_boot",
                })
                self._atomic_write(path, plan)
                valid.append(plan)
                self._loaded_this_run.add(plan["plan_id"])
                continue
            if plan.get("lifecycle_state") in {
                "EVIDENCE_ACCEPTED",
                "EVIDENCE_INSUFFICIENT",
                "EVIDENCE_REJECTED",
                "ARENA_REDELIBERATION_COMPLETED",
                "RATIFIED",
                "REJECTED",
                "DEFERRED",
            }:
                route = {
                    "EVIDENCE_ACCEPTED": (
                        "EVIDENCE_ACCEPTED_TO_ARENA_EVIDENCE_ADMISSION_GATE"
                    ),
                    "EVIDENCE_INSUFFICIENT": (
                        "EVIDENCE_INSUFFICIENT_TO_EVIDENCE_REMEDIATION_PLANNER"
                    ),
                    "EVIDENCE_REJECTED": (
                        "EVIDENCE_REJECTED_TO_EVIDENCE_REVIEW_OR_REPLAN"
                    ),
                    "ARENA_REDELIBERATION_COMPLETED": (
                        plan.get("boot_recovery_route")
                        or (
                            "DECISION_PROPOSAL_TO_ARENA_FORMAL_SELECTION_GATE"
                            if plan.get("redeliberation_outcome")
                            == "DECISION_PROPOSAL_AVAILABLE"
                            else "ARENA_REDELIBERATION_COMPLETED_TO_FUTURE_CONSUMER"
                        )
                    ),
                    "RATIFIED": (
                        "RATIFIED_TO_FUTURE_SELECTED_CANDIDATE_EXECUTION_ADMISSION_GATE"
                    ),
                    "REJECTED": "REJECTED_TO_ARENA_REVIEW_OR_REMEDIATION",
                    "DEFERRED": (
                        "DEFERRED_TO_FORMAL_SELECTION_RECOVERY_OR_CLARIFICATION"
                    ),
                }[plan.get("lifecycle_state")]
                plan["boot_recovery_route"] = route
                plan["evidence_state"] = plan.get("lifecycle_state")
                plan["execution_authority"] = "NONE"
                plan["candidate_execution_authority"] = "NONE"
                plan["truth_authority"] = "NONE"
                plan["trust_authority"] = "NONE"
                plan["graduation_authority"] = "NONE"
                plan["updated_at"] = self._now()
                plan.setdefault("history", []).append({
                    "timestamp": plan["updated_at"],
                    "state": plan.get("lifecycle_state"),
                    "event": "terminal_evidence_plan_restored_at_boot",
                })
                self._atomic_write(path, plan)
                valid.append(plan)
                self._loaded_this_run.add(plan["plan_id"])
                continue
            plan["lifecycle_state"] = "LOADED_AT_BOOT"
            plan["updated_at"] = self._now()
            plan.setdefault("history", []).append({
                "timestamp": plan["updated_at"],
                "state": "LOADED_AT_BOOT",
                "event": "plan_loaded_at_boot",
            })
            self._atomic_write(path, plan)
            valid.append(plan)
            self._loaded_this_run.add(plan["plan_id"])
        valid.sort(key=lambda item: (-int(item.get("priority", 0)), item["plan_id"]))
        consumption_ready = [
            plan for plan in valid
            if plan.get("lifecycle_state") not in {
                "WAITING_EXECUTION",
                "SCHEDULING_PREPARED",
                "SCHEDULED",
                "RAW_RESULT_CAPTURED",
                "EVIDENCE_ACCEPTED",
                "EVIDENCE_INSUFFICIENT",
                "EVIDENCE_REJECTED",
                "ARENA_REDELIBERATION_COMPLETED",
                "RATIFIED",
                "REJECTED",
                "DEFERRED",
            }
        ]
        waiting_execution = [
            plan for plan in valid
            if plan.get("lifecycle_state") in {
                "WAITING_EXECUTION",
                "SCHEDULING_PREPARED",
            }
        ]
        scheduled = [
            plan for plan in valid
            if plan.get("lifecycle_state") == "SCHEDULED"
        ]
        raw_result_captured = [
            plan for plan in valid
            if plan.get("lifecycle_state") == "RAW_RESULT_CAPTURED"
        ]
        terminal_evidence = [
            plan for plan in valid
            if plan.get("lifecycle_state") in {
                "EVIDENCE_ACCEPTED",
                "EVIDENCE_INSUFFICIENT",
                "EVIDENCE_REJECTED",
                "ARENA_REDELIBERATION_COMPLETED",
                "RATIFIED",
                "REJECTED",
                "DEFERRED",
            }
        ]
        highest = (
            consumption_ready[0]
            if consumption_ready else waiting_execution[0]
            if waiting_execution else scheduled[0]
            if scheduled else raw_result_captured[0]
            if raw_result_captured else terminal_evidence[0]
            if terminal_evidence else {}
        )
        self.last_report = {
            **self._empty_report(),
            "evidence_plan_store_state": "READY",
            "evidence_plan_boot_load_state": (
                "PENDING_PLANS_LOADED" if valid else "NO_PENDING_PLANS"
            ),
            "pending_evidence_plan_count": len(consumption_ready),
            "evidence_plans_loaded_at_boot": len(valid),
            "evidence_plan_storage_state": "BOOT_LOAD_COMPLETE",
            "evidence_plan_storage_path": str(self.root_path),
            "quarantined_plan_count": len(quarantined),
            "quarantined_plans": quarantined,
            "waiting_execution_plan_count": len(waiting_execution),
            "scheduled_evidence_plan_count": len(scheduled),
            "raw_result_captured_plan_count": len(raw_result_captured),
            "terminal_evidence_plan_count": len(terminal_evidence),
            "boot_recovery_route": (
                "WAITING_EXECUTION_TO_VALIDATION_SCHEDULER"
                if waiting_execution and not consumption_ready
                else "SCHEDULED_TO_VALIDATION_EXECUTION_PIPELINE"
                if scheduled and not waiting_execution and not consumption_ready
                else "RAW_RESULT_CAPTURED_TO_VALIDATION_EVIDENCE_EVALUATOR"
                if raw_result_captured
                and not scheduled
                and not waiting_execution
                and not consumption_ready
                else terminal_evidence[0].get("boot_recovery_route")
                if terminal_evidence
                and not raw_result_captured
                and not scheduled
                and not waiting_execution
                and not consumption_ready
                else "CONSUMPTION_PENDING_TO_TRAINING_ASSISTANT"
                if consumption_ready
                else "NO_PENDING_PLAN"
            ),
            "evidence_plan_lifecycle_state": (
                "WAITING_EXECUTION"
                if waiting_execution and not consumption_ready
                else "SCHEDULED"
                if scheduled and not waiting_execution and not consumption_ready
                else "RAW_RESULT_CAPTURED"
                if raw_result_captured
                and not scheduled
                and not waiting_execution
                and not consumption_ready
                else terminal_evidence[0].get("lifecycle_state")
                if terminal_evidence
                and not raw_result_captured
                and not scheduled
                and not waiting_execution
                and not consumption_ready
                else "LOADED_AT_BOOT"
                if consumption_ready
                else "Not Available"
            ),
            "persisted_selected_validation_task": (
                waiting_execution[0].get("selected_validation_task_id")
                if waiting_execution else scheduled[0].get(
                    "selected_validation_task_id"
                )
                if scheduled else raw_result_captured[0].get(
                    "selected_validation_task_id"
                )
                if raw_result_captured else terminal_evidence[0].get(
                    "selected_validation_task_id"
                )
                if terminal_evidence else "Not Available"
            ),
            "execution_state": (
                waiting_execution[0].get("execution_state", "NOT_SCHEDULED")
                if waiting_execution else scheduled[0].get(
                    "execution_state",
                    "NOT_STARTED",
                )
                if scheduled else raw_result_captured[0].get(
                    "execution_state",
                    "RAW_RESULT_CAPTURED",
                )
                if raw_result_captured else terminal_evidence[0].get(
                    "execution_state",
                    "RAW_RESULT_CAPTURED",
                )
                if terminal_evidence else "Not Available"
            ),
            "execution_authority": "NONE",
            "schedule_id": (
                scheduled[0].get("schedule_id")
                if scheduled else raw_result_captured[0].get("schedule_id")
                if raw_result_captured else "Not Available"
            ),
            "raw_result_id": (
                raw_result_captured[0].get("raw_result_id")
                if raw_result_captured else "Not Available"
            ),
            "evidence_state": (
                raw_result_captured[0].get("evidence_state", "NOT_EVALUATED")
                if raw_result_captured else terminal_evidence[0].get(
                    "evidence_state",
                    terminal_evidence[0].get("lifecycle_state"),
                )
                if terminal_evidence else "Not Available"
            ),
        }
        return {
            **dict(self.last_report),
            "pending_evidence_acquisition_plans": consumption_ready,
            "waiting_execution_evidence_plans": waiting_execution,
            "scheduled_evidence_plans": scheduled,
            "raw_result_captured_evidence_plans": raw_result_captured,
            "terminal_evidence_plans": terminal_evidence,
            "highest_priority_pending_evidence_plan": highest,
        }

    def get_pending_plans(self) -> list[dict[str, Any]]:
        report = self.load_pending_plans()
        return list(report.get("pending_evidence_acquisition_plans") or [])

    def deliver_plan_to_training_assistant(self, plan_id: str) -> dict[str, Any]:
        self.initialize()
        for path in self._plan_files(self.pending_path):
            plan, error = self._read_plan(path)
            if error or not plan or plan.get("plan_id") != plan_id:
                continue
            plan["delivery_attempt_count"] = int(
                plan.get("delivery_attempt_count", 0) or 0
            ) + 1
            plan["lifecycle_state"] = "DELIVERED_TO_TRAINING_ASSISTANT"
            plan["consumption_state"] = "DELIVERED_NOT_CONSUMED"
            plan["updated_at"] = self._now()
            plan.setdefault("history", []).append({
                "timestamp": plan["updated_at"],
                "state": plan["lifecycle_state"],
                "event": "plan_delivered_to_training_assistant",
            })
            self._atomic_write(path, plan)
            return {
                **self._empty_report(),
                "evidence_plan_store_state": "READY",
                "evidence_plan_boot_load_state": "PENDING_PLAN_DELIVERED",
                "evidence_plan_id": plan_id,
                "evidence_plan_fingerprint": plan.get("plan_fingerprint"),
                "evidence_plan_lifecycle_state": plan["lifecycle_state"],
                "evidence_plan_storage_state": (
                    "DELIVERED_TO_TRAINING_ASSISTANT"
                ),
                "evidence_plan_storage_path": str(path),
                "evidence_plans_delivered_to_training_assistant": 1,
                "training_assistant_plan_available": True,
                "current_run_consumption_expected": True,
                "next_run_consumption_required": False,
            }
        return {
            **self._empty_report(),
            "evidence_plan_store_state": "READY",
            "evidence_plan_storage_state": "PLAN_NOT_FOUND",
            "plan_persistence_failure_reason": "plan_not_found",
        }

    def mark_consumption_pending(self, plan_id: str) -> dict[str, Any]:
        delivery = self.deliver_plan_to_training_assistant(plan_id)
        if delivery.get("evidence_plan_storage_state") != (
            "DELIVERED_TO_TRAINING_ASSISTANT"
        ):
            return delivery
        path = Path(delivery["evidence_plan_storage_path"])
        plan, error = self._read_plan(path)
        if error or not plan:
            return delivery
        plan["lifecycle_state"] = "CONSUMPTION_PENDING"
        plan["consumption_state"] = "CONSUMPTION_PENDING"
        plan["updated_at"] = self._now()
        plan.setdefault("history", []).append({
            "timestamp": plan["updated_at"],
            "state": "CONSUMPTION_PENDING",
            "event": "training_assistant_consumption_pending",
        })
        self._atomic_write(path, plan)
        self.last_report = {
            **delivery,
            "evidence_plan_lifecycle_state": "CONSUMPTION_PENDING",
            "evidence_plan_storage_state": "CONSUMPTION_PENDING",
        }
        return dict(self.last_report)

    def persist_selection_from_consumption_report(
        self,
        consumption_report: dict[str, Any] | None,
    ) -> dict[str, Any]:
        report = {
            **self._empty_report(),
            "evidence_plan_store_state": "READY",
            "lifecycle_update_attempted": False,
            "lifecycle_update_persisted": False,
            "persisted_lifecycle_state": "Not Available",
            "persisted_selected_validation_task": "Not Available",
            "boot_recovery_route": "Not Available",
            "execution_state": "NOT_SCHEDULED",
            "execution_authority": "NONE",
        }
        consumption_report = (
            consumption_report if isinstance(consumption_report, dict) else {}
        )
        if consumption_report.get("selection_state") != "WAITING_EXECUTION":
            return {
                **report,
                "evidence_plan_storage_state": "LIFECYCLE_UPDATE_NOT_APPLICABLE",
                "plan_persistence_failure_reason": "selection_state_not_waiting_execution",
            }
        plan_id = self._term(consumption_report.get("current_plan_id"))
        if plan_id == "Not Available":
            return {
                **report,
                "lifecycle_update_attempted": True,
                "evidence_plan_storage_state": "PLAN_SELECTION_UPDATE_FAILED",
                "plan_persistence_failure_reason": "missing_plan_id",
            }
        selected_task = self._term(
            consumption_report.get("selected_validation_task")
        )
        if selected_task == "Not Available":
            return {
                **report,
                "lifecycle_update_attempted": True,
                "evidence_plan_id": plan_id,
                "evidence_plan_storage_state": "PLAN_SELECTION_UPDATE_FAILED",
                "plan_persistence_failure_reason": "missing_selected_validation_task",
            }

        path = None
        plan = None
        for directory in (self.pending_path, self.active_path):
            candidate = directory / f"{plan_id}.json"
            loaded, error = self._read_plan(candidate)
            if error or not loaded:
                continue
            plan = loaded
            path = candidate
            break
        if not plan or not path:
            return {
                **report,
                "lifecycle_update_attempted": True,
                "evidence_plan_id": plan_id,
                "evidence_plan_storage_state": "PLAN_SELECTION_UPDATE_FAILED",
                "plan_persistence_failure_reason": "plan_not_found",
            }

        metadata = consumption_report.get("selected_validation_task_metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        now = self._now()
        previous_state = plan.get("lifecycle_state")
        update_payload = {
            "updated_at": now,
            "lifecycle_state": "WAITING_EXECUTION",
            "consumption_state": "MATCHING_COMPLETED",
            "selected_validation_task_id": selected_task,
            "selected_curriculum_id": self._term(
                metadata.get("curriculum_id")
                or consumption_report.get("best_matching_curriculum")
            ),
            "selected_curriculum": self._term(
                consumption_report.get("best_matching_curriculum")
            ),
            "matching_score": consumption_report.get("matching_score", 0.0),
            "matching_explanation": self._term(
                consumption_report.get("matching_explanation")
            ),
            "selection_authority": "TRAINING_ASSISTANT",
            "selection_timestamp": now,
            "required_evidence": self._term(
                consumption_report.get("current_required_evidence")
                or plan.get("required_evidence")
            ),
            "required_evidence_category": self._term(
                plan.get("required_evidence_category")
            ),
            "target_candidate": self._term(plan.get("target_candidate")),
            "target_operation": self._term(
                consumption_report.get("current_target_operation")
                or plan.get("target_operation")
            ),
            "tie_break_strategy": self._term(
                consumption_report.get("current_tie_break_strategy")
                or plan.get("tie_break_strategy")
            ),
            "execution_state": "NOT_SCHEDULED",
            "execution_authority": "NONE",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "boot_recovery_route": "WAITING_EXECUTION_TO_VALIDATION_SCHEDULER",
        }
        updated = {**plan, **update_payload}
        updated.setdefault("history", []).append({
            "timestamp": now,
            "state": "WAITING_EXECUTION",
            "event": "training_assistant_selected_validation_task",
            "previous_state": previous_state,
            "selected_validation_task_id": selected_task,
        })
        try:
            self._atomic_write(path, updated)
        except (OSError, TypeError, ValueError) as error:
            return {
                **report,
                "lifecycle_update_attempted": True,
                "evidence_plan_id": plan_id,
                "evidence_plan_fingerprint": plan.get(
                    "plan_fingerprint",
                    "Not Available",
                ),
                "evidence_plan_storage_state": "PLAN_SELECTION_UPDATE_FAILED",
                "plan_persistence_failure_reason": str(error),
                "evidence_plan_storage_path": str(path),
            }

        self.last_report = {
            **report,
            "lifecycle_update_attempted": True,
            "lifecycle_update_persisted": True,
            "evidence_plan_id": plan_id,
            "evidence_plan_fingerprint": updated.get("plan_fingerprint"),
            "evidence_plan_lifecycle_state": "WAITING_EXECUTION",
            "evidence_plan_storage_state": "LIFECYCLE_UPDATE_PERSISTED",
            "evidence_plan_storage_path": str(path),
            "persisted_lifecycle_state": "WAITING_EXECUTION",
            "persisted_selected_validation_task": selected_task,
            "boot_recovery_route": "WAITING_EXECUTION_TO_VALIDATION_SCHEDULER",
            "execution_state": "NOT_SCHEDULED",
            "execution_authority": "NONE",
            "plan_persistence_failure_reason": "none",
        }
        return dict(self.last_report)

    def handoff_payload(self, plan: dict[str, Any]) -> dict[str, Any]:
        return {
            "plan_id": plan.get("plan_id"),
            "required_evidence_category": plan.get("required_evidence_category"),
            "required_evidence": plan.get("required_evidence"),
            "required_validation_task": plan.get("required_validation_task"),
            "tie_break_strategy": plan.get("tie_break_strategy"),
            "target_candidate": plan.get("target_candidate"),
            "target_operation": plan.get("target_operation"),
            "expected_tie_break_impact": plan.get("expected_tie_break_impact"),
            "governed_reentry_action": plan.get("governed_reentry_action"),
            "authority": {
                "truth": "NONE",
                "trust": "NONE",
                "graduation": "NONE",
                "execution": "NONE",
            },
        }

    def deliver_pending_plans_to_training_assistant(
        self,
        plans: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        source_plans = plans if plans is not None else self.get_pending_plans()
        payloads: list[dict[str, Any]] = []
        reports: list[dict[str, Any]] = []
        for plan in source_plans:
            if not isinstance(plan, dict) or not plan.get("plan_id"):
                continue
            report = self.mark_consumption_pending(str(plan["plan_id"]))
            reports.append(report)
            if report.get("training_assistant_plan_available") is True:
                payloads.append(self.handoff_payload(plan))
        lifecycle_state = (
            reports[-1].get("evidence_plan_lifecycle_state")
            if reports else "Not Available"
        )
        self.last_report = {
            **self.last_report,
            "evidence_plan_store_state": "READY",
            "evidence_plan_boot_load_state": (
                "PENDING_PLAN_DELIVERED"
                if payloads else self.last_report.get("evidence_plan_boot_load_state")
            ),
            "evidence_plan_lifecycle_state": lifecycle_state,
            "evidence_plan_storage_state": (
                "CONSUMPTION_PENDING" if payloads else "NO_PENDING_PLANS"
            ),
            "evidence_plans_delivered_to_training_assistant": len(payloads),
            "training_assistant_plan_available": bool(payloads),
            "current_run_consumption_expected": bool(payloads),
            "next_run_consumption_required": False,
            "pending_evidence_plan_count": len(payloads),
            "inbound_evidence_plan_state": (
                "PLAN_AVAILABLE_FOR_CURRENT_RUN_CONSUMPTION"
                if payloads else "NO_INBOUND_PENDING_PLAN"
            ),
        }
        return {
            **dict(self.last_report),
            "pending_evidence_acquisition_plans": payloads,
            "delivery_reports": reports,
            "highest_priority_pending_evidence_plan": (
                payloads[0] if payloads else {}
            ),
        }

    def plan_from_candidate_arena_summary(
        self,
        summary: dict[str, Any],
        *,
        source_run_id: str | None = None,
        source_task_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(summary, dict):
            return None
        if summary.get("evidence_acquisition_state") != (
            "EVIDENCE_ACQUISITION_PLAN_READY"
        ):
            return None
        return {
            "source_run_id": source_run_id or summary.get("source_run_id"),
            "source_task_id": (
                source_task_id
                or summary.get("source_task_id")
                or summary.get("validation_probe_candidate_id")
                or summary.get("arena_winner")
            ),
            "source_candidate_id": (
                summary.get("evidence_acquisition_target_candidate")
                or summary.get("validation_probe_candidate_id")
                or summary.get("arena_winner")
            ),
            "source_operation": (
                summary.get("evidence_acquisition_target_operation")
                or summary.get("validation_probe_operation")
                or summary.get("winner_operation")
            ),
            "evidence_acquisition_state": (
                summary.get("evidence_acquisition_state")
            ),
            "evidence_acquisition_trigger": (
                summary.get("evidence_acquisition_trigger")
            ),
            "required_evidence_category": (
                summary.get("evidence_acquisition_required_category")
            ),
            "required_evidence": (
                summary.get("evidence_acquisition_required_evidence")
            ),
            "required_validation_task": (
                summary.get("evidence_acquisition_validation_task")
            ),
            "tie_break_strategy": (
                summary.get("evidence_acquisition_tie_break_strategy")
            ),
            "expected_tie_break_impact": (
                summary.get("evidence_acquisition_expected_tie_break_impact")
            ),
            "target_candidate": (
                summary.get("evidence_acquisition_target_candidate")
                or summary.get("validation_probe_candidate_id")
            ),
            "target_operation": (
                summary.get("evidence_acquisition_target_operation")
                or summary.get("validation_probe_operation")
            ),
            "governed_reentry_action": (
                summary.get("evidence_acquisition_governed_reentry_action")
            ),
        }
