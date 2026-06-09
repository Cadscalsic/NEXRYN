"""Build causal graphs from perception and scene-graph evidence."""

from __future__ import annotations

from typing import Any, Mapping

from core.causal.causal_chain_builder import CausalChainBuilder
from core.causal.causal_graph import CausalGraph
from core.epistemic_models import clamp
from core.perception import ObjectExtractor, ObjectTracker
from core.scene_graph import GraphReasoner
from core.world_model.placement_reasoner import PlacementReasoner


class SceneCausalGraphBuilder:
    """Translate object/scene changes into explicit causal concept chains."""

    def __init__(
        self,
        object_extractor: ObjectExtractor | None = None,
        object_tracker: ObjectTracker | None = None,
        graph_reasoner: GraphReasoner | None = None,
        placement_reasoner: PlacementReasoner | None = None,
        chain_builder: CausalChainBuilder | None = None,
    ) -> None:
        self.object_extractor = object_extractor or ObjectExtractor()
        self.object_tracker = object_tracker or ObjectTracker(self.object_extractor)
        self.graph_reasoner = graph_reasoner or GraphReasoner(
            object_tracker=self.object_tracker,
        )
        self.placement_reasoner = placement_reasoner or PlacementReasoner(
            graph_reasoner=self.graph_reasoner,
        )
        self.chain_builder = chain_builder or CausalChainBuilder()

    def build_from_grids(
        self,
        input_grid: Any,
        output_grid: Any,
        operation: str | None = None,
        position_rule: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        input_objects = self.object_extractor.extract_objects(input_grid)
        output_objects = self.object_extractor.extract_objects(output_grid)
        tracking = self.object_tracker.track(input_grid, output_grid)
        inferred_operation = operation or self._infer_operation(
            input_objects,
            output_objects,
            tracking,
        )
        graph = CausalGraph()
        self._add_scene_nodes(graph, inferred_operation)
        self._add_preservation_spine(graph, inferred_operation, tracking)
        self._add_operation_outcomes(
            graph,
            inferred_operation,
            input_objects,
            output_objects,
            tracking,
            position_rule,
        )
        chains = self.chain_builder.build(
            graph,
            sources=["shape_preservation"],
            targets=[inferred_operation],
        )
        operation_chains = self.chain_builder.build(
            graph,
            sources=[inferred_operation],
            targets=["shape_preservation"],
        )
        return {
            "system": "scene_causal_graph_builder",
            "mode": "perception_scene_causal_graph",
            "operation": inferred_operation,
            "input_object_count": len(input_objects),
            "output_object_count": len(output_objects),
            "tracking": tracking,
            "causal_graph": graph.export_graph(),
            "causal_chains": chains,
            "best_causal_chain": self._best_chain(chains),
            "operation_causal_chains": operation_chains,
            "best_operation_causal_chain": self._best_chain(operation_chains),
            "causal_graph_alignment_hint": self._alignment_hint(graph, chains),
        }

    def _infer_operation(
        self,
        input_objects: list[Mapping[str, Any]],
        output_objects: list[Mapping[str, Any]],
        tracking: Mapping[str, Any],
    ) -> str:
        if len(output_objects) > len(input_objects):
            return "duplication"
        if self._has_size_expansion(input_objects, output_objects, tracking):
            return "expand_object"
        if tracking.get("moved_objects"):
            return "translation"
        return "structural_transformation"

    def _has_size_expansion(
        self,
        input_objects: list[Mapping[str, Any]],
        output_objects: list[Mapping[str, Any]],
        tracking: Mapping[str, Any],
    ) -> bool:
        output_by_id = {obj["id"]: obj for obj in output_objects}
        input_by_id = {obj["id"]: obj for obj in input_objects}
        for match in tracking.get("matches", []):
            input_obj = input_by_id.get(match.get("input_object"))
            output_obj = output_by_id.get(match.get("output_object"))
            if input_obj and output_obj and output_obj.get("size", 0) > input_obj.get(
                "size",
                0,
            ):
                return True
        if len(input_objects) == len(output_objects) == 1:
            return output_objects[0].get("size", 0) > input_objects[0].get("size", 0)
        return False

    def _add_scene_nodes(
        self,
        graph: CausalGraph,
        operation: str,
    ) -> None:
        for node_id, node_type, confidence in [
            ("shape_preservation", "concept", 0.92),
            ("object_identity_preservation", "concept", 0.88),
            ("topology_preservation", "concept", 0.86),
            ("scene_graph_construction", "event", 0.84),
            (operation, "transformation", 0.86),
        ]:
            graph.add_node(
                node_id=node_id,
                node_type=node_type,
                name=node_id,
                confidence=confidence,
                support_score=confidence,
                evidence_count=1,
            )

    def _add_preservation_spine(
        self,
        graph: CausalGraph,
        operation: str,
        tracking: Mapping[str, Any],
    ) -> None:
        evidence = [{"source": "object_tracker", "tracking": tracking}]
        self._edge(
            graph,
            "shape_preservation",
            "object_identity_preservation",
            "supports",
            0.90,
            evidence,
        )
        self._edge(
            graph,
            "object_identity_preservation",
            "topology_preservation",
            "supports",
            0.88,
            evidence,
        )
        self._edge(
            graph,
            "topology_preservation",
            "scene_graph_construction",
            "enables",
            0.86,
            evidence,
        )
        self._edge(
            graph,
            "scene_graph_construction",
            operation,
            "explains",
            0.84,
            evidence,
        )

    def _add_operation_outcomes(
        self,
        graph: CausalGraph,
        operation: str,
        input_objects: list[Mapping[str, Any]],
        output_objects: list[Mapping[str, Any]],
        tracking: Mapping[str, Any],
        position_rule: Mapping[str, Any] | None,
    ) -> None:
        if operation == "duplication":
            self._add_duplication_causal_chain(graph, operation)
            if tracking.get("added_objects"):
                vector = tracking["added_objects"][0].get("placement_vector", {})
                direction = vector.get("direction")
                if direction:
                    self._add_outcome(
                        graph,
                        operation,
                        f"placement:{direction}",
                        clamp(position_rule.get("confidence", 0.84))
                        if isinstance(position_rule, Mapping)
                        else 0.84,
                        evidence=[{"placement_vector": vector}],
                    )
            return

        if operation == "expand_object":
            self._add_outcome(graph, operation, "object_size_increase", 0.90)
            self._add_outcome(graph, operation, "boundary_growth", 0.84)
            return

        if operation == "translation":
            self._add_outcome(graph, operation, "position_change", 0.88)
            return

        size_delta = sum(obj.get("size", 0) for obj in output_objects) - sum(
            obj.get("size", 0) for obj in input_objects
        )
        if size_delta:
            self._add_outcome(graph, operation, "structural_size_delta", 0.78)

    def _add_duplication_causal_chain(
        self,
        graph: CausalGraph,
        operation: str,
    ) -> None:
        """Encode duplication as an ordered causal chain, not adjacent tags."""

        evidence = [{"source": "scene_causal_graph_builder"}]
        chain = [
            (operation, "object_count_increase", "causes", 0.90),
            ("object_count_increase", "identity_split", "causes", 0.88),
            ("identity_split", "topology_splitting", "causes", 0.86),
            ("topology_splitting", "shape_preservation", "causes", 0.84),
        ]

        for source, target, relation_type, confidence in chain:
            if target not in graph.nodes:
                graph.add_node(
                    node_id=target,
                    node_type=(
                        "concept"
                        if target == "shape_preservation"
                        else "outcome"
                    ),
                    name=target,
                    confidence=confidence,
                    support_score=confidence,
                    evidence_count=1,
                )
            self._edge(
                graph,
                source,
                target,
                relation_type,
                confidence,
                evidence,
            )

        self._add_outcome(
            graph,
            operation,
            "object_lineage_split",
            0.86,
            evidence=evidence,
        )

    def _add_outcome(
        self,
        graph: CausalGraph,
        operation: str,
        outcome: str,
        confidence: float,
        evidence: list[dict[str, Any]] | None = None,
    ) -> None:
        graph.add_node(
            node_id=outcome,
            node_type="outcome",
            name=outcome,
            confidence=confidence,
            support_score=confidence,
            evidence_count=1,
        )
        self._edge(
            graph,
            operation,
            outcome,
            "causes",
            confidence,
            evidence or [{"source": "scene_causal_graph_builder"}],
        )

    def _edge(
        self,
        graph: CausalGraph,
        source: str,
        target: str,
        relation_type: str,
        confidence: float,
        evidence: list[dict[str, Any]],
    ) -> None:
        graph.add_edge(
            source=source,
            target=target,
            relation_type=relation_type,
            weight=confidence,
            confidence=confidence,
            evidence=evidence,
        )

    def _best_chain(self, chains: Mapping[str, Any]) -> list[str]:
        indirect = chains.get("indirect_chains", [])
        if indirect:
            return indirect[0].get("causal_chain", [])
        direct = chains.get("direct_chains", [])
        if direct:
            return direct[0].get("causal_chain", [])
        return []

    def _alignment_hint(
        self,
        graph: CausalGraph,
        chains: Mapping[str, Any],
    ) -> dict[str, Any]:
        best_chain = self._best_chain(chains)
        required = {
            "shape_preservation",
            "object_identity_preservation",
            "topology_preservation",
        }
        chain_coverage = len(required.intersection(best_chain)) / len(required)
        return {
            "alignment_score": clamp(
                graph.compute_graph_strength() * 0.55 + chain_coverage * 0.45
            ),
            "chain_coverage": round(chain_coverage, 4),
            "graph_strength": graph.compute_graph_strength(),
            "alignment_ready": bool(best_chain) and chain_coverage >= 1.0,
        }


__all__ = [
    "SceneCausalGraphBuilder",
]
