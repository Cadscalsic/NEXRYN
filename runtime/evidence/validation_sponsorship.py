from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from runtime.evidence.current_evidence_need import (
    CurrentEvidenceNeedAuthorityEngine,
    EvidenceNeedLifecycleStatus,
    EvidenceNeedType,
)


UNKNOWN = {"", "NONE", "None", "Not Available", "UNKNOWN", "null", "NULL"}


class ValidationSponsorshipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    CONSUMED = "CONSUMED"
    REVOKED = "REVOKED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"


class ValidationSponsorshipScope(str, Enum):
    GENERAL_EVIDENCE_VALIDATION = "GENERAL_EVIDENCE_VALIDATION"
    INDEPENDENT_SOURCE_VALIDATION = "INDEPENDENT_SOURCE_VALIDATION"
    CAUSAL_SUPPORT_VALIDATION = "CAUSAL_SUPPORT_VALIDATION"
    INDEPENDENT_REPLICATION_VALIDATION = "INDEPENDENT_REPLICATION_VALIDATION"
    CONTRADICTION_RESOLUTION_VALIDATION = "CONTRADICTION_RESOLUTION_VALIDATION"
    REVALIDATION = "REVALIDATION"
    CANDIDATE_DISAMBIGUATION_VALIDATION = "CANDIDATE_DISAMBIGUATION_VALIDATION"


NEED_TYPE_TO_SCOPE = {
    EvidenceNeedType.GENERAL_SUPPORT_REQUIRED.value: (
        ValidationSponsorshipScope.GENERAL_EVIDENCE_VALIDATION.value
    ),
    EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value: (
        ValidationSponsorshipScope.INDEPENDENT_SOURCE_VALIDATION.value
    ),
    EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value: (
        ValidationSponsorshipScope.CAUSAL_SUPPORT_VALIDATION.value
    ),
    EvidenceNeedType.REPRODUCIBILITY_REQUIRED.value: (
        ValidationSponsorshipScope.INDEPENDENT_REPLICATION_VALIDATION.value
    ),
    EvidenceNeedType.CONTRADICTION_RESOLUTION_REQUIRED.value: (
        ValidationSponsorshipScope.CONTRADICTION_RESOLUTION_VALIDATION.value
    ),
    EvidenceNeedType.REVALIDATION_REQUIRED.value: (
        ValidationSponsorshipScope.REVALIDATION.value
    ),
    EvidenceNeedType.CANDIDATE_DISAMBIGUATION_REQUIRED.value: (
        ValidationSponsorshipScope.CANDIDATE_DISAMBIGUATION_VALIDATION.value
    ),
}


ALLOWED_PRODUCERS = {
    "CurrentEvidenceNeedAuthorityEngine",
    "ValidationSponsorshipAuthorityEngine",
}


class ValidationSponsorshipError(ValueError):
    """Raised when a sponsorship request is malformed."""


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


class ValidationSponsorshipSubject:
    """Canonical semantic target of validation sponsorship permission."""

    schema_version = "1.0"

    def __init__(
        self,
        *,
        evidence_need_id: str,
        target_type: str,
        capability_id: str,
        need_type: str,
        validation_scope: str,
        evidence_need_decision_id: str | None = None,
        claim_id: str | None = None,
        claim_subject_ref: Mapping[str, Any] | str | None = None,
        capability_subject: Mapping[str, Any] | None = None,
        qualification_target_level: str | None = None,
        current_qualification_level: str | None = None,
        required_independent_sources: int | None = None,
    ) -> None:
        if _missing(evidence_need_id):
            raise ValidationSponsorshipError("missing_evidence_need_id")
        if _missing(target_type):
            raise ValidationSponsorshipError("missing_target_type")
        if _missing(capability_id):
            raise ValidationSponsorshipError("missing_capability_id")
        if _missing(need_type):
            raise ValidationSponsorshipError("missing_need_type")
        if _missing(validation_scope):
            raise ValidationSponsorshipError("missing_validation_scope")
        self.payload = {
            "schema_version": self.schema_version,
            "evidence_need_id": str(evidence_need_id),
            "evidence_need_decision_id": str(
                evidence_need_decision_id or "Not Available"
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
            "validation_scope": str(validation_scope),
        }
        self.payload["sponsorship_subject_id"] = (
            "validation_sponsorship_subject_"
            f"{_fingerprint(self.semantic_identity())[:16]}"
        )

    @classmethod
    def from_need_state(
        cls,
        need_state: Mapping[str, Any],
        *,
        validation_scope: str | None = None,
    ) -> "ValidationSponsorshipSubject":
        need_state = _copy_mapping(need_state)
        subject = _copy_mapping(need_state.get("subject"))
        need_type = str(need_state.get("need_type") or "")
        scope = validation_scope or NEED_TYPE_TO_SCOPE.get(need_type)
        return cls(
            evidence_need_id=need_state.get("evidence_need_id"),
            evidence_need_decision_id=need_state.get("current_decision_id"),
            target_type=subject.get("target_type"),
            capability_id=subject.get("capability_id"),
            claim_id=subject.get("claim_id"),
            claim_subject_ref=subject.get("claim_subject_ref"),
            capability_subject=subject.get("capability_subject"),
            qualification_target_level=subject.get("qualification_target_level"),
            current_qualification_level=subject.get("current_qualification_level"),
            required_independent_sources=subject.get("required_independent_sources"),
            need_type=need_type,
            validation_scope=scope or "Not Available",
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ValidationSponsorshipSubject":
        return cls(
            evidence_need_id=value.get("evidence_need_id"),
            evidence_need_decision_id=value.get("evidence_need_decision_id"),
            target_type=value.get("target_type"),
            capability_id=value.get("capability_id"),
            claim_id=value.get("claim_id"),
            claim_subject_ref=value.get("claim_subject_ref"),
            capability_subject=value.get("capability_subject"),
            qualification_target_level=value.get("qualification_target_level"),
            current_qualification_level=value.get("current_qualification_level"),
            required_independent_sources=value.get("required_independent_sources"),
            need_type=value.get("need_type"),
            validation_scope=value.get("validation_scope"),
        )

    def semantic_identity(self) -> dict[str, Any]:
        return {
            key: self.payload[key]
            for key in (
                "evidence_need_id",
                "target_type",
                "capability_id",
                "claim_id",
                "claim_subject_ref",
                "need_type",
                "validation_scope",
            )
        }

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


class ValidationSponsorshipAuthorityEngine:
    """Single authority for current validation sponsorship permission."""

    schema_version = "1.0"
    authority = "VALIDATION_SPONSORSHIP_AUTHORITY_ENGINE"
    candidate_authority = "NONE"
    assessment_authority = "NONE"

    def __init__(
        self,
        state_dir: str | os.PathLike[str] = "runtime/state/validation_sponsorships",
        *,
        need_authority: CurrentEvidenceNeedAuthorityEngine | None = None,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.decisions_dir = self.state_dir / "decisions"
        self.current_dir = self.state_dir / "current"
        self.history_dir = self.state_dir / "history"
        self.invalid_dir = self.state_dir / "invalid"
        self.need_authority = need_authority or CurrentEvidenceNeedAuthorityEngine()

    def initialize(self) -> None:
        for path in (
            self.decisions_dir,
            self.current_dir,
            self.history_dir,
            self.invalid_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def validation_sponsorship_id(
        self,
        subject: Mapping[str, Any] | ValidationSponsorshipSubject,
    ) -> str:
        payload = (
            subject.to_dict()
            if isinstance(subject, ValidationSponsorshipSubject)
            else ValidationSponsorshipSubject.from_mapping(subject).to_dict()
        )
        return "validation_sponsorship_" + _fingerprint({
            key: payload[key]
            for key in (
                "evidence_need_id",
                "target_type",
                "capability_id",
                "claim_id",
                "claim_subject_ref",
                "need_type",
                "validation_scope",
            )
        })[:16]

    def candidate_from_current_need(
        self,
        evidence_need_id: str,
        *,
        validation_scope: str | None = None,
        producer: str = "CurrentEvidenceNeedAuthorityEngine",
        existing_plan_index: Iterable[Mapping[str, Any]] | None = None,
        pending_work_index: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if producer not in ALLOWED_PRODUCERS:
            return self._rejected_candidate(
                producer=producer,
                reason="DENIED_WRONG_AUTHORITY",
            )
        need_state = self.need_authority.get_current_evidence_need_state(
            evidence_need_id
        )
        if not need_state or not need_state.get("is_current"):
            return self._rejected_candidate(
                producer=producer,
                reason="DENIED_NO_CURRENT_EVIDENCE_NEED",
                evidence_need_id=evidence_need_id,
            )
        subject = ValidationSponsorshipSubject.from_need_state(
            need_state,
            validation_scope=validation_scope,
        )
        return self.propose_candidate(
            subject=subject.to_dict(),
            sponsorship_reason="active_current_evidence_need",
            producer=producer,
            source_need_state=need_state,
            existing_plan_index=existing_plan_index,
            pending_work_index=pending_work_index,
        )

    def propose_candidate(
        self,
        *,
        subject: Mapping[str, Any],
        sponsorship_reason: str,
        producer: str,
        source_need_state: Mapping[str, Any] | None = None,
        existing_plan_index: Iterable[Mapping[str, Any]] | None = None,
        pending_work_index: Iterable[Mapping[str, Any]] | None = None,
        urgency: str = "ADVISORY",
        severity: str = "ADVISORY",
    ) -> dict[str, Any]:
        subject_payload = ValidationSponsorshipSubject.from_mapping(subject).to_dict()
        sponsorship_id = self.validation_sponsorship_id(subject_payload)
        need_state = _copy_mapping(source_need_state)
        candidate = {
            "schema_version": self.schema_version,
            "system": "validation_sponsorship_candidate",
            "validation_sponsorship_id": sponsorship_id,
            "evidence_need_id": subject_payload.get("evidence_need_id"),
            "evidence_need_decision_id": subject_payload.get(
                "evidence_need_decision_id"
            ),
            "source_need_state_fingerprint": need_state.get("state_fingerprint"),
            "subject": subject_payload,
            "need_type": subject_payload.get("need_type"),
            "requested_validation_scope": subject_payload.get("validation_scope"),
            "sponsorship_reason": str(sponsorship_reason or "UNKNOWN"),
            "producer": str(producer or "UNKNOWN"),
            "provenance": {
                "source": "current_evidence_need",
                "source_evidence_need_id": subject_payload.get("evidence_need_id"),
                "source_evidence_need_decision_id": subject_payload.get(
                    "evidence_need_decision_id"
                ),
            },
            "priority_metadata": {
                "urgency": str(urgency or "ADVISORY"),
                "severity": str(severity or "ADVISORY"),
                "task_ranking_authority": "NONE",
            },
            "existing_plan_matches": [dict(item) for item in existing_plan_index or []],
            "pending_work_matches": [dict(item) for item in pending_work_index or []],
            "candidate_authority": self.candidate_authority,
            "authority": self.candidate_authority,
            "validation_request_created": False,
            "evidence_plan_created": False,
            "validation_schedule_created": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
            "qualification_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
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
        duplicate = self.is_validation_sponsorship_current(
            candidate.get("validation_sponsorship_id")
        )
        existing_plan = bool(candidate.get("existing_plan_matches"))
        if existing_plan:
            failures.append("plan_already_covers_need")
        pending_work = bool(candidate.get("pending_work_matches"))
        if pending_work:
            failures.append("pending_work_already_covers_need")
        assessment = {
            "schema_version": self.schema_version,
            "system": "validation_sponsorship_assessment",
            "validation_sponsorship_id": candidate.get(
                "validation_sponsorship_id"
            ),
            "evidence_need_id": candidate.get("evidence_need_id"),
            "evidence_need_decision_id": candidate.get("evidence_need_decision_id"),
            "subject": candidate.get("subject"),
            "validation_scope": candidate.get("requested_validation_scope"),
            "current_need_valid": "source_need_not_current" not in failures,
            "need_type_supported": "unsupported_need_type" not in failures,
            "validation_scope_valid": "invalid_validation_scope" not in failures,
            "canonical_target_resolved": "missing_capability_id" not in failures,
            "current_equivalent_sponsorship_exists": duplicate,
            "current_equivalent_plan_exists": existing_plan,
            "pending_work_exists": pending_work,
            "governance_allows": "governance_block" not in failures,
            "need_still_unresolved": "source_need_not_current" not in failures,
            "assessment_failures": sorted(set(failures)),
            "assessment_state": (
                "SPONSORSHIP_ASSESSMENT_ACCEPTED"
                if not failures
                else "SPONSORSHIP_ASSESSMENT_DENIED"
            ),
            "authority": self.assessment_authority,
            "validation_request_created": False,
            "evidence_plan_created": False,
            "created_at": _now(),
        }
        assessment["assessment_fingerprint"] = _fingerprint(
            self._assessment_fingerprint_payload(assessment)
        )
        return assessment

    def decide_sponsorship(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        self.initialize()
        candidate = _copy_mapping(candidate)
        assessment = self.assess_candidate(candidate)
        previous = self.get_current_validation_sponsorship(
            candidate.get("validation_sponsorship_id")
        )
        if assessment.get("assessment_failures"):
            reason = ";".join(assessment["assessment_failures"])
            status = ValidationSponsorshipStatus.INVALIDATED.value
            decision_state = self._denied_state(reason)
        elif previous and previous.get("lifecycle_status") == "ACTIVE":
            reason = "CURRENT_SPONSORSHIP_ALREADY_ACTIVE"
            status = ValidationSponsorshipStatus.ACTIVE.value
            decision_state = "CURRENT_SPONSORSHIP_ALREADY_ACTIVE"
        else:
            reason = "active_current_need_permitted_for_validation_orchestration"
            status = ValidationSponsorshipStatus.ACTIVE.value
            decision_state = "VALIDATION_SPONSORSHIP_ACTIVE"
        return self._persist_decision(
            validation_sponsorship_id=candidate.get("validation_sponsorship_id"),
            evidence_need_id=candidate.get("evidence_need_id"),
            evidence_need_decision_id=candidate.get("evidence_need_decision_id"),
            source_need_state_fingerprint=candidate.get(
                "source_need_state_fingerprint"
            ),
            subject=candidate.get("subject"),
            validation_scope=candidate.get("requested_validation_scope"),
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

    def consume_sponsorship(
        self,
        validation_sponsorship_id: str,
        *,
        consumer: str,
        consumption_reason: str = "governed_downstream_consumption",
    ) -> dict[str, Any]:
        state = self.get_current_validation_sponsorship(validation_sponsorship_id)
        if not state:
            return self._invalid_transition(
                validation_sponsorship_id,
                "DENIED_SPONSORSHIP_NOT_FOUND",
                reason="sponsorship_not_found",
            )
        return self._transition(
            state,
            decision_state="VALIDATION_SPONSORSHIP_CONSUMED",
            lifecycle_status=ValidationSponsorshipStatus.CONSUMED.value,
            reason=consumption_reason,
            provenance={"consumer": consumer},
        )

    def open_review(self, validation_sponsorship_id: str, *, review_reason: str) -> dict[str, Any]:
        state = self.get_current_validation_sponsorship(validation_sponsorship_id)
        if not state:
            return self._invalid_transition(
                validation_sponsorship_id,
                "DENIED_SPONSORSHIP_NOT_FOUND",
                reason="sponsorship_not_found",
            )
        return self._transition(
            state,
            decision_state="VALIDATION_SPONSORSHIP_UNDER_REVIEW",
            lifecycle_status=ValidationSponsorshipStatus.UNDER_REVIEW.value,
            reason=review_reason,
        )

    def revoke_sponsorship(
        self,
        validation_sponsorship_id: str,
        *,
        revocation_reason: str,
    ) -> dict[str, Any]:
        state = self.get_current_validation_sponsorship(validation_sponsorship_id)
        if not state:
            return self._invalid_transition(
                validation_sponsorship_id,
                "DENIED_SPONSORSHIP_NOT_FOUND",
                reason="sponsorship_not_found",
            )
        return self._transition(
            state,
            decision_state="VALIDATION_SPONSORSHIP_REVOKED",
            lifecycle_status=ValidationSponsorshipStatus.REVOKED.value,
            reason=revocation_reason,
        )

    def supersede_sponsorship(
        self,
        validation_sponsorship_id: str,
        *,
        replacement_validation_sponsorship_id: str,
        supersession_reason: str,
    ) -> dict[str, Any]:
        state = self.get_current_validation_sponsorship(validation_sponsorship_id)
        if not state:
            return self._invalid_transition(
                validation_sponsorship_id,
                "DENIED_SPONSORSHIP_NOT_FOUND",
                reason="sponsorship_not_found",
            )
        return self._transition(
            state,
            decision_state="VALIDATION_SPONSORSHIP_SUPERSEDED",
            lifecycle_status=ValidationSponsorshipStatus.SUPERSEDED.value,
            reason=supersession_reason,
            provenance={
                "replacement_validation_sponsorship_id": replacement_validation_sponsorship_id
            },
        )

    def expire_sponsorship(
        self,
        validation_sponsorship_id: str,
        *,
        expiration_reason: str,
    ) -> dict[str, Any]:
        state = self.get_current_validation_sponsorship(validation_sponsorship_id)
        if not state:
            return self._invalid_transition(
                validation_sponsorship_id,
                "DENIED_SPONSORSHIP_NOT_FOUND",
                reason="sponsorship_not_found",
            )
        return self._transition(
            state,
            decision_state="VALIDATION_SPONSORSHIP_EXPIRED",
            lifecycle_status=ValidationSponsorshipStatus.EXPIRED.value,
            reason=expiration_reason,
        )

    def get_current_validation_sponsorship(
        self,
        validation_sponsorship_id: str,
    ) -> dict[str, Any] | None:
        if _missing(validation_sponsorship_id):
            return None
        path = self.current_dir / f"{validation_sponsorship_id}.json"
        if not path.exists():
            return None
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return None
        if not isinstance(state, dict):
            return None
        valid = self._state_integrity_valid(state)
        need_current = self._source_need_dependency_valid(state)
        return {
            **state,
            "currentness_integrity_state": "VALID" if valid else "INVALID",
            "source_need_currentness_state": (
                "CURRENT" if need_current else "NOT_CURRENT"
            ),
            "is_current": bool(
                valid
                and need_current
                and state.get("lifecycle_status")
                == ValidationSponsorshipStatus.ACTIVE.value
            ),
        }

    def get_validation_sponsorship_history(
        self,
        validation_sponsorship_id: str,
    ) -> list[dict[str, Any]]:
        path = self.history_dir / f"{validation_sponsorship_id}.json"
        if not path.exists():
            return []
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return []
        return rows if isinstance(rows, list) else []

    def is_validation_sponsorship_current(
        self,
        validation_sponsorship_id: str,
        *,
        expected_evidence_need_id: str | None = None,
        expected_capability_id: str | None = None,
        expected_claim_id: str | None = None,
        expected_need_type: str | None = None,
        expected_validation_scope: str | None = None,
    ) -> bool:
        state = self.get_current_validation_sponsorship(validation_sponsorship_id)
        if not state or not state.get("is_current"):
            return False
        subject = _copy_mapping(state.get("subject"))
        if expected_evidence_need_id and state.get("evidence_need_id") != expected_evidence_need_id:
            return False
        if expected_capability_id and subject.get("capability_id") != expected_capability_id:
            return False
        if expected_claim_id and subject.get("claim_id") != expected_claim_id:
            return False
        if expected_need_type and subject.get("need_type") != expected_need_type:
            return False
        if expected_validation_scope and state.get("validation_scope") != expected_validation_scope:
            return False
        return True

    def list_current_validation_sponsorships(
        self,
        *,
        include_non_active: bool = False,
    ) -> list[dict[str, Any]]:
        if not self.current_dir.exists():
            return []
        rows = []
        for path in sorted(self.current_dir.glob("*.json")):
            state = self.get_current_validation_sponsorship(path.stem)
            if state and (include_non_active or state.get("is_current")):
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
            validation_sponsorship_id=state.get("validation_sponsorship_id"),
            evidence_need_id=state.get("evidence_need_id"),
            evidence_need_decision_id=state.get("evidence_need_decision_id"),
            source_need_state_fingerprint=state.get("source_need_state_fingerprint"),
            subject=state.get("subject"),
            validation_scope=state.get("validation_scope"),
            decision_state=decision_state,
            lifecycle_status=lifecycle_status,
            reason=reason,
            previous_state=state,
            provenance=dict(provenance or {}),
        )

    def _persist_decision(
        self,
        *,
        validation_sponsorship_id: str,
        evidence_need_id: str,
        evidence_need_decision_id: str,
        source_need_state_fingerprint: str | None,
        subject: Mapping[str, Any] | None,
        validation_scope: str | None,
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
            "system": "validation_sponsorship_decision",
            "validation_sponsorship_decision_id": "pending",
            "validation_sponsorship_id": validation_sponsorship_id,
            "previous_decision_id": previous_state.get("current_decision_id"),
            "evidence_need_id": evidence_need_id,
            "evidence_need_decision_id": evidence_need_decision_id,
            "source_need_state_fingerprint": source_need_state_fingerprint,
            "subject": dict(subject or {}),
            "validation_scope": validation_scope,
            "decision_state": decision_state,
            "lifecycle_status": lifecycle_status,
            "reason": reason,
            "authority": self.authority,
            "provenance": dict(provenance or {}),
            "assessment": dict(assessment or {}),
            "validation_request_created": False,
            "evidence_plan_created": False,
            "validation_schedule_created": False,
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
        decision["validation_sponsorship_decision_id"] = (
            "validation_sponsorship_decision_"
            f"{decision['decision_fingerprint'][:16]}"
        )
        state = self._state_from_decision(decision)
        self._write_json(
            self.decisions_dir
            / f"{decision['validation_sponsorship_decision_id']}.json",
            decision,
        )
        self._write_json(
            self.current_dir / f"{validation_sponsorship_id}.json",
            state,
        )
        history = self.get_validation_sponsorship_history(validation_sponsorship_id)
        history.append({
            "event_type": "VALIDATION_SPONSORSHIP_DECISION",
            "decision": decision,
            "resulting_state": state,
        })
        self._write_json(
            self.history_dir / f"{validation_sponsorship_id}.json",
            history,
        )
        return {
            "decision": decision,
            "current_state": state,
            "assessment": dict(assessment or {}),
            "authority": self.authority,
            "validation_request_created": False,
            "evidence_plan_created": False,
            "validation_schedule_created": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
        }

    def _state_from_decision(self, decision: Mapping[str, Any]) -> dict[str, Any]:
        state = {
            "schema_version": self.schema_version,
            "system": "validation_sponsorship_state",
            "validation_sponsorship_id": decision.get("validation_sponsorship_id"),
            "current_decision_id": decision.get("validation_sponsorship_decision_id"),
            "previous_decision_id": decision.get("previous_decision_id"),
            "evidence_need_id": decision.get("evidence_need_id"),
            "evidence_need_decision_id": decision.get("evidence_need_decision_id"),
            "source_need_state_fingerprint": decision.get(
                "source_need_state_fingerprint"
            ),
            "subject": decision.get("subject", {}),
            "validation_scope": decision.get("validation_scope"),
            "decision_state": decision.get("decision_state"),
            "lifecycle_status": decision.get("lifecycle_status"),
            "reason": decision.get("reason"),
            "authority": self.authority,
            "state_authority": self.authority,
            "decision_fingerprint": decision.get("decision_fingerprint"),
            "updated_at": decision.get("created_at"),
            "is_actionable_validation_sponsorship": (
                decision.get("lifecycle_status")
                == ValidationSponsorshipStatus.ACTIVE.value
            ),
            "validation_request_created": False,
            "evidence_plan_created": False,
            "validation_schedule_created": False,
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
            failures.append("missing_sponsorship_subject")
        if _missing(subject.get("capability_id")):
            failures.append("missing_capability_id")
        need_type = str(candidate.get("need_type") or subject.get("need_type") or "")
        scope = str(candidate.get("requested_validation_scope") or "")
        if need_type not in NEED_TYPE_TO_SCOPE:
            failures.append("unsupported_need_type")
        elif NEED_TYPE_TO_SCOPE[need_type] != scope:
            failures.append("invalid_validation_scope")
        need_state = self.need_authority.get_current_evidence_need_state(
            candidate.get("evidence_need_id")
        )
        if not need_state or not need_state.get("is_current"):
            failures.append("source_need_not_current")
        else:
            if need_state.get("current_decision_id") != candidate.get(
                "evidence_need_decision_id"
            ):
                failures.append("stale_need_decision")
            if need_state.get("state_fingerprint") != candidate.get(
                "source_need_state_fingerprint"
            ):
                failures.append("source_need_fingerprint_mismatch")
            need_subject = _copy_mapping(need_state.get("subject"))
            if need_subject.get("capability_id") != subject.get("capability_id"):
                failures.append("cross_capability_sponsorship")
            if (
                not _missing(need_subject.get("claim_id"))
                and need_subject.get("claim_id") != subject.get("claim_id")
            ):
                failures.append("cross_claim_sponsorship")
            if need_state.get("need_type") != need_type:
                failures.append("cross_need_type_sponsorship")
        expected_id = None
        if subject:
            try:
                expected_id = self.validation_sponsorship_id(subject)
            except ValidationSponsorshipError:
                expected_id = None
        if expected_id and candidate.get("validation_sponsorship_id") != expected_id:
            failures.append("validation_sponsorship_id_mismatch")
        expected_fp = _fingerprint(self._candidate_fingerprint_payload(candidate))
        if candidate.get("candidate_fingerprint") != expected_fp:
            failures.append("candidate_fingerprint_invalid")
        return failures

    def _source_need_dependency_valid(self, state: Mapping[str, Any]) -> bool:
        need_state = self.need_authority.get_current_evidence_need_state(
            state.get("evidence_need_id")
        )
        if not need_state or not need_state.get("is_current"):
            return False
        return (
            need_state.get("current_decision_id")
            == state.get("evidence_need_decision_id")
            and need_state.get("state_fingerprint")
            == state.get("source_need_state_fingerprint")
        )

    def _state_integrity_valid(self, state: Mapping[str, Any]) -> bool:
        if state.get("state_authority") != self.authority:
            return False
        expected = _fingerprint(self._state_fingerprint_payload(state))
        return state.get("state_fingerprint") == expected

    def _invalid_transition(
        self,
        validation_sponsorship_id: str,
        decision_state: str,
        *,
        reason: str,
    ) -> dict[str, Any]:
        return {
            "decision": {
                "validation_sponsorship_id": validation_sponsorship_id,
                "decision_state": decision_state,
                "reason": reason,
                "authority": self.authority,
            },
            "current_state": {},
            "authority": self.authority,
            "validation_request_created": False,
            "evidence_plan_created": False,
            "validation_schedule_created": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
        }

    def _denied_state(self, reason: str) -> str:
        if "wrong_authority" in reason:
            return "DENIED_WRONG_AUTHORITY"
        if "source_need_not_current" in reason:
            return "DENIED_NEED_NOT_CURRENT"
        if "plan_already_covers_need" in reason:
            return "PLAN_ALREADY_COVERS_NEED"
        if "pending_work_already_covers_need" in reason:
            return "PENDING_WORK_ALREADY_COVERS_NEED"
        if "invalid_validation_scope" in reason:
            return "DENIED_INVALID_VALIDATION_SCOPE"
        if "fingerprint" in reason or "mismatch" in reason:
            return "DENIED_SPONSORSHIP_INTEGRITY_FAILURE"
        return "DENIED_VALIDATION_SPONSORSHIP"

    def _candidate_fingerprint_payload(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "validation_sponsorship_id": candidate.get("validation_sponsorship_id"),
            "evidence_need_id": candidate.get("evidence_need_id"),
            "evidence_need_decision_id": candidate.get("evidence_need_decision_id"),
            "source_need_state_fingerprint": candidate.get(
                "source_need_state_fingerprint"
            ),
            "subject": candidate.get("subject"),
            "need_type": candidate.get("need_type"),
            "requested_validation_scope": candidate.get(
                "requested_validation_scope"
            ),
            "sponsorship_reason": candidate.get("sponsorship_reason"),
            "producer": candidate.get("producer"),
            "provenance": candidate.get("provenance", {}),
        }

    def _assessment_fingerprint_payload(self, assessment: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "validation_sponsorship_id": assessment.get("validation_sponsorship_id"),
            "evidence_need_id": assessment.get("evidence_need_id"),
            "validation_scope": assessment.get("validation_scope"),
            "assessment_failures": assessment.get("assessment_failures", []),
            "assessment_state": assessment.get("assessment_state"),
        }

    def _decision_fingerprint_payload(self, decision: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "validation_sponsorship_id": decision.get("validation_sponsorship_id"),
            "previous_decision_id": decision.get("previous_decision_id"),
            "evidence_need_id": decision.get("evidence_need_id"),
            "evidence_need_decision_id": decision.get("evidence_need_decision_id"),
            "source_need_state_fingerprint": decision.get(
                "source_need_state_fingerprint"
            ),
            "subject": decision.get("subject", {}),
            "validation_scope": decision.get("validation_scope"),
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
            "validation_sponsorship_id": state.get("validation_sponsorship_id"),
            "current_decision_id": state.get("current_decision_id"),
            "previous_decision_id": state.get("previous_decision_id"),
            "evidence_need_id": state.get("evidence_need_id"),
            "evidence_need_decision_id": state.get("evidence_need_decision_id"),
            "source_need_state_fingerprint": state.get(
                "source_need_state_fingerprint"
            ),
            "subject": state.get("subject", {}),
            "validation_scope": state.get("validation_scope"),
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
        evidence_need_id: str | None = None,
    ) -> dict[str, Any]:
        candidate = {
            "schema_version": self.schema_version,
            "system": "validation_sponsorship_candidate",
            "validation_sponsorship_id": "Not Available",
            "evidence_need_id": evidence_need_id or "Not Available",
            "evidence_need_decision_id": "Not Available",
            "source_need_state_fingerprint": "Not Available",
            "subject": {},
            "need_type": "Not Available",
            "requested_validation_scope": "Not Available",
            "sponsorship_reason": reason,
            "producer": str(producer or "UNKNOWN"),
            "provenance": {"rejection_reason": reason},
            "candidate_authority": self.candidate_authority,
            "authority": self.candidate_authority,
            "validation_request_created": False,
            "evidence_plan_created": False,
            "validation_schedule_created": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
            "created_at": _now(),
        }
        candidate["candidate_fingerprint"] = _fingerprint(
            self._candidate_fingerprint_payload(candidate)
        )
        return candidate


__all__ = [
    "NEED_TYPE_TO_SCOPE",
    "ValidationSponsorshipAuthorityEngine",
    "ValidationSponsorshipError",
    "ValidationSponsorshipScope",
    "ValidationSponsorshipStatus",
    "ValidationSponsorshipSubject",
]
