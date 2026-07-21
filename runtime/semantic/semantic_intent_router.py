"""Bridge semantic concepts into validated executable transformation intents."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.semantic.executable_coverage import ExecutableCoverageTracker
from runtime.semantic.executable_semantics import ExecutableSemanticIntelligence
from runtime.semantic.semantic_operation_mapper import SemanticOperationMapper


INTENT_BY_CONCEPT = {
    "replication": "duplicate_object",
    "duplication": "duplicate_object",
    "object_creation": "duplicate_object",
    "color_preservation": "preserve_color_mapping",
    "color_mapping": "replace_color_mapping",
    "symbolic_remapping": "remap_symbols",
    "topology_preservation": "preserve_topology",
    "shape_preservation": "preserve_shape",
    "size_preservation": "preserve_size",
    "density_preservation": "preserve_density",
    "topological_growth": "expand_topology",
    "growth": "grow_topology",
    "symmetry_preservation": "preserve_symmetry",
    "symmetry_reasoning": "preserve_symmetry",
    "symmetry_creation": "create_symmetry",
    "directional_motion": "translate_object",
    "object_translation": "translate_object",
    "rotation": "rotation",
    "orientation_change": "rotation",
    "reflection": "reflection",
    "rotation_reflection": "rotation_reflection",
    "scaling": "scaling",
    "scale_transformation": "scaling",
    "size_transformation": "scaling",
    "path_finding": "path_construction",
    "route_completion": "path_construction",
    "path_construction": "path_construction",
    "bridge_creation": "component_connection",
    "component_connection": "component_connection",
    "connectivity_change": "component_connection",
    "topology_change": "component_connection",
    "topology_repair": "topology_repair",
    "hole_removal": "topology_repair",
    "connectivity_restoration": "topology_repair",
    "noise_removal": "noise_or_artifact_filtering",
    "artifact_filtering": "noise_or_artifact_filtering",
    "object_removal": "noise_or_artifact_filtering",
}

LEGACY_OPERATION_ALIASES = {
    "duplicate_object": "duplicate_object",
    "preserve_color": "preserve_colors",
    "preserve_color_mapping": "preserve_colors",
    "replace_color": "replace_color",
    "remap_symbols": "replace_color",
    "preserve_topology": "preserve_topology",
    "preserve_shape": "preserve_shape",
    "preserve_size": "preserve_size",
    "preserve_density": "preserve_density",
    "expand_topology": "grow_topology",
    "grow_topology": "grow_topology",
    "preserve_symmetry": "preserve_symmetry",
    "mirror_object": "reflect",
    "translate_object": "translate",
    "rotate": "rotate",
    "reflect": "reflect",
    "rotate_or_reflect": "rotate_or_reflect",
    "scale": "scale",
    "construct_path": "construct_path",
    "connect_components": "connect_components",
    "repair_topology": "repair_topology",
    "remove_noise": "remove_noise",
    "remove_object": "remove_object",
}


class SemanticIntentRouter:
    """Create execution proposals only after governance and executability pass."""

    system_name = "semantic_intent_router"

    def __init__(
        self,
        executable_semantics: ExecutableSemanticIntelligence | None = None,
        operation_mapper: SemanticOperationMapper | None = None,
        coverage_tracker: ExecutableCoverageTracker | None = None,
    ):
        self.executable_semantics = executable_semantics or ExecutableSemanticIntelligence()
        self.operation_mapper = operation_mapper or SemanticOperationMapper()
        self.coverage_tracker = coverage_tracker or ExecutableCoverageTracker(self.executable_semantics)

    def route(
        self,
        detected_concepts: list[str] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        concept_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        concepts = self._collect_concepts(detected_concepts, runtime_context, concept_report)
        tools = self._collect_tools(runtime_context)
        governance = self._governance_report(runtime_context)
        proposals = []
        blocked = []

        for concept in sorted(concepts):
            semantic = self.executable_semantics.evaluate(concept, runtime_context=runtime_context)
            mapping = self.operation_mapper.map(concept)
            if not governance["governance_passed"]:
                blocked.append(self._blocked(concept, "governance_rejected", governance))
                continue
            if not semantic.get("is_executable"):
                blocked.append(self._blocked(concept, semantic.get("coverage_state"), governance))
                continue
            if not mapping.get("operation_ready"):
                blocked.append(self._blocked(concept, "operation_mapping_missing", governance))
                continue
            proposals.append(self._proposal(concept, semantic, mapping, tools, runtime_context))

        proposals = self._dedupe_proposals(proposals)
        coverage = self.coverage_tracker.evaluate(concepts, runtime_context=runtime_context)
        execution_intents = [self._execution_intent(proposal) for proposal in proposals]
        routed_concepts = {
            concept
            for intent in execution_intents
            for concept in intent.get("matched_concepts", []) or []
        }
        return {
            "system": self.system_name,
            "semantic_intent_routing_success": bool(execution_intents),
            "intent_router_success": bool(execution_intents),
            "execution_intents": execution_intents,
            "execution_proposals": proposals,
            "execution_intent_count": len(execution_intents),
            "detected_concepts": sorted(concepts),
            "enabled_tools": sorted(tools),
            "unrouted_concepts": sorted(concepts - routed_concepts),
            "blocked_concepts": blocked,
            "governance_report": governance,
            "executable_coverage_report": coverage,
            "timestamp": str(datetime.utcnow()),
        }

    def infer_intent(
        self,
        concept: str,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = self.route([concept], runtime_context=runtime_context)
        proposals = report.get("execution_proposals", [])
        if proposals:
            return proposals[0]
        return {
            "concept": _normalize(concept),
            "semantic_intent": None,
            "intent_confidence": 0.0,
            "operation_family": None,
            "intent_ready": False,
        }

    def _proposal(self, concept, semantic, mapping, tools, runtime_context):
        confidence = min(
            float(mapping.get("confidence", 0.0) or 0.0),
            0.98,
        )
        operation = self._refine_operation(
            str(mapping.get("operation_name") or ""),
            semantic.get("execution_path"),
            runtime_context,
        )
        matched_tools = sorted(tools.intersection(self._tool_hints(semantic, mapping)))
        semantic_intent = INTENT_BY_CONCEPT.get(concept, operation)
        return {
            "concept": concept,
            "semantic_intent": semantic_intent,
            "intent_confidence": round(confidence, 4),
            "operation_family": mapping.get("primitive_family") or semantic.get("primitive_family"),
            "operation_name": operation,
            "primitive_family": semantic.get("primitive_family"),
            "required_primitives": list(semantic.get("required_primitives", []) or []),
            "execution_path": semantic.get("execution_path"),
            "intent_ready": True,
            "matched_concepts": [concept],
            "matched_tools": matched_tools,
            "routing_status": "ROUTED" if matched_tools or not tools else "ROUTED_WITHOUT_TOOL_CONFIRMATION",
            "source": self.system_name,
        }

    def _execution_intent(self, proposal):
        operation = LEGACY_OPERATION_ALIASES.get(
            proposal.get("operation_name"),
            proposal.get("operation_name"),
        )
        if proposal.get("semantic_intent") in {"rotation", "rotation_reflection"}:
            operation = proposal.get("operation_name")
        return {
            "intent": proposal["semantic_intent"],
            "semantic_intent": proposal["semantic_intent"],
            "operation": operation,
            "operation_family": proposal["operation_family"],
            "confidence": proposal["intent_confidence"],
            "intent_confidence": proposal["intent_confidence"],
            "source": self.system_name,
            "matched_concepts": list(proposal.get("matched_concepts", [])),
            "matched_tools": list(proposal.get("matched_tools", [])),
            "routing_status": proposal.get("routing_status", "ROUTED"),
            "activation_reason": self._activation_reason(proposal),
            "intent_ready": True,
            "required_primitives": list(proposal.get("required_primitives", [])),
            "execution_path": proposal.get("execution_path"),
        }

    def _collect_concepts(
        self,
        detected_concepts: list[str] | None,
        runtime_context: Mapping[str, Any],
        concept_report: Mapping[str, Any] | None,
    ) -> set[str]:
        concepts = set()

        def visit(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, str):
                token = _normalize(value)
                if token:
                    concepts.add(token)
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
        return {_normalize(tool) for tool in tools}

    def _governance_report(self, runtime_context: Mapping[str, Any]) -> dict[str, Any]:
        checks = {
            "truth_governance": self._check(runtime_context, (
                "truth_governance_report",
                "truth_commit_result",
                "truth_validation_report",
            )),
            "identity_governance": self._check(runtime_context, (
                "identity_governance_report",
                "identity_continuity_engine_report",
                "identity_continuity_guardian_report",
            )),
            "contextual_truth": self._check(runtime_context, (
                "contextual_truth_report",
                "contextual_truth_authority_report",
                "semantic_context_report",
            )),
            "dependency_validation": self._check(runtime_context, (
                "dependency_graph_validation",
                "typed_dependency_validation_report",
                "dependency_activation_report",
            )),
        }
        passed = all(item["passed"] for item in checks.values())
        return {
            "governance_passed": passed,
            "checks": checks,
            "blocked_reasons": [
                name for name, result in checks.items()
                if not result["passed"]
            ],
        }

    def _check(self, runtime_context: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
        observed = []
        for key in keys:
            value = runtime_context.get(key)
            if not isinstance(value, Mapping):
                continue
            observed.append(key)
            if self._explicit_failure(value):
                return {"passed": False, "observed": observed, "reason": f"{key}_failed"}
        return {"passed": True, "observed": observed, "reason": "no_blocking_failure"}

    def _explicit_failure(self, value: Mapping[str, Any]) -> bool:
        for key, item in value.items():
            normalized_key = _normalize(key)
            normalized_value = _normalize(item)
            if normalized_key.endswith(("passed", "success", "ready", "validated")) and item is False:
                return True
            if normalized_key in {"status", "state", "validation_state", "governance_state"}:
                if normalized_value in {"failed", "rejected", "blocked", "invalid", "unsafe"}:
                    return True
        return False

    def _refine_operation(self, operation, execution_path, runtime_context):
        signature = str(runtime_context.get("rotation_signature") or "").lower()
        if operation in {"rotate", "rotate_or_reflect"} or execution_path == "geometric_rotation":
            if "90" in signature or "clockwise" in signature:
                return "rotate_clockwise_90"
            if "180" in signature:
                return "rotate_180"
            if "270" in signature or "counterclockwise" in signature:
                return "rotate_counterclockwise_90"
        return operation

    def _tool_hints(self, semantic, mapping):
        family = _normalize(mapping.get("primitive_family") or semantic.get("primitive_family"))
        hints = {"semantic_to_transformation_compiler", "transformation_execution"}
        if "geometric" in family:
            hints.update({"rotation_execution", "reflection_execution"})
        if "scale" in family:
            hints.add("scaling_execution")
        if "path" in family:
            hints.add("path_execution")
        return hints

    def _activation_reason(self, proposal):
        if proposal.get("matched_tools"):
            return "semantic_concepts_matched_enabled_execution_tools"
        return "semantic_concepts_validated_as_executable_intents"

    def _blocked(self, concept, reason, governance):
        return {
            "concept": concept,
            "blocked_reason": reason,
            "governance_passed": governance.get("governance_passed"),
        }

    def _dedupe_proposals(self, proposals):
        by_intent = {}
        for proposal in sorted(
            proposals,
            key=lambda item: (-item["intent_confidence"], item["semantic_intent"], item["concept"]),
        ):
            key = proposal["semantic_intent"]
            if key not in by_intent:
                by_intent[key] = proposal
                continue
            existing = by_intent[key]
            existing["matched_concepts"] = sorted(set(existing["matched_concepts"]) | set(proposal["matched_concepts"]))
            existing["matched_tools"] = sorted(set(existing["matched_tools"]) | set(proposal["matched_tools"]))
        return list(by_intent.values())


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


semantic_intent_router = SemanticIntentRouter()

__all__ = [
    "INTENT_BY_CONCEPT",
    "SemanticIntentRouter",
    "semantic_intent_router",
]
