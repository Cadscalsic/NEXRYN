"""Runtime execution integrity authority."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.security.permission_manager import permission_manager, SecurityDecision
from runtime.security.security_reporter import security_reporter


class RuntimeIntegrityGuard:
    def validate_execution(
        self,
        runtime_context: Mapping[str, Any] | None,
    ) -> SecurityDecision:
        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        execution = self._first_mapping(
            context,
            "execution_report",
            "execution_integrity_report",
            "transformation_report",
        )
        planned_ops = execution.get("planned_ops")
        executed_ops = execution.get("executed_ops")
        if planned_ops is not None and executed_ops is not None and planned_ops != executed_ops:
            decision = permission_manager.deny(
                "execute_program",
                "EXECUTION_INTEGRITY_VIOLATION",
                "CRITICAL",
                notes=["planned_ops_mismatch"],
            )
            security_reporter.record_integrity_violation(
                "EXECUTION_INTEGRITY_VIOLATION",
                {"planned_ops": planned_ops, "executed_ops": executed_ops},
            )
            return security_reporter.record_decision(decision, "program", dict(execution))

        if execution.get("execution_authorized") is False:
            decision = permission_manager.deny(
                "execute_program",
                "execution_not_authorized",
                "HIGH",
            )
            return security_reporter.record_decision(decision, "program", dict(execution))

        plan_id = execution.get("execution_plan_id")
        current_plan_id = context.get("execution_plan_id")
        if plan_id and current_plan_id and plan_id != current_plan_id:
            decision = permission_manager.deny(
                "execute_program",
                "EXECUTION_INTEGRITY_VIOLATION",
                "CRITICAL",
                notes=["execution_plan_id_changed"],
            )
            security_reporter.record_integrity_violation(
                "EXECUTION_INTEGRITY_VIOLATION",
                {"execution_plan_id": plan_id, "current_execution_plan_id": current_plan_id},
            )
            return security_reporter.record_decision(decision, "program", dict(execution))

        if context.get("runtime_state_corrupted") is True:
            decision = permission_manager.deny(
                "modify_runtime_state",
                "runtime_state_corruption_detected",
                "CRITICAL",
            )
            return security_reporter.record_decision(decision, "runtime", dict(context))

        if (
            context.get("episode_completed") is True
            and context.get("episode_completed_overridden") is True
        ):
            decision = permission_manager.deny(
                "modify_runtime_state",
                "episode_completed_override_blocked",
                "HIGH",
            )
            return security_reporter.record_decision(decision, "runtime", dict(context))

        return security_reporter.record_decision(
            permission_manager.allow("execute_program", "execution_integrity_preserved", "HIGH"),
            "program",
            dict(execution),
        )

    def _first_mapping(self, context, *keys):
        for key in keys:
            value = context.get(key)
            if isinstance(value, Mapping) and value:
                return value
        return {}


runtime_integrity_guard = RuntimeIntegrityGuard()


__all__ = [
    "RuntimeIntegrityGuard",
    "runtime_integrity_guard",
]
