"""Causal localization layer for object-centric transformations."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from core.perception import ObjectExtractor
from core.world_model import PlacementReasoner


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
    ) -> dict[str, Any]:
        """Localize by comparing the current scene with the target scene."""

        if target_grid is None:
            return self._localization_report(
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

        placement = self.placement_reasoner.reason(
            input_grid,
            target_grid,
            operation=operation,
            position_rule=position_rule,
            search_radius=search_radius,
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
        objects = self._objects(input_grid)
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
        return self._localization_report(
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

    def localize_program(
        self,
        input_grid: Any,
        target_grid: Any | None,
        synthesized_program: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Return a localized copy of a synthesized program."""

        program = deepcopy(synthesized_program or {})
        steps = list(program.get("steps", []))
        reports = []
        localized_steps = []
        for step in steps:
            localized_step = dict(step)
            operation = localized_step.get("operation")
            parameters = dict(localized_step.get("parameters", {}) or {})
            if operation == "duplicate_object":
                report = self.localize_from_grids(
                    input_grid,
                    target_grid,
                    operation=operation,
                    position_rule=parameters,
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
            localized_steps.append(localized_step)

        program["steps"] = localized_steps
        program["step_count"] = len(localized_steps)
        ready = bool(reports) and all(report["localization_ready"] for report in reports)
        return {
            "system": self.system_name,
            "localized_program": program,
            "localization_reports": reports,
            "localization_ready": ready,
            "localized_step_count": sum(
                1
                for report in reports
                if report.get("localization_ready")
            ),
        }

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
