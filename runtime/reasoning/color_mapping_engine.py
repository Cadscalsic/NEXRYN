"""Explicit color mapping reasoning for transformation synthesis."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping

import numpy as np

from core.perception.object_extractor import ObjectExtractor
from runtime.memory.color_mapping_memory import color_mapping_memory
from runtime.transforms import primitive_executor


@dataclass
class ColorMappingMatrix:
    """Represent direct, weighted, and conditional color mappings."""

    mapping: dict[str, int] = field(default_factory=dict)
    weighted_mappings: dict[str, dict[str, float]] = field(default_factory=dict)
    conditional_mappings: list[dict[str, Any]] = field(default_factory=list)
    mapping_type: str = "direct"
    scope: str = "global"
    condition_type: str | None = None
    object_color_relationships: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ColorMappingReasoningEngine:
    """Infer executable recolor functions from grid and object evidence."""

    system_name = "color_mapping_reasoning_engine"

    def __init__(self, memory=None, executor=None, object_extractor=None):
        self.memory = memory or color_mapping_memory
        self.executor = executor or primitive_executor
        self.object_extractor = object_extractor or ObjectExtractor()
        self.reasoning_history = []

    def analyze(
        self,
        input_grid=None,
        output_grid=None,
        concept_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        minimum_confidence: float = 0.55,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        input_grid = input_grid if input_grid is not None else runtime_context.get("input_grid")
        output_grid = output_grid if output_grid is not None else runtime_context.get("output_grid")
        if output_grid is None:
            output_grid = runtime_context.get("target_grid")

        source = self._array(input_grid)
        target = self._array(output_grid)
        if source.size == 0 or target.size == 0:
            return self._empty_report()

        input_objects = self.object_extractor.extract_objects(source)
        output_objects = self.object_extractor.extract_objects(target)
        correspondences = self._object_correspondences(input_objects, output_objects)
        detected_changes = self._detected_color_changes(source, target)

        candidates = []
        candidates.extend(self._memory_candidates(source))
        candidates.extend(self._direct_mapping_candidates(source, target))
        candidates.extend(self._global_recolor_candidates(source, target))
        candidates.extend(self._object_specific_candidates(correspondences))
        candidates.extend(self._position_based_candidates(source, target))
        candidates.extend(self._context_candidates(source, target, correspondences, concept_report))
        candidates = self._dedupe_candidates(candidates)
        candidates = self._validate_candidates(candidates, source, target, minimum_confidence)
        candidates = self._counterfactual_search(candidates, source, target)
        candidates = sorted(candidates, key=lambda item: item.get("score", 0.0), reverse=True)

        selected = candidates[0] if candidates else None
        selected_program = (
            selected.get("selected_program")
            if selected
            else self._program({})
        )
        program_accuracy = (
            selected.get("program_accuracy", 0.0)
            if selected
            else 0.0
        )
        validated_mappings = [
            candidate
            for candidate in candidates
            if candidate.get("validated")
        ]

        if selected:
            self.memory.remember(
                selected.get("mapping_matrix", {}),
                program=selected_program,
                accuracy=program_accuracy,
                success=program_accuracy >= 1.0,
                evidence=selected.get("evidence", {}),
            )

        report = {
            "system": self.system_name,
            "detected_color_changes": detected_changes,
            "object_correspondences": correspondences,
            "candidate_mappings": candidates,
            "validated_mappings": validated_mappings,
            "mapping_confidence": round(float(selected.get("confidence", 0.0)) if selected else 0.0, 4),
            "mapping_matrix": selected.get("mapping_matrix", {}) if selected else ColorMappingMatrix().to_dict(),
            "selected_program": selected_program,
            "program_accuracy": round(float(program_accuracy), 4),
            "reuse_hits": len([candidate for candidate in candidates if candidate.get("reuse_hit")]),
            "timestamp": str(datetime.utcnow()),
        }
        report["COLOR_MAPPING_REPORT"] = {
            key: report[key]
            for key in [
                "detected_color_changes",
                "candidate_mappings",
                "validated_mappings",
                "mapping_confidence",
                "mapping_matrix",
                "selected_program",
                "program_accuracy",
                "reuse_hits",
            ]
        }
        self.reasoning_history.append(report)
        return report

    def synthesize_program(
        self,
        input_grid,
        output_grid,
        concept_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.analyze(
            input_grid=input_grid,
            output_grid=output_grid,
            concept_report=concept_report,
        ).get("selected_program", self._program({}))

    def _detected_color_changes(self, source, target):
        input_palette = self._palette(source)
        output_palette = self._palette(target)
        return {
            "input_palette": input_palette,
            "output_palette": output_palette,
            "colors_eliminated": sorted(set(input_palette) - set(output_palette)),
            "colors_introduced": sorted(set(output_palette) - set(input_palette)),
            "palette_changed": input_palette != output_palette,
        }

    def _direct_mapping_candidates(self, source, target):
        if source.shape != target.shape:
            return []
        votes = defaultdict(Counter)
        for source_value, target_value in zip(source.flatten(), target.flatten()):
            source_color = int(source_value)
            target_color = int(target_value)
            if source_color == 0 or target_color == 0:
                continue
            votes[source_color][target_color] += 1
        mapping, weighted = self._mapping_from_votes(votes)
        if not mapping:
            return []
        return [self._candidate(
            ColorMappingMatrix(
                mapping=mapping,
                weighted_mappings=weighted,
                mapping_type="direct",
                scope="global",
            ),
            "cellwise_color_correspondence",
            0.88,
        )]

    def _global_recolor_candidates(self, source, target):
        source_colors = [int(color) for color in np.unique(source) if int(color) != 0]
        target_colors = [int(color) for color in np.unique(target) if int(color) != 0]
        if len(source_colors) <= 1 or len(target_colors) != 1:
            return []
        target_color = target_colors[0]
        mapping = {str(color): target_color for color in source_colors if color != target_color}
        if not mapping:
            return []
        return [self._candidate(
            ColorMappingMatrix(
                mapping=mapping,
                weighted_mappings={
                    str(color): {str(target_color): 1.0}
                    for color in source_colors
                },
                mapping_type="many_to_one",
                scope="global",
            ),
            "global_recoloring",
            0.82,
        )]

    def _object_specific_candidates(self, correspondences):
        conditional = []
        votes = defaultdict(Counter)
        relationships = []
        for match in correspondences:
            source_color = match.get("source_color")
            target_color = match.get("target_color")
            if source_color is None or target_color is None:
                continue
            votes[int(source_color)][int(target_color)] += max(match.get("confidence", 0.0), 0.01)
            relation = {
                "input_object": match.get("input_object"),
                "output_object": match.get("output_object"),
                "source_color": int(source_color),
                "target_color": int(target_color),
                "confidence": round(float(match.get("confidence", 0.0)), 4),
                "support": "object_identity_preserved",
            }
            relationships.append(relation)
            if int(source_color) != int(target_color):
                conditional.append({
                    "condition": {
                        "type": "object_identity",
                        "object_id": match.get("input_object"),
                    },
                    "from": int(source_color),
                    "to": int(target_color),
                    "confidence": round(float(match.get("confidence", 0.0)), 4),
                    "evidence": "shape_topology_centroid_correspondence",
                })
        mapping, weighted = self._mapping_from_votes(votes)
        if not mapping:
            return []
        mapping_type = "object_specific" if conditional else "direct"
        return [self._candidate(
            ColorMappingMatrix(
                mapping=mapping,
                weighted_mappings=weighted,
                conditional_mappings=conditional,
                mapping_type=mapping_type,
                scope="object",
                condition_type="object_identity" if conditional else None,
                object_color_relationships=relationships,
            ),
            "object_correspondence_color_mapping",
            0.90,
        )]

    def _position_based_candidates(self, source, target):
        if source.shape != target.shape:
            return []
        conditional = []
        votes = defaultdict(Counter)
        for color in [int(value) for value in np.unique(source) if int(value) != 0]:
            replacements = Counter(
                int(target[row, col])
                for row, col in np.argwhere(source == color)
                if int(target[row, col]) != 0
            )
            if len(replacements) <= 1:
                continue
            for target_color, count in replacements.items():
                votes[color][target_color] += count
                conditional.append({
                    "condition": {
                        "type": "position",
                        "source_color": color,
                    },
                    "from": color,
                    "to": int(target_color),
                    "support_score": count / max(sum(replacements.values()), 1),
                    "evidence": "same_color_different_replacement_by_location",
                })
        mapping, weighted = self._mapping_from_votes(votes)
        if not conditional:
            return []
        return [self._candidate(
            ColorMappingMatrix(
                mapping=mapping,
                weighted_mappings=weighted,
                conditional_mappings=conditional,
                mapping_type="one_to_many",
                scope="position",
                condition_type="position",
            ),
            "position_based_color_mapping",
            0.72,
        )]

    def _context_candidates(self, source, target, correspondences, concept_report):
        concepts = self._collect_concepts(concept_report)
        context_markers = {
            "inside_outside",
            "containment",
            "topology_change",
            "connectivity_change",
            "symmetry_reasoning",
        }
        if not concepts.intersection(context_markers):
            return []
        base = self._object_specific_candidates(correspondences)
        for candidate in base:
            matrix = candidate["mapping_matrix"]
            matrix["scope"] = "context"
            matrix["condition_type"] = sorted(concepts.intersection(context_markers))[0]
            matrix["mapping_type"] = "context_based"
            candidate["evidence"]["source"] = "contextual_color_mapping"
            candidate["confidence"] = round(min(candidate["confidence"] + 0.03, 0.97), 4)
        return base

    def _memory_candidates(self, source):
        input_colors = [int(color) for color in np.unique(source) if int(color) != 0]
        candidates = []
        for record in self.memory.retrieve_successful(input_colors):
            matrix = record.get("mapping_matrix", {})
            candidates.append({
                "mapping_matrix": matrix,
                "mapping": matrix.get("mapping", {}),
                "confidence": min(0.93, max(record.get("accuracy", 0.0), 0.75)),
                "support_score": 0.80,
                "evidence": {
                    "source": "color_mapping_memory",
                    "memory_signature": record.get("signature"),
                },
                "reuse_hit": True,
                "selected_program": record.get("program", self._program(matrix.get("mapping", {}))),
            })
        return candidates

    def _object_correspondences(self, input_objects, output_objects):
        correspondences = []
        for input_object in input_objects:
            ranked = []
            for output_object in output_objects:
                score, evidence = self._object_match_score(input_object, output_object)
                if score <= 0.0:
                    continue
                ranked.append((score, output_object, evidence))
            if not ranked:
                continue
            ranked.sort(key=lambda item: item[0], reverse=True)
            score, output_object, evidence = ranked[0]
            correspondences.append({
                "input_object": input_object.get("id"),
                "output_object": output_object.get("id"),
                "source_color": input_object.get("color"),
                "target_color": output_object.get("color"),
                "confidence": round(float(score), 4),
                "evidence": evidence,
            })
        return correspondences

    def _object_match_score(self, input_object, output_object):
        evidence = {}
        score = 0.0
        if input_object.get("canonical_shape_signature") == output_object.get("canonical_shape_signature"):
            score += 0.35
            evidence["shape_preserved"] = True
        if input_object.get("size") == output_object.get("size"):
            score += 0.15
            evidence["size_preserved"] = True
        if input_object.get("holes") == output_object.get("holes"):
            score += 0.10
            evidence["topology_preserved"] = True
        input_cells = {tuple(cell) for cell in input_object.get("cells", [])}
        output_cells = {tuple(cell) for cell in output_object.get("cells", [])}
        overlap = len(input_cells.intersection(output_cells)) / max(len(input_cells.union(output_cells)), 1)
        if overlap:
            score += min(0.20, overlap * 0.20)
            evidence["object_overlap"] = round(overlap, 4)
        distance = self._centroid_distance(input_object, output_object)
        centroid_score = max(0.0, 1.0 - distance / 10.0)
        score += centroid_score * 0.20
        evidence["centroid_similarity"] = round(centroid_score, 4)
        return min(score, 1.0), evidence

    def _validate_candidates(self, candidates, source, target, minimum_confidence):
        validated = []
        for candidate in candidates:
            matrix = candidate.get("mapping_matrix", {})
            mapping = matrix.get("mapping", candidate.get("mapping", {}))
            program = candidate.get("selected_program", self._program(mapping))
            accuracy = self._program_accuracy(program, source, target)
            consistency = self._mapping_consistency(mapping, source, target)
            preservation = self._preservation_support(matrix)
            confidence = self._clamp(
                candidate.get("confidence", 0.0) * 0.35
                + candidate.get("support_score", 0.0) * 0.20
                + consistency * 0.15
                + preservation * 0.10
                + accuracy * 0.20
            )
            candidate["selected_program"] = program
            candidate["program_accuracy"] = accuracy
            candidate["mapping_consistency"] = round(consistency, 4)
            candidate["validation"] = {
                "topology_preservation": round(preservation, 4),
                "shape_preservation": round(preservation, 4),
                "identity_preservation": round(preservation, 4),
                "object_consistency": round(candidate.get("support_score", 0.0), 4),
                "region_consistency": round(consistency, 4),
            }
            candidate["confidence"] = round(confidence, 4)
            candidate["validated"] = confidence >= minimum_confidence and bool(mapping)
            candidate["score"] = round(
                confidence * 0.45
                + accuracy * 0.35
                + self._simplicity(mapping) * 0.20,
                4,
            )
            if candidate["validated"]:
                validated.append(candidate)
        return validated

    def _counterfactual_search(self, candidates, source, target):
        if candidates and candidates[0].get("program_accuracy", 0.0) >= 1.0:
            return candidates
        if source.shape != target.shape:
            return candidates
        output_colors = [int(color) for color in np.unique(target) if int(color) != 0]
        variants = []
        for candidate in candidates[:3]:
            mapping = candidate.get("mapping", {})
            for source_color in list(mapping.keys()):
                for target_color in output_colors:
                    if int(mapping[source_color]) == target_color:
                        continue
                    variant_mapping = dict(mapping)
                    variant_mapping[source_color] = target_color
                    variants.append(self._candidate(
                        ColorMappingMatrix(
                            mapping=variant_mapping,
                            weighted_mappings={
                                key: {str(value): 1.0}
                                for key, value in variant_mapping.items()
                            },
                            mapping_type="counterfactual",
                            scope="global",
                        ),
                        "counterfactual_color_search",
                        max(candidate.get("confidence", 0.0) - 0.08, 0.0),
                    ))
        if variants:
            candidates.extend(self._validate_candidates(variants, source, target, 0.0))
        return candidates

    def _candidate(self, matrix: ColorMappingMatrix, evidence_source: str, confidence: float):
        matrix_dict = matrix.to_dict()
        mapping = matrix_dict.get("mapping", {})
        support = self._support_from_weighted(matrix_dict.get("weighted_mappings", {}))
        return {
            "mapping_matrix": matrix_dict,
            "mapping": mapping,
            "confidence": round(float(confidence), 4),
            "support_score": round(float(support), 4),
            "evidence": {
                "source": evidence_source,
                "mapping_entries": [
                    {
                        "from": int(source_color),
                        "to": int(target_color),
                        "confidence": round(float(confidence), 4),
                        "support": evidence_source,
                    }
                    for source_color, target_color in mapping.items()
                ],
            },
            "reuse_hit": False,
        }

    def _mapping_from_votes(self, votes):
        mapping = {}
        weighted = {}
        for source_color, targets in votes.items():
            total = sum(targets.values())
            if total <= 0:
                continue
            target_color, _ = targets.most_common(1)[0]
            if int(source_color) == int(target_color):
                continue
            mapping[str(int(source_color))] = int(target_color)
            weighted[str(int(source_color))] = {
                str(int(color)): round(float(count / total), 4)
                for color, count in targets.items()
            }
        return mapping, weighted

    def _program(self, mapping):
        return {
            "program_type": "color_transformation_program",
            "step_count": 1 if mapping else 0,
            "steps": [
                {
                    "operation": "recolor",
                    "parameters": {
                        "mapping": dict(mapping),
                        "color_mapping": dict(mapping),
                    },
                }
            ] if mapping else [],
        }

    def _program_accuracy(self, program, source, target):
        try:
            primitives = [
                {
                    "primitive": "replace_color"
                    if step.get("operation") == "recolor"
                    else step.get("operation"),
                    "parameters": step.get("parameters", {}),
                }
                for step in program.get("steps", []) or []
            ]
            result = self.executor.run_execution(source, primitives)
            predicted = np.array(result.get("output_grid"))
            if predicted.shape != target.shape:
                return 0.0
            return round(float(np.sum(predicted == target) / max(target.size, 1)), 4)
        except Exception:
            return 0.0

    def _mapping_consistency(self, mapping, source, target):
        if source.shape != target.shape or not mapping:
            return 0.0
        supported = 0
        total = 0
        for source_color, target_color in mapping.items():
            positions = source == int(source_color)
            total += int(np.sum(positions))
            supported += int(np.sum(target[positions] == int(target_color)))
        return supported / max(total, 1)

    def _preservation_support(self, matrix):
        relationships = matrix.get("object_color_relationships", []) or []
        if not relationships:
            return 0.75
        preserved = [
            relation.get("confidence", 0.0)
            for relation in relationships
        ]
        return sum(preserved) / max(len(preserved), 1)

    def _simplicity(self, mapping):
        return max(0.0, 1.0 - len(mapping) * 0.03)

    def _support_from_weighted(self, weighted):
        if not weighted:
            return 0.65
        maxima = []
        for options in weighted.values():
            if options:
                maxima.append(max(float(value) for value in options.values()))
        return sum(maxima) / max(len(maxima), 1)

    def _dedupe_candidates(self, candidates):
        seen = set()
        unique = []
        for candidate in candidates:
            matrix = candidate.get("mapping_matrix", {})
            signature = self.memory.build_signature(
                matrix,
                {
                    "mapping_type": matrix.get("mapping_type"),
                    "scope": matrix.get("scope"),
                    "condition_type": matrix.get("condition_type"),
                },
            )
            if signature in seen:
                continue
            seen.add(signature)
            unique.append(candidate)
        return unique

    def _palette(self, grid):
        return {
            int(color): int(np.sum(grid == color))
            for color in np.unique(grid)
            if int(color) != 0
        }

    def _array(self, grid):
        if grid is None:
            return np.array([])
        if hasattr(grid, "grid"):
            return np.array(grid.grid)
        return np.array(grid)

    def _centroid_distance(self, input_object, output_object):
        input_center = input_object.get("center", {})
        output_center = output_object.get("center", {})
        return abs(float(input_center.get("row", 0.0)) - float(output_center.get("row", 0.0))) + abs(
            float(input_center.get("col", 0.0)) - float(output_center.get("col", 0.0))
        )

    def _collect_concepts(self, source):
        concepts = set()

        def visit(value):
            if isinstance(value, str):
                concepts.add(value.lower().replace("-", "_").replace(" ", "_"))
            elif isinstance(value, Mapping):
                for item in value.values():
                    visit(item)
            elif isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)

        visit(source)
        return concepts

    def _clamp(self, value):
        return max(0.0, min(float(value or 0.0), 1.0))

    def _empty_report(self):
        report = {
            "system": self.system_name,
            "detected_color_changes": {},
            "object_correspondences": [],
            "candidate_mappings": [],
            "validated_mappings": [],
            "mapping_confidence": 0.0,
            "mapping_matrix": ColorMappingMatrix().to_dict(),
            "selected_program": self._program({}),
            "program_accuracy": 0.0,
            "reuse_hits": 0,
            "timestamp": str(datetime.utcnow()),
        }
        report["COLOR_MAPPING_REPORT"] = {
            key: report[key]
            for key in [
                "detected_color_changes",
                "candidate_mappings",
                "validated_mappings",
                "mapping_confidence",
                "mapping_matrix",
                "selected_program",
                "program_accuracy",
                "reuse_hits",
            ]
        }
        return report


color_mapping_engine = ColorMappingReasoningEngine()


__all__ = [
    "ColorMappingMatrix",
    "ColorMappingReasoningEngine",
    "color_mapping_engine",
]
