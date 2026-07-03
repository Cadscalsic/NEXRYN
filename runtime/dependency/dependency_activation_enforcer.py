from __future__ import annotations

from typing import Any, Iterable

from runtime.dependency.dependency_activation_trace import (
    DependencyActivationTrace,
)


MANDATORY_DEPENDENCY_CONCEPTS = {
    "gravity",
    "path_finding",
    "route_completion",
    "bridge_creation",
    "component_connection",
    "transformation_sequence",
    "multi_step_reasoning",
}


class DependencyActivationEnforcer:
    """Ensures dependency concepts cannot bypass activation silently."""

    system_name = "dependency_activation_enforcer"

    def enforce(
        self,
        concepts: Iterable[Any],
        runtime_context: dict[str, Any] | None = None,
        trace: DependencyActivationTrace | None = None,
        requested_tool: str = "dependency_reasoning",
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, dict) else {}
        trace = trace or DependencyActivationTrace()
        normalized = [_normalize(concept) for concept in concepts or []]
        matched = sorted(
            {
                concept
                for concept in normalized
                if concept in MANDATORY_DEPENDENCY_CONCEPTS
            }
        )
        trace.detect_concepts(normalized)
        trace.set_dependency_candidates(matched)

        existing_requests = runtime_context.get("runtime_tool_requests", {})
        existing_request = (
            existing_requests.get(requested_tool, {})
            if isinstance(existing_requests, dict)
            else {}
        )
        enabled_tools = set(runtime_context.get("enabled_tools", []) or [])
        tool_selection_report = runtime_context.get("tool_selection_report", {})
        if isinstance(tool_selection_report, dict):
            enabled_tools.update(tool_selection_report.get("enabled_tools", []) or [])
            enabled_tools.update(tool_selection_report.get("selected_tools", []) or [])

        already_requested = (
            existing_request.get("request_state") == "REQUESTED"
            or requested_tool in enabled_tools
        )
        request_generated = False
        reason = None
        if matched and not already_requested:
            reason = "mandatory_dependency_concept_detected:" + ",".join(matched)
            request = trace.request(
                requested_tool=requested_tool,
                requested_by=self.system_name,
                reason=reason,
                concepts=matched,
            )
            runtime_context["runtime_tool_requests"] = {
                **(
                    existing_requests
                    if isinstance(existing_requests, dict)
                    else {}
                ),
                requested_tool: {
                    "tool_name": requested_tool,
                    "request_state": "REQUESTED",
                    "requested_by": self.system_name,
                    "activation_state": "DEPENDENCY_REQUIRED",
                    "reason": reason,
                    "matched_signals": matched,
                    "trace_request": request,
                },
            }
            runtime_context["enabled_tools"] = sorted(enabled_tools | {requested_tool})
            runtime_context["dependency_activation_reason"] = reason
            request_generated = True
        elif matched:
            reason = (
                existing_request.get("reason")
                or runtime_context.get("dependency_activation_reason")
                or "dependency_request_already_present"
            )
            trace.request(
                requested_tool=requested_tool,
                requested_by=self.system_name,
                reason=reason,
                concepts=matched,
            )
            trace.approve(
                requested_tool=requested_tool,
                approved_by=self.system_name,
                reason="existing_request_or_enabled_tool",
            )

        return {
            "system": self.system_name,
            "mandatory_concepts": sorted(MANDATORY_DEPENDENCY_CONCEPTS),
            "matched_concepts": matched,
            "activation_required": bool(matched),
            "activation_request_generated": request_generated,
            "activation_already_requested": already_requested,
            "requested_tool": requested_tool,
            "activation_reason": reason,
            "runtime_context": runtime_context,
            "trace": trace,
        }


def _normalize(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


dependency_activation_enforcer = DependencyActivationEnforcer()


__all__ = [
    "MANDATORY_DEPENDENCY_CONCEPTS",
    "DependencyActivationEnforcer",
    "dependency_activation_enforcer",
]
