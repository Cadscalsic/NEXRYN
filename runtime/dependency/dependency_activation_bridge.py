"""Bridge concept discovery to dependency runtime execution."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.dependency.dependency_activation_enforcer import (
    dependency_activation_enforcer,
)
from runtime.dependency.dependency_activation_manager import (
    DEPENDENCY_NOT_REQUIRED,
    DEPENDENCY_RECOMMENDED,
    DEPENDENCY_REQUIRED,
    DependencyActivationManager,
)
from runtime.dependency.dependency_activation_trace import (
    SKIP_REPORT_KEY,
    TRACE_REPORT_KEY,
    DependencyActivationTrace,
)
from runtime.dependency.dependency_chain_builder import DependencyChainBuilder
from runtime.dependency.dependency_execution_bridge import DependencyExecutionBridge
from runtime.dependency.dependency_graph_builder import DependencyGraphBuilder
from runtime.instrumentation import runtime_lifecycle


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
        "falling": {
            "dependency_reasoning",
            "process_semantics",
            "causal_reasoning",
        },
        "support": {
            "dependency_reasoning",
            "process_semantics",
            "causal_reasoning",
        },
        "collision": {
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
        "falling",
        "support",
        "collision",
        "multi_step_reasoning",
    }

    PROCESS_CONCEPTS = {
        "route_completion",
        "transformation_sequence",
        "multi_step_reasoning",
        "gravity",
        "falling",
        "support",
        "collision",
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
        execution_bridge: DependencyExecutionBridge | None = None,
        process_engine=None,
    ):
        self.activation_manager = activation_manager or DependencyActivationManager()
        self.graph_builder = graph_builder or DependencyGraphBuilder()
        self.chain_builder = chain_builder or DependencyChainBuilder()
        self.execution_bridge = execution_bridge or DependencyExecutionBridge()
        self.process_engine = process_engine
        self.activation_history = []

    def activate(
        self,
        detected_concepts: list[str] | None = None,
        selected_tools: list[str] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        lifecycle_execution = runtime_lifecycle.create(
            module_name=self.system_name,
            runtime_name="Dependency Runtime",
            caller="execution_dispatcher",
            trigger="dependency_activation",
        )
        runtime_lifecycle.requested(lifecycle_execution)
        runtime_lifecycle.queued(lifecycle_execution)
        runtime_lifecycle.started(lifecycle_execution)
        runtime_lifecycle.running(lifecycle_execution)
        concepts = self._collect_concepts(detected_concepts, runtime_context)
        mutable_context = dict(runtime_context)
        trace = DependencyActivationTrace()
        trace.detect_concepts(concepts)
        selected = sorted(set(selected_tools or self._selected_tools(runtime_context)))
        required_tools = self._required_tools(concepts)
        required_tool_set = set(required_tools)
        enforcement = dependency_activation_enforcer.enforce(
            concepts,
            mutable_context,
            trace=trace,
        )
        mutable_context = enforcement["runtime_context"]
        activation_request_generated = bool(
            enforcement.get("activation_request_generated")
        )
        selection_checkpoint = "no_request"
        if activation_request_generated:
            selection_checkpoint = "request_created"
        elif "dependency_reasoning" in selected and not concepts:
            selection_checkpoint = "request_created"
            reason = (
                mutable_context.get("dependency_activation_reason")
                or "dependency_reasoning_selected_without_detected_concepts"
            )
            trace.request(
                requested_tool="dependency_reasoning",
                requested_by=self.system_name,
                reason=reason,
                concepts=concepts,
            )
            existing_requests = mutable_context.get("runtime_tool_requests", {})
            if isinstance(existing_requests, dict):
                existing_requests = dict(existing_requests)
            else:
                existing_requests = {}
            mutable_context["runtime_tool_requests"] = {
                **existing_requests,
                "dependency_reasoning": {
                    "tool_name": "dependency_reasoning",
                    "request_state": "REQUESTED",
                    "requested_by": self.system_name,
                    "activation_state": DEPENDENCY_REQUIRED,
                    "reason": reason,
                    "matched_signals": list(concepts),
                    "trace_request": {
                        "requested_tool": "dependency_reasoning",
                        "requested_by": self.system_name,
                        "request_state": "REQUESTED",
                        "reason": reason,
                    },
                },
            }
            mutable_context["enabled_tools"] = sorted(
                set(mutable_context.get("enabled_tools", []) or [])
                | {"dependency_reasoning"}
            )
            mutable_context["dependency_activation_reason"] = reason
            activation_request_generated = True
        elif enforcement.get("activation_already_requested"):
            selection_checkpoint = "existing_request"
        elif selected:
            selection_checkpoint = "selection_only"

        if enforcement.get("activation_required") and "dependency_reasoning" not in selected:
            selected = sorted(set(selected) | {"dependency_reasoning"})
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
            runtime_context=mutable_context,
        )
        links = graph_report.get("dependency_links", [])
        trace.set_dependency_candidates(
            [link.get("source") for link in links if isinstance(link, Mapping)]
        )
        activation_decision = self.activation_manager.evaluate(
            {
                **mutable_context,
                "detected_concepts": concepts,
                "enabled_tools": activated_tools,
                "process_note": " ".join(concepts),
            },
            task_profile=mutable_context.get("task_profile", {}),
            links_loaded=len(links),
        )
        if required_tools:
            trace.approve(
                requested_tool="dependency_reasoning",
                approved_by=self.system_name,
                reason=activation_decision.get("dependency_activation_reason"),
            )
        trace.enter_runtime(self.system_name, concepts)

        execution_report = {}
        if concepts or required_tools or activation_request_generated:
            execution_report = self.execution_bridge.execute(
                activation_request={
                    "requested_tool": "dependency_reasoning",
                    "detected_concepts": concepts,
                    "required_tools": required_tools,
                },
                activation_decision=activation_decision,
                concepts=concepts,
                activated_tools=activated_tools,
                graph_report=graph_report,
                runtime_context=mutable_context,
            )
        else:
            execution_report = {
                "execution_started": False,
                "execution_completed": False,
                "execution_success": False,
                "execution_duration": 0.0,
                "chains_generated": 0,
                "dependency_depth": 0,
                "dependency_confidence": 0.0,
                "failure_reason": None,
                "execution_failures": [],
                "dependency_outputs": [],
                "dependency_reports": [],
                "dependency_graph_discovery_report": {},
                "DEPENDENCY_GRAPH_REPORT": {},
                "dependency_graph_count": 0,
                "dependency_node_count": 0,
                "dependency_edge_count": 0,
                "dependency_graph_depth": 0,
                "dependency_graph_reuse_rate": 0.0,
                "dependency_graph_validation_score": 0.0,
                "dependency_output_registry_report": {},
                "gateway_report": {},
            }
        dependency_reports = execution_report.get("dependency_reports", [])

        process_contexts = []
        if "process_semantics" in activated_tools and dependency_reports:
            process_engine = self._process_engine()
            for chain in dependency_reports:
                process_concept = (
                    graph_report.get("dependency_chains", [{}])[0].get(
                        "process_concept",
                    )
                    if graph_report.get("dependency_chains")
                    else chain.get("concept")
                )
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
                            "process_dependency_links_used": max(
                                len(chain.get("chain", []) or []),
                                len(links),
                            ),
                            "dependency_confidence": chain.get(
                                "dependency_confidence",
                                0.0,
                            ),
                        },
                        runtime_context={
                            **mutable_context,
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
            execution_report,
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
        trace.exit_runtime(
            self.system_name,
            executed=bool(
                dependency_chain_count
                or process_context_count
                or causal_context_count
            ),
            failure=(
                "activation_required_but_no_runtime_outputs"
                if required_tools
                and not (
                    dependency_chain_count
                    or process_context_count
                    or causal_context_count
                )
                else None
            ),
        )
        missing_warning = trace.assert_requested_when_concepts_exist()
        skip_reports = []
        if skipped_tools:
            for tool in skipped_tools:
                skip_reports.append(
                    trace.skip_report(
                        requested_tool=tool,
                        activation_attempted=bool(required_tools),
                        activation_blocked=True,
                        block_reason=skip_reasons.get(tool),
                        blocking_module=self.system_name,
                        blocking_condition="selected_tool_not_required",
                    )
                )
        if required_tools and not dependency_chain_count and "dependency_reasoning" in required_tools:
            skip_reports.append(
                trace.skip_report(
                    requested_tool="dependency_reasoning",
                    activation_attempted=True,
                    activation_blocked=True,
                    block_reason="no_dependency_chains_executed",
                    blocking_module=self.system_name,
                    blocking_condition="dependency_runtime_output_empty",
                )
            )
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
            "ACTIVATED"
            if success_count > 0 and not failures
            else "REQUESTED"
            if activation_request_generated
            and not success_count
            else activation_decision.get("activation_state", DEPENDENCY_REQUIRED)
            if required_tools
            else DEPENDENCY_NOT_REQUIRED
        )
        if dependency_chain_count or process_context_count or causal_context_count:
            runtime_lifecycle.completed(
                lifecycle_execution,
                completion_reason="dependency_runtime_outputs_generated",
                output_count=(
                    dependency_chain_count
                    + process_context_count
                    + causal_context_count
                ),
                memory_cost=(
                    dependency_chain_count
                    + process_context_count
                    + causal_context_count
                ),
            )
        elif required_tools:
            runtime_lifecycle.blocked(
                lifecycle_execution,
                "no_dependency_runtime_outputs",
                metadata={"required_tools": required_tools},
            )
        else:
            runtime_lifecycle.completed(
                lifecycle_execution,
                completion_reason="dependency_runtime_not_required",
                output_count=0,
                memory_cost=0,
            )
        runtime_lifecycle.reported(lifecycle_execution)
        lifecycle_data = lifecycle_execution.as_dict()
        dependency_runtime_duration = max(
            float(execution_report.get("execution_duration", 0.0) or 0.0),
            lifecycle_data["elapsed_seconds"],
        )
        audit_report = self._build_activation_audit_report(
            selected=selected,
            required_tools=required_tools,
            activation_request_generated=activation_request_generated,
            activation_already_requested=enforcement.get("activation_already_requested"),
            selection_checkpoint=selection_checkpoint,
            concepts=concepts,
            activation_decision=activation_decision,
            execution_report=execution_report,
            runtime_context=mutable_context,
        )
        failure_report = self._build_activation_failure_report(
            requested_tool="dependency_reasoning",
            activation_request_generated=activation_request_generated,
            activation_state=activation_state,
            failures=failures,
            execution_report=execution_report,
            trace=trace,
        )

        report = {
            "system": self.system_name,
            "execution_id": lifecycle_data["execution_id"],
            "execution_start": lifecycle_data["execution_start"],
            "execution_end": lifecycle_data["execution_end"],
            "start_timestamp": lifecycle_data["start_timestamp"],
            "end_timestamp": lifecycle_data["end_timestamp"],
            "elapsed_seconds": dependency_runtime_duration,
            "elapsed_time": dependency_runtime_duration,
            "duration_seconds": dependency_runtime_duration,
            "wall_clock_time": lifecycle_data["wall_clock_time"],
            "cpu_time": lifecycle_data["cpu_time"],
            "exclusive_time": lifecycle_data["exclusive_time"],
            "inclusive_time": lifecycle_data["inclusive_time"],
            "cpu_cost": lifecycle_data["cpu_cost"],
            "memory_cost": lifecycle_data["memory_cost"],
            "input_count": len(concepts) + len(selected),
            "output_count": lifecycle_data["output_count"],
            "success": bool(
                dependency_chain_count
                or process_context_count
                or causal_context_count
                or not required_tools
            ),
            "failure": lifecycle_data["failure_reason"],
            "runtime_lifecycle": lifecycle_data,
            "detected_concepts": concepts,
            "selected_tools": selected,
            "activated_tools": activated_tools,
            "skipped_tools": skipped_tools,
            "skip_reasons": skip_reasons,
            "dependency_graph_report": graph_report,
            "dependency_reports": dependency_reports,
            "dependency_execution_bridge_report": execution_report,
            "DEPENDENCY_EXECUTION_REPORT": execution_report.get(
                "DEPENDENCY_EXECUTION_REPORT",
                {},
            ),
            "dependency_graph_discovery_report": execution_report.get(
                "dependency_graph_discovery_report",
                {},
            ),
            "DEPENDENCY_GRAPH_REPORT": execution_report.get(
                "DEPENDENCY_GRAPH_REPORT",
                {},
            ),
            "dependency_output_registry_report": execution_report.get(
                "dependency_output_registry_report",
                {},
            ),
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
            SKIP_REPORT_KEY: skip_reports,
            TRACE_REPORT_KEY: trace.report(),
            "activation_request_count": len(trace.activation_requests),
            "dependency_activation_state": activation_state,
            "DEPENDENCY_ACTIVATION_AUDIT_REPORT": audit_report,
            "DEPENDENCY_ACTIVATION_FAILURE_REPORT": failure_report,
            "dependency_activation_reason": self._activation_reason(
                concepts,
                required_tools,
                activation_decision,
            ),
            "dependency_runtime_triggered": bool(
                activation_request_generated
                or execution_report.get("execution_started")
                or dependency_chain_count > 0
                or process_context_count > 0
                or causal_context_count > 0
            ),
            "dependency_graph_size": graph_report.get("dependency_graph", {}).get(
                "edge_count",
                0,
            ),
            "dependency_chain_count": dependency_chain_count,
            "process_context_count": process_context_count,
            "causal_context_count": causal_context_count,
            "activation_success_rate": success_rate,
            "dependency_chain_coverage": round(dependency_coverage, 4),
            "dependency_reasoning_time": dependency_runtime_duration,
            "dependency_execution_count": 1 if execution_report.get("execution_started") else 0,
            "dependency_execution_time": dependency_runtime_duration,
            "dependency_reasoning_time_seconds": dependency_runtime_duration,
            "dependency_chains_executed": dependency_chain_count,
            "dependency_chain_depth": dependency_depth,
            "dependency_execution_success_rate": (
                1.0 if execution_report.get("execution_success") else 0.0
            ),
            "dependency_runtime_utilization": (
                1.0 if execution_report.get("execution_started") else 0.0
            ),
            "dependency_graph_count": execution_report.get("dependency_graph_count", 0),
            "dependency_node_count": execution_report.get("dependency_node_count", 0),
            "dependency_edge_count": execution_report.get("dependency_edge_count", 0),
            "dependency_graph_depth": execution_report.get("dependency_graph_depth", 0),
            "dependency_graph_reuse_rate": execution_report.get(
                "dependency_graph_reuse_rate",
                0.0,
            ),
            "dependency_graph_validation_score": execution_report.get(
                "dependency_graph_validation_score",
                0.0,
            ),
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
                "dependency_execution_count",
                "dependency_execution_time",
                "dependency_graph_count",
                "dependency_node_count",
                "dependency_edge_count",
                "dependency_graph_depth",
                "process_contexts_generated",
                "causal_contexts_generated",
                "activation_failures",
                "skip_reasons",
            ]
        }
        report["DEPENDENCY_ACTIVATION_REPORT"].update({
            "activation_requests": trace.report()["activation_requests"],
            "activation_approvals": trace.report()["activation_approvals"],
            "activation_executions": trace.report()["activation_executions"],
            "dependency_execution_result": execution_report.get(
                "gateway_report",
                {},
            ).get("DEPENDENCY_EXECUTION_RESULT", {}),
            "activation_failures": (
                report["DEPENDENCY_ACTIVATION_REPORT"]["activation_failures"]
                + trace.report()["activation_failures"]
            ),
            "activation_success_rate": success_rate,
            "skip_reports": skip_reports,
            "missing_warning": missing_warning,
        })
        self.activation_history.append(report)
        return report

    def _build_activation_audit_report(
        self,
        *,
        selected: list[str],
        required_tools: list[str],
        activation_request_generated: bool,
        activation_already_requested: bool | None,
        selection_checkpoint: str,
        concepts: list[str],
        activation_decision: Mapping[str, Any],
        execution_report: Mapping[str, Any],
        runtime_context: Mapping[str, Any],
    ) -> dict[str, Any]:
        selected_set = set(selected)
        budget_report = runtime_context.get("cognitive_budget_report", {})
        if not isinstance(budget_report, Mapping):
            budget_report = {}
        process_semantics_enabled = bool(
            "process_semantics" in selected_set
            or bool(runtime_context.get("process_semantics_enabled"))
            or bool(budget_report.get("process_semantics_enabled"))
        )
        dependency_reasoning_enabled = bool(
            "dependency_reasoning" in selected_set
            or bool(runtime_context.get("dependency_reasoning_enabled"))
            or bool(budget_report.get("dependency_reasoning_enabled"))
        )
        return {
            "system": "dependency_activation_audit",
            "selected_tools": sorted(selected),
            "required_tools": sorted(required_tools),
            "activation_required": bool(required_tools),
            "activation_request_generated": bool(activation_request_generated),
            "activation_already_requested": bool(activation_already_requested),
            "selection_checkpoint": selection_checkpoint,
            "detected_concepts": list(concepts),
            "process_semantics_enabled": process_semantics_enabled,
            "dependency_reasoning_enabled": dependency_reasoning_enabled,
            "activation_request_count": 1 if activation_request_generated else 0,
            "dependency_activation_state": (
                "REQUESTED"
                if activation_request_generated
                else str(
                    activation_decision.get("activation_state", DEPENDENCY_NOT_REQUIRED)
                )
            ),
            "activation_state": (
                "REQUESTED"
                if activation_request_generated
                else str(
                    activation_decision.get("activation_state", DEPENDENCY_NOT_REQUIRED)
                )
            ),
            "execution_started": bool(execution_report.get("execution_started")),
            "execution_completed": bool(execution_report.get("execution_completed")),
            "execution_success": bool(execution_report.get("execution_success")),
        }

    def _build_activation_failure_report(
        self,
        *,
        requested_tool: str,
        activation_request_generated: bool,
        activation_state: str,
        failures: list[dict[str, Any]],
        execution_report: Mapping[str, Any],
        trace: DependencyActivationTrace,
    ) -> dict[str, Any]:
        failure_messages = [str(item.get("message", item)) for item in failures]
        failure_detected = bool(
            failure_messages
            or (
                requested_tool in {"dependency_reasoning"}
                and not activation_request_generated
                and activation_state == DEPENDENCY_NOT_REQUIRED
            )
        )
        return {
            "system": "dependency_activation_failure",
            "requested_tool": requested_tool,
            "failure_detected": failure_detected,
            "failure_messages": failure_messages,
            "execution_failures": list(execution_report.get("execution_failures", []) or []),
            "trace_failures": trace.report().get("activation_failures", []),
        }

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

    def _validate(
        self,
        concepts,
        dependency_reports,
        process_contexts,
        causal_contexts,
        execution_report=None,
    ):
        execution_report = execution_report if isinstance(execution_report, Mapping) else {}
        warnings = []
        concept_set = set(concepts)
        if (
            concept_set.intersection(self.DEPENDENCY_CONCEPTS)
            and not execution_report.get("execution_started")
        ):
            warnings.append({
                "type": "DEPENDENCY_EXECUTION_FAILURE",
                "message": "dependency activation approved but execution did not start",
            })
        if (
            execution_report.get("execution_started")
            and not execution_report.get("execution_completed")
        ):
            warnings.append({
                "type": "DEPENDENCY_EXECUTION_FAILURE",
                "message": "dependency execution started but did not complete",
            })
        if execution_report.get("execution_failures"):
            for failure in execution_report.get("execution_failures", []):
                warnings.append({
                    "type": "DEPENDENCY_EXECUTION_FAILURE",
                    "message": str(failure),
                })
        if concept_set.intersection(self.DEPENDENCY_CONCEPTS) and not dependency_reports:
            warnings.append({
                "type": "DEPENDENCY_EXECUTION_FAILURE",
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
