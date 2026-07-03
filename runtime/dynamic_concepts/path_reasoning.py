"""Path-finding reasoning for dynamic ARC concepts."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.dynamic_concepts.reachability_reasoning import ReachabilityReasoning


class PathReasoning:
    """Build candidate paths and completion strategies from reachability graphs."""

    family = "path_finding"

    def __init__(self, reachability=None):
        self.reachability = reachability or ReachabilityReasoning()

    def reason(
        self,
        input_grid=None,
        output_grid=None,
        causal_context_report: Mapping[str, Any] | None = None,
        process_context_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        concepts = set(str(item) for item in runtime_context.get("detected_concepts", []) or [])
        causal_families = set((causal_context_report or {}).get("causal_families_detected", []) or [])
        if not concepts.intersection({"path_finding", "route_completion"}) and "path_cause" not in causal_families:
            return []
        reach = self.reachability.reason(
            input_grid=input_grid,
            output_grid=output_grid,
            causal_context_report=causal_context_report,
            process_context_report=process_context_report,
            runtime_context=runtime_context,
        )
        base = reach[0] if reach else {}
        candidate_paths = base.get("candidate_paths", [])
        best_path = candidate_paths[0] if candidate_paths else []
        confidence = 0.90 if best_path else 0.62
        return [{
            "concept_family": self.family,
            "dynamic_concept": "path_finding",
            "activation_reason": "path_concept_requires_executable_route",
            "start_node": base.get("start_node"),
            "goal_node": base.get("goal_node"),
            "reachable_nodes": base.get("accessible_nodes", []),
            "blocked_nodes": base.get("blocked_nodes", []),
            "candidate_paths": candidate_paths,
            "best_path": best_path,
            "path_completion_strategy": "construct_shortest_accessible_path",
            "state_transitions": [
                "select_start_goal",
                "search_reachable_nodes",
                "construct_path",
            ],
            "candidate_transformation": {
                "operation": "construct_path",
                "path": best_path,
            },
            "simulation_plan": {
                "type": "path",
                "path": best_path,
            },
            "confidence": confidence,
        }]


path_reasoning = PathReasoning()


__all__ = ["PathReasoning", "path_reasoning"]
