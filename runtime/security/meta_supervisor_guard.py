"""Guard downstream compliance with Meta Supervisor directives."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.security.permission_manager import permission_manager
from runtime.security.security_reporter import security_reporter


class MetaSupervisorGuard:
    STOPPED_ACTIONS = {
        "reasoning",
        "deep_reasoning",
        "program_synthesis",
        "strategy_search",
        "context_discovery",
        "governance_revalidation",
        "self_improvement",
    }

    def evaluate(
        self,
        requested_action: str,
        runtime_context: Mapping[str, Any] | None,
    ):
        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        directive = context.get("cognitive_directive") or {}
        if not isinstance(directive, Mapping):
            directive = {}
        selected_action = directive.get("action")
        requested_action = str(requested_action)
        if selected_action == "STOP_COGNITION" and requested_action in self.STOPPED_ACTIONS:
            decision = permission_manager.deny(
                requested_action,
                "meta_supervisor_stop_cognition_enforced",
                "HIGH",
            )
            return security_reporter.record_decision(decision, "meta_supervisor", dict(directive))

        if selected_action == "REUSE_EXECUTABLE_PROGRAM" and requested_action in {
            "program_synthesis",
            "strategy_search",
            "deep_reasoning",
        }:
            decision = permission_manager.deny(
                requested_action,
                "meta_supervisor_program_reuse_enforced",
                "MEDIUM",
            )
            return security_reporter.record_decision(decision, "meta_supervisor", dict(directive))

        if selected_action == "REUSE_KNOWN_STRATEGY" and requested_action in {
            "strategy_search",
            "hypothesis_expansion",
        }:
            decision = permission_manager.deny(
                requested_action,
                "meta_supervisor_strategy_reuse_enforced",
                "MEDIUM",
            )
            return security_reporter.record_decision(decision, "meta_supervisor", dict(directive))

        return security_reporter.record_decision(
            permission_manager.allow(requested_action, "meta_supervisor_directive_compliant", "LOW"),
            "meta_supervisor",
            dict(directive),
        )


meta_supervisor_guard = MetaSupervisorGuard()


__all__ = [
    "MetaSupervisorGuard",
    "meta_supervisor_guard",
]
