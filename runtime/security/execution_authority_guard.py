"""High-level execution permission facade."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.security.memory_access_guard import memory_access_guard
from runtime.security.meta_supervisor_guard import meta_supervisor_guard
from runtime.security.permission_manager import permission_manager
from runtime.security.program_safety_guard import program_safety_guard
from runtime.security.runtime_integrity_guard import runtime_integrity_guard
from runtime.security.security_reporter import security_reporter
from runtime.security.self_repair_safety_guard import self_repair_safety_guard
from runtime.security.strategy_safety_guard import strategy_safety_guard


class ExecutionAuthorityGuard:
    def request_permission(
        self,
        action: str,
        runtime_context: Mapping[str, Any] | None = None,
        payload: Mapping[str, Any] | Any | None = None,
    ):
        action = str(action)
        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        meta_decision = meta_supervisor_guard.evaluate(action, context)
        if meta_decision.permission == "DENY":
            return meta_decision

        if action == "execute_program":
            integrity = runtime_integrity_guard.validate_execution(context)
            if integrity.permission == "DENY":
                return integrity
            program = payload if isinstance(payload, Mapping) else context.get("synthesized_program", {})
            return program_safety_guard.evaluate(program, context)
        if action == "reuse_program":
            return program_safety_guard.evaluate(payload if isinstance(payload, Mapping) else {}, context)
        if action == "reuse_strategy":
            return strategy_safety_guard.evaluate(payload or {}, context)
        if action == "repair_runtime":
            return self_repair_safety_guard.evaluate_plan(payload or {})
        if action in {"write_memory", "update_truth_state", "invalidate_cache"}:
            payload = payload if isinstance(payload, Mapping) else {}
            return memory_access_guard.check_access(
                payload.get("memory_layer", "unknown"),
                payload.get("operation", "write"),
                payload,
            )
        if action == "shutdown_runtime":
            return security_reporter.record_decision(
                permission_manager.allow("shutdown_runtime", "shutdown_authorized", "MEDIUM"),
                "runtime",
                dict(context),
            )
        return security_reporter.record_decision(
            permission_manager.allow(action, "action_not_sensitive_or_allowed", "LOW"),
            "runtime",
            dict(context),
        )


execution_authority_guard = ExecutionAuthorityGuard()


__all__ = [
    "ExecutionAuthorityGuard",
    "execution_authority_guard",
]
