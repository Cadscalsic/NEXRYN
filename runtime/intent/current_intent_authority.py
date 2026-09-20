"""Canonical current Intent authority and lifecycle governance."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.goals.current_goal_authority import GoalCurrentAuthorityEngine
from runtime.knowledge.current_knowledge_admission import CurrentKnowledgeAdmissionGate
from runtime.truth.current_truth_admission import CurrentTruthAdmissionGate


UNKNOWN = {None, "", "UNKNOWN", "NOT_AVAILABLE", "Not Available"}


class IntentLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SATISFIED = "SATISFIED"
    INVALIDATED = "INVALIDATED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    SUPERSEDED = "SUPERSEDED"
    ABANDONED = "ABANDONED"


INTENT_SOURCES = {
    "USER_DIRECTED",
    "GOAL_DERIVED",
    "PLANNING_DERIVED",
    "KNOWLEDGE_INFORMED",
    "GOVERNANCE_REQUIRED",
    "SYSTEM_MAINTENANCE",
    "REPAIR_PROPOSED",
    "TRAINING_PROPOSED",
    "SELF_IMPROVEMENT_PROPOSED",
}


REVIEW_TRIGGERS = {
    "SUPPORT_CHANGED",
    "GOAL_STRUCTURE_CHANGED",
    "GOAL_FAILURE",
    "GOAL_SATISFIED",
    "CONSTRAINT_CHANGED",
    "GOVERNANCE_CHANGED",
    "CAPABILITY_CHANGED",
    "DEPENDENCY_INTENT_CHANGED",
    "USER_PURPOSE_CHANGED",
    "PLANNING_FEASIBILITY_CHANGED",
    "INTENT_CONFLICT_CHANGED",
    "INTENT_DECISION_INTEGRITY_FAILURE",
    "INTENT_PROVENANCE_INVALID",
    "PERSISTENCE_INTEGRITY_FAILURE",
}


NEGOTIATION_OUTCOMES = {
    "COEXIST",
    "SEQUENCE",
    "PAUSE",
    "REVIEW",
    "MERGE_PROPOSAL",
    "SCOPE_SPLIT",
    "REPRIORITIZE",
    "REJECT_PROPOSAL",
}


CONSTRAINT_CLASSES = {
    "SCOPE_CONSTRAINT",
    "RESOURCE_CONSTRAINT",
    "TEMPORAL_CONSTRAINT",
    "GOVERNANCE_CONSTRAINT",
    "DEPENDENCY_CONSTRAINT",
    "CAPABILITY_CONSTRAINT",
    "KNOWLEDGE_CONSTRAINT",
    "USER_CONSTRAINT",
    "SYSTEM_INVARIANT",
}


@dataclass(frozen=True)
class IntentSubject:
    intent_type: str
    purpose: str
    directional_target: str = "UNSPECIFIED"
    scope: str = "GLOBAL"
    domain: str = "GENERAL"
    context_class: str = "GENERAL"
    constraint_domain: str = "GENERAL"
    authority_origin: str = "UNSPECIFIED"
    parent_intent_id: str | None = None
    depends_on_intent_ids: tuple[str, ...] = ()
    supports_intent_ids: tuple[str, ...] = ()

    @property
    def intent_id(self) -> str:
        seed = {
            "intent_type": _canon(self.intent_type),
            "purpose": _canon(self.purpose),
            "directional_target": _canon(self.directional_target),
            "scope": _canon(self.scope),
            "domain": _canon(self.domain),
            "context_class": _canon(self.context_class),
            "constraint_domain": _canon(self.constraint_domain),
            "authority_origin": _canon(self.authority_origin),
            "parent_intent_id": _canon(self.parent_intent_id),
            "depends_on_intent_ids": sorted(_canon(item) for item in self.depends_on_intent_ids),
            "supports_intent_ids": sorted(_canon(item) for item in self.supports_intent_ids),
        }
        return f"intent_{_sha1(seed)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "intent_type": _canon(self.intent_type),
            "purpose": _canon(self.purpose),
            "directional_target": _canon(self.directional_target),
            "scope": _canon(self.scope),
            "domain": _canon(self.domain),
            "context_class": _canon(self.context_class),
            "constraint_domain": _canon(self.constraint_domain),
            "authority_origin": _canon(self.authority_origin),
            "parent_intent_id": _canon(self.parent_intent_id),
            "depends_on_intent_ids": list(self.depends_on_intent_ids),
            "supports_intent_ids": list(self.supports_intent_ids),
            "identity_excludes_run_id": True,
            "identity_excludes_task_id": True,
            "identity_excludes_timestamp": True,
            "identity_excludes_artifact_path": True,
            "identity_excludes_goal_id": True,
            "identity_excludes_plan_id": True,
            "identity_excludes_knowledge_decision_id": True,
            "identity_excludes_truth_decision_id": True,
        }


@dataclass(frozen=True)
class IntentProposal:
    intent_proposal_id: str
    intent_id: str
    intent_instance_id: str
    intent_revision_id: str
    intent_subject: dict[str, Any]
    source: str
    support_refs: list[dict[str, Any]]
    constraint_refs: list[dict[str, Any]]
    goal_refs: list[dict[str, Any]]
    conflict_refs: list[dict[str, Any]]
    governance_refs: list[dict[str, Any]]
    capability_refs: list[dict[str, Any]]
    provenance: dict[str, Any]
    proposal_fingerprint: str
    priority_score: float | None = None
    authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntentAssessment:
    intent_assessment_id: str
    intent_id: str
    intent_instance_id: str
    intent_proposal_id: str
    assessment_state: str
    intent_authority_predicate_satisfied: bool
    failures: list[str]
    identity_validity_state: str
    source_validity_state: str
    provenance_state: str
    scope_state: str
    governance_compatibility_state: str
    constraint_compatibility_state: str
    goal_compatibility_state: str
    resource_implication_state: str
    conflict_state: str
    dependency_state: str
    support_state: str
    persistence_scope_state: str
    user_authority_state: str
    system_invariant_state: str
    priority_role: str
    priority_authority_status: str
    negotiation_authority_status: str
    current_knowledge_refs: list[dict[str, Any]]
    denied_knowledge_refs: list[dict[str, Any]]
    current_truth_refs: list[dict[str, Any]]
    denied_truth_refs: list[dict[str, Any]]
    support_dependency_graph: dict[str, Any]
    support_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IntentCurrentAuthorityEngine:
    """The sole owner of current Intent lifecycle decisions."""

    schema_version = "1.0"
    system_name = "intent_current_authority_engine"
    authority = "INTENT_CURRENT_AUTHORITY"

    def __init__(
        self,
        state_dir: str | Path | None = None,
        *,
        knowledge_admission_gate: CurrentKnowledgeAdmissionGate | None = None,
        truth_admission_gate: CurrentTruthAdmissionGate | None = None,
        goal_authority_engine: GoalCurrentAuthorityEngine | None = None,
    ) -> None:
        self.state_dir = Path(state_dir) if state_dir is not None else None
        self.knowledge_admission_gate = (
            knowledge_admission_gate or CurrentKnowledgeAdmissionGate()
        )
        self.truth_admission_gate = truth_admission_gate or CurrentTruthAdmissionGate()
        self.goal_authority_engine = goal_authority_engine or GoalCurrentAuthorityEngine()

    def create_subject(
        self,
        *,
        intent_type: str,
        purpose: str,
        directional_target: str = "UNSPECIFIED",
        scope: str = "GLOBAL",
        domain: str = "GENERAL",
        context_class: str = "GENERAL",
        constraint_domain: str = "GENERAL",
        authority_origin: str = "UNSPECIFIED",
        parent_intent_id: str | None = None,
        depends_on_intent_ids: Iterable[Any] | None = None,
        supports_intent_ids: Iterable[Any] | None = None,
    ) -> IntentSubject:
        if intent_type in UNKNOWN:
            raise ValueError("intent_type_required")
        if purpose in UNKNOWN:
            raise ValueError("intent_purpose_required")
        return IntentSubject(
            intent_type=intent_type,
            purpose=purpose,
            directional_target=directional_target,
            scope=scope,
            domain=domain,
            context_class=context_class,
            constraint_domain=constraint_domain,
            authority_origin=authority_origin,
            parent_intent_id=parent_intent_id,
            depends_on_intent_ids=tuple(
                _canon(item) for item in depends_on_intent_ids or [] if _canon(item)
            ),
            supports_intent_ids=tuple(
                _canon(item) for item in supports_intent_ids or [] if _canon(item)
            ),
        )

    def create_proposal(
        self,
        subject: IntentSubject | Mapping[str, Any],
        *,
        source: str,
        support_refs: Iterable[Mapping[str, Any]] | None = None,
        constraint_refs: Iterable[Mapping[str, Any]] | None = None,
        goal_refs: Iterable[Mapping[str, Any]] | None = None,
        conflict_refs: Iterable[Mapping[str, Any]] | None = None,
        governance_refs: Iterable[Mapping[str, Any]] | None = None,
        capability_refs: Iterable[Mapping[str, Any]] | None = None,
        provenance: Mapping[str, Any] | None = None,
        proposal_context: Mapping[str, Any] | None = None,
        priority_score: float | None = None,
    ) -> IntentProposal:
        subject_record = _subject_record(subject)
        intent_id = str(subject_record["intent_id"])
        instance_seed = {
            "intent_id": intent_id,
            "source": _canon(source),
            "proposal_context": dict(proposal_context or {}),
            "constraint_refs": _records(constraint_refs),
            "governance_refs": _records(governance_refs),
        }
        intent_instance_id = f"intent_instance_{_sha1(instance_seed)}"
        revision_seed = {
            "intent_instance_id": intent_instance_id,
            "intent_subject": subject_record,
            "source": _canon(source),
            "support_refs": _records(support_refs),
            "constraint_refs": _records(constraint_refs),
            "goal_refs": _records(goal_refs),
            "conflict_refs": _records(conflict_refs),
            "governance_refs": _records(governance_refs),
            "capability_refs": _records(capability_refs),
            "provenance": dict(provenance or {}),
            "authority": "NONE",
        }
        intent_revision_id = f"intent_revision_{_sha1(revision_seed)}"
        proposal_seed = {**revision_seed, "intent_revision_id": intent_revision_id}
        return IntentProposal(
            intent_proposal_id=f"intent_proposal_{_sha1(proposal_seed)}",
            intent_id=intent_id,
            intent_instance_id=intent_instance_id,
            intent_revision_id=intent_revision_id,
            intent_subject=subject_record,
            source=_canon(source),
            support_refs=proposal_seed["support_refs"],
            constraint_refs=proposal_seed["constraint_refs"],
            goal_refs=proposal_seed["goal_refs"],
            conflict_refs=proposal_seed["conflict_refs"],
            governance_refs=proposal_seed["governance_refs"],
            capability_refs=proposal_seed["capability_refs"],
            provenance=dict(provenance or {}),
            proposal_fingerprint=self._fingerprint(proposal_seed),
            priority_score=priority_score,
        )

    def assess_proposal(
        self,
        proposal: IntentProposal | Mapping[str, Any],
        subject: IntentSubject | Mapping[str, Any],
        *,
        min_current_knowledge: int = 0,
        min_current_truth: int = 0,
        negotiation_recommendation: str | None = None,
    ) -> IntentAssessment:
        proposal_record = _object_dict(proposal)
        subject_record = _subject_record(subject)
        failures: list[str] = []
        if proposal_record.get("authority") != "NONE":
            failures.append("INTENT_PROPOSAL_MUST_HAVE_NO_AUTHORITY")
        if proposal_record.get("intent_id") != subject_record.get("intent_id"):
            failures.append("INTENT_SUBJECT_IDENTITY_MISMATCH")
        for key, failure in (
            ("intent_proposal_id", "INTENT_PROPOSAL_ID_MISSING"),
            ("intent_instance_id", "INTENT_INSTANCE_ID_MISSING"),
            ("intent_revision_id", "INTENT_REVISION_ID_MISSING"),
            ("proposal_fingerprint", "INTENT_PROPOSAL_FINGERPRINT_MISSING"),
        ):
            if _unknown(proposal_record.get(key)):
                failures.append(failure)

        source = _canon(proposal_record.get("source"))
        source_valid = source in INTENT_SOURCES
        if not source_valid:
            failures.append("INTENT_SOURCE_INVALID")
        if source == "SELF_IMPROVEMENT_PROPOSED" and not _explicit_governed_request(
            proposal_record
        ):
            failures.append("SELF_IMPROVEMENT_INTENT_REQUIRES_EXTERNAL_GOVERNANCE")

        provenance = proposal_record.get("provenance")
        provenance_valid = isinstance(provenance, Mapping) and bool(
            provenance.get("origin")
            or provenance.get("user_request_id")
            or provenance.get("goal_decision_id")
            or provenance.get("planning_decision_id")
            or provenance.get("governance_event_id")
        )
        if not provenance_valid:
            failures.append("INTENT_PROVENANCE_INVALID")

        if _constraints_self_relaxed(proposal_record):
            failures.append("INTENT_CONSTRAINT_SELF_RELAXATION_REJECTED")
        if _user_constraints_rewritten(proposal_record):
            failures.append("USER_CONSTRAINT_REWRITE_REJECTED")

        graph = self.intent_support_dependency_graph(proposal_record, subject_record)
        current_knowledge: list[dict[str, Any]] = []
        denied_knowledge: list[dict[str, Any]] = []
        current_truth: list[dict[str, Any]] = []
        denied_truth: list[dict[str, Any]] = []
        for row in graph["support_refs"]:
            if row.get("support_type") == "knowledge" or row.get("knowledge_id"):
                admission = self.knowledge_admission_gate.admit_current_knowledge(
                    row,
                    consumer_scope="intent_support_dependency",
                )
                enriched = {**row, "current_knowledge_admission": admission.to_dict()}
                if admission.admitted:
                    current_knowledge.append(enriched)
                else:
                    denied_knowledge.append(enriched)
            if row.get("support_type") == "truth" or row.get("truth_id"):
                admission = self.truth_admission_gate.admit_current_truth(
                    row,
                    consumer_scope="intent_support_dependency",
                )
                enriched = {**row, "current_truth_admission": admission.to_dict()}
                if admission.admitted:
                    current_truth.append(enriched)
                else:
                    denied_truth.append(enriched)
        if denied_knowledge:
            failures.append("NONCURRENT_KNOWLEDGE_SUPPORT_REJECTED")
        if denied_truth:
            failures.append("NONCURRENT_TRUTH_SUPPORT_REJECTED")
        if len(current_knowledge) < int(min_current_knowledge or 0):
            failures.append("INSUFFICIENT_CURRENT_KNOWLEDGE_SUPPORT")
        if len(current_truth) < int(min_current_truth or 0):
            failures.append("INSUFFICIENT_CURRENT_TRUTH_SUPPORT")

        negotiation_state = (
            "NEGOTIATION_REVIEW_RECOMMENDED"
            if negotiation_recommendation in {"PAUSE", "REVIEW", "REJECT_PROPOSAL"}
            else "NO_BLOCKING_NEGOTIATION"
        )
        if negotiation_recommendation == "REJECT_PROPOSAL":
            failures.append("INTENT_NEGOTIATION_BLOCKING")

        identity_state = "IDENTITY_VALID" if not _unknown(subject_record.get("intent_id")) else "IDENTITY_INVALID"
        if identity_state != "IDENTITY_VALID":
            failures.append("INTENT_IDENTITY_INVALID")
        scope_state = "INTENT_SCOPE_VALID" if not _unknown(subject_record.get("scope")) else "INTENT_SCOPE_INVALID"
        if scope_state != "INTENT_SCOPE_VALID":
            failures.append("INTENT_SCOPE_INVALID")

        support_fingerprint = self._fingerprint(graph)
        assessment_seed = {
            "intent_id": proposal_record.get("intent_id"),
            "intent_instance_id": proposal_record.get("intent_instance_id"),
            "intent_proposal_id": proposal_record.get("intent_proposal_id"),
            "failures": sorted(failures),
            "support_fingerprint": support_fingerprint,
        }
        predicate = not failures
        return IntentAssessment(
            intent_assessment_id=f"intent_assessment_{_sha1(assessment_seed)}",
            intent_id=str(proposal_record.get("intent_id")),
            intent_instance_id=str(proposal_record.get("intent_instance_id")),
            intent_proposal_id=str(proposal_record.get("intent_proposal_id")),
            assessment_state=(
                "INTENT_ASSESSMENT_PASSED"
                if predicate
                else "INTENT_ASSESSMENT_FAILED"
            ),
            intent_authority_predicate_satisfied=predicate,
            failures=failures,
            identity_validity_state=identity_state,
            source_validity_state=(
                "INTENT_SOURCE_VALID" if source_valid else "INTENT_SOURCE_INVALID"
            ),
            provenance_state=(
                "INTENT_PROVENANCE_VALID"
                if provenance_valid
                else "INTENT_PROVENANCE_INVALID"
            ),
            scope_state=scope_state,
            governance_compatibility_state="GOVERNANCE_COMPATIBLE",
            constraint_compatibility_state=(
                "CONSTRAINTS_COMPATIBLE"
                if not {
                    "INTENT_CONSTRAINT_SELF_RELAXATION_REJECTED",
                    "USER_CONSTRAINT_REWRITE_REJECTED",
                } & set(failures)
                else "CONSTRAINTS_INCOMPATIBLE"
            ),
            goal_compatibility_state="GOAL_REFS_ADVISORY",
            resource_implication_state="RESOURCE_REQUEST_ONLY",
            conflict_state=negotiation_state,
            dependency_state="DEPENDENCIES_VALID",
            support_state=(
                "INTENT_SUPPORT_CURRENT"
                if current_knowledge or current_truth
                else "INTENT_SUPPORT_NOT_REQUIRED"
            ),
            persistence_scope_state="PERSISTENCE_NOT_AUTHORITY",
            user_authority_state=(
                "USER_ORIGIN_STRONG_PROPOSAL_AUTHORITY"
                if source == "USER_DIRECTED"
                else "SYSTEM_ORIGIN_PROPOSAL_ONLY"
            ),
            system_invariant_state="SYSTEM_INVARIANTS_SATISFIED",
            priority_role="INTENT_PRIORITY_ADVISORY_ONLY",
            priority_authority_status="ADVISORY_GOVERNED",
            negotiation_authority_status="ADVISORY_GOVERNED",
            current_knowledge_refs=current_knowledge,
            denied_knowledge_refs=denied_knowledge,
            current_truth_refs=current_truth,
            denied_truth_refs=denied_truth,
            support_dependency_graph=graph,
            support_fingerprint=support_fingerprint,
        )

    def commit_intent(
        self,
        subject: IntentSubject | Mapping[str, Any],
        proposal: IntentProposal | Mapping[str, Any],
        assessment: IntentAssessment | Mapping[str, Any],
        *,
        previous_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._decision(
            subject,
            proposal,
            assessment,
            requested_status=IntentLifecycleStatus.ACTIVE.value,
            granted_status=IntentLifecycleStatus.ACTIVE.value,
            previous_state=previous_state,
            decision_type="IntentAuthorityDecision",
        )

    def current_state_from_decision(
        self,
        previous_state: Mapping[str, Any] | None,
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        decision_record = dict(decision or {})
        if decision_record.get("authority") != self.authority:
            raise ValueError("intent_authority_required")
        if decision_record.get("decision_fingerprint") != self._decision_fingerprint(
            decision_record
        ):
            raise ValueError("intent_decision_fingerprint_invalid")
        previous = dict(previous_state or {})
        if previous and previous.get("intent_id") != decision_record.get("intent_id"):
            raise ValueError("cross_intent_decision_rejected")
        expected_previous = previous.get("current_intent_decision_id")
        if expected_previous and decision_record.get("previous_decision_id") != expected_previous:
            raise ValueError("stale_intent_decision_rejected")
        state = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "authority": self.authority,
            "intent_id": decision_record.get("intent_id"),
            "intent_instance_id": decision_record.get("intent_instance_id"),
            "intent_revision_id": decision_record.get("intent_revision_id"),
            "intent_proposal_id": decision_record.get("intent_proposal_id"),
            "intent_assessment_id": decision_record.get("intent_assessment_id"),
            "intent_subject": decision_record.get("intent_subject"),
            "source": decision_record.get("source"),
            "support_refs": decision_record.get("support_refs", []),
            "constraint_refs": decision_record.get("constraint_refs", []),
            "goal_refs": decision_record.get("goal_refs", []),
            "conflict_refs": decision_record.get("conflict_refs", []),
            "governance_refs": decision_record.get("governance_refs", []),
            "capability_refs": decision_record.get("capability_refs", []),
            "support_dependency_graph": decision_record.get(
                "support_dependency_graph", {}
            ),
            "lifecycle_status": decision_record.get("granted_status"),
            "current_intent_decision_id": decision_record.get("intent_decision_id"),
            "intent_decision_fingerprint": decision_record.get(
                "decision_fingerprint"
            ),
            "current_intent_authority_status": "CURRENT_INTENT_AUTHORITY_VERIFIED",
            "goal_authority": "NONE",
            "planning_authority": "NONE",
            "action_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "capability_authority": "NONE",
            "telemetry_authority": "NONE",
            "history": list(previous.get("history", [])),
        }
        if previous:
            state["history"].append(
                {
                    "intent_id": previous.get("intent_id"),
                    "intent_instance_id": previous.get("intent_instance_id"),
                    "intent_revision_id": previous.get("intent_revision_id"),
                    "current_intent_decision_id": previous.get(
                        "current_intent_decision_id"
                    ),
                    "lifecycle_status": previous.get("lifecycle_status"),
                    "fingerprint": previous.get("fingerprint"),
                }
            )
        state["fingerprint"] = self._fingerprint(
            {key: value for key, value in state.items() if key != "fingerprint"}
        )
        return state

    def propose_goal_from_intent(
        self,
        current_intent: Mapping[str, Any],
        *,
        goal_type: str,
        objective: str,
        target_state: str,
        scope: str | None = None,
        domain: str | None = None,
        context_class: str | None = None,
    ) -> dict[str, Any]:
        state = dict(current_intent or {})
        if state.get("lifecycle_status") != IntentLifecycleStatus.ACTIVE.value:
            raise ValueError("active_intent_required_for_goal_proposal")
        subject = self.goal_authority_engine.create_subject(
            goal_type=goal_type,
            objective=objective,
            target_state=target_state,
            scope=scope or (state.get("intent_subject") or {}).get("scope", "GLOBAL"),
            domain=domain or (state.get("intent_subject") or {}).get("domain", "GENERAL"),
            context_class=context_class
            or (state.get("intent_subject") or {}).get("context_class", "GENERAL"),
            constraint_domain=(state.get("intent_subject") or {}).get(
                "constraint_domain",
                "GENERAL",
            ),
        )
        proposal = self.goal_authority_engine.create_proposal(
            subject,
            source="PLANNING_DERIVED",
            support_refs=[],
            constraint_refs=[
                {
                    "constraint_type": "intent_boundary",
                    "source_intent_id": state.get("intent_id"),
                    "source_intent_decision_id": state.get(
                        "current_intent_decision_id"
                    ),
                    "authority": "NONE",
                }
            ],
            provenance={
                "origin": "intent_to_goal_proposal",
                "source_intent_id": state.get("intent_id"),
                "source_intent_decision_id": state.get(
                    "current_intent_decision_id"
                ),
            },
        )
        payload = proposal.to_dict()
        payload["source_intent_id"] = state.get("intent_id")
        payload["source_intent_decision_id"] = state.get(
            "current_intent_decision_id"
        )
        payload["intent_to_goal_authority"] = "GOAL_PROPOSAL_ONLY"
        payload["goal_authority"] = "NONE"
        return payload

    def create_goal_derived_intent_proposal(
        self,
        goal: Mapping[str, Any],
        *,
        intent_type: str,
        purpose: str,
    ) -> IntentProposal:
        goal_record = dict(goal or {})
        subject = self.create_subject(
            intent_type=intent_type,
            purpose=purpose,
            directional_target=purpose,
            scope=(goal_record.get("goal_subject") or {}).get("scope", "GLOBAL"),
            domain=(goal_record.get("goal_subject") or {}).get("domain", "GENERAL"),
            context_class=(goal_record.get("goal_subject") or {}).get(
                "context_class",
                "GENERAL",
            ),
            authority_origin="GOAL_DERIVED_SIGNAL",
        )
        return self.create_proposal(
            subject,
            source="GOAL_DERIVED",
            goal_refs=[goal_record],
            provenance={
                "origin": "goal_to_intent_signal",
                "goal_id": goal_record.get("goal_id"),
                "goal_decision_id": goal_record.get("current_goal_decision_id"),
            },
        )

    def negotiate_intents(
        self,
        intents: Iterable[Mapping[str, Any]],
        *,
        recommendation: str = "COEXIST",
        reason: str = "compatible_scopes",
    ) -> dict[str, Any]:
        if recommendation not in NEGOTIATION_OUTCOMES:
            raise ValueError("intent_negotiation_recommendation_invalid")
        records = _records(intents)
        return {
            "schema_version": self.schema_version,
            "system": "intent_negotiation",
            "intent_ids": [row.get("intent_id") for row in records],
            "recommendation": recommendation,
            "reason": reason,
            "authority": "NONE",
            "intent_authority": "NONE",
            "negotiation_grants_authority": False,
        }

    def merge_proposal(self, intents: Iterable[Mapping[str, Any]], *, reason: str) -> dict[str, Any]:
        records = _records(intents)
        return {
            "schema_version": self.schema_version,
            "proposal_type": "IntentMergeProposal",
            "source_intent_ids": [row.get("intent_id") for row in records],
            "reason": reason,
            "authority": "NONE",
            "direct_replacement": False,
        }

    def split_proposal(self, intent: Mapping[str, Any], *, child_purposes: Iterable[str]) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "proposal_type": "IntentSplitProposal",
            "source_intent_id": dict(intent or {}).get("intent_id"),
            "child_purposes": [str(item) for item in child_purposes],
            "authority": "NONE",
            "children_active": False,
        }

    def open_review(
        self,
        current_state: Mapping[str, Any],
        *,
        trigger: str,
        affected_dependencies: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if trigger not in REVIEW_TRIGGERS:
            raise ValueError("intent_review_trigger_not_allowed")
        state = dict(current_state or {})
        decision = {
            **self._status_seed(state),
            "decision_type": "IntentReviewDecision",
            "requested_status": IntentLifecycleStatus.UNDER_REVIEW.value,
            "granted_status": IntentLifecycleStatus.UNDER_REVIEW.value,
            "trigger": trigger,
            "affected_dependencies": _records(affected_dependencies),
            "authority": self.authority,
            "timestamp": str(datetime.utcnow()),
        }
        return self._finish_status_decision(decision, "intent_review_decision")

    def pause_intent(self, current_state: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
        return self._status_decision(
            current_state,
            decision_type="IntentPauseDecision",
            requested_status=IntentLifecycleStatus.PAUSED.value,
            granted_status=IntentLifecycleStatus.PAUSED.value,
            reason=reason,
            support_evaluation={},
        )

    def satisfy_intent(
        self,
        current_state: Mapping[str, Any],
        *,
        satisfaction_evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not satisfaction_evidence:
            raise ValueError("intent_satisfaction_evidence_required")
        return self._status_decision(
            current_state,
            decision_type="IntentSatisfactionDecision",
            requested_status=IntentLifecycleStatus.SATISFIED.value,
            granted_status=IntentLifecycleStatus.SATISFIED.value,
            reason="intent_completion_criteria_met",
            support_evaluation=satisfaction_evidence,
        )

    def invalidate_intent(self, current_state: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
        return self._status_decision(
            current_state,
            decision_type="IntentInvalidationDecision",
            requested_status=IntentLifecycleStatus.INVALIDATED.value,
            granted_status=IntentLifecycleStatus.INVALIDATED.value,
            reason=reason,
            support_evaluation={},
        )

    def abandon_intent(self, current_state: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
        return self._status_decision(
            current_state,
            decision_type="IntentAbandonmentDecision",
            requested_status=IntentLifecycleStatus.ABANDONED.value,
            granted_status=IntentLifecycleStatus.ABANDONED.value,
            reason=reason,
            support_evaluation={},
        )

    def reassess_under_review(
        self,
        current_state: Mapping[str, Any],
        *,
        assessment: IntentAssessment | Mapping[str, Any],
        decision_result: str | None = None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        if state.get("lifecycle_status") != IntentLifecycleStatus.UNDER_REVIEW.value:
            raise ValueError("under_review_intent_required")
        assessment_record = _object_dict(assessment)
        passed = bool(assessment_record.get("intent_authority_predicate_satisfied"))
        granted = (
            IntentLifecycleStatus.ACTIVE.value
            if passed and decision_result == IntentLifecycleStatus.ACTIVE.value
            else IntentLifecycleStatus.REVALIDATION_REQUIRED.value
        )
        return self._status_decision(
            state,
            decision_type="IntentRevalidationDecision",
            requested_status=decision_result or granted,
            granted_status=granted,
            reason="intent_reassessment",
            support_evaluation=assessment_record,
        )

    def supersede_intent(
        self,
        current_state: Mapping[str, Any],
        *,
        replacement_subject: IntentSubject | Mapping[str, Any],
        replacement_proposal: IntentProposal | Mapping[str, Any],
        replacement_assessment: IntentAssessment | Mapping[str, Any],
        reason: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        state = dict(current_state or {})
        if state.get("lifecycle_status") != IntentLifecycleStatus.ACTIVE.value:
            raise ValueError("active_intent_required_for_supersession")
        supersession = self._status_decision(
            state,
            decision_type="IntentSupersessionDecision",
            requested_status=IntentLifecycleStatus.SUPERSEDED.value,
            granted_status=IntentLifecycleStatus.SUPERSEDED.value,
            reason=reason,
            support_evaluation={},
        )
        replacement = self.commit_intent(
            replacement_subject,
            replacement_proposal,
            replacement_assessment,
        )
        replacement["supersedes_intent_id"] = state.get("intent_id")
        replacement["supersedes_intent_decision_id"] = state.get(
            "current_intent_decision_id"
        )
        replacement["decision_fingerprint"] = self._decision_fingerprint(replacement)
        return supersession, replacement

    def support_change_review_signal(
        self,
        current_state: Mapping[str, Any],
        *,
        trigger: str,
        upstream_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "signal": "INTENT_REASSESSMENT_REQUIRED",
            "authority": "NONE",
            "intent_authority": "NONE",
            "intent_id": current_state.get("intent_id") if isinstance(current_state, Mapping) else None,
            "current_intent_decision_id": (
                current_state.get("current_intent_decision_id")
                if isinstance(current_state, Mapping)
                else None
            ),
            "trigger": trigger,
            "upstream_report": dict(upstream_report or {}),
            "direct_intent_mutation": False,
        }

    def get_current_intent_state(self, intent_id: str) -> dict[str, Any]:
        if self.state_dir is None:
            return {}
        path = self._current_path(intent_id)
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def get_intent_history(self, intent_id: str) -> list[dict[str, Any]]:
        current = self.get_current_intent_state(intent_id)
        history = current.get("history", []) if isinstance(current, Mapping) else []
        rows = [row for row in history if isinstance(row, Mapping)]
        if current:
            rows.append(dict(current))
        return rows

    def is_intent_current(self, intent: Mapping[str, Any]) -> dict[str, Any]:
        candidate = dict(intent or {})
        intent_id = candidate.get("intent_id")
        current = self.get_current_intent_state(str(intent_id)) if intent_id else {}
        if not current:
            return self._currentness(False, "CURRENT_INTENT_STATE_NOT_FOUND")
        if current.get("lifecycle_status") != IntentLifecycleStatus.ACTIVE.value:
            return self._currentness(False, "CURRENT_INTENT_NOT_ACTIVE", current)
        if candidate.get("current_intent_decision_id") != current.get(
            "current_intent_decision_id"
        ):
            return self._currentness(False, "STALE_INTENT_DECISION", current)
        if candidate.get("fingerprint") != current.get("fingerprint"):
            return self._currentness(False, "STALE_INTENT_STATE_REJECTED", current)
        return self._currentness(True, "CURRENT_INTENT_AUTHORITY_VERIFIED", current)

    def persist_current_state(
        self,
        state: Mapping[str, Any],
        *,
        lifecycle_decision: Mapping[str, Any] | None = None,
        proposal: Mapping[str, Any] | None = None,
        assessment: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.state_dir is None:
            return {
                "persistence_attempted": False,
                "persistence_state": "NO_STATE_DIR_CONFIGURED",
            }
        payload = dict(state or {})
        intent_id = str(payload.get("intent_id") or "")
        if not intent_id:
            raise ValueError("intent_id_required_for_persistence")
        self._current_path(intent_id).parent.mkdir(parents=True, exist_ok=True)
        self._history_dir(intent_id).mkdir(parents=True, exist_ok=True)
        self._current_path(intent_id).write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        for label, row in (
            ("proposal", proposal),
            ("assessment", assessment),
            ("decision", lifecycle_decision),
        ):
            if not row:
                continue
            record = dict(row)
            record_id = str(
                record.get("intent_decision_id")
                or record.get("intent_assessment_id")
                or record.get("intent_proposal_id")
                or _sha1(record)
            )
            (self._history_dir(intent_id) / f"{label}_{record_id}.json").write_text(
                json.dumps(record, indent=2, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
        return {
            "persistence_attempted": True,
            "persistence_state": "CURRENT_INTENT_STATE_PERSISTED",
            "persistence_implies_intent_authority": False,
            "intent_id": intent_id,
            "current_intent_decision_id": payload.get("current_intent_decision_id"),
        }

    def intent_dependency_graph(self, current_state: Mapping[str, Any]) -> dict[str, Any]:
        state = dict(current_state or {})
        subject = dict(state.get("intent_subject") or {})
        return {
            "schema_version": self.schema_version,
            "intent_id": state.get("intent_id"),
            "parent_intent_id": subject.get("parent_intent_id"),
            "child_intent_ids": [],
            "depends_on_intent_ids": list(subject.get("depends_on_intent_ids", [])),
            "supports_intent_ids": list(subject.get("supports_intent_ids", [])),
            "support_dependencies": state.get("support_refs", []),
            "goal_dependencies": state.get("goal_refs", []),
            "constraint_dependencies": state.get("constraint_refs", []),
            "dependency_graph_authority": "NONE",
        }

    def intent_support_dependency_graph(
        self,
        proposal: Mapping[str, Any],
        subject: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "intent_id": proposal.get("intent_id") or subject.get("intent_id"),
            "intent_instance_id": proposal.get("intent_instance_id"),
            "intent_revision_id": proposal.get("intent_revision_id"),
            "intent_proposal_id": proposal.get("intent_proposal_id"),
            "intent_subject": dict(subject),
            "support_refs": _records(proposal.get("support_refs")),
            "constraint_refs": _records(proposal.get("constraint_refs")),
            "goal_refs": _records(proposal.get("goal_refs")),
            "conflict_refs": _records(proposal.get("conflict_refs")),
            "governance_refs": _records(proposal.get("governance_refs")),
            "capability_refs": _records(proposal.get("capability_refs")),
            "authority": "NONE",
        }

    def _decision(
        self,
        subject: IntentSubject | Mapping[str, Any],
        proposal: IntentProposal | Mapping[str, Any],
        assessment: IntentAssessment | Mapping[str, Any],
        *,
        requested_status: str,
        granted_status: str,
        previous_state: Mapping[str, Any] | None,
        decision_type: str,
    ) -> dict[str, Any]:
        subject_record = _subject_record(subject)
        proposal_record = _object_dict(proposal)
        assessment_record = _object_dict(assessment)
        if not assessment_record.get("intent_authority_predicate_satisfied"):
            raise ValueError("intent_assessment_does_not_grant_authority")
        if proposal_record.get("intent_id") != subject_record.get("intent_id"):
            raise ValueError("intent_subject_proposal_mismatch")
        if assessment_record.get("intent_proposal_id") != proposal_record.get(
            "intent_proposal_id"
        ):
            raise ValueError("intent_assessment_proposal_mismatch")
        previous = dict(previous_state or {})
        decision = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "decision_type": decision_type,
            "intent_decision_id": "",
            "intent_id": proposal_record.get("intent_id"),
            "intent_instance_id": proposal_record.get("intent_instance_id"),
            "intent_revision_id": proposal_record.get("intent_revision_id"),
            "previous_decision_id": previous.get("current_intent_decision_id"),
            "intent_proposal_id": proposal_record.get("intent_proposal_id"),
            "intent_assessment_id": assessment_record.get("intent_assessment_id"),
            "intent_subject": subject_record,
            "source": proposal_record.get("source"),
            "requested_status": requested_status,
            "granted_status": granted_status,
            "support_refs": list(assessment_record.get("current_knowledge_refs", []))
            + list(assessment_record.get("current_truth_refs", [])),
            "constraint_refs": list(proposal_record.get("constraint_refs", [])),
            "goal_refs": list(proposal_record.get("goal_refs", [])),
            "conflict_refs": list(proposal_record.get("conflict_refs", [])),
            "governance_refs": list(proposal_record.get("governance_refs", [])),
            "capability_refs": list(proposal_record.get("capability_refs", [])),
            "support_dependency_graph": assessment_record.get(
                "support_dependency_graph", {}
            ),
            "authority": self.authority,
            "goal_authority": "NONE",
            "planning_authority": "NONE",
            "action_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "capability_authority": "NONE",
            "timestamp": str(datetime.utcnow()),
        }
        decision_id = f"intent_decision_{_sha1(decision)}"
        decision["intent_decision_id"] = decision_id
        decision["decision_fingerprint"] = self._decision_fingerprint(decision)
        return decision

    def _status_decision(
        self,
        current_state: Mapping[str, Any],
        *,
        decision_type: str,
        requested_status: str,
        granted_status: str,
        reason: str,
        support_evaluation: Mapping[str, Any],
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        if state.get("lifecycle_status") not in {
            IntentLifecycleStatus.ACTIVE.value,
            IntentLifecycleStatus.PAUSED.value,
            IntentLifecycleStatus.UNDER_REVIEW.value,
            IntentLifecycleStatus.REVALIDATION_REQUIRED.value,
        }:
            raise ValueError("current_intent_required_for_lifecycle_transition")
        decision = {
            **self._status_seed(state),
            "decision_type": decision_type,
            "requested_status": requested_status,
            "granted_status": granted_status,
            "authority": self.authority,
            "reason": reason,
            "support_evaluation": dict(support_evaluation or {}),
            "timestamp": str(datetime.utcnow()),
        }
        return self._finish_status_decision(decision, _camel_to_snake(decision_type))

    def _status_seed(self, state: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "intent_decision_id": "",
            "intent_id": state.get("intent_id"),
            "intent_instance_id": state.get("intent_instance_id"),
            "intent_revision_id": state.get("intent_revision_id"),
            "previous_decision_id": state.get("current_intent_decision_id"),
            "intent_proposal_id": state.get("intent_proposal_id"),
            "intent_assessment_id": state.get("intent_assessment_id"),
            "intent_subject": state.get("intent_subject"),
            "source": state.get("source"),
            "support_refs": state.get("support_refs", []),
            "constraint_refs": state.get("constraint_refs", []),
            "goal_refs": state.get("goal_refs", []),
            "conflict_refs": state.get("conflict_refs", []),
            "governance_refs": state.get("governance_refs", []),
            "capability_refs": state.get("capability_refs", []),
            "support_dependency_graph": state.get("support_dependency_graph", {}),
            "goal_authority": "NONE",
            "planning_authority": "NONE",
            "action_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "capability_authority": "NONE",
        }

    def _finish_status_decision(self, decision: dict[str, Any], prefix: str) -> dict[str, Any]:
        decision_id = f"{prefix}_{_sha1(decision)}"
        decision["intent_decision_id"] = decision_id
        decision["decision_fingerprint"] = self._decision_fingerprint(decision)
        return decision

    def _currentness(
        self,
        current: bool,
        reason: str,
        state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "is_current_intent": current,
            "current_intent_state": (
                "CURRENT_INTENT" if current else "HISTORICAL_INTENT"
            ),
            "reason": reason,
            "intent_id": (state or {}).get("intent_id"),
            "current_intent_decision_id": (state or {}).get(
                "current_intent_decision_id"
            ),
        }

    def _current_path(self, intent_id: str) -> Path:
        assert self.state_dir is not None
        return self.state_dir / "current" / f"{intent_id}.json"

    def _history_dir(self, intent_id: str) -> Path:
        assert self.state_dir is not None
        return self.state_dir / "history" / intent_id

    def _fingerprint(self, payload: Any) -> str:
        return f"intent_fingerprint_{_sha256(payload)}"

    def _decision_fingerprint(self, decision: Mapping[str, Any]) -> str:
        payload = {
            key: value
            for key, value in dict(decision).items()
            if key not in {"decision_fingerprint", "fingerprint"}
        }
        return f"intent_decision_fingerprint_{_sha256(payload)}"


def get_current_intent_state(
    intent_id: str,
    *,
    authority_engine: IntentCurrentAuthorityEngine | None = None,
) -> dict[str, Any]:
    engine = authority_engine or intent_current_authority_engine
    return engine.get_current_intent_state(intent_id)


def get_intent_history(
    intent_id: str,
    *,
    authority_engine: IntentCurrentAuthorityEngine | None = None,
) -> list[dict[str, Any]]:
    engine = authority_engine or intent_current_authority_engine
    return engine.get_intent_history(intent_id)


def is_intent_current(
    intent: Mapping[str, Any],
    *,
    authority_engine: IntentCurrentAuthorityEngine | None = None,
) -> dict[str, Any]:
    engine = authority_engine or intent_current_authority_engine
    return engine.is_intent_current(intent)


def _object_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return dict(value) if isinstance(value, Mapping) else {}


def _subject_record(value: IntentSubject | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, IntentSubject):
        return value.to_dict()
    record = dict(value) if isinstance(value, Mapping) else {}
    if "intent_id" not in record:
        subject = IntentSubject(
            intent_type=record.get("intent_type", ""),
            purpose=record.get("purpose", ""),
            directional_target=record.get("directional_target", "UNSPECIFIED"),
            scope=record.get("scope", "GLOBAL"),
            domain=record.get("domain", "GENERAL"),
            context_class=record.get("context_class", "GENERAL"),
            constraint_domain=record.get("constraint_domain", "GENERAL"),
            authority_origin=record.get("authority_origin", "UNSPECIFIED"),
            parent_intent_id=record.get("parent_intent_id"),
            depends_on_intent_ids=tuple(_records_to_strings(record.get("depends_on_intent_ids"))),
            supports_intent_ids=tuple(_records_to_strings(record.get("supports_intent_ids"))),
        )
        record.update(subject.to_dict())
    return record


def _records(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [dict(value)]
    records = []
    for item in value or []:
        if isinstance(item, Mapping):
            records.append(dict(item))
    return records


def _records_to_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [str(value.get("id") or value.get("intent_id") or value)]
    return [str(item) for item in value or [] if item not in UNKNOWN]


def _explicit_governed_request(proposal: Mapping[str, Any]) -> bool:
    provenance = proposal.get("provenance")
    return isinstance(provenance, Mapping) and bool(
        provenance.get("governance_event_id")
        or provenance.get("user_request_id")
        or provenance.get("external_authorization")
    )


def _constraints_self_relaxed(proposal: Mapping[str, Any]) -> bool:
    for row in _records(proposal.get("constraint_refs")):
        if row.get("changed_by") == "INTENT_SELF":
            return True
        if row.get("self_relaxation") is True:
            return True
    return False


def _user_constraints_rewritten(proposal: Mapping[str, Any]) -> bool:
    for row in _records(proposal.get("constraint_refs")):
        if row.get("constraint_type") == "USER_CONSTRAINT" and row.get("rewritten_by") == "INTENT":
            return True
    return False


def _unknown(value: Any) -> bool:
    return value in UNKNOWN or _canon(value) in UNKNOWN


def _canon(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _sha1(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _sha256(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _camel_to_snake(value: str) -> str:
    output = []
    for index, char in enumerate(value):
        if char.isupper() and index:
            output.append("_")
        output.append(char.lower())
    return "".join(output)


intent_current_authority_engine = IntentCurrentAuthorityEngine()


__all__ = [
    "CONSTRAINT_CLASSES",
    "INTENT_SOURCES",
    "NEGOTIATION_OUTCOMES",
    "REVIEW_TRIGGERS",
    "IntentAssessment",
    "IntentCurrentAuthorityEngine",
    "IntentLifecycleStatus",
    "IntentProposal",
    "IntentSubject",
    "get_current_intent_state",
    "get_intent_history",
    "intent_current_authority_engine",
    "is_intent_current",
]
