"""Graph view for process semantic state transitions."""

from __future__ import annotations

from typing import Any

from runtime.process.process_state_model import ProcessSemanticContext


class ProcessTransitionGraph:
    system_name = "process_transition_graph"

    def build(self, context: ProcessSemanticContext) -> dict[str, Any]:
        initial_state = f"{context.concept}_pre_state"
        final_state = f"{context.concept}_post_state"
        transition_nodes = [
            f"{context.concept}_transition_{index + 1}"
            for index, _ in enumerate(context.transition_steps)
        ]
        nodes = [
            {
                "id": initial_state,
                "node_type": "state",
                "predicates": list(context.preconditions),
            },
            *[
                {
                    "id": node,
                    "node_type": "transition",
                    "transition_step": step,
                }
                for node, step in zip(transition_nodes, context.transition_steps)
            ],
            {
                "id": final_state,
                "node_type": "state",
                "predicates": list(context.postconditions),
            },
        ]
        sequence = [initial_state, *transition_nodes, final_state]
        edges = [
            {
                "source": source,
                "target": target,
                "relation": "precedes",
            }
            for source, target in zip(sequence, sequence[1:])
        ]
        return {
            "system": self.system_name,
            "concept": context.concept,
            "model": "STATE_TRANSITION_STATE",
            "temporal_reasoning_enabled": False,
            "nodes": nodes,
            "edges": edges,
            "initial_state": nodes[0],
            "transition_steps": list(context.transition_steps),
            "final_state": nodes[-1],
            "invariants": list(context.invariants),
            "temporal_constraints": list(context.temporal_constraints),
        }


__all__ = ["ProcessTransitionGraph"]
