"""Runtime Intent entry orchestration without authority ownership."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.intent.current_intent_authority import (
    IntentCurrentAuthorityEngine,
    IntentLifecycleStatus,
    IntentSubject,
)


DIAGNOSTIC_OBJECTIVES = {
    "COMPLETED",
    "NOT_APPLICABLE",
    "NOT_DEFINED",
    "REACHABILITY_CLEAR",
    "ACTIVE",
    "AUTHORIZE",
    "BYPASS_ASSESSMENT",
    "BYPASS_AUTHORITY",
    "UNKNOWN",
    "NONE",
    "NULL",
}


@dataclass(frozen=True)
class IntentOrchestrationResult:
    run_id: str | None
    task_id: str | None
    objective_ref: str | None
    objective_type: str
    source: str | None
    intent_id: str | None
    intent_proposal_id: str | None
    assessment_id: str | None
    assessment_state: str | None
    intent_decision_id: str | None
    intent_status: str | None
    orchestration_state: str
    reason: str
    authority_source: str
    timestamp: str
    telemetry: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IntentManager:
    """Routes runtime objectives into the governed Intent authority pipeline."""

    system_name = "intent_manager"
    authority = "NONE"
    behavioral_authority = "NONE"

    def __init__(
        self,
        *,
        authority_engine: IntentCurrentAuthorityEngine | None = None,
    ) -> None:
        self.authority_engine = authority_engine or IntentCurrentAuthorityEngine()

    def orchestrate_runtime_objective(
        self,
        objective: Any,
        *,
        run_id: str | None = None,
        task_id: str | None = None,
        source_component: str = "runtime_objective_entry",
        source_type: str = "TASK_DERIVED",
        task_local: bool = True,
        objective_ref: str | None = None,
    ) -> IntentOrchestrationResult:
        timestamp = str(datetime.utcnow())
        telemetry = self._telemetry(
            runtime_intent_entry_reached=True,
            intent_proposal_created=False,
            intent_assessment_reached=False,
            intent_authority_reached=False,
            intent_activation_result="NOT_EVALUATED",
        )
        eligibility = self._eligible_objective(objective)
        if not eligibility["eligible"]:
            return IntentOrchestrationResult(
                run_id=run_id,
                task_id=task_id,
                objective_ref=objective_ref or eligibility["objective_ref"],
                objective_type=source_type,
                source=None,
                intent_id=None,
                intent_proposal_id=None,
                assessment_id=None,
                assessment_state=None,
                intent_decision_id=None,
                intent_status=None,
                orchestration_state="NO_INTENT_PROPOSAL",
                reason=eligibility["reason"],
                authority_source=self.authority_engine.system_name,
                timestamp=timestamp,
                telemetry=telemetry,
            )

        source = self._classify_source(source_type)
        subject = self._subject_from_objective(
            eligibility["objective_ref"],
            source_type=source_type,
            source=source,
            task_local=task_local,
        )
        current_state = self.authority_engine.get_current_intent_state(
            subject.intent_id
        )
        if current_state.get("lifecycle_status") == IntentLifecycleStatus.ACTIVE.value:
            return IntentOrchestrationResult(
                run_id=run_id,
                task_id=task_id,
                objective_ref=objective_ref or eligibility["objective_ref"],
                objective_type=source_type,
                source=source,
                intent_id=subject.intent_id,
                intent_proposal_id=None,
                assessment_id=None,
                assessment_state=None,
                intent_decision_id=current_state.get("current_intent_decision_id"),
                intent_status=IntentLifecycleStatus.ACTIVE.value,
                orchestration_state="CURRENT_INTENT_ALREADY_ACTIVE",
                reason="current_active_intent_reused",
                authority_source=self.authority_engine.system_name,
                timestamp=timestamp,
                telemetry={
                    **telemetry,
                    "intent_activation_result": "CURRENT_INTENT_ALREADY_ACTIVE",
                },
            )
        if current_state:
            return IntentOrchestrationResult(
                run_id=run_id,
                task_id=task_id,
                objective_ref=objective_ref or eligibility["objective_ref"],
                objective_type=source_type,
                source=source,
                intent_id=subject.intent_id,
                intent_proposal_id=None,
                assessment_id=None,
                assessment_state=None,
                intent_decision_id=current_state.get("current_intent_decision_id"),
                intent_status=current_state.get("lifecycle_status"),
                orchestration_state="NONCURRENT_INTENT_EXISTS",
                reason="noncurrent_intent_not_auto_reactivated",
                authority_source=self.authority_engine.system_name,
                timestamp=timestamp,
                telemetry={
                    **telemetry,
                    "intent_activation_result": "NONCURRENT_INTENT_EXISTS",
                },
            )

        proposal = self.authority_engine.create_proposal(
            subject,
            source=source,
            provenance={
                "origin": "runtime_objective",
                "run_id": run_id,
                "task_id": task_id,
                "objective_ref": objective_ref or eligibility["objective_ref"],
                "source_component": source_component,
                "source_type": source_type,
            },
            proposal_context={
                "run_id": run_id,
                "task_id": task_id,
                "objective_ref": objective_ref or eligibility["objective_ref"],
            },
        )
        telemetry = {
            **telemetry,
            "intent_proposal_created": True,
            "proposal_authority": proposal.authority,
        }
        assessment = self.authority_engine.assess_proposal(proposal, subject)
        telemetry = {**telemetry, "intent_assessment_reached": True}
        if not assessment.intent_authority_predicate_satisfied:
            return IntentOrchestrationResult(
                run_id=run_id,
                task_id=task_id,
                objective_ref=objective_ref or eligibility["objective_ref"],
                objective_type=source_type,
                source=source,
                intent_id=proposal.intent_id,
                intent_proposal_id=proposal.intent_proposal_id,
                assessment_id=assessment.intent_assessment_id,
                assessment_state=assessment.assessment_state,
                intent_decision_id=None,
                intent_status=None,
                orchestration_state="INTENT_ASSESSMENT_DENIED",
                reason=";".join(assessment.failures) or "assessment_denied",
                authority_source=self.authority_engine.system_name,
                timestamp=timestamp,
                telemetry={
                    **telemetry,
                    "intent_activation_result": "ASSESSMENT_DENIED",
                },
            )

        decision = self.authority_engine.commit_intent(subject, proposal, assessment)
        state = self.authority_engine.current_state_from_decision({}, decision)
        persistence = self.authority_engine.persist_current_state(
            state,
            lifecycle_decision=decision,
            proposal=proposal.to_dict(),
            assessment=assessment.to_dict(),
        )
        return IntentOrchestrationResult(
            run_id=run_id,
            task_id=task_id,
            objective_ref=objective_ref or eligibility["objective_ref"],
            objective_type=source_type,
            source=source,
            intent_id=proposal.intent_id,
            intent_proposal_id=proposal.intent_proposal_id,
            assessment_id=assessment.intent_assessment_id,
            assessment_state=assessment.assessment_state,
            intent_decision_id=decision.get("intent_decision_id"),
            intent_status=state.get("lifecycle_status"),
            orchestration_state="INTENT_OPERATIONAL_ENTRY_ESTABLISHED",
            reason=persistence.get("persistence_state", "intent_authority_committed"),
            authority_source=self.authority_engine.system_name,
            timestamp=timestamp,
            telemetry={
                **telemetry,
                "intent_authority_reached": True,
                "intent_activation_result": state.get("lifecycle_status"),
                "persistence_state": persistence.get("persistence_state"),
            },
        )

    def _subject_from_objective(
        self,
        objective_ref: str,
        *,
        source_type: str,
        source: str,
        task_local: bool,
    ) -> IntentSubject:
        scope = "TASK_LOCAL" if task_local else "GLOBAL"
        return self.authority_engine.create_subject(
            intent_type="runtime_objective",
            purpose=objective_ref,
            directional_target="governed_task_execution",
            scope=scope,
            domain="GENERAL",
            context_class="adaptive_runtime",
            constraint_domain="runtime_governance",
            authority_origin=source,
        )

    def _eligible_objective(self, objective: Any) -> dict[str, Any]:
        if objective is None:
            return {"eligible": False, "reason": "OBJECTIVE_MISSING", "objective_ref": None}
        if isinstance(objective, Mapping):
            value = (
                objective.get("objective")
                or objective.get("task_id")
                or objective.get("task_file")
                or objective.get("purpose")
            )
        else:
            value = objective
        objective_ref = str(value or "").strip()
        if not objective_ref:
            return {"eligible": False, "reason": "OBJECTIVE_EMPTY", "objective_ref": objective_ref}
        if objective_ref.upper() in DIAGNOSTIC_OBJECTIVES:
            return {
                "eligible": False,
                "reason": "DIAGNOSTIC_OBJECTIVE_REJECTED",
                "objective_ref": objective_ref,
            }
        lowered = objective_ref.lower()
        if lowered.endswith((".receipt.json", ".jsonl")) or "runtime/artifacts/" in lowered:
            return {
                "eligible": False,
                "reason": "ARTIFACT_OBJECTIVE_REJECTED",
                "objective_ref": objective_ref,
            }
        if lowered.startswith(("report:", "telemetry:", "status:")):
            return {
                "eligible": False,
                "reason": "DIAGNOSTIC_OBJECTIVE_REJECTED",
                "objective_ref": objective_ref,
            }
        return {"eligible": True, "reason": "OBJECTIVE_ELIGIBLE", "objective_ref": objective_ref}

    def _classify_source(self, source_type: str) -> str:
        normalized = str(source_type or "").upper()
        if normalized == "USER_TASK_OBJECTIVE":
            return "USER_DIRECTED"
        if normalized in {"TRAINING_OBJECTIVE", "TRAINING_PROPOSED"}:
            return "TRAINING_PROPOSED"
        if normalized in {"REPAIR_OBJECTIVE", "REPAIR_PROPOSED"}:
            return "REPAIR_PROPOSED"
        if normalized in {"SELF_IMPROVEMENT", "SELF_IMPROVEMENT_PROPOSED"}:
            return "SELF_IMPROVEMENT_PROPOSED"
        if normalized in {"SYSTEM_MAINTENANCE", "RUNTIME_MAINTENANCE"}:
            return "SYSTEM_MAINTENANCE"
        return "PLANNING_DERIVED"

    def _telemetry(self, **values: Any) -> dict[str, Any]:
        return {
            "runtime_intent_entry_reached": False,
            "intent_proposal_created": False,
            "intent_assessment_reached": False,
            "intent_authority_reached": False,
            "intent_activation_result": "NOT_EVALUATED",
            "goal_activation": False,
            "plan_activation": False,
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "capability_authority": "NONE",
            **values,
        }


def build_runtime_objective_ref(task_file: Any) -> str:
    task_name = Path(str(task_file)).name
    return f"governed_task_execution:{task_name}"
