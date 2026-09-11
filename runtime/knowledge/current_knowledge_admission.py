"""Downstream admission gate for current Knowledge consumers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from runtime.knowledge.current_knowledge_authority import (
    KnowledgeCurrentAuthorityEngine,
    KnowledgeLifecycleStatus,
    knowledge_current_authority_engine,
)


UNKNOWN = {None, "", "UNKNOWN", "NOT_AVAILABLE", "Not Available"}


@dataclass(frozen=True)
class CurrentKnowledgeAdmission:
    knowledge_id: str | None
    subject_id: str | None
    current_knowledge_decision_id: str | None
    current_status: str | None
    current_state_fingerprint: str | None
    admission_state: str
    admission_reason: str
    authority_source: str
    consumer_scope: str

    @property
    def admitted(self) -> bool:
        return self.admission_state == "CURRENT_KNOWLEDGE_ADMITTED"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["admitted"] = self.admitted
        return payload


class CurrentKnowledgeAdmissionGate:
    """Delegate downstream currentness decisions to Knowledge authority."""

    system_name = "current_knowledge_admission_gate"

    def __init__(
        self,
        authority_engine: KnowledgeCurrentAuthorityEngine | None = None,
    ) -> None:
        self.authority_engine = (
            authority_engine or knowledge_current_authority_engine
        )

    def admit_current_knowledge(
        self,
        knowledge: Mapping[str, Any] | None,
        *,
        consumer_scope: str = "downstream_knowledge_consumer",
        expected_subject_id: str | None = None,
        expected_claim_id: str | None = None,
        expected_scope: str | None = None,
    ) -> CurrentKnowledgeAdmission:
        candidate = knowledge if isinstance(knowledge, Mapping) else {}
        knowledge_id = _text(candidate.get("knowledge_id"))
        subject_id = _text(candidate.get("subject_id"))
        decision_id = _text(candidate.get("current_knowledge_decision_id"))
        if knowledge_id in UNKNOWN:
            return self._denied(
                knowledge_id,
                subject_id,
                decision_id,
                None,
                None,
                "DENIED_KNOWLEDGE_IDENTITY_MISSING",
                consumer_scope,
            )

        current = self.authority_engine.get_current_knowledge_state(
            str(knowledge_id)
        )
        if not current:
            return self._denied(
                knowledge_id,
                subject_id,
                decision_id,
                None,
                None,
                "DENIED_KNOWLEDGE_CURRENT_AUTHORITY_UNVERIFIED",
                consumer_scope,
            )

        current_subject_id = _text(current.get("subject_id"))
        current_decision_id = _text(current.get("current_knowledge_decision_id"))
        current_status = _text(current.get("lifecycle_status"))
        current_fingerprint = _text(current.get("fingerprint"))

        if expected_subject_id not in UNKNOWN and current_subject_id != expected_subject_id:
            return self._denied(
                knowledge_id,
                current_subject_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_KNOWLEDGE_IDENTITY_MISMATCH",
                consumer_scope,
            )
        if subject_id not in UNKNOWN and subject_id != current_subject_id:
            return self._denied(
                knowledge_id,
                subject_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_KNOWLEDGE_IDENTITY_MISMATCH",
                consumer_scope,
            )
        if expected_claim_id not in UNKNOWN and _text(current.get("claim_id")) != expected_claim_id:
            return self._denied(
                knowledge_id,
                current_subject_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_KNOWLEDGE_IDENTITY_MISMATCH",
                consumer_scope,
            )
        if expected_scope not in UNKNOWN and _text(current.get("scope")) != expected_scope:
            return self._denied(
                knowledge_id,
                current_subject_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_KNOWLEDGE_IDENTITY_MISMATCH",
                consumer_scope,
            )
        if decision_id in UNKNOWN:
            return self._denied(
                knowledge_id,
                current_subject_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_KNOWLEDGE_DECISION_MISSING",
                consumer_scope,
            )
        if decision_id != current_decision_id:
            return self._denied(
                knowledge_id,
                current_subject_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_STALE_KNOWLEDGE_DECISION",
                consumer_scope,
            )

        candidate_fingerprint = _text(
            candidate.get("fingerprint")
            or candidate.get("current_state_fingerprint")
        )
        if candidate_fingerprint not in UNKNOWN and candidate_fingerprint != current_fingerprint:
            return self._denied(
                knowledge_id,
                current_subject_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_KNOWLEDGE_FINGERPRINT_INVALID",
                consumer_scope,
            )

        support_fingerprint = _text(candidate.get("support_fingerprint"))
        current_support_fingerprint = _text(
            (current.get("knowledge_assessment") or {}).get("support_fingerprint")
            if isinstance(current.get("knowledge_assessment"), Mapping)
            else None
        )
        if (
            support_fingerprint not in UNKNOWN
            and current_support_fingerprint not in UNKNOWN
            and support_fingerprint != current_support_fingerprint
        ):
            return self._denied(
                knowledge_id,
                current_subject_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_KNOWLEDGE_STALE",
                consumer_scope,
            )

        if current_status != KnowledgeLifecycleStatus.ACTIVE.value:
            return self._denied(
                knowledge_id,
                current_subject_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                _status_reason(current_status),
                consumer_scope,
            )
        if current.get("current_authority_status") != (
            "CURRENT_KNOWLEDGE_AUTHORITY_VERIFIED"
        ):
            return self._denied(
                knowledge_id,
                current_subject_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_KNOWLEDGE_CURRENT_AUTHORITY_UNVERIFIED",
                consumer_scope,
            )

        return CurrentKnowledgeAdmission(
            knowledge_id=str(knowledge_id),
            subject_id=str(current_subject_id),
            current_knowledge_decision_id=str(current_decision_id),
            current_status=str(current_status),
            current_state_fingerprint=str(current_fingerprint),
            admission_state="CURRENT_KNOWLEDGE_ADMITTED",
            admission_reason="CURRENT_KNOWLEDGE_AUTHORITY_VERIFIED",
            authority_source=self.authority_engine.authority,
            consumer_scope=consumer_scope,
        )

    def _denied(
        self,
        knowledge_id: str | None,
        subject_id: str | None,
        decision_id: str | None,
        status: str | None,
        fingerprint: str | None,
        reason: str,
        consumer_scope: str,
    ) -> CurrentKnowledgeAdmission:
        return CurrentKnowledgeAdmission(
            knowledge_id=knowledge_id,
            subject_id=subject_id,
            current_knowledge_decision_id=decision_id,
            current_status=status,
            current_state_fingerprint=fingerprint,
            admission_state="CURRENT_KNOWLEDGE_DENIED",
            admission_reason=reason,
            authority_source=self.authority_engine.authority,
            consumer_scope=consumer_scope,
        )


def admit_current_knowledge(
    knowledge: Mapping[str, Any] | None,
    *,
    consumer_scope: str = "downstream_knowledge_consumer",
    expected_subject_id: str | None = None,
    expected_claim_id: str | None = None,
    expected_scope: str | None = None,
    admission_gate: CurrentKnowledgeAdmissionGate | None = None,
) -> CurrentKnowledgeAdmission:
    gate = admission_gate or CurrentKnowledgeAdmissionGate()
    return gate.admit_current_knowledge(
        knowledge,
        consumer_scope=consumer_scope,
        expected_subject_id=expected_subject_id,
        expected_claim_id=expected_claim_id,
        expected_scope=expected_scope,
    )


def filter_current_knowledge(
    knowledge_items: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | Any,
    *,
    consumer_scope: str,
    admission_gate: CurrentKnowledgeAdmissionGate | None = None,
) -> dict[str, Any]:
    gate = admission_gate or CurrentKnowledgeAdmissionGate()
    current = []
    historical = []
    excluded = []
    for item in knowledge_items or []:
        if not isinstance(item, Mapping):
            continue
        admission = gate.admit_current_knowledge(
            item,
            consumer_scope=consumer_scope,
        )
        record = dict(item)
        record["current_knowledge_admission"] = admission.to_dict()
        historical.append(record)
        if admission.admitted:
            current.append(record)
        else:
            excluded.append(record)
    return {
        "current_knowledge_inputs": current,
        "historical_knowledge_inputs": historical,
        "excluded_noncurrent_knowledge": excluded,
        "current_knowledge_input_count": len(current),
        "excluded_noncurrent_knowledge_count": len(excluded),
    }


def _text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _status_reason(status: str | None) -> str:
    return {
        KnowledgeLifecycleStatus.UNDER_REVIEW.value: "DENIED_KNOWLEDGE_UNDER_REVIEW",
        KnowledgeLifecycleStatus.INVALIDATED.value: "DENIED_KNOWLEDGE_INVALIDATED",
        KnowledgeLifecycleStatus.SUPERSEDED.value: "DENIED_KNOWLEDGE_SUPERSEDED",
        KnowledgeLifecycleStatus.REVALIDATION_REQUIRED.value: (
            "DENIED_KNOWLEDGE_REVALIDATION_REQUIRED"
        ),
    }.get(status or "", "DENIED_KNOWLEDGE_CURRENT_AUTHORITY_UNVERIFIED")


current_knowledge_admission_gate = CurrentKnowledgeAdmissionGate()


__all__ = [
    "CurrentKnowledgeAdmission",
    "CurrentKnowledgeAdmissionGate",
    "admit_current_knowledge",
    "current_knowledge_admission_gate",
    "filter_current_knowledge",
]
