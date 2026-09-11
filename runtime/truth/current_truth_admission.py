"""Downstream admission gate for current Truth consumers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from runtime.truth.truth_current_authority_lifecycle import (
    TruthCurrentAuthorityLifecycleEngine,
    TruthLifecycleStatus,
    truth_current_authority_lifecycle_engine,
)


UNKNOWN = {None, "", "UNKNOWN", "NOT_AVAILABLE", "Not Available"}


@dataclass(frozen=True)
class CurrentTruthAdmission:
    truth_id: str | None
    claim_id: str | None
    current_truth_decision_id: str | None
    current_status: str | None
    current_state_fingerprint: str | None
    admission_state: str
    admission_reason: str
    authority_source: str
    consumer_scope: str

    @property
    def admitted(self) -> bool:
        return self.admission_state == "CURRENT_TRUTH_ADMITTED"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["admitted"] = self.admitted
        return payload


class CurrentTruthAdmissionGate:
    """Delegate downstream currentness decisions to Truth lifecycle authority."""

    system_name = "current_truth_admission_gate"

    def __init__(
        self,
        lifecycle_engine: TruthCurrentAuthorityLifecycleEngine | None = None,
    ) -> None:
        self.lifecycle_engine = (
            lifecycle_engine or truth_current_authority_lifecycle_engine
        )

    def admit_current_truth(
        self,
        truth: Mapping[str, Any] | None,
        *,
        consumer_scope: str = "downstream_truth_consumer",
        expected_claim_id: str | None = None,
    ) -> CurrentTruthAdmission:
        candidate = truth if isinstance(truth, Mapping) else {}
        truth_id = _text(candidate.get("truth_id"))
        claim_id = _text(candidate.get("claim_id"))
        decision_id = _text(candidate.get("current_truth_decision_id"))
        if truth_id in UNKNOWN:
            return self._denied(
                truth_id,
                claim_id,
                decision_id,
                None,
                None,
                "DENIED_TRUTH_IDENTITY_MISSING",
                consumer_scope,
            )

        current = self.lifecycle_engine.get_current_truth_state(str(truth_id))
        if not current:
            return self._denied(
                truth_id,
                claim_id,
                decision_id,
                None,
                None,
                "DENIED_TRUTH_CURRENT_AUTHORITY_UNVERIFIED",
                consumer_scope,
            )

        current_claim_id = _text(current.get("claim_id"))
        current_decision_id = _text(current.get("current_truth_decision_id"))
        current_status = _text(current.get("lifecycle_status"))
        current_fingerprint = _text(current.get("fingerprint"))

        if expected_claim_id not in UNKNOWN and current_claim_id != expected_claim_id:
            return self._denied(
                truth_id,
                current_claim_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_TRUTH_IDENTITY_MISMATCH",
                consumer_scope,
            )
        if claim_id not in UNKNOWN and claim_id != current_claim_id:
            return self._denied(
                truth_id,
                claim_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_TRUTH_IDENTITY_MISMATCH",
                consumer_scope,
            )
        if decision_id in UNKNOWN:
            return self._denied(
                truth_id,
                current_claim_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_TRUTH_DECISION_MISSING",
                consumer_scope,
            )
        if decision_id != current_decision_id:
            return self._denied(
                truth_id,
                current_claim_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_STALE_TRUTH_DECISION",
                consumer_scope,
            )
        candidate_fingerprint = _text(candidate.get("fingerprint"))
        if candidate_fingerprint not in UNKNOWN and candidate_fingerprint != current_fingerprint:
            return self._denied(
                truth_id,
                current_claim_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_TRUTH_FINGERPRINT_INVALID",
                consumer_scope,
            )

        if current_status != TruthLifecycleStatus.ACTIVE.value:
            return self._denied(
                truth_id,
                current_claim_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                _status_reason(current_status),
                consumer_scope,
            )
        if current.get("current_authority_status") != (
            "CURRENT_TRUTH_AUTHORITY_VERIFIED"
        ):
            return self._denied(
                truth_id,
                current_claim_id,
                current_decision_id,
                current_status,
                current_fingerprint,
                "DENIED_TRUTH_CURRENT_AUTHORITY_UNVERIFIED",
                consumer_scope,
            )

        return CurrentTruthAdmission(
            truth_id=str(truth_id),
            claim_id=str(current_claim_id),
            current_truth_decision_id=str(current_decision_id),
            current_status=str(current_status),
            current_state_fingerprint=str(current_fingerprint),
            admission_state="CURRENT_TRUTH_ADMITTED",
            admission_reason="CURRENT_TRUTH_AUTHORITY_VERIFIED",
            authority_source=self.lifecycle_engine.authority,
            consumer_scope=consumer_scope,
        )

    def _denied(
        self,
        truth_id: str | None,
        claim_id: str | None,
        decision_id: str | None,
        status: str | None,
        fingerprint: str | None,
        reason: str,
        consumer_scope: str,
    ) -> CurrentTruthAdmission:
        return CurrentTruthAdmission(
            truth_id=truth_id,
            claim_id=claim_id,
            current_truth_decision_id=decision_id,
            current_status=status,
            current_state_fingerprint=fingerprint,
            admission_state="CURRENT_TRUTH_DENIED",
            admission_reason=reason,
            authority_source=self.lifecycle_engine.authority,
            consumer_scope=consumer_scope,
        )


def admit_current_truth(
    truth: Mapping[str, Any] | None,
    *,
    consumer_scope: str = "downstream_truth_consumer",
    expected_claim_id: str | None = None,
    admission_gate: CurrentTruthAdmissionGate | None = None,
) -> CurrentTruthAdmission:
    gate = admission_gate or CurrentTruthAdmissionGate()
    return gate.admit_current_truth(
        truth,
        consumer_scope=consumer_scope,
        expected_claim_id=expected_claim_id,
    )


def filter_current_truths(
    truths: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | Any,
    *,
    consumer_scope: str,
    admission_gate: CurrentTruthAdmissionGate | None = None,
) -> dict[str, Any]:
    gate = admission_gate or CurrentTruthAdmissionGate()
    current = []
    historical = []
    excluded = []
    for item in truths or []:
        if not isinstance(item, Mapping):
            continue
        admission = gate.admit_current_truth(item, consumer_scope=consumer_scope)
        record = dict(item)
        record["current_truth_admission"] = admission.to_dict()
        historical.append(record)
        if admission.admitted:
            current.append(record)
        else:
            excluded.append(record)
    return {
        "current_truth_inputs": current,
        "historical_truth_inputs": historical,
        "excluded_noncurrent_truths": excluded,
        "current_truth_input_count": len(current),
        "excluded_noncurrent_truth_count": len(excluded),
    }


def _text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _status_reason(status: str | None) -> str:
    return {
        TruthLifecycleStatus.UNDER_REVIEW.value: "DENIED_TRUTH_UNDER_REVIEW",
        TruthLifecycleStatus.INVALIDATED.value: "DENIED_TRUTH_INVALIDATED",
        TruthLifecycleStatus.SUPERSEDED.value: "DENIED_TRUTH_SUPERSEDED",
        TruthLifecycleStatus.REVALIDATION_REQUIRED.value: (
            "DENIED_TRUTH_REVALIDATION_REQUIRED"
        ),
    }.get(str(status), "DENIED_TRUTH_CURRENT_AUTHORITY_UNVERIFIED")


current_truth_admission_gate = CurrentTruthAdmissionGate()


__all__ = [
    "CurrentTruthAdmission",
    "CurrentTruthAdmissionGate",
    "admit_current_truth",
    "current_truth_admission_gate",
    "filter_current_truths",
]
