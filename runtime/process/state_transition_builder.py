"""Build ordered state transitions from dependency graphs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


class StateTransitionBuilder:
    """Generate initial, intermediate, and terminal states from graph flow."""

    system_name = "state_transition_builder"

    STATE_LABELS = {
        "unsupported_object": "unsupported",
        "fall": "falling",
        "falling": "falling",
        "collision": "collision",
        "rest_state": "stable",
        "start": "start_identified",
        "reachable_nodes": "search_space_expanded",
        "candidate_paths": "path_selected",
        "goal": "goal_reached",
        "component_a": "components_disconnected",
        "component_A": "components_disconnected",
        "connector": "connector_introduced",
        "component_b": "bridge_formed",
        "component_B": "bridge_formed",
        "source_color": "source_color_observed",
        "mapping_rule": "mapping_rule_applied",
        "target_color": "target_color_produced",
    }

    def build(
        self,
        graph: Mapping[str, Any] | None = None,
        process_family: str = "multi_step_process",
    ) -> dict[str, Any]:
        graph = graph if isinstance(graph, Mapping) else {}
        ordered_nodes = self._normalize_process_flow(
            self._ordered_nodes(graph),
            process_family,
        )
        states = [
            self._state(node, index, len(ordered_nodes), process_family)
            for index, node in enumerate(ordered_nodes)
        ]
        transitions = []
        for index in range(len(states) - 1):
            source = states[index]
            target = states[index + 1]
            transitions.append({
                "transition_id": f"transition_{index}",
                "transition": (
                    f"{source['state_name']}->{target['state_name']}"
                ),
                "transition_type": self._transition_type(
                    source["raw_label"],
                    target["raw_label"],
                    process_family,
                ),
                "source_state": source["state_name"],
                "target_state": target["state_name"],
                "confidence": round(
                    min(
                        float(source.get("state_confidence", 0.0) or 0.0),
                        float(target.get("state_confidence", 0.0) or 0.0),
                    ),
                    4,
                ),
                "evidence": {
                    "source_node": source.get("source_node"),
                    "target_node": target.get("source_node"),
                    "process_family": process_family,
                },
            })
        transition_confidence = self._average(
            transition["confidence"] for transition in transitions
        )
        return {
            "system": self.system_name,
            "initial_state": states[0] if states else {},
            "intermediate_states": states[1:-1],
            "final_state": states[-1] if states else {},
            "states": states,
            "state_count": len(states),
            "transition_states": states[1:],
            "transitions": transitions,
            "transition_sequence": [
                transition["transition"]
                for transition in transitions
            ],
            "transition_count": len(transitions),
            "process_depth": max(len(states) - 1, 0),
            "state_confidence": self._average(
                state.get("state_confidence", 0.0)
                for state in states
            ),
            "transition_confidence": transition_confidence,
            "transition_ordering": [
                state["state_name"]
                for state in states
            ],
            "timestamp": str(datetime.utcnow()),
        }

    def _ordered_nodes(self, graph: Mapping[str, Any]) -> list[dict[str, Any]]:
        nodes = {
            str(node.get("id")): dict(node)
            for node in graph.get("nodes", []) or []
            if isinstance(node, Mapping) and node.get("id") is not None
        }
        edges = [
            dict(edge)
            for edge in graph.get("edges", []) or []
            if isinstance(edge, Mapping)
        ]
        adjacency: dict[str, list[str]] = {}
        incoming = set()
        for edge in edges:
            source = str(edge.get("source"))
            target = str(edge.get("target"))
            adjacency.setdefault(source, []).append(target)
            incoming.add(target)
        roots = [
            node_id
            for node_id, node in nodes.items()
            if node_id not in incoming
            and str(node.get("node_family") or node.get("type")) == "CONCEPT"
        ]
        if not roots:
            roots = [node_id for node_id in nodes if node_id not in incoming]
        ordered = []
        seen = set()

        def walk(node_id: str) -> None:
            if node_id in seen:
                return
            seen.add(node_id)
            node = nodes.get(node_id)
            if node and str(node.get("node_family") or node.get("type")) != "CONCEPT":
                ordered.append(node)
            for child in adjacency.get(node_id, []):
                walk(child)

        for root in roots:
            walk(root)
        if not ordered:
            ordered = [
                node
                for node in nodes.values()
                if str(node.get("node_family") or node.get("type")) != "CONCEPT"
            ]
        return ordered

    def _normalize_process_flow(self, ordered_nodes, process_family):
        if process_family != "gravity_process":
            return ordered_nodes
        labels = [
            str(node.get("label") or node.get("name") or node.get("id")).lower()
            for node in ordered_nodes
        ]
        if "collision" in labels:
            return ordered_nodes
        normalized = []
        for node in ordered_nodes:
            label = str(node.get("label") or node.get("name") or node.get("id"))
            normalized.append(node)
            if label.lower() in {"fall", "falling"}:
                synthetic = dict(node)
                synthetic["id"] = f"{node.get('id', 'gravity')}:collision"
                synthetic["label"] = "collision"
                synthetic["name"] = "collision"
                synthetic["node_family"] = "CONSTRAINT"
                synthetic["node_confidence"] = node.get("node_confidence", 0.82)
                normalized.append(synthetic)
        return normalized

    def _state(self, node, index, count, process_family):
        label = str(node.get("label") or node.get("name") or node.get("id"))
        canonical = self.STATE_LABELS.get(label, self.STATE_LABELS.get(label.lower()))
        state_name = canonical or label
        if index == 0:
            role = "initial_state"
        elif index == count - 1:
            role = "final_state"
        else:
            role = "intermediate_state"
        return {
            "state_id": index,
            "state_name": state_name,
            "raw_label": label,
            "state_role": role,
            "process_family": process_family,
            "state_confidence": round(
                float(
                    node.get(
                        "node_confidence",
                        node.get("confidence", 0.82),
                    )
                    or 0.0
                ),
                4,
            ),
            "source_node": node.get("id"),
        }

    def _transition_type(self, source, target, process_family):
        text = f"{source} {target} {process_family}".lower()
        if "path" in text or "goal" in text or "reachable" in text:
            return "path_constructed"
        if "bridge" in text or "connector" in text or "component" in text:
            return "bridge_created"
        if "color" in text or "mapping" in text:
            return "object_recolored"
        if "fall" in text or "gravity" in text or "support" in text:
            return "object_moved"
        if "rotation" in text:
            return "rotation_applied"
        if "reflection" in text:
            return "reflection_applied"
        return "dependency_step"

    def _average(self, values):
        numbers = [float(value or 0.0) for value in values]
        return round(sum(numbers) / len(numbers), 4) if numbers else 0.0


state_transition_builder = StateTransitionBuilder()


__all__ = ["StateTransitionBuilder", "state_transition_builder"]
