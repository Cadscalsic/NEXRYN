from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass
class ResidualEvidence:
    residual_difference_count: int
    residual_locations: list[Any]
    residual_type: str
    probable_root_cause: str
    future_learning_priority: str
    prediction_accuracy: float
    structural_score: float
    color_similarity: float
    source_execution_id: str
    source_candidate_id: str
    task_id: str
    run_id: str
    validation_state: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RecoverabilityGate:
    """Admit only actionable recoverable failures into governed repair."""

    def build_residual_evidence(
        self,
        evaluation_result: Mapping[str, Any] | None,
        residual_analysis: Mapping[str, Any] | None,
        execution_state: Mapping[str, Any] | None = None,
        task_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        evaluation = evaluation_result if isinstance(evaluation_result, Mapping) else {}
        residual = residual_analysis if isinstance(residual_analysis, Mapping) else {}
        state = execution_state if isinstance(execution_state, Mapping) else {}
        context = task_context if isinstance(task_context, Mapping) else {}

        count = _integer(
            residual.get(
                "residual_difference_count",
                evaluation.get("difference_count", evaluation.get("residual_difference_count", 0)),
            ),
            0,
        )
        locations = residual.get("residual_locations")
        locations = list(locations) if isinstance(locations, list) else []
        residual_type = str(residual.get("residual_type") or "none")
        evidence = ResidualEvidence(
            residual_difference_count=count,
            residual_locations=locations,
            residual_type=residual_type,
            probable_root_cause=str(residual.get("probable_root_cause") or "none"),
            future_learning_priority=str(residual.get("future_learning_priority") or "none"),
            prediction_accuracy=_number(
                evaluation.get("prediction_accuracy", evaluation.get("accuracy", 0.0)),
            ),
            structural_score=_number(
                evaluation.get("structural_score", evaluation.get("accuracy", 0.0)),
            ),
            color_similarity=_number(
                evaluation.get("color_similarity", 1.0 if count == 0 else 0.0),
            ),
            source_execution_id=str(
                state.get("execution_id")
                or context.get("execution_id")
                or context.get("run_id")
                or "current_execution"
            ),
            source_candidate_id=str(
                state.get("candidate_id")
                or context.get("candidate_id")
                or context.get("selected_candidate_id")
                or "current_candidate"
            ),
            task_id=str(context.get("task_id") or context.get("task_path") or "current_task"),
            run_id=str(context.get("run_id") or state.get("run_id") or "current_run"),
            validation_state="RESIDUAL_EVIDENCE_NOT_APPLICABLE",
        )
        data = evidence.to_dict()
        data["validation_state"] = self.validate_residual_evidence(data)
        return data

    def validate_residual_evidence(self, residual_evidence: Mapping[str, Any] | None) -> str:
        evidence = residual_evidence if isinstance(residual_evidence, Mapping) else {}
        count = _integer(evidence.get("residual_difference_count"), 0)
        residual_type = str(evidence.get("residual_type") or "none")
        locations = evidence.get("residual_locations")
        locations_present = isinstance(locations, list) and len(locations) > 0
        if count <= 0 and residual_type in {"none", "exact_success"}:
            return "RESIDUAL_EVIDENCE_NOT_APPLICABLE"
        if count > 0 and not residual_type:
            return "RESIDUAL_EVIDENCE_INCOMPLETE"
        if count > 0 and locations_present and len(locations) > count:
            return "RESIDUAL_EVIDENCE_CONFLICTED"
        if residual_type == "localized_color_residual" and count > 0 and locations_present:
            return "RESIDUAL_EVIDENCE_VALID"
        if count > 0 and residual_type not in {"none", "unknown_residual"}:
            return "RESIDUAL_EVIDENCE_VALID" if locations_present else "RESIDUAL_EVIDENCE_INCOMPLETE"
        return "RESIDUAL_EVIDENCE_INCOMPLETE"

    def evaluate(
        self,
        *,
        evaluation_result: Mapping[str, Any] | None,
        residual_analysis: Mapping[str, Any] | None,
        execution_state: Mapping[str, Any] | None = None,
        retry_budget: Mapping[str, Any] | None = None,
        governance_state: Mapping[str, Any] | None = None,
        task_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        evaluation = evaluation_result if isinstance(evaluation_result, Mapping) else {}
        context = task_context if isinstance(task_context, Mapping) else {}
        governance = governance_state if isinstance(governance_state, Mapping) else {}
        budget = retry_budget if isinstance(retry_budget, Mapping) else {}
        evidence = self.build_residual_evidence(
            evaluation,
            residual_analysis,
            execution_state,
            context,
        )

        success_state = str(evaluation.get("success_state") or "")
        retry_allowed = evaluation.get("retry_allowed", context.get("retry_allowed")) is True
        episode_completed = evaluation.get("episode_completed", context.get("episode_completed")) is True
        remaining = self._remaining_repair_budget(budget, context)
        governance_blocked = self._governance_blocked(governance, context)
        evidence_valid = evidence["validation_state"] == "RESIDUAL_EVIDENCE_VALID"

        state = "NOT_APPLICABLE"
        reason = "repair_not_applicable"
        required = False
        allowed = False
        blocked = False
        if success_state in {"SUCCESS", "EXACT_SUCCESS", "SUCCESS_WITH_RESIDUALS", "LEARNING_PROGRESS"}:
            state = "NOT_APPLICABLE"
            reason = "terminal_or_exact_success"
        elif success_state in {"CRITICAL_FAILURE", "UNRECOVERABLE_FAILURE", "INVALID_TASK"}:
            state = "BLOCKED"
            reason = "unrecoverable_or_invalid_failure"
            blocked = True
        elif governance_blocked:
            state = "BLOCKED"
            reason = "critical_governance_block"
            blocked = True
        elif not retry_allowed:
            state = "BLOCKED"
            reason = "retry_not_allowed"
            blocked = True
        elif remaining <= 0:
            state = "DEFERRED"
            reason = "repair_budget_exhausted"
        elif success_state == "RECOVERABLE_FAILURE" and not episode_completed:
            if evidence_valid and evidence["residual_difference_count"] > 0:
                state = "REPAIR_REQUIRED"
                reason = "recoverable_failure_with_actionable_residual"
                required = True
                allowed = True
            else:
                state = "BLOCKED"
                reason = "residual_evidence_not_actionable"
                blocked = True

        return {
            "repair_admission_state": state,
            "repair_required": required,
            "repair_allowed": allowed,
            "repair_blocked": blocked,
            "repair_reason": reason,
            "remaining_repair_budget": remaining,
            "recommended_repair_family": self._recommended_family(evidence),
            "residual_evidence": evidence,
        }

    def _remaining_repair_budget(self, budget: Mapping[str, Any], context: Mapping[str, Any]) -> int:
        max_attempts = _integer(
            budget.get(
                "MAX_REPAIR_ATTEMPTS_PER_TASK",
                budget.get(
                    "max_repair_attempts_per_task",
                    context.get("MAX_REPAIR_ATTEMPTS_PER_TASK", 3),
                ),
            ),
            3,
        )
        used = _integer(budget.get("repair_attempts", context.get("repair_attempts", 0)), 0)
        return max(0, max_attempts - used)

    def _governance_blocked(self, governance: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
        if governance.get("critical_governance_block") is True:
            return True
        if governance.get("governance_state") in {"BLOCKED", "CRITICAL_BLOCK"}:
            return True
        return context.get("critical_governance_block") is True

    def _recommended_family(self, evidence: Mapping[str, Any]) -> str | None:
        if evidence.get("residual_type") == "localized_color_residual":
            return "localized_repair"
        return None


def _integer(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


recoverability_gate = RecoverabilityGate()


__all__ = ["RecoverabilityGate", "ResidualEvidence", "recoverability_gate"]
