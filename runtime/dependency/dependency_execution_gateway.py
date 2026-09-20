"""Single entry point for approved dependency runtime executions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from time import perf_counter
from typing import Any, Mapping

from runtime.dependency.dependency_graph_discovery import DependencyGraphDiscovery
from runtime.dependency.dependency_output_registry import DependencyOutputRegistry


MANDATORY_EXECUTION_CONCEPTS = {
    "gravity",
    "falling",
    "support",
    "collision",
    "path_finding",
    "route_completion",
    "bridge_creation",
    "component_connection",
    "transformation_sequence",
    "multi_step_reasoning",
}


FIRST_GENERATION_CHAINS = {
    "gravity": ["gravity", "unsupported_object", "fall", "rest_state"],
    "falling": ["falling", "unsupported_object", "fall", "rest_state"],
    "support": ["support", "supported_object", "stable_state"],
    "collision": ["collision", "contact", "constraint", "rest_state"],
    "path_finding": ["path_finding", "start", "reachable_nodes", "goal"],
    "route_completion": ["route_completion", "start", "reachable_nodes", "goal"],
    "bridge_creation": ["bridge_creation", "component_A", "connector", "component_B"],
    "component_connection": [
        "component_connection",
        "component_A",
        "connector",
        "component_B",
    ],
    "transformation_sequence": [
        "transformation_sequence",
        "input_state",
        "step",
        "output_state",
    ],
    "multi_step_reasoning": [
        "multi_step_reasoning",
        "initial_state",
        "intermediate_state",
        "final_state",
    ],
}


@dataclass
class DependencyExecutionResult:
    execution_started: bool
    execution_completed: bool
    execution_success: bool
    execution_duration: float
    chains_generated: int
    dependency_depth: int
    dependency_confidence: float
    failure_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["execution_duration"] = round(float(self.execution_duration or 0.0), 6)
        data["dependency_confidence"] = round(
            float(self.dependency_confidence or 0.0),
            4,
        )
        return data


class DependencyExecutionGateway:
    """Execute dependency chains after activation approval."""

    system_name = "dependency_execution_gateway"

    def __init__(
        self,
        output_registry: DependencyOutputRegistry | None = None,
        graph_discovery: DependencyGraphDiscovery | None = None,
    ):
        self.output_registry = output_registry or DependencyOutputRegistry()
        self.graph_discovery = graph_discovery or DependencyGraphDiscovery()

    def execute(
        self,
        *,
        concepts: list[str],
        activation_approved: bool,
        graph_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        activation_request: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        started_at = perf_counter()
        graph_report = graph_report if isinstance(graph_report, Mapping) else {}
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        normalized = self._normalize_concepts(concepts)
        lineage = {
            "gateway": self.system_name,
            "activation_request": dict(activation_request or {}),
            "task_id": runtime_context.get("task_id"),
            "runtime_context_keys": sorted(str(key) for key in runtime_context.keys()),
        }

        if not activation_approved:
            result = DependencyExecutionResult(
                execution_started=False,
                execution_completed=False,
                execution_success=False,
                execution_duration=perf_counter() - started_at,
                chains_generated=0,
                dependency_depth=0,
                dependency_confidence=0.0,
                failure_reason="activation_not_approved",
            )
            return self._report(result, [], lineage, {}, {})

        outputs = []
        try:
            for concept in normalized:
                chain = self._chain_for(concept, graph_report)
                if not chain:
                    continue
                confidence = self._confidence_for(concept, graph_report, chain)
                output = self._output_for(concept, chain, confidence, lineage)
                self.output_registry.register(
                    concept=concept,
                    chain=chain,
                    output=output,
                    confidence=confidence,
                    lineage=lineage,
                )
                outputs.append(output)
        except Exception as exc:  # pragma: no cover - defensive execution barrier.
            result = DependencyExecutionResult(
                execution_started=True,
                execution_completed=True,
                execution_success=False,
                execution_duration=perf_counter() - started_at,
                chains_generated=len(outputs),
                dependency_depth=max(
                    [item.get("dependency_chain_depth", 0) for item in outputs]
                    or [0],
                ),
                dependency_confidence=0.0,
                failure_reason=str(exc),
            )
            graph_report = self._discover_graph(normalized, outputs, runtime_context)
            return self._report(
                result,
                outputs,
                lineage,
                graph_report,
                runtime_context,
            )

        depths = [int(item.get("dependency_chain_depth", 0) or 0) for item in outputs]
        confidences = [
            float(item.get("dependency_confidence", 0.0) or 0.0)
            for item in outputs
        ]
        required = bool(set(normalized).intersection(MANDATORY_EXECUTION_CONCEPTS))
        failure_reason = None
        if required and not outputs:
            failure_reason = "DEPENDENCY_EXECUTION_FAILURE"
        result = DependencyExecutionResult(
            execution_started=True,
            execution_completed=True,
            execution_success=bool(outputs) and failure_reason is None,
            execution_duration=perf_counter() - started_at,
            chains_generated=len(outputs),
            dependency_depth=max(depths or [0]),
            dependency_confidence=(
                round(sum(confidences) / len(confidences), 4)
                if confidences
                else 0.0
            ),
            failure_reason=failure_reason,
        )
        graph_report = self._discover_graph(normalized, outputs, runtime_context)
        return self._report(result, outputs, lineage, graph_report, runtime_context)

    def _report(
        self,
        result: DependencyExecutionResult,
        outputs: list[dict[str, Any]],
        lineage: Mapping[str, Any],
        graph_report: Mapping[str, Any],
        runtime_context: Mapping[str, Any],
    ) -> dict[str, Any]:
        result_dict = result.as_dict()
        registry_report = self.output_registry.report()
        dependency_graph_report = graph_report.get("DEPENDENCY_GRAPH_REPORT", {})
        return {
            "system": self.system_name,
            **result_dict,
            "dependency_outputs": outputs,
            "dependency_reports": outputs,
            "generated_chains": [
                output.get("resolved_dependency_chain", [])
                for output in outputs
            ],
            "execution_lineage": dict(lineage),
            "dependency_output_registry_report": registry_report,
            "dependency_graph_discovery_report": dict(graph_report),
            "DEPENDENCY_GRAPH_REPORT": dict(dependency_graph_report),
            "dependency_graph_count": graph_report.get("dependency_graph_count", 0),
            "dependency_node_count": graph_report.get("dependency_node_count", 0),
            "dependency_edge_count": graph_report.get("dependency_edge_count", 0),
            "dependency_graph_depth": graph_report.get("dependency_graph_depth", 0),
            "dependency_graph_reuse_rate": graph_report.get(
                "dependency_graph_reuse_rate",
                0.0,
            ),
            "dependency_graph_validation_score": graph_report.get(
                "dependency_graph_validation_score",
                0.0,
            ),
            "DEPENDENCY_EXECUTION_RESULT": result_dict,
            "timestamp": str(datetime.utcnow()),
        }

    def _discover_graph(
        self,
        concepts: list[str],
        outputs: list[dict[str, Any]],
        runtime_context: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not outputs:
            return {}
        return self.graph_discovery.discover(
            concepts=concepts,
            dependency_outputs=outputs,
            runtime_context=runtime_context,
        )

    def _normalize_concepts(self, concepts: list[str]) -> list[str]:
        normalized = []
        for concept in concepts or []:
            token = str(concept).strip().lower().replace("-", "_").replace(" ", "_")
            if token and token not in normalized:
                normalized.append(token)
        return normalized

    def _chain_for(self, concept: str, graph_report: Mapping[str, Any]) -> list[str]:
        if concept in FIRST_GENERATION_CHAINS:
            return list(FIRST_GENERATION_CHAINS[concept])
        for chain_record in graph_report.get("dependency_chains", []) or []:
            if chain_record.get("concept") == concept:
                return [concept, *list(chain_record.get("chain", []) or [])]
        return []

    def _confidence_for(
        self,
        concept: str,
        graph_report: Mapping[str, Any],
        chain: list[str],
    ) -> float:
        for chain_record in graph_report.get("dependency_chains", []) or []:
            if chain_record.get("concept") == concept:
                return round(
                    float(chain_record.get("dependency_confidence", 0.0) or 0.0),
                    4,
                )
        if concept in MANDATORY_EXECUTION_CONCEPTS:
            return 0.9
        return round(min(0.82 + max(len(chain) - 3, 0) * 0.02, 0.96), 4)

    def _output_for(
        self,
        concept: str,
        chain: list[str],
        confidence: float,
        lineage: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "concept": concept,
            "resolved_dependency_chain": list(chain),
            "chain": list(chain),
            "dependencies": list(chain),
            "dependency_chain_depth": max(len(chain) - 1, 0),
            "dependency_depth": max(len(chain) - 1, 0),
            "dependency_confidence": round(float(confidence or 0.0), 4),
            "dependency_chain_coverage": 1.0,
            "dependency_output_produced": True,
            "governance_consumable": True,
            "execution_lineage": dict(lineage),
        }


dependency_execution_gateway = DependencyExecutionGateway()


__all__ = [
    "DependencyExecutionGateway",
    "DependencyExecutionResult",
    "FIRST_GENERATION_CHAINS",
    "MANDATORY_EXECUTION_CONCEPTS",
    "dependency_execution_gateway",
]
