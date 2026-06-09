"""Build compact scene graphs from perceived objects and spatial relations."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Mapping

from core.perception import ObjectTracker
from core.scene_graph.relation_extractor import RelationExtractor


class SceneGraphBuilder:
    """Construct scene graphs that downstream causal systems can consume."""

    def __init__(
        self,
        relation_extractor: RelationExtractor | None = None,
        object_tracker: ObjectTracker | None = None,
    ) -> None:
        self.relation_extractor = relation_extractor or RelationExtractor()
        self.object_tracker = object_tracker or ObjectTracker()

    def build(self, grid: Any) -> dict[str, Any]:
        extracted = self.relation_extractor.extract_from_grid(grid)
        return self.build_from_objects(
            extracted["objects"],
            extracted["relations"],
        )

    def build_from_objects(
        self,
        objects: list[Mapping[str, Any]],
        relations: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        relation_rows = list(relations or [])
        nodes = {
            str(obj["id"]): {
                "id": obj["id"],
                "color": obj.get("color"),
                "size": obj.get("size"),
                "bbox": obj.get("bbox", {}),
                "center": obj.get("center", {}),
                "shape_signature": obj.get("shape_signature"),
                "canonical_shape_signature": obj.get(
                    "canonical_shape_signature"
                ),
                "shape_analysis": obj.get("shape_analysis", {}),
            }
            for obj in objects
        }
        edges = [
            {
                "source": relation["source"],
                "relation": relation["relation"],
                "target": relation["target"],
                "confidence": relation.get("confidence", 1.0),
                "delta_row": relation.get("delta_row", 0.0),
                "delta_col": relation.get("delta_col", 0.0),
                "axis_alignment": relation.get("axis_alignment", "unknown"),
            }
            for relation in relation_rows
        ]
        graph = {
            "system": "scene_graph_builder",
            "nodes": nodes,
            "edges": edges,
            "adjacency": self._adjacency(edges),
            "relation_index": self._relation_index(edges),
            "relation_triples": self._relation_triples(edges),
        }
        graph["summary"] = self._summary(graph)
        return graph

    def build_comparison(
        self,
        input_grid: Any,
        output_grid: Any,
    ) -> dict[str, Any]:
        """Build a graph whose edges include object identity transitions."""

        input_graph = self.build(input_grid)
        output_graph = self.build(output_grid)
        tracking = self.object_tracker.track(input_grid, output_grid)
        identity_edges = self._identity_edges(
            tracking.get("object_identities", []),
        )
        graph = {
            "system": "scene_graph_builder",
            "mode": "object_identity_comparison",
            "input_scene_graph": input_graph,
            "output_scene_graph": output_graph,
            "nodes": output_graph.get("nodes", {}),
            "edges": [
                *output_graph.get("edges", []),
                *identity_edges,
            ],
            "object_identities": tracking.get("object_identities", []),
            "tracking": tracking,
        }
        graph["adjacency"] = self._adjacency(graph["edges"])
        graph["relation_index"] = self._relation_index(graph["edges"])
        graph["identity_transition_index"] = self._identity_transition_index(
            tracking.get("object_identities", []),
        )
        graph["relation_triples"] = self._relation_triples(graph["edges"])
        graph["summary"] = self._comparison_summary(graph)
        return graph

    def _adjacency(
        self,
        edges: list[Mapping[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        adjacency: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in edges:
            adjacency[str(edge["source"])].append({
                "relation": edge["relation"],
                "target": edge["target"],
                "confidence": edge.get("confidence", 1.0),
            })
        return dict(sorted(adjacency.items()))

    def _relation_index(
        self,
        edges: list[Mapping[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        relation_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in edges:
            relation_index[str(edge["relation"])].append({
                "source": edge["source"],
                "target": edge["target"],
                "confidence": edge.get("confidence", 1.0),
            })
        return dict(sorted(relation_index.items()))

    def _identity_edges(
        self,
        object_identities: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        edges = []
        for identity in object_identities:
            source = identity.get("source_id")
            targets = list(identity.get("targets", []))
            if identity.get("target_id"):
                targets.append(identity["target_id"])
            for target in sorted(set(str(item) for item in targets if item)):
                edges.append({
                    "source": source,
                    "relation": identity.get("transition", "identity_transition"),
                    "target": target,
                    "confidence": identity.get(
                        "confidence",
                        identity.get("continuity_score", 0.0),
                    ),
                    "evidence_type": "object_identity_transition",
                    "continuity_score": identity.get("continuity_score", 0.0),
                    "identity_transition": identity.get(
                        "identity_transition",
                        identity.get("transition_kind"),
                    ),
                })
        return edges

    def _relation_triples(
        self,
        edges: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "subject": edge["source"],
                "predicate": edge["relation"],
                "object": edge["target"],
                "confidence": edge.get("confidence", 1.0),
                "evidence_type": edge.get("evidence_type", "scene_relation"),
            }
            for edge in edges
        ]

    def _identity_transition_index(
        self,
        object_identities: list[Mapping[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        index: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for identity in object_identities:
            transition = str(
                identity.get(
                    "identity_transition",
                    identity.get("transition_kind", "IdentityPreserved"),
                )
            )
            index[transition].append(dict(identity))
        return {
            transition: sorted(
                identities,
                key=lambda item: (
                    str(item.get("source_id")),
                    str(item.get("target_id", "")),
                    ",".join(str(target) for target in item.get("targets", [])),
                ),
            )
            for transition, identities in sorted(index.items())
        }

    def _summary(self, graph: Mapping[str, Any]) -> dict[str, Any]:
        nodes = graph.get("nodes", {})
        edges = graph.get("edges", [])
        relation_counts = Counter(edge["relation"] for edge in edges)
        return {
            "object_count": len(nodes),
            "edge_count": len(edges),
            "relation_counts": dict(sorted(relation_counts.items())),
            "has_spatial_relations": bool(edges),
            "has_repeated_shapes": self._has_repeated(nodes, "canonical_shape_signature"),
            "has_repeated_colors": self._has_repeated(nodes, "color"),
        }

    def _comparison_summary(self, graph: Mapping[str, Any]) -> dict[str, Any]:
        output_summary = graph.get("output_scene_graph", {}).get("summary", {})
        input_summary = graph.get("input_scene_graph", {}).get("summary", {})
        identities = graph.get("object_identities", [])
        identity_transitions = Counter(
            identity.get("transition", "identity_transition")
            for identity in identities
        )
        identity_transition_kinds = Counter(
            identity.get(
                "identity_transition",
                identity.get("transition_kind", "IdentityPreserved"),
            )
            for identity in identities
        )
        relation_counts = Counter(
            edge["relation"]
            for edge in graph.get("edges", [])
        )
        return {
            "input_object_count": input_summary.get("object_count", 0),
            "output_object_count": output_summary.get("object_count", 0),
            "object_count_delta": (
                output_summary.get("object_count", 0)
                - input_summary.get("object_count", 0)
            ),
            "edge_count": len(graph.get("edges", [])),
            "identity_relation_count": len(identities),
            "identity_transitions": dict(sorted(identity_transitions.items())),
            "identity_transition_kinds": dict(
                sorted(identity_transition_kinds.items())
            ),
            "relation_counts": dict(sorted(relation_counts.items())),
            "has_identity_split": identity_transitions.get("identity_split", 0) > 0,
            "has_identity_merge": (
                identity_transition_kinds.get("IdentityMerged", 0) > 0
            ),
            "has_identity_creation": (
                identity_transition_kinds.get("IdentityCreated", 0) > 0
            ),
            "has_identity_destruction": (
                identity_transition_kinds.get("IdentityDestroyed", 0) > 0
            ),
            "has_object_relations": bool(graph.get("edges", [])),
            "object_level_ready": bool(graph.get("nodes")),
        }

    def _has_repeated(
        self,
        nodes: Mapping[str, Mapping[str, Any]],
        key: str,
    ) -> bool:
        counts = Counter(node.get(key) for node in nodes.values())
        return any(value is not None and count > 1 for value, count in counts.items())


__all__ = [
    "SceneGraphBuilder",
]
