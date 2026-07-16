"""Transformation synthesis between concept attribution and execution."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Mapping

import numpy as np

from runtime.memory.transformation_memory import transformation_memory
from runtime.reasoning.color_mapping_engine import color_mapping_engine
from runtime.reasoning.mechanistic_reasoning_engine import mechanistic_reasoning_engine
from runtime.reasoning.transformation_explanation_engine import transformation_explanation_engine
from runtime.reasoning.transformation_language_engine import transformation_language_engine
from runtime.reasoning.transformation_theory_engine import transformation_theory_engine
from runtime.semantic_routing import cognitive_context_router, semantic_intent_router
from runtime.transformation_compilation import semantic_to_transformation_compiler
from runtime.transforms import primitive_executor


class TransformationSynthesisEngine:
    """Infer executable transformation programs from observations."""

    system_name = "transformation_synthesis_engine"

    CONCEPT_TO_OPERATIONS = {
        "density_increase": ["expand", "grow", "fill_region", "duplicate"],
        "object_creation": ["duplicate"],
        "symmetry_creation": ["duplicate", "mirror_horizontal", "mirror_vertical"],
        "object_counting": ["duplicate", "remove_object", "select_object"],
        "cardinality": ["select_object"],
        "quantity_preservation": ["select_object"],
        "quantity_transformation": ["duplicate", "remove_object"],
        "numerical_reasoning": ["select_object"],
        "set_reasoning": ["select_object"],
        "gravity": ["translate"],
        "gravity_simulation": ["translate"],
        "falling": ["translate"],
        "support": ["translate"],
        "collision": ["translate", "connect_components"],
        "rest_state": ["translate"],
        "downward_motion": ["translate"],
        "rotation_reflection": ["rotate", "mirror_horizontal", "mirror_vertical"],
        "orientation_change": ["rotate"],
        "relative_position": ["translate"],
        "spatial_relation": ["translate"],
        "object_translation": ["translate"],
        "directional_motion": ["translate"],
        "symbolic_remapping": ["recolor"],
        "color_mapping": ["recolor"],
        "color_elimination": ["recolor"],
        "pattern_completion": ["fill_region"],
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
        "object_identity_preservation": ["select_object"],
        "shape_preservation": ["select_object"],
        "object_selection": ["select_object"],
        "region_filling": ["fill_region"],
        "scaling": ["scale_up", "scale_down"],
    }

    CONCEPT_SEMANTICS = {
        "density_increase": {
            "candidate_meanings": [
                "object_expansion_around_centroid",
                "axis_growth",
                "region_fill",
                "object_duplication",
            ],
            "reference_frames": [
                "object_centroid",
                "object_bounding_box",
                "grid_axis",
                "local_neighborhood",
            ],
        },
        "relative_position": {
            "candidate_meanings": [
                "object_translation",
                "anchor_relative_placement",
                "centroid_shift",
                "neighbor_relation_preservation",
            ],
            "reference_frames": [
                "source_object",
                "target_object",
                "object_centroid",
                "grid_origin",
            ],
        },
        "spatial_relation": {
            "candidate_meanings": [
                "relation_preservation",
                "anchor_relative_placement",
                "component_connection",
            ],
            "reference_frames": [
                "neighbor_object",
                "object_bounding_box",
                "grid_axis",
            ],
        },
        "color_mapping": {
            "candidate_meanings": [
                "symbolic_color_substitution",
                "palette_remapping",
                "object_color_rebinding",
            ],
            "reference_frames": [
                "color_class",
                "object_identity",
                "global_palette",
            ],
        },
        "symbolic_remapping": {
            "candidate_meanings": [
                "symbolic_color_substitution",
                "class_label_rebinding",
            ],
            "reference_frames": [
                "symbol_class",
                "color_class",
            ],
        },
        "transformation_sequence": {
            "candidate_meanings": [
                "ordered_operation_composition",
                "multi_step_state_transition",
                "mechanism_graph_execution",
            ],
            "reference_frames": [
                "previous_state",
                "intermediate_state",
                "program_order",
            ],
        },
        "gravity": {
            "candidate_meanings": [
                "falling_simulation",
                "support_detection",
                "collision_resolution",
                "rest_state_detection",
            ],
            "reference_frames": [
                "grid_down_axis",
                "support_surface",
                "object_cells",
            ],
        },
        "gravity_simulation": {
            "candidate_meanings": [
                "falling_simulation",
                "support_detection",
                "collision_resolution",
                "rest_state_detection",
            ],
            "reference_frames": [
                "grid_down_axis",
                "support_surface",
                "object_cells",
            ],
        },
        "rotation_reflection": {
            "candidate_meanings": [
                "rotation_angle_inference",
                "rotation_center_selection",
                "orientation_update",
                "reflection_axis_selection",
            ],
            "reference_frames": [
                "grid_center",
                "object_centroid",
                "bounding_box_center",
            ],
        },
        "object_counting": {
            "candidate_meanings": [
                "object_grouping",
                "cardinality_extraction",
                "quantity_rule_selection",
                "quantity_transformation",
            ],
            "reference_frames": [
                "object_components",
                "color_groups",
                "set_membership",
            ],
        },
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
        self.transformation_language_engine = transformation_language_engine
        self.transformation_explanation_engine = transformation_explanation_engine
        self.mechanistic_reasoning_engine = mechanistic_reasoning_engine
        self.transformation_theory_engine = transformation_theory_engine
        self.cognitive_context_router = cognitive_context_router
        self.semantic_intent_router = semantic_intent_router
        self.semantic_to_transformation_compiler = semantic_to_transformation_compiler
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
        semantics_report = self._build_semantics_report(
            concepts,
            input_grid,
            output_grid,
        )
        language_report = self.transformation_language_engine.parse(
            concepts,
            runtime_context,
        )
        explanation_report = self.transformation_explanation_engine.explain(
            concepts,
            runtime_context,
            transformation_language_report=language_report,
        )
        theory_report = self.transformation_theory_engine.build_theory(
            concepts,
            runtime_context,
            transformation_explanation_report=explanation_report,
        )
        mechanistic_report = self.mechanistic_reasoning_engine.reason(
            concepts=concepts,
            input_grid=input_grid,
            output_grid=output_grid,
            runtime_context=runtime_context,
            transformation_theory_report=theory_report,
            transformation_explanation_report=explanation_report,
        )
        context_routing_report = self.cognitive_context_router.route(
            concepts,
            runtime_context=runtime_context,
            semantic_context_report=semantic_context_report,
        )
        routed_concepts = context_routing_report.get("routed_concepts") or concepts
        semantic_intent_report = self.semantic_intent_router.route(
            detected_concepts=routed_concepts,
            runtime_context=runtime_context,
            concept_report=concept_report,
        )
        candidates = []
        candidates.extend(self._memory_candidates(concepts))
        candidates.extend(self._explanation_candidates(explanation_report, input_grid, output_grid))
        candidates.extend(self._mechanism_candidates(mechanistic_report))
        candidates.extend(self._concept_candidates(concepts, semantics_report))
        candidates.extend(self._observation_candidates(input_grid, output_grid, concepts))
        compiler_report = self.semantic_to_transformation_compiler.compile(
            input_grid=input_grid,
            output_grid=output_grid,
            detected_concepts=routed_concepts,
            runtime_context=runtime_context,
            execution_intents=semantic_intent_report.get("execution_intents", []),
            semantic_intent_report=semantic_intent_report,
        )
        candidates.extend(self._semantic_compiler_candidates(compiler_report))

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
            language_report,
            explanation_report,
            theory_report,
            semantics_report,
            mechanistic_report,
            context_routing_report,
            compiler_report,
            semantic_intent_report,
        )
        self.synthesis_history.append(report)
        return report

    def _explanation_candidates(self, explanation_report, input_grid, output_grid):
        selected = explanation_report.get("selected_explanation", {})
        if not isinstance(selected, Mapping):
            return []
        explanation_id = selected.get("explanation_id")
        candidates = []
        if explanation_id == "symbolic_color_remapping":
            candidates.extend(self._recolor_candidates(
                self._array(input_grid),
                self._array(output_grid),
                ["symbolic_remapping", "color_mapping"],
            ))
            for candidate in candidates:
                candidate["kind"] = "explanation:symbolic_color_remapping"
                candidate.setdefault("evidence", {})["transformation_explanation"] = selected
            return candidates
        if explanation_id in {"symmetric_object_creation", "quantity_rule_transformation"}:
            source = self._array(input_grid)
            target = self._array(output_grid)
            if source.size and target.size and int(np.sum(target != 0)) > int(np.sum(source != 0)):
                return [self._single_step_candidate(
                    "duplicate",
                    {
                        "macro_concept": selected.get("macro_concept"),
                        "transformation_explanation": selected,
                    },
                    selected.get("explanation_confidence", 0.70),
                    selected.get("explanation_confidence", 0.70),
                    {
                        "source": "transformation_explanation",
                        "transformation_explanation": selected,
                    },
                )]
        return []

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

    def _build_semantics_report(self, concepts, input_grid=None, output_grid=None):
        interpretations = []
        source = self._array(input_grid) if input_grid is not None else None
        target = self._array(output_grid) if output_grid is not None else None
        density_delta = None
        if source is not None and target is not None and source.size and target.size:
            source_density = float(np.sum(source != 0) / max(source.size, 1))
            target_density = float(np.sum(target != 0) / max(target.size, 1))
            density_delta = round(target_density - source_density, 4)

        for concept in concepts:
            spec = self.CONCEPT_SEMANTICS.get(concept, {})
            operations = list(self.CONCEPT_TO_OPERATIONS.get(concept, []))
            meanings = list(spec.get("candidate_meanings", []))
            reference_frames = list(spec.get("reference_frames", []))
            if not meanings and operations:
                meanings = [f"{operation}_mechanism" for operation in operations]
            if not reference_frames:
                reference_frames = ["grid", "object"]
            interpretation = {
                "concept": concept,
                "candidate_meanings": meanings,
                "candidate_operations": operations,
                "reference_frames": reference_frames,
                "selected_meaning": meanings[0] if meanings else None,
                "selected_reference_frame": reference_frames[0] if reference_frames else None,
                "execution_ready": bool(operations),
            }
            if concept == "density_increase" and density_delta is not None:
                interpretation["evidence"] = {
                    "density_delta": density_delta,
                    "density_increased": density_delta > 0.0,
                }
            interpretations.append(interpretation)

        return {
            "system": "transformation_semantics_engine",
            "semantic_interpretations": interpretations,
            "concept_count": len(concepts),
            "transformation_sequence_state": (
                "MECHANISM_GRAPH_REQUIRED"
                if "transformation_sequence" in concepts
                else "NOT_REQUIRED"
            ),
            "execution_ready_concepts": [
                item["concept"]
                for item in interpretations
                if item.get("execution_ready")
            ],
        }

    def _mechanism_candidates(self, mechanistic_report):
        candidates = []
        for graph in mechanistic_report.get("executable_mechanism_graphs", []) or []:
            if not isinstance(graph, Mapping):
                continue
            family = graph.get("family")
            readiness = float(graph.get("execution_readiness", 0.0) or 0.0)
            operations = graph.get("candidate_operations", []) or []
            if family == "gravity" and "translate" in operations:
                fall = self._mechanism_evidence_value(
                    graph,
                    "downward_trajectory_simulation",
                    "fall_distance",
                    0,
                )
                candidates.append(self._single_step_candidate(
                    "translate",
                    {
                        "delta_row": int(fall),
                        "delta_col": 0,
                        "translation": [int(fall), 0],
                        "mechanism_family": family,
                        "mechanism_graph": graph,
                    },
                    max(0.74, readiness),
                    readiness,
                    {
                        "source": "mechanistic_reasoning",
                        "mechanism_family": family,
                        "mechanism_graph": graph,
                    },
                ))
            elif family == "rotation" and "rotate" in operations:
                degrees = self._mechanism_evidence_value(
                    graph,
                    "rotation_angle_inference",
                    "degrees",
                    90,
                )
                candidates.append(self._single_step_candidate(
                    "rotate",
                    {
                        "degrees": int(degrees or 90),
                        "rotation_center": "grid_center",
                        "mechanism_family": family,
                        "mechanism_graph": graph,
                    },
                    max(0.76, readiness),
                    readiness,
                    {
                        "source": "mechanistic_reasoning",
                        "mechanism_family": family,
                        "mechanism_graph": graph,
                    },
                ))
            elif family == "object_counting":
                delta = self._mechanism_evidence_value(
                    graph,
                    "quantity_transformation",
                    "count_delta",
                    0,
                )
                operation = "duplicate" if delta > 0 else "remove_object" if delta < 0 else "select_object"
                candidates.append(self._single_step_candidate(
                    operation,
                    {
                        "count_delta": int(delta),
                        "mechanism_family": family,
                        "mechanism_graph": graph,
                    },
                    max(0.68, readiness),
                    readiness,
                    {
                        "source": "mechanistic_reasoning",
                        "mechanism_family": family,
                        "mechanism_graph": graph,
                    },
                ))
        return candidates

    def _mechanism_evidence_value(self, graph, mechanism, key, default):
        for node in graph.get("nodes", []) or []:
            if not isinstance(node, Mapping):
                continue
            if node.get("mechanism") == mechanism:
                evidence = node.get("evidence", {})
                if isinstance(evidence, Mapping):
                    return evidence.get(key, default)
        return default

    def _concept_candidates(self, concepts, semantics_report=None):
        candidates = []
        semantics_by_concept = {
            item.get("concept"): item
            for item in (semantics_report or {}).get("semantic_interpretations", [])
            if isinstance(item, Mapping)
        }
        for concept in concepts:
            for operation in self.CONCEPT_TO_OPERATIONS.get(concept, []):
                if operation == "compose":
                    continue
                semantics = semantics_by_concept.get(concept, {})
                candidates.append(self._single_step_candidate(
                    operation,
                    {
                        "semantic_concept": concept,
                        "semantic_meaning": semantics.get("selected_meaning"),
                        "reference_frame": semantics.get("selected_reference_frame"),
                    },
                    0.58,
                    0.55,
                    {
                        "concept": concept,
                        "source": "concept_mapping",
                        "semantic_meaning": semantics.get("selected_meaning"),
                        "reference_frame": semantics.get("selected_reference_frame"),
                    },
                ))
        return candidates

    def _observation_candidates(self, input_grid, output_grid, concepts):
        if input_grid is None or output_grid is None:
            return []
        source = self._array(input_grid)
        target = self._array(output_grid)
        candidates = []
        candidates.extend(self._translation_candidates(source, target))
        candidates.extend(self._rotation_candidates(source, target))
        candidates.extend(self._reflection_candidates(source, target))
        if source.shape == target.shape:
            candidates.extend(self._recolor_candidates(source, target, concepts))
            candidates.extend(self._object_count_candidates(source, target))
            candidates.extend(self._density_candidates(source, target, concepts))
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
        if source.ndim == 2 and source.shape[0] == source.shape[1]:
            if np.array_equal(source.T, target):
                candidates.append(self._candidate(
                    "diagonal_reflection",
                    self._program([
                        {
                            "operation": "rotate",
                            "parameters": {"degrees": 90},
                        },
                        {
                            "operation": "mirror_horizontal",
                            "parameters": {},
                        },
                    ]),
                    0.91,
                    1.0,
                    {
                        "observation": "main_diagonal_reflection_match",
                        "composition": ["rotate_90", "mirror_horizontal"],
                    },
                ))
            anti_diagonal = np.fliplr(np.flipud(source.T))
            if np.array_equal(anti_diagonal, target):
                candidates.append(self._candidate(
                    "anti_diagonal_reflection",
                    self._program([
                        {
                            "operation": "rotate",
                            "parameters": {"degrees": 270},
                        },
                        {
                            "operation": "mirror_horizontal",
                            "parameters": {},
                        },
                    ]),
                    0.91,
                    1.0,
                    {
                        "observation": "anti_diagonal_reflection_match",
                        "composition": ["rotate_270", "mirror_horizontal"],
                    },
                ))
        rotated_horizontal = np.fliplr(np.rot90(source, 1))
        if np.array_equal(rotated_horizontal, target):
            candidates.append(self._candidate(
                "rotation_mirror_combination",
                self._program([
                    {
                        "operation": "rotate",
                        "parameters": {"degrees": 90},
                    },
                    {
                        "operation": "mirror_horizontal",
                        "parameters": {},
                    },
                ]),
                0.88,
                1.0,
                {"observation": "rotation_then_horizontal_mirror_match"},
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
        if not {"growth", "topological_growth", "object_expansion"}.intersection(concepts):
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

    def _density_candidates(self, source, target, concepts):
        if "density_increase" not in concepts:
            return []
        source_count = int(np.sum(source != 0))
        target_count = int(np.sum(target != 0))
        if target_count <= source_count:
            return []
        added = np.argwhere((target != 0) & (source == 0))
        evidence = {
            "observation": "density_increase",
            "source_nonzero_count": source_count,
            "target_nonzero_count": target_count,
            "added_cell_count": int(len(added)),
        }
        candidates = [
            self._single_step_candidate(
                "expand",
                {
                    "growth_mode": "around_object",
                    "reference_frame": "object_centroid",
                    "semantic_concept": "density_increase",
                },
                0.83,
                min(1.0, (target_count - source_count) / max(source_count, 1)),
                {
                    **evidence,
                    "semantic_meaning": "object_expansion_around_centroid",
                },
            ),
            self._single_step_candidate(
                "grow",
                {
                    "growth_mode": "axis_growth",
                    "reference_frame": "grid_axis",
                    "semantic_concept": "density_increase",
                },
                0.79,
                min(1.0, (target_count - source_count) / max(source_count, 1)),
                {
                    **evidence,
                    "semantic_meaning": "axis_growth",
                },
            ),
        ]
        if len(added):
            fill_color = int(Counter([int(target[tuple(point)]) for point in added]).most_common(1)[0][0])
            candidates.append(self._single_step_candidate(
                "fill_region",
                {
                    "fill_color": fill_color,
                    "reference_frame": "object_bounding_box",
                    "semantic_concept": "density_increase",
                },
                0.74,
                0.62,
                {
                    **evidence,
                    "semantic_meaning": "region_fill",
                },
            ))
        return candidates

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

    def _semantic_compiler_candidates(self, compiler_report):
        if not isinstance(compiler_report, Mapping):
            return []
        if not compiler_report.get("semantic_to_transformation_compilation_success"):
            return []
        program = compiler_report.get("compiled_program", {})
        validation = compiler_report.get("validation", {})
        if not program.get("steps"):
            return []
        accuracy = float(validation.get("accuracy", 0.0))
        return [self._candidate(
            "semantic_to_transformation_compiler",
            program,
            max(0.86, accuracy),
            max(0.80, accuracy),
            {
                "source": "semantic_to_transformation_compiler",
                "selected_intent": compiler_report.get("selected_intent"),
                "transformation_plan": compiler_report.get("transformation_plan", {}),
                "transformation_graph": compiler_report.get("transformation_graph", {}),
                "compiler_validation": validation,
            },
        )]

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

    def _build_report(
        self,
        concepts,
        candidates,
        selected,
        selected_program,
        language_report,
        explanation_report,
        theory_report,
        semantics_report,
        mechanistic_report,
        context_routing_report,
        compiler_report,
        semantic_intent_report,
    ):
        selected_steps = selected_program.get("steps", []) or []
        report = {
            "system": self.system_name,
            "detected_concepts": concepts,
            "generated_transformations": [
                candidate.get("program")
                for candidate in candidates
            ],
            "candidate_count": len(candidates),
            "transformation_language_report": language_report,
            "transformation_explanation_report": explanation_report,
            "transformation_theory_report": theory_report,
            "transformation_semantics_report": semantics_report,
            "mechanistic_reasoning_report": mechanistic_report,
            "context_routing_report": context_routing_report,
            "semantic_intent_routing_report": semantic_intent_report,
            "semantic_to_transformation_compilation_report": compiler_report,
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
                "transformation_language_report",
                "transformation_explanation_report",
                "transformation_theory_report",
                "transformation_semantics_report",
                "mechanistic_reasoning_report",
                "context_routing_report",
                "semantic_intent_routing_report",
                "semantic_to_transformation_compilation_report",
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
