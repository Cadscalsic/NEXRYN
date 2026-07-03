"""Bridge concept discovery to dependency runtime execution."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.dependency.dependency_activation_manager import (
    DEPENDENCY_COMPLETED,
    DEPENDENCY_NOT_REQUIRED,
    DEPENDENCY_REQUIRED,
    DependencyActivationManager,
)
from runtime.dependency.dependency_chain_builder import DependencyChainBuilder
from runtime.dependency.dependency_graph_builder import DependencyGraphBuilder


class DependencyActivationBridge:
    """Activate dependency/process/causal reasoning from discovered concepts."""

    system_name = "dependency_activation_bridge"

    ACTIVATION_RULES = {
        "path_finding": {"dependency_reasoning"},
        "route_completion": {"dependency_reasoning", "process_semantics"},
        "bridge_creation": {"dependency_reasoning"},
        "component_connection": {"dependency_reasoning"},
        "transformation_sequence": {"process_semantics"},
        "multi_step_reasoning": {"dependency_reasoning", "process_semantics"},
        "gravity": {
            "dependency_reasoning",
            "process_semantics",
            "causal_reasoning",
        },
        "connectivity_change": {"dependency_reasoning", "process_semantics"},
        "topology_change": {"dependency_reasoning", "process_semantics"},
        "relative_position": {"dependency_reasoning"},
        "spatial_relation": {"dependency_reasoning"},
    }

    DEPENDENCY_CONCEPTS = {
        "path_finding",
        "route_completion",
        "bridge_creation",
        "component_connection",
        "connectivity_change",
        "topology_change",
        "relative_position",
        "spatial_relation",
        "gravity",
        "multi_step_reasoning",
    }

    PROCESS_CONCEPTS = {
        "route_completion",
        "transformation_sequence",
        "multi_step_reasoning",
        "gravity",
        "connectivity_change",
        "topology_change",
    }

    CAUSAL_CONCEPTS = {
        "gravity",
        "bridge_creation",
        "component_connection",
        "connectivity_change",
        "topology_change",
        "transformation_sequence",
    }

    def __init__(
        self,
        activation_manager: DependencyActivationManager | None = None,
        graph_builder: DependencyGraphBuilder | None = None,
        chain_builder: DependencyChainBuilder | None = None,
        process_engine=None,
    ):
        self.activation_manager = activation_manager or DependencyActivationManager()
        self.graph_builder = graph_builder or DependencyGraphBuilder()
        self.chain_builder = chain_builder or DependencyChainBuilder()
        self.process_engine = process_engine
        self.activation_history = []

    def activate(
        self,
        detected_concepts: list[str] | None = None,
        selected_tools: list[str] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        concepts = self._collect_concepts(detected_concepts, runtime_context)
        selected = sorted(set(selected_tools or self._selected_tools(runtime_context)))
        required_tools = self._required_tools(concepts)
        required_tool_set = set(required_tools)
        activated_tools = sorted(
            set(selected).intersection(required_tool_set)
            | required_tool_set
        )
        skipped_tools = sorted(set(selected) - set(activated_tools))
        skip_reasons = {
            tool: "selected_tool_not_required_by_detected_dependency_concepts"
            for tool in skipped_tools
        }

        graph_report = self.graph_builder.build(
            concepts,
            runtime_context=runtime_context,
        )
        links = graph_report.get("dependency_links", [])
        activation_decision = self.activation_manager.evaluate(
            {
                **dict(runtime_context),
                "detected_concepts": concepts,
                "enabled_tools": activated_tools,
                "process_note": " ".join(concepts),
            },
            task_profile=runtime_context.get("task_profile", {}),
            links_loaded=len(links),
        )

        dependency_reports = []
        if "dependency_reasoning" in activated_tools and links:
            for chain in graph_report.get("dependency_chains", []) or []:
                dependency_reports.append(
                    self.chain_builder.build(
                        chain.get("concept", ""),
                        links,
                        observed_contradictions=runtime_context.get(
                            "observed_contradictions",
                            runtime_context.get("contradictions", []),
                        ),
                    )
                )

        process_contexts = []
        if "process_semantics" in activated_tools and graph_report.get("dependency_chains"):
            process_engine = self._process_engine()
            for chain in graph_report.get("dependency_chains", []) or []:
                process_concept = chain.get("process_concept")
                if not process_concept:
                    continue
                process_contexts.append(
                    process_engine.synthesize(
                        process_concept,
                        dependency_chain={
                            "resolved_dependency_chain": chain.get("chain", []),
                            "typed_dependency_relations": links,
                            "typed_process_dependencies_enabled": True,
                            "process_dependency_links_loaded": len(links),
                            "process_dependency_links_used": len(links),
                            "dependency_confidence": chain.get(
                                "dependency_confidence",
                                0.0,
                            ),
                        },
                        runtime_context={
                            **dict(runtime_context),
                            "dependency_confidence": chain.get(
                                "dependency_confidence",
                                0.0,
                            ),
                            "causal_alignment": chain.get(
                                "dependency_confidence",
                                0.0,
                            ),
                            "typed_dependency_report": {
                                "typed_process_dependencies_enabled": True,
                                "typed_dependency_relations": links,
                                "process_dependency_links_loaded": len(links),
                                "process_dependency_links_used": len(links),
                                "dependency_confidence": chain.get(
                                    "dependency_confidence",
                                    0.0,
                                ),
                            },
                        },
                    )
                )

        causal_contexts = []
        if "causal_reasoning" in activated_tools or set(concepts).intersection(
            self.CAUSAL_CONCEPTS
        ):
            causal_contexts = graph_report.get("causal_context_templates", [])

        validation = self._validate(
            concepts,
            dependency_reports,
            process_contexts,
            causal_contexts,
        )
        failures = list(validation.get("structured_warnings", []))

        dependency_chain_count = len(dependency_reports)
        dependency_depth = max(
            [
                report.get("dependency_chain_depth", 0)
                for report in dependency_reports
            ]
            + [graph_report.get("dependency_depth", 0)]
        )
        dependency_coverage = max(
            [
                float(report.get("dependency_chain_coverage", 0.0) or 0.0)
                for report in dependency_reports
            ]
            + [float(graph_report.get("dependency_coverage", 0.0) or 0.0)]
        )
        process_context_count = len(
            [
                report
                for report in process_contexts
                if report.get("process_context_generated")
            ]
        )
        causal_context_count = len(causal_contexts)
        required_count = max(len(required_tools), 1)
        success_count = len(
            [
                tool
                for tool in required_tools
                if (
                    tool == "dependency_reasoning"
                    and dependency_chain_count > 0
                )
                or (
                    tool == "process_semantics"
                    and process_context_count > 0
                )
                or (
                    tool == "causal_reasoning"
                    and causal_context_count > 0
                )
            ]
        )
        success_rate = round(success_count / required_count, 4)
        activation_state = (
            DEPENDENCY_COMPLETED
            if success_count > 0 and not failures
            else activation_decision.get("activation_state", DEPENDENCY_REQUIRED)
            if required_tools
            else DEPENDENCY_NOT_REQUIRED
        )

        report = {
            "system": self.system_name,
            "detected_concepts": concepts,
            "selected_tools": selected,
            "activated_tools": activated_tools,
            "skipped_tools": skipped_tools,
            "skip_reasons": skip_reasons,
            "dependency_graph_report": graph_report,
            "dependency_reports": dependency_reports,
            "process_contexts": process_contexts,
            "causal_contexts": causal_contexts,
            "dependency_chains_generated": dependency_chain_count,
            "dependency_depth": dependency_depth,
            "dependency_coverage": round(dependency_coverage, 4),
            "dependency_confidence": graph_report.get("dependency_confidence", 0.0),
            "process_contexts_generated": process_context_count,
            "causal_contexts_generated": causal_context_count,
            "activation_failures": failures,
            "activation_validation": validation,
            "dependency_activation_state": activation_state,
            "dependency_activation_reason": self._activation_reason(
                concepts,
                required_tools,
                activation_decision,
            ),
            "dependency_runtime_triggered": bool(dependency_chain_count > 0),
            "dependency_graph_size": graph_report.get("dependency_graph", {}).get(
                "edge_count",
                0,
            ),
            "dependency_chain_count": dependency_chain_count,
            "process_context_count": process_context_count,
            "causal_context_count": causal_context_count,
            "activation_success_rate": success_rate,
            "dependency_chains_executed": dependency_chain_count,
            "dependency_chain_depth": dependency_depth,
            "dependency_chain_coverage": round(dependency_coverage, 4),
            "dependency_reasoning_time": 0.0 if dependency_chain_count == 0 else 0.0001,
            "timestamp": str(datetime.utcnow()),
        }
        report["DEPENDENCY_ACTIVATION_REPORT"] = {
            key: report[key]
            for key in [
                "detected_concepts",
                "selected_tools",
                "activated_tools",
                "skipped_tools",
                "dependency_chains_generated",
                "dependency_depth",
                "process_contexts_generated",
                "causal_contexts_generated",
                "activation_failures",
                "skip_reasons",
            ]
        }
        self.activation_history.append(report)
        return report

    def _process_engine(self):
        if self.process_engine is None:
            from runtime.process.process_semantic_context_engine import (
                ProcessSemanticContextEngine,
            )

            self.process_engine = ProcessSemanticContextEngine()
        return self.process_engine

    def _collect_concepts(self, detected_concepts, runtime_context):
        concepts = []

        def add(value):
            token = str(value).strip().lower().replace("-", "_").replace(" ", "_")
            if token and token not in concepts:
                concepts.append(token)

        for concept in detected_concepts or []:
            add(concept)

        def visit(value):
            if isinstance(value, str):
                token = value.lower().replace("-", "_").replace(" ", "_")
                if token in self.ACTIVATION_RULES:
                    add(token)
            elif isinstance(value, Mapping):
                for key, item in value.items():
                    if key in {
                        "concept",
                        "concepts",
                        "detected_concepts",
                        "suspected_concepts",
                        "attributed_concepts",
                        "semantic_context",
                        "symbolic_type",
                        "abstract_rule",
                        "type",
                    }:
                        visit(item)
                    elif isinstance(item, (Mapping, list, tuple, set)):
                        visit(item)
            elif isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)

        for key in [
            "detected_concepts",
            "suspected_concepts",
            "semantic_abstractions",
            "concept_attribution_report",
            "semantic_attribution_report",
            "tool_selection_report",
            "pre_reasoning_task_profile",
            "task_profile",
        ]:
            visit(runtime_context.get(key))
        return concepts

    def _selected_tools(self, runtime_context):
        tools = set(runtime_context.get("enabled_tools", []) or [])
        for key in ["selected_tools", "tools", "enabled_tools"]:
            report = runtime_context.get("tool_selection_report", {})
            if isinstance(report, Mapping):
                tools.update(report.get(key, []) or [])
        requests = runtime_context.get("runtime_tool_requests", {})
        if isinstance(requests, Mapping):
            tools.update(requests.keys())
        return sorted(tools)

    def _required_tools(self, concepts):
        tools = set()
        for concept in concepts:
            tools.update(self.ACTIVATION_RULES.get(concept, set()))
            if any(marker in concept for marker in ["path", "route", "bridge", "connect"]):
                tools.add("dependency_reasoning")
            if any(marker in concept for marker in ["sequence", "multi_step", "process"]):
                tools.add("process_semantics")
            if any(marker in concept for marker in ["causal", "gravity", "support", "fall"]):
                tools.update({"dependency_reasoning", "process_semantics", "causal_reasoning"})
        return sorted(tools)

    def _validate(self, concepts, dependency_reports, process_contexts, causal_contexts):
        warnings = []
        concept_set = set(concepts)
        if concept_set.intersection(self.DEPENDENCY_CONCEPTS) and not dependency_reports:
            warnings.append({
                "type": "dependency_activation_missing",
                "message": "dependency concepts detected but no dependency chains executed",
            })
        if concept_set.intersection(self.PROCESS_CONCEPTS) and not process_contexts:
            warnings.append({
                "type": "process_context_missing",
                "message": "process concepts detected but no process contexts generated",
            })
        if concept_set.intersection(self.CAUSAL_CONCEPTS) and not causal_contexts:
            warnings.append({
                "type": "causal_context_missing",
                "message": "causal concepts detected but no causal contexts generated",
            })
        return {
            "dependency_validation_passed": not warnings,
            "structured_warnings": warnings,
        }

    def _activation_reason(self, concepts, required_tools, activation_decision):
        if required_tools:
            return (
                "concept_discovery_required_runtime_activation:"
                + ",".join(concepts)
            )
        return activation_decision.get(
            "dependency_activation_reason",
            "no_dependency_trigger_detected",
        )


dependency_activation_bridge = DependencyActivationBridge()


__all__ = [
    "DependencyActivationBridge",
    "dependency_activation_bridge",
]
