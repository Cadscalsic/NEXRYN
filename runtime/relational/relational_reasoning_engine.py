"""Relational concept reasoning for object-pair symmetry."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


RELATIONAL_CONCEPTS = {
    "symmetry_reasoning",
    "symmetry_analysis",
    "symmetry_relation",
    "reflection_relation",
}


class RelationalReasoningEngine:
    """Build relation-level evidence without redefining intrinsic invariants."""

    system_name = "relational_reasoning_engine"

    def evaluate(
        self,
        concept: str,
        scene_graph_report: Mapping[str, Any] | None = None,
        semantic_context: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        concept = _normalize(concept)
        runtime_context = (
            runtime_context
            if isinstance(runtime_context, Mapping)
            else {}
        )
        semantic_context = (
            semantic_context
            if isinstance(semantic_context, Mapping)
            else runtime_context.get("semantic_context", {})
        )
        scene_graph_report = (
            scene_graph_report
            if isinstance(scene_graph_report, Mapping)
            else runtime_context.get("scene_graph_comparison", {})
        )
        concept_type = (
            "RELATIONAL"
            if concept in RELATIONAL_CONCEPTS or "reasoning" in concept
            else "INTRINSIC"
        )
        explicit_relations = self._explicit_relations(
            runtime_context,
            semantic_context,
        )
        scene_relations = self._scene_symmetry_relations(scene_graph_report)
        symmetry_relations = _dedupe_relations([
            *explicit_relations,
            *scene_relations,
        ])
        symmetry_axis = self._select_axis(
            runtime_context,
            semantic_context,
            symmetry_relations,
        )
        conflicts = self._relation_conflicts(symmetry_relations)
        pair_coverage = clamp(
            len({
                tuple(sorted((item["source"], item["target"])))
                for item in symmetry_relations
                if item.get("source") and item.get("target")
            }) / max(self._object_pair_floor(scene_graph_report), 1)
        )
        relation_confidence = (
            sum(clamp(item.get("confidence", 0.0)) for item in symmetry_relations)
            / len(symmetry_relations)
            if symmetry_relations
            else 0.0
        )
        axis_consistency = clamp(
            sum(
                1
                for item in symmetry_relations
                if not symmetry_axis
                or item.get("axis") in {symmetry_axis, "unknown", ""}
            ) / max(len(symmetry_relations), 1)
        )
        conflict_penalty = min(len(conflicts) * 0.18, 0.54)
        relation_consistency = clamp(
            relation_confidence * 0.48
            + pair_coverage * 0.22
            + axis_consistency * 0.20
            + (0.10 if concept_type == "RELATIONAL" else 0.0)
            - conflict_penalty
        )
        relation_ready = (
            concept_type == "RELATIONAL"
            and bool(symmetry_relations)
            and relation_consistency > 0.82
            and not conflicts
        )

        return {
            "system": self.system_name,
            "concept": concept,
            "concept_type": concept_type,
            "symmetry_relations": symmetry_relations,
            "symmetry_axis": symmetry_axis or "unknown",
            "relation_consistency": round(relation_consistency, 4),
            "relation_ready": relation_ready,
            "relational_conflicts": conflicts,
            "intrinsic_relational_distinction": {
                "symmetry_preservation": "INTRINSIC_INVARIANT",
                "symmetry_reasoning": "RELATIONAL_STRUCTURE",
            },
            "relational_evidence_tokens": [
                "object_observation",
                "symmetry_relation",
                "symmetry_axis",
                "object_pair_mapping",
                "relation_consistency",
                "relational_symmetry",
            ],
        }

    def _explicit_relations(self, *sources):
        relations = []
        for source in sources:
            if not isinstance(source, Mapping):
                continue
            for key in ("symmetry_relations", "relational_pairs"):
                value = source.get(key, [])
                if isinstance(value, Mapping):
                    value = [value]
                if not isinstance(value, Iterable) or isinstance(
                    value,
                    (str, bytes),
                ):
                    continue
                for item in value:
                    relation = self._relation_from_item(item, source)
                    if relation:
                        relations.append(relation)
        return relations

    def _relation_from_item(self, item, source):
        if isinstance(item, Mapping):
            pair = item.get("pair", item.get("objects"))
            if isinstance(pair, Iterable) and not isinstance(pair, (str, bytes)):
                pair = list(pair)
            else:
                pair = []
            source_id = item.get("source", pair[0] if len(pair) > 0 else "")
            target_id = item.get("target", pair[1] if len(pair) > 1 else "")
            if not source_id or not target_id:
                return {}
            return {
                "source": str(source_id),
                "target": str(target_id),
                "relation": _normalize(item.get("relation", "symmetric_pair")),
                "axis": _normalize(
                    item.get("axis", source.get("symmetry_axis", "unknown"))
                ),
                "confidence": clamp(item.get("confidence", 0.88)),
                "evidence_type": "explicit_relational_symmetry",
            }
        return {}

    def _scene_symmetry_relations(self, scene_graph_report):
        if not isinstance(scene_graph_report, Mapping):
            return []
        graphs = []
        for key in ("input_scene_graph", "output_scene_graph"):
            graph = scene_graph_report.get(key)
            if isinstance(graph, Mapping):
                graphs.append(graph)
        if not graphs and "nodes" in scene_graph_report:
            graphs.append(scene_graph_report)

        relations = []
        for graph in graphs:
            relations.extend(self._edge_relations(graph))
            relations.extend(self._inferred_pair_relations(graph))
        return relations

    def _edge_relations(self, graph):
        relations = []
        for edge in graph.get("edges", []):
            if not isinstance(edge, Mapping):
                continue
            relation = _normalize(edge.get("relation"))
            if not any(
                marker in relation
                for marker in ("symmetr", "mirror", "reflect", "opposite")
            ):
                continue
            relations.append({
                "source": str(edge.get("source", "")),
                "target": str(edge.get("target", "")),
                "relation": relation,
                "axis": self._axis_from_relation(relation),
                "confidence": clamp(edge.get("confidence", 0.84)),
                "evidence_type": "scene_graph_relation",
            })
        return [
            item
            for item in relations
            if item["source"] and item["target"]
        ]

    def _inferred_pair_relations(self, graph):
        nodes = graph.get("nodes", {})
        if not isinstance(nodes, Mapping) or len(nodes) < 2:
            return []
        width = float(graph.get("width") or 0)
        height = float(graph.get("height") or 0)
        if width <= 0 and height <= 0:
            return []
        candidates = []
        for (left_id, left), (right_id, right) in combinations(
            sorted(nodes.items()),
            2,
        ):
            if not isinstance(left, Mapping) or not isinstance(right, Mapping):
                continue
            shape_match = (
                left.get("shape_signature") == right.get("shape_signature")
            )
            size_match = left.get("size") == right.get("size")
            if not shape_match or not size_match:
                continue
            left_center = left.get("center", {})
            right_center = right.get("center", {})
            lx = float(left_center.get("x", 0.0))
            ly = float(left_center.get("y", 0.0))
            rx = float(right_center.get("x", 0.0))
            ry = float(right_center.get("y", 0.0))
            vertical_error = (
                abs((lx + rx) - (width - 1)) / max(width - 1, 1)
                + abs(ly - ry) / max(height - 1, 1)
            ) if width else 1.0
            horizontal_error = (
                abs((ly + ry) - (height - 1)) / max(height - 1, 1)
                + abs(lx - rx) / max(width - 1, 1)
            ) if height else 1.0
            axis, error = (
                ("vertical", vertical_error)
                if vertical_error <= horizontal_error
                else ("horizontal", horizontal_error)
            )
            if error <= 0.24:
                candidates.append({
                    "source": str(left_id),
                    "target": str(right_id),
                    "relation": "inferred_symmetric_pair",
                    "axis": axis,
                    "confidence": clamp(1.0 - error),
                    "evidence_type": "inferred_scene_graph_symmetry",
                })
        return candidates

    def _select_axis(self, runtime_context, semantic_context, relations):
        for source in (runtime_context, semantic_context):
            if isinstance(source, Mapping):
                axis = _normalize(source.get("symmetry_axis"))
                if axis:
                    return axis
        axis_scores = {}
        for relation in relations:
            axis = _normalize(relation.get("axis", "unknown"))
            if not axis or axis == "unknown":
                continue
            axis_scores[axis] = axis_scores.get(axis, 0.0) + clamp(
                relation.get("confidence", 0.0)
            )
        if not axis_scores:
            return ""
        return max(axis_scores.items(), key=lambda item: item[1])[0]

    def _relation_conflicts(self, relations):
        conflicts = []
        pair_axes = {}
        for relation in relations:
            pair = tuple(sorted((relation.get("source"), relation.get("target"))))
            axis = _normalize(relation.get("axis", "unknown"))
            if pair in pair_axes and axis not in {pair_axes[pair], "unknown"}:
                conflicts.append({
                    "conflict": "multiple_axes_for_pair",
                    "pair": list(pair),
                    "axes": sorted({pair_axes[pair], axis}),
                })
            if axis != "unknown":
                pair_axes[pair] = axis
        return conflicts

    def _object_pair_floor(self, scene_graph_report):
        if not isinstance(scene_graph_report, Mapping):
            return 1
        summary = scene_graph_report.get("summary", {})
        if isinstance(summary, Mapping):
            count = max(
                int(summary.get("input_object_count", 0) or 0),
                int(summary.get("output_object_count", 0) or 0),
            )
            if count:
                return max(count // 2, 1)
        graph = scene_graph_report.get("input_scene_graph", scene_graph_report)
        nodes = graph.get("nodes", {}) if isinstance(graph, Mapping) else {}
        return max(len(nodes) // 2, 1) if isinstance(nodes, Mapping) else 1

    def _axis_from_relation(self, relation):
        relation = _normalize(relation)
        if "horizontal" in relation or "above_below" in relation:
            return "horizontal"
        if "vertical" in relation or "left_right" in relation:
            return "vertical"
        if "diagonal" in relation:
            return "diagonal"
        return "unknown"


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _dedupe_relations(relations):
    seen = set()
    deduped = []
    for relation in relations:
        key = (
            relation.get("source"),
            relation.get("target"),
            relation.get("relation"),
            relation.get("axis"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(relation)
    return deduped


relational_reasoning_engine = RelationalReasoningEngine()


__all__ = [
    "RelationalReasoningEngine",
    "relational_reasoning_engine",
]
