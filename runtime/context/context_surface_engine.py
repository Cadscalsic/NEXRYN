"""Measure contextual diversity for process concepts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


DIVERSITY_KEYS = (
    "directions",
    "object_types",
    "colors",
    "topologies",
    "sizes",
    "spatial_patterns",
)


PROCESS_REQUIREMENTS = {
    "growth": {
        "directions": 1,
        "object_types": 2,
        "colors": 2,
        "topologies": 3,
        "sizes": 2,
        "spatial_patterns": 2,
    },
    "replication": {
        "directions": 2,
        "object_types": 2,
        "colors": 2,
        "topologies": 2,
        "sizes": 2,
        "spatial_patterns": 3,
    },
    "propagation": {
        "directions": 3,
        "object_types": 2,
        "colors": 2,
        "topologies": 2,
        "sizes": 1,
        "spatial_patterns": 3,
    },
    "topological_growth": {
        "directions": 1,
        "object_types": 2,
        "colors": 1,
        "topologies": 3,
        "sizes": 2,
        "spatial_patterns": 2,
    },
    "directional_motion": {
        "directions": 3,
        "object_types": 1,
        "colors": 1,
        "topologies": 1,
        "sizes": 1,
        "spatial_patterns": 3,
    },
}


PROCESS_RECOMMENDATIONS = {
    "growth": {
        "directions": ["asymmetric_growth", "bidirectional_growth"],
        "object_types": ["line_growth", "block_growth", "compound_object_growth"],
        "colors": ["multi_color_growth"],
        "topologies": ["hole_preserving_growth", "branching_growth"],
        "sizes": ["small_object_growth", "large_object_growth"],
        "spatial_patterns": ["edge_constrained_growth", "interior_growth"],
    },
    "replication": {
        "directions": ["diagonal_replication", "cross_axis_replication"],
        "object_types": ["multi_object_replication", "multi_source_replication"],
        "colors": ["multi_color_replication"],
        "topologies": ["topology_constrained_replication", "nested_replication"],
        "sizes": ["small_to_large_replication"],
        "spatial_patterns": ["cross_axis_replication", "nested_replication"],
    },
    "propagation": {
        "directions": ["diagonal_propagation", "reverse_direction_propagation"],
        "object_types": ["multi_object_propagation"],
        "colors": ["multi_color_propagation"],
        "topologies": ["obstacle_aware_propagation"],
        "sizes": ["variable_length_propagation"],
        "spatial_patterns": ["gap_crossing_propagation", "turning_propagation"],
    },
    "topological_growth": {
        "directions": ["axis_constrained_topological_growth"],
        "object_types": ["compound_topology_growth"],
        "colors": ["multi_color_topological_growth"],
        "topologies": ["hole_forming_growth", "branching_topological_growth"],
        "sizes": ["scale_varying_topological_growth"],
        "spatial_patterns": ["nested_topological_growth"],
    },
    "directional_motion": {
        "directions": ["diagonal_motion", "reverse_motion", "multi_axis_motion"],
        "object_types": ["multi_object_motion"],
        "colors": ["multi_color_motion"],
        "topologies": ["topology_preserving_motion"],
        "sizes": ["variable_size_motion"],
        "spatial_patterns": ["offset_motion", "gap_motion", "turning_motion"],
    },
}


class ContextSurfaceEngine:
    """Track contextual diversity without rewarding repeated observations."""

    system_name = "context_surface_engine"

    def __init__(self) -> None:
        self._history: dict[str, list[dict[str, Any]]] = {}

    def evaluate(
        self,
        concept: str,
        dependency_chain: Iterable[Any] | None = None,
        process_signature: Mapping[str, Any] | None = None,
        semantic_context: Mapping[str, Any] | None = None,
        task_metadata: Mapping[str, Any] | Iterable[Any] | None = None,
        transformation_traces: Iterable[Any] | Mapping[str, Any] | None = None,
        execution_histories: Iterable[Any] | Mapping[str, Any] | None = None,
        object_statistics: Mapping[str, Any] | Iterable[Any] | None = None,
        spatial_relations: Iterable[Any] | Mapping[str, Any] | None = None,
        topology_descriptors: Iterable[Any] | Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        track_history: bool = True,
    ) -> dict[str, Any]:
        concept = _normalize(concept)
        runtime_context = (
            runtime_context
            if isinstance(runtime_context, Mapping)
            else {}
        )
        signature = (
            process_signature
            if isinstance(process_signature, Mapping)
            else runtime_context.get("process_signature_report", {})
        )
        semantic = (
            semantic_context
            if isinstance(semantic_context, Mapping)
            else runtime_context.get("semantic_context", {})
        )
        evidence = [
            dependency_chain,
            signature,
            semantic,
            task_metadata,
            transformation_traces,
            execution_histories,
            object_statistics,
            spatial_relations,
            topology_descriptors,
            runtime_context.get("context_surface_evidence"),
            runtime_context.get("transformation_report"),
            runtime_context.get("execution_result"),
            runtime_context.get("object_statistics"),
            runtime_context.get("spatial_relations"),
            runtime_context.get("topology_descriptors"),
            runtime_context.get("task_metadata"),
        ]
        categories = {key: set() for key in DIVERSITY_KEYS}
        for item in evidence:
            self._collect(item, categories)
        self._collect_dependency_chain(dependency_chain, categories)
        self._collect_signature(signature, categories)
        diversity = {
            key: len(values)
            for key, values in categories.items()
        }
        requirements = PROCESS_REQUIREMENTS.get(
            concept,
            {key: 1 for key in DIVERSITY_KEYS},
        )
        ratios = {
            key: clamp(diversity[key] / max(requirements.get(key, 1), 1))
            for key in DIVERSITY_KEYS
        }
        context_saturation = clamp(
            sum(ratios.values()) / len(DIVERSITY_KEYS)
        )
        signature_confidence = clamp(
            signature.get(
                "signature_confidence",
                signature.get("signature_strength", 0.0),
            )
            if isinstance(signature, Mapping)
            else 0.0
        )
        dependency_coverage = clamp(
            runtime_context.get(
                "dependency_chain_coverage",
                signature.get("dependency_chain_coverage", 0.0)
                if isinstance(signature, Mapping)
                else 0.0,
            )
        )
        stability = self._stability(concept, diversity)
        context_surface_score = clamp(
            context_saturation * 0.55
            + signature_confidence * 0.18
            + dependency_coverage * 0.17
            + stability * 0.10
        )
        context_strength_estimate = clamp(
            context_surface_score * 0.82
            + context_saturation * 0.18
        )
        missing_contexts = self._missing_contexts(
            concept,
            diversity,
            requirements,
        )
        report = {
            "system": self.system_name,
            "concept": concept,
            "context_surface_score": round(context_surface_score, 4),
            "context_strength_estimate": round(context_strength_estimate, 4),
            "context_diversity": diversity,
            "context_saturation": round(context_saturation, 4),
            "missing_contexts": missing_contexts,
            "recommended_training_contexts": self._recommendations(
                concept,
                diversity,
                requirements,
            ),
            "promotion_readiness": (
                context_surface_score >= 0.68
                and context_saturation >= 0.58
                and not self._identity_scope_leakage(runtime_context, signature)
            ),
            "context_stability": round(stability, 4),
            "context_surface_evidence": {
                key: sorted(values)
                for key, values in categories.items()
            },
            "context_surface_categories_are_unique": True,
            "repetition_rewarded": False,
            "identity_scope_leakage_detected":
            self._identity_scope_leakage(runtime_context, signature),
        }
        if track_history:
            self._history.setdefault(concept, []).append(deepcopy(report))
        return report

    def report(self, concept: str | None = None) -> dict[str, Any]:
        if concept:
            concept = _normalize(concept)
            history = self._history.get(concept, [])
            return {
                "system": self.system_name,
                "concept": concept,
                "history_size": len(history),
                "latest": deepcopy(history[-1]) if history else {},
            }
        return {
            "system": self.system_name,
            "tracked_concepts": sorted(self._history),
            "history_size": sum(len(items) for items in self._history.values()),
        }

    def _collect(self, value: Any, categories: dict[str, set[str]]) -> None:
        if value is None:
            return
        if isinstance(value, Mapping):
            for key, item in value.items():
                self._collect_key_value(str(key), item, categories)
                self._collect(item, categories)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                self._collect(item, categories)
            return
        if isinstance(value, str):
            self._collect_token(value, categories)

    def _collect_key_value(
        self,
        key: str,
        value: Any,
        categories: dict[str, set[str]],
    ) -> None:
        normalized_key = _normalize(key)
        values = self._values(value)
        if normalized_key in {"direction", "directions", "axis"}:
            categories["directions"].update(_normalize(item) for item in values)
        elif normalized_key in {"color", "colors", "palette"}:
            categories["colors"].update(_normalize(item) for item in values)
        elif normalized_key in {
            "object_type",
            "object_types",
            "shape",
            "shape_signature",
        }:
            categories["object_types"].update(
                _normalize(item) for item in values
            )
        elif normalized_key in {"size", "sizes", "area", "cell_count"}:
            categories["sizes"].update(self._size_bucket(item) for item in values)
        elif normalized_key in {
            "topology",
            "topologies",
            "topology_descriptor",
            "topology_descriptors",
        }:
            categories["topologies"].update(_normalize(item) for item in values)
        elif normalized_key in {
            "spatial_pattern",
            "spatial_patterns",
            "placement_strategy",
            "relative_position",
        }:
            categories["spatial_patterns"].update(
                _normalize(item) for item in values
            )
        elif normalized_key in {"delta", "relative_offset", "position_delta"}:
            self._collect_delta(value, categories)

    def _collect_token(self, token: str, categories: dict[str, set[str]]) -> None:
        normalized = _normalize(token)
        if not normalized or normalized == "unknown":
            return
        for direction in (
            "up",
            "down",
            "left",
            "right",
            "diagonal",
            "horizontal",
            "vertical",
            "cross_axis",
        ):
            if direction in normalized:
                categories["directions"].add(direction)
        for topology in (
            "topology",
            "hole",
            "branch",
            "nested",
            "split",
            "expansion",
            "constrained",
        ):
            if topology in normalized:
                categories["topologies"].add(topology)
        for pattern in (
            "offset",
            "cross_axis",
            "nested",
            "edge",
            "interior",
            "gap",
            "turning",
            "diagonal",
        ):
            if pattern in normalized:
                categories["spatial_patterns"].add(pattern)

    def _collect_delta(self, value: Any, categories: dict[str, set[str]]) -> None:
        if isinstance(value, Mapping):
            row = value.get("delta_row", value.get("row"))
            col = value.get("delta_col", value.get("col"))
        elif isinstance(value, (list, tuple)) and len(value) >= 2:
            row, col = value[0], value[1]
        else:
            return
        try:
            row = int(row or 0)
            col = int(col or 0)
        except (TypeError, ValueError):
            return
        if row < 0:
            categories["directions"].add("up")
        elif row > 0:
            categories["directions"].add("down")
        if col < 0:
            categories["directions"].add("left")
        elif col > 0:
            categories["directions"].add("right")
        if row and col:
            categories["directions"].add("diagonal")
        if row or col:
            categories["spatial_patterns"].add("offset")

    def _collect_dependency_chain(
        self,
        chain: Iterable[Any] | None,
        categories: dict[str, set[str]],
    ) -> None:
        for node in chain or []:
            normalized = _normalize(node)
            if "topology" in normalized:
                categories["topologies"].add(normalized)
            if normalized in {"local_shape", "shape_preservation"}:
                categories["object_types"].add(normalized)
            if normalized in {"directional_motion", "position_change"}:
                categories["spatial_patterns"].add(normalized)
                categories["directions"].add("directional")

    def _collect_signature(
        self,
        signature: Mapping[str, Any],
        categories: dict[str, set[str]],
    ) -> None:
        if not isinstance(signature, Mapping):
            return
        for key in (
            "signature_invariants",
            "signature_constraints",
            "signature_capabilities",
            "signature_tokens",
        ):
            self._collect(signature.get(key), categories)

    def _values(self, value: Any) -> list[Any]:
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]

    def _size_bucket(self, value: Any) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return _normalize(value)
        if number <= 2:
            return "small"
        if number <= 6:
            return "medium"
        return "large"

    def _missing_contexts(
        self,
        concept: str,
        diversity: Mapping[str, int],
        requirements: Mapping[str, int],
    ) -> list[str]:
        missing = []
        recommendations = PROCESS_RECOMMENDATIONS.get(concept, {})
        for key in DIVERSITY_KEYS:
            if diversity.get(key, 0) < requirements.get(key, 1):
                missing.extend(recommendations.get(key, [key]))
        return _dedupe(missing)

    def _recommendations(
        self,
        concept: str,
        diversity: Mapping[str, int],
        requirements: Mapping[str, int],
    ) -> list[str]:
        missing = self._missing_contexts(concept, diversity, requirements)
        if missing:
            return missing[:6]
        return [
            f"{concept}_cross_context_validation",
            f"{concept}_unseen_spatial_configuration",
        ]

    def _stability(self, concept: str, diversity: Mapping[str, int]) -> float:
        history = self._history.get(concept, [])
        if not history:
            return 0.72
        previous = history[-1].get("context_diversity", {})
        stable = sum(
            1
            for key in DIVERSITY_KEYS
            if diversity.get(key, 0) >= previous.get(key, 0)
        )
        return clamp(stable / len(DIVERSITY_KEYS))

    def _identity_scope_leakage(
        self,
        runtime_context: Mapping[str, Any],
        signature: Mapping[str, Any],
    ) -> bool:
        if runtime_context.get("identity_scope_leakage_detected"):
            return True
        if isinstance(signature, Mapping):
            return bool(signature.get("identity_scope_leakage_detected"))
        return False


def _normalize(value: Any, default: str = "unknown") -> str:
    if value is None:
        return default
    return str(value).strip().lower().replace(" ", "_") or default


def _dedupe(values: Iterable[Any]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        normalized = _normalize(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


context_surface_engine = ContextSurfaceEngine()


__all__ = [
    "ContextSurfaceEngine",
    "context_surface_engine",
]
