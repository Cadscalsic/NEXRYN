"""State graph builder for semantic process models."""

from __future__ import annotations

from typing import Any, Mapping


class ProcessStateGraph:
    system_name = "process_state_graph"

    def build(self, model: Mapping[str, Any]) -> dict[str, Any]:
        concept = str(model.get("concept", "process"))
        preconditions = list(model.get("preconditions", []) or [])
        transition_steps = list(model.get("transition_steps", []) or [])
        postconditions = list(model.get("postconditions", []) or [])
        nodes = [
            {
                "id": f"{concept}_initial_state",
                "node_type": "state",
                "predicates": preconditions,
            },
            *[
                {
                    "id": f"{concept}_transition_{index + 1}",
                    "node_type": "transition",
                    "transition_step": step,
                }
                for index, step in enumerate(transition_steps)
            ],
            {
                "id": f"{concept}_final_state",
                "node_type": "state",
                "predicates": postconditions,
            },
        ]
        return {
            "system": self.system_name,
            "concept": concept,
            "model": "STATE_TRANSITION_STATE",
            "temporal_reasoning_enabled": False,
            "nodes": nodes,
            "edges": [
                {
                    "source": source["id"],
                    "target": target["id"],
                    "relation": "unfolds_to",
                }
                for source, target in zip(nodes, nodes[1:])
            ],
            "preconditions": preconditions,
            "transition_steps": transition_steps,
            "postconditions": postconditions,
            "invariants": list(model.get("invariants", []) or []),
        }


__all__ = ["ProcessStateGraph"]
