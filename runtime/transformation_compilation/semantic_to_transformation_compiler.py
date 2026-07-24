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

from runtime.transformation_compilation.compiler_infrastructure import (
    PRIMITIVE_OPERATION_REGISTRY,
    compiler_infrastructure_analyzer,
)


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
    SHAPE_PRESERVATION_CONCEPTS = {
        "shape_preservation",
        "preserve_shape",
    }
    SIZE_PRESERVATION_CONCEPTS = {
        "size_preservation",
        "preserve_size",
    }
    DENSITY_PRESERVATION_CONCEPTS = {
        "density_preservation",
        "preserve_density",
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
    }
    TOPOLOGY_PRESERVATION_CONCEPTS = {
        "topology_preservation",
        "preserve_topology",
    }
    SYMMETRY_PRESERVATION_CONCEPTS = {
        "symmetry_preservation",
        "symmetry_reasoning",
        "preserve_symmetry",
    }
    COMPILER_RULES = {
        "scale_up": "RULE_SCALING_CELL_REPEAT_01",
        "scale_down": "RULE_SCALING_CELL_REPEAT_01",
        "rotate": "RULE_ROTATION_ALIGNMENT_01",
        "mirror_horizontal": "RULE_REFLECTION_ALIGNMENT_01",
        "mirror_vertical": "RULE_REFLECTION_ALIGNMENT_01",
        "construct_path": "RULE_PATH_CONSTRUCTION_01",
        "connect_components": "RULE_CONNECTIVITY_BRIDGE_01",
        "remove_object": "RULE_ARTIFACT_FILTERING_01",
        "replace_color": "RULE_SYMBOLIC_REMAP_01",
        "duplicate_object": "RULE_GROWTH_DUPLICATION_01",
        "preserve_grid": "RULE_GRID_PRESERVATION_01",
        "preserve_colors": "RULE_COLOR_PRESERVATION_01",
        "preserve_topology": "RULE_TOPOLOGY_PRESERVATION_01",
        "preserve_shape": "RULE_SHAPE_PRESERVATION_01",
        "preserve_size": "RULE_SIZE_PRESERVATION_01",
        "preserve_density": "RULE_DENSITY_PRESERVATION_01",
        "preserve_symmetry": "RULE_SYMMETRY_PRESERVATION_01",
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
                source=source,
                target=target,
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
        if concepts.intersection(self.SHAPE_PRESERVATION_CONCEPTS) or self._has_intent(execution_intents, {"preserve_shape"}):
            candidate = self._compile_preservation(source, target, "shape_preservation", "preserve_shape")
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.SIZE_PRESERVATION_CONCEPTS) or self._has_intent(execution_intents, {"preserve_size"}):
            candidate = self._compile_preservation(source, target, "size_preservation", "preserve_size")
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.DENSITY_PRESERVATION_CONCEPTS) or self._has_intent(execution_intents, {"preserve_density"}):
            candidate = self._compile_preservation(source, target, "density_preservation", "preserve_density")
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.TOPOLOGY_PRESERVATION_CONCEPTS) or self._has_intent(execution_intents, {"preserve_topology"}):
            candidate = self._compile_preservation(source, target, "topology_preservation", "preserve_topology")
            if candidate:
                candidates.append(candidate)
        if concepts.intersection(self.SYMMETRY_PRESERVATION_CONCEPTS) or self._has_intent(execution_intents, {"preserve_symmetry"}):
            candidate = self._compile_preservation(source, target, "symmetry_preservation", "preserve_symmetry")
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
                source=source,
                target=target,
            )

        for candidate in candidates:
            predicted = self.execute_program(source, candidate["compiled_program"])
            candidate["candidate_output_grid"] = predicted.tolist()
            candidate["validation"] = self._validation(predicted, target)
            candidate["failure_diagnostics"] = self._candidate_failure_diagnostics(
                candidate,
                source,
                target,
            )

        candidates.sort(
            key=lambda item: (
                item["validation"]["exact_match"],
                item["validation"]["accuracy"],
                item["confidence"],
            ),
            reverse=True,
        )
        selected = candidates[0]
        report = {
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
            "compiler_failure_diagnostics": self._compiler_failure_diagnostics(
                concepts,
                execution_intents,
                source,
                target,
                candidates,
            ),
            "timestamp": str(datetime.utcnow()),
        }
        report["compiler_infrastructure_report"] = (
            compiler_infrastructure_analyzer.build_report(
                compiler_report=report,
                expected_operations=report["compiler_failure_diagnostics"].get(
                    "expected_operations",
                    [],
                ),
                candidate_programs=candidates,
            )
        )
        return report

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
            elif operation in {
                "preserve_grid",
                "preserve_colors",
                "preserve_topology",
                "preserve_shape",
                "preserve_size",
                "preserve_density",
                "preserve_symmetry",
            }:
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
        source: np.ndarray | None = None,
        target: np.ndarray | None = None,
    ) -> dict[str, Any]:
        report = {
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
            "compiler_failure_diagnostics": self._compiler_failure_diagnostics(
                concepts,
                execution_intents or [],
                source,
                target,
                [],
                failure_reason=reason,
            ),
            "timestamp": str(datetime.utcnow()),
        }
        report["compiler_infrastructure_report"] = (
            compiler_infrastructure_analyzer.build_report(
                compiler_report=report,
                expected_operations=report["compiler_failure_diagnostics"].get(
                    "expected_operations",
                    [],
                ),
                candidate_programs=[],
            )
        )
        return report

    def _compiler_failure_diagnostics(
        self,
        concepts: set[str],
        execution_intents: list[Mapping[str, Any]],
        source: np.ndarray | None,
        target: np.ndarray | None,
        candidates: list[dict[str, Any]],
        *,
        failure_reason: str | None = None,
    ) -> dict[str, Any]:
        trace_events = self._expected_operation_traces(concepts, execution_intents)
        expected_operations = sorted(
            dict.fromkeys(
                str(event.get("expected_operation"))
                for event in trace_events
                if event.get("expected_operation")
            )
        )
        domain_counts = Counter(
            str(event.get("domain") or self._domain_for_operation(str(event.get("expected_operation"))))
            for event in trace_events
        )
        reason_counts = Counter()
        rows = []
        grounding_requirement_rows = []
        if failure_reason:
            reason_counts[failure_reason] += 1
        if not trace_events:
            reason_counts["operation_ambiguity"] += 1
            rows.append({
                "trace_id": "compiler_trace:unknown:unknown:unknown",
                "program": "semantic_program_unknown",
                "semantic_intent": "unknown",
                "operation": "unknown",
                "expected_operation": "unknown",
                "resolved_operation": "unknown",
                "domain": "Transformation",
                "failure_stage": "semantic_operation_resolution",
                "reason": "operation_ambiguity",
                "detail": "no_supported_semantic_operation_detected",
                "compiler_rule": "RULE_NOT_RESOLVED",
                "diagnostic_row_source": "semantic_to_transformation_compiler",
            })
        for event in trace_events:
            operation = str(event.get("expected_operation") or "unknown")
            resolved_operation = str(event.get("resolved_operation") or operation)
            domain = str(event.get("domain") or self._domain_for_operation(operation))
            reason = None
            detail = ""
            failure_stage = "program_candidate_generation"
            matched_candidate = None
            if source is None or target is None or source.size == 0 or target.size == 0:
                reason = "missing_grid_pair"
                detail = "input_or_target_grid_missing"
                failure_stage = "compiler_input_binding"
            elif resolved_operation != operation:
                reason = "operation_semantics_mismatch"
                detail = (
                    f"expected_operation={operation}; "
                    f"resolved_operation={resolved_operation}"
                )
                failure_stage = "semantic_operation_resolution"
            elif not self._operation_has_primitive(operation):
                reason = "missing_primitive"
                detail = f"primitive_not_registered:{operation}"
                failure_stage = "primitive_resolution"
            elif source.shape != target.shape and operation not in {
                "scale_up",
                "scale_down",
                "rotate",
                "mirror_horizontal",
                "mirror_vertical",
            }:
                reason = "shape_contract_mismatch"
                detail = f"source_shape={source.shape}; target_shape={target.shape}"
                failure_stage = "execution_contract_validation"
            else:
                matching = [
                    candidate for candidate in candidates
                    if self._candidate_operation(candidate) == operation
                ]
                if not matching:
                    reason = self._missing_candidate_reason(
                        operation,
                        source,
                        target,
                    )
                    detail = f"candidate_not_emitted:{operation}"
                    failure_stage = (
                        "semantic_operation_resolution"
                        if reason == "operation_semantics_mismatch"
                        else "program_candidate_generation"
                    )
                else:
                    best = max(
                        matching,
                        key=lambda item: float(
                            item.get("validation", {}).get("accuracy", 0.0)
                        ),
                    )
                    matched_candidate = best
                    validation = best.get("validation", {})
                    if not validation.get("exact_match"):
                        reason = "execution_mismatch"
                        detail = (
                            "best_accuracy="
                            f"{validation.get('accuracy', 0.0)}"
                        )
                        failure_stage = "program_execution_validation"
            if reason:
                reason_counts[reason] += 1
                if reason == "missing_grid_pair":
                    grounding_requirement_rows.append(
                        self._grounding_requirement_row(
                            operation=operation,
                            domain=domain,
                            program=event.get("program"),
                            semantic_intent=event.get("semantic_intent"),
                            trace_id=event.get("trace_id"),
                        )
                    )
                deep_diagnostic = self._deep_failure_diagnostic(
                    operation=operation,
                    resolved_operation=resolved_operation,
                    reason=reason,
                    failure_stage=failure_stage,
                    detail=detail,
                    candidate=matched_candidate,
                )
                rows.append({
                    "trace_id": event.get("trace_id"),
                    "program": event.get("program"),
                    "semantic_intent": event.get("semantic_intent"),
                    "operation": operation,
                    "expected_operation": operation,
                    "resolved_operation": resolved_operation,
                    "domain": domain,
                    "failure_stage": failure_stage,
                    "reason": reason,
                    "detail": detail,
                    "compiler_rule": event.get("compiler_rule"),
                    **deep_diagnostic,
                    "diagnostic_row_source": "semantic_to_transformation_compiler",
                })
        grounding_failure_count = sum(
            count
            for reason, count in reason_counts.items()
            if reason in {"missing_grid_pair"}
        )
        semantic_failure_count = sum(
            count
            for reason, count in reason_counts.items()
            if reason in {
                "operation_semantics_mismatch",
                "operation_ambiguity",
                "missing_primitive",
                "shape_contract_mismatch",
                "execution_mismatch",
                "partial_execution_mismatch",
            }
        )
        total_failures = grounding_failure_count + semantic_failure_count
        return {
            "failure_reason_counts": dict(sorted(reason_counts.items())),
            "failure_domain_distribution": dict(sorted(domain_counts.items())),
            "failure_rows": rows[:25],
            "grounding_requirement_rows": grounding_requirement_rows[:25],
            "grounding_required_for_operations": sorted(
                {
                    str(row.get("operation"))
                    for row in grounding_requirement_rows
                    if row.get("operation")
                }
            ),
            "grounding_required_for_domains": dict(
                sorted(
                    Counter(
                        str(row.get("domain"))
                        for row in grounding_requirement_rows
                        if row.get("domain")
                    ).items()
                )
            ),
            "expected_operations": expected_operations,
            "compiler_trace_events": trace_events[:25],
            "candidate_count": len(candidates),
            "operational_grounding_failure_count": grounding_failure_count,
            "compiler_semantic_failure_count": semantic_failure_count,
            "operational_grounding_failure_rate": round(
                grounding_failure_count / max(total_failures, 1),
                4,
            ),
            "operational_grounding_state": (
                "GROUNDING_FAILURE_DOMINANT"
                if grounding_failure_count > semantic_failure_count
                and grounding_failure_count > 0
                else "GROUNDING_FAILURE_PRESENT"
                if grounding_failure_count > 0
                else "GROUNDED_COMPILER_INPUTS"
            ),
            "compiler_failure_interpretation": (
                "operational_grounding_failure"
                if grounding_failure_count > semantic_failure_count
                and grounding_failure_count > 0
                else "mixed_grounding_and_compiler_failure"
                if grounding_failure_count > 0
                else "compiler_semantic_or_execution_failure"
            ),
        }

    def _grounding_requirement_row(
        self,
        *,
        operation: str,
        domain: str,
        program: Any,
        semantic_intent: Any,
        trace_id: Any,
    ) -> dict[str, Any]:
        return {
            "trace_id": trace_id,
            "program": program,
            "semantic_intent": semantic_intent,
            "operation": operation,
            "domain": domain,
            "missing_grounding": "input_output_grid_pair",
            "required_evidence": "exact_or_governed_validation_success",
            "required_task_property": self._required_grounding_task_property(
                operation
            ),
            "grounding_stage": "compiler_input_grounding",
            "action": "select_grounding_aligned_task",
        }

    def _required_grounding_task_property(self, operation: str) -> str:
        operation = str(operation or "")
        if operation in {"translate", "move_object"}:
            return "unambiguous_directional_translation_ground_truth"
        if operation in {"preserve_topology", "topological_reasoning"}:
            return "topology_preserving_transformation_ground_truth"
        if operation in {"preserve_grid", "preserve_shape", "preserve_size"}:
            return "paired_identity_preservation_ground_truth"
        if operation in {"duplicate_object", "replicate_object"}:
            return "paired_symbolic_object_replication_ground_truth"
        if operation in {"replace_color", "preserve_colors"}:
            return "color_invariance_under_transformation"
        return "paired_source_target_grid_ground_truth"

    def _candidate_failure_diagnostics(
        self,
        candidate: Mapping[str, Any],
        source: np.ndarray,
        target: np.ndarray,
    ) -> dict[str, Any]:
        operation = self._candidate_operation(candidate)
        validation = candidate.get("validation", {})
        if validation.get("exact_match"):
            reason = "none"
        elif validation.get("shape_match") is False:
            reason = "shape_contract_mismatch"
        elif float(validation.get("accuracy", 0.0) or 0.0) <= 0.0:
            reason = "execution_mismatch"
        else:
            reason = "partial_execution_mismatch"
        return {
            "operation": operation,
            "domain": self._domain_for_operation(operation),
            "reason": reason,
            "accuracy": validation.get("accuracy", 0.0),
            "shape_match": validation.get("shape_match"),
            "source_shape": list(source.shape),
            "target_shape": list(target.shape),
            **self._deep_failure_diagnostic(
                operation=operation,
                resolved_operation=operation,
                reason=reason,
                failure_stage=(
                    "program_execution_validation"
                    if reason not in {"none", "shape_contract_mismatch"}
                    else "execution_contract_validation"
                ),
                detail=str(validation),
                candidate=candidate,
            ),
        }

    def _deep_failure_diagnostic(
        self,
        *,
        operation: str,
        resolved_operation: str,
        reason: str,
        failure_stage: str,
        detail: str,
        candidate: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = PRIMITIVE_OPERATION_REGISTRY.get(operation, {})
        package = metadata.get("package")
        parameter_support = metadata.get("parameters", []) or []
        candidate = candidate if isinstance(candidate, Mapping) else {}
        program = candidate.get("compiled_program")
        program = program if isinstance(program, Mapping) else {}
        steps = program.get("steps") if isinstance(program.get("steps"), list) else []
        parameters = {}
        if steps and isinstance(steps[0], Mapping):
            parameters = steps[0].get("parameters")
            parameters = parameters if isinstance(parameters, Mapping) else {}
        missing_parameters = [
            str(parameter)
            for parameter in parameter_support
            if parameter not in parameters
        ]
        parameter_failure = (
            "PARAMETER_CONTRACT_EMPTY"
            if reason in {"invalid_composition", "execution_mismatch"}
            and parameter_support
            and not parameters
            else "PARAMETER_CONTRACT_PARTIAL"
            if reason in {"invalid_composition", "execution_mismatch"}
            and missing_parameters
            else "NONE"
        )
        return {
            "failed_primitive": operation,
            "execution_package": package,
            "primitive_failure": (
                "MISSING_PRIMITIVE"
                if reason == "missing_primitive"
                else "EXECUTION_PACKAGE_UNRESOLVED"
                if not package
                else "NONE"
            ),
            "parameter_failure": parameter_failure,
            "missing_parameters": missing_parameters,
            "semantic_mapping_failure": (
                "SEMANTIC_OPERATION_MISMATCH"
                if reason == "operation_semantics_mismatch"
                or resolved_operation != operation
                else "NONE"
            ),
            "program_composition_failure": (
                "PROGRAM_COMPOSITION_INVALID"
                if reason == "invalid_composition"
                else "MULTI_STEP_COMPOSITION_UNVERIFIED"
                if len(steps) > 1 and reason not in {"none"}
                else "NONE"
            ),
            "execution_package_failure": (
                "EXECUTION_PACKAGE_MISSING"
                if not package
                else "EXECUTION_PACKAGE_PARTIAL_OR_UNVERIFIED"
                if reason in {"execution_mismatch", "invalid_composition"}
                else "NONE"
            ),
            "failure_detail_depth": "PRIMITIVE_PACKAGE_PARAMETER_TRACE",
            "diagnostic_detail": detail,
        }

    def _expected_operations(
        self,
        concepts: set[str],
        execution_intents: list[Mapping[str, Any]],
    ) -> list[str]:
        return sorted(
            dict.fromkeys(
                str(event.get("expected_operation"))
                for event in self._expected_operation_traces(
                    concepts,
                    execution_intents,
                )
                if event.get("expected_operation")
            )
        )

    def _expected_operation_traces(
        self,
        concepts: set[str],
        execution_intents: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        traces = []
        seen: set[tuple[str, str, str]] = set()
        intent_expected_operations: set[str] = set()
        concept_operation_pairs = self._concept_operation_pairs()
        for intent in execution_intents:
            if not isinstance(intent, Mapping):
                continue
            semantic_intent = str(intent.get("intent") or "unknown")
            matched = {
                semantic_intent,
                *[str(item) for item in intent.get("matched_concepts", []) or []],
            }
            expected_operation = self._operation_for_concepts(
                matched,
                concept_operation_pairs,
            )
            resolved_operation = str(intent.get("operation") or expected_operation or "unknown")
            if not expected_operation:
                expected_operation = resolved_operation
            intent_expected_operations.add(str(expected_operation))
            program = (
                intent.get("program_id")
                or intent.get("candidate_id")
                or intent.get("program")
                or f"semantic_program_{expected_operation}"
            )
            traces.append(
                self._compiler_trace_event(
                    program=str(program),
                    semantic_intent=semantic_intent,
                    expected_operation=str(expected_operation),
                    resolved_operation=str(resolved_operation),
                    seen=seen,
                )
            )
        for concept_set, operation in concept_operation_pairs:
            if operation in intent_expected_operations:
                continue
            matches = sorted(concepts.intersection(concept_set))
            for concept in matches:
                traces.append(
                    self._compiler_trace_event(
                        program=f"semantic_program_{operation}",
                        semantic_intent=concept,
                        expected_operation=operation,
                        resolved_operation=operation,
                        seen=seen,
                    )
                )
        return [trace for trace in traces if trace]

    def _compiler_trace_event(
        self,
        *,
        program: str,
        semantic_intent: str,
        expected_operation: str,
        resolved_operation: str,
        seen: set[tuple[str, str, str]],
    ) -> dict[str, Any]:
        key = (program, semantic_intent, expected_operation)
        if key in seen:
            return {}
        seen.add(key)
        compiler_rule = self._compiler_rule_for(expected_operation)
        return {
            "trace_id": (
                "compiler_trace:"
                f"{program}:{semantic_intent}:{expected_operation}"
            ),
            "program": program,
            "semantic_intent": semantic_intent,
            "expected_operation": expected_operation,
            "resolved_operation": resolved_operation,
            "operation": expected_operation,
            "domain": self._domain_for_operation(expected_operation),
            "compiler_rule": compiler_rule,
        }

    def _operation_for_concepts(
        self,
        concepts: set[str],
        concept_operation_pairs: list[tuple[set[str], str]],
    ) -> str | None:
        for concept_set, operation in concept_operation_pairs:
            if concepts.intersection(concept_set):
                return operation
        return None

    def _concept_operation_pairs(self) -> list[tuple[set[str], str]]:
        return [
            (self.ROTATION_CONCEPTS, "rotate"),
            (self.REFLECTION_CONCEPTS, "mirror_horizontal"),
            (self.SCALING_CONCEPTS, "scale_up"),
            (self.PATH_CONCEPTS, "construct_path"),
            (self.FILTER_CONCEPTS, "remove_object"),
            (self.TOPOLOGY_REPAIR_CONCEPTS, "construct_path"),
            (self.COLOR_PRESERVATION_CONCEPTS, "preserve_colors"),
            (self.SHAPE_PRESERVATION_CONCEPTS, "preserve_shape"),
            (self.SIZE_PRESERVATION_CONCEPTS, "preserve_size"),
            (self.DENSITY_PRESERVATION_CONCEPTS, "preserve_density"),
            (self.TOPOLOGY_PRESERVATION_CONCEPTS, "preserve_topology"),
            (self.SYMMETRY_PRESERVATION_CONCEPTS, "preserve_symmetry"),
            (self.GRID_PRESERVATION_CONCEPTS, "preserve_grid"),
            (self.COLOR_REMAP_CONCEPTS, "replace_color"),
            (self.DUPLICATION_CONCEPTS, "duplicate_object"),
        ]

    def _compiler_rule_for(self, operation: str) -> str:
        return self.COMPILER_RULES.get(operation, "RULE_NOT_RESOLVED")

    def _legacy_expected_operations(
        self,
        concepts: set[str],
        execution_intents: list[Mapping[str, Any]],
    ) -> list[str]:
        operations = []
        intent_operations = {
            str(intent.get("operation"))
            for intent in execution_intents
            if isinstance(intent, Mapping) and intent.get("operation")
        }
        operations.extend(
            operation for operation in sorted(intent_operations)
            if operation and operation != "None"
        )
        concept_operation_pairs = self._concept_operation_pairs()
        for concept_set, operation in concept_operation_pairs:
            if concepts.intersection(concept_set):
                operations.append(operation)
        return sorted(dict.fromkeys(operations))

    def _candidate_operation(self, candidate: Mapping[str, Any]) -> str:
        steps = candidate.get("compiled_program", {}).get("steps", [])
        if steps and isinstance(steps[0], Mapping):
            return str(steps[0].get("operation") or "unknown")
        return "unknown"

    def _operation_has_primitive(self, operation: str) -> bool:
        return operation in {
            "scale_up",
            "scale_down",
            "rotate",
            "mirror_horizontal",
            "mirror_vertical",
            "construct_path",
            "connect_components",
            "remove_object",
            "replace_color",
            "duplicate_object",
            "preserve_grid",
            "preserve_colors",
            "preserve_topology",
            "preserve_shape",
            "preserve_size",
            "preserve_density",
            "preserve_symmetry",
        }

    def _missing_candidate_reason(
        self,
        operation: str,
        source: np.ndarray,
        target: np.ndarray,
    ) -> str:
        if operation.startswith("preserve_") and not np.array_equal(source, target):
            return "operation_semantics_mismatch"
        if operation == "replace_color" and source.shape == target.shape:
            changed = np.argwhere(source != target)
            mappings = {}
            for row, col in changed:
                src = int(source[row, col])
                dst = int(target[row, col])
                if src in mappings and mappings[src] != dst:
                    return "operation_ambiguity"
                mappings[src] = dst
        if operation == "duplicate_object":
            background = self._background_color(source)
            if not np.any((source == background) & (target != background)):
                return "execution_mismatch"
        return "invalid_composition"

    def _domain_for_operation(self, operation: str) -> str:
        if operation in {"replace_color", "preserve_colors"}:
            return "Color"
        if operation in {
            "translate",
            "preserve_grid",
            "preserve_shape",
            "preserve_size",
            "rotate",
            "mirror_horizontal",
            "mirror_vertical",
        }:
            return "Spatial"
        if operation in {"construct_path", "connect_components", "preserve_topology"}:
            return "Topology"
        if operation in {"duplicate_object", "preserve_density", "scale_up", "scale_down"}:
            return "Growth"
        if operation in {"preserve_symmetry"}:
            return "Geometry"
        return "Transformation"

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
