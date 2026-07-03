"""Dynamic topology reasoning for ARC concepts."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.dynamic_concepts.gravity_reasoning import _grid, _shape


class DynamicTopologyReasoning:
    """Model topology creation/destruction and connectivity evolution."""

    family = "dynamic_topology"

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
        before = self._component_count(input_grid)
        after = self._component_count(output_grid)
        topology_changed = before != after
        if not topology_changed and not concepts.intersection({
            "topology_change",
            "connectivity_change",
            "bridge_creation",
            "component_connection",
        }):
            return []
        if after < before:
            evolution = "region_merging"
        elif after > before:
            evolution = "region_splitting"
        else:
            evolution = "connectivity_evolution"
        return [{
            "concept_family": self.family,
            "dynamic_concept": "dynamic_topology",
            "activation_reason": "topology_or_connectivity_changes_require_evolution_model",
            "topology_creation": max(after - before, 0),
            "topology_destruction": max(before - after, 0),
            "connectivity_evolution": evolution,
            "bridge_formation": after < before,
            "region_merging": after < before,
            "region_splitting": after > before,
            "state_transitions": [
                "measure_components_before",
                "apply_connection_or_split",
                "measure_components_after",
            ],
            "candidate_transformation": {
                "operation": "connect_components" if after < before else "split_or_expand_region",
            },
            "simulation_plan": {
                "type": "dynamic_topology",
                "before_components": before,
                "after_components": after,
            },
            "confidence": 0.90 if topology_changed else 0.76,
        }]

    def _component_count(self, grid):
        grid = _grid(grid)
        rows, cols = _shape(grid)
        seen = set()
        count = 0
        for r in range(rows):
            for c in range(cols):
                if not grid[r][c] or (r, c) in seen:
                    continue
                count += 1
                stack = [(r, c)]
                seen.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if (
                            0 <= nr < rows
                            and 0 <= nc < cols
                            and grid[nr][nc]
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
        return count


dynamic_topology_reasoning = DynamicTopologyReasoning()


__all__ = ["DynamicTopologyReasoning", "dynamic_topology_reasoning"]
