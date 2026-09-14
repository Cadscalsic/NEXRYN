from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from runtime.evidence.validation_sponsorship import (
    NEED_TYPE_TO_SCOPE,
    ValidationSponsorshipAuthorityEngine,
)


UNKNOWN = {"", "NONE", "None", "Not Available", "UNKNOWN", "null", "NULL"}


class ValidationRequestStatus(str, Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    CONSUMED_TO_EVIDENCE_PLAN = "CONSUMED_TO_EVIDENCE_PLAN"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"


class ValidationRequestError(ValueError):
    """Raised when a validation request subject is malformed."""


REQUEST_SCOPE_BY_SPONSORSHIP_SCOPE = {
    "GENERAL_EVIDENCE_VALIDATION": "GENERAL_SUPPORT",
    "INDEPENDENT_SOURCE_VALIDATION": "SOURCE_INDEPENDENCE",
    "CAUSAL_SUPPORT_VALIDATION": "CAUSAL_SUPPORT",
    "INDEPENDENT_REPLICATION_VALIDATION": "REPRODUCIBILITY",
    "CONTRADICTION_RESOLUTION_VALIDATION": "CONTRADICTION_RESOLUTION",
    "REVALIDATION": "REVALIDATION",
}


REQUEST_NEED_CONTRACT = {
    "GENERAL_SUPPORT_REQUIRED": {
        "required_evidence_category": "GOVERNED_VALIDATION",
        "required_evidence": "governed_validation_evidence",
        "required_validation_task": "general_support_validation_task",
        "tie_break_strategy": "governed_validation",
    },
    "SOURCE_INDEPENDENCE_REQUIRED": {
        "required_evidence_category": "CROSS_SOURCE_CONSENSUS",
        "required_evidence": "cross_source_consensus_evidence",
        "required_validation_task": "select_cross_source_tie_break_validation_task",
        "tie_break_strategy": "cross_source_consensus",
    },
    "CAUSAL_SUPPORT_REQUIRED": {
        "required_evidence_category": "CAUSAL_SUPPORT",
        "required_evidence": "causal_alignment_evidence",
        "required_validation_task": "causal_support_validation_task",
        "tie_break_strategy": "causal_support_validation",
    },
    "REPRODUCIBILITY_REQUIRED": {
        "required_evidence_category": "INDEPENDENT_REPLICATION",
        "required_evidence": "independent_replication_evidence",
        "required_validation_task": "independent_replication_validation_task",
        "tie_break_strategy": "independent_replication",
    },
    "CONTRADICTION_RESOLUTION_REQUIRED": {
        "required_evidence_category": "CONTRADICTION_RESOLUTION",
        "required_evidence": "contradiction_resolution_evidence",
        "required_validation_task": "contradiction_resolution_validation_task",
        "tie_break_strategy": "contradiction_resolution",
    },
    "REVALIDATION_REQUIRED": {
        "required_evidence_category": "REVALIDATION",
        "required_evidence": "governed_revalidation_evidence",
        "required_validation_task": "governed_revalidation_task",
        "tie_break_strategy": "governed_revalidation",
    },
}


ALLOWED_PRODUCERS = {
    "ValidationSponsorshipAuthorityEngine",
    "ValidationRequestAuthorityEngine",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _fingerprint(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def _missing(value: Any) -> bool:
    return str(value or "").strip() in UNKNOWN


def _copy_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


class ValidationRequestSubject:
    """Canonical semantic target of sponsored validation work."""

    schema_version = "1.0"

    def __init__(
        self,
        *,
        evidence_need_id: str,
        validation_sponsorship_id: str,
        target_type: str,
        capability_id: str,
        need_type: str,
        requested_validation_scope: str,
        validation_sponsorship_decision_id: str | None = None,
        evidence_need_decision_id: str | None = None,
        claim_id: str | None = None,
        claim_subject_ref: Mapping[str, Any] | str | None = None,
        capability_subject: Mapping[str, Any] | None = None,
        qualification_target_level: str | None = None,
        current_qualification_level: str | None = None,
        required_independent_sources: int | None = None,
    ) -> None:
        if _missing(evidence_need_id):
            raise ValidationRequestError("missing_evidence_need_id")
        if _missing(validation_sponsorship_id):
            raise ValidationRequestError("missing_validation_sponsorship_id")
        if _missing(target_type):
            raise ValidationRequestError("missing_target_type")
        if _missing(capability_id):
            raise ValidationRequestError("missing_capability_id")
        if _missing(need_type):
            raise ValidationRequestError("missing_need_type")
        if _missing(requested_validation_scope):
            raise ValidationRequestError("missing_requested_validation_scope")
        self.payload = {
            "schema_version": self.schema_version,
            "evidence_need_id": str(evidence_need_id),
            "evidence_need_decision_id": str(
                evidence_need_decision_id or "Not Available"
            ),
            "validation_sponsorship_id": str(validation_sponsorship_id),
            "validation_sponsorship_decision_id": str(
                validation_sponsorship_decision_id or "Not Available"
            ),
            "target_type": str(target_type),
            "capability_id": str(capability_id),
            "claim_id": str(claim_id or "Not Available"),
            "claim_subject_ref": (
                dict(claim_subject_ref)
                if isinstance(claim_subject_ref, Mapping)
                else str(claim_subject_ref or "Not Available")
            ),
            "capability_subject": (
                dict(capability_subject)
                if isinstance(capability_subject, Mapping)
                else {}
            ),
            "qualification_target_level": str(
                qualification_target_level or "Not Available"
            ),
            "current_qualification_level": str(
                current_qualification_level or "Not Available"
            ),
            "required_independent_sources": (
                int(required_independent_sources)
                if required_independent_sources is not None
                else 0
            ),
            "need_type": str(need_type),
            "requested_validation_scope": str(requested_validation_scope),
        }
        self.payload["validation_request_subject_id"] = (
            "validation_request_subject_"
            f"{_fingerprint(self.semantic_identity())[:16]}"
        )

    @classmethod
    def from_sponsorship_state(
        cls,
        sponsorship_state: Mapping[str, Any],
        *,
        requested_validation_scope: str | None = None,
    ) -> "ValidationRequestSubject":
        sponsorship_state = _copy_mapping(sponsorship_state)
        subject = _copy_mapping(sponsorship_state.get("subject"))
        sponsorship_scope = str(sponsorship_state.get("validation_scope") or "")
        request_scope = (
            requested_validation_scope
            or REQUEST_SCOPE_BY_SPONSORSHIP_SCOPE.get(sponsorship_scope)
            or sponsorship_scope
        )
        return cls(
            evidence_need_id=sponsorship_state.get("evidence_need_id"),
            evidence_need_decision_id=sponsorship_state.get("evidence_need_decision_id"),
            validation_sponsorship_id=sponsorship_state.get(
                "validation_sponsorship_id"
            ),
            validation_sponsorship_decision_id=sponsorship_state.get(
                "current_decision_id"
            ),
            target_type=subject.get("target_type"),
            capability_id=subject.get("capability_id"),
            claim_id=subject.get("claim_id"),
            claim_subject_ref=subject.get("claim_subject_ref"),
            capability_subject=subject.get("capability_subject"),
            qualification_target_level=subject.get("qualification_target_level"),
            current_qualification_level=subject.get("current_qualification_level"),
            required_independent_sources=subject.get("required_independent_sources"),
            need_type=subject.get("need_type") or sponsorship_state.get("need_type"),
            requested_validation_scope=request_scope,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ValidationRequestSubject":
        return cls(
            evidence_need_id=value.get("evidence_need_id"),
            evidence_need_decision_id=value.get("evidence_need_decision_id"),
            validation_sponsorship_id=value.get("validation_sponsorship_id"),
            validation_sponsorship_decision_id=value.get(
                "validation_sponsorship_decision_id"
            ),
            target_type=value.get("target_type"),
            capability_id=value.get("capability_id"),
            claim_id=value.get("claim_id"),
            claim_subject_ref=value.get("claim_subject_ref"),
            capability_subject=value.get("capability_subject"),
            qualification_target_level=value.get("qualification_target_level"),
            current_qualification_level=value.get("current_qualification_level"),
            required_independent_sources=value.get("required_independent_sources"),
            need_type=value.get("need_type"),
            requested_validation_scope=value.get("requested_validation_scope"),
        )

    def semantic_identity(self) -> dict[str, Any]:
        return {
            key: self.payload[key]
            for key in (
                "evidence_need_id",
                "validation_sponsorship_id",
                "target_type",
                "capability_id",
                "claim_id",
                "claim_subject_ref",
                "need_type",
                "requested_validation_scope",
            )
        }

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


class ValidationRequestAuthorityEngine:
    """Single authority for current sponsored validation requests."""

    schema_version = "1.0"
    authority = "VALIDATION_REQUEST_AUTHORITY_ENGINE"
    candidate_authority = "NONE"
    assessment_authority = "NONE"

    def __init__(
        self,
        state_dir: str | os.PathLike[str] = "runtime/state/validation_requests",
        *,
        sponsorship_authority: ValidationSponsorshipAuthorityEngine | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.decisions_dir = self.state_dir / "decisions"
        self.current_dir = self.state_dir / "current"
        self.history_dir = self.state_dir / "history"
        self.invalid_dir = self.state_dir / "invalid"
        self.sponsorship_authority = (
            sponsorship_authority or ValidationSponsorshipAuthorityEngine()
        )

    def initialize(self) -> None:
        for path in (
            self.decisions_dir,
            self.current_dir,
            self.history_dir,
            self.invalid_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def validation_request_id(
        self,
        subject: Mapping[str, Any] | ValidationRequestSubject,
    ) -> str:
        payload = (
            subject.to_dict()
            if isinstance(subject, ValidationRequestSubject)
            else ValidationRequestSubject.from_mapping(subject).to_dict()
        )
        return "validation_request_" + _fingerprint({
            key: payload[key]
            for key in (
                "evidence_need_id",
                "validation_sponsorship_id",
                "target_type",
                "capability_id",
                "claim_id",
                "claim_subject_ref",
                "need_type",
                "requested_validation_scope",
            )
        })[:16]

    def candidate_from_current_sponsorship(
        self,
        validation_sponsorship_id: str,
        *,
        requested_validation_scope: str | None = None,
        producer: str = "ValidationSponsorshipAuthorityEngine",
        existing_plan_index: Iterable[Mapping[str, Any]] | None = None,
        pending_work_index: Iterable[Mapping[str, Any]] | None = None,
        governance_blocks: Iterable[Mapping[str, Any] | str] | None = None,
    ) -> dict[str, Any]:
        if producer not in ALLOWED_PRODUCERS:
            return self._rejected_candidate(
                producer=producer,
                reason="DENIED_WRONG_AUTHORITY",
                validation_sponsorship_id=validation_sponsorship_id,
            )
        sponsorship = self.sponsorship_authority.get_current_validation_sponsorship(
            validation_sponsorship_id
        )
        if not sponsorship or not sponsorship.get("is_current"):
            return self._rejected_candidate(
                producer=producer,
                reason="DENIED_NO_CURRENT_VALIDATION_SPONSORSHIP",
                validation_sponsorship_id=validation_sponsorship_id,
            )
        subject = ValidationRequestSubject.from_sponsorship_state(
            sponsorship,
            requested_validation_scope=requested_validation_scope,
        )
        return self.propose_candidate(
            subject=subject.to_dict(),
            producer=producer,
            request_reason="current_sponsorship_requests_validation_work",
            source_sponsorship_state=sponsorship,
            existing_plan_index=existing_plan_index,
            pending_work_index=pending_work_index,
            governance_blocks=governance_blocks,
        )

    def propose_candidate(
        self,
        *,
        subject: Mapping[str, Any],
        producer: str,
        request_reason: str,
        source_sponsorship_state: Mapping[str, Any] | None = None,
        existing_plan_index: Iterable[Mapping[str, Any]] | None = None,
        pending_work_index: Iterable[Mapping[str, Any]] | None = None,
        governance_blocks: Iterable[Mapping[str, Any] | str] | None = None,
        priority: str = "ADVISORY",
    ) -> dict[str, Any]:
        subject_payload = ValidationRequestSubject.from_mapping(subject).to_dict()
        request_id = self.validation_request_id(subject_payload)
        sponsorship_state = _copy_mapping(source_sponsorship_state)
        need_type = subject_payload.get("need_type")
        need_contract = dict(REQUEST_NEED_CONTRACT.get(str(need_type), {}))
        candidate = {
            "schema_version": self.schema_version,
            "system": "validation_request_candidate",
            "validation_request_id": request_id,
            "validation_sponsorship_id": subject_payload.get(
                "validation_sponsorship_id"
            ),
            "validation_sponsorship_decision_id": subject_payload.get(
                "validation_sponsorship_decision_id"
            ),
            "source_sponsorship_state_fingerprint": sponsorship_state.get(
                "state_fingerprint"
            ),
            "evidence_need_id": subject_payload.get("evidence_need_id"),
            "evidence_need_decision_id": subject_payload.get(
                "evidence_need_decision_id"
            ),
            "subject": subject_payload,
            "target": {
                "target_type": subject_payload.get("target_type"),
                "capability_id": subject_payload.get("capability_id"),
                "claim_id": subject_payload.get("claim_id"),
                "claim_subject_ref": subject_payload.get("claim_subject_ref"),
                "target_operation": (
                    (subject_payload.get("capability_subject") or {}).get(
                        "operation"
                    )
                    if isinstance(
                        subject_payload.get("capability_subject"),
                        Mapping,
                    )
                    else None
                ),
            },
            "need_type": need_type,
            "requested_validation_scope": subject_payload.get(
                "requested_validation_scope"
            ),
            "request_reason": str(request_reason or "UNKNOWN"),
            "producer": str(producer or "UNKNOWN"),
            "provenance": {
                "source": "validation_sponsorship",
                "source_validation_sponsorship_id": subject_payload.get(
                    "validation_sponsorship_id"
                ),
                "source_validation_sponsorship_decision_id": subject_payload.get(
                    "validation_sponsorship_decision_id"
                ),
                "source_evidence_need_id": subject_payload.get("evidence_need_id"),
                "source_evidence_need_decision_id": subject_payload.get(
                    "evidence_need_decision_id"
                ),
            },
            "evidence_need": {
                **need_contract,
                "evidence_need_id": subject_payload.get("evidence_need_id"),
                "validation_sponsorship_id": subject_payload.get(
                    "validation_sponsorship_id"
                ),
                "target_candidate": subject_payload.get("capability_id"),
                "target_operation": (
                    (subject_payload.get("capability_subject") or {}).get(
                        "operation"
                    )
                    if isinstance(
                        subject_payload.get("capability_subject"),
                        Mapping,
                    )
                    else subject_payload.get("need_type")
                ),
                "governed_reentry_action": (
                    "admit_request_to_future_evidence_plan_authority"
                ),
                "claim_required": not _missing(subject_payload.get("claim_id")),
            },
            "priority_metadata": {
                "priority": str(priority or "ADVISORY"),
                "task_ranking_authority": "NONE",
            },
            "existing_plan_matches": [dict(item) for item in existing_plan_index or []],
            "pending_work_matches": [dict(item) for item in pending_work_index or []],
            "governance_blocks": [
                dict(item) if isinstance(item, Mapping) else {"block": str(item)}
                for item in governance_blocks or []
            ],
            "candidate_authority": self.candidate_authority,
            "authority": self.candidate_authority,
            "evidence_plan_created": False,
            "validation_schedule_created": False,
            "validation_execution_started": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
            "qualification_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "planning_authority": "NONE",
            "goal_authority": "NONE",
            "intent_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "selector_authority": "NONE",
            "created_at": _now(),
        }
        candidate["candidate_fingerprint"] = _fingerprint(
            self._candidate_fingerprint_payload(candidate)
        )
        return candidate

    def assess_candidate(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        candidate = _copy_mapping(candidate)
        failures = self._candidate_failures(candidate)
        duplicate = self.is_validation_request_current(
            candidate.get("validation_request_id")
        )
        existing_plan = bool(candidate.get("existing_plan_matches"))
        pending_work = bool(candidate.get("pending_work_matches"))
        governance_block = bool(candidate.get("governance_blocks"))
        if duplicate:
            failures.append("validation_request_already_pending")
        if existing_plan:
            failures.append("plan_already_covers_request")
        if pending_work:
            failures.append("validation_already_scheduled")
        if governance_block:
            failures.append("governance_block")
        assessment = {
            "schema_version": self.schema_version,
            "system": "validation_request_assessment",
            "validation_request_id": candidate.get("validation_request_id"),
            "validation_sponsorship_id": candidate.get("validation_sponsorship_id"),
            "evidence_need_id": candidate.get("evidence_need_id"),
            "subject": candidate.get("subject"),
            "requested_validation_scope": candidate.get(
                "requested_validation_scope"
            ),
            "sponsorship_current": (
                "sponsorship_not_current" not in failures
                and "missing_sponsorship" not in failures
            ),
            "need_current": "source_need_not_current" not in failures,
            "target_valid": "missing_capability_id" not in failures,
            "scope_valid": "invalid_validation_scope" not in failures,
            "request_duplicated": duplicate,
            "current_plan_exists": existing_plan,
            "active_schedule_exists": pending_work,
            "request_still_necessary": not (existing_plan or pending_work),
            "governance_allows_downstream_planning": not governance_block,
            "assessment_failures": sorted(set(failures)),
            "assessment_state": (
                "VALIDATION_REQUEST_ASSESSMENT_ACCEPTED"
                if not failures
                else "VALIDATION_REQUEST_ASSESSMENT_DENIED"
            ),
            "authority": self.assessment_authority,
            "evidence_plan_created": False,
            "validation_schedule_created": False,
            "validation_execution_started": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
            "created_at": _now(),
        }
        assessment["assessment_fingerprint"] = _fingerprint(
            self._assessment_fingerprint_payload(assessment)
        )
        return assessment

    def decide_request(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        self.initialize()
        candidate = _copy_mapping(candidate)
        assessment = self.assess_candidate(candidate)
        previous = self.get_current_validation_request(
            candidate.get("validation_request_id")
        )
        if assessment.get("assessment_failures"):
            reason = ";".join(assessment["assessment_failures"])
            status = ValidationRequestStatus.INVALIDATED.value
            decision_state = self._denied_state(reason)
            if "validation_request_already_pending" in reason:
                status = ValidationRequestStatus.PENDING.value
        elif previous and previous.get("lifecycle_status") == "PENDING":
            reason = "VALIDATION_REQUEST_ALREADY_PENDING"
            status = ValidationRequestStatus.PENDING.value
            decision_state = "VALIDATION_REQUEST_ALREADY_PENDING"
        else:
            reason = "current_sponsorship_admits_validation_request"
            status = ValidationRequestStatus.PENDING.value
            decision_state = "VALIDATION_REQUEST_PENDING"
        return self._persist_decision(
            validation_request_id=candidate.get("validation_request_id"),
            validation_sponsorship_id=candidate.get("validation_sponsorship_id"),
            validation_sponsorship_decision_id=candidate.get(
                "validation_sponsorship_decision_id"
            ),
            source_sponsorship_state_fingerprint=candidate.get(
                "source_sponsorship_state_fingerprint"
            ),
            evidence_need_id=candidate.get("evidence_need_id"),
            evidence_need_decision_id=candidate.get("evidence_need_decision_id"),
            subject=candidate.get("subject"),
            requested_validation_scope=candidate.get("requested_validation_scope"),
            evidence_need=candidate.get("evidence_need"),
            decision_state=decision_state,
            lifecycle_status=status,
            reason=reason,
            assessment=assessment,
            previous_state=previous,
            provenance={
                "candidate_fingerprint": candidate.get("candidate_fingerprint"),
                "producer": candidate.get("producer"),
                "provenance": candidate.get("provenance", {}),
            },
        )

    def consume_request(
        self,
        validation_request_id: str,
        *,
        evidence_plan_id: str,
        consumer: str,
        consumer_decision_id: str | None = None,
    ) -> dict[str, Any]:
        state = self.get_current_validation_request(validation_request_id)
        if not state:
            return self._invalid_transition(
                validation_request_id,
                "DENIED_VALIDATION_REQUEST_NOT_FOUND",
                reason="validation_request_not_found",
            )
        return self._transition(
            state,
            decision_state="VALIDATION_REQUEST_CONSUMED_TO_EVIDENCE_PLAN",
            lifecycle_status=ValidationRequestStatus.CONSUMED_TO_EVIDENCE_PLAN.value,
            reason="governed_evidence_plan_consumed_request",
            provenance={
                "consumer": consumer,
                "evidence_plan_id": evidence_plan_id,
                "consumer_decision_id": consumer_decision_id or "Not Available",
            },
        )

    def cancel_request(
        self,
        validation_request_id: str,
        *,
        cancellation_reason: str,
    ) -> dict[str, Any]:
        state = self.get_current_validation_request(validation_request_id)
        if not state:
            return self._invalid_transition(
                validation_request_id,
                "DENIED_VALIDATION_REQUEST_NOT_FOUND",
                reason="validation_request_not_found",
            )
        return self._transition(
            state,
            decision_state="VALIDATION_REQUEST_CANCELLED",
            lifecycle_status=ValidationRequestStatus.CANCELLED.value,
            reason=cancellation_reason,
        )

    def open_review(self, validation_request_id: str, *, review_reason: str) -> dict[str, Any]:
        state = self.get_current_validation_request(validation_request_id)
        if not state:
            return self._invalid_transition(
                validation_request_id,
                "DENIED_VALIDATION_REQUEST_NOT_FOUND",
                reason="validation_request_not_found",
            )
        return self._transition(
            state,
            decision_state="VALIDATION_REQUEST_UNDER_REVIEW",
            lifecycle_status=ValidationRequestStatus.UNDER_REVIEW.value,
            reason=review_reason,
        )

    def expire_request(
        self,
        validation_request_id: str,
        *,
        expiration_reason: str,
    ) -> dict[str, Any]:
        state = self.get_current_validation_request(validation_request_id)
        if not state:
            return self._invalid_transition(
                validation_request_id,
                "DENIED_VALIDATION_REQUEST_NOT_FOUND",
                reason="validation_request_not_found",
            )
        return self._transition(
            state,
            decision_state="VALIDATION_REQUEST_EXPIRED",
            lifecycle_status=ValidationRequestStatus.EXPIRED.value,
            reason=expiration_reason,
        )

    def get_current_validation_request(
        self,
        validation_request_id: str,
    ) -> dict[str, Any] | None:
        if _missing(validation_request_id):
            return None
        path = self.current_dir / f"{validation_request_id}.json"
        if not path.exists():
            return None
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return None
        if not isinstance(state, dict):
            return None
        valid = self._state_integrity_valid(state)
        sponsorship_current = self._source_sponsorship_dependency_valid(state)
        return {
            **state,
            "currentness_integrity_state": "VALID" if valid else "INVALID",
            "source_sponsorship_currentness_state": (
                "CURRENT" if sponsorship_current else "NOT_CURRENT"
            ),
            "is_current": bool(
                valid
                and sponsorship_current
                and state.get("lifecycle_status")
                == ValidationRequestStatus.PENDING.value
            ),
            "is_actionable_validation_request": bool(
                valid
                and sponsorship_current
                and state.get("lifecycle_status")
                == ValidationRequestStatus.PENDING.value
            ),
        }

    def get_validation_request_history(
        self,
        validation_request_id: str,
    ) -> list[dict[str, Any]]:
        path = self.history_dir / f"{validation_request_id}.json"
        if not path.exists():
            return []
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return []
        return rows if isinstance(rows, list) else []

    def is_validation_request_current(
        self,
        validation_request_id: str,
        *,
        expected_evidence_need_id: str | None = None,
        expected_validation_sponsorship_id: str | None = None,
        expected_capability_id: str | None = None,
        expected_claim_id: str | None = None,
        expected_need_type: str | None = None,
        expected_validation_scope: str | None = None,
    ) -> bool:
        state = self.get_current_validation_request(validation_request_id)
        if not state or not state.get("is_current"):
            return False
        subject = _copy_mapping(state.get("subject"))
        if expected_evidence_need_id and state.get("evidence_need_id") != expected_evidence_need_id:
            return False
        if expected_validation_sponsorship_id and state.get("validation_sponsorship_id") != expected_validation_sponsorship_id:
            return False
        if expected_capability_id and subject.get("capability_id") != expected_capability_id:
            return False
        if expected_claim_id and subject.get("claim_id") != expected_claim_id:
            return False
        if expected_need_type and subject.get("need_type") != expected_need_type:
            return False
        if expected_validation_scope and state.get("requested_validation_scope") != expected_validation_scope:
            return False
        return True

    def list_current_validation_requests(
        self,
        *,
        include_non_pending: bool = False,
    ) -> list[dict[str, Any]]:
        if not self.current_dir.exists():
            return []
        rows = []
        for path in sorted(self.current_dir.glob("*.json")):
            state = self.get_current_validation_request(path.stem)
            if state and (include_non_pending or state.get("is_current")):
                rows.append(state)
        return rows

    def _transition(
        self,
        state: Mapping[str, Any],
        *,
        decision_state: str,
        lifecycle_status: str,
        reason: str,
        provenance: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._persist_decision(
            validation_request_id=state.get("validation_request_id"),
            validation_sponsorship_id=state.get("validation_sponsorship_id"),
            validation_sponsorship_decision_id=state.get(
                "validation_sponsorship_decision_id"
            ),
            source_sponsorship_state_fingerprint=state.get(
                "source_sponsorship_state_fingerprint"
            ),
            evidence_need_id=state.get("evidence_need_id"),
            evidence_need_decision_id=state.get("evidence_need_decision_id"),
            subject=state.get("subject"),
            requested_validation_scope=state.get("requested_validation_scope"),
            evidence_need=state.get("evidence_need"),
            decision_state=decision_state,
            lifecycle_status=lifecycle_status,
            reason=reason,
            previous_state=state,
            provenance=dict(provenance or {}),
        )

    def _persist_decision(
        self,
        *,
        validation_request_id: str,
        validation_sponsorship_id: str,
        validation_sponsorship_decision_id: str,
        source_sponsorship_state_fingerprint: str | None,
        evidence_need_id: str,
        evidence_need_decision_id: str,
        subject: Mapping[str, Any] | None,
        requested_validation_scope: str | None,
        evidence_need: Mapping[str, Any] | None,
        decision_state: str,
        lifecycle_status: str,
        reason: str,
        previous_state: Mapping[str, Any] | None = None,
        assessment: Mapping[str, Any] | None = None,
        provenance: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        previous_state = _copy_mapping(previous_state)
        decision = {
            "schema_version": self.schema_version,
            "system": "validation_request_decision",
            "validation_request_decision_id": "pending",
            "validation_request_id": validation_request_id,
            "previous_decision_id": previous_state.get("current_decision_id"),
            "validation_sponsorship_id": validation_sponsorship_id,
            "validation_sponsorship_decision_id": validation_sponsorship_decision_id,
            "source_sponsorship_state_fingerprint": (
                source_sponsorship_state_fingerprint
            ),
            "evidence_need_id": evidence_need_id,
            "evidence_need_decision_id": evidence_need_decision_id,
            "subject": dict(subject or {}),
            "requested_validation_scope": requested_validation_scope,
            "evidence_need": dict(evidence_need or {}),
            "decision_state": decision_state,
            "lifecycle_status": lifecycle_status,
            "reason": reason,
            "authority": self.authority,
            "provenance": dict(provenance or {}),
            "assessment": dict(assessment or {}),
            "evidence_plan_created": False,
            "validation_schedule_created": False,
            "validation_execution_started": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
            "qualification_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "planning_authority": "NONE",
            "goal_authority": "NONE",
            "intent_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "selector_authority": "NONE",
            "created_at": _now(),
        }
        decision["decision_fingerprint"] = _fingerprint(
            self._decision_fingerprint_payload(decision)
        )
        decision["validation_request_decision_id"] = (
            "validation_request_decision_"
            f"{decision['decision_fingerprint'][:16]}"
        )
        state = self._state_from_decision(decision)
        self._write_json(
            self.decisions_dir / f"{decision['validation_request_decision_id']}.json",
            decision,
        )
        self._write_json(self.current_dir / f"{validation_request_id}.json", state)
        history = self.get_validation_request_history(validation_request_id)
        history.append({
            "event_type": "VALIDATION_REQUEST_DECISION",
            "decision": decision,
            "resulting_state": state,
        })
        self._write_json(self.history_dir / f"{validation_request_id}.json", history)
        return {
            "decision": decision,
            "current_state": state,
            "assessment": dict(assessment or {}),
            "authority": self.authority,
            "evidence_plan_created": False,
            "validation_schedule_created": False,
            "validation_execution_started": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
        }

    def _state_from_decision(self, decision: Mapping[str, Any]) -> dict[str, Any]:
        state = {
            "schema_version": self.schema_version,
            "system": "validation_request_state",
            "validation_request_id": decision.get("validation_request_id"),
            "current_decision_id": decision.get("validation_request_decision_id"),
            "previous_decision_id": decision.get("previous_decision_id"),
            "validation_sponsorship_id": decision.get("validation_sponsorship_id"),
            "validation_sponsorship_decision_id": decision.get(
                "validation_sponsorship_decision_id"
            ),
            "source_sponsorship_state_fingerprint": decision.get(
                "source_sponsorship_state_fingerprint"
            ),
            "evidence_need_id": decision.get("evidence_need_id"),
            "evidence_need_decision_id": decision.get("evidence_need_decision_id"),
            "subject": decision.get("subject", {}),
            "requested_validation_scope": decision.get("requested_validation_scope"),
            "evidence_need": decision.get("evidence_need", {}),
            "decision_state": decision.get("decision_state"),
            "lifecycle_status": decision.get("lifecycle_status"),
            "reason": decision.get("reason"),
            "authority": self.authority,
            "state_authority": self.authority,
            "decision_fingerprint": decision.get("decision_fingerprint"),
            "updated_at": decision.get("created_at"),
            "evidence_plan_created": False,
            "validation_schedule_created": False,
            "validation_execution_started": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
            "qualification_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "planning_authority": "NONE",
            "goal_authority": "NONE",
            "intent_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "selector_authority": "NONE",
        }
        state["state_fingerprint"] = _fingerprint(
            self._state_fingerprint_payload(state)
        )
        return state

    def _candidate_failures(self, candidate: Mapping[str, Any]) -> list[str]:
        failures = []
        if candidate.get("producer") not in ALLOWED_PRODUCERS:
            failures.append("wrong_authority")
        if candidate.get("candidate_authority") not in {self.candidate_authority, None}:
            failures.append("candidate_claims_authority")
        subject = _copy_mapping(candidate.get("subject"))
        if not subject:
            failures.append("missing_request_subject")
        if _missing(subject.get("capability_id")):
            failures.append("missing_capability_id")
        sponsorship_id = candidate.get("validation_sponsorship_id")
        sponsorship = self.sponsorship_authority.get_current_validation_sponsorship(
            sponsorship_id
        )
        if not sponsorship:
            failures.append("missing_sponsorship")
        elif not sponsorship.get("is_current"):
            failures.append("sponsorship_not_current")
        else:
            if sponsorship.get("current_decision_id") != candidate.get(
                "validation_sponsorship_decision_id"
            ):
                failures.append("stale_sponsorship_decision")
            if sponsorship.get("state_fingerprint") != candidate.get(
                "source_sponsorship_state_fingerprint"
            ):
                failures.append("sponsorship_fingerprint_mismatch")
            if sponsorship.get("evidence_need_id") != candidate.get(
                "evidence_need_id"
            ):
                failures.append("cross_need_request")
            sponsorship_subject = _copy_mapping(sponsorship.get("subject"))
            if sponsorship_subject.get("capability_id") != subject.get("capability_id"):
                failures.append("cross_capability_request")
            if (
                not _missing(sponsorship_subject.get("claim_id"))
                and sponsorship_subject.get("claim_id") != subject.get("claim_id")
            ):
                failures.append("cross_claim_request")
            need_type = str(subject.get("need_type") or candidate.get("need_type") or "")
            expected_sponsorship_scope = NEED_TYPE_TO_SCOPE.get(need_type)
            if sponsorship.get("validation_scope") != expected_sponsorship_scope:
                failures.append("cross_scope_request")
            expected_request_scope = REQUEST_SCOPE_BY_SPONSORSHIP_SCOPE.get(
                str(sponsorship.get("validation_scope") or "")
            )
            if candidate.get("requested_validation_scope") != expected_request_scope:
                failures.append("invalid_validation_scope")
        need_type = str(candidate.get("need_type") or subject.get("need_type") or "")
        if need_type not in REQUEST_NEED_CONTRACT:
            failures.append("unsupported_need_type")
        expected_id = None
        if subject:
            try:
                expected_id = self.validation_request_id(subject)
            except ValidationRequestError:
                expected_id = None
        if expected_id and candidate.get("validation_request_id") != expected_id:
            failures.append("validation_request_id_mismatch")
        expected_fp = _fingerprint(self._candidate_fingerprint_payload(candidate))
        if candidate.get("candidate_fingerprint") != expected_fp:
            failures.append("candidate_fingerprint_invalid")
        return failures

    def _source_sponsorship_dependency_valid(self, state: Mapping[str, Any]) -> bool:
        sponsorship = self.sponsorship_authority.get_current_validation_sponsorship(
            state.get("validation_sponsorship_id")
        )
        if not sponsorship or not sponsorship.get("is_current"):
            return False
        return (
            sponsorship.get("current_decision_id")
            == state.get("validation_sponsorship_decision_id")
            and sponsorship.get("state_fingerprint")
            == state.get("source_sponsorship_state_fingerprint")
            and sponsorship.get("evidence_need_id") == state.get("evidence_need_id")
        )

    def _state_integrity_valid(self, state: Mapping[str, Any]) -> bool:
        if state.get("state_authority") != self.authority:
            return False
        expected = _fingerprint(self._state_fingerprint_payload(state))
        return state.get("state_fingerprint") == expected

    def _invalid_transition(
        self,
        validation_request_id: str,
        decision_state: str,
        *,
        reason: str,
    ) -> dict[str, Any]:
        return {
            "decision": {
                "validation_request_id": validation_request_id,
                "decision_state": decision_state,
                "reason": reason,
                "authority": self.authority,
            },
            "current_state": {},
            "authority": self.authority,
            "evidence_plan_created": False,
            "validation_schedule_created": False,
            "validation_execution_started": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
        }

    def _denied_state(self, reason: str) -> str:
        if "wrong_authority" in reason:
            return "DENIED_WRONG_AUTHORITY"
        if "missing_sponsorship" in reason or "sponsorship_not_current" in reason:
            return "DENIED_NO_CURRENT_VALIDATION_SPONSORSHIP"
        if "fingerprint" in reason or "mismatch" in reason:
            return "DENIED_VALIDATION_REQUEST_INTEGRITY_FAILURE"
        if "cross_" in reason:
            return "DENIED_CROSS_BOUNDARY_REQUEST"
        if "source_need_not_current" in reason:
            return "DENIED_NEED_NOT_CURRENT"
        if "invalid_validation_scope" in reason:
            return "DENIED_INVALID_VALIDATION_SCOPE"
        if "plan_already_covers_request" in reason:
            return "PLAN_ALREADY_COVERS_REQUEST"
        if "validation_already_scheduled" in reason:
            return "VALIDATION_ALREADY_SCHEDULED"
        if "validation_request_already_pending" in reason:
            return "VALIDATION_REQUEST_ALREADY_PENDING"
        return "DENIED_VALIDATION_REQUEST"

    def _candidate_fingerprint_payload(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "validation_request_id": candidate.get("validation_request_id"),
            "validation_sponsorship_id": candidate.get("validation_sponsorship_id"),
            "validation_sponsorship_decision_id": candidate.get(
                "validation_sponsorship_decision_id"
            ),
            "source_sponsorship_state_fingerprint": candidate.get(
                "source_sponsorship_state_fingerprint"
            ),
            "evidence_need_id": candidate.get("evidence_need_id"),
            "evidence_need_decision_id": candidate.get("evidence_need_decision_id"),
            "subject": candidate.get("subject"),
            "need_type": candidate.get("need_type"),
            "requested_validation_scope": candidate.get(
                "requested_validation_scope"
            ),
            "request_reason": candidate.get("request_reason"),
            "producer": candidate.get("producer"),
            "provenance": candidate.get("provenance", {}),
        }

    def _assessment_fingerprint_payload(self, assessment: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "validation_request_id": assessment.get("validation_request_id"),
            "validation_sponsorship_id": assessment.get("validation_sponsorship_id"),
            "evidence_need_id": assessment.get("evidence_need_id"),
            "requested_validation_scope": assessment.get(
                "requested_validation_scope"
            ),
            "assessment_failures": assessment.get("assessment_failures", []),
            "assessment_state": assessment.get("assessment_state"),
        }

    def _decision_fingerprint_payload(self, decision: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "validation_request_id": decision.get("validation_request_id"),
            "previous_decision_id": decision.get("previous_decision_id"),
            "validation_sponsorship_id": decision.get("validation_sponsorship_id"),
            "validation_sponsorship_decision_id": decision.get(
                "validation_sponsorship_decision_id"
            ),
            "source_sponsorship_state_fingerprint": decision.get(
                "source_sponsorship_state_fingerprint"
            ),
            "evidence_need_id": decision.get("evidence_need_id"),
            "evidence_need_decision_id": decision.get("evidence_need_decision_id"),
            "subject": decision.get("subject", {}),
            "requested_validation_scope": decision.get(
                "requested_validation_scope"
            ),
            "evidence_need": decision.get("evidence_need", {}),
            "decision_state": decision.get("decision_state"),
            "lifecycle_status": decision.get("lifecycle_status"),
            "reason": decision.get("reason"),
            "authority": decision.get("authority"),
            "provenance": decision.get("provenance", {}),
            "assessment": decision.get("assessment", {}),
            "created_at": decision.get("created_at"),
        }

    def _state_fingerprint_payload(self, state: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "validation_request_id": state.get("validation_request_id"),
            "current_decision_id": state.get("current_decision_id"),
            "previous_decision_id": state.get("previous_decision_id"),
            "validation_sponsorship_id": state.get("validation_sponsorship_id"),
            "validation_sponsorship_decision_id": state.get(
                "validation_sponsorship_decision_id"
            ),
            "source_sponsorship_state_fingerprint": state.get(
                "source_sponsorship_state_fingerprint"
            ),
            "evidence_need_id": state.get("evidence_need_id"),
            "evidence_need_decision_id": state.get("evidence_need_decision_id"),
            "subject": state.get("subject", {}),
            "requested_validation_scope": state.get("requested_validation_scope"),
            "evidence_need": state.get("evidence_need", {}),
            "decision_state": state.get("decision_state"),
            "lifecycle_status": state.get("lifecycle_status"),
            "reason": state.get("reason"),
            "authority": state.get("authority"),
            "state_authority": state.get("state_authority"),
            "decision_fingerprint": state.get("decision_fingerprint"),
            "updated_at": state.get("updated_at"),
        }

    def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
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

    def _rejected_candidate(
        self,
        *,
        producer: str,
        reason: str,
        validation_sponsorship_id: str | None = None,
    ) -> dict[str, Any]:
        candidate = {
            "schema_version": self.schema_version,
            "system": "validation_request_candidate",
            "validation_request_id": "Not Available",
            "validation_sponsorship_id": validation_sponsorship_id or "Not Available",
            "validation_sponsorship_decision_id": "Not Available",
            "source_sponsorship_state_fingerprint": "Not Available",
            "evidence_need_id": "Not Available",
            "evidence_need_decision_id": "Not Available",
            "subject": {},
            "target": {},
            "need_type": "Not Available",
            "requested_validation_scope": "Not Available",
            "request_reason": reason,
            "producer": str(producer or "UNKNOWN"),
            "provenance": {"rejection_reason": reason},
            "evidence_need": {},
            "existing_plan_matches": [],
            "pending_work_matches": [],
            "governance_blocks": [],
            "candidate_authority": self.candidate_authority,
            "authority": self.candidate_authority,
            "evidence_plan_created": False,
            "validation_schedule_created": False,
            "validation_execution_started": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
            "created_at": _now(),
        }
        candidate["candidate_fingerprint"] = _fingerprint(
            self._candidate_fingerprint_payload(candidate)
        )
        return candidate


__all__ = [
    "REQUEST_NEED_CONTRACT",
    "REQUEST_SCOPE_BY_SPONSORSHIP_SCOPE",
    "ValidationRequestAuthorityEngine",
    "ValidationRequestError",
    "ValidationRequestStatus",
    "ValidationRequestSubject",
]
