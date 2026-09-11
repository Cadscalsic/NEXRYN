"""Canonical current Plan authority and lifecycle governance."""

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


class PlanLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    INVALIDATED = "INVALIDATED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    SUPERSEDED = "SUPERSEDED"


REVIEW_TRIGGERS = {
    "SUPPORTING_KNOWLEDGE_UNDER_REVIEW",
    "SUPPORTING_KNOWLEDGE_INVALIDATED",
    "SUPPORTING_KNOWLEDGE_SUPERSEDED",
    "SUPPORTING_KNOWLEDGE_REVALIDATION_REQUIRED",
    "OBJECTIVE_CHANGED",
    "GOAL_CHANGED",
    "CONSTRAINT_CHANGED",
    "DEPENDENCY_INVALIDATED",
    "STRATEGY_INVALIDATED",
    "GOVERNANCE_CONTEXT_CHANGED",
    "BUDGET_CONTEXT_CHANGED",
    "PLAN_DECISION_INTEGRITY_FAILURE",
    "PLANNING_PROVENANCE_INVALID",
    "GOVERNANCE_REVIEW_REQUIRED",
}


@dataclass(frozen=True)
class PlanningSubject:
    objective_refs: tuple[str, ...]
    planning_scope: str = "GLOBAL"
    domain: str = "GENERAL"
    context_class: str = "GENERAL"
    constraint_domain: str = "GENERAL"

    @property
    def plan_id(self) -> str:
        seed = {
            "objective_refs": sorted(_canon(item) for item in self.objective_refs),
            "planning_scope": _canon(self.planning_scope),
            "domain": _canon(self.domain),
            "context_class": _canon(self.context_class),
            "constraint_domain": _canon(self.constraint_domain),
        }
        return f"plan_{_sha1(seed)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "objective_refs": list(self.objective_refs),
            "planning_scope": _canon(self.planning_scope),
            "domain": _canon(self.domain),
            "context_class": _canon(self.context_class),
            "constraint_domain": _canon(self.constraint_domain),
            "identity_excludes_run_id": True,
            "identity_excludes_task_id": True,
            "identity_excludes_timestamp": True,
            "identity_excludes_artifact_path": True,
            "identity_excludes_knowledge_decision_id": True,
        }


@dataclass(frozen=True)
class PlanCandidate:
    plan_candidate_id: str
    plan_id: str
    plan_instance_id: str
    planning_subject: dict[str, Any]
    objective_refs: list[str]
    goal_refs: list[dict[str, Any]]
    supporting_knowledge_refs: list[dict[str, Any]]
    strategy_refs: list[dict[str, Any]]
    dependency_refs: list[dict[str, Any]]
    constraint_refs: list[dict[str, Any]]
    proposed_operations: list[dict[str, Any]]
    source_planner: str
    provenance: dict[str, Any]
    candidate_fingerprint: str
    authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlanAssessment:
    plan_assessment_id: str
    plan_id: str
    plan_instance_id: str
    plan_candidate_id: str
    assessment_state: str
    plan_authority_predicate_satisfied: bool
    failures: list[str]
    current_knowledge_refs: list[dict[str, Any]]
    denied_knowledge_refs: list[dict[str, Any]]
    relevant_knowledge_refs: list[dict[str, Any]]
    irrelevant_knowledge_refs: list[dict[str, Any]]
    goal_compatibility_state: str
    objective_consistency_state: str
    dependency_validity_state: str
    constraint_satisfaction_state: str
    governance_compatibility_state: str
    resource_feasibility_state: str
    budget_feasibility_state: str
    strategy_coherence_state: str
    support_dependency_graph: dict[str, Any]
    support_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PlanningCurrentAuthorityEngine:
    """The sole owner of current Plan lifecycle decisions."""

    schema_version = "1.0"
    system_name = "planning_current_authority_engine"
    authority = "PLANNING_CURRENT_AUTHORITY"

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
        objective_refs: Iterable[Any],
        planning_scope: str = "GLOBAL",
        domain: str = "GENERAL",
        context_class: str = "GENERAL",
        constraint_domain: str = "GENERAL",
    ) -> PlanningSubject:
        objectives = tuple(
            _canon(item) for item in objective_refs or [] if _canon(item)
        )
        if not objectives:
            raise ValueError("planning_objective_ref_required")
        return PlanningSubject(
            objective_refs=objectives,
            planning_scope=planning_scope,
            domain=domain,
            context_class=context_class,
            constraint_domain=constraint_domain,
        )

    def create_candidate(
        self,
        subject: PlanningSubject | Mapping[str, Any],
        *,
        goal_refs: Iterable[Mapping[str, Any]] | None = None,
        supporting_knowledge_refs: Iterable[Mapping[str, Any]] | None = None,
        strategy_refs: Iterable[Mapping[str, Any]] | None = None,
        dependency_refs: Iterable[Mapping[str, Any]] | None = None,
        constraint_refs: Iterable[Mapping[str, Any]] | None = None,
        proposed_operations: Iterable[Mapping[str, Any]] | None = None,
        source_planner: str = "planning_proposal",
        provenance: Mapping[str, Any] | None = None,
        plan_instance_context: Mapping[str, Any] | None = None,
    ) -> PlanCandidate:
        subject_record = _subject_record(subject)
        plan_id = str(subject_record["plan_id"])
        instance_seed = {
            "plan_id": plan_id,
            "source_planner": source_planner,
            "plan_instance_context": dict(plan_instance_context or {}),
            "proposed_operations": _records(proposed_operations),
            "constraint_refs": _records(constraint_refs),
        }
        plan_instance_id = f"plan_instance_{_sha1(instance_seed)}"
        seed = {
            "plan_id": plan_id,
            "plan_instance_id": plan_instance_id,
            "planning_subject": subject_record,
            "objective_refs": list(subject_record.get("objective_refs") or []),
            "goal_refs": _records(goal_refs),
            "supporting_knowledge_refs": _records(supporting_knowledge_refs),
            "strategy_refs": _records(strategy_refs),
            "dependency_refs": _records(dependency_refs),
            "constraint_refs": _records(constraint_refs),
            "proposed_operations": _records(proposed_operations),
            "source_planner": str(source_planner),
            "provenance": dict(provenance or {}),
            "authority": "NONE",
        }
        candidate_id = f"plan_candidate_{_sha1(seed)}"
        candidate_fingerprint = self._fingerprint({**seed, "plan_candidate_id": candidate_id})
        return PlanCandidate(
            plan_candidate_id=candidate_id,
            plan_id=plan_id,
            plan_instance_id=plan_instance_id,
            planning_subject=subject_record,
            objective_refs=seed["objective_refs"],
            goal_refs=seed["goal_refs"],
            supporting_knowledge_refs=seed["supporting_knowledge_refs"],
            strategy_refs=seed["strategy_refs"],
            dependency_refs=seed["dependency_refs"],
            constraint_refs=seed["constraint_refs"],
            proposed_operations=seed["proposed_operations"],
            source_planner=str(source_planner),
            provenance=dict(provenance or {}),
            candidate_fingerprint=candidate_fingerprint,
        )

    def assess_candidate(
        self,
        candidate: PlanCandidate | Mapping[str, Any],
        subject: PlanningSubject | Mapping[str, Any],
        *,
        min_relevant_knowledge: int = 0,
    ) -> PlanAssessment:
        candidate_record = _object_dict(candidate)
        subject_record = _subject_record(subject)
        failures: list[str] = []
        if candidate_record.get("authority") != "NONE":
            failures.append("PLAN_CANDIDATE_MUST_HAVE_NO_AUTHORITY")
        if candidate_record.get("plan_id") != subject_record.get("plan_id"):
            failures.append("PLAN_SUBJECT_IDENTITY_MISMATCH")
        if not candidate_record.get("plan_candidate_id"):
            failures.append("PLAN_CANDIDATE_ID_MISSING")
        if not candidate_record.get("plan_instance_id"):
            failures.append("PLAN_INSTANCE_ID_MISSING")
        if not candidate_record.get("candidate_fingerprint"):
            failures.append("PLAN_CANDIDATE_FINGERPRINT_MISSING")

        graph = self.plan_support_dependency_graph(candidate_record, subject_record)
        current_refs: list[dict[str, Any]] = []
        denied_refs: list[dict[str, Any]] = []
        relevant_refs: list[dict[str, Any]] = []
        irrelevant_refs: list[dict[str, Any]] = []
        for row in graph["supporting_knowledge_refs"]:
            admission = self.knowledge_admission_gate.admit_current_knowledge(
                row,
                consumer_scope="planning_support_dependency",
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

        objective_state = (
            "OBJECTIVE_CONSISTENT"
            if candidate_record.get("objective_refs")
            else "OBJECTIVE_MISSING"
        )
        if objective_state != "OBJECTIVE_CONSISTENT":
            failures.append("OBJECTIVE_INCONSISTENT")
        dependency_state = "DEPENDENCIES_VALID"
        constraint_state = "CONSTRAINTS_SATISFIED"
        governance_state = "GOVERNANCE_COMPATIBLE"
        resource_state = "RESOURCE_FEASIBLE"
        budget_state = "BUDGET_FEASIBLE"
        strategy_state = "STRATEGY_COHERENT"
        support_fingerprint = self._fingerprint(graph)
        assessment_seed = {
            "plan_id": candidate_record.get("plan_id"),
            "plan_instance_id": candidate_record.get("plan_instance_id"),
            "plan_candidate_id": candidate_record.get("plan_candidate_id"),
            "failures": sorted(failures),
            "support_fingerprint": support_fingerprint,
        }
        predicate = not failures
        return PlanAssessment(
            plan_assessment_id=f"plan_assessment_{_sha1(assessment_seed)}",
            plan_id=str(candidate_record.get("plan_id")),
            plan_instance_id=str(candidate_record.get("plan_instance_id")),
            plan_candidate_id=str(candidate_record.get("plan_candidate_id")),
            assessment_state=(
                "PLAN_ASSESSMENT_PASSED"
                if predicate
                else "PLAN_ASSESSMENT_FAILED"
            ),
            plan_authority_predicate_satisfied=predicate,
            failures=failures,
            current_knowledge_refs=current_refs,
            denied_knowledge_refs=denied_refs,
            relevant_knowledge_refs=relevant_refs,
            irrelevant_knowledge_refs=irrelevant_refs,
            goal_compatibility_state="GOAL_METADATA_ADVISORY",
            objective_consistency_state=objective_state,
            dependency_validity_state=dependency_state,
            constraint_satisfaction_state=constraint_state,
            governance_compatibility_state=governance_state,
            resource_feasibility_state=resource_state,
            budget_feasibility_state=budget_state,
            strategy_coherence_state=strategy_state,
            support_dependency_graph=graph,
            support_fingerprint=support_fingerprint,
        )

    def commit_plan(
        self,
        subject: PlanningSubject | Mapping[str, Any],
        candidate: PlanCandidate | Mapping[str, Any],
        assessment: PlanAssessment | Mapping[str, Any],
        *,
        previous_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._decision(
            subject,
            candidate,
            assessment,
            requested_status=PlanLifecycleStatus.ACTIVE.value,
            granted_status=PlanLifecycleStatus.ACTIVE.value,
            previous_state=previous_state,
            decision_type="PlanningDecision",
        )

    def current_state_from_decision(
        self,
        previous_state: Mapping[str, Any] | None,
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        decision_record = dict(decision or {})
        if decision_record.get("authority") != self.authority:
            raise ValueError("planning_authority_required")
        if decision_record.get("decision_fingerprint") != self._decision_fingerprint(
            decision_record
        ):
            raise ValueError("planning_decision_fingerprint_invalid")
        previous = dict(previous_state or {})
        if previous and previous.get("plan_id") != decision_record.get("plan_id"):
            raise ValueError("cross_plan_decision_rejected")
        expected_previous = previous.get("current_planning_decision_id")
        if expected_previous and decision_record.get("previous_decision_id") != expected_previous:
            raise ValueError("stale_planning_decision_rejected")
        state = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "authority": self.authority,
            "plan_id": decision_record.get("plan_id"),
            "plan_instance_id": decision_record.get("plan_instance_id"),
            "plan_candidate_id": decision_record.get("plan_candidate_id"),
            "planning_subject": decision_record.get("planning_subject"),
            "objective_refs": decision_record.get("objective_refs", []),
            "goal_refs": decision_record.get("goal_refs", []),
            "supporting_knowledge_refs": decision_record.get(
                "supporting_knowledge_refs", []
            ),
            "strategy_refs": decision_record.get("strategy_refs", []),
            "constraint_refs": decision_record.get("constraint_refs", []),
            "dependency_refs": decision_record.get("dependency_refs", []),
            "support_dependency_graph": decision_record.get(
                "support_dependency_graph", {}
            ),
            "lifecycle_status": decision_record.get("granted_status"),
            "current_planning_decision_id": decision_record.get(
                "planning_decision_id"
            ),
            "planning_decision_fingerprint": decision_record.get(
                "decision_fingerprint"
            ),
            "current_plan_authority_status": "CURRENT_PLAN_AUTHORITY_VERIFIED",
            "action_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "goal_priority_authority_status": "GOAL_PRIORITY_AUTHORITY_UNRESOLVED",
            "goal_conflict_authority_status": "GOAL_CONFLICT_AUTHORITY_ADVISORY",
            "history": list(previous.get("history", [])),
        }
        if previous:
            state["history"].append(
                {
                    "plan_id": previous.get("plan_id"),
                    "plan_instance_id": previous.get("plan_instance_id"),
                    "current_planning_decision_id": previous.get(
                        "current_planning_decision_id"
                    ),
                    "lifecycle_status": previous.get("lifecycle_status"),
                    "fingerprint": previous.get("fingerprint"),
                }
            )
        state["fingerprint"] = self._fingerprint(
            {k: v for k, v in state.items() if k != "fingerprint"}
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
            raise ValueError("planning_review_trigger_not_allowed")
        state = dict(current_state or {})
        decision = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "decision_type": "PlanningReviewDecision",
            "review_decision_id": "",
            "planning_decision_id": "",
            "plan_id": state.get("plan_id"),
            "plan_instance_id": state.get("plan_instance_id"),
            "current_planning_decision_id": state.get(
                "current_planning_decision_id"
            ),
            "previous_decision_id": state.get("current_planning_decision_id"),
            "trigger": trigger,
            "affected_dependencies": _records(affected_dependencies),
            "current_support_state": self._current_support_state(state),
            "constraint_state": "CONSTRAINT_REVIEW_REQUIRED",
            "requested_status": PlanLifecycleStatus.UNDER_REVIEW.value,
            "granted_status": PlanLifecycleStatus.UNDER_REVIEW.value,
            "authority": self.authority,
            "timestamp": str(datetime.utcnow()),
        }
        decision_id = f"planning_review_decision_{_sha1(decision)}"
        decision["review_decision_id"] = decision_id
        decision["planning_decision_id"] = decision_id
        decision["decision_fingerprint"] = self._decision_fingerprint(decision)
        decision["fingerprint"] = decision["decision_fingerprint"]
        return decision

    def invalidate_plan(
        self,
        current_state: Mapping[str, Any],
        *,
        reason: str,
        support_evaluation: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        if state.get("lifecycle_status") not in {
            PlanLifecycleStatus.ACTIVE.value,
            PlanLifecycleStatus.UNDER_REVIEW.value,
            PlanLifecycleStatus.REVALIDATION_REQUIRED.value,
        }:
            raise ValueError("current_plan_required_for_invalidation")
        decision = self._status_decision(
            state,
            decision_type="PlanningInvalidationDecision",
            requested_status=PlanLifecycleStatus.INVALIDATED.value,
            granted_status=PlanLifecycleStatus.INVALIDATED.value,
            reason=reason,
            support_evaluation=support_evaluation or {},
        )
        return decision

    def reassess_under_review(
        self,
        current_state: Mapping[str, Any],
        *,
        assessment: PlanAssessment | Mapping[str, Any],
        decision_result: str | None = None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        if state.get("lifecycle_status") != PlanLifecycleStatus.UNDER_REVIEW.value:
            raise ValueError("under_review_plan_required")
        assessment_record = _object_dict(assessment)
        passed = bool(assessment_record.get("plan_authority_predicate_satisfied"))
        granted = (
            PlanLifecycleStatus.ACTIVE.value
            if passed and decision_result == PlanLifecycleStatus.ACTIVE.value
            else PlanLifecycleStatus.REVALIDATION_REQUIRED.value
        )
        return self._status_decision(
            state,
            decision_type="PlanningRevalidationDecision",
            requested_status=decision_result or granted,
            granted_status=granted,
            reason="planning_reassessment",
            support_evaluation=assessment_record,
        )

    def supersede_plan(
        self,
        current_state: Mapping[str, Any],
        *,
        replacement_subject: PlanningSubject | Mapping[str, Any],
        replacement_candidate: PlanCandidate | Mapping[str, Any],
        replacement_assessment: PlanAssessment | Mapping[str, Any],
        reason: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        state = dict(current_state or {})
        if state.get("lifecycle_status") != PlanLifecycleStatus.ACTIVE.value:
            raise ValueError("active_plan_required_for_supersession")
        supersession = self._status_decision(
            state,
            decision_type="PlanningSupersessionDecision",
            requested_status=PlanLifecycleStatus.SUPERSEDED.value,
            granted_status=PlanLifecycleStatus.SUPERSEDED.value,
            reason=reason,
            support_evaluation={},
        )
        replacement = self.commit_plan(
            replacement_subject,
            replacement_candidate,
            replacement_assessment,
            previous_state=None,
        )
        replacement["supersedes_plan_id"] = state.get("plan_id")
        replacement["supersedes_planning_decision_id"] = state.get(
            "current_planning_decision_id"
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
            "signal": "PLAN_SUPPORT_REASSESSMENT_REQUIRED",
            "authority": "NONE",
            "planning_authority": "NONE",
            "plan_id": current_state.get("plan_id") if isinstance(current_state, Mapping) else None,
            "current_planning_decision_id": (
                current_state.get("current_planning_decision_id")
                if isinstance(current_state, Mapping)
                else None
            ),
            "trigger": trigger,
            "upstream_report": dict(upstream_report or {}),
            "direct_plan_mutation": False,
        }

    def get_current_plan_state(self, plan_id: str) -> dict[str, Any]:
        if self.state_dir is None:
            return {}
        path = self._current_path(plan_id)
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def get_plan_history(self, plan_id: str) -> list[dict[str, Any]]:
        current = self.get_current_plan_state(plan_id)
        history = current.get("history", []) if isinstance(current, Mapping) else []
        rows = [row for row in history if isinstance(row, Mapping)]
        if current:
            rows.append(dict(current))
        return rows

    def is_plan_current(self, plan: Mapping[str, Any]) -> dict[str, Any]:
        candidate = dict(plan or {})
        plan_id = candidate.get("plan_id")
        current = self.get_current_plan_state(str(plan_id)) if plan_id else {}
        if not current:
            return self._currentness(False, "CURRENT_PLAN_STATE_NOT_FOUND")
        if current.get("lifecycle_status") != PlanLifecycleStatus.ACTIVE.value:
            return self._currentness(False, "CURRENT_PLAN_NOT_ACTIVE", current)
        if candidate.get("current_planning_decision_id") != current.get(
            "current_planning_decision_id"
        ):
            return self._currentness(False, "STALE_PLAN_DECISION", current)
        if candidate.get("fingerprint") != current.get("fingerprint"):
            return self._currentness(False, "STALE_PLAN_STATE_REJECTED", current)
        return self._currentness(True, "CURRENT_PLAN_AUTHORITY_VERIFIED", current)

    def persist_current_state(
        self,
        state: Mapping[str, Any],
        *,
        lifecycle_decision: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.state_dir is None:
            return {
                "persistence_attempted": False,
                "persistence_state": "NO_STATE_DIR_CONFIGURED",
            }
        payload = dict(state or {})
        plan_id = str(payload.get("plan_id") or "")
        if not plan_id:
            raise ValueError("plan_id_required_for_persistence")
        self._current_path(plan_id).parent.mkdir(parents=True, exist_ok=True)
        self._history_dir(plan_id).mkdir(parents=True, exist_ok=True)
        self._current_path(plan_id).write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        if lifecycle_decision:
            decision = dict(lifecycle_decision)
            decision_id = str(
                decision.get("planning_decision_id")
                or decision.get("review_decision_id")
                or _sha1(decision)
            )
            (self._history_dir(plan_id) / f"{decision_id}.json").write_text(
                json.dumps(decision, indent=2, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
        return {
            "persistence_attempted": True,
            "persistence_state": "CURRENT_PLAN_STATE_PERSISTED",
            "plan_id": plan_id,
            "current_planning_decision_id": payload.get(
                "current_planning_decision_id"
            ),
        }

    def plan_support_dependency_graph(
        self,
        candidate: Mapping[str, Any],
        subject: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "plan_id": candidate.get("plan_id") or subject.get("plan_id"),
            "plan_instance_id": candidate.get("plan_instance_id"),
            "plan_candidate_id": candidate.get("plan_candidate_id"),
            "planning_subject": dict(subject),
            "supporting_knowledge_refs": _records(
                candidate.get("supporting_knowledge_refs")
            ),
            "strategy_refs": _records(candidate.get("strategy_refs")),
            "goal_refs": _records(candidate.get("goal_refs")),
            "constraint_refs": _records(candidate.get("constraint_refs")),
            "dependency_refs": _records(candidate.get("dependency_refs")),
            "proposed_operations": _records(candidate.get("proposed_operations")),
        }

    def _decision(
        self,
        subject: PlanningSubject | Mapping[str, Any],
        candidate: PlanCandidate | Mapping[str, Any],
        assessment: PlanAssessment | Mapping[str, Any],
        *,
        requested_status: str,
        granted_status: str,
        previous_state: Mapping[str, Any] | None,
        decision_type: str,
    ) -> dict[str, Any]:
        subject_record = _subject_record(subject)
        candidate_record = _object_dict(candidate)
        assessment_record = _object_dict(assessment)
        if not assessment_record.get("plan_authority_predicate_satisfied"):
            raise ValueError("plan_assessment_does_not_grant_authority")
        if candidate_record.get("plan_id") != subject_record.get("plan_id"):
            raise ValueError("plan_subject_candidate_mismatch")
        if assessment_record.get("plan_candidate_id") != candidate_record.get(
            "plan_candidate_id"
        ):
            raise ValueError("plan_assessment_candidate_mismatch")
        previous = dict(previous_state or {})
        decision = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "decision_type": decision_type,
            "planning_decision_id": "",
            "plan_id": candidate_record.get("plan_id"),
            "plan_instance_id": candidate_record.get("plan_instance_id"),
            "previous_decision_id": previous.get("current_planning_decision_id"),
            "plan_candidate_id": candidate_record.get("plan_candidate_id"),
            "plan_assessment_id": assessment_record.get("plan_assessment_id"),
            "requested_status": requested_status,
            "granted_status": granted_status,
            "planning_subject": subject_record,
            "objective_refs": list(candidate_record.get("objective_refs", [])),
            "goal_refs": list(candidate_record.get("goal_refs", [])),
            "supporting_knowledge_refs": list(
                assessment_record.get("relevant_knowledge_refs", [])
            ),
            "strategy_refs": list(candidate_record.get("strategy_refs", [])),
            "constraint_refs": list(candidate_record.get("constraint_refs", [])),
            "dependency_refs": list(candidate_record.get("dependency_refs", [])),
            "support_dependency_graph": assessment_record.get(
                "support_dependency_graph", {}
            ),
            "authority": self.authority,
            "action_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "timestamp": str(datetime.utcnow()),
        }
        decision_id = f"planning_decision_{_sha1(decision)}"
        decision["planning_decision_id"] = decision_id
        decision["decision_fingerprint"] = self._decision_fingerprint(decision)
        return decision

    def _status_decision(
        self,
        state: Mapping[str, Any],
        *,
        decision_type: str,
        requested_status: str,
        granted_status: str,
        reason: str,
        support_evaluation: Mapping[str, Any],
    ) -> dict[str, Any]:
        decision = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "decision_type": decision_type,
            "planning_decision_id": "",
            "plan_id": state.get("plan_id"),
            "plan_instance_id": state.get("plan_instance_id"),
            "previous_decision_id": state.get("current_planning_decision_id"),
            "plan_candidate_id": state.get("plan_candidate_id"),
            "requested_status": requested_status,
            "granted_status": granted_status,
            "planning_subject": state.get("planning_subject"),
            "objective_refs": state.get("objective_refs", []),
            "goal_refs": state.get("goal_refs", []),
            "supporting_knowledge_refs": state.get("supporting_knowledge_refs", []),
            "strategy_refs": state.get("strategy_refs", []),
            "constraint_refs": state.get("constraint_refs", []),
            "dependency_refs": state.get("dependency_refs", []),
            "support_dependency_graph": state.get("support_dependency_graph", {}),
            "authority": self.authority,
            "reason": reason,
            "support_evaluation": dict(support_evaluation or {}),
            "action_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "timestamp": str(datetime.utcnow()),
        }
        prefix = _camel_to_snake(decision_type)
        decision_id = f"{prefix}_{_sha1(decision)}"
        decision["planning_decision_id"] = decision_id
        decision["decision_fingerprint"] = self._decision_fingerprint(decision)
        return decision

    def _knowledge_relevant(
        self,
        knowledge: Mapping[str, Any],
        subject: Mapping[str, Any],
    ) -> bool:
        objectives = {_canon(item) for item in subject.get("objective_refs", [])}
        claim_id = _canon(knowledge.get("claim_id"))
        knowledge_id = _canon(knowledge.get("knowledge_id"))
        subject_id = _canon(knowledge.get("subject_id"))
        if objectives & {claim_id, knowledge_id, subject_id}:
            return True
        if _canon(knowledge.get("planning_relevance")) == "RELEVANT":
            return True
        return False

    def _current_support_state(self, state: Mapping[str, Any]) -> str:
        support = state.get("supporting_knowledge_refs", [])
        return "PLAN_HAS_KNOWLEDGE_SUPPORT" if support else "PLAN_HAS_NO_KNOWLEDGE_SUPPORT"

    def _currentness(
        self,
        current: bool,
        reason: str,
        state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "is_current_plan": current,
            "current_plan_state": (
                "CURRENT_PLAN" if current else "HISTORICAL_PLAN"
            ),
            "reason": reason,
            "plan_id": (state or {}).get("plan_id"),
            "current_planning_decision_id": (state or {}).get(
                "current_planning_decision_id"
            ),
        }

    def _current_path(self, plan_id: str) -> Path:
        assert self.state_dir is not None
        return self.state_dir / "current" / f"{plan_id}.json"

    def _history_dir(self, plan_id: str) -> Path:
        assert self.state_dir is not None
        return self.state_dir / "history" / plan_id

    def _fingerprint(self, payload: Any) -> str:
        return f"plan_fingerprint_{_sha256(payload)}"

    def _decision_fingerprint(self, decision: Mapping[str, Any]) -> str:
        payload = {
            key: value
            for key, value in dict(decision).items()
            if key not in {"decision_fingerprint", "fingerprint"}
        }
        return f"planning_decision_fingerprint_{_sha256(payload)}"


def get_current_plan_state(
    plan_id: str,
    *,
    authority_engine: PlanningCurrentAuthorityEngine | None = None,
) -> dict[str, Any]:
    engine = authority_engine or planning_current_authority_engine
    return engine.get_current_plan_state(plan_id)


def get_plan_history(
    plan_id: str,
    *,
    authority_engine: PlanningCurrentAuthorityEngine | None = None,
) -> list[dict[str, Any]]:
    engine = authority_engine or planning_current_authority_engine
    return engine.get_plan_history(plan_id)


def is_plan_current(
    plan: Mapping[str, Any],
    *,
    authority_engine: PlanningCurrentAuthorityEngine | None = None,
) -> dict[str, Any]:
    engine = authority_engine or planning_current_authority_engine
    return engine.is_plan_current(plan)


def _object_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return dict(value) if isinstance(value, Mapping) else {}


def _subject_record(value: PlanningSubject | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, PlanningSubject):
        return value.to_dict()
    record = dict(value) if isinstance(value, Mapping) else {}
    if "plan_id" not in record:
        subject = PlanningSubject(
            objective_refs=tuple(_records_to_strings(record.get("objective_refs"))),
            planning_scope=record.get("planning_scope", "GLOBAL"),
            domain=record.get("domain", "GENERAL"),
            context_class=record.get("context_class", "GENERAL"),
            constraint_domain=record.get("constraint_domain", "GENERAL"),
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
        return [str(value.get("id") or value.get("objective_ref") or value)]
    return [str(item) for item in value or [] if item not in UNKNOWN]


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


planning_current_authority_engine = PlanningCurrentAuthorityEngine()


__all__ = [
    "PlanAssessment",
    "PlanCandidate",
    "PlanLifecycleStatus",
    "PlanningCurrentAuthorityEngine",
    "PlanningSubject",
    "REVIEW_TRIGGERS",
    "get_current_plan_state",
    "get_plan_history",
    "is_plan_current",
    "planning_current_authority_engine",
]
