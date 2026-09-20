from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore


class TrainingOutcomeValidationBoundary:
    """Authority-free bridge from training experience to validation request."""

    BOUNDARY = (
        "TRAINING_EXPERIENCE_MAY_REQUEST_GOVERNED_VALIDATION_BUT_IS_NOT_EVIDENCE"
    )
    AUTHORITY = "NONE"
    BEHAVIORAL_AUTHORITY = "NONE"
    ELIGIBLE_PURPOSES = {
        "CAPABILITY_EVIDENCE_ACQUISITION",
        "REMEDIATION",
        "VALIDATION",
        "TRAINING",
        "EXPLORATION",
    }

    def __init__(
        self,
        root_path: str | os.PathLike[str] = (
            "runtime/state/training_validation_requests"
        ),
        evidence_plan_store: EvidenceAcquisitionPlanStore | None = None,
    ) -> None:
        self.root_path = Path(root_path)
        self.candidates_path = self.root_path / "evidence_candidates"
        self.requests_path = self.root_path / "validation_requests"
        self.invalid_path = self.root_path / "invalid"
        self.evidence_plan_store = evidence_plan_store

    def assess_outcome(
        self,
        outcome: Mapping[str, Any] | None,
        *,
        evidence_need: Mapping[str, Any] | None = None,
        task_metadata: Mapping[str, Any] | None = None,
        selection_context: Mapping[str, Any] | None = None,
        persist: bool = True,
        route_to_plan: bool = False,
    ) -> dict[str, Any]:
        started = datetime.now(timezone.utc)
        self._initialize()
        experience = self.training_experience(
            outcome,
            task_metadata=task_metadata,
            selection_context=selection_context,
        )
        candidate = self.evidence_candidate(
            experience,
            evidence_need=evidence_need,
        )
        request = self.validation_request(candidate, evidence_need=evidence_need)
        persistence = self._persist_candidate_and_request(candidate, request) if persist else {}
        plan_report = {}
        if route_to_plan and request.get("request_admission_state") == "ADMITTED":
            plan_report = self.route_request_to_evidence_plan(request)
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        return {
            "system": "training_outcome_validation_boundary",
            "boundary": self.BOUNDARY,
            "authority": self.AUTHORITY,
            "behavioral_authority": self.BEHAVIORAL_AUTHORITY,
            "training_experience": experience,
            "evidence_candidate": candidate,
            "validation_request": request,
            "candidate_created": candidate.get("candidate_state")
            == "CANDIDATE_CREATED",
            "validation_request_created": request.get("request_state")
            in {"PENDING", "CONSUMED_TO_EVIDENCE_PLAN"},
            "evidence_plan_report": plan_report,
            "persistence_report": persistence,
            "performance": {
                "elapsed_seconds": round(elapsed, 6),
                "candidate_bytes": len(json.dumps(candidate, sort_keys=True)),
                "request_bytes": len(json.dumps(request, sort_keys=True)),
                "pending_request_count": len(self._json_files(self.requests_path)),
            },
            "direct_raw_evidence_created": False,
            "direct_accepted_evidence_created": False,
            "qualification_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "selector_authority": "NONE",
            "realized_yield_selector_consumption": False,
        }

    def training_experience(
        self,
        outcome: Mapping[str, Any] | None,
        *,
        task_metadata: Mapping[str, Any] | None = None,
        selection_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        outcome = dict(outcome or {})
        task_metadata = dict(task_metadata or {})
        selection_context = dict(selection_context or {})
        validation = outcome.get("validation")
        validation = validation if isinstance(validation, Mapping) else {}
        evaluation = outcome.get("evaluation")
        evaluation = evaluation if isinstance(evaluation, Mapping) else {}
        residual = (
            outcome.get("residual_analysis")
            or validation.get("residual_analysis")
            or evaluation.get("residual_analysis")
            or {}
        )
        if not isinstance(residual, Mapping):
            residual = {}
        task_id = self._first(
            outcome,
            "task_id",
            "task",
            "source_task_id",
            default=selection_context.get("task_id"),
        )
        run_id = self._first(outcome, "run_id", "source_run_id")
        execution_plan_id = self._first(outcome, "execution_plan_id")
        task_execution_id = self._first(
            outcome,
            "task_execution_id",
            "origin_task_execution_id",
        )
        if self._missing(task_execution_id) and not (
            self._missing(run_id) or self._missing(task_id)
        ):
            task_execution_id = self._id(
                "training_task_execution",
                {
                    "run_id": run_id,
                    "task_id": task_id,
                    "execution_plan_id": execution_plan_id,
                },
            )
        success_state = self._first(
            outcome,
            "success_state",
            default=validation.get("success_state"),
        )
        accuracy = self._first(outcome, "accuracy", default=validation.get("accuracy"))
        final_score = self._first(
            outcome,
            "final_score",
            default=validation.get("final_score"),
        )
        purpose = self._term(
            selection_context.get("selection_purpose")
            or selection_context.get("task_purpose")
            or outcome.get("selection_purpose")
            or "TRAINING"
        ).upper()
        return {
            "schema_version": "1.0",
            "experience_type": "TRAINING_TASK_OUTCOME",
            "source_run_id": self._term(run_id),
            "source_task_id": self._term(task_id),
            "source_task_execution_id": self._term(task_execution_id),
            "execution_plan_id": self._term(execution_plan_id),
            "success_state": self._term(success_state),
            "accuracy": accuracy,
            "final_score": final_score,
            "residual": dict(residual),
            "failure_classification": self._term(
                outcome.get("failure_classification")
                or residual.get("probable_root_cause")
            ),
            "task_metadata": task_metadata,
            "selection_purpose": purpose,
            "selection_context": selection_context,
            "authority": self.AUTHORITY,
            "behavioral_authority": self.BEHAVIORAL_AUTHORITY,
            "experience_is_evidence": False,
        }

    def evidence_candidate(
        self,
        experience: Mapping[str, Any],
        *,
        evidence_need: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        experience = dict(experience or {})
        evidence_need = dict(evidence_need or {})
        capability = self._capability_resolution(experience, evidence_need)
        claim = self._claim_resolution(evidence_need)
        eligibility = self._candidate_eligibility(experience, evidence_need, capability)
        fingerprint_payload = {
            "source_task_execution_id": experience.get("source_task_execution_id"),
            "source_run_id": experience.get("source_run_id"),
            "source_task_id": experience.get("source_task_id"),
            "capability_id": capability.get("capability_id"),
            "claim_id": claim.get("claim_id"),
            "required_evidence": evidence_need.get("required_evidence"),
            "required_validation_task": evidence_need.get("required_validation_task"),
            "success_state": experience.get("success_state"),
            "failure_classification": experience.get("failure_classification"),
        }
        fingerprint = self._fingerprint(fingerprint_payload)
        target_resolution_missing = (
            bool(evidence_need)
            and (
                capability["capability_resolution_state"].endswith("UNRESOLVED")
                or claim["claim_resolution_state"].endswith("UNRESOLVED")
            )
        )
        candidate_state = (
            "CANDIDATE_CREATED"
            if eligibility["candidate_eligible"]
            else "TARGET_RESOLUTION_REQUIRED"
            if target_resolution_missing
            else "NOT_VALIDATION_WORTHY"
        )
        return {
            "schema_version": "1.0",
            "evidence_candidate_id": f"evidence_candidate_{fingerprint[:12]}",
            "candidate_fingerprint": fingerprint,
            "source_task_execution_id": experience.get("source_task_execution_id"),
            "source_run_id": experience.get("source_run_id"),
            "source_task_id": experience.get("source_task_id"),
            "candidate_type": "TRAINING_OBSERVATION_FOR_VALIDATION_CONSIDERATION",
            "candidate_scope": "VALIDATION_REQUEST_PRECURSOR_ONLY",
            "observation_summary": {
                "success_state": experience.get("success_state"),
                "accuracy": experience.get("accuracy"),
                "final_score": experience.get("final_score"),
                "failure_classification": experience.get(
                    "failure_classification"
                ),
            },
            "candidate_capability_refs": capability.get("capability_refs", []),
            "capability_id": capability.get("capability_id"),
            "capability_resolution_state": capability[
                "capability_resolution_state"
            ],
            "candidate_claim_ref": claim.get("claim_id"),
            "claim_id": claim.get("claim_id"),
            "claim_subject": claim.get("claim_subject"),
            "claim_resolution_state": claim["claim_resolution_state"],
            "diagnostic_refs": self._diagnostic_refs(experience),
            "outcome_refs": {
                "source_task_execution_id": experience.get(
                    "source_task_execution_id"
                ),
                "source_task_id": experience.get("source_task_id"),
            },
            "proposal_reason": eligibility["proposal_reason"],
            "eligibility_state": eligibility["eligibility_state"],
            "candidate_state": candidate_state,
            "validation_request_eligible": eligibility["candidate_eligible"],
            "provenance": {
                "source": "TRAINING_TASK_OUTCOME",
                "source_run_id": experience.get("source_run_id"),
                "source_task_id": experience.get("source_task_id"),
                "source_task_execution_id": experience.get(
                    "source_task_execution_id"
                ),
            },
            "authority": self.AUTHORITY,
            "behavioral_authority": self.BEHAVIORAL_AUTHORITY,
            "raw_evidence_authority": "NONE",
            "accepted_evidence_authority": "NONE",
            "truth_authority": "NONE",
        }

    def validation_request(
        self,
        candidate: Mapping[str, Any],
        *,
        evidence_need: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        candidate = dict(candidate or {})
        evidence_need = dict(evidence_need or {})
        failures = []
        if candidate.get("candidate_state") != "CANDIDATE_CREATED":
            failures.append("candidate_not_validation_request_eligible")
        if self._missing(candidate.get("source_task_execution_id")):
            failures.append("missing_source_task_execution_id")
        if self._missing(candidate.get("capability_id")):
            failures.append("missing_canonical_capability_id")
        if evidence_need.get("claim_required", True) and self._missing(
            candidate.get("claim_id")
        ):
            failures.append("missing_claim_id")
        for field in (
            "required_evidence",
            "required_validation_task",
            "required_evidence_category",
            "target_candidate",
            "target_operation",
            "tie_break_strategy",
            "governed_reentry_action",
        ):
            if self._missing(evidence_need.get(field)):
                failures.append(f"missing_{field}")
        request_fingerprint = self._fingerprint({
            "candidate_fingerprint": candidate.get("candidate_fingerprint"),
            "capability_id": candidate.get("capability_id"),
            "claim_id": candidate.get("claim_id"),
            "required_evidence": evidence_need.get("required_evidence"),
            "required_validation_task": evidence_need.get(
                "required_validation_task"
            ),
            "target_candidate": evidence_need.get("target_candidate"),
            "target_operation": evidence_need.get("target_operation"),
        })
        existing = self._find_existing_request(request_fingerprint)
        request_state = "PENDING"
        admission = "ADMITTED"
        reason = "validation_request_contract_satisfied"
        if failures:
            request_state = "REJECTED"
            admission = "REJECTED"
            reason = ";".join(failures)
        elif existing:
            request_state = "PENDING"
            admission = "DEDUPLICATED"
            reason = "VALIDATION_NEED_ALREADY_PENDING"
        return {
            "schema_version": "1.0",
            "validation_request_id": f"validation_request_{request_fingerprint[:12]}",
            "request_fingerprint": request_fingerprint,
            "request_state": request_state,
            "request_admission_state": admission,
            "request_admission_reason": reason,
            "deduplicated": bool(existing) and not failures,
            "existing_validation_request_id": (
                existing.get("validation_request_id") if existing else None
            ),
            "evidence_candidate_id": candidate.get("evidence_candidate_id"),
            "source_task_execution_id": candidate.get(
                "source_task_execution_id"
            ),
            "source_run_id": candidate.get("source_run_id"),
            "source_task_id": candidate.get("source_task_id"),
            "capability_id": candidate.get("capability_id"),
            "claim_id": candidate.get("claim_id"),
            "claim_subject": candidate.get("claim_subject"),
            "requested_validation_scope": "GOVERNED_EVIDENCE_PLAN_REQUEST",
            "validation_reason": candidate.get("proposal_reason"),
            "supporting_diagnostics": candidate.get("diagnostic_refs", []),
            "evidence_need": evidence_need,
            "provenance": {
                "source_evidence_candidate_id": candidate.get(
                    "evidence_candidate_id"
                ),
                "source_training_experience": candidate.get("provenance"),
                "validation_execution_origin": "NOT_CREATED_BY_REQUEST",
            },
            "authority": self.AUTHORITY,
            "behavioral_authority": self.BEHAVIORAL_AUTHORITY,
            "evidence_plan_authority": "NONE",
            "raw_evidence_authority": "NONE",
            "accepted_evidence_authority": "NONE",
            "qualification_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
        }

    def route_request_to_evidence_plan(
        self,
        request: Mapping[str, Any],
        *,
        evidence_plan_store: EvidenceAcquisitionPlanStore | None = None,
    ) -> dict[str, Any]:
        request = dict(request or {})
        if request.get("request_admission_state") != "ADMITTED":
            return {
                "request_consumed": False,
                "request_consumption_state": "NOT_CONSUMED",
                "request_consumption_reason": request.get(
                    "request_admission_reason",
                    "request_not_admitted",
                ),
                "evidence_plan_created": False,
            }
        store = evidence_plan_store or self.evidence_plan_store
        if store is None:
            store = EvidenceAcquisitionPlanStore()
        need = dict(request.get("evidence_need") or {})
        plan_payload = {
            **need,
            "source_run_id": request.get("source_run_id"),
            "source_task_id": request.get("source_task_id"),
            "source_task_execution_id": request.get("source_task_execution_id"),
            "source_candidate_id": need.get("target_candidate"),
            "source_operation": need.get("target_operation"),
            "validation_request_id": request.get("validation_request_id"),
            "evidence_candidate_id": request.get("evidence_candidate_id"),
            "claim_id": request.get("claim_id"),
            "claim_subject": request.get("claim_subject"),
            "training_experience_origin": request.get("provenance", {}).get(
                "source_training_experience",
                {},
            ),
        }
        report = store.persist_plan(plan_payload)
        consumed = report.get("evidence_plan_storage_state") in {
            "NEW_PLAN_PERSISTED",
            "EQUIVALENT_PENDING_PLAN_REUSED",
        }
        if consumed:
            request = {
                **request,
                "request_state": "CONSUMED_TO_EVIDENCE_PLAN",
                "request_consumption_state": "CONSUMED",
                "evidence_plan_id": report.get("evidence_plan_id"),
                "evidence_plan_fingerprint": report.get(
                    "evidence_plan_fingerprint"
                ),
            }
            self._write_request(request)
        return {
            **report,
            "request_consumed": consumed,
            "request_consumption_state": (
                "CONSUMED" if consumed else "NOT_CONSUMED"
            ),
            "validation_request_id": request.get("validation_request_id"),
            "evidence_candidate_id": request.get("evidence_candidate_id"),
            "evidence_plan_created": report.get("evidence_plan_persisted", False),
            "request_is_not_evidence_plan": True,
        }

    def deny_direct_raw_evidence(self, outcome: Mapping[str, Any] | None) -> dict[str, Any]:
        return self._denial("DIRECT_TASKOUTCOME_TO_RAWEVIDENCE_DENIED", outcome)

    def deny_direct_accepted_evidence(
        self,
        outcome: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        return self._denial("DIRECT_TASKOUTCOME_TO_ACCEPTEDEVIDENCE_DENIED", outcome)

    def _candidate_eligibility(
        self,
        experience: Mapping[str, Any],
        evidence_need: Mapping[str, Any],
        capability: Mapping[str, Any],
    ) -> dict[str, Any]:
        if self._missing(experience.get("source_task_execution_id")):
            return self._ineligible("missing_task_execution_id")
        if not evidence_need:
            return self._ineligible("no_current_evidence_need")
        if evidence_need.get("evidence_need_state") not in {
            "CURRENT",
            "ACTIVE",
            "PENDING",
            "QUALIFICATION_EVIDENCE_REQUIRED",
        }:
            return self._ineligible("evidence_need_not_current")
        if capability.get("capability_resolution_state") != (
            "CANONICAL_CAPABILITY_TARGET_RESOLVED"
        ):
            return self._ineligible("canonical_capability_target_not_resolved")
        purpose = str(experience.get("selection_purpose") or "TRAINING").upper()
        if purpose not in self.ELIGIBLE_PURPOSES:
            return self._ineligible("selection_purpose_not_validation_relevant")
        reason = str(evidence_need.get("validation_sponsorship_reason") or "")
        novel = bool(evidence_need.get("novel_diagnostic_failure"))
        qualification = bool(evidence_need.get("qualification_evidence_need"))
        explicit = bool(evidence_need.get("explicit_validation_sponsorship"))
        if qualification or explicit or novel or reason:
            return {
                "candidate_eligible": True,
                "eligibility_state": "VALIDATION_REQUEST_ELIGIBLE",
                "proposal_reason": (
                    reason
                    or (
                        "qualification_evidence_need"
                        if qualification
                        else "novel_diagnostic_failure"
                        if novel
                        else "explicit_validation_sponsorship"
                    )
                ),
            }
        return self._ineligible("outcome_not_materially_validation_worthy")

    def _capability_resolution(
        self,
        experience: Mapping[str, Any],
        evidence_need: Mapping[str, Any],
    ) -> dict[str, Any]:
        capability_id = evidence_need.get("capability_id")
        state = evidence_need.get("capability_identity_state")
        if capability_id and state == "CANONICAL_CAPABILITY_TARGET_RESOLVED":
            return {
                "capability_resolution_state": (
                    "CANONICAL_CAPABILITY_TARGET_RESOLVED"
                ),
                "capability_id": str(capability_id),
                "capability_refs": [str(capability_id)],
            }
        labels = []
        metadata = experience.get("task_metadata")
        if isinstance(metadata, Mapping):
            for key in ("target_concepts", "target_capability", "capability_targets"):
                value = metadata.get(key)
                if isinstance(value, list):
                    labels.extend(str(item) for item in value if item)
                elif value:
                    labels.append(str(value))
        if len(set(labels)) > 1:
            return {
                "capability_resolution_state": "MULTIPLE_CAPABILITY_TARGETS",
                "capability_id": None,
                "capability_refs": sorted(set(labels)),
            }
        if labels:
            return {
                "capability_resolution_state": "CAPABILITY_TARGET_AMBIGUOUS",
                "capability_id": None,
                "capability_refs": sorted(set(labels)),
            }
        return {
            "capability_resolution_state": "CAPABILITY_TARGET_UNRESOLVED",
            "capability_id": None,
            "capability_refs": [],
        }

    def _claim_resolution(self, evidence_need: Mapping[str, Any]) -> dict[str, Any]:
        claim_id = evidence_need.get("claim_id")
        claim_subject = evidence_need.get("claim_subject")
        if claim_id and claim_subject:
            return {
                "claim_resolution_state": "CANONICAL_CLAIM_TARGET_RESOLVED",
                "claim_id": str(claim_id),
                "claim_subject": claim_subject,
            }
        if evidence_need.get("claim_required", True):
            return {
                "claim_resolution_state": "CLAIM_TARGET_UNRESOLVED",
                "claim_id": None,
                "claim_subject": claim_subject,
            }
        return {
            "claim_resolution_state": "CLAIM_NOT_REQUIRED_FOR_REQUEST",
            "claim_id": claim_id,
            "claim_subject": claim_subject,
        }

    def _persist_candidate_and_request(
        self,
        candidate: Mapping[str, Any],
        request: Mapping[str, Any],
    ) -> dict[str, Any]:
        candidate_persisted = candidate.get("candidate_state") in {
            "CANDIDATE_CREATED",
            "TARGET_RESOLUTION_REQUIRED",
        }
        if candidate_persisted:
            self._write_candidate(dict(candidate))
        if request.get("request_state") in {"PENDING", "CONSUMED_TO_EVIDENCE_PLAN"}:
            self._write_request(dict(request))
            rejected_persisted = False
        elif candidate_persisted:
            path = self.invalid_path / f"{request.get('validation_request_id')}.json"
            self._atomic_write(path, dict(request))
            rejected_persisted = True
        else:
            rejected_persisted = False
        return {
            "candidate_persisted": candidate_persisted,
            "request_persisted": request.get("request_state") in {
                "PENDING",
                "CONSUMED_TO_EVIDENCE_PLAN",
            },
            "request_rejected_persisted": rejected_persisted,
            "pending_request_count": len(self._json_files(self.requests_path)),
        }

    def _write_candidate(self, candidate: dict[str, Any]) -> None:
        path = self.candidates_path / f"{candidate['evidence_candidate_id']}.json"
        if not path.exists():
            self._atomic_write(path, candidate)

    def _write_request(self, request: dict[str, Any]) -> None:
        request.setdefault("request_currentness_state", "PENDING_CURRENT")
        path = self.requests_path / f"{request['validation_request_id']}.json"
        self._atomic_write(path, request)

    def _find_existing_request(self, request_fingerprint: str) -> dict[str, Any] | None:
        for path in self._json_files(self.requests_path):
            try:
                request = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if (
                request.get("request_fingerprint") == request_fingerprint
                and request.get("request_state")
                in {"PENDING", "CONSUMED_TO_EVIDENCE_PLAN"}
            ):
                return request
        return None

    def _initialize(self) -> None:
        for path in (self.candidates_path, self.requests_path, self.invalid_path):
            path.mkdir(parents=True, exist_ok=True)

    def _json_files(self, path: Path) -> list[Path]:
        if not path.exists():
            return []
        return sorted(p for p in path.glob("*.json") if not p.name.endswith(".tmp"))

    def _atomic_write(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True)
        json.loads(encoded)
        tmp = path.with_suffix(f"{path.suffix}.tmp")
        with tmp.open("w", encoding="utf-8") as file:
            file.write(encoded)
            file.write("\n")
            file.flush()
            try:
                os.fsync(file.fileno())
            except OSError:
                pass
        tmp.replace(path)

    def _denial(self, reason: str, outcome: Mapping[str, Any] | None) -> dict[str, Any]:
        outcome = dict(outcome or {})
        return {
            "admission_state": "DENIED",
            "denial_reason": reason,
            "source_task_execution_id": self._first(
                outcome,
                "task_execution_id",
                "origin_task_execution_id",
            ),
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
            "authority": self.AUTHORITY,
        }

    def _diagnostic_refs(self, experience: Mapping[str, Any]) -> list[dict[str, Any]]:
        refs = []
        residual = experience.get("residual")
        if isinstance(residual, Mapping) and residual:
            refs.append({
                "diagnostic_type": "residual_analysis",
                "residual_type": residual.get("residual_type"),
                "residual_difference_count": residual.get(
                    "residual_difference_count"
                ),
            })
        failure = experience.get("failure_classification")
        if not self._missing(failure):
            refs.append({
                "diagnostic_type": "failure_classification",
                "failure_classification": failure,
            })
        return refs

    def _ineligible(self, reason: str) -> dict[str, Any]:
        return {
            "candidate_eligible": False,
            "eligibility_state": "NOT_VALIDATION_WORTHY",
            "proposal_reason": reason,
        }

    def _first(self, mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
        for key in keys:
            value = mapping.get(key)
            if not self._missing(value):
                return value
        return default

    def _term(self, value: Any) -> str:
        text = str(value or "").strip()
        return text if text else "Not Available"

    def _missing(self, value: Any) -> bool:
        return str(value or "").strip() in {"", "Not Available", "None", "null"}

    def _fingerprint(self, payload: Mapping[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _id(self, prefix: str, payload: Mapping[str, Any]) -> str:
        return f"{prefix}_{self._fingerprint(payload)[:12]}"
