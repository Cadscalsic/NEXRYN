"""Unified object runtime for ARC-style object-centric cognition."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp
from core.perception.object_tracker import ObjectTracker


class ObjectRuntime:
    """Represent Object(t0) -> Transformation -> Object(t1) explicitly."""

    def __init__(
        self,
        object_tracker: ObjectTracker | None = None,
        scene_graph_builder: SceneGraphBuilder | None = None,
        dependency_graph_builder: Any | None = None,
        identity_continuity_engine: Any | None = None,
    ) -> None:
        self.object_tracker = object_tracker or ObjectTracker()
        if scene_graph_builder is None:
            from core.scene_graph.scene_graph_builder import SceneGraphBuilder

            scene_graph_builder = SceneGraphBuilder(
                object_tracker=self.object_tracker,
            )
        self.scene_graph_builder = scene_graph_builder
        if dependency_graph_builder is None:
            from core.dependency.dependency_graph_builder import (
                DependencyGraphBuilder,
            )

            dependency_graph_builder = DependencyGraphBuilder(
                object_tracker=self.object_tracker,
                scene_graph_builder=self.scene_graph_builder,
            )
        if identity_continuity_engine is None:
            from core.identity.identity_continuity_engine import (
                IdentityContinuityEngine,
            )

            identity_continuity_engine = IdentityContinuityEngine(
                object_tracker=self.object_tracker,
            )
        self.dependency_graph_builder = dependency_graph_builder
        self.identity_continuity_engine = identity_continuity_engine

    def run(
        self,
        input_grid: Any,
        output_grid: Any,
        operation: str | None = None,
    ) -> dict[str, Any]:
        tracking = self.object_tracker.track(input_grid, output_grid)
        scene_graph = self.scene_graph_builder.build_comparison(
            input_grid,
            output_grid,
        )
        dependency_report = self.dependency_graph_builder.build_from_grids(
            input_grid,
            output_grid,
            source=operation,
        )
        identity_report = self.identity_continuity_engine.evaluate_objects(
            input_grid,
            output_grid,
        )
        timeline = self._object_timeline(
            tracking=tracking,
            operation=dependency_report.get("operation", operation),
        )
        runtime_confidence = self._runtime_confidence(
            tracking,
            scene_graph,
            dependency_report,
            identity_report,
        )
        return {
            "system": "object_runtime",
            "phase": "PHASE_6_OBJECT_CENTRIC_COGNITION",
            "operation": dependency_report.get("operation", operation),
            "runtime_state": self._runtime_state(runtime_confidence, timeline),
            "runtime_confidence": runtime_confidence,
            "object_timeline": timeline,
            "object_timeline_count": len(timeline),
            "tracking": tracking,
            "scene_graph": scene_graph,
            "dependency_report": dependency_report,
            "identity_continuity_report": identity_report,
            "dependency_evidence": dependency_report.get(
                "dependency_evidence",
                [],
            ),
        }

    def _object_timeline(
        self,
        tracking: Mapping[str, Any],
        operation: str | None,
    ) -> list[dict[str, Any]]:
        timeline = []
        for transition in tracking.get("identity_transitions", []):
            targets = list(transition.get("targets", []))
            if transition.get("target"):
                targets.append(transition["target"])
            if not targets:
                targets = [None]
            for target in sorted(set(targets), key=lambda item: str(item)):
                timeline.append({
                    "object_t0": transition.get("source"),
                    "transformation": operation
                    or transition.get("transition_type")
                    or "unknown_transformation",
                    "object_t1": target,
                    "identity_transition": transition.get("identity_transition"),
                    "transition_type": transition.get("transition_type"),
                    "continuity": clamp(transition.get("confidence", 0.0)),
                    "evidence": dict(transition.get("evidence", {})),
                })
        return timeline

    def _runtime_confidence(
        self,
        tracking: Mapping[str, Any],
        scene_graph: Mapping[str, Any],
        dependency_report: Mapping[str, Any],
        identity_report: Mapping[str, Any],
    ) -> float:
        scene_ready = 1.0 if scene_graph.get("summary", {}).get(
            "has_object_relations"
        ) else 0.72
        chain_ready = 1.0 if dependency_report.get("chain_complete") else 0.40
        return clamp(
            tracking.get("identity_runtime_confidence", 0.0) * 0.34
            + identity_report.get("continuity_score", 0.0) * 0.28
            + chain_ready * 0.22
            + scene_ready * 0.16
        )

    def _runtime_state(
        self,
        runtime_confidence: float,
        timeline: list[Mapping[str, Any]],
    ) -> str:
        if runtime_confidence >= 0.82 and timeline:
            return "OBJECT_RUNTIME_READY"
        if runtime_confidence >= 0.62 and timeline:
            return "OBJECT_RUNTIME_PROVISIONAL"
        return "OBJECT_RUNTIME_INCOMPLETE"


class _LazyObjectRuntime:
    """Delay ObjectRuntime construction until it is actually used."""

    def __init__(self) -> None:
        self._runtime: ObjectRuntime | None = None

    def _get(self) -> ObjectRuntime:
        if self._runtime is None:
            self._runtime = ObjectRuntime()
        return self._runtime

    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self._get().run(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get(), name)


object_runtime = _LazyObjectRuntime()


__all__ = [
    "ObjectRuntime",
    "object_runtime",
]
