"""Isolated candidate simulation for arena comparison."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping

import numpy as np

from runtime.arena.executor_contract import (
    EXECUTOR_CONTRACT_ID,
    EXECUTOR_CONTRACT_VERSION,
)


class CandidateSimulator:
    """Execute candidate programs only against isolated grid copies."""

    system_name = "candidate_simulator"
    EXECUTOR_CONTRACT_ID = EXECUTOR_CONTRACT_ID
    EXECUTOR_CONTRACT_VERSION = EXECUTOR_CONTRACT_VERSION

    def simulate(
        self,
        candidate: Mapping[str, Any],
        input_grid: Any = None,
        target_grid: Any = None,
    ) -> dict[str, Any]:
        candidate_id = candidate.get("candidate_id")
        source = self._array(input_grid)
        target = self._array(target_grid)
        working = source.copy()
        prediction_timestamp = datetime.now(timezone.utc).isoformat()
        predicted_cells, applicability = self._predicted_localization(
            candidate, source
        )
        trace = []
        unsupported = []
        errors = []
        for index, step in enumerate(candidate.get("program", {}).get("steps", []) or []):
            if not isinstance(step, Mapping):
                unsupported.append({"index": index, "operation": None, "reason": "step_not_mapping"})
                continue
            operation = str(step.get("operation") or "").strip().lower()
            parameters = step.get("parameters") if isinstance(step.get("parameters"), Mapping) else {}
            before = working.copy()
            try:
                working, supported = self._execute(working, operation, parameters)
                if not supported:
                    unsupported.append({"index": index, "operation": operation, "reason": "unsupported_operation"})
                trace.append({
                    "step_index": index,
                    "operation": operation,
                    "supported": supported,
                    "input_shape": list(before.shape),
                    "output_shape": list(working.shape),
                })
            except Exception as error:
                errors.append({"index": index, "operation": operation, "error": repr(error)})
        metrics = self._metrics(source, working, target)
        localization_observation = self._localization_observation(
            candidate,
            source,
            target,
            predicted_cells,
            applicability,
            prediction_timestamp,
        )
        return {
            "system": self.system_name,
            "candidate_id": candidate_id,
            "simulation_success": not errors and not unsupported,
            "predicted_output": working.tolist() if working.size else [],
            "execution_trace": trace,
            "prediction_accuracy": metrics["prediction_accuracy"],
            "difference_count": metrics["difference_count"],
            "structural_score": metrics["structural_score"],
            "color_score": metrics["color_score"],
            "object_score": metrics["object_score"],
            "topology_score": metrics["topology_score"],
            "unsupported_steps": unsupported,
            "simulation_errors": errors,
            "localization_observation": localization_observation,
        }

    def _predicted_localization(self, candidate, source):
        if source.size == 0:
            return set(), "OBSERVATION_UNAVAILABLE"
        predicted = set()
        applicable = False
        for step in candidate.get("program", {}).get("steps", []) or []:
            if not isinstance(step, Mapping):
                continue
            operation = str(step.get("operation") or "").strip().lower()
            parameters = step.get("parameters") if isinstance(step.get("parameters"), Mapping) else {}
            explicit = parameters.get("affected_positions") or []
            if explicit:
                predicted.update((int(row), int(col)) for row, col in explicit)
                applicable = True
            elif operation in {"construct_path", "connect_components"}:
                predicted.update((int(row), int(col)) for row, col in parameters.get("path_cells", []) or [])
                applicable = True
            elif operation == "duplicate_object":
                predicted.update((int(cell.get("row", 0)), int(cell.get("col", 0))) for cell in parameters.get("cells_to_write", []) or [] if isinstance(cell, Mapping))
                applicable = True
            elif operation == "remove_object":
                predicted.update((int(row), int(col)) for row, col in parameters.get("cells_to_clear", []) or [])
                for color in parameters.get("remove_colors", []) or []:
                    predicted.update(map(tuple, np.argwhere(source == int(color)).tolist()))
                applicable = True
            elif operation in {"replace_color", "recolor"}:
                mapping = parameters.get("color_mapping") or {}
                if not mapping and "source_color" in parameters and "target_color" in parameters:
                    mapping = {parameters["source_color"]: parameters["target_color"]}
                for source_color, target_color in mapping.items():
                    if int(source_color) != int(target_color):
                        predicted.update(map(tuple, np.argwhere(source == int(source_color)).tolist()))
                applicable = True
            elif operation in {"preserve_grid", "noop"}:
                applicable = True
            elif operation in {"translate", "rotate", "mirror_horizontal", "mirror_vertical", "mirror_object"}:
                predicted.update(map(tuple, np.ndindex(source.shape)))
                applicable = True
        return predicted, (
            "SPATIAL_LOCALIZATION_APPLICABLE"
            if applicable
            else "NON_LOCALIZABLE_OPERATION"
        )

    def _localization_observation(self, candidate, source, target, predicted, applicability, prediction_timestamp):
        observation_timestamp = datetime.now(timezone.utc).isoformat()
        universe = set(map(tuple, np.ndindex(source.shape))) if source.size else set()
        if target.size == 0 or source.shape != target.shape:
            applicability = "OBSERVATION_UNAVAILABLE"
            observed = set()
        else:
            observed = set(map(tuple, np.argwhere(source != target).tolist()))
        predicted = {cell for cell in predicted if cell in universe}
        payload = {
            "observation_id": "localization_observation_" + hashlib.sha256(json.dumps([candidate.get("candidate_id"), prediction_timestamp, sorted(predicted)], default=str).encode()).hexdigest()[:16],
            "schema_version": "candidate_localization_observation.v1",
            "candidate_id": candidate.get("candidate_id"),
            "candidate_fingerprint": candidate.get("candidate_fingerprint"),
            "operation_id": candidate.get("operation"),
            "run_id": candidate.get("run_id"),
            "task_id": candidate.get("task_id"),
            "execution_plan_id": candidate.get("execution_plan_id"),
            "prediction_timestamp": prediction_timestamp,
            "observation_timestamp": observation_timestamp,
            "predicted_affected_cells": [list(cell) for cell in sorted(predicted)],
            "predicted_preserved_cells": [list(cell) for cell in sorted(universe - predicted)],
            "observed_affected_cells": [list(cell) for cell in sorted(observed)],
            "observed_preserved_cells": [list(cell) for cell in sorted(universe - observed)],
            "false_positive_cells": [list(cell) for cell in sorted(predicted - observed)],
            "missed_cells": [list(cell) for cell in sorted(observed - predicted)],
            "comparison_method": "AFFECTED_REGION_JACCARD",
            "applicability_state": applicability,
            "coverage": 1.0 if applicability == "SPATIAL_LOCALIZATION_APPLICABLE" else 0.0,
            "provenance": "candidate_semantics_prediction_then_independent_task_target_observation",
            "producer_identity": self.system_name,
            "independence_state": "INDEPENDENT_TASK_TARGET",
            "provenance_verified": applicability == "SPATIAL_LOCALIZATION_APPLICABLE",
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
        }
        payload["immutable_fingerprint"] = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str, separators=(",", ":")).encode()).hexdigest()
        return payload

    def _execute(self, grid: np.ndarray, operation: str, parameters: Mapping[str, Any]) -> tuple[np.ndarray, bool]:
        output = grid.copy()
        if operation in {
            "preserve_grid",
            "preserve_colors",
            "preserve_topology",
            "preserve_shape",
            "preserve_size",
            "preserve_density",
            "preserve_symmetry",
            "noop",
        }:
            return output, True
        if operation in {"replace_color", "recolor"}:
            mapping = parameters.get("color_mapping") or {}
            if not mapping and "source_color" in parameters and "target_color" in parameters:
                mapping = {parameters["source_color"]: parameters["target_color"]}
            affected_positions = parameters.get("affected_positions") or []
            if affected_positions:
                normalized_mapping = {
                    int(source_color): int(target_color)
                    for source_color, target_color in mapping.items()
                }
                for row, col in affected_positions:
                    row = int(row)
                    col = int(col)
                    if 0 <= row < output.shape[0] and 0 <= col < output.shape[1]:
                        source_color = int(grid[row, col])
                        if source_color in normalized_mapping:
                            output[row, col] = normalized_mapping[source_color]
                return output, True
            for source_color, target_color in mapping.items():
                output[grid == int(source_color)] = int(target_color)
            return output, True
        if operation == "construct_path" or operation == "connect_components":
            color = int(parameters.get("path_color", parameters.get("fill_color", 1)))
            for row, col in parameters.get("path_cells", []) or []:
                if 0 <= int(row) < output.shape[0] and 0 <= int(col) < output.shape[1]:
                    output[int(row), int(col)] = color
            return output, True
        if operation == "remove_object":
            background = int(parameters.get("background_color", 0))
            for row, col in parameters.get("cells_to_clear", []) or []:
                if 0 <= int(row) < output.shape[0] and 0 <= int(col) < output.shape[1]:
                    output[int(row), int(col)] = background
            for color in parameters.get("remove_colors", []) or []:
                output[output == int(color)] = background
            return output, True
        if operation == "duplicate_object":
            for cell in parameters.get("cells_to_write", []) or []:
                row = int(cell.get("row", 0))
                col = int(cell.get("col", 0))
                if 0 <= row < output.shape[0] and 0 <= col < output.shape[1]:
                    output[row, col] = int(cell.get("value", output[row, col]))
            return output, True
        if operation == "translate":
            delta_row = int(parameters.get("delta_row", parameters.get("translation", [0, 0])[0] if parameters.get("translation") else 0))
            delta_col = int(parameters.get("delta_col", parameters.get("translation", [0, 0])[1] if parameters.get("translation") else 0))
            translated = np.zeros_like(output)
            rows, cols = np.nonzero(output)
            for row, col in zip(rows, cols):
                target_row = row + delta_row
                target_col = col + delta_col
                if 0 <= target_row < output.shape[0] and 0 <= target_col < output.shape[1]:
                    translated[target_row, target_col] = output[row, col]
            return translated, True
        if operation == "rotate":
            degrees = int(parameters.get("degrees", 90))
            return np.rot90(output, k=(degrees // 90) % 4), True
        if operation in {"mirror_horizontal", "mirror_object"}:
            return np.fliplr(output), True
        if operation == "mirror_vertical":
            return np.flipud(output), True
        return output, False

    def _metrics(self, source: np.ndarray, predicted: np.ndarray, target: np.ndarray) -> dict[str, Any]:
        if target.size == 0 or predicted.shape != target.shape:
            accuracy = 0.0
            difference_count = int(target.size or predicted.size)
        else:
            difference_count = int(np.sum(predicted != target))
            accuracy = float(np.sum(predicted == target) / max(target.size, 1))
        structural_score = 1.0 if target.size and predicted.shape == target.shape else 0.0
        color_score = self._color_score(predicted, target)
        object_score = self._object_score(predicted, target)
        topology_score = self._topology_score(predicted, target)
        return {
            "prediction_accuracy": round(accuracy, 4),
            "difference_count": difference_count,
            "structural_score": round(structural_score, 4),
            "color_score": round(color_score, 4),
            "object_score": round(object_score, 4),
            "topology_score": round(topology_score, 4),
        }

    def _color_score(self, predicted: np.ndarray, target: np.ndarray) -> float:
        if predicted.size == 0 or target.size == 0:
            return 0.0
        return len(set(predicted.flatten()) & set(target.flatten())) / max(len(set(target.flatten())), 1)

    def _object_score(self, predicted: np.ndarray, target: np.ndarray) -> float:
        if predicted.size == 0 or target.size == 0 or predicted.shape != target.shape:
            return 0.0
        pred_nonzero = predicted != 0
        target_nonzero = target != 0
        union = np.logical_or(pred_nonzero, target_nonzero)
        if not np.any(union):
            return 1.0
        return float(np.sum(np.logical_and(pred_nonzero, target_nonzero)) / np.sum(union))

    def _topology_score(self, predicted: np.ndarray, target: np.ndarray) -> float:
        return self._object_score(predicted, target)

    def _array(self, grid: Any) -> np.ndarray:
        if grid is None:
            return np.array([])
        if hasattr(grid, "grid"):
            return np.array(grid.grid)
        return np.array(deepcopy(grid))


candidate_simulator = CandidateSimulator()

__all__ = ["CandidateSimulator", "candidate_simulator"]
