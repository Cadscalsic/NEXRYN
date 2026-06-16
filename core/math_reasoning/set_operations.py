"""Passive mathematical set operations for ARC objects, grids, and graph nodes."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.math_reasoning.graph_relations import GraphRelationsEngine
from core.math_reasoning.spatial_relations import SpatialRelationsEngine, normalize_object


NormalizedSet = dict[str, Any]


class SetOperationsEngine:
    """Reason over ARC data as deterministic mathematical sets."""

    system_name = "set_operations_engine"

    def normalize_set(self, set_like: Any) -> NormalizedSet:
        if isinstance(set_like, Mapping):
            name = str(set_like.get("name", "set"))
            items = set_like.get("items", [])
        else:
            name = "set"
            items = set_like
        item_map = {_item_key(item): _item_value(item) for item in items or []}
        keys = set(item_map)
        return {
            "name": name,
            "items": _sorted_values(keys, item_map),
            "item_keys": keys,
            "item_map": item_map,
            "size": len(keys),
        }

    def union(self, set_a: Any, set_b: Any) -> dict[str, Any]:
        a, b = self.normalize_set(set_a), self.normalize_set(set_b)
        item_map = {**a["item_map"], **b["item_map"]}
        result_keys = a["item_keys"] | b["item_keys"]
        return self._operation_report("union", a, b, result_keys, item_map)

    def intersection(self, set_a: Any, set_b: Any) -> dict[str, Any]:
        a, b = self.normalize_set(set_a), self.normalize_set(set_b)
        item_map = {**a["item_map"], **b["item_map"]}
        result_keys = a["item_keys"] & b["item_keys"]
        return self._operation_report("intersection", a, b, result_keys, item_map)

    def difference(self, set_a: Any, set_b: Any) -> dict[str, Any]:
        a, b = self.normalize_set(set_a), self.normalize_set(set_b)
        result_keys = a["item_keys"] - b["item_keys"]
        return self._operation_report("difference", a, b, result_keys, a["item_map"])

    def symmetric_difference(self, set_a: Any, set_b: Any) -> dict[str, Any]:
        a, b = self.normalize_set(set_a), self.normalize_set(set_b)
        item_map = {**a["item_map"], **b["item_map"]}
        result_keys = a["item_keys"] ^ b["item_keys"]
        return self._operation_report("symmetric_difference", a, b, result_keys, item_map)

    def is_subset(self, set_a: Any, set_b: Any) -> bool:
        a, b = self.normalize_set(set_a), self.normalize_set(set_b)
        return a["item_keys"].issubset(b["item_keys"])

    def is_superset(self, set_a: Any, set_b: Any) -> bool:
        a, b = self.normalize_set(set_a), self.normalize_set(set_b)
        return a["item_keys"].issuperset(b["item_keys"])

    def is_disjoint(self, set_a: Any, set_b: Any) -> bool:
        a, b = self.normalize_set(set_a), self.normalize_set(set_b)
        return a["item_keys"].isdisjoint(b["item_keys"])

    def jaccard_similarity(self, set_a: Any, set_b: Any) -> float:
        a, b = self.normalize_set(set_a), self.normalize_set(set_b)
        union_size = len(a["item_keys"] | b["item_keys"])
        if union_size == 0:
            return 1.0
        return round(len(a["item_keys"] & b["item_keys"]) / union_size, 4)

    def overlap_ratio(self, set_a: Any, set_b: Any) -> float:
        a, b = self.normalize_set(set_a), self.normalize_set(set_b)
        smaller_size = min(a["size"], b["size"])
        if smaller_size == 0:
            return 1.0 if a["size"] == b["size"] else 0.0
        return round(len(a["item_keys"] & b["item_keys"]) / smaller_size, 4)

    def containment_score(self, set_a: Any, set_b: Any) -> float:
        a, b = self.normalize_set(set_a), self.normalize_set(set_b)
        if a["size"] == 0:
            return 1.0
        return round(len(a["item_keys"] & b["item_keys"]) / a["size"], 4)

    def set_signature(self, set_like: Any) -> dict[str, Any]:
        normalized = self.normalize_set(set_like)
        return {
            "name": normalized["name"],
            "size": normalized["size"],
            "items": normalized["items"],
            "item_types": sorted({_type_name(item) for item in normalized["items"]}),
        }

    def compare_sets(self, set_a: Any, set_b: Any) -> dict[str, Any]:
        a, b = self.normalize_set(set_a), self.normalize_set(set_b)
        item_map = {**a["item_map"], **b["item_map"]}
        intersection_keys = a["item_keys"] & b["item_keys"]
        union_keys = a["item_keys"] | b["item_keys"]
        added_keys = b["item_keys"] - a["item_keys"]
        removed_keys = a["item_keys"] - b["item_keys"]
        return {
            "system": self.system_name,
            "set_a": a["name"],
            "set_b": b["name"],
            "a_size": a["size"],
            "b_size": b["size"],
            "intersection_size": len(intersection_keys),
            "union_size": len(union_keys),
            "added_items": _sorted_values(added_keys, item_map),
            "removed_items": _sorted_values(removed_keys, item_map),
            "preserved_items": _sorted_values(intersection_keys, item_map),
            "jaccard_similarity": self.jaccard_similarity(a, b),
            "relation": self._classify_relation(a, b),
        }

    def cells_of_object(self, object_item: Mapping[str, Any]) -> dict[str, Any]:
        obj = normalize_object(object_item)
        return {"name": f"{obj['id']}_cells", "items": obj["cells"]}

    def colors_of_grid(self, grid: Any) -> dict[str, Any]:
        normalized = _normalize_grid(grid)
        colors = [value for row in normalized for value in row]
        return {"name": "grid_colors", "items": colors}

    def nonzero_cells(self, grid: Any) -> dict[str, Any]:
        normalized = _normalize_grid(grid)
        cells = [
            (row_index, col_index)
            for row_index, row in enumerate(normalized)
            for col_index, value in enumerate(row)
            if int(value) != 0
        ]
        return {"name": "nonzero_cells", "items": cells}

    def object_ids(self, objects: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        ids = [
            normalize_object(obj, fallback_id=f"object_{index + 1}")["id"]
            for index, obj in enumerate(objects)
        ]
        return {"name": "object_ids", "items": ids}

    def objects_by_color(self, objects: Iterable[Mapping[str, Any]], color: Any) -> dict[str, Any]:
        ids = []
        for index, obj in enumerate(objects):
            normalized = normalize_object(obj, fallback_id=f"object_{index + 1}")
            if normalized.get("color") == color:
                ids.append(normalized["id"])
        return {"name": f"objects_color_{color}", "items": ids}

    def group_by_color(self, objects: Iterable[Mapping[str, Any]]) -> dict[Any, dict[str, Any]]:
        groups: dict[Any, list[str]] = {}
        for index, obj in enumerate(objects):
            normalized = normalize_object(obj, fallback_id=f"object_{index + 1}")
            groups.setdefault(normalized.get("color"), []).append(normalized["id"])
        return {
            color: {"name": f"objects_color_{color}", "items": sorted(ids)}
            for color, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        }

    def group_by_area(self, objects: Iterable[Mapping[str, Any]]) -> dict[int, dict[str, Any]]:
        groups: dict[int, list[str]] = {}
        for index, obj in enumerate(objects):
            normalized = normalize_object(obj, fallback_id=f"object_{index + 1}")
            groups.setdefault(int(normalized.get("area", 0)), []).append(normalized["id"])
        return {
            area: {"name": f"objects_area_{area}", "items": sorted(ids)}
            for area, ids in sorted(groups.items())
        }

    def compare_input_output_cells(
        self,
        input_objects: Iterable[Mapping[str, Any]],
        output_objects: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        input_cells = [
            cell
            for obj in input_objects
            for cell in normalize_object(obj).get("cells", [])
        ]
        output_cells = [
            cell
            for obj in output_objects
            for cell in normalize_object(obj).get("cells", [])
        ]
        report = self.compare_sets(
            {"name": "input_object_cells", "items": input_cells},
            {"name": "output_object_cells", "items": output_cells},
        )
        report["use_cases"] = self._cell_use_cases(report)
        return report

    def compare_input_output_colors(self, input_grid: Any, output_grid: Any) -> dict[str, Any]:
        input_colors = self.colors_of_grid(input_grid)
        output_colors = self.colors_of_grid(output_grid)
        input_colors["name"] = "input_colors"
        output_colors["name"] = "output_colors"
        report = self.compare_sets(input_colors, output_colors)
        report["color_preservation"] = report["removed_items"] == []
        report["color_change"] = bool(report["added_items"] or report["removed_items"])
        return report

    def compare_object_groups(
        self,
        input_objects: Iterable[Mapping[str, Any]],
        output_objects: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        report = self.compare_sets(
            self.object_ids(input_objects) | {"name": "input_object_ids"},
            self.object_ids(output_objects) | {"name": "output_object_ids"},
        )
        report["object_count_growth"] = report["b_size"] > report["a_size"]
        report["object_removal"] = bool(report["removed_items"])
        return report

    def analyze_from_graph(self, graph: Mapping[str, Any]) -> dict[str, Any]:
        return self.set_signature(
            {
                "name": "graph_nodes",
                "items": [node.get("id") for node in graph.get("nodes", [])],
            }
        )

    def build_graph_node_set(
        self,
        objects: Iterable[Mapping[str, Any]],
        spatial_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        graph = GraphRelationsEngine().build_graph(objects, spatial_report)
        return {"name": "graph_nodes", "items": [node["id"] for node in graph["nodes"]]}

    def analyze_spatial_object_set(self, objects: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        spatial_report = SpatialRelationsEngine().analyze(objects)
        return self.build_graph_node_set(objects, spatial_report)

    def _operation_report(
        self,
        operation: str,
        set_a: NormalizedSet,
        set_b: NormalizedSet,
        result_keys: set[tuple[str, Any]],
        item_map: Mapping[tuple[str, Any], Any],
    ) -> dict[str, Any]:
        result = _sorted_values(result_keys, item_map)
        return {
            "system": self.system_name,
            "operation": operation,
            "set_a": set_a["name"],
            "set_b": set_b["name"],
            "result": result,
            "result_size": len(result),
            "evidence": {
                "a_size": set_a["size"],
                "b_size": set_b["size"],
            },
        }

    def _classify_relation(self, set_a: NormalizedSet, set_b: NormalizedSet) -> str:
        a_keys = set_a["item_keys"]
        b_keys = set_b["item_keys"]
        transformation_context = self._is_transformation_context(set_a["name"], set_b["name"])
        if a_keys == b_keys:
            return "equal"
        if not a_keys & b_keys:
            return "disjoint"
        if a_keys < b_keys:
            return "expanded" if transformation_context else "subset"
        if a_keys > b_keys:
            return "reduced" if transformation_context else "superset"
        if a_keys.issubset(b_keys):
            return "subset"
        if a_keys.issuperset(b_keys):
            return "superset"
        if len(a_keys) == len(b_keys):
            return "transformed"
        return "partial_overlap"

    def _cell_use_cases(self, report: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "shape_cell_preservation": report["removed_items"] == [] and report["added_items"] == [],
            "topology_cell_change": bool(report["added_items"] or report["removed_items"]),
            "source_target_overlap": report["intersection_size"],
            "preserved_region": report["preserved_items"],
            "added_region": report["added_items"],
            "removed_region": report["removed_items"],
            "replication_candidates": report["removed_items"] == [] and bool(report["added_items"]),
        }

    def _is_transformation_context(self, set_a_name: str, set_b_name: str) -> bool:
        return set_a_name.startswith("input_") and set_b_name.startswith("output_")


def _normalize_grid(grid: Any) -> list[list[int]]:
    if grid is None:
        return []
    source = grid
    for method_name in ("to_list", "tolist"):
        method = getattr(source, method_name, None)
        if callable(method):
            source = method()
            break
    for attr_name in ("grid", "data", "cells"):
        if hasattr(source, attr_name):
            source = getattr(source, attr_name)
            break
    try:
        rows = list(source)
    except TypeError:
        return []
    normalized: list[list[int]] = []
    for row in rows:
        values = row.tolist() if hasattr(row, "tolist") else list(row)
        normalized.append([int(value) for value in values])
    return normalized


def _item_key(item: Any) -> tuple[str, Any]:
    if isinstance(item, tuple):
        return ("sequence", tuple(_item_key(value) for value in item))
    if isinstance(item, list):
        return ("sequence", tuple(_item_key(value) for value in item))
    if isinstance(item, Mapping):
        return ("mapping", tuple(sorted((str(key), _item_key(value)) for key, value in item.items())))
    return (_type_name(item), item)


def _item_value(item: Any) -> Any:
    if isinstance(item, tuple):
        return [_item_value(value) for value in item]
    if isinstance(item, list):
        return [_item_value(value) for value in item]
    if isinstance(item, Mapping):
        return {str(key): _item_value(value) for key, value in sorted(item.items())}
    return item


def _sorted_values(keys: Iterable[tuple[str, Any]], item_map: Mapping[tuple[str, Any], Any]) -> list[Any]:
    return [item_map[key] for key in sorted(keys, key=lambda item: repr(item))]


def _type_name(item: Any) -> str:
    if isinstance(item, (tuple, list)):
        return "sequence"
    if isinstance(item, Mapping):
        return "mapping"
    return type(item).__name__


__all__ = ["SetOperationsEngine"]
