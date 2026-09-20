"""Bridge approved dependency activations into runtime execution."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.dependency.dependency_execution_gateway import (
    DependencyExecutionGateway,
    MANDATORY_EXECUTION_CONCEPTS,
)
from runtime.instrumentation import runtime_lifecycle


class DependencyExecutionBridge:
    """Validate activation approval, execute, and capture outcomes."""

    system_name = "dependency_execution_bridge"

    def __init__(self, gateway: DependencyExecutionGateway | None = None):
        self.gateway = gateway or DependencyExecutionGateway()

    def execute(
        self,
        *,
        activation_request: Mapping[str, Any] | None = None,
        activation_decision: Mapping[str, Any] | None = None,
        concepts: list[str] | None = None,
        activated_tools: list[str] | None = None,
        graph_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        lifecycle_execution = runtime_lifecycle.create(
            module_name=self.system_name,
            runtime_name="Dependency Runtime",
            caller="execution_dispatcher",
            trigger="dependency_execution",
        )
        runtime_lifecycle.requested(lifecycle_execution)
        runtime_lifecycle.queued(lifecycle_execution)
        runtime_lifecycle.started(lifecycle_execution)
        runtime_lifecycle.running(lifecycle_execution)
        activation_request = (
            activation_request
            if isinstance(activation_request, Mapping)
            else {}
        )
        activation_decision = (
            activation_decision
            if isinstance(activation_decision, Mapping)
            else {}
        )
        normalized = self._normalize_concepts(concepts or [])
        approval = self._approval_valid(
            activation_decision,
            activated_tools or [],
            normalized,
            activation_request,
        )
        execution = self.gateway.execute(
            concepts=normalized,
            activation_approved=approval,
            graph_report=graph_report,
            runtime_context=runtime_context,
            activation_request=activation_request,
        )
        failures = []
        if approval and not execution.get("execution_started"):
            failures.append("DEPENDENCY_EXECUTION_FAILURE")
        if approval and self._mandatory(normalized) and execution.get("chains_generated", 0) <= 0:
            failures.append("DEPENDENCY_EXECUTION_FAILURE")
        if execution.get("failure_reason"):
            failures.append(execution["failure_reason"])
        if execution.get("execution_success"):
            runtime_lifecycle.completed(
                lifecycle_execution,
                completion_reason="dependency_execution_success",
                output_count=int(execution.get("chains_generated", 0) or 0),
                memory_cost=len(execution.get("dependency_outputs", []) or []),
            )
        elif approval:
            runtime_lifecycle.failed(
                lifecycle_execution,
                failures[0] if failures else "DEPENDENCY_EXECUTION_FAILURE",
            )
        else:
            runtime_lifecycle.blocked(
                lifecycle_execution,
                "activation_not_approved",
            )
        runtime_lifecycle.reported(lifecycle_execution)
        lifecycle_data = lifecycle_execution.as_dict()
        execution_duration = max(
            float(execution.get("execution_duration", 0.0) or 0.0),
            lifecycle_data["elapsed_seconds"],
        )

        report = {
            "system": self.system_name,
            "execution_id": lifecycle_data["execution_id"],
            "execution_start": lifecycle_data["execution_start"],
            "execution_end": lifecycle_data["execution_end"],
            "start_timestamp": lifecycle_data["start_timestamp"],
            "end_timestamp": lifecycle_data["end_timestamp"],
            "elapsed_seconds": execution_duration,
            "elapsed_time": execution_duration,
            "duration_seconds": execution_duration,
            "wall_clock_time": lifecycle_data["wall_clock_time"],
            "cpu_time": lifecycle_data["cpu_time"],
            "exclusive_time": lifecycle_data["exclusive_time"],
            "inclusive_time": lifecycle_data["inclusive_time"],
            "cpu_cost": lifecycle_data["cpu_cost"],
            "memory_cost": lifecycle_data["memory_cost"],
            "input_count": len(normalized),
            "output_count": lifecycle_data["output_count"],
            "success": bool(execution.get("execution_success")),
            "failure": lifecycle_data["failure_reason"],
            "runtime_lifecycle": lifecycle_data,
            "activation_approved": approval,
            "execution_started": execution.get("execution_started", False),
            "execution_completed": execution.get("execution_completed", False),
            "execution_success": execution.get("execution_success", False),
            "execution_duration": execution_duration,
            "dependency_reasoning_time": execution_duration,
            "dependency_reasoning_time_seconds": execution_duration,
            "chains_generated": execution.get("chains_generated", 0),
            "dependency_depth": execution.get("dependency_depth", 0),
            "dependency_confidence": execution.get("dependency_confidence", 0.0),
            "failure_reason": execution.get("failure_reason"),
            "execution_failures": sorted(set(failures)),
            "dependency_outputs": execution.get("dependency_outputs", []),
            "dependency_reports": execution.get("dependency_reports", []),
            "dependency_graph_discovery_report": execution.get(
                "dependency_graph_discovery_report",
                {},
            ),
            "DEPENDENCY_GRAPH_REPORT": execution.get(
                "DEPENDENCY_GRAPH_REPORT",
                {},
            ),
            "dependency_graph_count": execution.get("dependency_graph_count", 0),
            "dependency_node_count": execution.get("dependency_node_count", 0),
            "dependency_edge_count": execution.get("dependency_edge_count", 0),
            "dependency_graph_depth": execution.get("dependency_graph_depth", 0),
            "dependency_graph_reuse_rate": execution.get(
                "dependency_graph_reuse_rate",
                0.0,
            ),
            "dependency_graph_validation_score": execution.get(
                "dependency_graph_validation_score",
                0.0,
            ),
            "dependency_output_registry_report": execution.get(
                "dependency_output_registry_report",
                {},
            ),
            "gateway_report": execution,
            "timestamp": str(datetime.utcnow()),
        }
        report["DEPENDENCY_EXECUTION_REPORT"] = {
            "activation_requests": 1 if activation_request else 0,
            "activation_approvals": 1 if approval else 0,
            "executions_started": 1 if report["execution_started"] else 0,
            "executions_completed": 1 if report["execution_completed"] else 0,
            "executions_failed": 0 if report["execution_success"] else 1,
            "chains_generated": report["chains_generated"],
            "dependency_depth": report["dependency_depth"],
            "execution_time": report["execution_duration"],
        }
        return report

    def _approval_valid(
        self,
        activation_decision: Mapping[str, Any],
        activated_tools: list[str],
        concepts: list[str],
        activation_request: Mapping[str, Any] | None = None,
    ) -> bool:
        if "dependency_reasoning" in set(activated_tools or []):
            return True
        request_state = str(
            activation_request.get("request_state", "")
            if isinstance(activation_request, Mapping)
            else ""
        ).upper()
        if request_state == "REQUESTED":
            return True
        state = str(activation_decision.get("activation_state", "")).upper()
        if state in {"DEPENDENCY_REQUIRED", "DEPENDENCY_RECOMMENDED"}:
            return True
        return self._mandatory(concepts)

    def _mandatory(self, concepts: list[str]) -> bool:
        return bool(set(concepts).intersection(MANDATORY_EXECUTION_CONCEPTS))

    def _normalize_concepts(self, concepts: list[str]) -> list[str]:
        normalized = []
        for concept in concepts or []:
            token = str(concept).strip().lower().replace("-", "_").replace(" ", "_")
            if token and token not in normalized:
                normalized.append(token)
        return normalized


dependency_execution_bridge = DependencyExecutionBridge()


__all__ = ["DependencyExecutionBridge", "dependency_execution_bridge"]
