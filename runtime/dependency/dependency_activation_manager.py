from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


DEPENDENCY_NOT_REQUIRED = "DEPENDENCY_NOT_REQUIRED"
DEPENDENCY_RECOMMENDED = "DEPENDENCY_RECOMMENDED"
DEPENDENCY_REQUIRED = "DEPENDENCY_REQUIRED"
DEPENDENCY_EXECUTING = "DEPENDENCY_EXECUTING"
DEPENDENCY_COMPLETED = "DEPENDENCY_COMPLETED"


PROCESS_SIGNALS = {
    "process",
    "dependency",
    "chain",
    "causal",
    "cause",
    "multi_step",
    "multi-step",
    "sequence",
    "transformation",
    "hierarchy",
    "hierarchical",
    "state_transition",
    "state transition",
    "gravity",
    "support",
    "unsupported",
    "fall",
    "falling",
    "physics",
    "collision",
    "rest_state",
    "rest state",
    "support_collision",
    "support collision",
    "downward_motion",
    "downward motion",
    "motion",
    "topology",
    "growth",
    "replication",
    "object_count",
    "object count",
    "identity_split",
    "bridge_creation",
    "component_connection",
    "connectivity_change",
    "topology_change",
    "transformation_sequence",
    "propagation",
    "path_finding",
    "path finding",
    "route_completion",
    "route completion",
    "reachability",
    "path_construction",
    "path construction",
    "reachable",
    "best_path",
    "best path",
    "color_mapping",
    "color mapping",
    "color_elimination",
    "color elimination",
    "color_introduction",
    "color introduction",
    "symbolic_remapping",
    "symbolic remapping",
    "mapping_rule",
    "mapping rule",
    "palette",
}


@dataclass(frozen=True)
class DependencyActivationDecision:
    state: str
    required: bool
    recommended: bool
    reason: str
    matched_signals: tuple[str, ...]
    links_loaded: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "system": "dependency_activation_manager",
            "activation_state": self.state,
            "dependency_required": self.required,
            "dependency_recommended": self.recommended,
            "dependency_activation_reason": self.reason,
            "matched_signals": list(self.matched_signals),
            "process_dependency_links_loaded": self.links_loaded,
        }


class DependencyActivationManager:
    """Promotes available dependency memory into runtime execution when needed."""

    def evaluate(
        self,
        context: dict[str, Any] | None = None,
        task_profile: dict[str, Any] | None = None,
        links_loaded: int = 0,
    ) -> dict[str, Any]:
        context = context if isinstance(context, dict) else {}
        task_profile = task_profile if isinstance(task_profile, dict) else {}
        matched = self._matched_signals(context, task_profile)
        requested = self._requested(context)
        enabled = self._enabled(context)

        if requested or enabled:
            decision = DependencyActivationDecision(
                DEPENDENCY_REQUIRED,
                True,
                True,
                "dependency_already_requested_by_runtime",
                tuple(matched),
                int(links_loaded or 0),
            )
        elif links_loaded <= 0:
            decision = DependencyActivationDecision(
                DEPENDENCY_NOT_REQUIRED,
                False,
                False,
                "no_process_dependency_links_loaded",
                tuple(matched),
                0,
            )
        elif matched:
            decision = DependencyActivationDecision(
                DEPENDENCY_REQUIRED,
                True,
                True,
                "structural_process_signals_detected",
                tuple(matched),
                int(links_loaded or 0),
            )
        elif context.get("process_contexts") or context.get("semantic_contexts"):
            decision = DependencyActivationDecision(
                DEPENDENCY_RECOMMENDED,
                False,
                True,
                "contextual_process_memory_available",
                tuple(matched),
                int(links_loaded or 0),
            )
        else:
            decision = DependencyActivationDecision(
                DEPENDENCY_NOT_REQUIRED,
                False,
                False,
                "no_dependency_trigger_detected",
                tuple(matched),
                int(links_loaded or 0),
            )
        return decision.as_dict()

    def promote_request(
        self,
        context: dict[str, Any],
        decision: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(context, dict):
            context = {}
        if decision.get("activation_state") not in {
            DEPENDENCY_REQUIRED,
            DEPENDENCY_RECOMMENDED,
        }:
            return context
        context["runtime_tool_requests"] = {
            **context.get("runtime_tool_requests", {}),
            "dependency_reasoning": {
                "request_state": "REQUESTED",
                "requested_by": "dependency_activation_manager",
                "tool_name": "dependency_reasoning",
                "activation_state": decision.get("activation_state"),
                "reason": decision.get("dependency_activation_reason"),
                "matched_signals": list(decision.get("matched_signals", [])),
            },
        }
        context["enabled_tools"] = sorted(
            set(context.get("enabled_tools", []) or [])
            | {"dependency_reasoning"}
        )
        context["dependency_activation_reason"] = (
            decision.get("dependency_activation_reason")
        )
        return context

    def _requested(self, context: dict[str, Any]) -> bool:
        requests = context.get("runtime_tool_requests", {})
        request = (
            requests.get("dependency_reasoning", {})
            if isinstance(requests, dict)
            else {}
        )
        return request.get("request_state") == "REQUESTED"

    def _enabled(self, context: dict[str, Any]) -> bool:
        enabled = set(context.get("enabled_tools", []) or [])
        report = context.get("tool_selection_report", {})
        if isinstance(report, dict):
            enabled.update(report.get("enabled_tools", []) or [])
        return "dependency_reasoning" in enabled

    def _matched_signals(
        self,
        context: dict[str, Any],
        task_profile: dict[str, Any],
    ) -> list[str]:
        payload = " ".join(
            str(value)
            for value in [
                context.get("process_note"),
                context.get("task_id"),
                context.get("task_profile"),
                context.get("pre_reasoning_task_profile"),
                context.get("semantic_abstractions"),
                context.get("semantic_attribution_report"),
                context.get("introspection_report"),
                context.get("epistemic_hypotheses"),
                context.get("process_contexts"),
                context.get("generated_contexts"),
                task_profile,
            ]
            if value not in (None, "")
        ).lower()
        tokens = set(re.findall(r"[a-z_ -]+", payload))
        matched = []
        for signal in sorted(PROCESS_SIGNALS):
            if signal in payload or signal in tokens:
                matched.append(signal)
        capabilities = set(task_profile.get("required_capabilities", []) or [])
        capabilities.update(context.get("required_capabilities", []) or [])
        if "dependency_reasoning" in capabilities:
            matched.append("dependency_reasoning")
        return sorted(set(matched))


dependency_activation_manager = DependencyActivationManager()


__all__ = [
    "DEPENDENCY_COMPLETED",
    "DEPENDENCY_EXECUTING",
    "DEPENDENCY_NOT_REQUIRED",
    "DEPENDENCY_RECOMMENDED",
    "DEPENDENCY_REQUIRED",
    "DependencyActivationManager",
    "dependency_activation_manager",
]
