"""Support-structure reasoning for dynamic ARC concepts."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.dynamic_concepts.gravity_reasoning import _grid, _nonzero_cells, _shape


class SupportReasoning:
    """Build support providers, supported objects, stacks, and stability conditions."""

    family = "support"

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
        rows, _ = _shape(input_grid)
        if not rows:
            return []
        stacks = self._dependency_stacks(input_grid)
        if not stacks and "support" not in concepts and "gravity" not in concepts:
            return []
        stable = sum(1 for stack in stacks if stack.get("stable"))
        confidence = min(0.70 + 0.05 * stable, 0.96)
        return [{
            "concept_family": self.family,
            "dynamic_concept": "support_structure",
            "activation_reason": "vertical_support_or_gravity_context",
            "support_providers": [stack["provider"] for stack in stacks if stack.get("provider")],
            "supported_objects": [stack["object"] for stack in stacks],
            "dependency_stacks": stacks,
            "load_chains": [
                [stack["object"], stack.get("provider", "boundary")]
                for stack in stacks
            ],
            "stability_conditions": [
                "object_has_support_below_or_boundary",
                "unsupported_object_requires_gravity_resolution",
            ],
            "state_transitions": [
                "evaluate_support",
                "resolve_stability",
            ],
            "simulation_plan": {
                "type": "support",
                "operation": "validate_stability",
            },
            "confidence": round(confidence, 4),
        }]

    def _dependency_stacks(self, input_grid):
        grid = _grid(input_grid)
        rows, _ = _shape(grid)
        stacks = []
        for r, c, value in _nonzero_cells(grid):
            below = grid[r + 1][c] if r + 1 < rows else None
            provider = "boundary" if r == rows - 1 else (
                {"row": r + 1, "col": c, "color": below} if below else None
            )
            stacks.append({
                "object": {"row": r, "col": c, "color": value},
                "provider": provider,
                "stable": bool(provider),
            })
        return stacks


support_reasoning = SupportReasoning()


__all__ = ["SupportReasoning", "support_reasoning"]
