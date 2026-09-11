"""Canonical current Goal authority and lifecycle governance."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.knowledge.current_knowledge_admission import (
    CurrentKnowledgeAdmissionGate,
)


UNKNOWN = {None, "", "UNKNOWN", "NOT_AVAILABLE", "Not Available"}


class GoalLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    SATISFIED = "SATISFIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    INVALIDATED = "INVALIDATED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    SUPERSEDED = "SUPERSEDED"
    ABANDONED = "ABANDONED"


GOAL_SOURCES = {
    "USER_DIRECTED",
    "TASK_DERIVED",
    "PLANNING_DERIVED",
    "KNOWLEDGE_INFORMED",
    "GOVERNANCE_REQUIRED",
    "REPAIR_DERIVED",
    "TRAINING_DERIVED",
    "SELF_IMPROVEMENT_PROPOSED",
    "SYSTEM_MAINTENANCE",
}


REVIEW_TRIGGERS = {
    "SUPPORTING_KNOWLEDGE_CHANGED",
    "SUPPORTING_TRUTH_CHANGED",
    "SUPPORTING_CAPABILITY_CHANGED",
    "PLANNING_CONTEXT_CHANGED",
    "CONSTRAINT_CHANGED",
    "GOAL_CONFLICT_CHANGED",
    "DEPENDENCY_GOAL_CHANGED",
    "USER_OBJECTIVE_CHANGED",
    "TARGET_STATE_REACHED",
    "TARGET_STATE_IMPOSSIBLE",
    "GOVERNANCE_REVIEW_REQUIRED",
    "GOAL_DECISION_INTEGRITY_FAILURE",
    "GOAL_PROVENANCE_INVALID",
}


TERMINAL_NONCURRENT = {
    GoalLifecycleStatus.PAUSED.value,
    GoalLifecycleStatus.SATISFIED.value,
    GoalLifecycleStatus.UNDER_REVIEW.value,
    GoalLifecycleStatus.INVALIDATED.value,
    GoalLifecycleStatus.REVALIDATION_REQUIRED.value,
    GoalLifecycleStatus.SUPERSEDED.value,
    GoalLifecycleStatus.ABANDONED.value,
}


@dataclass(frozen=True)
class GoalSubject:
    goal_type: str
    objective: str
    target_state: str = "UNSPECIFIED"
    scope: str = "GLOBAL"
    domain: str = "GENERAL"
    context_class: str = "GENERAL"
    constraint_domain: str = "GENERAL"
    parent_goal_id: str | None = None
    depends_on_goal_ids: tuple[str, ...] = ()

    @property
    def goal_id(self) -> str:
        seed = {
            "goal_type": _canon(self.goal_type),
            "objective": _canon(self.objective),
            "target_state": _canon(self.target_state),
            "scope": _canon(self.scope),
            "domain": _canon(self.domain),
            "context_class": _canon(self.context_class),
            "constraint_domain": _canon(self.constraint_domain),
            "parent_goal_id": _canon(self.parent_goal_id),
            "depends_on_goal_ids": sorted(_canon(item) for item in self.depends_on_goal_ids),
        }
        return f"goal_{_sha1(seed)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "goal_type": _canon(self.goal_type),
            "objective": _canon(self.objective),
            "target_state": _canon(self.target_state),
            "scope": _canon(self.scope),
            "domain": _canon(self.domain),
            "context_class": _canon(self.context_class),
            "constraint_domain": _canon(self.constraint_domain),
            "parent_goal_id": _canon(self.parent_goal_id),
            "depends_on_goal_ids": list(self.depends_on_goal_ids),
            "identity_excludes_run_id": True,
            "identity_excludes_task_id": True,
            "identity_excludes_timestamp": True,
            "identity_excludes_artifact_path": True,
            "identity_excludes_knowledge_id": True,
            "identity_excludes_plan_id": True,
        }


@dataclass(frozen=True)
class GoalProposal:
    goal_proposal_id: str
    goal_id: str
    goal_instance_id: str
    goal_revision_id: str
    goal_subject: dict[str, Any]
    source: str
    support_refs: list[dict[str, Any]]
    constraint_refs: list[dict[str, Any]]
    conflict_refs: list[dict[str, Any]]
    planning_refs: list[dict[str, Any]]
    capability_refs: list[dict[str, Any]]
    provenance: dict[str, Any]
    proposal_fingerprint: str
    priority_score: float | None = None
    authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GoalAssessment:
    goal_assessment_id: str
    goal_id: str
    goal_instance_id: str
    goal_proposal_id: str
    assessment_state: str
    goal_authority_predicate_satisfied: bool
    failures: list[str]
    identity_validity_state: str
    source_validity_state: str
    provenance_state: str
    scope_state: str
    objective_coherence_state: str
    target_state_validity_state: str
    constraint_compatibility_state: str
    governance_compatibility_state: str
    conflict_state: str
    dependency_state: str
    support_state: str
    planning_compatibility_state: str
    priority_role: str
    priority_authority_status: str
    conflict_authority_status: str
    current_knowledge_refs: list[dict[str, Any]]
    denied_knowledge_refs: list[dict[str, Any]]
    relevant_knowledge_refs: list[dict[str, Any]]
    irrelevant_knowledge_refs: list[dict[str, Any]]
    support_dependency_graph: dict[str, Any]
    support_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GoalCurrentAuthorityEngine:
    """The sole owner of current Goal lifecycle decisions."""

    schema_version = "1.0"
    system_name = "goal_current_authority_engine"
    authority = "GOAL_CURRENT_AUTHORITY"

    def __init__(
        self,
        state_dir: str | Path | None = None,
        *,
        knowledge_admission_gate: CurrentKnowledgeAdmissionGate | None = None,
    ) -> None:
        self.state_dir = Path(state_dir) if state_dir is not None else None
        self.knowledge_admission_gate = (
            knowledge_admission_gate or CurrentKnowledgeAdmissionGate()
        )

    def create_subject(
        self,
        *,
        goal_type: str,
        objective: str,
        target_state: str = "UNSPECIFIED",
        scope: str = "GLOBAL",
        domain: str = "GENERAL",
        context_class: str = "GENERAL",
        constraint_domain: str = "GENERAL",
        parent_goal_id: str | None = None,
        depends_on_goal_ids: Iterable[Any] | None = None,
    ) -> GoalSubject:
        if goal_type in UNKNOWN:
            raise ValueError("goal_type_required")
        if objective in UNKNOWN:
            raise ValueError("goal_objective_required")
        return GoalSubject(
            goal_type=goal_type,
            objective=objective,
            target_state=target_state,
            scope=scope,
            domain=domain,
            context_class=context_class,
            constraint_domain=constraint_domain,
            parent_goal_id=parent_goal_id,
            depends_on_goal_ids=tuple(
                _canon(item) for item in depends_on_goal_ids or [] if _canon(item)
            ),
        )

    def create_proposal(
        self,
        subject: GoalSubject | Mapping[str, Any],
        *,
        source: str,
        support_refs: Iterable[Mapping[str, Any]] | None = None,
        constraint_refs: Iterable[Mapping[str, Any]] | None = None,
        conflict_refs: Iterable[Mapping[str, Any]] | None = None,
        planning_refs: Iterable[Mapping[str, Any]] | None = None,
        capability_refs: Iterable[Mapping[str, Any]] | None = None,
        provenance: Mapping[str, Any] | None = None,
        proposal_context: Mapping[str, Any] | None = None,
        priority_score: float | None = None,
    ) -> GoalProposal:
        subject_record = _subject_record(subject)
        goal_id = str(subject_record["goal_id"])
        instance_seed = {
            "goal_id": goal_id,
            "source": _canon(source),
            "proposal_context": dict(proposal_context or {}),
            "constraint_refs": _records(constraint_refs),
            "planning_refs": _records(planning_refs),
        }
        goal_instance_id = f"goal_instance_{_sha1(instance_seed)}"
        revision_seed = {
            "goal_instance_id": goal_instance_id,
            "goal_subject": subject_record,
            "support_refs": _records(support_refs),
            "constraint_refs": _records(constraint_refs),
            "conflict_refs": _records(conflict_refs),
            "planning_refs": _records(planning_refs),
            "capability_refs": _records(capability_refs),
            "source": _canon(source),
            "provenance": dict(provenance or {}),
            "authority": "NONE",
        }
        goal_revision_id = f"goal_revision_{_sha1(revision_seed)}"
        proposal_seed = {**revision_seed, "goal_revision_id": goal_revision_id}
        proposal_id = f"goal_proposal_{_sha1(proposal_seed)}"
        return GoalProposal(
            goal_proposal_id=proposal_id,
            goal_id=goal_id,
            goal_instance_id=goal_instance_id,
            goal_revision_id=goal_revision_id,
            goal_subject=subject_record,
            source=_canon(source),
            support_refs=proposal_seed["support_refs"],
            constraint_refs=proposal_seed["constraint_refs"],
            conflict_refs=proposal_seed["conflict_refs"],
            planning_refs=proposal_seed["planning_refs"],
            capability_refs=proposal_seed["capability_refs"],
            provenance=dict(provenance or {}),
            proposal_fingerprint=self._fingerprint(proposal_seed),
            priority_score=priority_score,
        )

    def assess_proposal(
        self,
        proposal: GoalProposal | Mapping[str, Any],
        subject: GoalSubject | Mapping[str, Any],
        *,
        min_relevant_knowledge: int = 0,
        conflict_recommendation: str | None = None,
    ) -> GoalAssessment:
        proposal_record = _object_dict(proposal)
        subject_record = _subject_record(subject)
        failures: list[str] = []
        if proposal_record.get("authority") != "NONE":
            failures.append("GOAL_PROPOSAL_MUST_HAVE_NO_AUTHORITY")
        if proposal_record.get("goal_id") != subject_record.get("goal_id"):
            failures.append("GOAL_SUBJECT_IDENTITY_MISMATCH")
        if not proposal_record.get("goal_proposal_id"):
            failures.append("GOAL_PROPOSAL_ID_MISSING")
        if not proposal_record.get("goal_instance_id"):
            failures.append("GOAL_INSTANCE_ID_MISSING")
        if not proposal_record.get("goal_revision_id"):
            failures.append("GOAL_REVISION_ID_MISSING")
        if not proposal_record.get("proposal_fingerprint"):
            failures.append("GOAL_PROPOSAL_FINGERPRINT_MISSING")

        source = _canon(proposal_record.get("source"))
        source_valid = source in GOAL_SOURCES
        if not source_valid:
            failures.append("GOAL_SOURCE_INVALID")
        if source == "SELF_IMPROVEMENT_PROPOSED" and not _explicit_governed_request(
            proposal_record
        ):
            failures.append("SELF_IMPROVEMENT_GOAL_REQUIRES_EXTERNAL_GOVERNANCE")

        provenance = proposal_record.get("provenance")
        provenance_valid = isinstance(provenance, Mapping) and bool(
            provenance.get("origin")
            or provenance.get("user_request_id")
            or provenance.get("task_id")
            or provenance.get("planning_decision_id")
            or provenance.get("governance_event_id")
        )
        if not provenance_valid:
            failures.append("GOAL_PROVENANCE_INVALID")

        graph = self.goal_support_dependency_graph(proposal_record, subject_record)
        current_refs: list[dict[str, Any]] = []
        denied_refs: list[dict[str, Any]] = []
        relevant_refs: list[dict[str, Any]] = []
        irrelevant_refs: list[dict[str, Any]] = []
        for row in graph["support_refs"]:
            if row.get("support_type") == "knowledge" or row.get("knowledge_id"):
                admission = self.knowledge_admission_gate.admit_current_knowledge(
                    row,
                    consumer_scope="goal_support_dependency",
                )
                enriched = {**row, "current_knowledge_admission": admission.to_dict()}
                if admission.admitted:
                    current_refs.append(enriched)
                    if self._knowledge_relevant(enriched, subject_record):
                        relevant_refs.append(enriched)
                    else:
                        irrelevant_refs.append(enriched)
                else:
                    denied_refs.append(enriched)
        if denied_refs:
            failures.append("NONCURRENT_KNOWLEDGE_SUPPORT_REJECTED")
        if irrelevant_refs:
            failures.append("IRRELEVANT_KNOWLEDGE_SUPPORT_REJECTED")
        if len(relevant_refs) < int(min_relevant_knowledge or 0):
            failures.append("INSUFFICIENT_RELEVANT_KNOWLEDGE_SUPPORT")

        conflict_state = (
            "CONFLICT_REVIEW_RECOMMENDED"
            if conflict_recommendation in {"REVIEW", "PAUSE", "REJECT"}
            else "NO_BLOCKING_CONFLICT"
        )
        if conflict_recommendation == "REJECT":
            failures.append("GOAL_CONFLICT_BLOCKING")

        identity_state = "IDENTITY_VALID" if not _unknown(subject_record.get("goal_id")) else "IDENTITY_INVALID"
        objective_state = (
            "OBJECTIVE_COHERENT"
            if not _unknown(subject_record.get("objective"))
            else "OBJECTIVE_MISSING"
        )
        if identity_state != "IDENTITY_VALID":
            failures.append("GOAL_IDENTITY_INVALID")
        if objective_state != "OBJECTIVE_COHERENT":
            failures.append("GOAL_OBJECTIVE_INCOHERENT")

        support_fingerprint = self._fingerprint(graph)
        assessment_seed = {
            "goal_id": proposal_record.get("goal_id"),
            "goal_instance_id": proposal_record.get("goal_instance_id"),
            "goal_proposal_id": proposal_record.get("goal_proposal_id"),
            "failures": sorted(failures),
            "support_fingerprint": support_fingerprint,
        }
        predicate = not failures
        return GoalAssessment(
            goal_assessment_id=f"goal_assessment_{_sha1(assessment_seed)}",
            goal_id=str(proposal_record.get("goal_id")),
            goal_instance_id=str(proposal_record.get("goal_instance_id")),
            goal_proposal_id=str(proposal_record.get("goal_proposal_id")),
            assessment_state=(
                "GOAL_ASSESSMENT_PASSED"
                if predicate
                else "GOAL_ASSESSMENT_FAILED"
            ),
            goal_authority_predicate_satisfied=predicate,
            failures=failures,
            identity_validity_state=identity_state,
            source_validity_state=(
                "GOAL_SOURCE_VALID" if source_valid else "GOAL_SOURCE_INVALID"
            ),
            provenance_state=(
                "GOAL_PROVENANCE_VALID"
                if provenance_valid
                else "GOAL_PROVENANCE_INVALID"
            ),
            scope_state="GOAL_SCOPE_VALID",
            objective_coherence_state=objective_state,
            target_state_validity_state="TARGET_STATE_VALID",
            constraint_compatibility_state="CONSTRAINTS_COMPATIBLE",
            governance_compatibility_state="GOVERNANCE_COMPATIBLE",
            conflict_state=conflict_state,
            dependency_state="DEPENDENCIES_VALID",
            support_state=(
                "GOAL_SUPPORT_CURRENT" if current_refs else "GOAL_SUPPORT_NOT_REQUIRED"
            ),
            planning_compatibility_state="PLANNING_REFS_ADVISORY",
            priority_role="GOAL_PRIORITY_ADVISORY_ONLY",
            priority_authority_status="ADVISORY_GOVERNED",
            conflict_authority_status="ADVISORY_GOVERNED",
            current_knowledge_refs=current_refs,
            denied_knowledge_refs=denied_refs,
            relevant_knowledge_refs=relevant_refs,
            irrelevant_knowledge_refs=irrelevant_refs,
            support_dependency_graph=graph,
            support_fingerprint=support_fingerprint,
        )

    def commit_goal(
        self,
        subject: GoalSubject | Mapping[str, Any],
        proposal: GoalProposal | Mapping[str, Any],
        assessment: GoalAssessment | Mapping[str, Any],
        *,
        previous_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._decision(
            subject,
            proposal,
            assessment,
            requested_status=GoalLifecycleStatus.ACTIVE.value,
            granted_status=GoalLifecycleStatus.ACTIVE.value,
            previous_state=previous_state,
            decision_type="GoalAuthorityDecision",
        )

    def current_state_from_decision(
        self,
        previous_state: Mapping[str, Any] | None,
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        decision_record = dict(decision or {})
        if decision_record.get("authority") != self.authority:
            raise ValueError("goal_authority_required")
        if decision_record.get("decision_fingerprint") != self._decision_fingerprint(
            decision_record
        ):
            raise ValueError("goal_decision_fingerprint_invalid")
        previous = dict(previous_state or {})
        if previous and previous.get("goal_id") != decision_record.get("goal_id"):
            raise ValueError("cross_goal_decision_rejected")
        expected_previous = previous.get("current_goal_decision_id")
        if expected_previous and decision_record.get("previous_decision_id") != expected_previous:
            raise ValueError("stale_goal_decision_rejected")
        state = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "authority": self.authority,
            "goal_id": decision_record.get("goal_id"),
            "goal_instance_id": decision_record.get("goal_instance_id"),
            "goal_revision_id": decision_record.get("goal_revision_id"),
            "goal_proposal_id": decision_record.get("goal_proposal_id"),
            "goal_assessment_id": decision_record.get("goal_assessment_id"),
            "goal_subject": decision_record.get("goal_subject"),
            "source": decision_record.get("source"),
            "support_refs": decision_record.get("support_refs", []),
            "constraint_refs": decision_record.get("constraint_refs", []),
            "conflict_refs": decision_record.get("conflict_refs", []),
            "planning_refs": decision_record.get("planning_refs", []),
            "capability_refs": decision_record.get("capability_refs", []),
            "support_dependency_graph": decision_record.get(
                "support_dependency_graph", {}
            ),
            "lifecycle_status": decision_record.get("granted_status"),
            "current_goal_decision_id": decision_record.get("goal_decision_id"),
            "goal_decision_fingerprint": decision_record.get(
                "decision_fingerprint"
            ),
            "current_goal_authority_status": "CURRENT_GOAL_AUTHORITY_VERIFIED",
            "planning_authority": "NONE",
            "action_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "capability_authority": "NONE",
            "history": list(previous.get("history", [])),
        }
        if previous:
            state["history"].append(
                {
                    "goal_id": previous.get("goal_id"),
                    "goal_instance_id": previous.get("goal_instance_id"),
                    "goal_revision_id": previous.get("goal_revision_id"),
                    "current_goal_decision_id": previous.get(
                        "current_goal_decision_id"
                    ),
                    "lifecycle_status": previous.get("lifecycle_status"),
                    "fingerprint": previous.get("fingerprint"),
                }
            )
        state["fingerprint"] = self._fingerprint(
            {key: value for key, value in state.items() if key != "fingerprint"}
        )
        return state

    def open_review(
        self,
        current_state: Mapping[str, Any],
        *,
        trigger: str,
        affected_dependencies: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if trigger not in REVIEW_TRIGGERS:
            raise ValueError("goal_review_trigger_not_allowed")
        state = dict(current_state or {})
        decision = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "decision_type": "GoalReviewDecision",
            "goal_decision_id": "",
            "goal_id": state.get("goal_id"),
            "goal_instance_id": state.get("goal_instance_id"),
            "goal_revision_id": state.get("goal_revision_id"),
            "previous_decision_id": state.get("current_goal_decision_id"),
            "current_goal_decision_id": state.get("current_goal_decision_id"),
            "goal_proposal_id": state.get("goal_proposal_id"),
            "goal_assessment_id": state.get("goal_assessment_id"),
            "goal_subject": state.get("goal_subject"),
            "source": state.get("source"),
            "requested_status": GoalLifecycleStatus.UNDER_REVIEW.value,
            "granted_status": GoalLifecycleStatus.UNDER_REVIEW.value,
            "support_refs": state.get("support_refs", []),
            "constraint_refs": state.get("constraint_refs", []),
            "conflict_refs": state.get("conflict_refs", []),
            "planning_refs": state.get("planning_refs", []),
            "capability_refs": state.get("capability_refs", []),
            "support_dependency_graph": state.get("support_dependency_graph", {}),
            "trigger": trigger,
            "affected_dependencies": _records(affected_dependencies),
            "authority": self.authority,
            "timestamp": str(datetime.utcnow()),
        }
        decision_id = f"goal_review_decision_{_sha1(decision)}"
        decision["goal_decision_id"] = decision_id
        decision["decision_fingerprint"] = self._decision_fingerprint(decision)
        decision["fingerprint"] = decision["decision_fingerprint"]
        return decision

    def pause_goal(self, current_state: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
        return self._status_decision(
            current_state,
            decision_type="GoalPauseDecision",
            requested_status=GoalLifecycleStatus.PAUSED.value,
            granted_status=GoalLifecycleStatus.PAUSED.value,
            reason=reason,
            support_evaluation={},
        )

    def satisfy_goal(
        self,
        current_state: Mapping[str, Any],
        *,
        target_state_evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not target_state_evidence:
            raise ValueError("target_state_evidence_required")
        return self._status_decision(
            current_state,
            decision_type="GoalSatisfactionDecision",
            requested_status=GoalLifecycleStatus.SATISFIED.value,
            granted_status=GoalLifecycleStatus.SATISFIED.value,
            reason="target_state_evidence_accepted",
            support_evaluation=dict(target_state_evidence),
        )

    def invalidate_goal(self, current_state: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
        return self._status_decision(
            current_state,
            decision_type="GoalInvalidationDecision",
            requested_status=GoalLifecycleStatus.INVALIDATED.value,
            granted_status=GoalLifecycleStatus.INVALIDATED.value,
            reason=reason,
            support_evaluation={},
        )

    def abandon_goal(self, current_state: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
        return self._status_decision(
            current_state,
            decision_type="GoalAbandonmentDecision",
            requested_status=GoalLifecycleStatus.ABANDONED.value,
            granted_status=GoalLifecycleStatus.ABANDONED.value,
            reason=reason,
            support_evaluation={},
        )

    def reassess_under_review(
        self,
        current_state: Mapping[str, Any],
        *,
        assessment: GoalAssessment | Mapping[str, Any],
        decision_result: str | None = None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        if state.get("lifecycle_status") != GoalLifecycleStatus.UNDER_REVIEW.value:
            raise ValueError("under_review_goal_required")
        assessment_record = _object_dict(assessment)
        passed = bool(assessment_record.get("goal_authority_predicate_satisfied"))
        granted = (
            GoalLifecycleStatus.ACTIVE.value
            if passed and decision_result == GoalLifecycleStatus.ACTIVE.value
            else GoalLifecycleStatus.REVALIDATION_REQUIRED.value
        )
        return self._status_decision(
            state,
            decision_type="GoalRevalidationDecision",
            requested_status=decision_result or granted,
            granted_status=granted,
            reason="goal_reassessment",
            support_evaluation=assessment_record,
        )

    def supersede_goal(
        self,
        current_state: Mapping[str, Any],
        *,
        replacement_subject: GoalSubject | Mapping[str, Any],
        replacement_proposal: GoalProposal | Mapping[str, Any],
        replacement_assessment: GoalAssessment | Mapping[str, Any],
        reason: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        state = dict(current_state or {})
        if state.get("lifecycle_status") != GoalLifecycleStatus.ACTIVE.value:
            raise ValueError("active_goal_required_for_supersession")
        supersession = self._status_decision(
            state,
            decision_type="GoalSupersessionDecision",
            requested_status=GoalLifecycleStatus.SUPERSEDED.value,
            granted_status=GoalLifecycleStatus.SUPERSEDED.value,
            reason=reason,
            support_evaluation={},
        )
        replacement = self.commit_goal(
            replacement_subject,
            replacement_proposal,
            replacement_assessment,
        )
        replacement["supersedes_goal_id"] = state.get("goal_id")
        replacement["supersedes_goal_decision_id"] = state.get(
            "current_goal_decision_id"
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
            "signal": "GOAL_REASSESSMENT_REQUIRED",
            "authority": "NONE",
            "goal_authority": "NONE",
            "goal_id": current_state.get("goal_id") if isinstance(current_state, Mapping) else None,
            "current_goal_decision_id": (
                current_state.get("current_goal_decision_id")
                if isinstance(current_state, Mapping)
                else None
            ),
            "trigger": trigger,
            "upstream_report": dict(upstream_report or {}),
            "direct_goal_mutation": False,
        }

    def get_current_goal_state(self, goal_id: str) -> dict[str, Any]:
        if self.state_dir is None:
            return {}
        path = self._current_path(goal_id)
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def get_goal_history(self, goal_id: str) -> list[dict[str, Any]]:
        current = self.get_current_goal_state(goal_id)
        history = current.get("history", []) if isinstance(current, Mapping) else []
        rows = [row for row in history if isinstance(row, Mapping)]
        if current:
            rows.append(dict(current))
        return rows

    def is_goal_current(self, goal: Mapping[str, Any]) -> dict[str, Any]:
        candidate = dict(goal or {})
        goal_id = candidate.get("goal_id")
        current = self.get_current_goal_state(str(goal_id)) if goal_id else {}
        if not current:
            return self._currentness(False, "CURRENT_GOAL_STATE_NOT_FOUND")
        if current.get("lifecycle_status") != GoalLifecycleStatus.ACTIVE.value:
            return self._currentness(False, "CURRENT_GOAL_NOT_ACTIVE", current)
        if candidate.get("current_goal_decision_id") != current.get(
            "current_goal_decision_id"
        ):
            return self._currentness(False, "STALE_GOAL_DECISION", current)
        if candidate.get("fingerprint") != current.get("fingerprint"):
            return self._currentness(False, "STALE_GOAL_STATE_REJECTED", current)
        return self._currentness(True, "CURRENT_GOAL_AUTHORITY_VERIFIED", current)

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
        goal_id = str(payload.get("goal_id") or "")
        if not goal_id:
            raise ValueError("goal_id_required_for_persistence")
        self._current_path(goal_id).parent.mkdir(parents=True, exist_ok=True)
        self._history_dir(goal_id).mkdir(parents=True, exist_ok=True)
        self._current_path(goal_id).write_text(
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
                record.get("goal_decision_id")
                or record.get("goal_assessment_id")
                or record.get("goal_proposal_id")
                or _sha1(record)
            )
            (self._history_dir(goal_id) / f"{label}_{record_id}.json").write_text(
                json.dumps(record, indent=2, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
        return {
            "persistence_attempted": True,
            "persistence_state": "CURRENT_GOAL_STATE_PERSISTED",
            "persistence_implies_goal_authority": False,
            "goal_id": goal_id,
            "current_goal_decision_id": payload.get("current_goal_decision_id"),
        }

    def goal_support_dependency_graph(
        self,
        proposal: Mapping[str, Any],
        subject: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "goal_id": proposal.get("goal_id") or subject.get("goal_id"),
            "goal_instance_id": proposal.get("goal_instance_id"),
            "goal_revision_id": proposal.get("goal_revision_id"),
            "goal_proposal_id": proposal.get("goal_proposal_id"),
            "goal_subject": dict(subject),
            "support_refs": _records(proposal.get("support_refs")),
            "constraint_refs": _records(proposal.get("constraint_refs")),
            "conflict_refs": _records(proposal.get("conflict_refs")),
            "planning_refs": _records(proposal.get("planning_refs")),
            "capability_refs": _records(proposal.get("capability_refs")),
            "parent_goal_id": subject.get("parent_goal_id"),
            "depends_on_goal_ids": list(subject.get("depends_on_goal_ids", [])),
            "authority": "NONE",
        }

    def goal_dependency_graph(
        self,
        current_state: Mapping[str, Any],
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        subject = dict(state.get("goal_subject") or {})
        return {
            "schema_version": self.schema_version,
            "goal_id": state.get("goal_id"),
            "parent_goal_id": subject.get("parent_goal_id"),
            "child_goal_ids": [],
            "depends_on_goal_ids": list(subject.get("depends_on_goal_ids", [])),
            "support_dependencies": state.get("support_refs", []),
            "constraint_dependencies": state.get("constraint_refs", []),
            "planning_dependencies": state.get("planning_refs", []),
            "dependency_graph_authority": "NONE",
        }

    def _decision(
        self,
        subject: GoalSubject | Mapping[str, Any],
        proposal: GoalProposal | Mapping[str, Any],
        assessment: GoalAssessment | Mapping[str, Any],
        *,
        requested_status: str,
        granted_status: str,
        previous_state: Mapping[str, Any] | None,
        decision_type: str,
    ) -> dict[str, Any]:
        subject_record = _subject_record(subject)
        proposal_record = _object_dict(proposal)
        assessment_record = _object_dict(assessment)
        if not assessment_record.get("goal_authority_predicate_satisfied"):
            raise ValueError("goal_assessment_does_not_grant_authority")
        if proposal_record.get("goal_id") != subject_record.get("goal_id"):
            raise ValueError("goal_subject_proposal_mismatch")
        if assessment_record.get("goal_proposal_id") != proposal_record.get(
            "goal_proposal_id"
        ):
            raise ValueError("goal_assessment_proposal_mismatch")
        previous = dict(previous_state or {})
        decision = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "decision_type": decision_type,
            "goal_decision_id": "",
            "goal_id": proposal_record.get("goal_id"),
            "goal_instance_id": proposal_record.get("goal_instance_id"),
            "goal_revision_id": proposal_record.get("goal_revision_id"),
            "previous_decision_id": previous.get("current_goal_decision_id"),
            "goal_proposal_id": proposal_record.get("goal_proposal_id"),
            "goal_assessment_id": assessment_record.get("goal_assessment_id"),
            "goal_subject": subject_record,
            "source": proposal_record.get("source"),
            "requested_status": requested_status,
            "granted_status": granted_status,
            "support_refs": list(assessment_record.get("relevant_knowledge_refs", [])),
            "constraint_refs": list(proposal_record.get("constraint_refs", [])),
            "conflict_refs": list(proposal_record.get("conflict_refs", [])),
            "planning_refs": list(proposal_record.get("planning_refs", [])),
            "capability_refs": list(proposal_record.get("capability_refs", [])),
            "support_dependency_graph": assessment_record.get(
                "support_dependency_graph", {}
            ),
            "authority": self.authority,
            "planning_authority": "NONE",
            "action_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "capability_authority": "NONE",
            "timestamp": str(datetime.utcnow()),
        }
        decision_id = f"goal_decision_{_sha1(decision)}"
        decision["goal_decision_id"] = decision_id
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
            GoalLifecycleStatus.ACTIVE.value,
            GoalLifecycleStatus.PAUSED.value,
            GoalLifecycleStatus.UNDER_REVIEW.value,
            GoalLifecycleStatus.REVALIDATION_REQUIRED.value,
        }:
            raise ValueError("current_goal_required_for_lifecycle_transition")
        decision = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "decision_type": decision_type,
            "goal_decision_id": "",
            "goal_id": state.get("goal_id"),
            "goal_instance_id": state.get("goal_instance_id"),
            "goal_revision_id": state.get("goal_revision_id"),
            "previous_decision_id": state.get("current_goal_decision_id"),
            "goal_proposal_id": state.get("goal_proposal_id"),
            "goal_assessment_id": state.get("goal_assessment_id"),
            "goal_subject": state.get("goal_subject"),
            "source": state.get("source"),
            "requested_status": requested_status,
            "granted_status": granted_status,
            "support_refs": state.get("support_refs", []),
            "constraint_refs": state.get("constraint_refs", []),
            "conflict_refs": state.get("conflict_refs", []),
            "planning_refs": state.get("planning_refs", []),
            "capability_refs": state.get("capability_refs", []),
            "support_dependency_graph": state.get("support_dependency_graph", {}),
            "authority": self.authority,
            "reason": reason,
            "support_evaluation": dict(support_evaluation or {}),
            "planning_authority": "NONE",
            "action_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "capability_authority": "NONE",
            "timestamp": str(datetime.utcnow()),
        }
        prefix = _camel_to_snake(decision_type)
        decision_id = f"{prefix}_{_sha1(decision)}"
        decision["goal_decision_id"] = decision_id
        decision["decision_fingerprint"] = self._decision_fingerprint(decision)
        return decision

    def _knowledge_relevant(
        self,
        knowledge: Mapping[str, Any],
        subject: Mapping[str, Any],
    ) -> bool:
        objective = _canon(subject.get("objective"))
        goal_id = _canon(subject.get("goal_id"))
        claim_id = _canon(knowledge.get("claim_id"))
        knowledge_id = _canon(knowledge.get("knowledge_id"))
        subject_id = _canon(knowledge.get("subject_id"))
        if {objective, goal_id} & {claim_id, knowledge_id, subject_id}:
            return True
        if _canon(knowledge.get("goal_relevance")) == "RELEVANT":
            return True
        return False

    def _currentness(
        self,
        current: bool,
        reason: str,
        state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "is_current_goal": current,
            "current_goal_state": "CURRENT_GOAL" if current else "HISTORICAL_GOAL",
            "reason": reason,
            "goal_id": (state or {}).get("goal_id"),
            "current_goal_decision_id": (state or {}).get(
                "current_goal_decision_id"
            ),
        }

    def _current_path(self, goal_id: str) -> Path:
        assert self.state_dir is not None
        return self.state_dir / "current" / f"{goal_id}.json"

    def _history_dir(self, goal_id: str) -> Path:
        assert self.state_dir is not None
        return self.state_dir / "history" / goal_id

    def _fingerprint(self, payload: Any) -> str:
        return f"goal_fingerprint_{_sha256(payload)}"

    def _decision_fingerprint(self, decision: Mapping[str, Any]) -> str:
        payload = {
            key: value
            for key, value in dict(decision).items()
            if key not in {"decision_fingerprint", "fingerprint"}
        }
        return f"goal_decision_fingerprint_{_sha256(payload)}"


def get_current_goal_state(
    goal_id: str,
    *,
    authority_engine: GoalCurrentAuthorityEngine | None = None,
) -> dict[str, Any]:
    engine = authority_engine or goal_current_authority_engine
    return engine.get_current_goal_state(goal_id)


def get_goal_history(
    goal_id: str,
    *,
    authority_engine: GoalCurrentAuthorityEngine | None = None,
) -> list[dict[str, Any]]:
    engine = authority_engine or goal_current_authority_engine
    return engine.get_goal_history(goal_id)


def is_goal_current(
    goal: Mapping[str, Any],
    *,
    authority_engine: GoalCurrentAuthorityEngine | None = None,
) -> dict[str, Any]:
    engine = authority_engine or goal_current_authority_engine
    return engine.is_goal_current(goal)


def _object_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return dict(value) if isinstance(value, Mapping) else {}


def _subject_record(value: GoalSubject | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, GoalSubject):
        return value.to_dict()
    record = dict(value) if isinstance(value, Mapping) else {}
    if "goal_id" not in record:
        subject = GoalSubject(
            goal_type=record.get("goal_type", ""),
            objective=record.get("objective", ""),
            target_state=record.get("target_state", "UNSPECIFIED"),
            scope=record.get("scope", "GLOBAL"),
            domain=record.get("domain", "GENERAL"),
            context_class=record.get("context_class", "GENERAL"),
            constraint_domain=record.get("constraint_domain", "GENERAL"),
            parent_goal_id=record.get("parent_goal_id"),
            depends_on_goal_ids=tuple(_records_to_strings(record.get("depends_on_goal_ids"))),
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
        return [str(value.get("id") or value.get("goal_id") or value)]
    return [str(item) for item in value or [] if item not in UNKNOWN]


def _explicit_governed_request(proposal: Mapping[str, Any]) -> bool:
    provenance = proposal.get("provenance")
    return isinstance(provenance, Mapping) and bool(
        provenance.get("governance_event_id")
        or provenance.get("user_request_id")
        or provenance.get("external_authorization")
    )


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


goal_current_authority_engine = GoalCurrentAuthorityEngine()


__all__ = [
    "GOAL_SOURCES",
    "GoalAssessment",
    "GoalCurrentAuthorityEngine",
    "GoalLifecycleStatus",
    "GoalProposal",
    "GoalSubject",
    "REVIEW_TRIGGERS",
    "get_current_goal_state",
    "get_goal_history",
    "goal_current_authority_engine",
    "is_goal_current",
]
