"""Route semantic concepts and selected tools into execution intents."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


class SemanticIntentRouter:
    """Create explicit execution intents from semantic and tool-selection signals."""

    system_name = "semantic_intent_router"

    INTENT_RULES = [
        {
            "intent": "rotation_reflection",
            "concepts": {"rotation_reflection", "rotation", "reflection", "orientation_change"},
            "tools": {"rotation_execution", "reflection_execution"},
            "operation_family": "geometric_transform",
            "operation": "rotate_or_reflect",
            "confidence": 0.92,
        },
        {
            "intent": "rotation",
            "concepts": {"rotation", "orientation_change"},
            "tools": {"rotation_execution"},
            "operation_family": "geometric_transform",
            "operation": "rotate",
            "confidence": 0.90,
        },
        {
            "intent": "reflection",
            "concepts": {"reflection", "symmetry_creation", "rotation_reflection"},
            "tools": {"reflection_execution"},
            "operation_family": "geometric_transform",
            "operation": "reflect",
            "confidence": 0.88,
        },
        {
            "intent": "scaling",
            "concepts": {"scaling", "scale_transformation", "size_transformation"},
            "tools": {"scaling_execution"},
            "operation_family": "scale_transform",
            "operation": "scale",
            "confidence": 0.88,
        },
        {
            "intent": "path_construction",
            "concepts": {
                "path_finding",
                "route_completion",
                "path_construction",
                "bridge_creation",
                "component_connection",
                "connectivity_change",
            },
            "tools": {"path_execution"},
            "operation_family": "path_transform",
            "operation": "construct_path",
            "confidence": 0.88,
        },
        {
            "intent": "component_connection",
            "concepts": {
                "bridge_creation",
                "component_connection",
                "connectivity_change",
                "topology_change",
            },
            "tools": {"semantic_to_transformation_compiler", "transformation_execution"},
            "operation_family": "topology_transform",
            "operation": "connect_components",
            "confidence": 0.91,
        },
        {
            "intent": "topology_repair",
            "concepts": {
                "hole_removal",
                "topology_repair",
                "connectivity_restoration",
                "topology_change",
                "connectivity_change",
            },
            "tools": {"transformation_execution"},
            "operation_family": "topology_transform",
            "operation": "repair_topology",
            "confidence": 0.84,
        },
        {
            "intent": "noise_or_artifact_filtering",
            "concepts": {"noise_removal", "artifact_filtering", "object_removal"},
            "tools": {"transformation_execution"},
            "operation_family": "filter_transform",
            "operation": "remove_noise",
            "confidence": 0.84,
        },
    ]

    def route(
        self,
        detected_concepts: list[str] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        concept_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        concepts = self._collect_concepts(detected_concepts, runtime_context, concept_report)
        tools = self._collect_tools(runtime_context)
        intents = []
        for rule in self.INTENT_RULES:
            concept_hits = sorted(concepts.intersection(rule["concepts"]))
            tool_hits = sorted(tools.intersection(rule["tools"]))
            if not concept_hits:
                continue
            if rule["tools"] and tools and not tool_hits:
                status = "ROUTED_WITHOUT_TOOL_CONFIRMATION"
            else:
                status = "ROUTED"
            intents.append({
                "intent": rule["intent"],
                "operation": self._refine_operation(rule, runtime_context),
                "operation_family": rule["operation_family"],
                "confidence": rule["confidence"],
                "source": "semantic_intent_router",
                "matched_concepts": concept_hits,
                "matched_tools": tool_hits,
                "routing_status": status,
                "activation_reason": self._activation_reason(concept_hits, tool_hits),
            })
        intents = self._dedupe_intents(intents)
        return {
            "system": self.system_name,
            "semantic_intent_routing_success": bool(intents),
            "execution_intents": intents,
            "execution_intent_count": len(intents),
            "detected_concepts": sorted(concepts),
            "enabled_tools": sorted(tools),
            "unrouted_concepts": sorted(
                concept for concept in concepts
                if not any(concept in intent.get("matched_concepts", []) for intent in intents)
            ),
            "timestamp": str(datetime.utcnow()),
        }

    def _collect_concepts(
        self,
        detected_concepts: list[str] | None,
        runtime_context: Mapping[str, Any],
        concept_report: Mapping[str, Any] | None,
    ) -> set[str]:
        concepts = set()

        def add(value: Any) -> None:
            token = self._normalize_token(value)
            if token:
                concepts.add(token)

        def visit(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, str):
                add(value)
                return
            if isinstance(value, Mapping):
                for key, item in value.items():
                    if key in {
                        "concept",
                        "concepts",
                        "detected_concepts",
                        "attributed_concepts",
                        "semantic_concepts",
                        "generated_concepts",
                        "target_concepts",
                        "semantic_context",
                        "intent",
                        "matched_concepts",
                    }:
                        visit(item)
                    elif isinstance(item, (Mapping, list, tuple, set)):
                        visit(item)
                return
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)

        visit(detected_concepts)
        for key in (
            "detected_concepts",
            "attributed_concepts",
            "target_concepts",
            "concepts",
            "semantic_concepts",
            "generated_concepts",
        ):
            visit(runtime_context.get(key))
        report = concept_report if isinstance(concept_report, Mapping) else {}
        for key in (
            "detected_concepts",
            "attributed_concepts",
            "concepts",
            "semantic_concepts",
            "generated_concepts",
        ):
            visit(report.get(key))
        return concepts

    def _collect_tools(self, runtime_context: Mapping[str, Any]) -> set[str]:
        tools = set(str(item) for item in runtime_context.get("enabled_tools", []) or [])
        report = runtime_context.get("tool_selection_report", {})
        if isinstance(report, Mapping):
            for key in ("enabled_tools", "selected_tools", "tools"):
                value = report.get(key)
                if isinstance(value, (list, tuple, set)):
                    tools.update(str(item) for item in value if item)
        return tools

    def _refine_operation(self, rule: Mapping[str, Any], runtime_context: Mapping[str, Any]) -> str:
        signature = str(runtime_context.get("rotation_signature") or "").lower()
        if rule["intent"] in {"rotation", "rotation_reflection"}:
            if "90" in signature or "clockwise" in signature:
                return "rotate_clockwise_90"
            if "180" in signature:
                return "rotate_180"
            if "270" in signature or "counterclockwise" in signature:
                return "rotate_counterclockwise_90"
        return str(rule["operation"])

    def _activation_reason(self, concept_hits: list[str], tool_hits: list[str]) -> str:
        if tool_hits:
            return "semantic_concepts_matched_enabled_execution_tools"
        return "semantic_concepts_matched_execution_intent_rule"

    def _dedupe_intents(self, intents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        unique = []
        for intent in sorted(intents, key=lambda item: (-item["confidence"], item["intent"])):
            key = intent["intent"]
            if key in seen:
                continue
            seen.add(key)
            unique.append(intent)
        return unique

    def _normalize_token(self, value: Any) -> str:
        token = str(value or "").strip().lower()
        token = token.replace("-", "_").replace(" ", "_")
        return token


semantic_intent_router = SemanticIntentRouter()
