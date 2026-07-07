"""Dispatch planned execution nodes into existing runtime executors.

The dispatcher is intentionally orchestration-only. It validates planned nodes,
records lifecycle transitions, calls already existing runtimes, and returns
runtime updates plus an execution dispatch report.
"""

from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Any, Mapping

from runtime.causal import causal_context_runtime
from runtime.dependency import dependency_execution_bridge
from runtime.instrumentation import runtime_lifecycle
from runtime.process import process_context_runtime


class ExecutionDispatcher:
    """Validate and dispatch :class:`ExecutionPlan` nodes to runtime layers."""

    system_name = "execution_dispatcher"

    def dispatch(
        self,
        *,
        execution_plan: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        runtime_budget: Any = None,
    ) -> dict[str, Any]:
        """Dispatch executable nodes and return report plus runtime updates.

        Args:
            execution_plan: Serializable execution plan from the planner.
            runtime_context: Current runtime context.
            runtime_budget: Optional budget object or mapping for readiness.

        Returns:
            A dictionary containing `EXECUTION_DISPATCH_REPORT`,
            `dispatched_execution_plan`, `runtime_updates`, and raw runtime
            result reports.
        """

        plan = execution_plan if isinstance(execution_plan, Mapping) else {}
        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        lifecycle_execution = runtime_lifecycle.create(
            module_name=self.system_name,
            runtime_name="Execution Runtime",
            caller="execution_planner",
            trigger="execution_dispatch",
        )
        runtime_lifecycle.requested(lifecycle_execution)
        runtime_lifecycle.queued(lifecycle_execution)
        runtime_lifecycle.started(lifecycle_execution)
        runtime_lifecycle.running(lifecycle_execution)
        budget = self._budget(runtime_budget, context)
        nodes = self._nodes(plan)
        pruning = self._pruning_reasons(plan)
        lifecycle = {}
        completed = set()
        runtime_updates: dict[str, Any] = {}
        runtime_results: dict[str, Any] = {}
        failures = []
        block_reasons = {}
        dispatched_nodes = []
        completed_nodes = []
        failed_nodes = []
        blocked_nodes = []
        ready_nodes = []
        dependency_dispatched = 0
        process_dispatched = 0
        causal_dispatched = 0
        dependency_called = False
        process_called = False
        causal_called = False

        for node in nodes:
            node_id = str(node.get("node_id") or "")
            if not node_id:
                continue
            lifecycle[node_id] = ["PLANNED"]
            readiness = self._readiness(node, completed, pruning, budget, context)
            if not readiness["ready"]:
                reason = readiness["reason"]
                node["status"] = "BLOCKED"
                node["dispatch_status"] = "BLOCKED_WITH_REASON"
                node["block_reason"] = reason
                lifecycle[node_id].append("BLOCKED")
                block_reasons[node_id] = reason
                blocked_nodes.append(dict(node))
                continue

            node["status"] = "READY"
            lifecycle[node_id].append("READY")
            ready_nodes.append(dict(node))
            node["status"] = "DISPATCHED"
            lifecycle[node_id].append("DISPATCHED")
            dispatched_nodes.append(dict(node))
            node["status"] = "RUNNING"
            lifecycle[node_id].append("RUNNING")
            started_at = perf_counter()

            try:
                dispatch_result = self._dispatch_node(node, context, runtime_updates)
            except Exception as exc:  # pragma: no cover - defensive boundary.
                dispatch_result = {
                    "runtime_called": False,
                    "success": False,
                    "failure_reason": str(exc),
                    "runtime_report": {},
                    "runtime_updates": {},
                }

            runtime_name = self._node_kind(node)
            if runtime_name == "dependency":
                dependency_called = dependency_called or dispatch_result["runtime_called"]
                dependency_dispatched += int(dispatch_result["runtime_called"])
            elif runtime_name == "process":
                process_called = process_called or dispatch_result["runtime_called"]
                process_dispatched += int(dispatch_result["runtime_called"])
            elif runtime_name == "causal":
                causal_called = causal_called or dispatch_result["runtime_called"]
                causal_dispatched += int(dispatch_result["runtime_called"])

            runtime_updates.update(dispatch_result.get("runtime_updates", {}))
            runtime_results[node_id] = dispatch_result.get("runtime_report", {})
            node["runtime_duration"] = round(perf_counter() - started_at, 6)
            if dispatch_result.get("success"):
                node["status"] = "COMPLETED"
                node["dispatch_status"] = "COMPLETED"
                lifecycle[node_id].append("COMPLETED")
                completed.add(node_id)
                completed_nodes.append(dict(node))
            else:
                reason = dispatch_result.get("failure_reason") or "DISPATCH_FAILURE"
                node["status"] = "FAILED"
                node["dispatch_status"] = "FAILED"
                node["failure_reason"] = reason
                lifecycle[node_id].append("FAILED")
                failures.append({
                    "node_id": node_id,
                    "tool": node.get("originating_tool"),
                    "reason": reason,
                })
                failed_nodes.append(dict(node))

        planned_after_dispatch = [
            node.get("node_id")
            for node in nodes
            if str(node.get("status", "")).upper() in {"PLANNED", "PENDING"}
        ]
        for node_id in planned_after_dispatch:
            failures.append({
                "node_id": node_id,
                "reason": "DISPATCH_FAILURE",
            })

        dependency_chains = self._int_value(
            runtime_updates.get(
                "dependency_lifecycle_report",
                {},
            ).get("dependency_chains_executed")
            if isinstance(
                runtime_updates.get("dependency_lifecycle_report"),
                Mapping,
            )
            else 0
        )
        process_count = self._int_value(
            runtime_updates.get(
                "process_context_report",
                {},
            ).get("process_context_count")
            if isinstance(runtime_updates.get("process_context_report"), Mapping)
            else 0
        )
        causal_count = self._int_value(
            runtime_updates.get(
                "causal_context_report",
                {},
            ).get("causal_context_count")
            if isinstance(runtime_updates.get("causal_context_report"), Mapping)
            else 0
        )
        report = {
            "system": self.system_name,
            "report_state": "final",
            "EXECUTION_DISPATCH_REPORT": True,
            "execution_plan_received": bool(plan),
            "execution_nodes_received": len(nodes),
            "nodes_ready": len(ready_nodes),
            "nodes_dispatched": len(dispatched_nodes),
            "nodes_completed": len(completed_nodes),
            "nodes_failed": len(failed_nodes),
            "nodes_blocked": len(blocked_nodes),
            "execution_nodes_completed": len(completed_nodes),
            "dependency_nodes_dispatched": dependency_dispatched,
            "process_nodes_dispatched": process_dispatched,
            "causal_nodes_dispatched": causal_dispatched,
            "dependency_runtime_called": dependency_called,
            "process_runtime_called": process_called,
            "causal_runtime_called": causal_called,
            "dependency_chains_executed": dependency_chains,
            "process_context_count": process_count,
            "causal_context_count": causal_count,
            "execution_failures": failures,
            "block_reasons": block_reasons,
            "node_lifecycle": lifecycle,
            "ready_nodes": ready_nodes,
            "dispatched_nodes": dispatched_nodes,
            "completed_nodes": completed_nodes,
            "failed_nodes": failed_nodes,
            "blocked_nodes": blocked_nodes,
            "planned_nodes_after_dispatch": planned_after_dispatch,
            "execution_summary": {
                "completed": len(completed_nodes),
                "failed": len(failed_nodes),
                "blocked": len(blocked_nodes),
                "runtimes_called": {
                    "dependency": dependency_called,
                    "process": process_called,
                    "causal": causal_called,
                },
            },
            "timestamp": str(datetime.utcnow()),
        }
        runtime_lifecycle.completed(
            lifecycle_execution,
            completion_reason="execution_dispatch_report_built",
            output_count=len(completed_nodes) + len(failed_nodes) + len(blocked_nodes),
            memory_cost=len(runtime_updates) + len(runtime_results),
        )
        runtime_lifecycle.reported(lifecycle_execution)
        lifecycle_data = lifecycle_execution.as_dict()
        report.update({
            "execution_id": lifecycle_data["execution_id"],
            "execution_start": lifecycle_data["execution_start"],
            "execution_end": lifecycle_data["execution_end"],
            "start_timestamp": lifecycle_data["start_timestamp"],
            "end_timestamp": lifecycle_data["end_timestamp"],
            "elapsed_seconds": lifecycle_data["elapsed_seconds"],
            "elapsed_time": lifecycle_data["elapsed_seconds"],
            "duration_seconds": lifecycle_data["elapsed_seconds"],
            "wall_clock_time": lifecycle_data["wall_clock_time"],
            "cpu_time": lifecycle_data["cpu_time"],
            "exclusive_time": lifecycle_data["exclusive_time"],
            "inclusive_time": lifecycle_data["inclusive_time"],
            "cpu_cost": lifecycle_data["cpu_cost"],
            "memory_cost": lifecycle_data["memory_cost"],
            "input_count": len(nodes),
            "output_count": lifecycle_data["output_count"],
            "success": not failed_nodes,
            "failure": None if not failed_nodes else "DISPATCH_FAILURES_RECORDED",
            "runtime_lifecycle": lifecycle_data,
        })
        return {
            "EXECUTION_DISPATCH_REPORT": report,
            "execution_dispatch_report": report,
            "dispatched_execution_plan": {
                **plan,
                "execution_nodes": nodes,
                "nodes": nodes,
                "execution_dispatched": True,
            },
            "runtime_updates": runtime_updates,
            "runtime_results": runtime_results,
        }

    def _dispatch_node(
        self,
        node: Mapping[str, Any],
        context: Mapping[str, Any],
        runtime_updates: Mapping[str, Any],
    ) -> dict[str, Any]:
        kind = self._node_kind(node)
        if kind == "dependency":
            return self._dispatch_dependency(node, context)
        if kind == "process":
            return self._dispatch_process(node, context, runtime_updates)
        if kind == "causal":
            return self._dispatch_causal(node, context, runtime_updates)
        return {
            "runtime_called": True,
            "success": True,
            "runtime_report": {
                "system": self.system_name,
                "stage": node.get("stage"),
                "tool": node.get("originating_tool"),
                "execution_result": "no_special_runtime_required",
            },
            "runtime_updates": {},
        }

    def _dispatch_dependency(
        self,
        node: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> dict[str, Any]:
        request = self._tool_request(context, "dependency_reasoning")
        report = dependency_execution_bridge.execute(
            activation_request=request,
            activation_decision=context.get("dependency_activation_manager_report", {}),
            concepts=self._concepts(context),
            activated_tools=context.get("enabled_tools", []),
            graph_report=(
                context.get("dependency_graph_discovery_report")
                or context.get("dependency_graph_report")
                or {}
            ),
            runtime_context=context,
        )
        chains = int(report.get("chains_generated", 0) or 0)
        duration = float(report.get("execution_duration", 0.0) or 0.0)
        if chains > 0 and duration <= 0.0:
            duration = 0.0001
        updates = {
            "dependency_execution_bridge_report": report,
            "dependency_reasoning_report": {
                **report,
                "dependency_activation_state": (
                    "COMPLETED" if chains > 0 else "FAILED"
                ),
                "dependency_time": duration,
                "dependency_chains_executed": chains,
            },
            "dependency_lifecycle_report": {
                "system": "dependency_runtime",
                "report_state": "final",
                "dependency_activation_state": (
                    "COMPLETED" if chains > 0 else "FAILED"
                ),
                "dependency_requested_by": "execution_dispatcher",
                "dependency_chains_executed": chains,
                "dependency_outputs_generated": len(
                    report.get("dependency_outputs", []) or []
                ),
                "dependency_time": duration,
                "dependency_activation_reason": node.get("activation_reason"),
                "dispatch_node_id": node.get("node_id"),
            },
            "dependency_chains": report.get("dependency_reports", []),
            "process_dependency_chains": {
                item.get("concept", f"dependency_{index}"): item
                for index, item in enumerate(report.get("dependency_reports", []) or [])
                if isinstance(item, Mapping)
            },
            "dependency_graph_discovery_report": report.get(
                "dependency_graph_discovery_report",
                {},
            ),
            "DEPENDENCY_GRAPH_REPORT": report.get("DEPENDENCY_GRAPH_REPORT", {}),
            "dependency_chain_depth": report.get("dependency_depth", 0),
            "dependency_chain_coverage": 1.0 if chains > 0 else 0.0,
        }
        return {
            "runtime_called": True,
            "success": chains > 0 or bool(report.get("execution_completed")),
            "failure_reason": report.get("failure_reason"),
            "runtime_report": report,
            "runtime_updates": updates,
        }

    def _dispatch_process(
        self,
        node: Mapping[str, Any],
        context: Mapping[str, Any],
        runtime_updates: Mapping[str, Any],
    ) -> dict[str, Any]:
        merged_context = {**dict(context), **dict(runtime_updates)}
        dependency_report = (
            merged_context.get("dependency_execution_bridge_report")
            or merged_context.get("dependency_reasoning_report")
            or merged_context.get("dependency_lifecycle_report")
            or {}
        )
        report = process_context_runtime.run(
            detected_concepts=self._concepts(merged_context),
            dependency_activation_report=dependency_report,
            runtime_context=merged_context,
        )
        count = int(report.get("process_context_count", 0) or 0)
        updates = {
            "process_context_runtime_report": report,
            "process_context_report": report,
            "process_context_registry_report": {
                "system": "process_context_registry",
                "report_state": "final",
                "process_context_count": count,
                "process_contexts": report.get("registered_contexts", []),
            },
            "process_execution_request_report": {
                "system": "process_semantic_execution",
                "report_state": "final",
                "process_activation_state": (
                    "COMPLETED" if count > 0 else "FAILED"
                ),
                "process_requested_by": "execution_dispatcher",
                "process_stage_created": True,
                "process_context_count": count,
                "process_generation_time": report.get(
                    "process_generation_time",
                    0.0,
                ),
                "process_validation_score": report.get(
                    "process_validation_score",
                    0.0,
                ),
                "dispatch_node_id": node.get("node_id"),
            },
        }
        return {
            "runtime_called": True,
            "success": count > 0,
            "failure_reason": None if count > 0 else "PROCESS_CONTEXT_NOT_GENERATED",
            "runtime_report": report,
            "runtime_updates": updates,
        }

    def _dispatch_causal(
        self,
        node: Mapping[str, Any],
        context: Mapping[str, Any],
        runtime_updates: Mapping[str, Any],
    ) -> dict[str, Any]:
        merged_context = {**dict(context), **dict(runtime_updates)}
        process_report = (
            merged_context.get("process_context_runtime_report")
            or merged_context.get("process_context_report")
            or {}
        )
        dependency_report = (
            merged_context.get("dependency_execution_bridge_report")
            or merged_context.get("dependency_reasoning_report")
            or {}
        )
        report = causal_context_runtime.run(
            process_context_report=process_report,
            dependency_activation_report=dependency_report,
            transformation_report=merged_context.get("transformation_report", {}),
            color_mapping_report=merged_context.get("color_mapping_report", {}),
            runtime_context=merged_context,
        )
        count = int(report.get("causal_context_count", 0) or 0)
        updates = {
            "causal_context_runtime_report": report,
            "causal_context_report": report,
            "CAUSAL_CONTEXT_REPORT": report.get("CAUSAL_CONTEXT_REPORT", {}),
            "causal_execution_request_report": {
                "system": "causal_validation_execution",
                "report_state": "final",
                "causal_activation_state": (
                    "COMPLETED" if count > 0 else "BLOCKED"
                ),
                "causal_requested_by": "execution_dispatcher",
                "causal_stage_created": True,
                "causal_context_count": count,
                "causal_block_reasons": report.get("block_reasons", []),
                "causal_generation_time": report.get(
                    "generation_time",
                    0.0,
                ),
                "causal_validation_score": report.get(
                    "causal_validation_score",
                    0.0,
                ),
                "dispatch_node_id": node.get("node_id"),
            },
        }
        return {
            "runtime_called": True,
            "success": count > 0,
            "failure_reason": (
                None
                if count > 0
                else {
                    "state": "CAUSAL_CONTEXT_BLOCKED",
                    "block_reasons": report.get("block_reasons", []),
                    "blocking_module": "causal_context_runtime",
                }
            ),
            "runtime_report": report,
            "runtime_updates": updates,
        }

    def _readiness(
        self,
        node: Mapping[str, Any],
        completed: set[str],
        pruning: Mapping[str, str],
        budget: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> dict[str, Any]:
        status = str(node.get("status", "")).upper()
        node_id = str(node.get("node_id") or "")
        tool = node.get("originating_tool")
        if status in {"BLOCKED", "DEFERRED"}:
            reason = pruning.get(node_id) or status
            if (
                tool == "process_semantics"
                and reason == "process_semantics_enabled=False"
                and "process_semantics" in set(context.get("enabled_tools", []) or [])
            ):
                return {"ready": True, "reason": None}
            return {
                "ready": False,
                "reason": reason,
            }
        parent = node.get("parent_node")
        if parent and parent not in completed:
            return {
                "ready": False,
                "reason": f"parent_not_completed:{parent}",
            }
        if (
            tool == "process_semantics"
            and budget.get("process_semantics_enabled") is False
            and "process_semantics" not in set(context.get("enabled_tools", []) or [])
        ):
            return {
                "ready": False,
                "reason": "process_semantics_enabled=False",
            }
        if tool == "dependency_reasoning" and int(
            budget.get("max_dependency_depth", 1) or 1
        ) <= 0:
            return {
                "ready": False,
                "reason": "max_dependency_depth<=0",
            }
        if tool == "causal_validation" and not (
            context.get("process_context_report")
            or context.get("process_context_runtime_report")
            or context.get("process_execution_request_report")
            or "process_semantics" in context.get("enabled_tools", [])
        ):
            return {
                "ready": False,
                "reason": "required_context_missing:process_context",
            }
        return {"ready": True, "reason": None}

    def _nodes(self, plan: Mapping[str, Any]) -> list[dict[str, Any]]:
        ordered = []
        by_id = {}
        for key in (
            "execution_nodes",
            "nodes",
            "dependency_nodes",
            "process_nodes",
            "causal_nodes",
            "blocked_nodes",
            "deferred_nodes",
        ):
            for node in plan.get(key, []) or []:
                if not isinstance(node, Mapping):
                    continue
                node_id = node.get("node_id")
                if node_id and node_id not in by_id:
                    by_id[node_id] = dict(node)
        for node_id in plan.get("execution_order", []) or []:
            if node_id in by_id:
                ordered.append(by_id.pop(node_id))
        ordered.extend(by_id.values())
        return ordered

    def _pruning_reasons(self, plan: Mapping[str, Any]) -> dict[str, str]:
        reasons = {}
        for item in plan.get("pruning_log", []) or []:
            if isinstance(item, Mapping) and item.get("node_id"):
                reasons[str(item["node_id"])] = str(
                    item.get("reason") or item.get("decision") or "BLOCKED"
                )
        return reasons

    def _node_kind(self, node: Mapping[str, Any]) -> str:
        tool = str(node.get("originating_tool") or "")
        stage = str(node.get("stage") or "")
        if tool == "dependency_reasoning" or "dependency" in stage:
            return "dependency"
        if tool == "process_semantics" or "process" in stage:
            return "process"
        if tool == "causal_validation" or "causal" in stage:
            return "causal"
        return "generic"

    def _tool_request(self, context: Mapping[str, Any], tool: str) -> dict[str, Any]:
        requests = context.get("runtime_tool_requests", {})
        if isinstance(requests, Mapping):
            request = requests.get(tool, {})
            if isinstance(request, Mapping):
                return dict(request)
        return {
            "tool_name": tool,
            "request_state": "REQUESTED",
            "requested_by": self.system_name,
        }

    def _concepts(self, context: Mapping[str, Any]) -> list[str]:
        concepts = []

        def add(value: Any) -> None:
            token = str(value).strip().lower().replace("-", "_").replace(" ", "_")
            if token and token not in concepts:
                concepts.append(token)

        for key in (
            "semantic_attribution_report",
            "introspection_report",
            "concept_attribution_report",
        ):
            report = context.get(key, {})
            if isinstance(report, Mapping):
                for item in (
                    report.get("attributed_concepts", [])
                    or report.get("concepts", [])
                    or []
                ):
                    add(item)
        for item in context.get("attributed_concepts", []) or []:
            add(item)
        if not concepts:
            add("multi_step_reasoning")
        return concepts

    def _budget(self, runtime_budget: Any, context: Mapping[str, Any]) -> dict[str, Any]:
        source = runtime_budget or context.get("current_reasoning_budget") or {}
        if isinstance(source, Mapping):
            return dict(source)
        return {
            key: getattr(source, key, None)
            for key in (
                "max_dependency_depth",
                "process_semantics_enabled",
                "max_execution_cost",
            )
        }

    def _int_value(self, value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


execution_dispatcher = ExecutionDispatcher()


__all__ = [
    "ExecutionDispatcher",
    "execution_dispatcher",
]
