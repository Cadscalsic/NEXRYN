"""State-evolution reasoning for dynamic ARC concepts."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.dynamic_concepts.gravity_reasoning import _grid, _shape


class StateEvolutionReasoning:
    """Represent initial, intermediate, terminal, and constrained states."""

    family = "state_evolution"

    def reason(
        self,
        input_grid=None,
        output_grid=None,
        causal_context_report: Mapping[str, Any] | None = None,
        process_context_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        transitions = self.transitions(input_grid, output_grid)
        if not transitions:
            concepts = set(str(item) for item in (runtime_context or {}).get("detected_concepts", []) or [])
            if "state_evolution" not in concepts and "transformation_sequence" not in concepts:
                return []
        return [{
            "concept_family": self.family,
            "dynamic_concept": "state_evolution",
            "activation_reason": "input_output_state_delta_requires_temporal_model",
            "initial_state": {"grid": _grid(input_grid)},
            "intermediate_states": self._intermediate_states(input_grid, transitions),
            "terminal_state": {"grid": _grid(output_grid)},
            "state_constraints": [
                "preserve_grid_bounds",
                "apply_observed_cell_deltas",
            ],
            "state_transitions": [item["transition"] for item in transitions],
            "transition_events": transitions,
            "simulation_plan": {
                "type": "state_evolution",
                "events": transitions,
            },
            "confidence": min(0.70 + 0.02 * len(transitions), 0.94),
        }]

    def transitions(self, input_grid, output_grid):
        ing = _grid(input_grid)
        outg = _grid(output_grid)
        rows, cols = _shape(outg or ing)
        transitions = []
        for r in range(rows):
            for c in range(cols):
                before = ing[r][c] if r < len(ing) and c < len(ing[r]) else 0
                after = outg[r][c] if r < len(outg) and c < len(outg[r]) else 0
                if before == after:
                    continue
                if before == 0 and after:
                    name = "object_added"
                elif before and after == 0:
                    name = "object_removed"
                elif before and after and before != after:
                    name = "object_recolored"
                else:
                    name = "state_changed"
                transitions.append({
                    "transition": name,
                    "row": r,
                    "col": c,
                    "before": before,
                    "after": after,
                })
        return transitions

    def _intermediate_states(self, input_grid, transitions):
        grid = _grid(input_grid)
        states = []
        for event in transitions[:4]:
            if not grid:
                break
            grid = [list(row) for row in grid]
            grid[event["row"]][event["col"]] = event["after"]
            states.append({
                "applied_transition": event["transition"],
                "grid": [list(row) for row in grid],
            })
        return states


state_evolution_reasoning = StateEvolutionReasoning()


__all__ = ["StateEvolutionReasoning", "state_evolution_reasoning"]
