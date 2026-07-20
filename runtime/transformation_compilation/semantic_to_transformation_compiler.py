"""Compile semantic concepts into executable transformation programs.

This layer is deliberately narrow: it does not discover new concepts and it does
not alter cognitive execution. It turns already-detected semantic intent plus
observed grid deltas into explicit primitive parameters.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Mapping

import numpy as np


class SemanticToTransformationCompiler:
    """Bridge semantic attribution and concrete transformation execution."""

    system_name = "semantic_to_transformation_compiler"

    PATH_CONCEPTS = {
        "path_finding",
        "route_completion",
        "reachability",
        "path_construction",
        "bridge_creation",
        "component_connection",
        "connectivity_change",
    }
    SCALING_CONCEPTS = {
        "scaling",
        "scale_transformation",
        "size_transformation",
        "density_increase",
    }
    FILTER_CONCEPTS = {
        "noise_removal",
        "artifact_filtering",
        "object_removal",
        "color_elimination",
    }
    ROTATION_CONCEPTS = {
        "rotation",
        "rotation_reflection",
        "orientation_change",
    }
    REFLECTION_CONCEPTS = {
        "reflection",
        "rotation_reflection",
        "symmetry_creation",
    }
    TOPOLOGY_REPAIR_CONCEPTS = {
        "hole_removal",
        "topology_repair",
        "connectivity_restoration",
        "topology_change",
    }
    COLOR_PRESERVATION_CONCEPTS = {
        "color_preservation",
        "preserve_color_mapping",
    }
    COLOR_REMAP_CONCEPTS = {
        "color_mapping",
        "symbolic_remapping",
        "replace_color_mapping",
        "remap_symbols",
    }
    DUPLICATION_CONCEPTS = {
        "replication",
        "duplication",
        "object_creation",
        "duplicate_object",
        "growth",
        "topological_growth",
        "propagation",
    }
    GRID_PRESERVATION_CONCEPTS = {
        "object_identity_preservation",
        "position_preservation",
        "shape_preservation",
        "size_preservation",
    }
    TOPOLOGY_PRESERVATION_CONCEPTS = {
        "topology_preservation",
        "preserve_topology",
    }

    def compile(
        self,
        input_grid=None,
        output_grid=None,
        detected_concepts: list[str] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        execution_intents: list[Mapping[str, Any]] | None = None,
        semantic_intent_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        input_grid = input_grid if input_grid is not None else runtime_context.get("input_grid")
        output_grid = output_grid if output_grid is not None else runtime_context.get("output_grid")
        if output_grid is None:
            output_grid = runtime_context.get("target_grid")

        execution_intents = list(execution_intents or runtime_context.get("execution_intents") or [])
        concept_values = list(detected_concepts or runtime_context.get("detected_concepts") or [])
        for intent in execution_intents:
            if isinstance(intent, Mapping):
                concept_values.append(str(intent.get("intent", "")))
                concept_values.extend(str(item) for item in intent.get("matched_concepts", []) or [])
        concepts = set(item for item in concept_values if item)
        source = self._array(input_grid)
        target = self._array(output_grid)

        if source.size == 0 or target.size == 0:
            return self._empty_report(
                concepts,
                "missing_grid_pair",
                execution_intents=execution_intents,
                semantic_intent_report=semantic_intent_report,
            )

        candidates = []
        if concepts.intersection(self.ROTATION_CONCEPTS) or self._has_intent(execution_intents, {"rotation", "rotation_reflection"}):
            candidates.extend(self._compile_rotation(source, target, execution_intents))
        if concepts.intersection(self.REFLECTION_CONCEPTS) or self._has_intent(execution_intents, {"reflection", "rotation_reflection"}):
            candidates.extend(self._compile_reflection(source, target))
        if concepts.intersection(self.SCALING_CONCEPTS):
            candidate = self._compile_scaling(source, target)
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.PATH_CONCEPTS):
            candidate = self._compile_path(source, target, concepts)
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.FILTER_CONCEPTS):
            candidate = self._compile_filter(source, target)
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.TOPOLOGY_REPAIR_CONCEPTS) or self._has_intent(execution_intents, {"topology_repair"}):
            candidate = self._compile_topology_repair(source, target)
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.COLOR_PRESERVATION_CONCEPTS) or self._has_intent(execution_intents, {"preserve_color_mapping"}):
            candidate = self._compile_preservation(source, target, "color_preservation", "preserve_colors")
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.TOPOLOGY_PRESERVATION_CONCEPTS) or self._has_intent(execution_intents, {"preserve_topology"}):
            candidate = self._compile_preservation(source, target, "topology_preservation", "preserve_topology")
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.GRID_PRESERVATION_CONCEPTS) or self._has_intent(execution_intents, {"preserve_grid", "object_identity_preservation"}):
            candidate = self._compile_preservation(source, target, "grid_preservation", "preserve_grid")
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.COLOR_REMAP_CONCEPTS) or self._has_intent(execution_intents, {"replace_color_mapping", "remap_symbols"}):
            candidate = self._compile_color_remap(source, target)
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.DUPLICATION_CONCEPTS) or self._has_intent(execution_intents, {"duplicate_object"}):
            candidate = self._compile_duplication(source, target)
            if candidate:
                candidates.append(candidate)

        if not candidates:
            reason = (
                "no_supported_compiler_for_execution_intents"
                if execution_intents
                else "no_supported_semantic_delta"
            )
            return self._empty_report(
                concepts,
                reason,
                execution_intents=execution_intents,
                semantic_intent_report=semantic_intent_report,
            )

        for candidate in candidates:
            predicted = self.execute_program(source, candidate["compiled_program"])
            candidate["candidate_output_grid"] = predicted.tolist()
            candidate["validation"] = self._validation(predicted, target)

        candidates.sort(
            key=lambda item: (
                item["validation"]["exact_match"],
                item["validation"]["accuracy"],
                item["confidence"],
            ),
            reverse=True,
        )
        selected = candidates[0]
        return {
            "system": self.system_name,
            "semantic_to_transformation_compilation_success": selected["validation"]["accuracy"] > 0.0,
            "detected_intents": sorted(concepts),
            "execution_intents": [dict(intent) for intent in execution_intents if isinstance(intent, Mapping)],
            "semantic_intent_routing_report": dict(semantic_intent_report or {}),
            "compiler_triggered_by_intents": bool(execution_intents),
            "selected_intent": selected["intent"],
            "transformation_plan": selected["transformation_plan"],
            "transformation_graph": selected["transformation_graph"],
            "compiled_program": selected["compiled_program"],
            "candidate_output_grid": selected["candidate_output_grid"],
            "validation": selected["validation"],
            "candidate_count": len(candidates),
            "compiler_candidates": candidates,
            "timestamp": str(datetime.utcnow()),
        }

    def execute_program(self, grid, program: Mapping[str, Any]) -> np.ndarray:
        output = self._array(grid).copy()
        for step in program.get("steps", []) or []:
            operation = step.get("operation")
            parameters = step.get("parameters", {}) or {}
            if operation in {"scale_up", "scale_down"}:
                output = self._execute_scale(output, parameters)
            elif operation == "rotate":
                output = self._execute_rotate(output, parameters)
            elif operation in {"mirror_horizontal", "mirror_vertical"}:
                output = self._execute_reflect(output, operation)
            elif operation in {"construct_path", "connect_components"}:
                output = self._execute_path(output, parameters)
            elif operation == "remove_object":
                output = self._execute_filter(output, parameters)
            elif operation == "replace_color":
                output = self._execute_color_remap(output, parameters)
            elif operation in {"preserve_grid", "preserve_colors", "preserve_topology"}:
                output = output.copy()
            elif operation == "duplicate_object":
                output = self._execute_cell_writes(output, parameters)
        return output

    def _compile_scaling(self, source: np.ndarray, target: np.ndarray) -> dict[str, Any] | None:
        if source.ndim != 2 or target.ndim != 2:
            return None
        if source.shape[0] == 0 or source.shape[1] == 0:
            return None
        if target.shape[0] % source.shape[0] or target.shape[1] % source.shape[1]:
            return None
        row_scale = target.shape[0] // source.shape[0]
        col_scale = target.shape[1] // source.shape[1]
        if row_scale < 1 or col_scale < 1:
            return None
        predicted = np.repeat(np.repeat(source, row_scale, axis=0), col_scale, axis=1)
        if predicted.shape != target.shape:
            return None
        accuracy = self._validation(predicted, target)["accuracy"]
        if accuracy < 0.75:
            return None
        parameters = {
            "scale_mode": "cell_repeat",
            "row_scale": int(row_scale),
            "col_scale": int(col_scale),
            "scale_factor": int(row_scale) if row_scale == col_scale else None,
        }
        return self._candidate(
            "scaling",
            "scale_up" if row_scale >= 1 and col_scale >= 1 else "scale_down",
            parameters,
            confidence=0.93,
            support=accuracy,
            rationale="semantic_scaling_to_cell_repeat_program",
        )

    def _compile_rotation(
        self,
        source: np.ndarray,
        target: np.ndarray,
        execution_intents: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        if source.ndim != 2 or target.ndim != 2:
            return []
        preferred = self._preferred_degrees(execution_intents)
        degrees_options = [preferred] if preferred else [90, 180, 270]
        candidates = []
        for degrees in degrees_options:
            predicted = np.rot90(source, k=(degrees // 90) % 4)
            if predicted.shape != target.shape:
                continue
            accuracy = self._validation(predicted, target)["accuracy"]
            if accuracy <= 0.0:
                continue
            candidates.append(self._candidate(
                "rotation",
                "rotate",
                {
                    "degrees": int(degrees),
                    "rotation_source": "execution_intent",
                },
                confidence=0.91,
                support=accuracy,
                rationale="semantic_rotation_intent_to_rotate_program",
            ))
        return candidates

    def _compile_reflection(self, source: np.ndarray, target: np.ndarray) -> list[dict[str, Any]]:
        if source.ndim != 2 or target.ndim != 2:
            return []
        options = [
            ("mirror_horizontal", np.fliplr(source), "vertical_axis_reflection"),
            ("mirror_vertical", np.flipud(source), "horizontal_axis_reflection"),
        ]
        candidates = []
        for operation, predicted, rationale in options:
            if predicted.shape != target.shape:
                continue
            accuracy = self._validation(predicted, target)["accuracy"]
            if accuracy <= 0.0:
                continue
            candidates.append(self._candidate(
                "reflection",
                operation,
                {"reflection_source": "execution_intent"},
                confidence=0.89,
                support=accuracy,
                rationale=f"semantic_reflection_intent_to_{rationale}",
            ))
        return candidates

    def _compile_preservation(
        self,
        source: np.ndarray,
        target: np.ndarray,
        intent: str,
        operation: str,
    ) -> dict[str, Any] | None:
        if source.shape != target.shape:
            return None
        if not np.array_equal(source, target):
            return None
        return self._candidate(
            intent,
            operation,
            {"preservation_policy": "validated_no_delta"},
            confidence=0.90,
            support=1.0,
            rationale=f"semantic_{intent}_to_preservation_program",
        )

    def _compile_color_remap(self, source: np.ndarray, target: np.ndarray) -> dict[str, Any] | None:
        if source.shape != target.shape:
            return None
        changed = np.argwhere(source != target)
        if len(changed) == 0:
            return None
        mapping = {}
        for row, col in changed:
            src = int(source[row, col])
            dst = int(target[row, col])
            if src in mapping and mapping[src] != dst:
                return None
            mapping[src] = dst
        predicted = source.copy()
        for src, dst in mapping.items():
            predicted[source == src] = dst
        validation = self._validation(predicted, target)
        if validation["accuracy"] < 0.75:
            return None
        parameters = {
            "color_mapping": {int(src): int(dst) for src, dst in mapping.items()},
            "remap_policy": "observed_symbol_delta",
        }
        return self._candidate(
            "symbolic_remapping",
            "replace_color",
            parameters,
            confidence=0.90,
            support=validation["accuracy"],
            rationale="semantic_symbolic_remapping_to_color_replacement",
        )

    def _compile_duplication(self, source: np.ndarray, target: np.ndarray) -> dict[str, Any] | None:
        if source.shape != target.shape:
            return None
        background = self._background_color(source)
        added = np.argwhere((source == background) & (target != background))
        if len(added) == 0:
            return None
        preserved = np.array_equal(
            source[source != background],
            target[source != background],
        )
        if not preserved:
            return None
        parameters = {
            "cells_to_write": [
                {
                    "row": int(row),
                    "col": int(col),
                    "value": int(target[row, col]),
                }
                for row, col in added
            ],
            "duplication_count": int(len(added)),
            "duplication_policy": "observed_added_object_cells",
        }
        return self._candidate(
            "duplicate_object",
            "duplicate_object",
            parameters,
            confidence=0.88,
            support=min(1.0, len(added) / max(int(np.sum(target != background)), 1)),
            rationale="semantic_replication_to_observed_duplicate_cells",
        )

    def _compile_topology_repair(self, source: np.ndarray, target: np.ndarray) -> dict[str, Any] | None:
        if source.shape != target.shape:
            return None
        background = self._background_color(source)
        fill_points = np.argwhere((source == background) & (target != background))
        if len(fill_points) == 0:
            return None
        fill_color = int(Counter(int(target[tuple(point)]) for point in fill_points).most_common(1)[0][0])
        parameters = {
            "fill_color": fill_color,
            "path_color": fill_color,
            "path_cells": [point.tolist() for point in fill_points],
            "topology_policy": "observed_hole_repair_delta",
        }
        return self._candidate(
            "topology_repair",
            "construct_path",
            parameters,
            confidence=0.86,
            support=min(1.0, len(fill_points) / max(int(np.sum(target != background)), 1)),
            rationale="semantic_topology_repair_intent_to_fill_delta",
        )

    def _compile_path(
        self,
        source: np.ndarray,
        target: np.ndarray,
        concepts: set[str],
    ) -> dict[str, Any] | None:
        if source.shape != target.shape:
            return None
        changed_to_nonzero = np.argwhere((source != target) & (target != 0))
        if len(changed_to_nonzero) == 0:
            return None
        path_color = int(Counter(int(target[tuple(point)]) for point in changed_to_nonzero).most_common(1)[0][0])
        path_cells = [point.tolist() for point in changed_to_nonzero]
        anchors = self._path_anchors(source, path_cells, path_color)
        parameters = {
            "path_color": path_color,
            "path_cells": path_cells,
            "start": anchors[0],
            "end": anchors[1],
            "path_policy": "observed_delta_path",
        }
        operation = "connect_components" if {"bridge_creation", "component_connection"}.intersection(concepts) else "construct_path"
        return self._candidate(
            "path_construction",
            operation,
            parameters,
            confidence=0.94,
            support=min(1.0, len(path_cells) / max(int(np.sum(target != 0)), 1)),
            rationale="semantic_path_delta_to_explicit_path_cells",
        )

    def _compile_filter(self, source: np.ndarray, target: np.ndarray) -> dict[str, Any] | None:
        if source.shape != target.shape:
            return None
        background = self._background_color(source)
        removed_points = np.argwhere((source != target) & (target == background))
        if len(removed_points) == 0:
            return None
        source_counts = Counter(int(value) for value in source.flatten())
        target_counts = Counter(int(value) for value in target.flatten())
        remove_colors = [
            color
            for color, count in source_counts.items()
            if color != background and target_counts.get(color, 0) < count
        ]
        parameters = {
            "background_color": int(background),
            "remove_colors": sorted(int(color) for color in remove_colors),
            "cells_to_clear": [point.tolist() for point in removed_points],
            "filter_policy": "observed_noise_delta",
        }
        return self._candidate(
            "noise_or_artifact_filtering",
            "remove_object",
            parameters,
            confidence=0.91,
            support=min(1.0, len(removed_points) / max(int(np.sum(source != background)), 1)),
            rationale="semantic_filtering_to_explicit_cell_clear_program",
        )

    def _candidate(
        self,
        intent: str,
        operation: str,
        parameters: Mapping[str, Any],
        confidence: float,
        support: float,
        rationale: str,
    ) -> dict[str, Any]:
        program = {
            "program_type": "transformation_program",
            "step_count": 1,
            "steps": [
                {
                    "operation": operation,
                    "parameters": dict(parameters),
                }
            ],
        }
        return {
            "intent": intent,
            "compiled_program": program,
            "confidence": round(float(confidence), 4),
            "support_score": round(float(support), 4),
            "transformation_plan": {
                "plan_type": "semantic_to_transformation",
                "intent": intent,
                "rationale": rationale,
                "steps": program["steps"],
            },
            "transformation_graph": {
                "node_count": 1,
                "edge_count": 0,
                "nodes": [
                    {
                        "node_id": f"{intent}:0",
                        "operation": operation,
                        "parameters": dict(parameters),
                    }
                ],
                "edges": [],
            },
        }

    def _execute_scale(self, grid: np.ndarray, parameters: Mapping[str, Any]) -> np.ndarray:
        if parameters.get("scale_mode") != "cell_repeat":
            return grid
        row_scale = int(parameters.get("row_scale") or parameters.get("scale_factor") or 1)
        col_scale = int(parameters.get("col_scale") or parameters.get("scale_factor") or 1)
        return np.repeat(np.repeat(grid, max(row_scale, 1), axis=0), max(col_scale, 1), axis=1)

    def _execute_rotate(self, grid: np.ndarray, parameters: Mapping[str, Any]) -> np.ndarray:
        degrees = int(parameters.get("degrees", 90))
        return np.rot90(grid, k=(degrees // 90) % 4)

    def _execute_reflect(self, grid: np.ndarray, operation: str) -> np.ndarray:
        if operation == "mirror_horizontal":
            return np.fliplr(grid)
        return np.flipud(grid)

    def _execute_path(self, grid: np.ndarray, parameters: Mapping[str, Any]) -> np.ndarray:
        output = grid.copy()
        path_color = int(parameters.get("path_color", 1))
        for row, col in parameters.get("path_cells", []) or []:
            output[int(row), int(col)] = path_color
        return output

    def _execute_filter(self, grid: np.ndarray, parameters: Mapping[str, Any]) -> np.ndarray:
        output = grid.copy()
        background = int(parameters.get("background_color", 0))
        for row, col in parameters.get("cells_to_clear", []) or []:
            output[int(row), int(col)] = background
        for color in parameters.get("remove_colors", []) or []:
            output[output == int(color)] = background
        return output

    def _execute_color_remap(self, grid: np.ndarray, parameters: Mapping[str, Any]) -> np.ndarray:
        output = grid.copy()
        mapping = parameters.get("color_mapping", {}) or {}
        for source_color, target_color in mapping.items():
            output[grid == int(source_color)] = int(target_color)
        return output

    def _execute_cell_writes(self, grid: np.ndarray, parameters: Mapping[str, Any]) -> np.ndarray:
        output = grid.copy()
        for cell in parameters.get("cells_to_write", []) or []:
            row = int(cell.get("row", 0))
            col = int(cell.get("col", 0))
            if 0 <= row < output.shape[0] and 0 <= col < output.shape[1]:
                output[row, col] = int(cell.get("value", output[row, col]))
        return output

    def _path_anchors(self, source: np.ndarray, path_cells: list[list[int]], path_color: int) -> tuple[list[int], list[int]]:
        colored = [point.tolist() for point in np.argwhere(source == path_color)]
        if len(colored) >= 2:
            first = min(colored, key=lambda point: min(self._manhattan(point, cell) for cell in path_cells))
            last = max(colored, key=lambda point: min(self._manhattan(point, cell) for cell in path_cells))
            return first, last
        nonzero = [point.tolist() for point in np.argwhere(source != 0)]
        if len(nonzero) >= 2:
            return nonzero[0], nonzero[-1]
        if path_cells:
            return path_cells[0], path_cells[-1]
        return [0, 0], [0, 0]

    def _validation(self, predicted: np.ndarray, target: np.ndarray) -> dict[str, Any]:
        if predicted.shape != target.shape:
            return {
                "exact_match": False,
                "accuracy": 0.0,
                "shape_match": False,
            }
        accuracy = float(np.sum(predicted == target) / max(target.size, 1))
        return {
            "exact_match": bool(np.array_equal(predicted, target)),
            "accuracy": round(accuracy, 4),
            "shape_match": True,
        }

    def _empty_report(
        self,
        concepts: set[str],
        reason: str,
        *,
        execution_intents: list[Mapping[str, Any]] | None = None,
        semantic_intent_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "semantic_to_transformation_compilation_success": False,
            "detected_intents": sorted(concepts),
            "execution_intents": [dict(intent) for intent in execution_intents or [] if isinstance(intent, Mapping)],
            "semantic_intent_routing_report": dict(semantic_intent_report or {}),
            "compiler_triggered_by_intents": bool(execution_intents),
            "selected_intent": None,
            "transformation_plan": {},
            "transformation_graph": {"node_count": 0, "edge_count": 0, "nodes": [], "edges": []},
            "compiled_program": {"program_type": "transformation_program", "step_count": 0, "steps": []},
            "candidate_output_grid": None,
            "validation": {"exact_match": False, "accuracy": 0.0, "shape_match": False},
            "candidate_count": 0,
            "compiler_candidates": [],
            "failure_reason": reason,
            "timestamp": str(datetime.utcnow()),
        }

    def _array(self, grid) -> np.ndarray:
        if grid is None:
            return np.array([])
        if hasattr(grid, "grid"):
            return np.array(grid.grid)
        return np.array(grid)

    def _background_color(self, grid: np.ndarray) -> int:
        return int(Counter(int(value) for value in grid.flatten()).most_common(1)[0][0])

    def _manhattan(self, left: list[int], right: list[int]) -> int:
        return abs(int(left[0]) - int(right[0])) + abs(int(left[1]) - int(right[1]))

    def _has_intent(self, intents: list[Mapping[str, Any]], names: set[str]) -> bool:
        return any(
            isinstance(intent, Mapping) and str(intent.get("intent")) in names
            for intent in intents
        )

    def _preferred_degrees(self, intents: list[Mapping[str, Any]]) -> int | None:
        for intent in intents:
            if not isinstance(intent, Mapping):
                continue
            operation = str(intent.get("operation", "")).lower()
            if "180" in operation:
                return 180
            if "counterclockwise" in operation:
                return 90
            if "clockwise" in operation or "270" in operation:
                return 270
            if "90" in operation:
                return 90
        return None


semantic_to_transformation_compiler = SemanticToTransformationCompiler()
