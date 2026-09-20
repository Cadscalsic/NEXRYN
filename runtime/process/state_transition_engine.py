"""Infer state transition sequences from observations."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Mapping

import numpy as np


class StateTransitionEngine:
    """Model how observed state evolves between input and output."""

    system_name = "state_transition_engine"

    def infer(
        self,
        input_grid=None,
        output_grid=None,
        dependency_chain: Mapping[str, Any] | None = None,
        concepts: list[str] | None = None,
    ) -> dict[str, Any]:
        source = self._array(input_grid)
        target = self._array(output_grid)
        concepts = [str(item) for item in concepts or []]
        dependency_items = self._dependency_items(dependency_chain)

        transitions = []
        if source.size and target.size:
            transitions.extend(self._grid_transitions(source, target))
        transitions.extend(self._dependency_transitions(dependency_items))
        transitions.extend(self._concept_transitions(concepts))

        transitions = self._dedupe(transitions)
        states = self._states_from_transitions(transitions, dependency_items)
        confidence = self._confidence(transitions, source, target, dependency_items)
        report = {
            "system": self.system_name,
            "states": states,
            "state_count": len(states),
            "transition_sequence": [
                transition["transition"]
                for transition in transitions
            ],
            "transitions": transitions,
            "transition_count": len(transitions),
            "process_depth": max(len(states) - 1, 0),
            "transition_confidence": confidence,
            "timestamp": str(datetime.utcnow()),
        }
        return report

    def _grid_transitions(self, source, target):
        transitions = []
        if source.shape != target.shape:
            transitions.append(self._transition(
                "shape_changed",
                "grid_shape_modified",
                0.72,
                {
                    "input_shape": list(source.shape),
                    "output_shape": list(target.shape),
                },
            ))
            return transitions

        source_nonzero = source != 0
        target_nonzero = target != 0
        added = np.argwhere(target_nonzero & ~source_nonzero)
        removed = np.argwhere(source_nonzero & ~target_nonzero)
        changed = np.argwhere((source != target) & source_nonzero & target_nonzero)

        if len(added):
            transitions.append(self._transition(
                "object_added",
                "new_foreground_cells_created",
                min(0.95, 0.70 + len(added) / max(target.size, 1)),
                {"cell_count": int(len(added))},
            ))
        if len(removed):
            transitions.append(self._transition(
                "object_removed",
                "foreground_cells_removed",
                min(0.95, 0.70 + len(removed) / max(source.size, 1)),
                {"cell_count": int(len(removed))},
            ))
        if len(changed):
            mappings = Counter(
                (
                    int(source[row, col]),
                    int(target[row, col]),
                )
                for row, col in changed
            )
            transitions.append(self._transition(
                "object_recolored",
                "foreground_colors_reassigned",
                0.86,
                {
                    "mapping_votes": {
                        f"{old}->{new}": count
                        for (old, new), count in mappings.items()
                    },
                },
            ))

        movement = self._movement_transition(source, target)
        if movement:
            transitions.append(movement)

        if int(np.sum(target_nonzero)) > int(np.sum(source_nonzero)):
            transitions.append(self._transition(
                "object_expanded",
                "foreground_area_increased",
                0.78,
                {
                    "input_area": int(np.sum(source_nonzero)),
                    "output_area": int(np.sum(target_nonzero)),
                },
            ))

        if len(added) and self._added_cells_form_path(target, added):
            transitions.append(self._transition(
                "path_constructed",
                "added_cells_form_connected_route",
                0.84,
                {"added_cell_count": int(len(added))},
            ))
            transitions.append(self._transition(
                "bridge_created",
                "new_cells_connect_existing_regions",
                0.80,
                {"added_cell_count": int(len(added))},
            ))
        if len(added) and self._region_fill_like(source, target, added):
            transitions.append(self._transition(
                "region_filled",
                "empty_region_reassigned",
                0.79,
                {"filled_cell_count": int(len(added))},
            ))
        return transitions

    def _movement_transition(self, source, target):
        shifts = []
        for color in [int(item) for item in np.unique(source) if int(item) != 0]:
            if color not in np.unique(target):
                continue
            source_points = np.argwhere(source == color)
            target_points = np.argwhere(target == color)
            if len(source_points) != len(target_points) or not len(source_points):
                continue
            delta = tuple(
                np.rint(target_points.mean(axis=0) - source_points.mean(axis=0))
                .astype(int)
            )
            if delta != (0, 0):
                shifts.append(delta)
        if not shifts:
            return None
        delta, count = Counter(shifts).most_common(1)[0]
        return self._transition(
            "object_moved",
            "centroid_delta_applied",
            min(0.95, 0.78 + count * 0.04),
            {"delta": [int(delta[0]), int(delta[1])]},
        )

    def _dependency_transitions(self, dependency_items):
        transitions = []
        for index in range(len(dependency_items) - 1):
            transitions.append(self._transition(
                "dependency_step",
                f"{dependency_items[index]}->{dependency_items[index + 1]}",
                0.82,
                {
                    "source": dependency_items[index],
                    "target": dependency_items[index + 1],
                },
            ))
        return transitions

    def _concept_transitions(self, concepts):
        transitions = []
        for concept in concepts:
            token = concept.lower().replace("-", "_").replace(" ", "_")
            if "path" in token or "route" in token:
                transitions.append(self._transition(
                    "path_constructed",
                    "reachability_resolved",
                    0.82,
                    {"concept": token},
                ))
            elif "bridge" in token or "component_connection" in token:
                transitions.append(self._transition(
                    "bridge_created",
                    "components_connected",
                    0.82,
                    {"concept": token},
                ))
            elif "sequence" in token or "multi_step" in token:
                transitions.append(self._transition(
                    "sequence_applied",
                    "ordered_transforms_applied",
                    0.80,
                    {"concept": token},
                ))
            elif "relative" in token or "spatial_relation" in token:
                transitions.append(self._transition(
                    "object_moved",
                    "spatial_relation_updated",
                    0.78,
                    {"concept": token},
                ))
            elif "gravity" in token or "support" in token:
                transitions.append(self._transition(
                    "object_moved",
                    "support_constraint_changed",
                    0.83,
                    {"concept": token},
                ))
        return transitions

    def _states_from_transitions(self, transitions, dependency_items):
        states = []
        if dependency_items:
            states.append({
                "state_id": 0,
                "state_name": str(dependency_items[0]),
                "state_role": "initial_state",
            })
            for index, item in enumerate(dependency_items[1:-1], start=1):
                states.append({
                    "state_id": index,
                    "state_name": str(item),
                    "state_role": "intermediate_state",
                })
            if len(dependency_items) > 1:
                states.append({
                    "state_id": len(states),
                    "state_name": str(dependency_items[-1]),
                    "state_role": "final_state",
                })
        else:
            states.append({
                "state_id": 0,
                "state_name": "observed_input_state",
                "state_role": "initial_state",
            })
            for index, transition in enumerate(transitions[:-1], start=1):
                states.append({
                    "state_id": index,
                    "state_name": f"after_{transition['transition']}",
                    "state_role": "intermediate_state",
                })
            states.append({
                "state_id": len(states),
                "state_name": "observed_output_state",
                "state_role": "final_state",
            })
        return states

    def _transition(self, transition_type, transition, confidence, evidence):
        return {
            "transition_type": transition_type,
            "transition": transition,
            "confidence": round(float(confidence), 4),
            "evidence": dict(evidence or {}),
        }

    def _dedupe(self, transitions):
        seen = set()
        deduped = []
        for transition in transitions:
            key = (
                transition.get("transition_type"),
                transition.get("transition"),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(transition)
        return deduped

    def _confidence(self, transitions, source, target, dependency_items):
        if not transitions:
            return 0.0
        base = sum(item.get("confidence", 0.0) for item in transitions) / len(transitions)
        dependency_bonus = 0.08 if dependency_items else 0.0
        observation_bonus = 0.07 if source.size and target.size else 0.0
        return round(min(base + dependency_bonus + observation_bonus, 1.0), 4)

    def _dependency_items(self, dependency_chain):
        if isinstance(dependency_chain, Mapping):
            candidates = (
                dependency_chain.get("resolved_dependency_chain")
                or dependency_chain.get("chain")
                or dependency_chain.get("dependencies")
                or []
            )
        else:
            candidates = dependency_chain or []
        return [str(item) for item in candidates if item is not None]

    def _added_cells_form_path(self, target, added):
        if len(added) < 2:
            return False
        added_set = {tuple(map(int, point)) for point in added}
        neighbors = 0
        for row, col in added_set:
            for delta_row, delta_col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if (row + delta_row, col + delta_col) in added_set:
                    neighbors += 1
        return neighbors >= max(len(added_set) - 1, 1)

    def _region_fill_like(self, source, target, added):
        if len(added) < 3:
            return False
        rows = [int(point[0]) for point in added]
        cols = [int(point[1]) for point in added]
        area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
        return len(added) / max(area, 1) >= 0.6

    def _array(self, grid):
        if grid is None:
            return np.array([])
        if hasattr(grid, "grid"):
            return np.array(grid.grid)
        return np.array(grid)


state_transition_engine = StateTransitionEngine()


__all__ = [
    "StateTransitionEngine",
    "state_transition_engine",
]
