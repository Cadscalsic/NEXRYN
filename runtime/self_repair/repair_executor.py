"""Execute only safe operational repairs."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any

from runtime.self_repair.repair_memory import RepairMemory
from runtime.self_repair.repair_planner import RepairPlan
from runtime.self_repair.rollback_manager import RollbackManager
from runtime.security import self_repair_safety_guard


ALLOWED_EXECUTABLE_ACTIONS = {
    "SET_SHUTDOWN_FAST",
    "MARK_EPISODE_COMPLETED",
    "STOP_BACKGROUND_LOOPS",
    "SYNC_SUCCESS_FLAGS",
    "SYNC_RECOMMENDED_NEXT_STEP",
    "INVALIDATE_TEMP_CACHE",
    "REQUEST_GOVERNANCE_REVIEW",
    "WRITE_REPAIR_MEMORY",
}


@dataclass
class RepairExecutionResult:
    repair_id: str
    anomaly_type: str
    severity: str
    actions_attempted: list[str] = field(default_factory=list)
    actions_executed: list[str] = field(default_factory=list)
    skipped_actions: list[str] = field(default_factory=list)
    success: bool = False
    rollback_used: bool = False
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RepairExecutor:
    def __init__(
        self,
        rollback_manager: RollbackManager,
        repair_memory: RepairMemory,
    ):
        self.rollback_manager = rollback_manager
        self.repair_memory = repair_memory

    def execute(
        self,
        runtime_context: dict[str, Any],
        plan: RepairPlan,
    ) -> tuple[dict[str, Any], RepairExecutionResult]:
        context = dict(runtime_context or {})
        result = RepairExecutionResult(
            repair_id=plan.repair_id,
            anomaly_type=plan.anomaly_type,
            severity=plan.severity,
            actions_attempted=list(plan.actions),
        )

        security_decision = self_repair_safety_guard.evaluate_plan(plan)
        if security_decision.permission == "DENY":
            result.reason = security_decision.reason
            result.skipped_actions = list(plan.actions)
            if security_decision.requires_governance_review:
                context["governance_review_requested"] = True
                context.setdefault("governance_review_reasons", []).append(
                    plan.anomaly_type
                )
            self._write_memory(plan, result)
            return context, result

        if self.repair_memory.loop_risk(plan.anomaly_type):
            result.reason = "repair_loop_risk_detected"
            result.skipped_actions = list(plan.actions)
            return context, result

        if not plan.safe_to_execute:
            result.reason = (
                "critical_or_governance_review_required"
                if plan.severity == "CRITICAL"
                else "repair_not_marked_safe"
            )
            result.skipped_actions = list(plan.actions)
            if plan.requires_governance_review:
                context["governance_review_requested"] = True
                context.setdefault("governance_review_reasons", []).append(
                    plan.anomaly_type
                )
            self._write_memory(plan, result)
            return context, result

        self.rollback_manager.snapshot(plan.repair_id, context)
        try:
            for action in plan.actions:
                if action not in ALLOWED_EXECUTABLE_ACTIONS:
                    result.skipped_actions.append(action)
                    continue
                if action == "WRITE_REPAIR_MEMORY":
                    continue
                self._apply_action(context, action, plan)
                result.actions_executed.append(action)
            result.success = True
            result.reason = "repair_executed"
        except Exception as error:
            restored = self.rollback_manager.restore(
                plan.repair_id,
                str(error),
            )
            context = restored
            result.rollback_used = True
            result.reason = "repair_failed_rollback_used"
            result.success = False

        self._write_memory(plan, result)
        return context, result

    def _apply_action(
        self,
        context: dict[str, Any],
        action: str,
        plan: RepairPlan,
    ) -> None:
        if action == "SET_SHUTDOWN_FAST":
            context["shutdown_mode"] = "fast"
            shutdown = dict(context.get("post_success_shutdown") or {})
            shutdown["enabled"] = True
            shutdown["mode"] = "fast"
            context["post_success_shutdown"] = shutdown
        elif action == "MARK_EPISODE_COMPLETED":
            context["episode_completed"] = True
            evaluation = dict(context.get("evaluation_result") or {})
            evaluation["episode_completed"] = True
            context["evaluation_result"] = evaluation
        elif action == "STOP_BACKGROUND_LOOPS":
            context["background_loops_active"] = False
            context["self_improvement_skipped"] = True
            context["strategy_evolution_skipped"] = True
            context["curiosity_expansion_skipped"] = True
        elif action == "SYNC_SUCCESS_FLAGS":
            success_state = self._canonical_success_state(context)
            context["success_state"] = success_state
            evaluation = dict(context.get("evaluation_result") or {})
            evaluation["success_state"] = success_state
            context["evaluation_result"] = evaluation
        elif action == "SYNC_RECOMMENDED_NEXT_STEP":
            context["recommended_next_step"] = "freeze_concept"
            learning = dict(context.get("learning_saturation_report") or {})
            learning["recommended_next_step"] = "freeze_concept"
            learning["enable_adaptive_training"] = False
            context["learning_saturation_report"] = learning
        elif action == "INVALIDATE_TEMP_CACHE":
            context["temporary_cache_invalidated"] = True
            context["cache_invalidation_reason"] = plan.anomaly_type
        elif action == "REQUEST_GOVERNANCE_REVIEW":
            context["governance_review_requested"] = True
            context.setdefault("governance_review_reasons", []).append(
                plan.anomaly_type
            )

    def _canonical_success_state(self, context: dict[str, Any]) -> str:
        evaluation = context.get("evaluation_result") or {}
        if evaluation.get("exact_success") is True:
            return "EXACT_SUCCESS"
        return (
            evaluation.get("success_state")
            or context.get("success_state")
            or "UNKNOWN"
        )

    def _write_memory(
        self,
        plan: RepairPlan,
        result: RepairExecutionResult,
    ) -> None:
        self.repair_memory.record(
            anomaly_type=plan.anomaly_type,
            severity=plan.severity,
            repair_actions=plan.actions,
            success=result.success,
            rollback_used=result.rollback_used,
        )


__all__ = [
    "ALLOWED_EXECUTABLE_ACTIONS",
    "RepairExecutionResult",
    "RepairExecutor",
]
