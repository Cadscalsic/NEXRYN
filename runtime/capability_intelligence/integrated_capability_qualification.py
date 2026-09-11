"""Governed capability qualification decisions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.epistemic.evidence_source_independence import (
    EvidenceSourceIndependenceEngine,
)
from runtime.validation.accepted_evidence_lifecycle import (
    AcceptedEvidenceLifecycleEngine,
)


UNKNOWN = {None, "", "unknown", "UNKNOWN", "NOT_AVAILABLE", "Not Available"}


class CapabilityQualificationLevel(str, Enum):
    NOT_QUALIFIED = "NOT_QUALIFIED"
    ARCHITECTURALLY_PRESENT = "ARCHITECTURALLY_PRESENT"
    RUNTIME_REACHABLE = "RUNTIME_REACHABLE"
    OPERATIONALLY_OBSERVED = "OPERATIONALLY_OBSERVED"
    CAUSALLY_DEMONSTRATED = "CAUSALLY_DEMONSTRATED"
    REPRODUCIBLY_SUPPORTED = "REPRODUCIBLY_SUPPORTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    QUALIFICATION_INVALIDATED = "QUALIFICATION_INVALIDATED"


class CapabilityQualificationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    INVALIDATED = "INVALIDATED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    SUPERSEDED = "SUPERSEDED"


REVIEW_TRIGGERS = {
    "ACCEPTED_EVIDENCE_REVOKED",
    "EVIDENCE_PROVENANCE_INVALIDATED",
    "SOURCE_INDEPENDENCE_COLLAPSED",
    "CAUSAL_SUPPORT_WITHDRAWN",
    "REPRODUCIBILITY_SUPPORT_INVALIDATED",
    "CAPABILITY_IDENTITY_CONFLICT",
    "CONTRADICTORY_ACCEPTED_EVIDENCE",
    "CURRENT_DECISION_CORRUPTED",
    "DECISION_PROVENANCE_INVALID",
    "GOVERNANCE_REVIEW_REQUIRED",
}


ORDERED_LEVELS = (
    CapabilityQualificationLevel.NOT_QUALIFIED,
    CapabilityQualificationLevel.ARCHITECTURALLY_PRESENT,
    CapabilityQualificationLevel.RUNTIME_REACHABLE,
    CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
    CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED,
    CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
)


@dataclass(frozen=True)
class CapabilitySubject:
    capability_name: str
    operation: str
    domain: str = "UNKNOWN"
    qualifiers: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = "1.0"

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_name": _token(self.capability_name),
            "operation": _token(self.operation),
            "domain": _token(self.domain),
            "qualifiers": {
                str(key): self.qualifiers[key]
                for key in sorted(self.qualifiers)
            },
        }


def capability_id_for_subject(subject: CapabilitySubject | Mapping[str, Any]) -> str:
    payload = _subject_payload(subject)
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return "capability_" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


class IntegratedCapabilityQualificationEngine:
    """Decide capability qualification without granting truth or runtime authority."""

    schema_version = "1.0"
    system_name = "integrated_capability_qualification_engine"
    qualification_authority = "INTEGRATED_CAPABILITY_QUALIFICATION_ENGINE"
    default_required_independent_sources = 2

    def __init__(
        self,
        state_dir: str | Path | None = None,
        *,
        source_engine: EvidenceSourceIndependenceEngine | None = None,
        evidence_lifecycle_engine: AcceptedEvidenceLifecycleEngine | None = None,
    ) -> None:
        self.state_dir = Path(state_dir) if state_dir is not None else None
        self.source_engine = source_engine or EvidenceSourceIndependenceEngine()
        self.evidence_lifecycle_engine = (
            evidence_lifecycle_engine or AcceptedEvidenceLifecycleEngine()
        )

    def assess_capability_evidence(
        self,
        capability_subject: CapabilitySubject | Mapping[str, Any],
        accepted_evidence: Iterable[Mapping[str, Any]] | None,
        *,
        assessment_run_id: str = "current_run",
        required_independent_sources: int | None = None,
    ) -> dict[str, Any]:
        subject = _subject_payload(capability_subject)
        capability_id = capability_id_for_subject(subject)
        evidence_rows = [dict(item) for item in accepted_evidence or []]
        valid = []
        rejected = []
        for item in evidence_rows:
            rejection = self._accepted_evidence_rejection(item, capability_id, subject)
            if rejection:
                rejected.append({
                    "accepted_evidence_id": item.get("accepted_evidence_id"),
                    "rejection_reason": rejection,
                })
                continue
            valid.append(self._source_flattened(item))
        support_lineage = [
            self._accepted_evidence_support_lineage(item) for item in valid
        ]

        required_sources = (
            int(required_independent_sources)
            if required_independent_sources is not None
            else self.default_required_independent_sources
        )
        coverage = self.source_engine.source_coverage(
            valid,
            claim_id=valid[0].get("claim_id") if valid else None,
            required_independent_sources=required_sources,
        )
        causal_count = sum(
            1 for item in valid if self._causal_support_state(item) == "CAUSALLY_SUPPORTED"
        )
        observed_count = len(valid)
        independent_count = int(
            coverage.get("current_proven_independent_source_count") or 0
        )
        return {
            "schema_version": self.schema_version,
            "system": "capability_evidence_assessment",
            "capability_evidence_assessment_id": self._stable_id(
                "capability_evidence_assessment",
                {
                    "capability_id": capability_id,
                    "assessment_run_id": assessment_run_id,
                    "accepted_evidence_ids": [
                        item.get("accepted_evidence_id") for item in valid
                    ],
                },
            ),
            "assessment_run_id": assessment_run_id,
            "capability_id": capability_id,
            "capability_subject": subject,
            "accepted_evidence_ids": [
                item.get("accepted_evidence_id") for item in valid
            ],
            "supporting_accepted_evidence_refs": support_lineage,
            "raw_evidence_ids": sorted({
                str(item.get("raw_evidence_id") or item.get("raw_result_id"))
                for item in support_lineage
                if item.get("raw_evidence_id") or item.get("raw_result_id")
            }),
            "origin_task_execution_ids": sorted({
                str(item.get("origin_task_execution_id"))
                for item in support_lineage
                if item.get("origin_task_execution_id") not in UNKNOWN
            }),
            "origin_task_ids": sorted({
                str(item.get("origin_task_id"))
                for item in support_lineage
                if item.get("origin_task_id") not in UNKNOWN
            }),
            "qualification_support_lineage_state": (
                "CAPABILITY_ASSESSMENT_LINEAGE_COMPLETE"
                if support_lineage and all(
                    item.get("accepted_evidence_origin_state")
                    == "TASK_ORIGIN_PRESERVED"
                    for item in support_lineage
                )
                else "CAPABILITY_ASSESSMENT_LINEAGE_NOT_APPLICABLE"
                if not support_lineage
                else "CAPABILITY_ASSESSMENT_LINEAGE_PARTIAL"
            ),
            "task_provenance_authority": "NONE",
            "rejected_evidence": rejected,
            "blocking_rejected_evidence_count": len([
                item for item in rejected
                if item.get("rejection_reason")
                != "not_current_active_accepted_evidence"
            ]),
            "valid_accepted_evidence_count": len(valid),
            "observed_supporting_evidence_count": observed_count,
            "causal_supporting_evidence_count": causal_count,
            "independent_source_count": independent_count,
            "required_independent_sources": required_sources,
            "source_coverage": coverage,
            "causal_support_state": (
                "CAUSALLY_SUPPORTED" if causal_count else "CAUSAL_SUPPORT_NOT_ESTABLISHED"
            ),
            "reproducibility_state": (
                "REPRODUCIBLY_SUPPORTED"
                if causal_count and independent_count >= required_sources
                else "INSUFFICIENT_INDEPENDENT_CAUSAL_REPLICATION"
                if causal_count
                else "REPRODUCIBILITY_NOT_EVALUABLE_WITHOUT_CAUSAL_SUPPORT"
            ),
            "source_independence_contract": "PROVENANCE_DERIVED_SOURCE_IDENTITY",
            "source_independence_inflation_count": int(
                coverage.get("duplicate_supporting_evidence_count") or 0
            ),
            "authority": {
                "qualification": "NONE",
                "truth": "NONE",
                "knowledge": "NONE",
                "runtime": "NONE",
                "budget": "NONE",
                "cognitive": "NONE",
            },
        }

    def decide(
        self,
        capability_subject: CapabilitySubject | Mapping[str, Any],
        accepted_evidence: Iterable[Mapping[str, Any]] | None,
        *,
        requested_level: CapabilityQualificationLevel | str,
        current_level: CapabilityQualificationLevel | str = (
            CapabilityQualificationLevel.NOT_QUALIFIED
        ),
        architecture_present: bool = False,
        runtime_reachable: bool = False,
        assessment_run_id: str = "current_run",
        required_independent_sources: int | None = None,
    ) -> dict[str, Any]:
        subject = _subject_payload(capability_subject)
        capability_id = capability_id_for_subject(subject)
        requested = _level(requested_level)
        current = _level(current_level)
        assessment = self.assess_capability_evidence(
            subject,
            accepted_evidence,
            assessment_run_id=assessment_run_id,
            required_independent_sources=required_independent_sources,
        )
        failures = self._promotion_failures(
            capability_id=capability_id,
            requested=requested,
            current=current,
            assessment=assessment,
            architecture_present=architecture_present,
            runtime_reachable=runtime_reachable,
        )
        granted = current if failures else requested
        state = "PROMOTION_DENIED" if failures else "PROMOTION_GRANTED"
        decision = {
            "schema_version": self.schema_version,
            "system": self.system_name,
        "qualification_decision_id": self._stable_id(
                "qualification_decision",
                {
                    "capability_id": capability_id,
                    "requested_level": requested.value,
                    "current_level": current.value,
                    "assessment_id": assessment["capability_evidence_assessment_id"],
                    "failures": failures,
                },
            ),
            "capability_id": capability_id,
            "capability_subject": subject,
            "capability_evidence_assessment_id": assessment[
                "capability_evidence_assessment_id"
            ],
            "current_level": current.value,
            "requested_level": requested.value,
            "granted_level": granted.value,
            "decision_state": state,
            "decision_reason": failures[0] if failures else "requirements_satisfied",
            "promotion_failures": failures,
            "accepted_evidence_ids": assessment["accepted_evidence_ids"],
            "capability_evidence_support_lineage": assessment.get(
                "supporting_accepted_evidence_refs", []
            ),
            "raw_evidence_ids": assessment.get("raw_evidence_ids", []),
            "origin_task_execution_ids": assessment.get(
                "origin_task_execution_ids", []
            ),
            "qualification_support_lineage_state": (
                "QUALIFICATION_SUPPORT_LINEAGE_COMPLETE"
                if assessment.get("qualification_support_lineage_state")
                == "CAPABILITY_ASSESSMENT_LINEAGE_COMPLETE"
                else "QUALIFICATION_SUPPORT_LINEAGE_NOT_APPLICABLE"
                if not assessment.get("accepted_evidence_ids")
                else "QUALIFICATION_SUPPORT_LINEAGE_PARTIAL"
            ),
            "qualification_support_attribution_semantics": (
                "DIRECT_SUPPORT_LINEAGE"
                if assessment.get("origin_task_execution_ids")
                else "ATTRIBUTION_UNRESOLVED"
            ),
            "task_provenance_authority": "NONE",
            "independent_source_count": assessment["independent_source_count"],
            "causal_support_state": assessment["causal_support_state"],
            "reproducibility_state": assessment["reproducibility_state"],
            "qualification_authority": self.qualification_authority,
            "qualification_authority_count": 1,
            "accepted_evidence_required": True,
            "raw_result_promotion_allowed": False,
            "evaluation_direct_promotion_allowed": False,
            "unaccepted_evidence_promotion_allowed": False,
            "task_count_used_as_source_independence": False,
            "run_count_used_as_source_independence": False,
            "qualification_implies_truth": False,
            "qualification_implies_knowledge": False,
            "qualification_implies_budget_authority": False,
            "qualification_implies_cognitive_authority": False,
            "persistence_implies_qualification": False,
            "historical_current_state_distinguished": True,
            "authority": {
                "qualification": self.qualification_authority,
                "truth": "NONE",
                "knowledge": "NONE",
                "runtime": "NONE",
                "budget": "NONE",
                "cognitive": "NONE",
                "reporting": "NONE",
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        decision["decision_fingerprint"] = self._decision_fingerprint(decision)
        return {
            "capability_evidence_assessment": assessment,
            "qualification_decision": decision,
            "capability_qualification_state": self._state_from_decision(decision),
        }

    def persist_decision(self, decision: Mapping[str, Any]) -> dict[str, Any]:
        if self.state_dir is None:
            raise ValueError("state_dir_required_for_persistence")
        self._assert_authoritative_decision(decision)
        decision_dir = self.state_dir / "qualification_decisions"
        state_dir = self.state_dir / "capability_qualification_state"
        history_dir = self.state_dir / "qualification_history"
        decision_dir.mkdir(parents=True, exist_ok=True)
        state_dir.mkdir(parents=True, exist_ok=True)
        history_dir.mkdir(parents=True, exist_ok=True)
        decision_path = decision_dir / f"{decision['qualification_decision_id']}.json"
        current = self.get_current_qualification(decision["capability_id"])
        if current and self._is_stale_decision(decision, current):
            raise ValueError("stale_qualification_decision_rejected")
        decision_path.write_text(
            json.dumps(dict(decision), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        state = self._state_from_decision(decision)
        state_path = state_dir / f"{decision['capability_id']}.json"
        state_path.write_text(
            json.dumps(state, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self._append_history(decision["capability_id"], {
            "event_type": "QUALIFICATION_DECISION",
            "decision": dict(decision),
            "resulting_state": state,
        })
        return {
            "persistence_state": "PERSISTED_BY_QUALIFICATION_AUTHORITY",
            "decision_path": str(decision_path),
            "state_path": str(state_path),
            "history_path": str(history_dir / f"{decision['capability_id']}.json"),
            "persistence_implies_qualification": False,
            "persistence_implies_invalidation": False,
        }

    def review_qualification(
        self,
        current_state: Mapping[str, Any],
        *,
        review_trigger: str,
        trigger_evidence: Mapping[str, Any],
        lifecycle_run_id: str = "current_run",
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        trigger = str(review_trigger or "")
        evidence = dict(trigger_evidence or {})
        failures = self._lifecycle_admission_failures(
            state,
            trigger=trigger,
            trigger_evidence=evidence,
            require_active=True,
        )
        new_status = (
            CapabilityQualificationStatus.ACTIVE.value
            if failures
            else CapabilityQualificationStatus.UNDER_REVIEW.value
        )
        decision = {
            "schema_version": self.schema_version,
            "system": "capability_qualification_review_decision",
            "review_decision_id": self._stable_id(
                "qualification_review_decision",
                {
                    "capability_id": state.get("capability_id"),
                    "previous_decision": state.get("last_qualification_decision_id"),
                    "review_trigger": trigger,
                    "trigger_evidence_id": evidence.get("accepted_evidence_id")
                    or evidence.get("evidence_id"),
                },
            ),
            "capability_id": state.get("capability_id"),
            "previous_qualification_decision_id": state.get(
                "last_qualification_decision_id"
            ),
            "previous_level": state.get("current_qualification_level"),
            "previous_status": state.get("qualification_status"),
            "new_status": new_status,
            "review_trigger": trigger,
            "supporting_evidence_refs": self._trigger_refs(evidence),
            "decision_state": "REVIEW_OPENED" if not failures else "REVIEW_DENIED",
            "decision_reason": failures[0] if failures else trigger,
            "review_failures": failures,
            "authority": self._lifecycle_authority(),
            "qualification_lifecycle_authority": self.qualification_authority,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        decision["decision_fingerprint"] = self._decision_fingerprint(decision)
        return decision

    def invalidate_qualification(
        self,
        current_state: Mapping[str, Any],
        review_decision: Mapping[str, Any],
        *,
        invalidation_reason: str,
        supporting_evidence_refs: Iterable[str] | None = None,
        lifecycle_run_id: str = "current_run",
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        review = dict(review_decision or {})
        failures = self._invalidation_failures(state, review)
        new_status = (
            CapabilityQualificationStatus.UNDER_REVIEW.value
            if failures
            else CapabilityQualificationStatus.INVALIDATED.value
        )
        decision = {
            "schema_version": self.schema_version,
            "system": "capability_qualification_invalidation_decision",
            "invalidation_decision_id": self._stable_id(
                "qualification_invalidation_decision",
                {
                    "capability_id": state.get("capability_id"),
                    "review_decision_id": review.get("review_decision_id"),
                    "reason": invalidation_reason,
                },
            ),
            "capability_id": state.get("capability_id"),
            "previous_qualification_decision_id": state.get(
                "last_qualification_decision_id"
            ),
            "previous_level": state.get("current_qualification_level"),
            "previous_status": state.get("qualification_status"),
            "new_status": new_status,
            "invalidation_reason": str(invalidation_reason or "UNKNOWN"),
            "supporting_evidence_refs": sorted(
                str(item) for item in supporting_evidence_refs or []
            ),
            "source_independence_state": review.get(
                "review_trigger",
                "GOVERNANCE_REVIEW_REQUIRED",
            ),
            "causal_support_state": (
                "WITHDRAWN"
                if review.get("review_trigger") == "CAUSAL_SUPPORT_WITHDRAWN"
                else "NOT_REASSESSED"
            ),
            "reproducibility_state": (
                "INVALIDATED"
                if review.get("review_trigger")
                == "REPRODUCIBILITY_SUPPORT_INVALIDATED"
                else "NOT_REASSESSED"
            ),
            "decision_state": (
                "QUALIFICATION_INVALIDATED" if not failures else "INVALIDATION_DENIED"
            ),
            "decision_reason": failures[0] if failures else str(invalidation_reason),
            "invalidation_failures": failures,
            "authority": self._lifecycle_authority(),
            "qualification_lifecycle_authority": self.qualification_authority,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        decision["decision_fingerprint"] = self._decision_fingerprint(decision)
        return decision

    def revalidate(
        self,
        current_state: Mapping[str, Any],
        accepted_evidence: Iterable[Mapping[str, Any]] | None,
        *,
        requested_level: CapabilityQualificationLevel | str,
        architecture_present: bool,
        runtime_reachable: bool,
        assessment_run_id: str = "current_run",
        required_independent_sources: int | None = None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        if state.get("qualification_status") not in {
            CapabilityQualificationStatus.UNDER_REVIEW.value,
            CapabilityQualificationStatus.INVALIDATED.value,
            CapabilityQualificationStatus.REVALIDATION_REQUIRED.value,
        }:
            raise ValueError("revalidation_requires_review_or_invalidated_state")
        subject = state.get("capability_subject")
        if not isinstance(subject, Mapping):
            raise ValueError("revalidation_requires_capability_subject")
        result = self.decide(
            subject,
            accepted_evidence,
            requested_level=requested_level,
            current_level=CapabilityQualificationLevel.NOT_QUALIFIED,
            architecture_present=architecture_present,
            runtime_reachable=runtime_reachable,
            assessment_run_id=assessment_run_id,
            required_independent_sources=required_independent_sources,
        )
        decision = result["qualification_decision"]
        if decision["capability_id"] != state.get("capability_id"):
            raise ValueError("cross_capability_revalidation_rejected")
        revalidation = {
            "schema_version": self.schema_version,
            "system": "capability_qualification_revalidation_decision",
            "revalidation_decision_id": self._stable_id(
                "qualification_revalidation_decision",
                {
                    "capability_id": state.get("capability_id"),
                    "previous_decision": state.get("last_qualification_decision_id"),
                    "new_decision": decision["qualification_decision_id"],
                },
            ),
            "capability_id": state.get("capability_id"),
            "previous_qualification_decision_id": state.get(
                "last_qualification_decision_id"
            ),
            "new_qualification_decision_id": decision["qualification_decision_id"],
            "previous_level": state.get("current_qualification_level"),
            "granted_level": decision["granted_level"],
            "result": self._revalidation_result(
                state.get("current_qualification_level"),
                decision["granted_level"],
                decision["decision_state"],
            ),
            "decision_state": "REVALIDATION_DECIDED",
            "authority": self._lifecycle_authority(),
            "qualification_lifecycle_authority": self.qualification_authority,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        revalidation["decision_fingerprint"] = self._decision_fingerprint(
            revalidation
        )
        result["revalidation_decision"] = revalidation
        result["capability_qualification_state"] = self._state_from_decision(
            decision,
            qualification_status=(
                CapabilityQualificationStatus.ACTIVE
                if decision["decision_state"] == "PROMOTION_GRANTED"
                else CapabilityQualificationStatus.INVALIDATED
            ),
        )
        return result

    def persist_review_decision(
        self,
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self._persist_lifecycle_decision(
            decision,
            decision_key="review_decision_id",
            directory_name="qualification_review_decisions",
            state_status=decision.get("new_status"),
        )

    def persist_invalidation_decision(
        self,
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self._persist_lifecycle_decision(
            decision,
            decision_key="invalidation_decision_id",
            directory_name="qualification_invalidation_decisions",
            state_status=decision.get("new_status"),
        )

    def persist_revalidation_decision(
        self,
        result: Mapping[str, Any],
    ) -> dict[str, Any]:
        decision = result.get("qualification_decision")
        revalidation = result.get("revalidation_decision")
        if not isinstance(decision, Mapping) or not isinstance(revalidation, Mapping):
            raise ValueError("revalidation_result_requires_decisions")
        self.persist_decision(decision)
        return self._persist_lifecycle_decision(
            revalidation,
            decision_key="revalidation_decision_id",
            directory_name="qualification_revalidation_decisions",
            state_status=result.get("capability_qualification_state", {}).get(
                "qualification_status"
            ),
            replacement_state=result.get("capability_qualification_state"),
        )

    def get_current_qualification(self, capability_id: str) -> dict[str, Any] | None:
        if self.state_dir is None:
            return None
        path = self.state_dir / "capability_qualification_state" / f"{capability_id}.json"
        if not path.exists():
            return None
        state = json.loads(path.read_text(encoding="utf-8"))
        if state.get("state_authority") != self.qualification_authority:
            return None
        return state

    def get_qualification_history(self, capability_id: str) -> list[dict[str, Any]]:
        if self.state_dir is None:
            return []
        path = self.state_dir / "qualification_history" / f"{capability_id}.json"
        if not path.exists():
            return []
        rows = json.loads(path.read_text(encoding="utf-8"))
        return rows if isinstance(rows, list) else []

    def _accepted_evidence_rejection(
        self,
        item: Mapping[str, Any],
        capability_id: str,
        subject: Mapping[str, Any],
    ) -> str | None:
        if item.get("evidence_acceptance_state") != "ACCEPTED":
            return "not_accepted_evidence"
        if not self.evidence_lifecycle_engine.is_currently_accepted(item):
            return "not_current_active_accepted_evidence"
        if item.get("evidence_decision_id") in UNKNOWN:
            return "missing_evidence_decision_id"
        if item.get("accepted_evidence_id") in UNKNOWN:
            return "missing_accepted_evidence_id"
        if item.get("claim_id") in UNKNOWN:
            return "missing_claim_id"
        if item.get("claim_evidence_binding_state") != "BOUND":
            return "claim_evidence_binding_not_bound"
        binding = item.get("claim_evidence_binding")
        if isinstance(binding, Mapping):
            if binding.get("claim_id") != item.get("claim_id"):
                return "claim_evidence_binding_claim_mismatch"
            if binding.get("accepted_evidence_id") != item.get("accepted_evidence_id"):
                return "claim_evidence_binding_evidence_mismatch"
        item_capability = item.get("capability_id")
        if item_capability not in UNKNOWN and item_capability != capability_id:
            return "capability_id_mismatch"
        item_operation = _token(
            item.get("target_operation")
            or item.get("source_operation")
            or item.get("operation")
        )
        if item_operation not in UNKNOWN and item_operation != subject["operation"]:
            return "capability_operation_mismatch"
        provenance = item.get("source_provenance")
        if isinstance(provenance, Mapping):
            if provenance.get("source_provenance_state") != "SOURCE_PROVENANCE_BOUND":
                return "source_provenance_not_bound"
        else:
            source_identity = self.source_engine.source_identity(item)
            if source_identity.get("source_identity_state") != "PROVEN":
                return "source_provenance_not_bound"
        return None

    def _source_flattened(self, item: Mapping[str, Any]) -> dict[str, Any]:
        flattened = dict(item)
        provenance = item.get("source_provenance")
        if isinstance(provenance, Mapping):
            for key in (
                "producer_operation_id",
                "producer_component_id",
                "producer_source_type",
                "source_lineage",
                "run_id",
                "task_id",
                "raw_validation_result_id",
                "origin_task_execution_id",
                "origin_run_id",
                "origin_task_id",
                "origin_attempt_id",
                "origin_operation_id",
                "origin_lineage_fingerprint",
            ):
                if key in provenance and key not in flattened:
                    flattened[key] = provenance[key]
            if "source_lineage" not in flattened and "upstream_lineage_refs" in provenance:
                flattened["source_lineage"] = provenance["upstream_lineage_refs"]
            if "raw_result_id" not in flattened:
                flattened["raw_result_id"] = provenance.get("raw_validation_result_id")
        origin = item.get("accepted_evidence_origin")
        if isinstance(origin, Mapping):
            for key in (
                "raw_evidence_id",
                "raw_result_id",
                "origin_task_execution_id",
                "origin_run_id",
                "origin_task_id",
                "origin_attempt_id",
                "origin_operation_id",
                "origin_lineage_fingerprint",
                "accepted_evidence_origin_state",
            ):
                if key in origin and key not in flattened:
                    flattened[key] = origin[key]
        return flattened

    def _accepted_evidence_support_lineage(
        self,
        item: Mapping[str, Any],
    ) -> dict[str, Any]:
        origin = item.get("accepted_evidence_origin")
        origin = dict(origin) if isinstance(origin, Mapping) else {}
        return {
            "accepted_evidence_id": item.get("accepted_evidence_id"),
            "evidence_decision_id": item.get("evidence_decision_id"),
            "raw_evidence_id": (
                origin.get("raw_evidence_id")
                or item.get("raw_evidence_id")
                or item.get("raw_result_id")
                or item.get("raw_validation_result_id")
            ),
            "raw_result_id": (
                origin.get("raw_result_id")
                or item.get("raw_result_id")
                or item.get("raw_validation_result_id")
            ),
            "origin_task_execution_id": (
                origin.get("origin_task_execution_id")
                or item.get("origin_task_execution_id")
            ),
            "origin_run_id": origin.get("origin_run_id") or item.get("origin_run_id"),
            "origin_task_id": (
                origin.get("origin_task_id") or item.get("origin_task_id")
            ),
            "origin_attempt_id": (
                origin.get("origin_attempt_id") or item.get("origin_attempt_id")
            ),
            "origin_operation_id": (
                origin.get("origin_operation_id")
                or item.get("origin_operation_id")
            ),
            "origin_lineage_fingerprint": (
                origin.get("origin_lineage_fingerprint")
                or item.get("origin_lineage_fingerprint")
            ),
            "accepted_evidence_origin_state": (
                origin.get("accepted_evidence_origin_state")
                or item.get("accepted_evidence_origin_state")
                or "LEGACY_ORIGIN_UNVERIFIED"
            ),
            "source_identity": item.get("canonical_source_identity"),
            "producer_operation_id": item.get("producer_operation_id"),
            "task_provenance_authority": "NONE",
            "qualification_authority": "NONE",
        }

    def _causal_support_state(self, item: Mapping[str, Any]) -> str:
        value = str(
            item.get("capability_causal_support_state")
            or item.get("causal_support_state")
            or item.get("causal_attribution_state")
            or ""
        ).upper()
        if value in {
            "CAUSALLY_SUPPORTED",
            "CAUSALLY_DEMONSTRATED",
            "MATERIAL_CONTRIBUTION_DEMONSTRATED",
        }:
            return "CAUSALLY_SUPPORTED"
        return "CAUSAL_SUPPORT_NOT_ESTABLISHED"

    def _promotion_failures(
        self,
        *,
        capability_id: str,
        requested: CapabilityQualificationLevel,
        current: CapabilityQualificationLevel,
        assessment: Mapping[str, Any],
        architecture_present: bool,
        runtime_reachable: bool,
    ) -> list[str]:
        failures = []
        if capability_id in UNKNOWN:
            failures.append("missing_capability_id")
        if requested not in ORDERED_LEVELS:
            failures.append("unsupported_requested_level")
            return failures
        if _level_index(requested) < _level_index(current):
            failures.append("demotion_requires_review")
        if not architecture_present:
            failures.append("architecture_presence_not_established")
        if _level_index(requested) >= _level_index(
            CapabilityQualificationLevel.RUNTIME_REACHABLE
        ) and not runtime_reachable:
            failures.append("runtime_reachability_not_established")
        if _level_index(requested) >= _level_index(
            CapabilityQualificationLevel.OPERATIONALLY_OBSERVED
        ) and not assessment.get("valid_accepted_evidence_count"):
            failures.append("accepted_evidence_missing")
        if _level_index(requested) >= _level_index(
            CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED
        ) and assessment.get("causal_support_state") != "CAUSALLY_SUPPORTED":
            failures.append("causal_support_not_established")
        if _level_index(requested) >= _level_index(
            CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED
        ):
            required = int(assessment.get("required_independent_sources") or 0)
            observed = int(assessment.get("independent_source_count") or 0)
            if observed < required:
                failures.append("independent_reproducibility_not_established")
        if assessment.get("blocking_rejected_evidence_count"):
            failures.append("some_evidence_rejected")
        return sorted(set(failures))

    def _state_from_decision(
        self,
        decision: Mapping[str, Any],
        *,
        qualification_status: CapabilityQualificationStatus = (
            CapabilityQualificationStatus.ACTIVE
        ),
    ) -> dict[str, Any]:
        if (
            decision.get("decision_state") != "PROMOTION_GRANTED"
            and qualification_status == CapabilityQualificationStatus.ACTIVE
        ):
            qualification_status = CapabilityQualificationStatus.REVALIDATION_REQUIRED
        status = (
            qualification_status.value
            if isinstance(qualification_status, CapabilityQualificationStatus)
            else str(qualification_status)
        )
        active = (
            decision.get("decision_state") == "PROMOTION_GRANTED"
            and status == CapabilityQualificationStatus.ACTIVE.value
        )
        return {
            "schema_version": self.schema_version,
            "system": "capability_qualification_state",
            "capability_id": decision.get("capability_id"),
            "capability_subject": decision.get("capability_subject"),
            "current_qualification_level": decision.get("granted_level"),
            "qualification_status": status,
            "current_authority_state": (
                "CURRENT_ACTIVE_QUALIFICATION" if active else "NO_ACTIVE_QUALIFICATION"
            ),
            "last_qualification_decision_id": decision.get(
                "qualification_decision_id"
            ),
            "current_lifecycle_decision_id": decision.get(
                "qualification_decision_id"
            ),
            "decision_state": decision.get("decision_state"),
            "state_authority": (
                self.qualification_authority
                if decision.get("qualification_authority")
                == self.qualification_authority
                else "NONE"
            ),
            "historical_record": False,
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "runtime_authority": "NONE",
            "budget_authority": "NONE",
            "cognitive_authority": "NONE",
            "created_at": decision.get("created_at"),
        }

    def _persist_lifecycle_decision(
        self,
        decision: Mapping[str, Any],
        *,
        decision_key: str,
        directory_name: str,
        state_status: Any,
        replacement_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.state_dir is None:
            raise ValueError("state_dir_required_for_persistence")
        decision = dict(decision or {})
        decision_id = decision.get(decision_key)
        if not decision_id:
            raise ValueError(f"{decision_key}_required")
        if decision.get("qualification_lifecycle_authority") != self.qualification_authority:
            raise ValueError("qualification_lifecycle_authority_required")
        if not self._decision_fingerprint_valid(decision):
            raise ValueError("corrupted_lifecycle_decision_fingerprint")
        capability_id = decision.get("capability_id")
        current = self.get_current_qualification(str(capability_id))
        if current and current.get("capability_id") != capability_id:
            raise ValueError("cross_capability_lifecycle_decision_rejected")
        decision_dir = self.state_dir / directory_name
        state_dir = self.state_dir / "capability_qualification_state"
        decision_dir.mkdir(parents=True, exist_ok=True)
        state_dir.mkdir(parents=True, exist_ok=True)
        decision_path = decision_dir / f"{decision_id}.json"
        decision_path.write_text(
            json.dumps(decision, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        if replacement_state is not None:
            state = dict(replacement_state)
        else:
            state = dict(current or {})
            if not state:
                raise ValueError("current_qualification_required")
            state["qualification_status"] = state_status
            state["current_authority_state"] = (
                "CURRENT_ACTIVE_QUALIFICATION"
                if state_status == CapabilityQualificationStatus.ACTIVE.value
                else "NO_ACTIVE_QUALIFICATION"
            )
            state["current_lifecycle_decision_id"] = decision_id
            state["last_lifecycle_reason"] = (
                decision.get("review_trigger")
                or decision.get("invalidation_reason")
                or decision.get("result")
            )
            state["created_at"] = decision.get("created_at", state.get("created_at"))
        state_path = state_dir / f"{capability_id}.json"
        state_path.write_text(
            json.dumps(state, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self._append_history(str(capability_id), {
            "event_type": directory_name.upper(),
            "decision": decision,
            "resulting_state": state,
        })
        return {
            "persistence_state": "PERSISTED_BY_QUALIFICATION_AUTHORITY",
            "decision_path": str(decision_path),
            "state_path": str(state_path),
            "persistence_implies_qualification": False,
            "persistence_implies_invalidation": False,
        }

    def _append_history(self, capability_id: str, row: Mapping[str, Any]) -> None:
        if self.state_dir is None:
            return
        history_dir = self.state_dir / "qualification_history"
        history_dir.mkdir(parents=True, exist_ok=True)
        path = history_dir / f"{capability_id}.json"
        rows = []
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            rows = existing if isinstance(existing, list) else []
        rows.append(dict(row))
        path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")

    def _assert_authoritative_decision(self, decision: Mapping[str, Any]) -> None:
        if not decision.get("qualification_decision_id"):
            raise ValueError("qualification_decision_id_required")
        if decision.get("qualification_authority") != self.qualification_authority:
            raise ValueError("qualification_authority_required")
        if not self._decision_fingerprint_valid(decision):
            raise ValueError("corrupted_decision_fingerprint")

    def _decision_fingerprint(self, decision: Mapping[str, Any]) -> str:
        payload = {
            key: value
            for key, value in dict(decision).items()
            if key != "decision_fingerprint"
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str).encode(
                "utf-8"
            )
        ).hexdigest()

    def _decision_fingerprint_valid(self, decision: Mapping[str, Any]) -> bool:
        fingerprint = decision.get("decision_fingerprint")
        return bool(fingerprint and fingerprint == self._decision_fingerprint(decision))

    def _is_stale_decision(
        self,
        decision: Mapping[str, Any],
        current_state: Mapping[str, Any],
    ) -> bool:
        if (
            current_state.get("current_lifecycle_decision_id")
            != current_state.get("last_qualification_decision_id")
            and decision.get("qualification_decision_id")
            == current_state.get("last_qualification_decision_id")
        ):
            return True
        return str(decision.get("created_at") or "") < str(
            current_state.get("created_at") or ""
        )

    def _lifecycle_admission_failures(
        self,
        state: Mapping[str, Any],
        *,
        trigger: str,
        trigger_evidence: Mapping[str, Any],
        require_active: bool,
    ) -> list[str]:
        failures = []
        if state.get("capability_id") in UNKNOWN:
            failures.append("missing_capability_id")
        if state.get("last_qualification_decision_id") in UNKNOWN:
            failures.append("missing_current_qualification_decision")
        if state.get("state_authority") != self.qualification_authority:
            failures.append("missing_current_state_authority")
        if require_active and state.get("qualification_status") != (
            CapabilityQualificationStatus.ACTIVE.value
        ):
            failures.append("active_status_required")
        if trigger not in REVIEW_TRIGGERS:
            failures.append("unsupported_review_trigger")
        if not trigger_evidence:
            failures.append("trigger_evidence_required")
        elif self._trigger_evidence_rejection(trigger_evidence):
            failures.append(self._trigger_evidence_rejection(trigger_evidence))
        if trigger_evidence.get("capability_id") not in UNKNOWN and (
            trigger_evidence.get("capability_id") != state.get("capability_id")
        ):
            failures.append("wrong_capability_id")
        return sorted(set(failures))

    def _invalidation_failures(
        self,
        state: Mapping[str, Any],
        review: Mapping[str, Any],
    ) -> list[str]:
        failures = []
        if review.get("decision_state") != "REVIEW_OPENED":
            failures.append("open_review_decision_required")
        if review.get("capability_id") != state.get("capability_id"):
            failures.append("wrong_capability_id")
        if review.get("qualification_lifecycle_authority") != self.qualification_authority:
            failures.append("qualification_lifecycle_authority_required")
        if not self._decision_fingerprint_valid(review):
            failures.append("corrupted_review_decision_fingerprint")
        if state.get("qualification_status") not in {
            CapabilityQualificationStatus.UNDER_REVIEW.value,
            CapabilityQualificationStatus.ACTIVE.value,
        }:
            failures.append("reviewable_status_required")
        return sorted(set(failures))

    def _trigger_evidence_rejection(self, evidence: Mapping[str, Any]) -> str | None:
        evidence_type = str(evidence.get("evidence_type") or "").upper()
        if evidence_type in {"RAW_RESULT", "RAW_VALIDATION_RESULT"}:
            return "raw_evidence_cannot_trigger_lifecycle"
        if evidence.get("evidence_acceptance_state") in {"REJECTED", "INSUFFICIENT"}:
            return "rejected_evidence_cannot_trigger_lifecycle"
        if evidence.get("source_provenance") == {}:
            return "trigger_provenance_missing"
        return None

    def _trigger_refs(self, evidence: Mapping[str, Any]) -> list[str]:
        refs = [
            evidence.get("accepted_evidence_id"),
            evidence.get("evidence_decision_id"),
            evidence.get("invalidation_evidence_id"),
            evidence.get("evidence_id"),
        ]
        return sorted(str(item) for item in refs if item not in UNKNOWN)

    def _revalidation_result(
        self,
        previous_level: Any,
        granted_level: Any,
        decision_state: str,
    ) -> str:
        if decision_state != "PROMOTION_GRANTED":
            return "INVALIDATED"
        previous = _level(previous_level or CapabilityQualificationLevel.NOT_QUALIFIED)
        granted = _level(granted_level)
        if granted == previous:
            return "RESTORED_SAME_LEVEL"
        if _level_index(granted) < _level_index(previous):
            return "REQUALIFIED_LOWER_LEVEL"
        return "PROMOTED_HIGHER_LEVEL"

    def _lifecycle_authority(self) -> dict[str, str]:
        return {
            "qualification_lifecycle": self.qualification_authority,
            "truth": "NONE",
            "knowledge": "NONE",
            "runtime": "NONE",
            "budget": "NONE",
            "cognitive": "NONE",
            "execution": "NONE",
            "deployment": "NONE",
        }

    def _stable_id(self, prefix: str, payload: Mapping[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        return f"{prefix}_{hashlib.sha1(encoded.encode('utf-8')).hexdigest()[:12]}"


def _subject_payload(subject: CapabilitySubject | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(subject, CapabilitySubject):
        return subject.canonical_payload()
    if not isinstance(subject, Mapping):
        raise ValueError("capability_subject_must_be_mapping")
    payload = {
        "schema_version": str(subject.get("schema_version") or "1.0"),
        "capability_name": _token(subject.get("capability_name")),
        "operation": _token(subject.get("operation")),
        "domain": _token(subject.get("domain", "UNKNOWN")),
        "qualifiers": dict(subject.get("qualifiers") or {}),
    }
    if payload["capability_name"] in UNKNOWN or payload["operation"] in UNKNOWN:
        raise ValueError("capability_subject_requires_name_and_operation")
    return payload


def _level(value: CapabilityQualificationLevel | str) -> CapabilityQualificationLevel:
    if isinstance(value, CapabilityQualificationLevel):
        return value
    return CapabilityQualificationLevel(str(value))


def _level_index(level: CapabilityQualificationLevel) -> int:
    return ORDERED_LEVELS.index(level) if level in ORDERED_LEVELS else -1


def _token(value: Any) -> str:
    return str(value or "UNKNOWN").strip().lower().replace(" ", "_")


capability_qualification_engine = IntegratedCapabilityQualificationEngine()


__all__ = [
    "CapabilityQualificationLevel",
    "CapabilityQualificationStatus",
    "CapabilitySubject",
    "REVIEW_TRIGGERS",
    "IntegratedCapabilityQualificationEngine",
    "capability_id_for_subject",
    "capability_qualification_engine",
]
