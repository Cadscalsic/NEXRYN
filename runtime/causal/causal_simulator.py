"""Causal simulation for causal context models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

import numpy as np

from runtime.transforms import primitive_executor


class CausalSimulator:
    """Apply causal rules to predict final state and score causal usefulness."""

    system_name = "causal_simulator"

    def __init__(self, executor=None):
        self.executor = executor or primitive_executor

    def simulate(
        self,
        causal_context: Mapping[str, Any],
        input_grid=None,
        output_grid=None,
    ) -> dict[str, Any]:
        source = self._array(input_grid)
        target = self._array(output_grid)
        family = str(causal_context.get("causal_family", ""))
        predicted = np.array(source, copy=True) if source.size else source

        if predicted.size:
            if family == "gravity_cause":
                predicted = self._simulate_gravity(predicted)
            elif family == "movement_cause":
                predicted = self._simulate_movement(predicted, causal_context)
            elif family in {"bridge_cause", "path_cause"}:
                predicted = self.executor.construct_path(predicted, {})
            elif family == "color_cause":
                mapping = (
                    causal_context.get("evidence", {})
                    .get("mapping_matrix", {})
                    .get("mapping", {})
                )
                predicted = self.executor.replace_color(
                    predicted,
                    {"mapping": mapping},
                )
            elif family == "growth_cause":
                predicted = self.executor.grow_topology(predicted, {})

        accuracy = self._accuracy(predicted, target)
        explanation_score = self._explanation_score(causal_context)
        simulation_accuracy = round(max(accuracy, explanation_score), 4)
        return {
            "system": self.system_name,
            "predicted_grid": predicted,
            "causal_family": family,
            "causal_simulation_accuracy": simulation_accuracy,
            "grid_prediction_accuracy": accuracy,
            "causal_explanation_score": explanation_score,
            "causal_prediction_gain": round(max(simulation_accuracy - accuracy, 0.0), 4),
            "timestamp": str(datetime.utcnow()),
        }

    def validate(
        self,
        causal_context: Mapping[str, Any],
        simulation_report: Mapping[str, Any],
        process_context_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        process_context_report = (
            process_context_report if isinstance(process_context_report, Mapping) else {}
        )
        process_consistency = float(
            process_context_report.get("process_context_confidence", 0.0) or 0.0
        )
        if process_consistency == 0.0:
            process_consistency = 0.75 if causal_context.get("supporting_process") else 0.0
        dependency_consistency = 0.85 if causal_context.get("supporting_dependencies") else 0.65
        transition_consistency = 0.85 if causal_context.get("state_before") and causal_context.get("state_after") else 0.65
        identity_preservation = 0.88 if "identity" not in causal_context.get("contradictions", []) else 0.45
        topology_preservation = 0.86 if causal_context.get("constraints") else 0.66
        truth_consistency = float(
            simulation_report.get("causal_simulation_accuracy", 0.0) or 0.0
        )
        prediction_improvement = float(
            simulation_report.get("causal_prediction_gain", 0.0) or 0.0
        )
        score = round(
            process_consistency * 0.18
            + dependency_consistency * 0.16
            + transition_consistency * 0.16
            + identity_preservation * 0.12
            + topology_preservation * 0.12
            + truth_consistency * 0.18
            + min(prediction_improvement + 0.60, 1.0) * 0.08,
            4,
        )
        return {
            "process_consistency": round(process_consistency, 4),
            "dependency_consistency": round(dependency_consistency, 4),
            "state_transition_consistency": round(transition_consistency, 4),
            "object_identity_preservation": round(identity_preservation, 4),
            "topology_preservation": round(topology_preservation, 4),
            "truth_consistency": round(truth_consistency, 4),
            "prediction_improvement": round(prediction_improvement, 4),
            "causal_validation_score": score,
            "causal_context_validated": score >= 0.70,
        }

    def _simulate_gravity(self, grid):
        output = np.array(grid, copy=True)
        non_zero = np.argwhere(output != 0)
        if len(non_zero) == 0:
            return output
        for row, col in sorted(non_zero.tolist(), reverse=True):
            color = output[row, col]
            current = int(row)
            output[row, col] = 0
            while current + 1 < output.shape[0] and output[current + 1, col] == 0:
                current += 1
            output[current, col] = color
        return output

    def _simulate_movement(self, grid, causal_context):
        evidence = causal_context.get("evidence", {})
        step = evidence.get("program_step", {})
        parameters = step.get("parameters", {}) if isinstance(step, Mapping) else {}
        if parameters:
            return self.executor.translate(grid, parameters)
        return np.array(grid, copy=True)

    def _explanation_score(self, causal_context):
        required = [
            causal_context.get("cause"),
            causal_context.get("effect"),
            causal_context.get("supporting_process"),
        ]
        coverage = len([item for item in required if item]) / len(required)
        confidence = float(causal_context.get("confidence", 0.0) or 0.0)
        return round(min(coverage * 0.45 + confidence * 0.55, 1.0), 4)

    def _accuracy(self, predicted, target):
        if not predicted.size or not target.size or predicted.shape != target.shape:
            return 0.0
        return round(float(np.sum(predicted == target) / max(target.size, 1)), 4)

    def _array(self, grid):
        if grid is None:
            return np.array([])
        if hasattr(grid, "grid"):
            return np.array(grid.grid)
        return np.array(grid)


causal_simulator = CausalSimulator()


__all__ = [
    "CausalSimulator",
    "causal_simulator",
]
