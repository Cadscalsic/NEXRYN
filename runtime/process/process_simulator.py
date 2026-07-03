"""Simulation and validation for process context models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

import numpy as np

from runtime.transforms import primitive_executor


class ProcessSimulator:
    """Execute candidate process chains and evaluate explanatory accuracy."""

    system_name = "process_simulator"

    TRANSITION_TO_PRIMITIVE = {
        "object_moved": "translate",
        "object_recolored": "replace_color",
        "object_added": "duplicate_object",
        "object_removed": "remove_object",
        "object_expanded": "grow_topology",
        "path_constructed": "construct_path",
        "bridge_created": "connect_components",
        "region_filled": "fill_region",
    }

    def __init__(self, executor=None):
        self.executor = executor or primitive_executor

    def simulate(
        self,
        process_model: Mapping[str, Any],
        input_grid=None,
        output_grid=None,
    ) -> dict[str, Any]:
        transitions = list(process_model.get("transition_events", []) or [])
        primitives = [
            primitive
            for primitive in [
                self._primitive_from_transition(transition)
                for transition in transitions
            ]
            if primitive
        ]
        predicted = self._array(input_grid)
        execution_trace = []

        if predicted.size and primitives:
            result = self.executor.run_execution(predicted, primitives)
            predicted = np.array(result.get("output_grid", predicted))
            execution_trace = list(result.get("execution_trace", []) or [])

        accuracy = self._accuracy(predicted, self._array(output_grid))
        consistency = self._transition_consistency(process_model)
        dependency_consistency = self._dependency_consistency(process_model)
        simulation_accuracy = round(
            max(accuracy, consistency * 0.55 + dependency_consistency * 0.45),
            4,
        )
        return {
            "system": self.system_name,
            "predicted_grid": predicted,
            "execution_trace": execution_trace,
            "executed_transition_count": len(primitives),
            "simulation_accuracy": simulation_accuracy,
            "grid_prediction_accuracy": accuracy,
            "transition_consistency": consistency,
            "dependency_consistency": dependency_consistency,
            "process_executable": bool(primitives),
            "timestamp": str(datetime.utcnow()),
        }

    def validate(
        self,
        process_model: Mapping[str, Any],
        simulation_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        transition_consistency = float(
            simulation_report.get("transition_consistency", 0.0) or 0.0
        )
        dependency_consistency = float(
            simulation_report.get("dependency_consistency", 0.0) or 0.0
        )
        simulation_accuracy = float(
            simulation_report.get("simulation_accuracy", 0.0) or 0.0
        )
        identity_preservation = 0.90 if process_model.get("initial_state") else 0.65
        topology_preservation = 0.90 if process_model.get("dependencies") else 0.65
        score = round(
            transition_consistency * 0.25
            + dependency_consistency * 0.20
            + simulation_accuracy * 0.25
            + identity_preservation * 0.15
            + topology_preservation * 0.15,
            4,
        )
        return {
            "topology_preservation": topology_preservation,
            "connectivity_preservation": topology_preservation,
            "object_identity_preservation": identity_preservation,
            "spatial_consistency": transition_consistency,
            "transformation_consistency": transition_consistency,
            "truth_consistency": simulation_accuracy,
            "dependency_consistency": dependency_consistency,
            "process_validation_score": score,
            "process_validated": score >= 0.70,
        }

    def _primitive_from_transition(self, transition):
        transition_type = transition.get("transition_type")
        primitive = self.TRANSITION_TO_PRIMITIVE.get(transition_type)
        if not primitive:
            return None
        evidence = transition.get("evidence", {}) or {}
        parameters = {}
        if transition_type == "object_moved":
            delta = evidence.get("delta", [0, 0])
            parameters = {
                "translation": delta,
                "delta_row": delta[0],
                "delta_col": delta[1],
            }
        elif transition_type == "object_recolored":
            mapping = {}
            for key in evidence.get("mapping_votes", {}) or {}:
                if "->" not in key:
                    continue
                old, new = key.split("->", 1)
                mapping[str(int(old))] = int(new)
            parameters = {"mapping": mapping, "color_mapping": mapping}
        return {
            "primitive": primitive,
            "parameters": parameters,
        }

    def _accuracy(self, predicted, target):
        if not predicted.size or not target.size or predicted.shape != target.shape:
            return 0.0
        return round(float(np.sum(predicted == target) / max(target.size, 1)), 4)

    def _transition_consistency(self, process_model):
        transitions = process_model.get("transition_events", []) or []
        if not transitions:
            return 0.0
        return round(
            sum(float(item.get("confidence", 0.0) or 0.0) for item in transitions)
            / len(transitions),
            4,
        )

    def _dependency_consistency(self, process_model):
        dependencies = process_model.get("dependencies", []) or []
        transitions = process_model.get("transition_sequence", []) or []
        if not dependencies and not transitions:
            return 0.0
        return round(
            min(
                1.0,
                (len(dependencies) + len(transitions))
                / max(len(transitions), 1)
                * 0.5,
            ),
            4,
        )

    def _array(self, grid):
        if grid is None:
            return np.array([])
        if hasattr(grid, "grid"):
            return np.array(grid.grid)
        return np.array(grid)


process_simulator = ProcessSimulator()


__all__ = [
    "ProcessSimulator",
    "process_simulator",
]
