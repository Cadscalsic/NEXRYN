"""Propagation reasoning for dynamic ARC concepts."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.dynamic_concepts.gravity_reasoning import _grid, _nonzero_cells, _shape


class PropagationReasoning:
    """Model origins, frontiers, spread directions, and affected regions."""

    family = "propagation"

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
        added = self._added_cells(input_grid, output_grid)
        if "propagation" not in concepts and not added:
            return []
        origin = self._origin(input_grid)
        frontier = self._frontier(input_grid)
        depth = max(
            [abs(r - origin[0]) + abs(c - origin[1]) for r, c, _ in added]
            or [0]
        ) if origin else 0
        confidence = min(0.68 + 0.04 * len(added), 0.95)
        return [{
            "concept_family": self.family,
            "dynamic_concept": "propagation",
            "activation_reason": "new_cells_expand_from_existing_region",
            "origin": origin,
            "spread_direction": self._spread_direction(origin, added),
            "expansion_frontier": frontier,
            "affected_regions": [
                {"row": r, "col": c, "color": value}
                for r, c, value in added
            ],
            "propagation_depth": depth,
            "state_transitions": [
                "identify_origin",
                "expand_frontier",
                "mark_affected_region",
            ],
            "candidate_transformation": {
                "operation": "expand_region",
                "depth": depth,
            },
            "simulation_plan": {
                "type": "propagation",
                "origin": origin,
                "depth": depth,
            },
            "confidence": round(confidence, 4),
        }]

    def _added_cells(self, input_grid, output_grid):
        ing = _grid(input_grid)
        outg = _grid(output_grid)
        rows, cols = _shape(outg)
        added = []
        for r in range(rows):
            for c in range(cols):
                before = ing[r][c] if r < len(ing) and c < len(ing[r]) else 0
                after = outg[r][c]
                if before == 0 and after:
                    added.append((r, c, after))
        return added

    def _origin(self, input_grid):
        cells = _nonzero_cells(input_grid)
        if not cells:
            return None
        r = round(sum(cell[0] for cell in cells) / len(cells))
        c = round(sum(cell[1] for cell in cells) / len(cells))
        return (r, c)

    def _frontier(self, input_grid):
        grid = _grid(input_grid)
        rows, cols = _shape(grid)
        frontier = []
        for r, c, value in _nonzero_cells(grid):
            if any(
                0 <= r + dr < rows
                and 0 <= c + dc < cols
                and grid[r + dr][c + dc] == 0
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                frontier.append({"row": r, "col": c, "color": value})
        return frontier

    def _spread_direction(self, origin, added):
        if not origin or not added:
            return "undetermined"
        dr = sum(r - origin[0] for r, _, _ in added)
        dc = sum(c - origin[1] for _, c, _ in added)
        if abs(dr) >= abs(dc):
            return "down" if dr > 0 else "up" if dr < 0 else "balanced"
        return "right" if dc > 0 else "left"


propagation_reasoning = PropagationReasoning()


__all__ = ["PropagationReasoning", "propagation_reasoning"]
