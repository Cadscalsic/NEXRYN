from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from runtime.claim_identity.claim_identity_contract import (
    ClaimIdentityError,
    ClaimKind,
    ClaimSubject,
    SemanticScope,
    derive_claim_id,
)


CLAIM_EVIDENCE_BINDING_SCHEMA_VERSION = "1.0"
CLAIM_EVIDENCE_BINDING_ID_PREFIX = "claim_evidence_binding_"
CLAIM_SUBJECT_OWNER = "semantic_candidate_operation"
CLAIM_EVIDENCE_BINDING_AUTHORITY = "OBSERVATION_ONLY"
CLAIM_EVIDENCE_BINDING_BEHAVIORAL_AUTHORITY = "NONE"


class ClaimEvidenceBindingError(ValueError):
    """Raised when evidence cannot be safely attributed to one canonical claim."""


def candidate_operation_claim_subject(
    *,
    subject_ref: str,
    operation: str,
    semantic_scope: SemanticScope | str = SemanticScope.CROSS_RUN,
) -> ClaimSubject:
    return ClaimSubject(
        kind=ClaimKind.CANDIDATE_OPERATION,
        semantic_scope=semantic_scope,
        subject_ref=subject_ref,
        operation=operation,
    )


def claim_subject_from_evidence_plan(plan: Mapping[str, Any]) -> ClaimSubject:
    if not isinstance(plan, Mapping):
        raise ClaimIdentityError("evidence plan must be a mapping")
    subject_ref = _first_present(
        plan.get("target_candidate"),
        plan.get("source_candidate_id"),
        plan.get("evidence_acquisition_target_candidate"),
    )
    operation = _first_present(
        plan.get("target_operation"),
        plan.get("source_operation"),
        plan.get("evidence_acquisition_target_operation"),
    )
    return candidate_operation_claim_subject(
        subject_ref=subject_ref,
        operation=operation,
        semantic_scope=SemanticScope.CROSS_RUN,
    )


def claim_identity_for_evidence_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    subject = claim_subject_from_evidence_plan(plan)
    return {
        "claim_id": derive_claim_id(subject),
        "claim_subject": subject.canonical_payload(),
        "claim_subject_owner": CLAIM_SUBJECT_OWNER,
        "claim_identity_source": "evidence_plan_semantic_target",
        "claim_evidence_binding_authority": CLAIM_EVIDENCE_BINDING_AUTHORITY,
        "claim_evidence_binding_behavioral_authority": (
            CLAIM_EVIDENCE_BINDING_BEHAVIORAL_AUTHORITY
        ),
    }


def build_claim_evidence_binding(
    *,
    claim_subject: Mapping[str, Any] | ClaimSubject,
    evidence_plan: Mapping[str, Any] | None = None,
    evidence_decision: Mapping[str, Any] | None = None,
    accepted_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    subject = _subject_from_payload(claim_subject)
    claim_payload = subject.canonical_payload()
    claim_id = derive_claim_id(subject)

    _assert_record_matches_claim(
        "evidence_plan",
        evidence_plan,
        claim_id,
        claim_payload,
    )
    _assert_record_matches_claim(
        "evidence_decision",
        evidence_decision,
        claim_id,
        claim_payload,
    )
    _assert_record_matches_claim(
        "accepted_evidence",
        accepted_evidence,
        claim_id,
        claim_payload,
    )

    plan_id = _record_value(evidence_plan, "plan_id")
    decision_id = _record_value(evidence_decision, "evidence_decision_id")
    accepted_id = _record_value(accepted_evidence, "accepted_evidence_id")
    if evidence_decision and plan_id:
        _assert_equal(
            "evidence_decision.plan_id",
            evidence_decision.get("plan_id"),
            plan_id,
        )
    if accepted_evidence and plan_id:
        _assert_equal("accepted_evidence.plan_id", accepted_evidence.get("plan_id"), plan_id)
    if accepted_evidence and evidence_decision and decision_id:
        _assert_equal(
            "accepted_evidence.evidence_decision_id",
            accepted_evidence.get("evidence_decision_id"),
            decision_id,
        )

    fingerprint_payload = {
        "schema_version": CLAIM_EVIDENCE_BINDING_SCHEMA_VERSION,
        "claim_id": claim_id,
        "evidence_plan_id": plan_id,
        "evidence_decision_id": decision_id,
        "accepted_evidence_id": accepted_id,
        "binding_type": "accepted_validation_evidence_support",
    }
    fingerprint = _fingerprint(fingerprint_payload)
    return {
        "schema_version": CLAIM_EVIDENCE_BINDING_SCHEMA_VERSION,
        "claim_evidence_binding_id": (
            f"{CLAIM_EVIDENCE_BINDING_ID_PREFIX}"
            f"{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
        ),
        "claim_evidence_binding_fingerprint": fingerprint,
        "claim_evidence_binding_state": "BOUND",
        "claim_evidence_binding_type": "accepted_validation_evidence_support",
        "claim_id": claim_id,
        "claim_subject": claim_payload,
        "claim_subject_owner": CLAIM_SUBJECT_OWNER,
        "evidence_plan_id": plan_id,
        "evidence_decision_id": decision_id,
        "accepted_evidence_id": accepted_id,
        "target_candidate": claim_payload.get("subject_ref"),
        "target_operation": claim_payload.get("operation"),
        "evidence_direction": _record_value(evidence_decision, "evidence_direction"),
        "evidence_acceptance_state": _record_value(
            evidence_decision,
            "evidence_acceptance_state",
        ),
        "authority": {
            "truth": "NONE",
            "trust": "NONE",
            "graduation": "NONE",
            "execution": "NONE",
        },
        "claim_evidence_binding_authority": CLAIM_EVIDENCE_BINDING_AUTHORITY,
        "claim_evidence_binding_behavioral_authority": (
            CLAIM_EVIDENCE_BINDING_BEHAVIORAL_AUTHORITY
        ),
        "truth_authority": "NONE",
        "trust_authority": "NONE",
        "graduation_authority": "NONE",
        "execution_authority": "NONE",
    }


def _subject_from_payload(value: Mapping[str, Any] | ClaimSubject) -> ClaimSubject:
    if isinstance(value, ClaimSubject):
        return value
    if not isinstance(value, Mapping):
        raise ClaimEvidenceBindingError("claim_subject must be a mapping")
    return ClaimSubject(
        kind=value.get("kind"),
        semantic_scope=value.get("semantic_scope"),
        subject_ref=value.get("subject_ref"),
        operation=value.get("operation"),
        normalized_statement=value.get("normalized_statement"),
        qualifiers=value.get("qualifiers") or {},
        schema_version=value.get("schema_version", "1.0"),
    )


def _assert_record_matches_claim(
    label: str,
    record: Mapping[str, Any] | None,
    claim_id: str,
    claim_payload: Mapping[str, Any],
) -> None:
    if not record:
        return
    record_claim_id = _first_present(record.get("claim_id"), default=None)
    if record_claim_id is not None:
        _assert_equal(f"{label}.claim_id", record_claim_id, claim_id)
    record_claim_subject = record.get("claim_subject")
    if record_claim_subject:
        if not isinstance(record_claim_subject, Mapping):
            raise ClaimEvidenceBindingError(f"{label}.claim_subject must be a mapping")
        canonical_record = _subject_from_payload(record_claim_subject).canonical_payload()
        if canonical_record != claim_payload:
            raise ClaimEvidenceBindingError(f"{label}.claim_subject does not match claim")
    target = _first_present(
        record.get("target_candidate"),
        record.get("source_candidate_id"),
        default=None,
    )
    if target is not None:
        _assert_equal(f"{label}.target_candidate", target, claim_payload.get("subject_ref"))
    operation = _first_present(
        record.get("target_operation"),
        record.get("source_operation"),
        default=None,
    )
    if operation is not None:
        candidate = candidate_operation_claim_subject(
            subject_ref=claim_payload.get("subject_ref"),
            operation=operation,
        )
        _assert_equal(
            f"{label}.target_operation",
            candidate.canonical_payload().get("operation"),
            claim_payload.get("operation"),
        )


def _assert_equal(label: str, left: Any, right: Any) -> None:
    if left != right:
        raise ClaimEvidenceBindingError(f"{label} mismatch: {left!r} != {right!r}")


def _first_present(*values: Any, default: Any = "Not Available") -> Any:
    for value in values:
        if value not in (None, "", "Not Available"):
            return value
    return default


def _record_value(record: Mapping[str, Any] | None, key: str) -> Any:
    if not record:
        return "Not Available"
    return _first_present(record.get(key))


def _fingerprint(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = [
    "CLAIM_EVIDENCE_BINDING_AUTHORITY",
    "CLAIM_EVIDENCE_BINDING_BEHAVIORAL_AUTHORITY",
    "CLAIM_EVIDENCE_BINDING_ID_PREFIX",
    "CLAIM_EVIDENCE_BINDING_SCHEMA_VERSION",
    "CLAIM_SUBJECT_OWNER",
    "ClaimEvidenceBindingError",
    "build_claim_evidence_binding",
    "candidate_operation_claim_subject",
    "claim_identity_for_evidence_plan",
    "claim_subject_from_evidence_plan",
]
