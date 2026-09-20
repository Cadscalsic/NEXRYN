"""Gravity reasoning for dynamic ARC concepts."""

from __future__ import annotations

from typing import Any, Mapping


def _grid(grid):
    return [list(row) for row in (grid or [])]


def _shape(grid):
    grid = _grid(grid)
    return len(grid), len(grid[0]) if grid else 0


def _nonzero_cells(grid):
    cells = []
    for r, row in enumerate(_grid(grid)):
        for c, value in enumerate(row):
            if value:
                cells.append((r, c, value))
    return cells


class GravityReasoning:
    """Model falling, support, collision, and rest-state evidence."""

    family = "gravity"

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
        concept_signal = any(
            item in concepts
            for item in {"gravity", "gravity_simulation", "support", "falling"}
        )
        causal_families = set(
            (causal_context_report or {}).get("causal_families_detected", []) or []
        )
        if not concept_signal and "gravity_cause" not in causal_families:
            if not self._looks_like_downward_motion(input_grid, output_grid):
                return []

        simulation = self.simulate(input_grid)
        fall_distance = self._observed_fall_distance(input_grid, output_grid)
        support = self._support_relationships(input_grid)
        confidence = 0.72
        if fall_distance > 0:
            confidence += 0.16
        if support["unsupported_count"] > 0:
            confidence += 0.08
        if "gravity_cause" in causal_families:
            confidence += 0.04
        return [{
            "concept_family": self.family,
            "dynamic_concept": "gravity_simulation",
            "activation_reason": "unsupported_cells_or_gravity_causal_context",
            "support_relationships": support,
            "fall_distance": fall_distance,
            "landing_positions": self._landing_positions(simulation),
            "stable_states": self._stable_cells(simulation),
            "state_transitions": [
                "detect_support",
                "fall_until_support_or_boundary",
                "settle_rest_state",
            ],
            "candidate_transformation": {
                "operation": "translate",
                "dx": 0,
                "dy": fall_distance,
            },
            "simulation_plan": {
                "type": "gravity",
                "direction": "down",
                "until": "support_or_boundary",
            },
            "confidence": round(min(confidence, 1.0), 4),
        }]

    def simulate(self, input_grid):
        grid = _grid(input_grid)
        rows, cols = _shape(grid)
        if not rows or not cols:
            return grid
        out = [[0 for _ in range(cols)] for _ in range(rows)]
        for c in range(cols):
            landing = rows - 1
            for r in range(rows - 1, -1, -1):
                value = grid[r][c]
                if value:
                    out[landing][c] = value
                    landing -= 1
        return out

    def _support_relationships(self, input_grid):
        grid = _grid(input_grid)
        rows, _ = _shape(grid)
        supported = []
        unsupported = []
        for r, c, value in _nonzero_cells(grid):
            below = grid[r + 1][c] if r + 1 < rows else None
            record = {"row": r, "col": c, "color": value}
            if r == rows - 1 or below:
                supported.append({**record, "support": "boundary" if r == rows - 1 else below})
            else:
                unsupported.append(record)
        return {
            "supported_count": len(supported),
            "unsupported_count": len(unsupported),
            "supported_objects": supported,
            "unsupported_objects": unsupported,
        }

    def _looks_like_downward_motion(self, input_grid, output_grid):
        return self._observed_fall_distance(input_grid, output_grid) > 0

    def _observed_fall_distance(self, input_grid, output_grid):
        input_cells = _nonzero_cells(input_grid)
        output_cells = _nonzero_cells(output_grid)
        if not input_cells or len(input_cells) != len(output_cells):
            return 0
        input_cols = sorted((c, value) for _, c, value in input_cells)
        output_cols = sorted((c, value) for _, c, value in output_cells)
        if input_cols != output_cols:
            return 0
        input_min = min(r for r, _, _ in input_cells)
        output_min = min(r for r, _, _ in output_cells)
        return max(output_min - input_min, 0)

    def _landing_positions(self, simulated_grid):
        return [
            {"row": r, "col": c, "color": value}
            for r, c, value in _nonzero_cells(simulated_grid)
        ]

    def _stable_cells(self, simulated_grid):
        support = self._support_relationships(simulated_grid)
        return support["supported_objects"]


gravity_reasoning = GravityReasoning()


__all__ = ["GravityReasoning", "gravity_reasoning"]
