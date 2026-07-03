"""Transformation synthesis between concept attribution and execution."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Mapping

import numpy as np

from runtime.memory.transformation_memory import transformation_memory
from runtime.reasoning.color_mapping_engine import color_mapping_engine
from runtime.transforms import primitive_executor


class TransformationSynthesisEngine:
    """Infer executable transformation programs from observations."""

    system_name = "transformation_synthesis_engine"

    CONCEPT_TO_OPERATIONS = {
        "relative_position": ["translate"],
        "spatial_relation": ["translate"],
        "object_translation": ["translate"],
        "directional_motion": ["translate"],
        "symbolic_remapping": ["recolor"],
        "color_mapping": ["recolor"],
        "path_finding": ["construct_path"],
        "route_completion": ["construct_path"],
        "bridge_creation": ["connect_components"],
        "component_connection": ["connect_components"],
        "connectivity_change": ["connect_components"],
        "growth": ["grow"],
        "topological_growth": ["grow"],
        "inside_outside": ["inside", "outside"],
        "containment": ["inside", "outside"],
        "topology_change": ["grow", "connect_components"],
        "transformation_sequence": ["compose"],
        "rotation": ["rotate"],
        "reflection": ["mirror_horizontal", "mirror_vertical"],
        "duplication": ["duplicate"],
        "replication": ["replicate"],
        "object_removal": ["remove_object"],
        "object_selection": ["select_object"],
        "region_filling": ["fill_region"],
        "scaling": ["scale_up", "scale_down"],
    }

    SIMPLE_COST = {
        "select_object": 0.02,
        "translate": 0.05,
        "recolor": 0.05,
        "rotate": 0.07,
        "mirror_horizontal": 0.07,
        "mirror_vertical": 0.07,
        "duplicate": 0.10,
        "replicate": 0.10,
        "construct_path": 0.12,
        "connect_components": 0.12,
        "fill_region": 0.12,
        "grow": 0.13,
        "expand": 0.13,
        "remove_object": 0.14,
        "inside": 0.16,
        "outside": 0.16,
        "scale_up": 0.18,
        "scale_down": 0.18,
        "compose": 0.20,
    }

    EXECUTION_ALIASES = {
        "translate": "translate",
        "recolor": "replace_color",
        "mirror_horizontal": "mirror_object",
        "mirror_vertical": "mirror_vertical",
        "rotate": "rotate_grid",
        "duplicate": "duplicate_object",
        "replicate": "duplicate_object",
        "grow": "grow_topology",
        "expand": "expand_pattern",
        "connect_components": "connect_components",
        "construct_path": "construct_path",
        "fill_region": "fill_region",
        "remove_object": "remove_object",
        "scale_up": "expand_grid",
        "scale_down": "shrink_grid",
        "select_object": "preserve_grid",
        "inside": "preserve_grid",
        "outside": "preserve_grid",
    }

    def __init__(self, memory=None, executor=None):
        self.memory = memory or transformation_memory
        self.executor = executor or primitive_executor
        self.color_mapping_engine = color_mapping_engine
        self.synthesis_history = []

    def synthesize(
        self,
        input_grid=None,
        output_grid=None,
        detected_concepts: list[str] | None = None,
        concept_report: Mapping[str, Any] | None = None,
        semantic_context_report: Mapping[str, Any] | None = None,
        reasoning_reports: list[Mapping[str, Any]] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        minimum_accuracy: float = 0.75,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        input_grid = input_grid if input_grid is not None else runtime_context.get("input_grid")
        if output_grid is None:
            output_grid = runtime_context.get("output_grid")
        if output_grid is None:
            output_grid = runtime_context.get("target_grid")
        reasoning_reports = list(reasoning_reports or [])

        concepts = self._collect_concepts(
            detected_concepts,
            concept_report,
            semantic_context_report,
            reasoning_reports,
            runtime_context,
        )
        candidates = []
        candidates.extend(self._memory_candidates(concepts))
        candidates.extend(self._concept_candidates(concepts))
        candidates.extend(self._observation_candidates(input_grid, output_grid, concepts))

        candidates = self._dedupe_candidates(candidates)
        candidates = self._score_candidates(candidates, input_grid, output_grid, concepts)
        candidates = self._counterfactual_search(
            candidates,
            input_grid,
            output_grid,
            minimum_accuracy,
        )

        selected = candidates[0] if candidates else None
        selected_program = (
            selected.get("program")
            if selected
            else self._program([])
        )

        if selected and output_grid is not None:
            self.memory.remember(
                selected_program,
                concepts=concepts,
                accuracy=selected.get("prediction_accuracy", 0.0),
                success=selected.get("prediction_accuracy", 0.0) >= minimum_accuracy,
                evidence=selected.get("evidence", {}),
            )

        report = self._build_report(
            concepts,
            candidates,
            selected,
            selected_program,
        )
        self.synthesis_history.append(report)
        return report

    def synthesize_from_runtime_context(
        self,
        runtime_context: Mapping[str, Any],
    ) -> dict[str, Any]:
        reports = []
        for key in [
            "spatial_reasoning_report",
            "symbolic_report",
            "causal_report",
            "semantic_context_report",
            "concept_attribution_report",
            "generalization_report",
        ]:
            value = runtime_context.get(key)
            if isinstance(value, Mapping):
                reports.append(value)
        return self.synthesize(
            concept_report=runtime_context.get("concept_attribution_report", {}),
            semantic_context_report=runtime_context.get("semantic_context_report", {}),
            reasoning_reports=reports,
            runtime_context=runtime_context,
        )

    def _collect_concepts(self, *sources) -> list[str]:
        concepts = []

        def visit(value):
            if value is None:
                return
            if isinstance(value, str):
                self._maybe_add_concept(concepts, value)
                return
            if isinstance(value, Mapping):
                for key, item in value.items():
                    if key in {
                        "concept",
                        "concepts",
                        "detected_concepts",
                        "attributed_concepts",
                        "semantic_context",
                        "symbolic_type",
                        "abstract_rule",
                        "type",
                        "dominant_transformation",
                    }:
                        visit(item)
                    elif isinstance(item, (Mapping, list, tuple, set)):
                        visit(item)
                return
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)

        for source in sources:
            visit(source)
        return list(dict.fromkeys(concepts))

    def _maybe_add_concept(self, concepts, value):
        token = value.strip().lower().replace("-", "_").replace(" ", "_")
        if token in self.CONCEPT_TO_OPERATIONS:
            concepts.append(token)
        elif token.endswith("_context") and token[:-8] in self.CONCEPT_TO_OPERATIONS:
            concepts.append(token[:-8])
        elif token.startswith("object_") and token in self.CONCEPT_TO_OPERATIONS:
            concepts.append(token)

    def _memory_candidates(self, concepts):
        candidates = []
        for record in self.memory.retrieve_successful(concepts):
            candidates.append(self._candidate(
                "memory_reuse",
                record.get("program", {}),
                record.get("accuracy", 0.0),
                0.88,
                {"memory_signature": record.get("signature")},
                program_reuse=True,
            ))
        return candidates

    def _concept_candidates(self, concepts):
        candidates = []
        for concept in concepts:
            for operation in self.CONCEPT_TO_OPERATIONS.get(concept, []):
                if operation == "compose":
                    continue
                candidates.append(self._single_step_candidate(
                    operation,
                    {},
                    0.58,
                    0.55,
                    {"concept": concept, "source": "concept_mapping"},
                ))
        return candidates

    def _observation_candidates(self, input_grid, output_grid, concepts):
        if input_grid is None or output_grid is None:
            return []
        source = self._array(input_grid)
        target = self._array(output_grid)
        candidates = []
        candidates.extend(self._translation_candidates(source, target))
        candidates.extend(self._recolor_candidates(source, target, concepts))
        candidates.extend(self._rotation_candidates(source, target))
        candidates.extend(self._reflection_candidates(source, target))
        candidates.extend(self._object_count_candidates(source, target))
        candidates.extend(self._growth_candidates(source, target, concepts))
        candidates.extend(self._path_candidates(source, target, concepts))
        candidates.extend(self._fill_candidates(source, target, concepts))
        candidates.extend(self._composition_candidates(candidates))
        return candidates

    def _translation_candidates(self, source, target):
        shifts = []
        for color in self._shared_colors(source, target):
            source_points = np.argwhere(source == color)
            target_points = np.argwhere(target == color)
            if len(source_points) == 0 or len(target_points) == 0:
                continue
            delta = tuple(np.rint(target_points.mean(axis=0) - source_points.mean(axis=0)).astype(int))
            if delta != (0, 0):
                shifts.append(delta)
        if not shifts:
            return []

        ranked = Counter(shifts).most_common(3)
        candidates = []
        for (delta_row, delta_col), support in ranked:
            candidates.append(self._single_step_candidate(
                "translate",
                {
                    "delta_row": int(delta_row),
                    "delta_col": int(delta_col),
                    "translation": [int(delta_row), int(delta_col)],
                    "translation_per_object": {"obj_1": [int(delta_row), int(delta_col)]},
                    "movable_objects": ["obj_1"],
                },
                min(0.95, 0.70 + support * 0.08),
                min(1.0, support / max(len(shifts), 1)),
                {
                    "observation": "object_centroid_shift",
                    "delta": [int(delta_row), int(delta_col)],
                },
            ))
        return candidates

    def _recolor_candidates(self, source, target, concepts):
        color_report = self.color_mapping_engine.analyze(
            input_grid=source,
            output_grid=target,
            concept_report={"concepts": concepts},
        )
        selected_program = color_report.get("selected_program", {})
        steps = selected_program.get("steps", []) or []
        if not steps:
            return []
        step = steps[0]
        parameters = step.get("parameters", {})
        mapping = parameters.get("mapping", {})
        if not mapping:
            return []
        return [self._single_step_candidate(
            "recolor",
            parameters,
            color_report.get("mapping_confidence", 0.0),
            max(
                color_report.get("mapping_confidence", 0.0),
                color_report.get("program_accuracy", 0.0),
            ),
            {
                "observation": "explicit_color_mapping_reasoning",
                "COLOR_MAPPING_REPORT": color_report.get(
                    "COLOR_MAPPING_REPORT",
                    {},
                ),
                "mapping_matrix": color_report.get("mapping_matrix", {}),
            },
        )]

    def _rotation_candidates(self, source, target):
        candidates = []
        for degrees in [90, 180, 270]:
            if np.array_equal(np.rot90(source, k=degrees // 90), target):
                candidates.append(self._single_step_candidate(
                    "rotate",
                    {"degrees": degrees},
                    0.94,
                    1.0,
                    {"observation": "grid_rotation_match"},
                ))
        return candidates

    def _reflection_candidates(self, source, target):
        candidates = []
        if np.array_equal(np.fliplr(source), target):
            candidates.append(self._single_step_candidate(
                "mirror_horizontal",
                {},
                0.94,
                1.0,
                {"observation": "horizontal_reflection_match"},
            ))
        if np.array_equal(np.flipud(source), target):
            candidates.append(self._single_step_candidate(
                "mirror_vertical",
                {},
                0.94,
                1.0,
                {"observation": "vertical_reflection_match"},
            ))
        return candidates

    def _object_count_candidates(self, source, target):
        source_count = int(np.sum(source != 0))
        target_count = int(np.sum(target != 0))
        if target_count > source_count:
            added = np.argwhere((target != 0) & (source == 0))
            existing = np.argwhere(source != 0)
            if len(added) and len(existing):
                delta = tuple((added[0] - existing[0]).astype(int))
                return [self._single_step_candidate(
                    "duplicate",
                    {"relative_offset": [int(delta[0]), int(delta[1])]},
                    0.80,
                    min(1.0, (target_count - source_count) / max(source_count, 1)),
                    {"observation": "new_nonzero_cells"},
                )]
        if target_count < source_count:
            return [self._single_step_candidate(
                "remove_object",
                {"removed_cell_count": source_count - target_count},
                0.76,
                min(1.0, (source_count - target_count) / max(source_count, 1)),
                {"observation": "nonzero_cells_removed"},
            )]
        return []

    def _growth_candidates(self, source, target, concepts):
        if "growth" not in concepts and "topological_growth" not in concepts:
            return []
        if int(np.sum(target != 0)) <= int(np.sum(source != 0)):
            return []
        return [self._single_step_candidate(
            "grow",
            {},
            0.78,
            0.68,
            {"observation": "area_increase"},
        )]

    def _path_candidates(self, source, target, concepts):
        if not {"path_finding", "route_completion", "bridge_creation", "component_connection"}.intersection(concepts):
            return []
        added = np.argwhere((target != 0) & (source == 0))
        if len(added) == 0:
            return []
        color = int(Counter([int(target[tuple(point)]) for point in added]).most_common(1)[0][0])
        operation = (
            "connect_components"
            if {"bridge_creation", "component_connection"}.intersection(concepts)
            else "construct_path"
        )
        return [self._single_step_candidate(
            operation,
            {"path_color": color},
            0.82,
            0.72,
            {"observation": "added_path_cells", "added_cell_count": int(len(added))},
        )]

    def _fill_candidates(self, source, target, concepts):
        if "region_filling" not in concepts:
            return []
        added = np.argwhere((target != 0) & (source == 0))
        if len(added) == 0:
            return []
        fill_color = int(Counter([int(target[tuple(point)]) for point in added]).most_common(1)[0][0])
        return [self._single_step_candidate(
            "fill_region",
            {"fill_color": fill_color},
            0.80,
            0.70,
            {"observation": "empty_region_filled"},
        )]

    def _composition_candidates(self, candidates):
        recolor = self._first_operation(candidates, "recolor")
        translate = self._first_operation(candidates, "translate")
        if not recolor or not translate:
            return []
        steps = []
        steps.extend(translate["program"].get("steps", []))
        steps.extend(recolor["program"].get("steps", []))
        return [self._candidate(
            "compose",
            self._program(steps),
            min(translate["confidence"], recolor["confidence"]) - 0.03,
            min(translate["support_score"], recolor["support_score"]),
            {"observation": "translation_and_recolor_sequence"},
        )]

    def _score_candidates(self, candidates, input_grid, output_grid, concepts):
        for candidate in candidates:
            program = candidate.get("program", {})
            prediction_accuracy = self._prediction_accuracy(program, input_grid, output_grid)
            candidate["prediction_accuracy"] = prediction_accuracy
            preservation = self._preservation_score(program)
            simplicity = self._simplicity_score(program)
            concept_support = self._concept_support(program, concepts)
            score = (
                candidate.get("confidence", 0.0) * 0.22
                + candidate.get("support_score", 0.0) * 0.16
                + preservation * 0.20
                + simplicity * 0.17
                + prediction_accuracy * 0.20
                + concept_support * 0.05
            )
            candidate["object_preservation"] = preservation
            candidate["color_preservation"] = preservation
            candidate["topology_preservation"] = preservation
            candidate["connectivity_preservation"] = preservation
            candidate["symmetry_preservation"] = preservation
            candidate["transformation_simplicity"] = simplicity
            candidate["score"] = round(float(score), 4)
        return sorted(candidates, key=lambda item: item.get("score", 0.0), reverse=True)

    def _counterfactual_search(self, candidates, input_grid, output_grid, minimum_accuracy):
        if input_grid is None or output_grid is None:
            return candidates
        if candidates and candidates[0].get("prediction_accuracy", 0.0) >= minimum_accuracy:
            return candidates

        variants = []
        for candidate in candidates[:5]:
            step = (candidate.get("program", {}).get("steps", []) or [None])[0]
            if not step or step.get("operation") != "translate":
                continue
            params = step.get("parameters", {})
            row = int(params.get("delta_row", 0))
            col = int(params.get("delta_col", 0))
            for delta_row in [row - 1, row, row + 1]:
                for delta_col in [col - 1, col, col + 1]:
                    if (delta_row, delta_col) == (row, col):
                        continue
                    variants.append(self._single_step_candidate(
                        "translate",
                        {
                            "delta_row": delta_row,
                            "delta_col": delta_col,
                            "translation": [delta_row, delta_col],
                            "translation_per_object": {"obj_1": [delta_row, delta_col]},
                            "movable_objects": ["obj_1"],
                        },
                        max(candidate.get("confidence", 0.0) - 0.05, 0.0),
                        candidate.get("support_score", 0.0),
                        {
                            **candidate.get("evidence", {}),
                            "counterfactual_variant": True,
                        },
                    ))
        if variants:
            candidates.extend(self._score_candidates(variants, input_grid, output_grid, []))
        return sorted(candidates, key=lambda item: item.get("score", 0.0), reverse=True)

    def _prediction_accuracy(self, program, input_grid, output_grid):
        if input_grid is None or output_grid is None:
            return 0.0
        try:
            primitives = [
                {
                    "primitive": self.EXECUTION_ALIASES.get(
                        step.get("operation"),
                        step.get("operation"),
                    ),
                    "parameters": step.get("parameters", {}),
                }
                for step in program.get("steps", []) or []
            ]
            result = self.executor.run_execution(input_grid, primitives)
            predicted = np.array(result.get("output_grid"))
            target = self._array(output_grid)
            if predicted.shape != target.shape:
                return 0.0
            return round(float(np.sum(predicted == target) / max(target.size, 1)), 4)
        except Exception:
            return 0.0

    def _preservation_score(self, program):
        operations = [
            step.get("operation", "")
            for step in program.get("steps", []) or []
        ]
        destructive = {"remove_object", "scale_up", "scale_down", "fill_region", "grow"}
        penalty = sum(0.10 for operation in operations if operation in destructive)
        return round(max(0.0, 1.0 - penalty), 4)

    def _simplicity_score(self, program):
        steps = program.get("steps", []) or []
        cost = sum(self.SIMPLE_COST.get(step.get("operation"), 0.25) for step in steps)
        cost += max(0, len(steps) - 1) * 0.08
        return round(max(0.0, 1.0 - cost), 4)

    def _concept_support(self, program, concepts):
        if not concepts:
            return 0.0
        operations = {
            step.get("operation")
            for step in program.get("steps", []) or []
        }
        supported = 0
        for concept in concepts:
            if operations.intersection(self.CONCEPT_TO_OPERATIONS.get(concept, [])):
                supported += 1
        return supported / max(len(concepts), 1)

    def _candidate(
        self,
        kind,
        program,
        confidence,
        support_score,
        evidence,
        program_reuse=False,
    ):
        return {
            "kind": kind,
            "program": program,
            "confidence": round(float(confidence), 4),
            "support_score": round(float(support_score), 4),
            "evidence": dict(evidence or {}),
            "program_reuse": program_reuse,
        }

    def _single_step_candidate(self, operation, parameters, confidence, support, evidence):
        return self._candidate(
            operation,
            self._program([{
                "operation": operation,
                "parameters": dict(parameters or {}),
            }]),
            confidence,
            support,
            evidence,
        )

    def _program(self, steps):
        return {
            "program_type": "transformation_program",
            "step_count": len(steps),
            "steps": steps,
        }

    def _dedupe_candidates(self, candidates):
        seen = set()
        unique = []
        for candidate in candidates:
            signature = self.memory.build_signature([], candidate.get("program", {}))
            if signature in seen:
                continue
            seen.add(signature)
            unique.append(candidate)
        return unique

    def _build_report(self, concepts, candidates, selected, selected_program):
        selected_steps = selected_program.get("steps", []) or []
        report = {
            "system": self.system_name,
            "detected_concepts": concepts,
            "generated_transformations": [
                candidate.get("program")
                for candidate in candidates
            ],
            "candidate_count": len(candidates),
            "selected_program": selected_program,
            "program_depth": len(selected_steps),
            "transformation_confidence": round(
                float(selected.get("confidence", 0.0)) if selected else 0.0,
                4,
            ),
            "transformation_accuracy": round(
                float(selected.get("prediction_accuracy", 0.0)) if selected else 0.0,
                4,
            ),
            "program_reuse": bool(selected.get("program_reuse", False)) if selected else False,
            "ranked_candidates": candidates,
            "timestamp": str(datetime.utcnow()),
        }
        report["TRANSFORMATION_SYNTHESIS_REPORT"] = {
            key: report[key]
            for key in [
                "detected_concepts",
                "generated_transformations",
                "candidate_count",
                "selected_program",
                "program_depth",
                "transformation_confidence",
                "transformation_accuracy",
                "program_reuse",
            ]
        }
        return report

    def _array(self, grid):
        if hasattr(grid, "grid"):
            return np.array(grid.grid)
        return np.array(grid)

    def _shared_colors(self, source, target):
        return [
            int(color)
            for color in np.unique(source)
            if int(color) != 0 and color in np.unique(target)
        ]

    def _first_operation(self, candidates, operation):
        for candidate in candidates:
            steps = candidate.get("program", {}).get("steps", []) or []
            if steps and steps[0].get("operation") == operation:
                return candidate
        return None


transformation_synthesis_engine = TransformationSynthesisEngine()


__all__ = [
    "TransformationSynthesisEngine",
    "transformation_synthesis_engine",
]
