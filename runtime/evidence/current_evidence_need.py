from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping


UNKNOWN = {"", "NONE", "None", "Not Available", "UNKNOWN", "null", "NULL"}


class EvidenceNeedType(str, Enum):
    GENERAL_SUPPORT_REQUIRED = "GENERAL_SUPPORT_REQUIRED"
    SOURCE_INDEPENDENCE_REQUIRED = "SOURCE_INDEPENDENCE_REQUIRED"
    CAUSAL_SUPPORT_REQUIRED = "CAUSAL_SUPPORT_REQUIRED"
    REPRODUCIBILITY_REQUIRED = "REPRODUCIBILITY_REQUIRED"
    CONTRADICTION_RESOLUTION_REQUIRED = "CONTRADICTION_RESOLUTION_REQUIRED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    CANDIDATE_DISAMBIGUATION_REQUIRED = "CANDIDATE_DISAMBIGUATION_REQUIRED"


class EvidenceNeedLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    SATISFIED = "SATISFIED"
    INVALIDATED = "INVALIDATED"
    SUPERSEDED = "SUPERSEDED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"


class DeficitSignalType(str, Enum):
    QUALIFICATION_DEFICIT = "QUALIFICATION_DEFICIT"
    SOURCE_INDEPENDENCE_DEFICIT = "SOURCE_INDEPENDENCE_DEFICIT"
    CAUSAL_SUPPORT_DEFICIT = "CAUSAL_SUPPORT_DEFICIT"
    REPRODUCIBILITY_DEFICIT = "REPRODUCIBILITY_DEFICIT"
    CONTRADICTION_RESOLUTION_DEFICIT = "CONTRADICTION_RESOLUTION_DEFICIT"
    REVALIDATION_DEFICIT = "REVALIDATION_DEFICIT"
    GENERAL_SUPPORT_DEFICIT = "GENERAL_SUPPORT_DEFICIT"
    CANDIDATE_DISAMBIGUATION_DEFICIT = "CANDIDATE_DISAMBIGUATION_DEFICIT"
    NOT_ELIGIBLE_FOR_NEED_PROPOSAL = "NOT_ELIGIBLE_FOR_NEED_PROPOSAL"


NEED_TYPE_TO_SUPPORT_CLASS = {
    EvidenceNeedType.GENERAL_SUPPORT_REQUIRED.value: "current_governed_support",
    EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value: (
        "provenance_derived_independent_source_support"
    ),
    EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value: "explicit_causal_support",
    EvidenceNeedType.REPRODUCIBILITY_REQUIRED.value: (
        "independent_causal_replication_support"
    ),
    EvidenceNeedType.CONTRADICTION_RESOLUTION_REQUIRED.value: (
        "governed_contradiction_resolution_support"
    ),
    EvidenceNeedType.REVALIDATION_REQUIRED.value: (
        "fresh_governed_revalidation_support"
    ),
    EvidenceNeedType.CANDIDATE_DISAMBIGUATION_REQUIRED.value: (
        "candidate_disambiguation_validation_support"
    ),
}


ALLOWED_PRODUCERS = {
    "IntegratedCapabilityQualificationEngine",
    "CapabilityEvidenceAssessment",
    "AcceptedEvidenceLifecycleEngine",
    "EvidenceSourceIndependenceEngine",
    "AcceptedEvidenceEpistemicAssessmentEngine",
    "TruthCurrentAuthorityLifecycle",
    "KnowledgeCurrentAuthority",
    "CurrentEvidenceNeedAuthorityEngine",
    "CandidateDisambiguationEvidenceLayer",
}


NEED_TYPES_BY_FAILURE = {
    "accepted_evidence_missing": [EvidenceNeedType.GENERAL_SUPPORT_REQUIRED.value],
    "architecture_presence_not_established": [
        EvidenceNeedType.GENERAL_SUPPORT_REQUIRED.value
    ],
    "runtime_reachability_not_established": [
        EvidenceNeedType.GENERAL_SUPPORT_REQUIRED.value
    ],
    "independent_reproducibility_not_established": [
        EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value,
        EvidenceNeedType.REPRODUCIBILITY_REQUIRED.value,
    ],
    "causal_support_not_established": [
        EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value
    ],
    "some_evidence_rejected": [
        EvidenceNeedType.CONTRADICTION_RESOLUTION_REQUIRED.value
    ],
}


class CurrentEvidenceNeedError(ValueError):
    """Raised when a need payload cannot be interpreted safely."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _fingerprint(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def _term(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "Not Available"


def _missing(value: Any) -> bool:
    return str(value or "").strip() in UNKNOWN


def _copy_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


class EvidenceNeedSubject:
    """Canonical semantic subject for current evidence-need identity."""

    schema_version = "1.0"

    def __init__(
        self,
        *,
        target_type: str,
        capability_id: str,
        qualification_subject_id: str | None = None,
        claim_id: str | None = None,
        claim_subject_ref: Mapping[str, Any] | str | None = None,
        domain: str | None = None,
        context_class: str | None = None,
        evidence_scope: str | None = None,
        capability_subject: Mapping[str, Any] | None = None,
        qualification_target_level: str | None = None,
        current_qualification_level: str | None = None,
        required_independent_sources: int | None = None,
    ) -> None:
        if _missing(target_type):
            raise CurrentEvidenceNeedError("missing_target_type")
        if _missing(capability_id):
            raise CurrentEvidenceNeedError("missing_capability_id")
        self.payload = {
            "schema_version": self.schema_version,
            "target_type": _term(target_type),
            "capability_id": _term(capability_id),
            "qualification_subject_id": _term(qualification_subject_id),
            "claim_id": _term(claim_id),
            "claim_subject_ref": (
                dict(claim_subject_ref)
                if isinstance(claim_subject_ref, Mapping)
                else _term(claim_subject_ref)
            ),
            "domain": _term(domain),
            "context_class": _term(context_class),
            "evidence_scope": _term(evidence_scope),
            "capability_subject": (
                dict(capability_subject)
                if isinstance(capability_subject, Mapping)
                else {}
            ),
            "qualification_target_level": _term(qualification_target_level),
            "current_qualification_level": _term(current_qualification_level),
            "required_independent_sources": (
                int(required_independent_sources)
                if required_independent_sources is not None
                else 0
            ),
        }
        self.payload["subject_id"] = (
            "evidence_need_subject_"
            f"{_fingerprint(self.semantic_identity())[:16]}"
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EvidenceNeedSubject":
        return cls(
            target_type=value.get("target_type"),
            capability_id=value.get("capability_id"),
            qualification_subject_id=value.get("qualification_subject_id"),
            claim_id=value.get("claim_id"),
            claim_subject_ref=value.get("claim_subject_ref")
            or value.get("claim_subject"),
            domain=value.get("domain"),
            context_class=value.get("context_class"),
            evidence_scope=value.get("evidence_scope"),
            capability_subject=value.get("capability_subject"),
            qualification_target_level=value.get("qualification_target_level"),
            current_qualification_level=value.get("current_qualification_level"),
            required_independent_sources=value.get("required_independent_sources"),
        )

    @classmethod
    def from_qualification(
        cls,
        qualification_result: Mapping[str, Any],
    ) -> "EvidenceNeedSubject":
        decision = _copy_mapping(qualification_result.get("qualification_decision"))
        assessment = _copy_mapping(
            qualification_result.get("capability_evidence_assessment")
        )
        subject = _copy_mapping(
            decision.get("capability_subject")
            or assessment.get("capability_subject")
        )
        capability_id = decision.get("capability_id") or assessment.get(
            "capability_id"
        )
        claim_subject = None
        accepted_refs = assessment.get("supporting_accepted_evidence_refs") or []
        if accepted_refs and isinstance(accepted_refs[0], Mapping):
            claim_subject = accepted_refs[0].get("claim_subject")
        return cls(
            target_type="capability",
            capability_id=capability_id,
            qualification_subject_id=subject.get("subject_id")
            or subject.get("capability_subject_id")
            or capability_id,
            claim_id=(
                accepted_refs[0].get("claim_id")
                if accepted_refs and isinstance(accepted_refs[0], Mapping)
                else None
            ),
            claim_subject_ref=claim_subject,
            domain=subject.get("domain"),
            context_class=subject.get("context_class") or "qualification",
            evidence_scope=subject.get("evidence_scope") or "capability_support",
            capability_subject=subject,
            qualification_target_level=decision.get("requested_level"),
            current_qualification_level=decision.get("current_level"),
            required_independent_sources=assessment.get(
                "required_independent_sources"
            ),
        )

    def semantic_identity(self) -> dict[str, Any]:
        return {
            key: self.payload[key]
            for key in (
                "target_type",
                "capability_id",
                "qualification_subject_id",
                "claim_id",
                "claim_subject_ref",
                "domain",
                "context_class",
                "evidence_scope",
            )
        }

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


class CurrentEvidenceNeedAuthorityEngine:
    """Single authority for deciding current evidence-need state."""

    schema_version = "1.0"
    authority = "CURRENT_EVIDENCE_NEED_AUTHORITY_ENGINE"
    candidate_authority = "NONE"
    assessment_authority = "NONE"

    def __init__(
        self,
        state_dir: str | os.PathLike[str] = "runtime/state/current_evidence_needs",
    ) -> None:
        self.state_dir = Path(state_dir)
        self.decisions_dir = self.state_dir / "decisions"
        self.current_dir = self.state_dir / "current"
        self.history_dir = self.state_dir / "history"
        self.invalid_dir = self.state_dir / "invalid"

    def initialize(self) -> None:
        for path in (
            self.decisions_dir,
            self.current_dir,
            self.history_dir,
            self.invalid_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def evidence_need_id(
        self,
        subject: Mapping[str, Any] | EvidenceNeedSubject,
        need_type: str,
        required_support_class: str | None = None,
    ) -> str:
        subject_payload = (
            subject.to_dict()
            if isinstance(subject, EvidenceNeedSubject)
            else EvidenceNeedSubject.from_mapping(subject).to_dict()
        )
        need_type = self._need_type(need_type)
        identity = {
            "subject": {
                key: subject_payload[key]
                for key in (
                    "target_type",
                    "capability_id",
                    "qualification_subject_id",
                    "claim_id",
                    "claim_subject_ref",
                    "domain",
                    "context_class",
                    "evidence_scope",
                )
            },
            "need_type": need_type,
            "required_support_class": (
                required_support_class or NEED_TYPE_TO_SUPPORT_CLASS[need_type]
            ),
        }
        return f"current_evidence_need_{_fingerprint(identity)[:16]}"

    def candidate_from_qualification_deficit(
        self,
        qualification_result: Mapping[str, Any],
        *,
        need_type: str | None = None,
        producer: str = "IntegratedCapabilityQualificationEngine",
    ) -> dict[str, Any]:
        candidates = self.candidates_from_qualification_deficit(
            qualification_result,
            producer=producer,
        )
        if need_type is None:
            if not candidates:
                raise CurrentEvidenceNeedError("no_qualification_deficit_candidate")
            return candidates[0]
        resolved = self._need_type(need_type)
        for candidate in candidates:
            if candidate.get("need_type") == resolved:
                return candidate
        raise CurrentEvidenceNeedError("requested_need_type_not_proposed")

    def candidates_from_qualification_deficit(
        self,
        qualification_result: Mapping[str, Any],
        *,
        producer: str = "IntegratedCapabilityQualificationEngine",
    ) -> list[dict[str, Any]]:
        if producer not in ALLOWED_PRODUCERS:
            return [
                self._rejected_candidate(
                    producer=producer,
                    reason="DENIED_UNAUTHORIZED_NEED_PRODUCER",
                )
            ]
        result = _copy_mapping(qualification_result)
        decision = _copy_mapping(result.get("qualification_decision"))
        assessment = _copy_mapping(result.get("capability_evidence_assessment"))
        failures = [
            str(item)
            for item in decision.get("promotion_failures", []) or []
            if item in NEED_TYPES_BY_FAILURE
        ]
        if not failures:
            return [
                self._rejected_candidate(
                    producer=producer,
                    reason="DENIED_NO_GOVERNED_DEFICIT_SOURCE",
                )
            ]
        subject = EvidenceNeedSubject.from_qualification(result)
        candidates = []
        for failure in sorted(set(failures)):
            for need_type in NEED_TYPES_BY_FAILURE[failure]:
                candidate = self.propose_candidate(
                    subject=subject.to_dict(),
                    need_type=need_type,
                    deficit_signal_type=self._deficit_signal_type(failure, need_type),
                    source_deficit_refs=[
                        {
                            "source_decision_id": decision.get(
                                "qualification_decision_id"
                            ),
                            "source_assessment_id": assessment.get(
                                "capability_evidence_assessment_id"
                            ),
                            "source_failure": failure,
                            "source_authority": decision.get(
                                "qualification_authority"
                            ),
                        }
                    ],
                    current_support_summary={
                        "valid_accepted_evidence_count": assessment.get(
                            "valid_accepted_evidence_count", 0
                        ),
                        "independent_source_count": assessment.get(
                            "independent_source_count", 0
                        ),
                        "required_independent_sources": assessment.get(
                            "required_independent_sources", 0
                        ),
                        "causal_support_state": assessment.get(
                            "causal_support_state"
                        ),
                        "reproducibility_state": assessment.get(
                            "reproducibility_state"
                        ),
                        "blocking_rejected_evidence_count": assessment.get(
                            "blocking_rejected_evidence_count", 0
                        ),
                    },
                    proposal_reason=failure,
                    producer=producer,
                    provenance={
                        "source": "qualification_deficit",
                        "qualification_decision_id": decision.get(
                            "qualification_decision_id"
                        ),
                        "capability_evidence_assessment_id": assessment.get(
                            "capability_evidence_assessment_id"
                        ),
                        "source_deficit_current": bool(
                            decision.get("decision_state") == "PROMOTION_DENIED"
                        ),
                        "source_decision_fingerprint": decision.get(
                            "decision_fingerprint"
                        ),
                        "assessment_run_id": assessment.get("assessment_run_id"),
                    },
                )
                candidates.append(candidate)
        return candidates

    def propose_candidate(
        self,
        *,
        subject: Mapping[str, Any],
        need_type: str,
        deficit_signal_type: str,
        source_deficit_refs: Iterable[Mapping[str, Any]] | None,
        current_support_summary: Mapping[str, Any] | None = None,
        proposal_reason: str = "governed_deficit_signal",
        producer: str = "CurrentEvidenceNeedAuthorityEngine",
        provenance: Mapping[str, Any] | None = None,
        severity: str = "ADVISORY",
        blocking_state: str = "UNKNOWN",
        urgency: str = "UNKNOWN",
    ) -> dict[str, Any]:
        subject_payload = EvidenceNeedSubject.from_mapping(subject).to_dict()
        need_type = self._need_type(need_type)
        required_support_class = NEED_TYPE_TO_SUPPORT_CLASS[need_type]
        evidence_need_id = self.evidence_need_id(
            subject_payload,
            need_type,
            required_support_class,
        )
        payload = {
            "schema_version": self.schema_version,
            "system": "current_evidence_need_candidate",
            "evidence_need_id": evidence_need_id,
            "subject": subject_payload,
            "need_type": need_type,
            "deficit_signal_type": self._deficit_signal_type_value(
                deficit_signal_type
            ),
            "source_deficit_refs": [
                dict(item) for item in source_deficit_refs or []
            ],
            "required_support_class": required_support_class,
            "current_support_summary": dict(current_support_summary or {}),
            "proposal_reason": str(proposal_reason or "governed_deficit_signal"),
            "producer": str(producer or "UNKNOWN"),
            "provenance": dict(provenance or {}),
            "priority_metadata": {
                "severity": str(severity or "ADVISORY"),
                "blocking_state": str(blocking_state or "UNKNOWN"),
                "urgency": str(urgency or "UNKNOWN"),
                "task_selection_authority": "NONE",
            },
            "candidate_authority": self.candidate_authority,
            "authority": self.candidate_authority,
            "validation_sponsorship_created": False,
            "validation_request_created": False,
            "evidence_plan_created": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
            "qualification_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "created_at": _now(),
        }
        payload["candidate_fingerprint"] = _fingerprint(
            self._candidate_fingerprint_payload(payload)
        )
        return payload

    def assess_candidate(
        self,
        candidate: Mapping[str, Any],
        *,
        current_support_summary: Mapping[str, Any] | None = None,
        current_source_decision_id: str | None = None,
    ) -> dict[str, Any]:
        candidate = _copy_mapping(candidate)
        failures = self._candidate_failures(
            candidate,
            current_source_decision_id=current_source_decision_id,
        )
        support = dict(
            current_support_summary
            if current_support_summary is not None
            else candidate.get("current_support_summary") or {}
        )
        support_sufficient = self._support_satisfies(
            candidate.get("need_type"),
            support,
        )
        if support_sufficient:
            failures.append("support_already_sufficient")
        assessment = {
            "schema_version": self.schema_version,
            "system": "evidence_need_assessment",
            "evidence_need_id": candidate.get("evidence_need_id"),
            "candidate_fingerprint": candidate.get("candidate_fingerprint"),
            "subject": candidate.get("subject"),
            "need_type": candidate.get("need_type"),
            "source_deficit_refs": candidate.get("source_deficit_refs", []),
            "canonical_subject_valid": (
                "missing_evidence_need_subject" not in failures
                and "missing_capability_id" not in failures
            ),
            "deficit_source_valid": (
                "denied_unauthorized_need_producer" not in failures
                and "missing_governed_deficit_source" not in failures
            ),
            "deficit_still_current": "stale_deficit" not in failures,
            "target_exists": "missing_capability_id" not in failures,
            "support_already_sufficient": support_sufficient,
            "need_type_justified": (
                "unsupported_need_type" not in failures
                and "need_type_not_supported_by_deficit" not in failures
            ),
            "contradiction_present": bool(
                support.get("contradiction_present")
                or support.get("blocking_rejected_evidence_count")
            ),
            "current_lifecycle_states_valid": (
                "invalid_source_lifecycle_state" not in failures
            ),
            "source_decision_current": "stale_deficit" not in failures,
            "duplicate_current_need_exists": self.is_evidence_need_current(
                candidate.get("evidence_need_id")
            ),
            "assessment_failures": sorted(set(failures)),
            "assessment_state": (
                "NEED_ASSESSMENT_ACCEPTED"
                if not failures
                else "NEED_ASSESSMENT_DENIED"
            ),
            "authority": self.assessment_authority,
            "validation_sponsorship_created": False,
            "evidence_plan_created": False,
            "created_at": _now(),
        }
        assessment["assessment_fingerprint"] = _fingerprint(
            self._assessment_fingerprint_payload(assessment)
        )
        return assessment

    def decide_current_need(
        self,
        candidate: Mapping[str, Any],
        *,
        current_support_summary: Mapping[str, Any] | None = None,
        current_source_decision_id: str | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        candidate = _copy_mapping(candidate)
        assessment = self.assess_candidate(
            candidate,
            current_support_summary=current_support_summary,
            current_source_decision_id=current_source_decision_id,
        )
        previous = self.get_current_evidence_need_state(
            candidate.get("evidence_need_id")
        )
        if assessment.get("assessment_failures"):
            reason = ";".join(assessment["assessment_failures"])
            state = EvidenceNeedLifecycleStatus.INVALIDATED.value
            decision_state = self._denied_state(reason)
        elif previous and previous.get("lifecycle_status") == (
            EvidenceNeedLifecycleStatus.ACTIVE.value
        ):
            reason = "CURRENT_NEED_ALREADY_ACTIVE"
            state = EvidenceNeedLifecycleStatus.ACTIVE.value
            decision_state = "CURRENT_NEED_ALREADY_ACTIVE"
        else:
            reason = "governed_deficit_current_and_unresolved"
            state = EvidenceNeedLifecycleStatus.ACTIVE.value
            decision_state = "CURRENT_EVIDENCE_NEED_ACTIVE"
        return self._persist_decision(
            evidence_need_id=candidate.get("evidence_need_id"),
            subject=candidate.get("subject"),
            need_type=candidate.get("need_type"),
            source_deficit_refs=candidate.get("source_deficit_refs", []),
            decision_state=decision_state,
            lifecycle_status=state,
            reason=reason,
            assessment=assessment,
            previous_state=previous,
            provenance={
                "candidate_fingerprint": candidate.get("candidate_fingerprint"),
                "producer": candidate.get("producer"),
                "provenance": candidate.get("provenance", {}),
            },
        )

    def satisfy_need(
        self,
        evidence_need_id: str,
        *,
        current_support_summary: Mapping[str, Any],
        reason: str = "support_predicate_satisfied",
    ) -> dict[str, Any]:
        state = self.get_current_evidence_need_state(evidence_need_id)
        if not state:
            return self._invalid_transition(
                evidence_need_id,
                "DENIED_NEED_NOT_FOUND",
                reason="need_not_found",
            )
        if not self._support_satisfies(
            state.get("need_type"),
            current_support_summary,
        ):
            return self._invalid_transition(
                evidence_need_id,
                "DENIED_NO_AUTHORITATIVE_SUPPORT_TRANSITION",
                reason="support_predicate_not_satisfied",
                previous_state=state,
            )
        return self._persist_decision(
            evidence_need_id=evidence_need_id,
            subject=state.get("subject"),
            need_type=state.get("need_type"),
            source_deficit_refs=state.get("source_deficit_refs", []),
            decision_state="CURRENT_EVIDENCE_NEED_SATISFIED",
            lifecycle_status=EvidenceNeedLifecycleStatus.SATISFIED.value,
            reason=reason,
            previous_state=state,
            provenance={
                "current_support_summary": dict(current_support_summary or {}),
            },
        )

    def open_review(
        self,
        evidence_need_id: str,
        *,
        review_reason: str,
        supporting_refs: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        state = self.get_current_evidence_need_state(evidence_need_id)
        if not state:
            return self._invalid_transition(
                evidence_need_id,
                "DENIED_NEED_NOT_FOUND",
                reason="need_not_found",
            )
        return self._persist_decision(
            evidence_need_id=evidence_need_id,
            subject=state.get("subject"),
            need_type=state.get("need_type"),
            source_deficit_refs=state.get("source_deficit_refs", []),
            decision_state="CURRENT_EVIDENCE_NEED_UNDER_REVIEW",
            lifecycle_status=EvidenceNeedLifecycleStatus.UNDER_REVIEW.value,
            reason=review_reason,
            previous_state=state,
            provenance={"supporting_refs": sorted(str(x) for x in supporting_refs or [])},
        )

    def invalidate_need(
        self,
        evidence_need_id: str,
        *,
        invalidation_reason: str,
        supporting_refs: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        state = self.get_current_evidence_need_state(evidence_need_id)
        if not state:
            return self._invalid_transition(
                evidence_need_id,
                "DENIED_NEED_NOT_FOUND",
                reason="need_not_found",
            )
        return self._persist_decision(
            evidence_need_id=evidence_need_id,
            subject=state.get("subject"),
            need_type=state.get("need_type"),
            source_deficit_refs=state.get("source_deficit_refs", []),
            decision_state="CURRENT_EVIDENCE_NEED_INVALIDATED",
            lifecycle_status=EvidenceNeedLifecycleStatus.INVALIDATED.value,
            reason=invalidation_reason,
            previous_state=state,
            provenance={"supporting_refs": sorted(str(x) for x in supporting_refs or [])},
        )

    def supersede_need(
        self,
        evidence_need_id: str,
        *,
        replacement_evidence_need_id: str,
        supersession_reason: str,
    ) -> dict[str, Any]:
        state = self.get_current_evidence_need_state(evidence_need_id)
        if not state:
            return self._invalid_transition(
                evidence_need_id,
                "DENIED_NEED_NOT_FOUND",
                reason="need_not_found",
            )
        return self._persist_decision(
            evidence_need_id=evidence_need_id,
            subject=state.get("subject"),
            need_type=state.get("need_type"),
            source_deficit_refs=state.get("source_deficit_refs", []),
            decision_state="CURRENT_EVIDENCE_NEED_SUPERSEDED",
            lifecycle_status=EvidenceNeedLifecycleStatus.SUPERSEDED.value,
            reason=supersession_reason,
            previous_state=state,
            provenance={"replacement_evidence_need_id": replacement_evidence_need_id},
        )

    def require_revalidation(
        self,
        evidence_need_id: str,
        *,
        revalidation_reason: str,
        supporting_refs: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        state = self.get_current_evidence_need_state(evidence_need_id)
        if not state:
            return self._invalid_transition(
                evidence_need_id,
                "DENIED_NEED_NOT_FOUND",
                reason="need_not_found",
            )
        return self._persist_decision(
            evidence_need_id=evidence_need_id,
            subject=state.get("subject"),
            need_type=state.get("need_type"),
            source_deficit_refs=state.get("source_deficit_refs", []),
            decision_state="CURRENT_EVIDENCE_NEED_REVALIDATION_REQUIRED",
            lifecycle_status=EvidenceNeedLifecycleStatus.REVALIDATION_REQUIRED.value,
            reason=revalidation_reason,
            previous_state=state,
            provenance={"supporting_refs": sorted(str(x) for x in supporting_refs or [])},
        )

    def get_current_evidence_need_state(
        self,
        evidence_need_id: str,
    ) -> dict[str, Any] | None:
        if _missing(evidence_need_id):
            return None
        path = self.current_dir / f"{evidence_need_id}.json"
        if not path.exists():
            return None
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return None
        if not isinstance(state, dict):
            return None
        if not self._state_integrity_valid(state):
            return {
                **state,
                "currentness_integrity_state": "INVALID",
                "is_current": False,
            }
        return {
            **state,
            "currentness_integrity_state": "VALID",
            "is_current": state.get("lifecycle_status")
            == EvidenceNeedLifecycleStatus.ACTIVE.value,
        }

    def get_evidence_need_history(self, evidence_need_id: str) -> list[dict[str, Any]]:
        path = self.history_dir / f"{evidence_need_id}.json"
        if not path.exists():
            return []
        try:
            history = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return []
        return history if isinstance(history, list) else []

    def is_evidence_need_current(
        self,
        evidence_need_id: str,
        *,
        expected_need_type: str | None = None,
        expected_capability_id: str | None = None,
        expected_claim_id: str | None = None,
    ) -> bool:
        state = self.get_current_evidence_need_state(evidence_need_id)
        if not state:
            return False
        if state.get("lifecycle_status") != EvidenceNeedLifecycleStatus.ACTIVE.value:
            return False
        if state.get("currentness_integrity_state") != "VALID":
            return False
        subject = _copy_mapping(state.get("subject"))
        if expected_need_type and state.get("need_type") != self._need_type(
            expected_need_type
        ):
            return False
        if expected_capability_id and subject.get("capability_id") != expected_capability_id:
            return False
        if expected_claim_id and subject.get("claim_id") != expected_claim_id:
            return False
        return True

    def list_current_evidence_needs(
        self,
        *,
        include_non_active: bool = False,
    ) -> list[dict[str, Any]]:
        if not self.current_dir.exists():
            return []
        rows = []
        for path in sorted(self.current_dir.glob("*.json")):
            state = self.get_current_evidence_need_state(path.stem)
            if not state:
                continue
            if include_non_active or state.get("is_current") is True:
                rows.append(state)
        return rows

    def _persist_decision(
        self,
        *,
        evidence_need_id: str,
        subject: Mapping[str, Any] | None,
        need_type: str | None,
        source_deficit_refs: Iterable[Mapping[str, Any]],
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
            "system": "current_evidence_need_decision",
            "evidence_need_decision_id": "pending",
            "evidence_need_id": evidence_need_id,
            "previous_decision_id": previous_state.get(
                "current_decision_id"
            ),
            "subject": dict(subject or {}),
            "need_type": need_type,
            "source_deficit_refs": [dict(item) for item in source_deficit_refs or []],
            "decision_state": decision_state,
            "lifecycle_status": lifecycle_status,
            "reason": reason,
            "authority": self.authority,
            "provenance": dict(provenance or {}),
            "assessment": dict(assessment or {}),
            "validation_sponsorship_created": False,
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
            "created_at": _now(),
        }
        decision["decision_fingerprint"] = _fingerprint(
            self._decision_fingerprint_payload(decision)
        )
        decision["evidence_need_decision_id"] = (
            "current_evidence_need_decision_"
            f"{decision['decision_fingerprint'][:16]}"
        )
        state = self._state_from_decision(decision)
        self._write_json(
            self.decisions_dir / f"{decision['evidence_need_decision_id']}.json",
            decision,
        )
        self._write_json(
            self.current_dir / f"{evidence_need_id}.json",
            state,
        )
        history = self.get_evidence_need_history(evidence_need_id)
        history.append({
            "event_type": "CURRENT_EVIDENCE_NEED_DECISION",
            "decision": decision,
            "resulting_state": state,
        })
        self._write_json(self.history_dir / f"{evidence_need_id}.json", history)
        return {
            "decision": decision,
            "current_state": state,
            "assessment": dict(assessment or {}),
            "authority": self.authority,
            "validation_sponsorship_created": False,
            "evidence_plan_created": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
        }

    def _invalid_transition(
        self,
        evidence_need_id: str,
        decision_state: str,
        *,
        reason: str,
        previous_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "decision": {
                "evidence_need_id": evidence_need_id,
                "decision_state": decision_state,
                "lifecycle_status": (
                    previous_state.get("lifecycle_status")
                    if isinstance(previous_state, Mapping)
                    else "NOT_AVAILABLE"
                ),
                "reason": reason,
                "authority": self.authority,
            },
            "current_state": dict(previous_state or {}),
            "authority": self.authority,
            "validation_sponsorship_created": False,
            "evidence_plan_created": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
        }

    def _state_from_decision(self, decision: Mapping[str, Any]) -> dict[str, Any]:
        state = {
            "schema_version": self.schema_version,
            "system": "current_evidence_need_state",
            "evidence_need_id": decision.get("evidence_need_id"),
            "current_decision_id": decision.get("evidence_need_decision_id"),
            "previous_decision_id": decision.get("previous_decision_id"),
            "subject": decision.get("subject", {}),
            "need_type": decision.get("need_type"),
            "source_deficit_refs": decision.get("source_deficit_refs", []),
            "decision_state": decision.get("decision_state"),
            "lifecycle_status": decision.get("lifecycle_status"),
            "reason": decision.get("reason"),
            "authority": self.authority,
            "state_authority": self.authority,
            "decision_fingerprint": decision.get("decision_fingerprint"),
            "updated_at": decision.get("created_at"),
            "is_actionable_current_need": decision.get("lifecycle_status")
            == EvidenceNeedLifecycleStatus.ACTIVE.value,
            "validation_sponsorship_created": False,
            "evidence_plan_created": False,
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
        }
        state["state_fingerprint"] = _fingerprint(
            self._state_fingerprint_payload(state)
        )
        return state

    def _candidate_failures(
        self,
        candidate: Mapping[str, Any],
        *,
        current_source_decision_id: str | None,
    ) -> list[str]:
        failures = []
        if candidate.get("producer") not in ALLOWED_PRODUCERS:
            failures.append("denied_unauthorized_need_producer")
        if candidate.get("candidate_authority") not in {self.candidate_authority, None}:
            failures.append("candidate_claims_authority")
        subject = _copy_mapping(candidate.get("subject"))
        if not subject:
            failures.append("missing_evidence_need_subject")
        if _missing(subject.get("capability_id")):
            failures.append("missing_capability_id")
        try:
            self._need_type(candidate.get("need_type"))
        except CurrentEvidenceNeedError:
            failures.append("unsupported_need_type")
        signal_type = str(candidate.get("deficit_signal_type") or "")
        if signal_type == DeficitSignalType.NOT_ELIGIBLE_FOR_NEED_PROPOSAL.value:
            failures.append("missing_governed_deficit_source")
        source_refs = candidate.get("source_deficit_refs")
        if not source_refs:
            failures.append("missing_governed_deficit_source")
        if candidate.get("provenance", {}).get("source_deficit_current") is False:
            failures.append("stale_deficit")
        if current_source_decision_id:
            source_ids = {
                str(item.get("source_decision_id"))
                for item in source_refs or []
                if isinstance(item, Mapping)
            }
            if str(current_source_decision_id) not in source_ids:
                failures.append("stale_deficit")
        expected_id = None
        if subject and candidate.get("need_type") in NEED_TYPE_TO_SUPPORT_CLASS:
            expected_id = self.evidence_need_id(
                subject,
                candidate.get("need_type"),
                candidate.get("required_support_class"),
            )
        if expected_id and candidate.get("evidence_need_id") != expected_id:
            failures.append("evidence_need_id_mismatch")
        expected_fp = _fingerprint(self._candidate_fingerprint_payload(candidate))
        if candidate.get("candidate_fingerprint") != expected_fp:
            failures.append("candidate_fingerprint_invalid")
        return failures

    def _support_satisfies(
        self,
        need_type: str | None,
        support: Mapping[str, Any] | None,
    ) -> bool:
        support = _copy_mapping(support)
        try:
            need_type = self._need_type(need_type)
        except CurrentEvidenceNeedError:
            return False
        if need_type == EvidenceNeedType.GENERAL_SUPPORT_REQUIRED.value:
            return int(support.get("valid_accepted_evidence_count", 0) or 0) > 0
        if need_type == EvidenceNeedType.SOURCE_INDEPENDENCE_REQUIRED.value:
            observed = int(support.get("independent_source_count", 0) or 0)
            required = int(support.get("required_independent_sources", 0) or 0)
            return required > 0 and observed >= required
        if need_type == EvidenceNeedType.CAUSAL_SUPPORT_REQUIRED.value:
            return (
                support.get("causal_support_state") == "CAUSALLY_SUPPORTED"
                or int(support.get("causal_supporting_evidence_count", 0) or 0) > 0
            )
        if need_type == EvidenceNeedType.REPRODUCIBILITY_REQUIRED.value:
            if support.get("reproducibility_state") == "REPRODUCIBLY_SUPPORTED":
                return True
            observed = int(support.get("independent_source_count", 0) or 0)
            required = int(support.get("required_independent_sources", 0) or 0)
            return (
                required > 0
                and observed >= required
                and support.get("causal_support_state") == "CAUSALLY_SUPPORTED"
            )
        if need_type == EvidenceNeedType.CONTRADICTION_RESOLUTION_REQUIRED.value:
            return support.get("contradiction_state") in {
                "NO_CONTRADICTION",
                "CONTRADICTION_RESOLVED",
                "RESOLVED",
            }
        if need_type == EvidenceNeedType.REVALIDATION_REQUIRED.value:
            return (
                support.get("revalidation_state") == "REVALIDATED"
                or support.get("fresh_governed_validation_support") is True
            )
        if need_type == EvidenceNeedType.CANDIDATE_DISAMBIGUATION_REQUIRED.value:
            return support.get("candidate_disambiguation_state") in {
                "DISAMBIGUATED",
                "TIE_CONFIRMED_NON_DISCRIMINATING_EVIDENCE",
                "TIE_REMAINS_OBSERVATIONALLY_EQUIVALENT",
            }
        return False

    def _state_integrity_valid(self, state: Mapping[str, Any]) -> bool:
        if state.get("state_authority") != self.authority:
            return False
        expected = _fingerprint(self._state_fingerprint_payload(state))
        return state.get("state_fingerprint") == expected

    def _candidate_fingerprint_payload(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "evidence_need_id": candidate.get("evidence_need_id"),
            "subject": candidate.get("subject"),
            "need_type": candidate.get("need_type"),
            "deficit_signal_type": candidate.get("deficit_signal_type"),
            "source_deficit_refs": candidate.get("source_deficit_refs", []),
            "required_support_class": candidate.get("required_support_class"),
            "current_support_summary": candidate.get("current_support_summary", {}),
            "proposal_reason": candidate.get("proposal_reason"),
            "producer": candidate.get("producer"),
            "provenance": candidate.get("provenance", {}),
        }

    def _assessment_fingerprint_payload(self, assessment: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "evidence_need_id": assessment.get("evidence_need_id"),
            "candidate_fingerprint": assessment.get("candidate_fingerprint"),
            "need_type": assessment.get("need_type"),
            "source_deficit_refs": assessment.get("source_deficit_refs", []),
            "assessment_failures": assessment.get("assessment_failures", []),
            "assessment_state": assessment.get("assessment_state"),
        }

    def _decision_fingerprint_payload(self, decision: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "evidence_need_id": decision.get("evidence_need_id"),
            "previous_decision_id": decision.get("previous_decision_id"),
            "subject": decision.get("subject", {}),
            "need_type": decision.get("need_type"),
            "source_deficit_refs": decision.get("source_deficit_refs", []),
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
            "evidence_need_id": state.get("evidence_need_id"),
            "current_decision_id": state.get("current_decision_id"),
            "previous_decision_id": state.get("previous_decision_id"),
            "subject": state.get("subject", {}),
            "need_type": state.get("need_type"),
            "source_deficit_refs": state.get("source_deficit_refs", []),
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

    def _need_type(self, value: Any) -> str:
        text = str(value or "").strip().upper()
        if text not in {item.value for item in EvidenceNeedType}:
            raise CurrentEvidenceNeedError("unsupported_need_type")
        return text

    def _deficit_signal_type_value(self, value: Any) -> str:
        text = str(value or "").strip().upper()
        if text not in {item.value for item in DeficitSignalType}:
            return DeficitSignalType.NOT_ELIGIBLE_FOR_NEED_PROPOSAL.value
        return text

    def _deficit_signal_type(self, failure: str, need_type: str | None = None) -> str:
        if need_type == EvidenceNeedType.REPRODUCIBILITY_REQUIRED.value:
            return DeficitSignalType.REPRODUCIBILITY_DEFICIT.value
        if failure == "independent_reproducibility_not_established":
            return DeficitSignalType.SOURCE_INDEPENDENCE_DEFICIT.value
        if failure == "causal_support_not_established":
            return DeficitSignalType.CAUSAL_SUPPORT_DEFICIT.value
        if failure == "some_evidence_rejected":
            return DeficitSignalType.CONTRADICTION_RESOLUTION_DEFICIT.value
        if failure == "accepted_evidence_missing":
            return DeficitSignalType.GENERAL_SUPPORT_DEFICIT.value
        return DeficitSignalType.QUALIFICATION_DEFICIT.value

    def _denied_state(self, reason: str) -> str:
        if "stale_deficit" in reason:
            return "DENIED_STALE_DEFICIT"
        if "support_already_sufficient" in reason:
            return "DENIED_SUPPORT_ALREADY_SUFFICIENT"
        if "missing_capability_id" in reason or "missing_evidence_need_subject" in reason:
            return "DENIED_MISSING_EVIDENCE_NEED_SUBJECT"
        if "denied_unauthorized_need_producer" in reason:
            return "DENIED_UNAUTHORIZED_NEED_PRODUCER"
        if "missing_governed_deficit_source" in reason:
            return "DENIED_NO_GOVERNED_DEFICIT_SOURCE"
        if "candidate_fingerprint_invalid" in reason or "evidence_need_id_mismatch" in reason:
            return "DENIED_DECISION_INTEGRITY_FAILURE"
        return "DENIED_CURRENT_EVIDENCE_NEED"

    def _rejected_candidate(self, *, producer: str, reason: str) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "system": "current_evidence_need_candidate",
            "evidence_need_id": "Not Available",
            "subject": {},
            "need_type": "Not Available",
            "deficit_signal_type": (
                DeficitSignalType.NOT_ELIGIBLE_FOR_NEED_PROPOSAL.value
            ),
            "source_deficit_refs": [],
            "required_support_class": "Not Available",
            "current_support_summary": {},
            "proposal_reason": reason,
            "producer": str(producer or "UNKNOWN"),
            "provenance": {"rejection_reason": reason},
            "candidate_authority": self.candidate_authority,
            "authority": self.candidate_authority,
            "validation_sponsorship_created": False,
            "validation_request_created": False,
            "evidence_plan_created": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
            "created_at": _now(),
        }
        payload["candidate_fingerprint"] = _fingerprint(
            self._candidate_fingerprint_payload(payload)
        )
        return payload


__all__ = [
    "DeficitSignalType",
    "EvidenceNeedLifecycleStatus",
    "EvidenceNeedSubject",
    "EvidenceNeedType",
    "CurrentEvidenceNeedAuthorityEngine",
    "CurrentEvidenceNeedError",
]
