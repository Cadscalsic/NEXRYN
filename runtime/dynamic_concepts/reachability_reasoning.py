"""Reachability reasoning for dynamic ARC concepts."""

from __future__ import annotations

from collections import deque
from typing import Any, Mapping

from runtime.dynamic_concepts.gravity_reasoning import _grid, _shape


class ReachabilityReasoning:
    """Construct accessible/blocked node graphs and route feasibility."""

    family = "reachability"

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
        if not concepts.intersection({"path_finding", "route_completion", "reachability"}):
            causal_families = set((causal_context_report or {}).get("causal_families_detected", []) or [])
            if not causal_families.intersection({"path_cause", "bridge_cause"}):
                return []
        graph = self.build_graph(input_grid)
        starts = self._marker_positions(input_grid, runtime_context.get("start_colors", {2}))
        goals = self._marker_positions(input_grid, runtime_context.get("goal_colors", {3}))
        start = starts[0] if starts else self._first_accessible(graph)
        goal = goals[0] if goals else self._last_accessible(graph)
        path = self.shortest_path(graph, start, goal) if start and goal else []
        return [{
            "concept_family": self.family,
            "dynamic_concept": "reachability",
            "activation_reason": "path_or_bridge_concept_requires_route_feasibility",
            "start_node": start,
            "goal_node": goal,
            "accessible_nodes": sorted(graph["accessible_nodes"]),
            "blocked_nodes": sorted(graph["blocked_nodes"]),
            "connectivity_requirements": ["start_and_goal_must_be_connected"],
            "route_feasibility": bool(path),
            "completion_criteria": "reachable_path_exists",
            "candidate_paths": [path] if path else [],
            "state_transitions": [
                "build_reachability_graph",
                "evaluate_route_feasibility",
            ],
            "simulation_plan": {
                "type": "reachability",
                "start": start,
                "goal": goal,
            },
            "confidence": 0.88 if path else 0.64,
        }]

    def build_graph(self, input_grid):
        grid = _grid(input_grid)
        rows, cols = _shape(grid)
        accessible = set()
        blocked = set()
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 1:
                    blocked.add((r, c))
                else:
                    accessible.add((r, c))
        return {
            "accessible_nodes": accessible,
            "blocked_nodes": blocked,
            "neighbors": {
                node: [
                    nxt for nxt in self._neighbors(node, rows, cols)
                    if nxt in accessible
                ]
                for node in accessible
            },
        }

    def shortest_path(self, graph, start, goal):
        if start not in graph["accessible_nodes"] or goal not in graph["accessible_nodes"]:
            return []
        queue = deque([(start, [start])])
        seen = {start}
        while queue:
            node, path = queue.popleft()
            if node == goal:
                return path
            for nxt in graph["neighbors"].get(node, []):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, path + [nxt]))
        return []

    def _neighbors(self, node, rows, cols):
        r, c = node
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                yield (nr, nc)

    def _marker_positions(self, grid, colors):
        colors = set(colors or [])
        return [
            (r, c)
            for r, row in enumerate(_grid(grid))
            for c, value in enumerate(row)
            if value in colors
        ]

    def _first_accessible(self, graph):
        return sorted(graph["accessible_nodes"])[0] if graph["accessible_nodes"] else None

    def _last_accessible(self, graph):
        return sorted(graph["accessible_nodes"])[-1] if graph["accessible_nodes"] else None


reachability_reasoning = ReachabilityReasoning()


__all__ = ["ReachabilityReasoning", "reachability_reasoning"]
