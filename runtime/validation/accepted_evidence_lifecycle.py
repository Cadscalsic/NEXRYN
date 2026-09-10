"""Current-authority lifecycle for governed accepted evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


UNKNOWN = {None, "", "unknown", "UNKNOWN", "NOT_AVAILABLE", "Not Available"}


class AcceptedEvidenceLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    REVOKED = "REVOKED"
    INVALIDATED = "INVALIDATED"
    SUPERSEDED = "SUPERSEDED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"


REVIEW_TRIGGERS = {
    "PROVENANCE_CONFLICT",
    "SOURCE_IDENTITY_COLLAPSE",
    "SOURCE_INVALIDATED",
    "ARTIFACT_INTEGRITY_FAILURE",
    "CONTRADICTORY_ACCEPTED_EVIDENCE",
    "VALIDATION_RESULT_RETRACTED",
    "UPSTREAM_MEASUREMENT_INVALIDATED",
    "EVIDENCE_CONTENT_CORRUPTION",
    "CANONICAL_IDENTITY_CONFLICT",
    "GOVERNANCE_REVIEW_REQUIRED",
}


REVOCATION_TRIGGERS = {
    "ACCEPTANCE_WITHDRAWN",
    "VALIDATION_RESULT_RETRACTED",
    "SOURCE_WITHDRAWN",
    "GOVERNANCE_REVIEW_REQUIRED",
}


INVALIDATION_TRIGGERS = {
    "PROVENANCE_CONFLICT",
    "SOURCE_INVALIDATED",
    "ARTIFACT_INTEGRITY_FAILURE",
    "EVIDENCE_CONTENT_CORRUPTION",
    "CANONICAL_IDENTITY_CONFLICT",
}


class AcceptedEvidenceLifecycleEngine:
    """Govern current accepted-evidence authority without changing evidence content."""

    schema_version = "1.0"
    system_name = "accepted_evidence_lifecycle_engine"
    authority = "VALIDATION_EVIDENCE_EVALUATOR"

    def __init__(self, state_dir: str | Path | None = None) -> None:
        self.state_dir = Path(state_dir) if state_dir is not None else None

    def initialize_current_state(
        self,
        accepted_evidence: Mapping[str, Any],
        *,
        lifecycle_run_id: str = "current_run",
    ) -> dict[str, Any]:
        evidence = dict(accepted_evidence or {})
        self._assert_accepted_evidence(evidence)
        state = {
            "schema_version": self.schema_version,
            "system": "accepted_evidence_current_state",
            "evidence_id": evidence["accepted_evidence_id"],
            "accepted_evidence_id": evidence["accepted_evidence_id"],
            "current_status": AcceptedEvidenceLifecycleStatus.ACTIVE.value,
            "current_acceptance_decision_id": evidence["evidence_decision_id"],
            "current_lifecycle_decision_id": evidence["evidence_decision_id"],
            "is_currently_accepted": True,
            "review_required": False,
            "superseded_by": None,
            "authority": self.authority,
            "lifecycle_run_id": lifecycle_run_id,
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "qualification_authority": "NONE",
            "runtime_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        state["fingerprint"] = self._fingerprint(state)
        return state

    def review_evidence(
        self,
        current_state: Mapping[str, Any],
        *,
        review_trigger: str,
        trigger_evidence: Mapping[str, Any],
        lifecycle_run_id: str = "current_run",
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        trigger = str(review_trigger or "")
        trigger_payload = dict(trigger_evidence or {})
        failures = self._review_failures(state, trigger, trigger_payload)
        decision = {
            "schema_version": self.schema_version,
            "system": "accepted_evidence_review_decision",
            "review_decision_id": self._stable_id(
                "accepted_evidence_review_decision",
                {
                    "evidence_id": state.get("evidence_id"),
                    "previous_lifecycle": state.get("current_lifecycle_decision_id"),
                    "review_trigger": trigger,
                    "trigger_refs": self._refs(trigger_payload),
                },
            ),
            "evidence_id": state.get("evidence_id"),
            "previous_acceptance_decision_id": state.get(
                "current_acceptance_decision_id"
            ),
            "previous_status": state.get("current_status"),
            "new_status": (
                AcceptedEvidenceLifecycleStatus.ACTIVE.value
                if failures
                else AcceptedEvidenceLifecycleStatus.UNDER_REVIEW.value
            ),
            "review_trigger": trigger,
            "trigger_evidence_refs": self._refs(trigger_payload),
            "provenance_state": self._provenance_state(trigger_payload),
            "source_identity_state": trigger_payload.get(
                "source_identity_state",
                "NOT_REASSESSED",
            ),
            "integrity_state": trigger_payload.get("integrity_state", "NOT_REASSESSED"),
            "decision_state": "REVIEW_OPENED" if not failures else "REVIEW_DENIED",
            "decision_reason": failures[0] if failures else trigger,
            "review_failures": failures,
            "authority": self._authority(),
            "lifecycle_run_id": lifecycle_run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        decision["decision_fingerprint"] = self._fingerprint(decision)
        return decision

    def revoke_evidence(
        self,
        current_state: Mapping[str, Any],
        review_decision: Mapping[str, Any],
        *,
        revocation_reason: str,
        supporting_refs: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        return self._terminal_decision(
            current_state,
            review_decision,
            decision_kind="revocation",
            decision_id_key="revocation_decision_id",
            target_status=AcceptedEvidenceLifecycleStatus.REVOKED,
            reason_key="revocation_reason",
            reason=revocation_reason,
            refs_key="supporting_refs",
            refs=supporting_refs,
        )

    def invalidate_evidence(
        self,
        current_state: Mapping[str, Any],
        review_decision: Mapping[str, Any],
        *,
        invalidation_reason: str,
        provenance_failure_refs: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        return self._terminal_decision(
            current_state,
            review_decision,
            decision_kind="invalidation",
            decision_id_key="invalidation_decision_id",
            target_status=AcceptedEvidenceLifecycleStatus.INVALIDATED,
            reason_key="invalidation_reason",
            reason=invalidation_reason,
            refs_key="provenance_failure_refs",
            refs=provenance_failure_refs,
        )

    def supersede_evidence(
        self,
        current_state: Mapping[str, Any],
        *,
        replacement_evidence: Mapping[str, Any],
        supersession_reason: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        state = dict(current_state or {})
        replacement = dict(replacement_evidence or {})
        failures = self._state_failures(state)
        try:
            self._assert_accepted_evidence(replacement)
        except ValueError as exc:
            failures.append(str(exc))
        if replacement.get("supersedes_evidence_id") != state.get("evidence_id"):
            failures.append("explicit_supersession_relation_required")
        decision = {
            "schema_version": self.schema_version,
            "system": "accepted_evidence_supersession_decision",
            "supersession_decision_id": self._stable_id(
                "accepted_evidence_supersession_decision",
                {
                    "evidence_id": state.get("evidence_id"),
                    "replacement": replacement.get("accepted_evidence_id"),
                    "reason": supersession_reason,
                },
            ),
            "evidence_id": state.get("evidence_id"),
            "replacement_evidence_id": replacement.get("accepted_evidence_id"),
            "previous_status": state.get("current_status"),
            "new_status": (
                AcceptedEvidenceLifecycleStatus.ACTIVE.value
                if failures
                else AcceptedEvidenceLifecycleStatus.SUPERSEDED.value
            ),
            "superseded_by": replacement.get("accepted_evidence_id")
            if not failures
            else None,
            "supersession_reason": str(supersession_reason or "UNKNOWN"),
            "decision_state": "EVIDENCE_SUPERSEDED" if not failures else "SUPERSESSION_DENIED",
            "decision_reason": failures[0] if failures else str(supersession_reason),
            "supersession_failures": sorted(set(failures)),
            "authority": self._authority(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        decision["decision_fingerprint"] = self._fingerprint(decision)
        replacement_state = self.initialize_current_state(replacement)
        return decision, replacement_state

    def reaccept_evidence(
        self,
        current_state: Mapping[str, Any],
        accepted_evidence: Mapping[str, Any],
        *,
        acceptance_decision_id: str,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        evidence = dict(accepted_evidence or {})
        if state.get("current_status") not in {
            AcceptedEvidenceLifecycleStatus.UNDER_REVIEW.value,
            AcceptedEvidenceLifecycleStatus.REVOKED.value,
            AcceptedEvidenceLifecycleStatus.INVALIDATED.value,
            AcceptedEvidenceLifecycleStatus.REVALIDATION_REQUIRED.value,
        }:
            raise ValueError("reacceptance_requires_non_active_state")
        self._assert_accepted_evidence(evidence)
        if evidence.get("accepted_evidence_id") != state.get("evidence_id"):
            raise ValueError("wrong_evidence_id")
        if acceptance_decision_id in UNKNOWN:
            raise ValueError("fresh_acceptance_decision_required")
        decision = {
            "schema_version": self.schema_version,
            "system": "accepted_evidence_reacceptance_decision",
            "reacceptance_decision_id": self._stable_id(
                "accepted_evidence_reacceptance_decision",
                {
                    "evidence_id": state.get("evidence_id"),
                    "previous_lifecycle": state.get("current_lifecycle_decision_id"),
                    "acceptance_decision_id": acceptance_decision_id,
                },
            ),
            "evidence_id": state.get("evidence_id"),
            "previous_status": state.get("current_status"),
            "new_status": AcceptedEvidenceLifecycleStatus.ACTIVE.value,
            "fresh_acceptance_decision_id": acceptance_decision_id,
            "decision_state": "EVIDENCE_REACCEPTED",
            "authority": self._authority(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        decision["decision_fingerprint"] = self._fingerprint(decision)
        return decision

    def current_state_from_lifecycle_decision(
        self,
        current_state: Mapping[str, Any],
        lifecycle_decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        decision = dict(lifecycle_decision or {})
        evidence_id = decision.get("evidence_id")
        if evidence_id != state.get("evidence_id"):
            raise ValueError("wrong_evidence_id")
        self._assert_lifecycle_decision(decision)
        new_status = decision.get("new_status")
        if not new_status:
            raise ValueError("new_status_required")
        state["current_status"] = new_status
        state["current_lifecycle_decision_id"] = self._decision_id(decision)
        state["is_currently_accepted"] = new_status == (
            AcceptedEvidenceLifecycleStatus.ACTIVE.value
        )
        state["review_required"] = new_status == (
            AcceptedEvidenceLifecycleStatus.UNDER_REVIEW.value
        )
        state["superseded_by"] = decision.get("superseded_by")
        state["current_authority_state"] = (
            "CURRENT_ACTIVE_ACCEPTED_EVIDENCE"
            if state["is_currently_accepted"]
            else "NO_CURRENT_ACCEPTED_EVIDENCE_AUTHORITY"
        )
        state["authority"] = self.authority
        state["updated_at"] = decision.get("created_at")
        state["fingerprint"] = self._fingerprint(state)
        return state

    def qualification_review_trigger(
        self,
        lifecycle_decision: Mapping[str, Any],
        *,
        capability_id: str | None = None,
    ) -> dict[str, Any]:
        decision = dict(lifecycle_decision or {})
        self._assert_lifecycle_decision(decision)
        return {
            "schema_version": self.schema_version,
            "system": "accepted_evidence_to_qualification_review_trigger",
            "trigger_state": "QUALIFICATION_REVIEW_TRIGGER_AVAILABLE",
            "review_trigger": self._qualification_trigger_for(decision.get("new_status")),
            "evidence_lifecycle_decision_id": self._decision_id(decision),
            "evidence_id": decision.get("evidence_id"),
            "capability_id": capability_id,
            "trigger_evidence": {
                "accepted_evidence_id": decision.get("evidence_id"),
                "evidence_acceptance_state": "ACCEPTED",
                "capability_id": capability_id,
                "source_provenance": {
                    "source_provenance_state": "SOURCE_PROVENANCE_BOUND"
                },
            },
            "qualification_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "runtime_authority": "NONE",
            "budget_authority": "NONE",
        }

    def persist_current_state(
        self,
        current_state: Mapping[str, Any],
        *,
        lifecycle_decision: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.state_dir is None:
            raise ValueError("state_dir_required_for_persistence")
        state = dict(current_state or {})
        if state.get("evidence_id") in UNKNOWN:
            raise ValueError("evidence_id_required")
        if state.get("authority") != self.authority:
            raise ValueError("accepted_evidence_lifecycle_authority_required")
        state_dir = self.state_dir / "accepted_evidence_current_state"
        history_dir = self.state_dir / "accepted_evidence_history"
        state_dir.mkdir(parents=True, exist_ok=True)
        history_dir.mkdir(parents=True, exist_ok=True)
        state_path = state_dir / f"{state['evidence_id']}.json"
        state_path.write_text(
            json.dumps(state, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        history_path = history_dir / f"{state['evidence_id']}.json"
        history = []
        if history_path.exists():
            existing = json.loads(history_path.read_text(encoding="utf-8"))
            history = existing if isinstance(existing, list) else []
        history.append({
            "current_state": state,
            "lifecycle_decision": dict(lifecycle_decision or {}),
        })
        history_path.write_text(
            json.dumps(history, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return {
            "persistence_state": "PERSISTED_BY_ACCEPTED_EVIDENCE_AUTHORITY",
            "state_path": str(state_path),
            "history_path": str(history_path),
            "persistence_implies_evidence_acceptance": False,
            "persistence_implies_evidence_revocation": False,
        }

    def get_current_evidence_state(self, evidence_id: str) -> dict[str, Any] | None:
        if self.state_dir is None:
            return None
        path = self.state_dir / "accepted_evidence_current_state" / f"{evidence_id}.json"
        if not path.exists():
            return None
        state = json.loads(path.read_text(encoding="utf-8"))
        if state.get("authority") != self.authority:
            return None
        return state

    def get_evidence_history(self, evidence_id: str) -> list[dict[str, Any]]:
        if self.state_dir is None:
            return []
        path = self.state_dir / "accepted_evidence_history" / f"{evidence_id}.json"
        if not path.exists():
            return []
        history = json.loads(path.read_text(encoding="utf-8"))
        return history if isinstance(history, list) else []

    def is_currently_accepted(self, accepted_evidence: Mapping[str, Any]) -> bool:
        item = dict(accepted_evidence or {})
        status = item.get("current_status") or item.get("accepted_evidence_current_status")
        if status not in UNKNOWN:
            return status == AcceptedEvidenceLifecycleStatus.ACTIVE.value
        current_state = item.get("accepted_evidence_current_state")
        if isinstance(current_state, Mapping):
            return bool(current_state.get("is_currently_accepted")) and (
                current_state.get("current_status")
                == AcceptedEvidenceLifecycleStatus.ACTIVE.value
            )
        evidence_id = item.get("accepted_evidence_id") or item.get("evidence_id")
        current = self.get_current_evidence_state(str(evidence_id)) if evidence_id else None
        if current is not None:
            return bool(current.get("is_currently_accepted")) and (
                current.get("current_status")
                == AcceptedEvidenceLifecycleStatus.ACTIVE.value
            )
        return item.get("evidence_acceptance_state") == "ACCEPTED"

    def _terminal_decision(
        self,
        current_state: Mapping[str, Any],
        review_decision: Mapping[str, Any],
        *,
        decision_kind: str,
        decision_id_key: str,
        target_status: AcceptedEvidenceLifecycleStatus,
        reason_key: str,
        reason: str,
        refs_key: str,
        refs: Iterable[str] | None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        review = dict(review_decision or {})
        failures = self._terminal_failures(state, review)
        decision = {
            "schema_version": self.schema_version,
            "system": f"accepted_evidence_{decision_kind}_decision",
            decision_id_key: self._stable_id(
                f"accepted_evidence_{decision_kind}_decision",
                {
                    "evidence_id": state.get("evidence_id"),
                    "review_decision_id": review.get("review_decision_id"),
                    "reason": reason,
                },
            ),
            "evidence_id": state.get("evidence_id"),
            "previous_acceptance_decision_id": state.get(
                "current_acceptance_decision_id"
            ),
            "previous_status": state.get("current_status"),
            "new_status": (
                state.get("current_status") if failures else target_status.value
            ),
            reason_key: str(reason or "UNKNOWN"),
            refs_key: sorted(str(item) for item in refs or []),
            "decision_state": (
                f"EVIDENCE_{target_status.value}"
                if not failures
                else f"{target_status.value}_DENIED"
            ),
            "decision_reason": failures[0] if failures else str(reason),
            f"{decision_kind}_failures": failures,
            "authority": self._authority(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        decision["decision_fingerprint"] = self._fingerprint(decision)
        return decision

    def _assert_accepted_evidence(self, evidence: Mapping[str, Any]) -> None:
        if evidence.get("accepted_evidence_id") in UNKNOWN:
            raise ValueError("evidence_id_required")
        if evidence.get("evidence_acceptance_state") != "ACCEPTED":
            raise ValueError("accepted_evidence_required")
        if evidence.get("evidence_decision_id") in UNKNOWN:
            raise ValueError("acceptance_decision_id_required")
        provenance = evidence.get("source_provenance")
        if isinstance(provenance, Mapping) and (
            provenance.get("source_provenance_state") != "SOURCE_PROVENANCE_BOUND"
        ):
            raise ValueError("source_provenance_not_bound")
        if evidence.get("claim_evidence_binding_state") not in UNKNOWN and (
            evidence.get("claim_evidence_binding_state") != "BOUND"
        ):
            raise ValueError("claim_evidence_binding_not_bound")

    def _review_failures(
        self,
        state: Mapping[str, Any],
        trigger: str,
        trigger_evidence: Mapping[str, Any],
    ) -> list[str]:
        failures = self._state_failures(state)
        if state.get("current_status") != AcceptedEvidenceLifecycleStatus.ACTIVE.value:
            failures.append("active_current_evidence_required")
        if trigger not in REVIEW_TRIGGERS:
            failures.append("unsupported_review_trigger")
        if not trigger_evidence:
            failures.append("trigger_evidence_required")
        elif trigger_evidence.get("evidence_type") in {"RAW_RESULT", "RAW_VALIDATION_RESULT"}:
            failures.append("raw_evidence_cannot_trigger_lifecycle")
        elif trigger_evidence.get("evidence_acceptance_state") in {"REJECTED", "INSUFFICIENT"}:
            failures.append("rejected_evidence_cannot_trigger_lifecycle")
        if trigger_evidence.get("evidence_id") not in UNKNOWN and (
            trigger_evidence.get("evidence_id") != state.get("evidence_id")
        ):
            failures.append("wrong_evidence_id")
        if trigger_evidence.get("accepted_evidence_id") not in UNKNOWN and (
            trigger_evidence.get("accepted_evidence_id") != state.get("evidence_id")
        ):
            failures.append("wrong_evidence_id")
        if trigger_evidence.get("source_provenance") == {}:
            failures.append("trigger_provenance_missing")
        if trigger_evidence.get("artifact_fingerprint_matches") is False:
            failures.append("artifact_integrity_failure")
        return sorted(set(failures))

    def _terminal_failures(
        self,
        state: Mapping[str, Any],
        review: Mapping[str, Any],
    ) -> list[str]:
        failures = self._state_failures(state)
        if review.get("decision_state") != "REVIEW_OPENED":
            failures.append("open_review_decision_required")
        if review.get("evidence_id") != state.get("evidence_id"):
            failures.append("wrong_evidence_id")
        if not self._fingerprint_valid(review):
            failures.append("corrupted_review_decision_fingerprint")
        if state.get("current_status") != AcceptedEvidenceLifecycleStatus.UNDER_REVIEW.value:
            failures.append("under_review_status_required")
        return sorted(set(failures))

    def _state_failures(self, state: Mapping[str, Any]) -> list[str]:
        failures = []
        if state.get("evidence_id") in UNKNOWN:
            failures.append("evidence_id_required")
        if state.get("current_acceptance_decision_id") in UNKNOWN:
            failures.append("acceptance_decision_id_required")
        if state.get("current_lifecycle_decision_id") in UNKNOWN:
            failures.append("lifecycle_decision_id_required")
        if state.get("authority") != self.authority:
            failures.append("accepted_evidence_lifecycle_authority_required")
        return failures

    def _assert_lifecycle_decision(self, decision: Mapping[str, Any]) -> None:
        if not self._decision_id(decision):
            raise ValueError("lifecycle_decision_id_required")
        authority = decision.get("authority")
        if not isinstance(authority, Mapping) or (
            authority.get("accepted_evidence_lifecycle") != self.authority
        ):
            raise ValueError("accepted_evidence_lifecycle_authority_required")
        if not self._fingerprint_valid(decision):
            raise ValueError("corrupted_lifecycle_fingerprint")

    def _decision_id(self, decision: Mapping[str, Any]) -> str | None:
        for key in (
            "review_decision_id",
            "revocation_decision_id",
            "invalidation_decision_id",
            "supersession_decision_id",
            "reacceptance_decision_id",
        ):
            if decision.get(key):
                return str(decision[key])
        return None

    def _qualification_trigger_for(self, status: Any) -> str:
        if status == AcceptedEvidenceLifecycleStatus.REVOKED.value:
            return "ACCEPTED_EVIDENCE_REVOKED"
        if status == AcceptedEvidenceLifecycleStatus.INVALIDATED.value:
            return "EVIDENCE_PROVENANCE_INVALIDATED"
        if status == AcceptedEvidenceLifecycleStatus.SUPERSEDED.value:
            return "GOVERNANCE_REVIEW_REQUIRED"
        return "GOVERNANCE_REVIEW_REQUIRED"

    def _refs(self, payload: Mapping[str, Any]) -> list[str]:
        return sorted(
            str(item)
            for item in (
                payload.get("accepted_evidence_id"),
                payload.get("evidence_id"),
                payload.get("evidence_decision_id"),
                payload.get("artifact_fingerprint"),
            )
            if item not in UNKNOWN
        )

    def _provenance_state(self, payload: Mapping[str, Any]) -> str:
        provenance = payload.get("source_provenance")
        if isinstance(provenance, Mapping):
            return str(provenance.get("source_provenance_state") or "UNKNOWN")
        return str(payload.get("provenance_state") or "NOT_REASSESSED")

    def _authority(self) -> dict[str, str]:
        return {
            "accepted_evidence_lifecycle": self.authority,
            "qualification": "NONE",
            "truth": "NONE",
            "knowledge": "NONE",
            "runtime": "NONE",
            "budget": "NONE",
            "execution": "NONE",
        }

    def _fingerprint(self, payload: Mapping[str, Any]) -> str:
        item = {
            key: value
            for key, value in dict(payload).items()
            if key not in {"fingerprint", "decision_fingerprint"}
        }
        encoded = json.dumps(item, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _fingerprint_valid(self, payload: Mapping[str, Any]) -> bool:
        fingerprint = payload.get("decision_fingerprint") or payload.get("fingerprint")
        return bool(fingerprint and fingerprint == self._fingerprint(payload))

    def _stable_id(self, prefix: str, payload: Mapping[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        return f"{prefix}_{hashlib.sha1(encoded.encode('utf-8')).hexdigest()[:12]}"


accepted_evidence_lifecycle_engine = AcceptedEvidenceLifecycleEngine()


__all__ = [
    "AcceptedEvidenceLifecycleEngine",
    "AcceptedEvidenceLifecycleStatus",
    "INVALIDATION_TRIGGERS",
    "REVIEW_TRIGGERS",
    "REVOCATION_TRIGGERS",
    "accepted_evidence_lifecycle_engine",
]
