"""Causal localization layer for object-centric transformations."""

from __future__ import annotations

from copy import deepcopy
import math
import time
from typing import Any, Iterable, Mapping

from core.perception import ObjectExtractor
from core.world_model import PlacementReasoner
from runtime.telemetry.localization_progress import (
    emit as emit_localization_progress,
    grid_shape as telemetry_grid_shape,
    stable_id as telemetry_stable_id,
)


class TransformationLocalizationEngine:
    """Infer where a symbolic transformation should be placed."""

    system_name = "transformation_localization_engine"

    def __init__(
        self,
        placement_reasoner: PlacementReasoner | None = None,
        object_extractor: ObjectExtractor | None = None,
    ) -> None:
        self.placement_reasoner = placement_reasoner or PlacementReasoner()
        self.object_extractor = object_extractor or ObjectExtractor()
        self._localization_call_counter = 0

    def localize(
        self,
        scene_graph: Mapping[str, Any] | None = None,
        object_centroids: Mapping[str, Any] | None = None,
        relative_positions: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None = None,
        adjacency_relations: Iterable[Mapping[str, Any]] | None = None,
        symmetry_axes: Iterable[Any] | None = None,
        empty_space_regions: Iterable[Any] | None = None,
        topology_constraints: Mapping[str, Any] | Iterable[Any] | None = None,
        transformation: Mapping[str, Any] | None = None,
        operation: str | None = None,
    ) -> dict[str, Any]:
        """Localize from already-computed spatial evidence."""

        operation = operation or self._operation_from_transformation(transformation)
        anchor = self._anchor_from_evidence(
            scene_graph=scene_graph,
            object_centroids=object_centroids,
            transformation=transformation,
        )
        offset = self._offset_from_evidence(
            relative_positions=relative_positions,
            transformation=transformation,
        )
        constraints = self._spatial_constraints(
            adjacency_relations=adjacency_relations,
            symmetry_axes=symmetry_axes,
            empty_space_regions=empty_space_regions,
            topology_constraints=topology_constraints,
            offset=offset,
        )
        empty_space_compatible = self._empty_space_compatible(
            empty_space_regions,
            offset,
        )
        topology_preserved = self._topology_preserved(topology_constraints)
        confidence = self._confidence(
            anchor=anchor,
            offset=offset,
            constraints=constraints,
            empty_space_compatible=empty_space_compatible,
            topology_preserved=topology_preserved,
        )
        localization_ready = bool(
            anchor
            and offset is not None
            and empty_space_compatible
            and topology_preserved
            and confidence >= 0.75
        )
        return self._localization_report(
            anchor_object=anchor,
            placement_strategy=self._placement_strategy(operation, offset),
            relative_offset=offset or [0, 0],
            placement_confidence=confidence,
            spatial_constraints=constraints,
            localization_ready=localization_ready,
            empty_space_compatible=empty_space_compatible,
            topology_preserved=topology_preserved,
            evidence={
                "operation": operation,
                "scene_graph_available": isinstance(scene_graph, Mapping),
                "object_centroid_count": len(object_centroids or {}),
                "relative_positions_available": bool(relative_positions),
            },
        )

    def localize_from_grids(
        self,
        input_grid: Any,
        target_grid: Any | None,
        operation: str = "duplicate_object",
        position_rule: Mapping[str, Any] | None = None,
        search_radius: int = 2,
        parent_call_id: str | None = None,
        parent_started_at: float | None = None,
        step_index: int | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Localize by comparing the current scene with the target scene."""

        call_id = f"{parent_call_id or 'localization'}:localize_from_grids:{step_index or 0}"
        started_at = time.perf_counter()
        emit_localization_progress(
            phase="ENTER",
            subcall_name="localize_from_grids",
            call_id=call_id,
            parent_call_id=parent_call_id,
            started_at=started_at,
            parent_started_at=parent_started_at,
            operation=operation,
            step_index=step_index,
            search_radius=search_radius,
            input_grid_shape=telemetry_grid_shape(input_grid),
            target_grid_shape=telemetry_grid_shape(target_grid),
            position_rule_fingerprint=telemetry_stable_id(position_rule or {}),
        )
        if target_grid is None:
            report = self._localization_report(
                anchor_object="",
                placement_strategy="target_scene_missing",
                relative_offset=[0, 0],
                placement_confidence=0.0,
                spatial_constraints=["target_grid_required_for_localization"],
                localization_ready=False,
                empty_space_compatible=False,
                topology_preserved=False,
                evidence={"operation": operation},
            )
            emit_localization_progress(
                phase="EXIT",
                subcall_name="localize_from_grids",
                call_id=call_id,
                parent_call_id=parent_call_id,
                started_at=started_at,
                parent_started_at=parent_started_at,
                exit_reason="target_grid_missing",
                localization_ready=False,
            )
            return report

        placement_call_id = f"{call_id}:placement_reasoning"
        emit_localization_progress(
            phase="ENTER",
            subcall_name="placement_reasoning",
            call_id=placement_call_id,
            parent_call_id=call_id,
            started_at=started_at,
            parent_started_at=started_at,
            operation=operation,
            search_radius=search_radius,
            input_grid_shape=telemetry_grid_shape(input_grid),
            target_grid_shape=telemetry_grid_shape(target_grid),
        )
        placement = self.placement_reasoner.reason(
            input_grid,
            target_grid,
            operation=operation,
            position_rule=position_rule,
            search_radius=search_radius,
            parent_call_id=placement_call_id,
            parent_started_at=started_at,
            runtime_context=runtime_context,
        )
        emit_localization_progress(
            phase="EXIT",
            subcall_name="placement_reasoning",
            call_id=placement_call_id,
            parent_call_id=call_id,
            started_at=started_at,
            parent_started_at=started_at,
            placement_state=placement.get("placement_state"),
            counterfactual_candidate_count=(
                placement.get("position_counterfactuals", {}).get("candidate_count")
                if isinstance(placement.get("position_counterfactuals"), Mapping)
                else None
            ),
        )
        rule = (
            placement.get("recommended_position_rule")
            or placement.get("position_rule")
            or {}
        )
        vector = dict(rule.get("placement_vector", {}))
        anchor = str(
            rule.get("source_object")
            or self._anchor_from_placement(placement)
            or ""
        )
        offset = [
            int(round(float(vector.get("delta_row", 0)))),
            int(round(float(vector.get("delta_col", 0)))),
        ]
        objects_call_id = f"{call_id}:source_object_extraction"
        emit_localization_progress(
            phase="ENTER",
            subcall_name="source_object_extraction",
            call_id=objects_call_id,
            parent_call_id=call_id,
            started_at=started_at,
            parent_started_at=started_at,
            input_grid_shape=telemetry_grid_shape(input_grid),
        )
        objects = self._objects(input_grid)
        emit_localization_progress(
            phase="EXIT",
            subcall_name="source_object_extraction",
            call_id=objects_call_id,
            parent_call_id=call_id,
            started_at=started_at,
            parent_started_at=started_at,
            source_object_count=len(objects),
        )
        source = self._source_object(objects, anchor)
        empty_space_compatible = self._duplicate_region_empty(
            input_grid,
            source,
            offset,
        )
        topology_preserved = self._duplicate_preserves_shape(source, offset)
        constraints = self._constraints_from_placement(
            placement=placement,
            vector=vector,
            empty_space_compatible=empty_space_compatible,
            topology_preserved=topology_preserved,
        )
        base_confidence = float(rule.get("confidence", 0.0) or 0.0)
        if placement.get("placement_state") == "PLACEMENT_REPAIRED_BY_COUNTERFACTUAL":
            base_confidence = max(base_confidence, 0.95)
        confidence = self._clamp(
            base_confidence
            - (0.12 if not empty_space_compatible else 0.0)
            - (0.12 if not topology_preserved else 0.0)
        )
        localization_ready = bool(
            anchor
            and confidence >= 0.75
            and empty_space_compatible
            and topology_preserved
        )
        report = self._localization_report(
            anchor_object=anchor,
            placement_strategy=self._placement_strategy(operation, offset, vector),
            relative_offset=offset,
            placement_confidence=confidence,
            spatial_constraints=constraints,
            localization_ready=localization_ready,
            empty_space_compatible=empty_space_compatible,
            topology_preserved=topology_preserved,
            evidence={
                "operation": operation,
                "placement_reasoning": placement,
                "position_rule": rule,
            },
        )
        emit_localization_progress(
            phase="EXIT",
            subcall_name="localize_from_grids",
            call_id=call_id,
            parent_call_id=parent_call_id,
            started_at=started_at,
            parent_started_at=parent_started_at,
            exit_reason="completed",
            localization_ready=report["localization_ready"],
            source_object_count=len(objects),
        )
        return report

    def localize_program(
        self,
        input_grid: Any,
        target_grid: Any | None,
        synthesized_program: Mapping[str, Any] | None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a localized copy of a synthesized program."""

        started_at = time.perf_counter()
        self._localization_call_counter += 1
        call_id = f"transformation_localization_call_{self._localization_call_counter}"
        program = deepcopy(synthesized_program or {})
        steps = list(program.get("steps", []))
        emit_localization_progress(
            phase="ENTER",
            subcall_name="localize_program",
            call_id=call_id,
            parent_call_id=None,
            started_at=started_at,
            parent_started_at=started_at,
            input_grid_shape=telemetry_grid_shape(input_grid),
            target_grid_shape=telemetry_grid_shape(target_grid),
            program_count=1,
            step_count=len(steps),
            program_fingerprint=telemetry_stable_id(program),
        )
        reports = []
        localized_steps = []
        for step_index, step in enumerate(steps):
            localized_step = dict(step)
            operation = (
                localized_step.get("operation")
                or localized_step.get("operator")
                or localized_step.get("primitive")
            )
            parameters = dict(localized_step.get("parameters", {}) or {})
            if operation == "duplicate_object":
                report = self.localize_from_grids(
                    input_grid,
                    target_grid,
                    operation=operation,
                    position_rule=parameters,
                    parent_call_id=call_id,
                    parent_started_at=started_at,
                    step_index=step_index,
                    runtime_context=runtime_context,
                )
                reports.append(report)
                if report["localization_ready"]:
                    parameters.update({
                        "anchor_object": report["anchor_object"],
                        "source_object": report["anchor_object"],
                        "relative_offset": report["relative_offset"],
                        "delta_row": report["relative_offset"][0],
                        "delta_col": report["relative_offset"][1],
                        "placement_vector": {
                            "delta_row": report["relative_offset"][0],
                            "delta_col": report["relative_offset"][1],
                        },
                        "placement_strategy": report["placement_strategy"],
                        "placement_confidence": report["placement_confidence"],
                        "spatial_constraints": report["spatial_constraints"],
                        "localization_ready": True,
                    })
                    localized_step["parameters"] = parameters
            elif self._is_attribute_mapping_operation(operation):
                report = self.localize_attribute_deltas(
                    input_grid,
                    target_grid,
                    operation=operation,
                    parameters=parameters,
                    parent_call_id=call_id,
                    parent_started_at=started_at,
                    step_index=step_index,
                )
                reports.append(report)
                if report["localization_ready"]:
                    primary_rule = report.get("localized_rules", [{}])[0]
                    parameters.update({
                        "mapping_type": primary_rule.get("mapping_type"),
                        "mapping": primary_rule.get("mapping", {}),
                        "color_mapping": primary_rule.get("mapping", {}),
                        "object_mappings": report.get("object_matches", []),
                        "attribute_deltas": report.get("attribute_deltas", []),
                        "localization_type": primary_rule.get(
                            "localization_type",
                            "color_mapping",
                        ),
                        "localization_ready": True,
                        "localization_confidence": report.get(
                            "localization_confidence",
                            0.0,
                        ),
                    })
                    localized_step["operation"] = "replace_color"
                    localized_step["parameters"] = parameters
            localized_steps.append(localized_step)

        program["steps"] = localized_steps
        program["step_count"] = len(localized_steps)
        ready = bool(reports) and all(report["localization_ready"] for report in reports)
        localization_confidences = [
            float(report.get("localization_confidence", 0.0) or 0.0)
            for report in reports
        ]
        identity_confidences = [
            float(match.get("identity_confidence", 0.0) or 0.0)
            for report in reports
            for match in report.get("object_matches", [])
            if isinstance(match, dict)
        ]
        shape_similarities = [
            float(match.get("shape_similarity", 0.0) or 0.0)
            for report in reports
            for match in report.get("object_matches", [])
            if isinstance(match, dict)
        ]
        topology_preserved = bool(reports) and all(
            bool(match.get("topology_preserved", False))
            for report in reports
            for match in report.get("object_matches", [])
            if isinstance(match, dict)
        )
        result = {
            "system": self.system_name,
            "localized_program": program,
            "localization_reports": reports,
            "localization_ready": ready,
            "localization_confidence": (
                round(min(localization_confidences), 4)
                if localization_confidences
                else 0.0
            ),
            "localized_step_count": sum(
                1
                for report in reports
                if report.get("localization_ready")
            ),
            "identity_confidence": (
                round(min(identity_confidences), 4)
                if identity_confidences
                else 0.0
            ),
            "topology_preserved": topology_preserved,
            "shape_similarity": (
                round(min(shape_similarities), 4)
                if shape_similarities
                else 0.0
            ),
        }
        emit_localization_progress(
            phase="EXIT",
            subcall_name="localize_program",
            call_id=call_id,
            parent_call_id=None,
            started_at=started_at,
            parent_started_at=started_at,
            exit_reason="completed",
            localization_ready=ready,
            localized_step_count=result["localized_step_count"],
            report_count=len(reports),
        )
        return result

    def localize_attribute_deltas(
        self,
        input_grid: Any,
        target_grid: Any | None,
        operation: str | None = None,
        parameters: Mapping[str, Any] | None = None,
        parent_call_id: str | None = None,
        parent_started_at: float | None = None,
        step_index: int | None = None,
    ) -> dict[str, Any]:
        """Match input objects to output objects and derive executable deltas."""

        started_at = time.perf_counter()
        call_id = f"{parent_call_id or 'localization'}:attribute_deltas:{step_index or 0}"
        emit_localization_progress(
            phase="ENTER",
            subcall_name="attribute_delta_localization",
            call_id=call_id,
            parent_call_id=parent_call_id,
            started_at=started_at,
            parent_started_at=parent_started_at,
            operation=operation or "attribute_mapping",
            step_index=step_index,
            input_grid_shape=telemetry_grid_shape(input_grid),
            target_grid_shape=telemetry_grid_shape(target_grid),
        )
        input_objects = self._objects(input_grid)
        output_objects = self._objects(target_grid)
        match_call_id = f"{call_id}:attribute_object_matching"
        emit_localization_progress(
            phase="ENTER",
            subcall_name="attribute_object_matching",
            call_id=match_call_id,
            parent_call_id=call_id,
            started_at=started_at,
            parent_started_at=started_at,
            source_object_count=len(input_objects),
            target_object_count=len(output_objects),
            pair_count=len(input_objects) * len(output_objects),
        )
        object_matches = self._match_objects(input_objects, output_objects)
        emit_localization_progress(
            phase="EXIT",
            subcall_name="attribute_object_matching",
            call_id=match_call_id,
            parent_call_id=call_id,
            started_at=started_at,
            parent_started_at=started_at,
            matched_object_count=len(object_matches),
        )
        attribute_deltas = [
            self._attribute_delta(match)
            for match in object_matches
            if match.get("output_object")
        ]
        localized_rules = self._localized_rules_from_deltas(
            attribute_deltas,
            parameters or {},
        )
        confidence = self._attribute_localization_confidence(
            object_matches,
            localized_rules,
        )
        ready = bool(localized_rules and confidence >= 0.75)
        report = {
            "system": self.system_name,
            "operation": operation or "attribute_mapping",
            "localization_ready": ready,
            "localized_rule_count": len(localized_rules),
            "localized_rules": localized_rules,
            "object_matches": object_matches,
            "attribute_deltas": attribute_deltas,
            "localization_confidence": confidence,
            "matching_features": [
                "centroid_proximity",
                "topology_preservation",
                "size_preservation",
                "shape_similarity",
                "object_identity_continuity",
            ],
            "causal_evidence": {
                "input_object_count": len(input_objects),
                "output_object_count": len(output_objects),
                "matched_object_count": len(object_matches),
            },
        }
        emit_localization_progress(
            phase="EXIT",
            subcall_name="attribute_delta_localization",
            call_id=call_id,
            parent_call_id=parent_call_id,
            started_at=started_at,
            parent_started_at=parent_started_at,
            exit_reason="completed",
            localization_ready=ready,
            source_object_count=len(input_objects),
            target_object_count=len(output_objects),
            matched_object_count=len(object_matches),
        )
        return report

    def _is_attribute_mapping_operation(self, operation: str | None) -> bool:
        name = str(operation or "").lower()
        return name in {
            "replace_color",
            "map_colors",
            "color_mapping",
            "color_transformation",
            "symbolic_remapping",
            "attribute_remapping",
            "position_mapping",
            "size_mapping",
            "shape_mapping",
            "topology_mapping",
        }

    def _match_objects(
        self,
        input_objects: list[Mapping[str, Any]],
        output_objects: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        unmatched_outputs = list(output_objects)
        matches = []
        for input_object in input_objects:
            best_output = None
            best_score = -1.0
            for output_object in unmatched_outputs:
                score = self._identity_score(input_object, output_object)
                if score > best_score:
                    best_score = score
                    best_output = output_object
            if best_output is None:
                continue
            unmatched_outputs.remove(best_output)
            matches.append({
                "input_object_id": input_object.get("id"),
                "output_object_id": best_output.get("id"),
                "input_object": dict(input_object),
                "output_object": dict(best_output),
                "identity_confidence": round(self._clamp(best_score), 4),
                "centroid_delta": self._centroid_delta(
                    input_object,
                    best_output,
                ),
                "topology_preserved": self._object_topology_preserved(
                    input_object,
                    best_output,
                ),
                "size_preserved": input_object.get("size") == best_output.get("size"),
                "shape_similarity": self._shape_similarity(
                    input_object,
                    best_output,
                ),
            })
        return matches

    def _identity_score(
        self,
        input_object: Mapping[str, Any],
        output_object: Mapping[str, Any],
    ) -> float:
        centroid_score = 1.0 / (1.0 + self._centroid_distance(input_object, output_object))
        size_score = 1.0 if input_object.get("size") == output_object.get("size") else 0.45
        shape_score = self._shape_similarity(input_object, output_object)
        topology_score = (
            1.0
            if self._object_topology_preserved(input_object, output_object)
            else 0.5
        )
        continuity_score = 1.0 if input_object.get("id") == output_object.get("id") else 0.65
        return (
            centroid_score * 0.30
            + topology_score * 0.20
            + size_score * 0.20
            + shape_score * 0.20
            + continuity_score * 0.10
        )

    def _attribute_delta(self, match: Mapping[str, Any]) -> dict[str, Any]:
        input_object = match.get("input_object", {})
        output_object = match.get("output_object", {})
        centroid_delta = match.get("centroid_delta", [0, 0])
        return {
            "input_object_id": match.get("input_object_id"),
            "output_object_id": match.get("output_object_id"),
            "color": [
                input_object.get("color"),
                output_object.get("color"),
            ],
            "position": centroid_delta,
            "size": [
                input_object.get("size"),
                output_object.get("size"),
            ],
            "shape": [
                input_object.get("canonical_shape_signature"),
                output_object.get("canonical_shape_signature"),
            ],
            "topology": {
                "holes": [
                    input_object.get("holes"),
                    output_object.get("holes"),
                ],
                "is_solid": [
                    input_object.get("is_solid"),
                    output_object.get("is_solid"),
                ],
            },
            "identity_confidence": match.get("identity_confidence", 0.0),
        }

    def _localized_rules_from_deltas(
        self,
        deltas: list[Mapping[str, Any]],
        parameters: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        rules = []
        color_mapping: dict[str, int] = {}
        for delta in deltas:
            old_color, new_color = delta.get("color", [None, None])
            if old_color is None or new_color is None or old_color == new_color:
                continue
            color_mapping[str(int(old_color))] = int(new_color)
        if not color_mapping:
            explicit = self._explicit_color_mapping(parameters)
            color_mapping.update(explicit)
        if color_mapping:
            rules.append({
                "mapping_type": "object_color_mapping",
                "localization_type": "color_mapping",
                "mapping": color_mapping,
                "confidence": 0.95,
            })
        position_rules = [
            {
                "input_object_id": delta.get("input_object_id"),
                "output_object_id": delta.get("output_object_id"),
                "delta": delta.get("position", [0, 0]),
            }
            for delta in deltas
            if delta.get("position") != [0, 0]
        ]
        if position_rules:
            rules.append({
                "mapping_type": "object_position_mapping",
                "localization_type": "position_mapping",
                "mapping": position_rules,
                "confidence": 0.9,
            })
        for field, mapping_type, localization_type in [
            ("size", "object_size_mapping", "size_mapping"),
            ("shape", "object_shape_mapping", "shape_mapping"),
            ("topology", "object_topology_mapping", "topology_mapping"),
        ]:
            mapping = [
                {
                    "input_object_id": delta.get("input_object_id"),
                    "output_object_id": delta.get("output_object_id"),
                    "delta": delta.get(field),
                }
                for delta in deltas
                if self._changed(delta.get(field))
            ]
            if mapping:
                rules.append({
                    "mapping_type": mapping_type,
                    "localization_type": localization_type,
                    "mapping": mapping,
                    "confidence": 0.85,
                })
        return rules

    def _explicit_color_mapping(
        self,
        parameters: Mapping[str, Any],
    ) -> dict[str, int]:
        mapping = parameters.get("mapping") or parameters.get("color_mapping")
        if isinstance(mapping, Mapping):
            return {
                str(int(old)): int(new)
                for old, new in mapping.items()
            }
        source = parameters.get("source_color")
        target = parameters.get("target_color")
        if source is not None and target is not None:
            return {str(int(source)): int(target)}
        removed = list(parameters.get("removed_colors", []) or [])
        added = list(parameters.get("added_colors", []) or [])
        return {
            str(int(old)): int(new)
            for old, new in zip(removed, added)
        }

    def _attribute_localization_confidence(
        self,
        matches: list[Mapping[str, Any]],
        rules: list[Mapping[str, Any]],
    ) -> float:
        if not matches or not rules:
            return 0.0
        identity = sum(
            float(match.get("identity_confidence", 0.0) or 0.0)
            for match in matches
        ) / len(matches)
        rule_confidence = max(
            float(rule.get("confidence", 0.0) or 0.0)
            for rule in rules
        )
        return round(self._clamp((identity * 0.55) + (rule_confidence * 0.45)), 4)

    def _centroid_distance(
        self,
        input_object: Mapping[str, Any],
        output_object: Mapping[str, Any],
    ) -> float:
        input_center = input_object.get("center", {}) or {}
        output_center = output_object.get("center", {}) or {}
        return math.dist(
            [
                float(input_center.get("row", 0.0)),
                float(input_center.get("col", 0.0)),
            ],
            [
                float(output_center.get("row", 0.0)),
                float(output_center.get("col", 0.0)),
            ],
        )

    def _centroid_delta(
        self,
        input_object: Mapping[str, Any],
        output_object: Mapping[str, Any],
    ) -> list[int]:
        input_center = input_object.get("center", {}) or {}
        output_center = output_object.get("center", {}) or {}
        return [
            int(round(float(output_center.get("row", 0.0)) - float(input_center.get("row", 0.0)))),
            int(round(float(output_center.get("col", 0.0)) - float(input_center.get("col", 0.0)))),
        ]

    def _shape_similarity(
        self,
        input_object: Mapping[str, Any],
        output_object: Mapping[str, Any],
    ) -> float:
        if input_object.get("canonical_shape_signature") == output_object.get(
            "canonical_shape_signature"
        ):
            return 1.0
        input_cells = set(tuple(cell) for cell in input_object.get("normalized_shape", []))
        output_cells = set(tuple(cell) for cell in output_object.get("normalized_shape", []))
        if not input_cells and not output_cells:
            return 1.0
        union = input_cells | output_cells
        if not union:
            return 0.0
        return len(input_cells & output_cells) / len(union)

    def _object_topology_preserved(
        self,
        input_object: Mapping[str, Any],
        output_object: Mapping[str, Any],
    ) -> bool:
        return (
            input_object.get("holes") == output_object.get("holes")
            and input_object.get("is_solid") == output_object.get("is_solid")
        )

    def _changed(self, value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(self._changed(item) for item in value.values())
        if isinstance(value, list) and len(value) == 2:
            return value[0] != value[1]
        return False

    def _operation_from_transformation(
        self,
        transformation: Mapping[str, Any] | None,
    ) -> str:
        if not isinstance(transformation, Mapping):
            return "unknown"
        return str(
            transformation.get("operator")
            or transformation.get("operation")
            or transformation.get("primitive")
            or "unknown"
        )

    def _anchor_from_evidence(
        self,
        scene_graph: Mapping[str, Any] | None,
        object_centroids: Mapping[str, Any] | None,
        transformation: Mapping[str, Any] | None,
    ) -> str:
        if isinstance(transformation, Mapping):
            source = transformation.get("source") or transformation.get("source_object")
            if source:
                return str(source)
        if object_centroids:
            return str(sorted(object_centroids)[0])
        if isinstance(scene_graph, Mapping):
            nodes = scene_graph.get("nodes", {})
            if isinstance(nodes, Mapping) and nodes:
                return str(sorted(nodes)[0])
        return ""

    def _offset_from_evidence(
        self,
        relative_positions: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None,
        transformation: Mapping[str, Any] | None,
    ) -> list[int] | None:
        if isinstance(transformation, Mapping):
            parameters = transformation.get("parameters", {})
            offset = parameters.get("relative_offset") if isinstance(parameters, Mapping) else None
            if offset and len(offset) >= 2:
                return [int(offset[0]), int(offset[1])]
            if isinstance(parameters, Mapping):
                row = parameters.get("delta_row")
                col = parameters.get("delta_col")
                if row is not None or col is not None:
                    return [int(row or 0), int(col or 0)]
        if isinstance(relative_positions, Mapping):
            if "delta_row" in relative_positions or "delta_col" in relative_positions:
                return [
                    int(relative_positions.get("delta_row", 0)),
                    int(relative_positions.get("delta_col", 0)),
                ]
            for value in relative_positions.values():
                offset = self._offset_from_evidence(value, None)
                if offset is not None:
                    return offset
        elif relative_positions:
            for item in relative_positions:
                offset = self._offset_from_evidence(item, None)
                if offset is not None:
                    return offset
        return None

    def _spatial_constraints(
        self,
        adjacency_relations: Iterable[Mapping[str, Any]] | None,
        symmetry_axes: Iterable[Any] | None,
        empty_space_regions: Iterable[Any] | None,
        topology_constraints: Mapping[str, Any] | Iterable[Any] | None,
        offset: list[int] | None,
    ) -> list[Any]:
        constraints = []
        if offset is not None:
            constraints.append({"type": "relative_offset", "value": offset})
        for relation in adjacency_relations or []:
            constraints.append({"type": "adjacency", "value": dict(relation)})
        for axis in symmetry_axes or []:
            constraints.append({"type": "symmetry_axis", "value": axis})
        if empty_space_regions:
            constraints.append({"type": "empty_region_compatibility", "value": True})
        if topology_constraints:
            constraints.append({"type": "topology_preservation", "value": topology_constraints})
        return constraints

    def _constraints_from_placement(
        self,
        placement: Mapping[str, Any],
        vector: Mapping[str, Any],
        empty_space_compatible: bool,
        topology_preserved: bool,
    ) -> list[Any]:
        constraints = [
            {
                "type": "relative_offset",
                "value": [
                    int(round(float(vector.get("delta_row", 0)))),
                    int(round(float(vector.get("delta_col", 0)))),
                ],
            },
            {
                "type": "empty_region_compatibility",
                "value": empty_space_compatible,
            },
            {
                "type": "topology_preservation",
                "value": topology_preserved,
            },
        ]
        for evidence in placement.get("dependency_evidence", []):
            constraints.append({
                "type": "causal_dependency",
                "source": evidence.get("source"),
                "target": evidence.get("target"),
                "confidence": evidence.get("confidence"),
            })
        return constraints

    def _anchor_from_placement(
        self,
        placement: Mapping[str, Any],
    ) -> str:
        graph_reasoning = placement.get("graph_reasoning", {})
        if isinstance(graph_reasoning, Mapping):
            placement_rules = graph_reasoning.get("placement_rules", []) or []
            for rule in placement_rules:
                if isinstance(rule, Mapping) and rule.get("source_object"):
                    return str(rule.get("source_object"))
        position_rule = placement.get("position_rule", {})
        if isinstance(position_rule, Mapping) and position_rule.get("source_object"):
            return str(position_rule.get("source_object"))
        return ""

    def _empty_space_compatible(
        self,
        empty_space_regions: Iterable[Any] | None,
        offset: list[int] | None,
    ) -> bool:
        if offset is None:
            return False
        regions = list(empty_space_regions or [])
        return True if not regions else bool(regions)

    def _topology_preserved(
        self,
        topology_constraints: Mapping[str, Any] | Iterable[Any] | None,
    ) -> bool:
        if not topology_constraints:
            return True
        if isinstance(topology_constraints, Mapping):
            return not bool(topology_constraints.get("forbid_duplication"))
        return True

    def _confidence(
        self,
        anchor: str,
        offset: list[int] | None,
        constraints: list[Any],
        empty_space_compatible: bool,
        topology_preserved: bool,
    ) -> float:
        score = 0.20
        if anchor:
            score += 0.25
        if offset is not None:
            score += 0.25
        if constraints:
            score += 0.15
        if empty_space_compatible:
            score += 0.10
        if topology_preserved:
            score += 0.05
        return round(self._clamp(score), 4)

    def _placement_strategy(
        self,
        operation: str,
        offset: list[int] | None,
        vector: Mapping[str, Any] | None = None,
    ) -> str:
        if not offset:
            return f"{operation}:unlocalized"
        vector = vector or {}
        direction = vector.get("direction")
        axis = vector.get("axis")
        if direction:
            if axis in ["vertical", "horizontal"]:
                return f"{axis}_{direction}"
            return str(direction)
        row, col = offset
        if abs(col) >= abs(row):
            return "horizontal_right" if col >= 0 else "horizontal_left"
        return "vertical_down" if row >= 0 else "vertical_up"

    def _objects(self, grid: Any) -> list[Mapping[str, Any]]:
        normalized = self.object_extractor.normalize_grid(grid)
        return self.object_extractor.extract_objects(normalized)

    def _source_object(
        self,
        objects: list[Mapping[str, Any]],
        anchor: str,
    ) -> Mapping[str, Any] | None:
        for obj in objects:
            if obj.get("id") == anchor:
                return obj
        return objects[0] if objects else None

    def _duplicate_region_empty(
        self,
        grid: Any,
        source: Mapping[str, Any] | None,
        offset: list[int],
    ) -> bool:
        if source is None:
            return False
        normalized = self.object_extractor.normalize_grid(grid)
        if not normalized:
            return False
        height = len(normalized)
        width = len(normalized[0])
        delta_row, delta_col = offset
        for row, col in source.get("cells", []):
            target_row = int(row) + delta_row
            target_col = int(col) + delta_col
            if target_row < 0 or target_row >= height:
                return False
            if target_col < 0 or target_col >= width:
                return False
            if normalized[target_row][target_col] != 0:
                return False
        return True

    def _duplicate_preserves_shape(
        self,
        source: Mapping[str, Any] | None,
        offset: list[int],
    ) -> bool:
        if source is None:
            return False
        return bool(source.get("cells")) and len(offset) == 2

    def _localization_report(
        self,
        anchor_object: str,
        placement_strategy: str,
        relative_offset: list[int],
        placement_confidence: float,
        spatial_constraints: list[Any],
        localization_ready: bool,
        empty_space_compatible: bool,
        topology_preserved: bool,
        evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "anchor_object": anchor_object,
            "placement_strategy": placement_strategy,
            "relative_offset": relative_offset,
            "placement_confidence": round(self._clamp(placement_confidence), 4),
            "spatial_constraints": spatial_constraints,
            "localization_ready": localization_ready,
            "empty_region_compatible": empty_space_compatible,
            "topology_preserved": topology_preserved,
            "causal_evidence": dict(evidence),
        }

    def _clamp(self, value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
        return max(minimum, min(float(value), maximum))


transformation_localization_engine = TransformationLocalizationEngine()


__all__ = [
    "TransformationLocalizationEngine",
    "transformation_localization_engine",
]
