"""Build ordered dependency chains from object-centric scene evidence."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp
from core.identity.identity_continuity_engine import IdentityContinuityEngine
from core.perception.color_analyzer import ColorAnalyzer
from core.perception.object_tracker import ObjectTracker
from core.perception.scene_graph_engine import SceneGraphEngine
from core.scene_graph.scene_graph_builder import SceneGraphBuilder


class DependencyGraphBuilder:
    """Translate scene comparisons into explicit dependency chains."""

    DUPLICATION_CHAIN = [
        "duplication",
        "identity_split",
        "object_count_increase",
        "topology_splitting",
    ]
    MERGE_CHAIN = [
        "object_convergence",
        "identity_merged",
        "object_count_decrease",
        "topology_compaction",
    ]
    CREATION_CHAIN = [
        "object_appearance",
        "identity_created",
        "object_count_increase",
        "scene_expansion",
    ]
    DESTRUCTION_CHAIN = [
        "object_disappearance",
        "identity_destroyed",
        "object_count_decrease",
        "scene_contraction",
    ]
    PRESERVATION_CHAIN = [
        "object_transformation",
        "identity_preserved",
        "attribute_or_position_change",
    ]

    def __init__(
        self,
        scene_graph_engine: SceneGraphEngine | None = None,
        scene_graph_builder: SceneGraphBuilder | None = None,
        object_tracker: ObjectTracker | None = None,
        color_analyzer: ColorAnalyzer | None = None,
        identity_continuity_engine: IdentityContinuityEngine | None = None,
    ) -> None:
        self.scene_graph_engine = scene_graph_engine or SceneGraphEngine()
        self.object_tracker = object_tracker or ObjectTracker()
        self.scene_graph_builder = scene_graph_builder or SceneGraphBuilder(
            object_tracker=self.object_tracker,
        )
        self.color_analyzer = color_analyzer or ColorAnalyzer(
            object_tracker=self.object_tracker,
        )
        self.identity_continuity_engine = (
            identity_continuity_engine
            or IdentityContinuityEngine(object_tracker=self.object_tracker)
        )

    def build_from_grids(
        self,
        input_grid: Any,
        output_grid: Any,
        source: str | None = None,
    ) -> dict[str, Any]:
        comparison = self.scene_graph_engine.compare_scene_graphs(
            input_grid,
            output_grid,
        )
        object_scene_graph = self.scene_graph_builder.build_comparison(
            input_grid,
            output_grid,
        )
        tracking = object_scene_graph.get("tracking", {})
        color_report = self.color_analyzer.compare_grids(
            input_grid,
            output_grid,
            source="color_preservation",
        )
        identity_continuity_report = (
            self.identity_continuity_engine.evaluate_objects(
                input_grid,
                output_grid,
            )
        )
        operation = source or self._infer_operation(
            comparison,
            object_scene_graph=object_scene_graph,
        )
        chain = self._chain_for_operation(
            operation,
            comparison,
            object_scene_graph=object_scene_graph,
            color_report=color_report,
        )
        dependencies = self._dependencies_for_chain(
            chain,
            comparison=comparison,
            object_scene_graph=object_scene_graph,
            color_report=color_report,
            identity_continuity_report=identity_continuity_report,
        )

        return {
            "system": "dependency_graph_builder",
            "mode": "object_centric_dependency_chain",
            "operation": operation,
            "dependency_chain": chain,
            "chain_complete": len(chain) > 1,
            "chain_depth": max(len(chain) - 1, 0),
            "dependency_evidence": dependencies,
            "object_scene_graph": object_scene_graph,
            "object_identities": tracking.get("object_identities", []),
            "scene_comparison_summary": comparison.get("summary", {}),
            "identity_report": comparison.get("identity_report", {}),
            "identity_continuity_report": identity_continuity_report,
            "color_report": color_report,
        }

    def _infer_operation(
        self,
        comparison: Mapping[str, Any],
        object_scene_graph: Mapping[str, Any] | None = None,
    ) -> str:
        summary = comparison.get("summary", {})
        scene_summary = (object_scene_graph or {}).get("summary", {})
        if summary.get("identity_behavior") == "identity_split":
            return "duplication"
        if scene_summary.get("has_identity_split"):
            return "duplication"
        if scene_summary.get("has_identity_merge"):
            return "object_convergence"
        if scene_summary.get("has_identity_creation"):
            return "object_appearance"
        if scene_summary.get("has_identity_destruction"):
            return "object_disappearance"
        if summary.get("object_count_delta", 0) > 0:
            return "object_appearance"
        if summary.get("object_count_delta", 0) < 0:
            return "object_disappearance"
        return "scene_transformation"

    def _chain_for_operation(
        self,
        operation: str,
        comparison: Mapping[str, Any],
        object_scene_graph: Mapping[str, Any] | None = None,
        color_report: Mapping[str, Any] | None = None,
    ) -> list[str]:
        if operation == "duplication":
            chain = list(self.DUPLICATION_CHAIN)
            if self._has_color_reassignment(color_report):
                chain.append("color_reassigned")
            return chain

        scene_summary = (object_scene_graph or {}).get("summary", {})
        if operation == "object_convergence" or scene_summary.get("has_identity_merge"):
            return list(self.MERGE_CHAIN)
        if operation == "object_appearance" or scene_summary.get(
            "has_identity_creation"
        ):
            return list(self.CREATION_CHAIN)
        if operation == "object_disappearance" or scene_summary.get(
            "has_identity_destruction"
        ):
            return list(self.DESTRUCTION_CHAIN)

        chain = [operation]
        summary = comparison.get("summary", {})
        if summary.get("object_count_delta", 0) != 0:
            chain.append("object_count_change")
        if summary.get("identity_behavior") == "identity_split":
            chain.append("identity_split")
        if comparison.get("relation_changes", {}).get("relations_added"):
            chain.append("relation_graph_change")
        if scene_summary.get("has_identity_split") and "identity_split" not in chain:
            chain.append("identity_split")
        if self._has_identity_preservation_change(object_scene_graph):
            chain.extend(
                item
                for item in self.PRESERVATION_CHAIN[1:]
                if item not in chain
            )
        if self._has_color_reassignment(color_report):
            chain.append("color_reassigned")
        return chain

    def _dependencies_for_chain(
        self,
        chain: list[str],
        comparison: Mapping[str, Any],
        object_scene_graph: Mapping[str, Any] | None = None,
        color_report: Mapping[str, Any] | None = None,
        identity_continuity_report: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        dependencies = []
        confidence = self._chain_confidence(
            comparison,
            object_scene_graph=object_scene_graph,
            color_report=color_report,
        )
        for source, target in zip(chain, chain[1:]):
            dependencies.append({
                "source": source,
                "target": target,
                "relation": "causes",
                "confidence": confidence,
                "dependency_type": "causal_dependency",
                "required": True,
                "supported": True,
                "transfer_success": True,
                "metadata": {
                    "builder": "dependency_graph_builder",
                    "chain": list(chain),
                    "scene_summary": comparison.get("summary", {}),
                    "object_scene_summary": (
                        object_scene_graph or {}
                    ).get("summary", {}),
                    "object_identities": (
                        object_scene_graph or {}
                    ).get("object_identities", []),
                    "color_behavior": (
                        color_report or {}
                    ).get("color_behavior"),
                    "identity_transition_kinds": (
                        object_scene_graph or {}
                    ).get("summary", {}).get("identity_transition_kinds", {}),
                    "relation_triples": (
                        object_scene_graph or {}
                    ).get("relation_triples", []),
                },
            })
        dependencies.extend(
            (identity_continuity_report or {}).get("dependency_evidence", [])
        )
        return dependencies

    def _chain_confidence(
        self,
        comparison: Mapping[str, Any],
        object_scene_graph: Mapping[str, Any] | None = None,
        color_report: Mapping[str, Any] | None = None,
    ) -> float:
        summary = comparison.get("summary", {})
        identity = comparison.get("identity_report", {})
        identity_continuity = identity.get("lineage_continuity", 0.0)
        object_signal = 0.90 if summary.get("object_count_delta", 0) > 0 else 0.72
        object_identity_scores = [
            identity.get("continuity_score", 0.0)
            for identity in (object_scene_graph or {}).get("object_identities", [])
        ]
        object_identity_signal = (
            sum(object_identity_scores) / len(object_identity_scores)
            if object_identity_scores
            else 0.0
        )
        color_signal = (
            color_report or {}
        ).get("mapping_confidence", 0.0) if self._has_color_reassignment(color_report) else 0.72
        split_signal = (
            max(
                [
                    event.get("confidence", 0.0)
                    for event in identity.get("split_events", [])
                ],
                default=0.0,
            )
            or 0.80
            if summary.get("identity_behavior") == "identity_split"
            else 0.68
        )
        return clamp(
            object_signal * 0.28
            + clamp(identity_continuity) * 0.24
            + clamp(split_signal) * 0.22
            + clamp(object_identity_signal) * 0.18
            + clamp(color_signal) * 0.08
        )

    def _has_identity_preservation_change(
        self,
        object_scene_graph: Mapping[str, Any] | None,
    ) -> bool:
        for identity in (object_scene_graph or {}).get("object_identities", []):
            if identity.get("identity_transition") != "IdentityPreserved":
                continue
            if identity.get("transition") != "preserved":
                return True
        return False

    def _has_color_reassignment(
        self,
        color_report: Mapping[str, Any] | None,
    ) -> bool:
        if (color_report or {}).get("color_behavior") != "color_reassigned":
            return False
        return any(
            event.get("input_color") is not None
            and event.get("input_color") != event.get("output_color")
            for event in (color_report or {}).get("recolor_events", [])
        )


__all__ = [
    "DependencyGraphBuilder",
]
