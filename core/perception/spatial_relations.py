"""Spatial relation analysis for perceived ARC objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from core.epistemic_models import clamp


@dataclass(frozen=True)
class SpatialRelationEvidence:
    source: str
    relation: str
    target: str
    confidence: float
    delta_row: float
    delta_col: float
    manhattan_distance: float
    bbox_gap: int
    axis_alignment: str


class SpatialRelationEngine:
    """Compute object-to-object spatial evidence and placement deltas."""

    def compute_relations(
        self,
        objects: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        relations: list[SpatialRelationEvidence] = []
        for index, source in enumerate(objects):
            for target in objects[index + 1:]:
                relations.extend(self.pairwise_relations(source, target))
        return [asdict(relation) for relation in relations]

    def pairwise_relations(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> list[SpatialRelationEvidence]:
        relations: list[SpatialRelationEvidence] = []
        relation_names = []
        relation_names.extend(self._directional_relation_names(source, target))
        relation_names.extend(self._symmetric_relation_names(source, target))
        for relation in relation_names:
            relations.append(self._relation(source, relation, target))
            if relation in {
                "touching",
                "adjacent",
                "same_color",
                "same_shape",
                "same_canonical_shape",
                "same_size",
                "aligned_row",
                "aligned_col",
                "overlaps_bbox",
                "near",
            }:
                relations.append(self._relation(target, relation, source))
            elif relation == "left_of":
                relations.append(self._relation(target, "right_of", source))
            elif relation == "right_of":
                relations.append(self._relation(target, "left_of", source))
            elif relation == "above":
                relations.append(self._relation(target, "below", source))
            elif relation == "below":
                relations.append(self._relation(target, "above", source))
            elif relation == "contains":
                relations.append(self._relation(target, "inside", source))
            elif relation == "inside":
                relations.append(self._relation(target, "contains", source))
        return relations

    def placement_vector(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> dict[str, Any]:
        source_center = source.get("center", {})
        target_center = target.get("center", {})
        delta_row = round(
            float(target_center.get("row", 0.0))
            - float(source_center.get("row", 0.0)),
            4,
        )
        delta_col = round(
            float(target_center.get("col", 0.0))
            - float(source_center.get("col", 0.0)),
            4,
        )
        return {
            "from_object": source.get("id"),
            "to_object": target.get("id"),
            "delta_row": delta_row,
            "delta_col": delta_col,
            "axis": self._axis(delta_row, delta_col),
            "direction": self._direction_name(delta_row, delta_col),
            "manhattan_distance": round(abs(delta_row) + abs(delta_col), 4),
            "bbox_gap": self.bbox_gap(source.get("bbox", {}), target.get("bbox", {})),
        }

    def describe_added_object(
        self,
        added_object: Mapping[str, Any],
        candidate_sources: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        source = self.best_source_candidate(added_object, candidate_sources)
        if not source:
            return {
                "added_object": added_object.get("id"),
                "source_candidate": None,
                "placement_vector": {},
                "source_relation": {},
                "confidence": 0.0,
            }
        vector = self.placement_vector(source, added_object)
        relation = self._relation(source, "placement_reference", added_object)
        return {
            "added_object": added_object.get("id"),
            "source_candidate": source.get("id"),
            "placement_vector": vector,
            "source_relation": asdict(relation),
            "confidence": self.object_match_score(source, added_object),
        }

    def best_source_candidate(
        self,
        target: Mapping[str, Any],
        candidates: list[Mapping[str, Any]],
    ) -> Mapping[str, Any] | None:
        if not candidates:
            return None
        best = max(
            candidates,
            key=lambda candidate: self.object_match_score(candidate, target),
        )
        return best if self.object_match_score(best, target) > 0 else None

    def object_match_score(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> float:
        score = 0.0
        if source.get("shape_signature") == target.get("shape_signature"):
            score += 0.38
        if source.get("canonical_shape_signature") == target.get(
            "canonical_shape_signature"
        ):
            score += 0.20
        if source.get("color") == target.get("color"):
            score += 0.18
        if source.get("size") == target.get("size"):
            score += 0.16
        if source.get("bbox", {}).get("height") == target.get("bbox", {}).get(
            "height"
        ):
            score += 0.04
        if source.get("bbox", {}).get("width") == target.get("bbox", {}).get(
            "width"
        ):
            score += 0.04
        return clamp(score)

    def bbox_gap(
        self,
        first: Mapping[str, Any],
        second: Mapping[str, Any],
    ) -> int:
        if not first or not second:
            return 0
        row_gap = max(
            int(second["min_row"]) - int(first["max_row"]) - 1,
            int(first["min_row"]) - int(second["max_row"]) - 1,
            0,
        )
        col_gap = max(
            int(second["min_col"]) - int(first["max_col"]) - 1,
            int(first["min_col"]) - int(second["max_col"]) - 1,
            0,
        )
        return max(row_gap, col_gap)

    def _directional_relation_names(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> list[str]:
        relations = []
        source_center = source["center"]
        target_center = target["center"]
        if source_center["col"] < target_center["col"]:
            relations.append("left_of")
        elif source_center["col"] > target_center["col"]:
            relations.append("right_of")
        if source_center["row"] < target_center["row"]:
            relations.append("above")
        elif source_center["row"] > target_center["row"]:
            relations.append("below")
        if self._contains_bbox(source["bbox"], target["bbox"]):
            relations.append("contains")
        elif self._contains_bbox(target["bbox"], source["bbox"]):
            relations.append("inside")
        return relations

    def _symmetric_relation_names(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> list[str]:
        checks = (
            ("touching", self._is_touching(source, target)),
            ("adjacent", self._is_adjacent(source, target)),
            ("same_color", source.get("color") == target.get("color")),
            (
                "same_shape",
                source.get("shape_signature") == target.get("shape_signature"),
            ),
            (
                "same_canonical_shape",
                source.get("canonical_shape_signature")
                == target.get("canonical_shape_signature"),
            ),
            ("same_size", int(source.get("size", -1)) == int(target.get("size", -2))),
            ("aligned_row", source["center"]["row"] == target["center"]["row"]),
            ("aligned_col", source["center"]["col"] == target["center"]["col"]),
            ("overlaps_bbox", self._overlaps_bbox(source["bbox"], target["bbox"])),
            ("near", self.bbox_gap(source["bbox"], target["bbox"]) <= 2),
        )
        return [name for name, enabled in checks if enabled]

    def _relation(
        self,
        source: Mapping[str, Any],
        relation: str,
        target: Mapping[str, Any],
        confidence: float = 1.0,
    ) -> SpatialRelationEvidence:
        vector = self.placement_vector(source, target)
        return SpatialRelationEvidence(
            source=str(source["id"]),
            relation=relation,
            target=str(target["id"]),
            confidence=clamp(confidence),
            delta_row=vector["delta_row"],
            delta_col=vector["delta_col"],
            manhattan_distance=vector["manhattan_distance"],
            bbox_gap=vector["bbox_gap"],
            axis_alignment=vector["axis"],
        )

    def _is_touching(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> bool:
        source_cells = self._cell_set(source)
        target_cells = self._cell_set(target)
        return any(
            (row + d_row, col + d_col) in target_cells
            for row, col in source_cells
            for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )

    def _is_adjacent(
        self,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> bool:
        for source_row, source_col in self._cell_set(source):
            for target_row, target_col in self._cell_set(target):
                d_row = abs(source_row - target_row)
                d_col = abs(source_col - target_col)
                if d_row == 1 and d_col == 1:
                    return True
                if (d_row == 2 and d_col == 0) or (d_row == 0 and d_col == 2):
                    return True
        return False

    def _cell_set(self, obj: Mapping[str, Any]) -> set[tuple[int, int]]:
        return {(int(row), int(col)) for row, col in obj.get("cells", [])}

    def _contains_bbox(
        self,
        outer: Mapping[str, Any],
        inner: Mapping[str, Any],
    ) -> bool:
        if outer == inner:
            return False
        return (
            outer["min_row"] <= inner["min_row"]
            and outer["min_col"] <= inner["min_col"]
            and outer["max_row"] >= inner["max_row"]
            and outer["max_col"] >= inner["max_col"]
        )

    def _overlaps_bbox(
        self,
        first: Mapping[str, Any],
        second: Mapping[str, Any],
    ) -> bool:
        return not (
            first["max_row"] < second["min_row"]
            or second["max_row"] < first["min_row"]
            or first["max_col"] < second["min_col"]
            or second["max_col"] < first["min_col"]
        )

    def _axis(self, delta_row: float, delta_col: float) -> str:
        if delta_row == 0 and delta_col == 0:
            return "same_position"
        if delta_row == 0:
            return "horizontal"
        if delta_col == 0:
            return "vertical"
        return "diagonal"

    def _direction_name(self, delta_row: float, delta_col: float) -> str:
        vertical = "down" if delta_row > 0 else "up" if delta_row < 0 else ""
        horizontal = "right" if delta_col > 0 else "left" if delta_col < 0 else ""
        return "_".join(part for part in [vertical, horizontal] if part) or "same"


__all__ = [
    "SpatialRelationEngine",
    "SpatialRelationEvidence",
]
