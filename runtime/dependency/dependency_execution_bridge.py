"""Bridge approved dependency activations into runtime execution."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.dependency.dependency_execution_gateway import (
    DependencyExecutionGateway,
    MANDATORY_EXECUTION_CONCEPTS,
)


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

        report = {
            "system": self.system_name,
            "activation_approved": approval,
            "execution_started": execution.get("execution_started", False),
            "execution_completed": execution.get("execution_completed", False),
            "execution_success": execution.get("execution_success", False),
            "execution_duration": execution.get("execution_duration", 0.0),
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
