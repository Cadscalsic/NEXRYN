"""Object-centric scene graph construction for NEXRYN perception output.

This module sits directly above ``PerceptionEngine``. It turns perceived
objects and spatial relations into a graph representation that downstream
dependency and causal systems can consume. It remains observational: it emits
evidence and soft structural hints, not truth decisions or causal conclusions.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from core.epistemic_models import clamp
from core.perception.color_analyzer import ColorAnalyzer
from core.perception.identity_tracker import IdentityTracker
from core.perception.perception_engine import PerceptionEngine
from core.perception.spatial_relations import SpatialRelationEngine


@dataclass(frozen=True)
class SceneGraphNode:
    """A perceived object represented as a graph node."""

    id: str
    color: int
    size: int
    bbox: dict[str, int]
    center: dict[str, float]
    shape_signature: str
    holes: int
    is_solid: bool
    edge_touching: bool
    degree: int = 0
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SceneGraphEdge:
    """A perceived relation represented as a graph edge."""

    source: str
    relation: str
    target: str
    confidence: float = 1.0
    evidence_type: str = "observed_spatial_relation"


class SceneGraphEngine:
    """Build object-level scene graphs from raw grids or perceived scenes."""

    def __init__(
        self,
        perception_engine: PerceptionEngine | None = None,
        spatial_relation_engine: SpatialRelationEngine | None = None,
        identity_tracker: IdentityTracker | None = None,
        color_analyzer: ColorAnalyzer | None = None,
    ) -> None:
        self.perception_engine = perception_engine or PerceptionEngine()
        self.spatial_relation_engine = (
            spatial_relation_engine or SpatialRelationEngine()
        )
        self.identity_tracker = identity_tracker or IdentityTracker()
        self.color_analyzer = color_analyzer or ColorAnalyzer()

    def build_scene_graph(self, grid_or_scene: Any) -> dict[str, Any]:
        """Return a dense object-centric graph for a grid or scene dict."""

        scene = self._ensure_scene(grid_or_scene)
        objects = list(scene.get("objects", []))
        relations = list(scene.get("relations", []))
        edges = [self._build_edge(relation) for relation in relations]
        degree = self._compute_degrees(edges)
        nodes = {
            obj["id"]: asdict(self._build_node(obj, degree.get(obj["id"], 0)))
            for obj in objects
        }
        edge_dicts = [asdict(edge) for edge in edges]

        graph = {
            "system": "scene_graph_engine",
            "source_system": scene.get("system", "perception_engine"),
            "height": scene.get("height", 0),
            "width": scene.get("width", 0),
            "background_color": scene.get("background_color", 0),
            "nodes": nodes,
            "edges": edge_dicts,
            "adjacency": self.build_adjacency(edge_dicts),
            "relation_index": self.build_relation_index(edge_dicts),
            "summary": self.summarize_graph(nodes, edge_dicts),
        }
        graph["dependency_evidence"] = self.extract_dependency_evidence(graph)
        return graph

    def build_adjacency(
        self,
        edges: list[Mapping[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Index outgoing relations by source object id."""

        adjacency: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in edges:
            adjacency[str(edge["source"])].append({
                "relation": edge["relation"],
                "target": edge["target"],
                "confidence": edge.get("confidence", 1.0),
            })
        return {
            source: sorted(
                values,
                key=lambda item: (item["relation"], item["target"]),
            )
            for source, values in sorted(adjacency.items())
        }

    def build_relation_index(
        self,
        edges: list[Mapping[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Index graph edges by relation type."""

        relation_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in edges:
            relation_index[str(edge["relation"])].append({
                "source": edge["source"],
                "target": edge["target"],
                "confidence": edge.get("confidence", 1.0),
            })
        return {
            relation: sorted(
                values,
                key=lambda item: (item["source"], item["target"]),
            )
            for relation, values in sorted(relation_index.items())
        }

    def summarize_graph(
        self,
        nodes: Mapping[str, Mapping[str, Any]],
        edges: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Summarize graph structure without assigning truth value."""

        node_count = len(nodes)
        relation_counts = Counter(edge["relation"] for edge in edges)
        degree_map = {
            node_id: int(node.get("degree", 0))
            for node_id, node in nodes.items()
        }
        max_degree = max(degree_map.values(), default=0)
        possible_edges = max(node_count * (node_count - 1), 1)
        shape_counts = Counter(
            node.get("shape_signature", "") for node in nodes.values()
        )
        color_counts = Counter(int(node.get("color", 0)) for node in nodes.values())

        return {
            "object_count": node_count,
            "edge_count": len(edges),
            "relation_types": sorted(relation_counts),
            "relation_counts": dict(sorted(relation_counts.items())),
            "central_objects": sorted(
                node_id
                for node_id, degree in degree_map.items()
                if degree == max_degree and max_degree > 0
            ),
            "isolated_objects": sorted(
                node_id
                for node_id, degree in degree_map.items()
                if degree == 0
            ),
            "graph_density": round(len(edges) / possible_edges, 4),
            "has_repeated_shapes": any(count > 1 for count in shape_counts.values()),
            "has_repeated_colors": any(count > 1 for count in color_counts.values()),
            "object_level_ready": node_count > 0,
        }

    def extract_dependency_evidence(
        self,
        scene_graph: Mapping[str, Any],
        source: str = "scene_graph",
    ) -> list[dict[str, Any]]:
        """Convert graph observations into dependency-graph input records."""

        nodes = scene_graph.get("nodes", {})
        relation_index = scene_graph.get("relation_index", {})
        summary = scene_graph.get("summary", {})
        evidence: list[dict[str, Any]] = []

        if summary:
            evidence.append(
                self._dependency(
                    source,
                    f"object_count:{summary.get('object_count', 0)}",
                    confidence=0.88,
                    dependency_type="structural_dependency",
                    metadata={"summary": summary},
                )
            )

        for relation, relation_edges in sorted(relation_index.items()):
            evidence.append(
                self._dependency(
                    source,
                    f"relation:{relation}",
                    confidence=self._relation_confidence(relation_edges),
                    dependency_type="observational_dependency",
                    metadata={
                        "relation": relation,
                        "edge_count": len(relation_edges),
                    },
                )
            )

        shape_counts = Counter(
            node.get("shape_signature", "") for node in nodes.values()
        )
        color_counts = Counter(int(node.get("color", 0)) for node in nodes.values())
        for shape_signature, count in sorted(shape_counts.items()):
            if shape_signature:
                evidence.append(
                    self._dependency(
                        source,
                        f"shape_signature:{shape_signature}",
                        confidence=0.84 if count == 1 else 0.90,
                        dependency_type="semantic_dependency",
                        metadata={"shape_signature": shape_signature, "count": count},
                    )
                )
        for color, count in sorted(color_counts.items()):
            evidence.append(
                self._dependency(
                    source,
                    f"color:{color}",
                    confidence=0.82 if count == 1 else 0.88,
                    dependency_type="contextual_dependency",
                    metadata={"color": color, "count": count},
                )
            )

        return evidence

    def build_dependency_evidence(
        self,
        grid_or_scene: Any,
        source: str,
    ) -> dict[str, Any]:
        """Build graph-derived dependency evidence for a concept/source."""

        graph = self.build_scene_graph(grid_or_scene)
        evidence = self.extract_dependency_evidence(graph, source=source)
        return {
            "system": "scene_graph_engine",
            "source": source,
            "dependency_evidence": evidence,
            "evidence_count": len(evidence),
            "scene_graph_summary": graph["summary"],
        }

    def compare_scene_graphs(
        self,
        input_grid: Any,
        output_grid: Any,
    ) -> dict[str, Any]:
        """Compare two object-level graphs and emit lineage-style hints."""

        input_graph = self.build_scene_graph(input_grid)
        output_graph = self.build_scene_graph(output_grid)
        matches = self._match_nodes(input_graph["nodes"], output_graph["nodes"])
        matched_inputs = {match["input_object"] for match in matches}
        matched_outputs = {match["output_object"] for match in matches}
        object_events = self._object_events(
            input_graph["nodes"],
            output_graph["nodes"],
            matches,
            matched_inputs,
            matched_outputs,
        )
        identity_report = self.identity_tracker.track_identity(
            input_grid,
            output_grid,
            source="object_identity_preservation",
        )
        color_report = self.color_analyzer.compare_grids(
            input_grid,
            output_grid,
            source="color_preservation",
        )

        return {
            "system": "scene_graph_engine",
            "input_scene_graph": input_graph,
            "output_scene_graph": output_graph,
            "object_matches": matches,
            "object_events": object_events,
            "identity_report": identity_report,
            "color_report": color_report,
            "relation_changes": self._relation_changes(input_graph, output_graph),
            "dependency_evidence": [
                *input_graph["dependency_evidence"],
                *output_graph["dependency_evidence"],
                *self._event_dependencies(object_events),
                *identity_report.get("dependency_evidence", []),
                *color_report.get("dependency_evidence", []),
            ],
            "summary": {
                "input_object_count": input_graph["summary"]["object_count"],
                "output_object_count": output_graph["summary"]["object_count"],
                "object_count_delta": (
                    output_graph["summary"]["object_count"]
                    - input_graph["summary"]["object_count"]
                ),
                "object_event_count": len(object_events),
                "identity_state": identity_report["identity_state"],
                "identity_behavior": identity_report["identity_behavior"],
                "lineage_continuity": identity_report["lineage_continuity"],
                "color_behavior": color_report["color_behavior"],
                "color_mapping_confidence": color_report["mapping_confidence"],
                "object_level_ready": True,
            },
        }

    def _ensure_scene(self, grid_or_scene: Any) -> dict[str, Any]:
        if isinstance(grid_or_scene, dict) and "objects" in grid_or_scene:
            return dict(grid_or_scene)
        return self.perception_engine.perceive(grid_or_scene)

    def _build_node(
        self,
        obj: Mapping[str, Any],
        degree: int,
    ) -> SceneGraphNode:
        return SceneGraphNode(
            id=str(obj["id"]),
            color=int(obj["color"]),
            size=int(obj["size"]),
            bbox=dict(obj["bbox"]),
            center=dict(obj["center"]),
            shape_signature=str(obj["shape_signature"]),
            holes=int(obj["holes"]),
            is_solid=bool(obj["is_solid"]),
            edge_touching=bool(obj["edge_touching"]),
            degree=int(degree),
            attributes={
                "cells": list(obj.get("cells", [])),
                "normalized_shape": list(obj.get("normalized_shape", [])),
                "canonical_shape_signature": obj.get(
                    "canonical_shape_signature",
                    obj.get("shape_signature", ""),
                ),
                "shape_analysis": dict(obj.get("shape_analysis", {})),
            },
        )

    def _build_edge(self, relation: Mapping[str, Any]) -> SceneGraphEdge:
        return SceneGraphEdge(
            source=str(relation["source"]),
            relation=str(relation["relation"]),
            target=str(relation["target"]),
            confidence=clamp(float(relation.get("confidence", 1.0))),
        )

    def _compute_degrees(self, edges: list[SceneGraphEdge]) -> dict[str, int]:
        degree: Counter[str] = Counter()
        for edge in edges:
            degree[edge.source] += 1
            degree[edge.target] += 1
        return dict(degree)

    def _dependency(
        self,
        source: str,
        target: str,
        confidence: float,
        dependency_type: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "source": source,
            "target": target,
            "relation": "depends_on",
            "confidence": clamp(confidence),
            "dependency_type": dependency_type,
            "required": True,
            "supported": True,
            "transfer_success": True,
            "metadata": metadata,
        }

    def _relation_confidence(
        self,
        relation_edges: list[Mapping[str, Any]],
    ) -> float:
        if not relation_edges:
            return 0.0
        average = sum(
            float(edge.get("confidence", 1.0)) for edge in relation_edges
        ) / len(relation_edges)
        volume_bonus = min(len(relation_edges), 4) * 0.02
        return clamp(average * 0.92 + volume_bonus)

    def _match_nodes(
        self,
        input_nodes: Mapping[str, Mapping[str, Any]],
        output_nodes: Mapping[str, Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        used_outputs: set[str] = set()
        for input_id, input_node in sorted(input_nodes.items()):
            candidates = [
                (output_id, output_node)
                for output_id, output_node in sorted(output_nodes.items())
                if output_id not in used_outputs
            ]
            if not candidates:
                continue
            output_id, output_node = max(
                candidates,
                key=lambda candidate: self._node_match_score(
                    input_node,
                    candidate[1],
                ),
            )
            score = self._node_match_score(input_node, output_node)
            if score <= 0:
                continue
            used_outputs.add(output_id)
            matches.append({
                "input_object": input_id,
                "output_object": output_id,
                "match_score": round(score, 4),
                "shape_preserved": (
                    input_node["shape_signature"]
                    == output_node["shape_signature"]
                ),
                "color_preserved": input_node["color"] == output_node["color"],
                "size_preserved": input_node["size"] == output_node["size"],
                "position_preserved": input_node["center"] == output_node["center"],
            })
        return matches

    def _node_match_score(
        self,
        input_node: Mapping[str, Any],
        output_node: Mapping[str, Any],
    ) -> float:
        score = 0.0
        if input_node["shape_signature"] == output_node["shape_signature"]:
            score += 0.42
        if input_node["color"] == output_node["color"]:
            score += 0.24
        if input_node["size"] == output_node["size"]:
            score += 0.20
        if input_node["center"] == output_node["center"]:
            score += 0.14
        return clamp(score)

    def _object_events(
        self,
        input_nodes: Mapping[str, Mapping[str, Any]],
        output_nodes: Mapping[str, Mapping[str, Any]],
        matches: list[Mapping[str, Any]],
        matched_inputs: set[str],
        matched_outputs: set[str],
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for match in matches:
            if not match["position_preserved"]:
                events.append({
                    "event": "object_moved",
                    "input_object": match["input_object"],
                    "output_object": match["output_object"],
                    "confidence": match["match_score"],
                })
            if not match["color_preserved"]:
                events.append({
                    "event": "object_color_changed",
                    "input_object": match["input_object"],
                    "output_object": match["output_object"],
                    "confidence": match["match_score"],
                })
            if not match["shape_preserved"]:
                events.append({
                    "event": "object_shape_changed",
                    "input_object": match["input_object"],
                    "output_object": match["output_object"],
                    "confidence": match["match_score"],
                })

        for input_id in sorted(set(input_nodes) - matched_inputs):
            events.append({
                "event": "object_removed",
                "input_object": input_id,
                "output_object": None,
                "confidence": 0.82,
            })
        for output_id in sorted(set(output_nodes) - matched_outputs):
            placement = self.spatial_relation_engine.describe_added_object(
                output_nodes[output_id],
                list(input_nodes.values()),
            )
            events.append({
                "event": "object_added",
                "input_object": None,
                "output_object": output_id,
                "confidence": 0.82,
                "source_candidate": placement["source_candidate"],
                "placement_vector": placement["placement_vector"],
                "source_relation": placement["source_relation"],
            })

        events.extend(self._possible_split_events(input_nodes, output_nodes))
        return events

    def _possible_split_events(
        self,
        input_nodes: Mapping[str, Mapping[str, Any]],
        output_nodes: Mapping[str, Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        output_by_shape: dict[str, list[str]] = defaultdict(list)
        for output_id, output_node in output_nodes.items():
            output_by_shape[str(output_node["shape_signature"])].append(output_id)
        for input_id, input_node in input_nodes.items():
            targets = sorted(output_by_shape[str(input_node["shape_signature"])])
            if len(targets) > 1:
                source = {
                    **input_node,
                    "id": input_id,
                }
                placements = [
                    self.spatial_relation_engine.placement_vector(
                        source,
                        {
                            **output_nodes[target],
                            "id": target,
                        },
                    )
                    for target in targets
                ]
                events.append({
                    "event": "object_split_possible",
                    "input_object": input_id,
                    "output_objects": targets,
                    "placement_vectors": placements,
                    "confidence": 0.78,
                })
        return events

    def _relation_changes(
        self,
        input_graph: Mapping[str, Any],
        output_graph: Mapping[str, Any],
    ) -> dict[str, list[str]]:
        input_relations = set(input_graph.get("relation_index", {}))
        output_relations = set(output_graph.get("relation_index", {}))
        return {
            "relations_added": sorted(output_relations - input_relations),
            "relations_removed": sorted(input_relations - output_relations),
            "relations_preserved": sorted(input_relations & output_relations),
        }

    def _event_dependencies(
        self,
        events: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        evidence = []
        for event in events:
            evidence.append(
                self._dependency(
                    "scene_graph",
                    f"object_event:{event['event']}",
                    confidence=float(event.get("confidence", 0.75)),
                    dependency_type="structural_dependency",
                    metadata={"event": dict(event)},
                )
            )
        return evidence


__all__ = [
    "SceneGraphEdge",
    "SceneGraphEngine",
    "SceneGraphNode",
]
