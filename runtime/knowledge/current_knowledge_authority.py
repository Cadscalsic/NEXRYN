"""Govern current Knowledge authority separately from CKIL and memory."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.epistemic.accepted_evidence_assessment import (
    AcceptedEvidenceEpistemicAssessmentEngine,
)
from runtime.truth.current_truth_admission import CurrentTruthAdmissionGate
from runtime.validation.accepted_evidence_lifecycle import (
    AcceptedEvidenceLifecycleEngine,
)


UNKNOWN = {None, "", "UNKNOWN", "NOT_AVAILABLE", "Not Available"}


class KnowledgeLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    INVALIDATED = "INVALIDATED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    SUPERSEDED = "SUPERSEDED"


REVIEW_TRIGGERS = {
    "SUPPORTING_TRUTH_UNDER_REVIEW",
    "SUPPORTING_TRUTH_INVALIDATED",
    "SUPPORTING_TRUTH_SUPERSEDED",
    "SUPPORTING_EPISTEMIC_ASSESSMENT_STALE",
    "SUPPORTING_EVIDENCE_REVOKED",
    "SOURCE_INDEPENDENCE_COLLAPSED",
    "CAUSAL_SUPPORT_WITHDRAWN",
    "REPRODUCIBILITY_SUPPORT_INVALIDATED",
    "CONTRADICTORY_CURRENT_SUPPORT",
    "KNOWLEDGE_DECISION_INTEGRITY_FAILURE",
    "KNOWLEDGE_PROVENANCE_INVALID",
    "GOVERNANCE_REVIEW_REQUIRED",
}


@dataclass(frozen=True)
class KnowledgeSubject:
    subject_type: str
    claim_id: str
    scope: str = "GLOBAL"
    context_class: str = "GENERAL"
    domain: str = "GENERAL"

    @property
    def subject_id(self) -> str:
        return self.knowledge_id

    @property
    def knowledge_id(self) -> str:
        seed = {
            "subject_type": _canon(self.subject_type),
            "claim_id": _canon(self.claim_id),
            "scope": _canon(self.scope),
            "context_class": _canon(self.context_class),
            "domain": _canon(self.domain),
        }
        encoded = json.dumps(seed, sort_keys=True, ensure_ascii=True)
        return f"knowledge_{hashlib.sha1(encoded.encode('utf-8')).hexdigest()[:16]}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_type": _canon(self.subject_type),
            "claim_id": _canon(self.claim_id),
            "scope": _canon(self.scope),
            "context_class": _canon(self.context_class),
            "domain": _canon(self.domain),
            "subject_id": self.subject_id,
            "knowledge_id": self.knowledge_id,
            "identity_excludes_run_id": True,
            "identity_excludes_task_id": True,
            "identity_excludes_evidence_id": True,
            "identity_excludes_truth_decision_id": True,
        }


@dataclass(frozen=True)
class KnowledgeCandidate:
    candidate_id: str
    knowledge_id: str
    subject_id: str
    candidate_state: str
    support_dependency_graph: dict[str, Any]
    formation_authority: str
    candidate_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeAssessment:
    assessment_id: str
    knowledge_id: str
    subject_id: str
    assessment_state: str
    commitment_predicate_satisfied: bool
    failures: list[str]
    current_truth_ids: list[str]
    denied_truth_ids: list[str]
    current_epistemic_assessment_ids: list[str]
    stale_epistemic_assessment_ids: list[str]
    current_evidence_ids: list[str]
    noncurrent_evidence_ids: list[str]
    source_independence_state: str
    causal_support_state: str
    reproducibility_state: str
    contradiction_state: str
    support_dependency_graph: dict[str, Any]
    support_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class KnowledgeCurrentAuthorityEngine:
    """The sole owner of current Knowledge lifecycle decisions."""

    schema_version = "1.0"
    system_name = "knowledge_current_authority_engine"
    authority = "KNOWLEDGE_CURRENT_AUTHORITY"

    def __init__(
        self,
        state_dir: str | Path | None = None,
        *,
        truth_admission_gate: CurrentTruthAdmissionGate | None = None,
        epistemic_assessment_engine: AcceptedEvidenceEpistemicAssessmentEngine | None = None,
        evidence_lifecycle_engine: AcceptedEvidenceLifecycleEngine | None = None,
    ) -> None:
        self.state_dir = Path(state_dir) if state_dir is not None else None
        self.truth_admission_gate = truth_admission_gate or CurrentTruthAdmissionGate()
        self.epistemic_assessment_engine = (
            epistemic_assessment_engine or AcceptedEvidenceEpistemicAssessmentEngine()
        )
        self.evidence_lifecycle_engine = (
            evidence_lifecycle_engine or AcceptedEvidenceLifecycleEngine()
        )

    def create_subject(
        self,
        *,
        subject_type: str,
        claim_id: str,
        scope: str = "GLOBAL",
        context_class: str = "GENERAL",
        domain: str = "GENERAL",
    ) -> KnowledgeSubject:
        if subject_type in UNKNOWN:
            raise ValueError("knowledge_subject_type_required")
        if claim_id in UNKNOWN:
            raise ValueError("knowledge_claim_id_required")
        return KnowledgeSubject(
            subject_type=subject_type,
            claim_id=claim_id,
            scope=scope,
            context_class=context_class,
            domain=domain,
        )

    def create_candidate(
        self,
        subject: KnowledgeSubject | Mapping[str, Any],
        support: Mapping[str, Any] | None = None,
    ) -> KnowledgeCandidate:
        subject_record = _subject_record(subject)
        self._assert_subject(subject_record)
        graph = self.support_dependency_graph(support or {})
        seed = {
            "knowledge_id": subject_record["knowledge_id"],
            "subject_id": subject_record["subject_id"],
            "support_dependency_graph": graph,
            "formation_authority": self.authority,
        }
        candidate_id = f"knowledge_candidate_{_sha1(seed)}"
        payload = {
            **seed,
            "candidate_id": candidate_id,
            "candidate_state": "KNOWLEDGE_CANDIDATE_CREATED",
        }
        return KnowledgeCandidate(
            candidate_id=candidate_id,
            knowledge_id=subject_record["knowledge_id"],
            subject_id=subject_record["subject_id"],
            candidate_state=payload["candidate_state"],
            support_dependency_graph=graph,
            formation_authority=self.authority,
            candidate_fingerprint=self._fingerprint(payload),
        )

    def assess_candidate(
        self,
        candidate: KnowledgeCandidate | Mapping[str, Any],
        subject: KnowledgeSubject | Mapping[str, Any],
        *,
        support: Mapping[str, Any] | None = None,
        min_current_truths: int = 1,
        min_independent_sources: int = 1,
    ) -> KnowledgeAssessment:
        candidate_record = _object_dict(candidate)
        subject_record = _subject_record(subject)
        self._assert_subject(subject_record)
        if candidate_record.get("knowledge_id") != subject_record.get("knowledge_id"):
            raise ValueError("candidate_subject_identity_mismatch")
        if candidate_record.get("formation_authority") != self.authority:
            raise ValueError("knowledge_authority_required")

        graph = self.support_dependency_graph(
            support or candidate_record.get("support_dependency_graph") or {}
        )
        failures: list[str] = []
        current_truth_ids: list[str] = []
        denied_truth_ids: list[str] = []
        for truth in graph["supporting_truths"]:
            admission = self.truth_admission_gate.admit_current_truth(
                truth,
                consumer_scope="knowledge_formation",
                expected_claim_id=subject_record["claim_id"],
            )
            if admission.admitted:
                current_truth_ids.append(str(admission.truth_id))
            else:
                denied_truth_ids.append(str(truth.get("truth_id") or "UNKNOWN"))
        if len(current_truth_ids) < int(min_current_truths):
            failures.append("INSUFFICIENT_CURRENT_TRUTH_SUPPORT")
        if denied_truth_ids:
            failures.append("NONCURRENT_TRUTH_SUPPORT_REJECTED")

        current_assessments: list[str] = []
        stale_assessments: list[str] = []
        for assessment in graph["epistemic_assessments"]:
            currentness = self.epistemic_assessment_engine.is_epistemic_assessment_current(
                assessment
            )
            assessment_id = str(
                assessment.get("epistemic_assessment_id")
                or assessment.get("assessment_id")
                or "UNKNOWN"
            )
            if currentness.get("assessment_current_state") == (
                "CURRENT_EPISTEMIC_ASSESSMENT"
            ):
                current_assessments.append(assessment_id)
            else:
                stale_assessments.append(assessment_id)
        if stale_assessments:
            failures.append("STALE_EPISTEMIC_ASSESSMENT_REJECTED")

        current_evidence: list[str] = []
        noncurrent_evidence: list[str] = []
        for evidence in graph["accepted_evidence"]:
            evidence_id = str(
                evidence.get("accepted_evidence_id")
                or evidence.get("evidence_id")
                or "UNKNOWN"
            )
            if self.evidence_lifecycle_engine.is_currently_accepted(evidence):
                current_evidence.append(evidence_id)
            else:
                noncurrent_evidence.append(evidence_id)
        if noncurrent_evidence:
            failures.append("NONCURRENT_ACCEPTED_EVIDENCE_REJECTED")
        if graph["accepted_evidence"] and not current_truth_ids:
            failures.append("DIRECT_EVIDENCE_REQUIRES_TRUTH_MEDIATION")

        source_ids = [str(item) for item in graph["source_identities"] if item not in UNKNOWN]
        if len(set(source_ids)) < int(min_independent_sources):
            failures.append("SOURCE_INDEPENDENCE_INSUFFICIENT")
        if graph["source_independence_state"] in {"COLLAPSED", "NOT_CURRENT"}:
            failures.append("SOURCE_INDEPENDENCE_COLLAPSED")
        if graph["causal_support_state"] in {"WITHDRAWN", "NOT_CURRENT"}:
            failures.append("CAUSAL_SUPPORT_WITHDRAWN")
        if graph["reproducibility_state"] in {"INVALIDATED", "NOT_CURRENT"}:
            failures.append("REPRODUCIBILITY_SUPPORT_INVALIDATED")
        if graph["contradictory_current_support"]:
            failures.append("CONTRADICTORY_CURRENT_SUPPORT")
        if not graph["valid_provenance"]:
            failures.append("KNOWLEDGE_PROVENANCE_INVALID")
        if graph["confidence_only"]:
            failures.append("CONFIDENCE_ONLY_REJECTED")
        if graph["run_count_inflation"] or graph["task_count_inflation"] or graph["artifact_count_inflation"]:
            failures.append("COUNT_INFLATION_REJECTED")

        satisfied = not failures
        state = (
            "KNOWLEDGE_ASSESSMENT_PASSED"
            if satisfied
            else "KNOWLEDGE_ASSESSMENT_DENIED"
        )
        support_fingerprint = self._fingerprint(graph)
        assessment_seed = {
            "knowledge_id": subject_record["knowledge_id"],
            "subject_id": subject_record["subject_id"],
            "support_fingerprint": support_fingerprint,
            "state": state,
            "failures": failures,
        }
        return KnowledgeAssessment(
            assessment_id=f"knowledge_assessment_{_sha1(assessment_seed)}",
            knowledge_id=subject_record["knowledge_id"],
            subject_id=subject_record["subject_id"],
            assessment_state=state,
            commitment_predicate_satisfied=satisfied,
            failures=failures,
            current_truth_ids=sorted(set(current_truth_ids)),
            denied_truth_ids=sorted(set(denied_truth_ids)),
            current_epistemic_assessment_ids=sorted(set(current_assessments)),
            stale_epistemic_assessment_ids=sorted(set(stale_assessments)),
            current_evidence_ids=sorted(set(current_evidence)),
            noncurrent_evidence_ids=sorted(set(noncurrent_evidence)),
            source_independence_state=(
                "PROVENANCE_DERIVED_INDEPENDENCE"
                if len(set(source_ids)) >= int(min_independent_sources)
                else "INSUFFICIENT_INDEPENDENT_SOURCES"
            ),
            causal_support_state=graph["causal_support_state"],
            reproducibility_state=graph["reproducibility_state"],
            contradiction_state=(
                "CONTRADICTORY_CURRENT_SUPPORT"
                if graph["contradictory_current_support"]
                else "NO_UNRESOLVED_CONTRADICTION"
            ),
            support_dependency_graph=graph,
            support_fingerprint=support_fingerprint,
        )

    def commit_knowledge(
        self,
        subject: KnowledgeSubject | Mapping[str, Any],
        candidate: KnowledgeCandidate | Mapping[str, Any],
        assessment: KnowledgeAssessment | Mapping[str, Any],
    ) -> dict[str, Any]:
        subject_record = _subject_record(subject)
        candidate_record = _object_dict(candidate)
        assessment_record = _object_dict(assessment)
        self._assert_subject(subject_record)
        if candidate_record.get("knowledge_id") != subject_record["knowledge_id"]:
            raise ValueError("cross_knowledge_candidate_rejected")
        if assessment_record.get("knowledge_id") != subject_record["knowledge_id"]:
            raise ValueError("cross_knowledge_assessment_rejected")
        if not assessment_record.get("commitment_predicate_satisfied"):
            return self._decision(
                kind="denial",
                subject=subject_record,
                candidate_id=candidate_record.get("candidate_id"),
                assessment=assessment_record,
                previous_decision_id=None,
                previous_status=None,
                new_status="DECISION_DENIED",
                reason="knowledge_commitment_predicate_failed",
            )
        return self._decision(
            kind="activation",
            subject=subject_record,
            candidate_id=candidate_record.get("candidate_id"),
            assessment=assessment_record,
            previous_decision_id=None,
            previous_status=None,
            new_status=KnowledgeLifecycleStatus.ACTIVE.value,
            reason="knowledge_commitment_predicate_satisfied",
        )

    def open_review(
        self,
        current_state: Mapping[str, Any],
        *,
        review_trigger: str,
        support_signal: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        self._assert_current_state(state)
        if review_trigger not in REVIEW_TRIGGERS:
            raise ValueError("unsupported_knowledge_review_trigger")
        return self._decision(
            kind="review",
            subject=state,
            candidate_id=state.get("knowledge_candidate_id"),
            assessment=state.get("knowledge_assessment", {}),
            previous_decision_id=state["current_knowledge_decision_id"],
            previous_status=state["lifecycle_status"],
            new_status=KnowledgeLifecycleStatus.UNDER_REVIEW.value,
            reason=review_trigger,
            support_signal=support_signal,
            extra={"review_trigger": review_trigger},
        )

    def reassess_under_review(
        self,
        current_state: Mapping[str, Any],
        *,
        assessment: KnowledgeAssessment | Mapping[str, Any],
        decision_result: str | None = None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        self._assert_current_state(state)
        if state["lifecycle_status"] != KnowledgeLifecycleStatus.UNDER_REVIEW.value:
            raise ValueError("knowledge_under_review_required")
        assessment_record = _object_dict(assessment)
        if assessment_record.get("knowledge_id") != state["knowledge_id"]:
            raise ValueError("cross_knowledge_assessment_rejected")
        if decision_result is None:
            decision_result = (
                "RESTORED_ACTIVE"
                if assessment_record.get("commitment_predicate_satisfied")
                else "INVALIDATED"
            )
        status = {
            "RESTORED_ACTIVE": KnowledgeLifecycleStatus.ACTIVE.value,
            "INVALIDATED": KnowledgeLifecycleStatus.INVALIDATED.value,
            "REVALIDATION_REQUIRED": KnowledgeLifecycleStatus.REVALIDATION_REQUIRED.value,
            "SUPERSEDED": KnowledgeLifecycleStatus.SUPERSEDED.value,
        }.get(decision_result)
        if status is None:
            raise ValueError("unsupported_knowledge_reassessment_result")
        return self._decision(
            kind="reassessment",
            subject=state,
            candidate_id=state.get("knowledge_candidate_id"),
            assessment=assessment_record,
            previous_decision_id=state["current_knowledge_decision_id"],
            previous_status=state["lifecycle_status"],
            new_status=status,
            reason=decision_result,
            extra={"support_reassessment": assessment_record},
        )

    def invalidate_knowledge(
        self,
        current_state: Mapping[str, Any],
        *,
        reason: str,
        assessment: KnowledgeAssessment | Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        self._assert_current_state(state)
        if state["lifecycle_status"] != KnowledgeLifecycleStatus.UNDER_REVIEW.value:
            raise ValueError("knowledge_review_required_before_invalidation")
        return self._decision(
            kind="invalidation",
            subject=state,
            candidate_id=state.get("knowledge_candidate_id"),
            assessment=_object_dict(assessment or state.get("knowledge_assessment", {})),
            previous_decision_id=state["current_knowledge_decision_id"],
            previous_status=state["lifecycle_status"],
            new_status=KnowledgeLifecycleStatus.INVALIDATED.value,
            reason=reason,
        )

    def revalidate_knowledge(
        self,
        current_state: Mapping[str, Any],
        *,
        candidate: KnowledgeCandidate | Mapping[str, Any],
        assessment: KnowledgeAssessment | Mapping[str, Any],
        reason: str = "fresh_current_support_verified",
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        self._assert_current_state(state)
        if state["lifecycle_status"] not in {
            KnowledgeLifecycleStatus.INVALIDATED.value,
            KnowledgeLifecycleStatus.UNDER_REVIEW.value,
            KnowledgeLifecycleStatus.REVALIDATION_REQUIRED.value,
        }:
            raise ValueError("revalidation_requires_non_active_knowledge_state")
        candidate_record = _object_dict(candidate)
        assessment_record = _object_dict(assessment)
        if candidate_record.get("knowledge_id") != state["knowledge_id"]:
            raise ValueError("cross_knowledge_candidate_rejected")
        if assessment_record.get("knowledge_id") != state["knowledge_id"]:
            raise ValueError("cross_knowledge_assessment_rejected")
        if not assessment_record.get("commitment_predicate_satisfied"):
            raise ValueError("fresh_current_knowledge_support_required")
        return self._decision(
            kind="revalidation",
            subject=state,
            candidate_id=candidate_record.get("candidate_id"),
            assessment=assessment_record,
            previous_decision_id=state["current_knowledge_decision_id"],
            previous_status=state["lifecycle_status"],
            new_status=KnowledgeLifecycleStatus.ACTIVE.value,
            reason=reason,
        )

    def supersede_knowledge(
        self,
        current_state: Mapping[str, Any],
        *,
        replacement_subject: KnowledgeSubject | Mapping[str, Any],
        replacement_candidate: KnowledgeCandidate | Mapping[str, Any],
        replacement_assessment: KnowledgeAssessment | Mapping[str, Any],
        reason: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        state = dict(current_state or {})
        self._assert_current_state(state)
        replacement_subject_record = _subject_record(replacement_subject)
        replacement_candidate_record = _object_dict(replacement_candidate)
        replacement_assessment_record = _object_dict(replacement_assessment)
        supersession = self._decision(
            kind="supersession",
            subject=state,
            candidate_id=state.get("knowledge_candidate_id"),
            assessment=state.get("knowledge_assessment", {}),
            previous_decision_id=state["current_knowledge_decision_id"],
            previous_status=state["lifecycle_status"],
            new_status=KnowledgeLifecycleStatus.SUPERSEDED.value,
            reason=reason,
            extra={
                "replacement_knowledge_id": replacement_subject_record["knowledge_id"],
                "supersession_relation": "EXPLICIT_GOVERNED_REPLACEMENT",
            },
        )
        replacement = self.commit_knowledge(
            replacement_subject_record,
            replacement_candidate_record,
            replacement_assessment_record,
        )
        return supersession, replacement

    def current_state_from_decision(
        self,
        current_state: Mapping[str, Any],
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        previous = dict(current_state or {})
        item = dict(decision or {})
        self._assert_decision(item)
        if item.get("new_status") == "DECISION_DENIED":
            raise ValueError("denied_knowledge_decision_cannot_create_current_state")
        if previous:
            if item.get("knowledge_id") != previous.get("knowledge_id"):
                raise ValueError("cross_knowledge_decision_rejected")
            if item.get("subject_id") != previous.get("subject_id"):
                raise ValueError("cross_knowledge_subject_decision_rejected")
            if item.get("previous_knowledge_decision_id") != previous.get(
                "current_knowledge_decision_id"
            ):
                raise ValueError("out_of_order_knowledge_decision_rejected")
        state = {
            "schema_version": self.schema_version,
            "system": "current_knowledge_state",
            "knowledge_id": item["knowledge_id"],
            "subject_id": item["subject_id"],
            "subject_type": item["subject_type"],
            "claim_id": item["claim_id"],
            "scope": item["scope"],
            "context_class": item["context_class"],
            "domain": item["domain"],
            "knowledge_candidate_id": item.get("knowledge_candidate_id"),
            "knowledge_assessment": dict(item.get("knowledge_assessment") or {}),
            "lifecycle_status": item["new_status"],
            "current_authority_status": (
                "CURRENT_KNOWLEDGE_AUTHORITY_VERIFIED"
                if item["new_status"] == KnowledgeLifecycleStatus.ACTIVE.value
                else "NO_CURRENT_ACTIVE_KNOWLEDGE_AUTHORITY"
            ),
            "current_knowledge_decision_id": self._decision_id(item),
            "previous_knowledge_decision_id": item.get("previous_knowledge_decision_id"),
            "support_dependency_graph": dict(item.get("support_dependency_graph") or {}),
            "knowledge_under_review": item["new_status"] == KnowledgeLifecycleStatus.UNDER_REVIEW.value,
            "knowledge_invalidated": item["new_status"] == KnowledgeLifecycleStatus.INVALIDATED.value,
            "knowledge_superseded": item["new_status"] == KnowledgeLifecycleStatus.SUPERSEDED.value,
            "authority": self.authority,
            "knowledge_authority": self.authority,
            "truth_authority": "NONE",
            "capability_authority": "NONE",
            "planning_authority": "NONE",
            "self_improvement_authority": "NONE",
            "runtime_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "updated_at": item.get("created_at"),
        }
        state["fingerprint"] = self._fingerprint(state)
        return state

    def persist_current_state(
        self,
        current_state: Mapping[str, Any],
        *,
        lifecycle_decision: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.state_dir is None:
            raise ValueError("state_dir_required_for_persistence")
        state = dict(current_state or {})
        self._assert_current_state(state)
        root = self.state_dir
        current_dir = root / "current_knowledge_state"
        history_dir = root / "knowledge_history"
        decision_dir = root / "knowledge_decisions"
        pointer_dir = root / "current_knowledge_decision_pointer"
        current_dir.mkdir(parents=True, exist_ok=True)
        history_dir.mkdir(parents=True, exist_ok=True)
        decision_dir.mkdir(parents=True, exist_ok=True)
        pointer_dir.mkdir(parents=True, exist_ok=True)
        knowledge_id = state["knowledge_id"]
        current_path = current_dir / f"{knowledge_id}.json"
        pointer_path = pointer_dir / f"{knowledge_id}.json"
        current_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        pointer = {
            "knowledge_id": knowledge_id,
            "current_knowledge_decision_id": state["current_knowledge_decision_id"],
            "current_state_fingerprint": state["fingerprint"],
            "authority": self.authority,
        }
        pointer["fingerprint"] = self._fingerprint(pointer)
        pointer_path.write_text(json.dumps(pointer, indent=2, sort_keys=True), encoding="utf-8")
        decision = dict(lifecycle_decision or {})
        if decision:
            self._assert_decision(decision)
            decision_path = decision_dir / f"{self._decision_id(decision)}.json"
            decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True), encoding="utf-8")
        history_path = history_dir / f"{knowledge_id}.json"
        history = []
        if history_path.exists():
            loaded = json.loads(history_path.read_text(encoding="utf-8"))
            history = loaded if isinstance(loaded, list) else []
        history.append({"current_state": state, "lifecycle_decision": decision})
        history_path.write_text(json.dumps(history, indent=2, sort_keys=True), encoding="utf-8")
        return {
            "persistence_state": "PERSISTED_BY_KNOWLEDGE_CURRENT_AUTHORITY",
            "current_state_path": str(current_path),
            "current_decision_pointer_path": str(pointer_path),
            "history_path": str(history_path),
            "persistence_implies_knowledge": False,
            "persistence_implies_current_knowledge": False,
            "persistence_implies_invalidation": False,
        }

    def get_current_knowledge_state(self, knowledge_id: str) -> dict[str, Any] | None:
        if self.state_dir is None:
            return None
        state_path = self.state_dir / "current_knowledge_state" / f"{knowledge_id}.json"
        pointer_path = (
            self.state_dir
            / "current_knowledge_decision_pointer"
            / f"{knowledge_id}.json"
        )
        if not state_path.exists() or not pointer_path.exists():
            return None
        state = json.loads(state_path.read_text(encoding="utf-8"))
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        if pointer.get("authority") != self.authority:
            return None
        if not self._fingerprint_valid(pointer):
            return None
        if pointer.get("current_knowledge_decision_id") != state.get(
            "current_knowledge_decision_id"
        ):
            return None
        if pointer.get("current_state_fingerprint") != state.get("fingerprint"):
            return None
        if state.get("authority") != self.authority:
            return None
        if not self._fingerprint_valid(state):
            return None
        return state

    def get_knowledge_history(self, knowledge_id: str) -> list[dict[str, Any]]:
        if self.state_dir is None:
            return []
        path = self.state_dir / "knowledge_history" / f"{knowledge_id}.json"
        if not path.exists():
            return []
        history = json.loads(path.read_text(encoding="utf-8"))
        return history if isinstance(history, list) else []

    def is_knowledge_current(self, knowledge_id: str) -> bool:
        current = self.get_current_knowledge_state(knowledge_id)
        return bool(
            current
            and current.get("lifecycle_status") == KnowledgeLifecycleStatus.ACTIVE.value
            and current.get("current_authority_status")
            == "CURRENT_KNOWLEDGE_AUTHORITY_VERIFIED"
        )

    def support_change_review_signal(
        self,
        current_state: Mapping[str, Any],
        *,
        trigger: str,
        upstream_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        decision = self.open_review(
            current_state,
            review_trigger=trigger,
            support_signal=upstream_report,
        )
        return {
            "schema_version": self.schema_version,
            "system": "knowledge_support_change_review_signal",
            "signal_state": "KNOWLEDGE_REVIEW_DECISION_AVAILABLE",
            "knowledge_review_decision": decision,
            "direct_knowledge_mutation": False,
            "truth_layer_knowledge_authority": "NONE",
            "evidence_layer_knowledge_authority": "NONE",
        }

    def support_dependency_graph(self, support: Mapping[str, Any]) -> dict[str, Any]:
        item = dict(support or {})
        return {
            "supporting_truths": [
                dict(value) for value in item.get("supporting_truths", []) or []
                if isinstance(value, Mapping)
            ],
            "epistemic_assessments": [
                dict(value) for value in item.get("epistemic_assessments", []) or []
                if isinstance(value, Mapping)
            ],
            "accepted_evidence": [
                dict(value) for value in item.get("accepted_evidence", []) or []
                if isinstance(value, Mapping)
            ],
            "source_identities": sorted(
                str(value) for value in item.get("source_identities", []) or []
            ),
            "causal_support_refs": sorted(
                str(value) for value in item.get("causal_support_refs", []) or []
            ),
            "reproducibility_refs": sorted(
                str(value) for value in item.get("reproducibility_refs", []) or []
            ),
            "source_independence_state": str(
                item.get("source_independence_state") or "PROVENANCE_DERIVED"
            ),
            "causal_support_state": str(
                item.get("causal_support_state") or "NOT_CLAIMED"
            ),
            "reproducibility_state": str(
                item.get("reproducibility_state") or "NOT_CLAIMED"
            ),
            "contradictory_current_support": bool(
                item.get("contradictory_current_support", False)
            ),
            "valid_provenance": bool(item.get("valid_provenance", True)),
            "confidence_only": bool(item.get("confidence_only", False)),
            "run_count_inflation": bool(item.get("run_count_inflation", False)),
            "task_count_inflation": bool(item.get("task_count_inflation", False)),
            "artifact_count_inflation": bool(item.get("artifact_count_inflation", False)),
        }

    def _decision(
        self,
        *,
        kind: str,
        subject: Mapping[str, Any],
        candidate_id: str | None,
        assessment: Mapping[str, Any],
        previous_decision_id: str | None,
        previous_status: str | None,
        new_status: str,
        reason: str,
        support_signal: Mapping[str, Any] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        subject_record = _subject_record(subject)
        support_graph = dict(
            assessment.get("support_dependency_graph")
            or subject.get("support_dependency_graph")
            or {}
        )
        payload = {
            "schema_version": self.schema_version,
            "system": f"knowledge_{kind}_decision",
            "knowledge_id": subject_record["knowledge_id"],
            "subject_id": subject_record["subject_id"],
            "subject_type": subject_record["subject_type"],
            "claim_id": subject_record["claim_id"],
            "scope": subject_record["scope"],
            "context_class": subject_record["context_class"],
            "domain": subject_record["domain"],
            "knowledge_candidate_id": candidate_id,
            "knowledge_assessment": dict(assessment or {}),
            "previous_knowledge_decision_id": previous_decision_id,
            "previous_status": previous_status,
            "requested_state": new_status,
            "granted_state": new_status,
            "new_status": new_status,
            "supporting_truth_ids": sorted(assessment.get("current_truth_ids", []) or []),
            "supporting_epistemic_assessment_ids": sorted(
                assessment.get("current_epistemic_assessment_ids", []) or []
            ),
            "supporting_evidence_ids": sorted(assessment.get("current_evidence_ids", []) or []),
            "source_independence_state": assessment.get("source_independence_state"),
            "causal_support_state": assessment.get("causal_support_state"),
            "reproducibility_state": assessment.get("reproducibility_state"),
            "support_dependency_graph": support_graph,
            "support_change_signal": dict(support_signal or {}),
            "decision_reason": reason,
            "authority": self._authority(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        payload.update(dict(extra or {}))
        payload[f"knowledge_{kind}_decision_id"] = self._stable_id(kind, payload)
        payload["decision_fingerprint"] = self._fingerprint(payload)
        return payload

    def _assert_subject(self, subject: Mapping[str, Any]) -> None:
        if subject.get("knowledge_id") in UNKNOWN:
            raise ValueError("knowledge_id_required")
        if subject.get("subject_id") in UNKNOWN:
            raise ValueError("knowledge_subject_id_required")
        if subject.get("claim_id") in UNKNOWN:
            raise ValueError("knowledge_claim_id_required")

    def _assert_current_state(self, state: Mapping[str, Any]) -> None:
        self._assert_subject(state)
        if state.get("current_knowledge_decision_id") in UNKNOWN:
            raise ValueError("current_knowledge_decision_id_required")
        if state.get("authority") != self.authority:
            raise ValueError("knowledge_current_authority_required")
        if not self._fingerprint_valid(state):
            raise ValueError("corrupted_knowledge_state_fingerprint")

    def _assert_decision(self, decision: Mapping[str, Any]) -> None:
        if self._decision_id(decision) in UNKNOWN:
            raise ValueError("knowledge_decision_id_required")
        authority = decision.get("authority")
        if not isinstance(authority, Mapping) or (
            authority.get("knowledge_current_authority") != self.authority
        ):
            raise ValueError("knowledge_current_authority_required")
        if decision.get("knowledge_id") in UNKNOWN:
            raise ValueError("knowledge_id_required")
        if decision.get("subject_id") in UNKNOWN:
            raise ValueError("knowledge_subject_id_required")
        if not self._fingerprint_valid(decision):
            raise ValueError("corrupted_knowledge_decision_fingerprint")

    def _decision_id(self, decision: Mapping[str, Any]) -> str | None:
        for key in (
            "knowledge_activation_decision_id",
            "knowledge_review_decision_id",
            "knowledge_reassessment_decision_id",
            "knowledge_invalidation_decision_id",
            "knowledge_revalidation_decision_id",
            "knowledge_supersession_decision_id",
            "knowledge_denial_decision_id",
        ):
            if decision.get(key):
                return str(decision[key])
        return None

    def _authority(self) -> dict[str, str]:
        return {
            "knowledge_current_authority": self.authority,
            "truth": "NONE",
            "evidence": "NONE",
            "epistemic_assessment": "NONE",
            "capability": "NONE",
            "planning": "NONE",
            "self_improvement": "NONE",
            "runtime": "NONE",
            "budget": "NONE",
            "execution": "NONE",
        }

    def _stable_id(self, kind: str, payload: Mapping[str, Any]) -> str:
        seed = {
            key: value
            for key, value in dict(payload).items()
            if key not in {"created_at", "decision_fingerprint"}
        }
        return f"knowledge_{kind}_decision_{_sha1(seed)}"

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


def get_current_knowledge_state(
    knowledge_id: str,
    *,
    authority_engine: KnowledgeCurrentAuthorityEngine | None = None,
) -> dict[str, Any] | None:
    engine = authority_engine or knowledge_current_authority_engine
    return engine.get_current_knowledge_state(knowledge_id)


def get_knowledge_history(
    knowledge_id: str,
    *,
    authority_engine: KnowledgeCurrentAuthorityEngine | None = None,
) -> list[dict[str, Any]]:
    engine = authority_engine or knowledge_current_authority_engine
    return engine.get_knowledge_history(knowledge_id)


def is_knowledge_current(
    knowledge_id: str,
    *,
    authority_engine: KnowledgeCurrentAuthorityEngine | None = None,
) -> bool:
    engine = authority_engine or knowledge_current_authority_engine
    return engine.is_knowledge_current(knowledge_id)


def _object_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _subject_record(subject: KnowledgeSubject | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(subject, KnowledgeSubject):
        return subject.to_dict()
    item = dict(subject or {})
    if item.get("knowledge_id") and item.get("subject_id"):
        return {
            "subject_type": str(item.get("subject_type") or "CLAIM"),
            "claim_id": str(item.get("claim_id") or item.get("subject_id")),
            "scope": str(item.get("scope") or "GLOBAL"),
            "context_class": str(item.get("context_class") or "GENERAL"),
            "domain": str(item.get("domain") or "GENERAL"),
            "subject_id": str(item["subject_id"]),
            "knowledge_id": str(item["knowledge_id"]),
        }
    return KnowledgeSubject(
        subject_type=str(item.get("subject_type") or "CLAIM"),
        claim_id=str(item.get("claim_id") or ""),
        scope=str(item.get("scope") or "GLOBAL"),
        context_class=str(item.get("context_class") or "GENERAL"),
        domain=str(item.get("domain") or "GENERAL"),
    ).to_dict()


def _canon(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _sha1(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()[:12]


knowledge_current_authority_engine = KnowledgeCurrentAuthorityEngine()


__all__ = [
    "KnowledgeAssessment",
    "KnowledgeCandidate",
    "KnowledgeCurrentAuthorityEngine",
    "KnowledgeLifecycleStatus",
    "KnowledgeSubject",
    "REVIEW_TRIGGERS",
    "get_current_knowledge_state",
    "get_knowledge_history",
    "is_knowledge_current",
    "knowledge_current_authority_engine",
]
