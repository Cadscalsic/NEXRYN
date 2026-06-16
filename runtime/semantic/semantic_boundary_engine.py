"""Semantic boundary governance for truth-preserving concepts."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from core.semantic_context import SemanticContextReasoner
from core.context_hierarchy import ContextHierarchy
from runtime.semantic.invariant_boundary_engine import InvariantBoundaryEngine


CONCEPT_BOUNDARIES = {
    "color_preservation": {
        "core_invariants": (
            "color_stability",
            "attribute_mapping_preservation",
            "no_color_reassignment",
            "color_preservation_expected",
        ),
        "neighbor_concepts": (
            "recoloring",
            "symbolic_remapping",
            "color_mapping",
            "attribute_remapping",
            "color_expansion",
            "shape_preservation",
            "position_preservation",
        ),
        "forbidden_tokens": (
            "recoloring",
            "color_reassignment",
            "unmapped_recoloring",
            "palette_change",
            "color_expansion",
            "hue_transform",
            "attribute_remapping",
        ),
    },
    "shape_preservation": {
        "core_invariants": (
            "shape_stability",
            "local_shape_preservation",
            "boundary_geometry_preservation",
        ),
        "neighbor_concepts": (
            "topology_preservation",
            "color_preservation",
            "scaling",
            "rotation",
        ),
        "forbidden_tokens": (
            "shape_reassignment",
            "untracked_shape_transform",
            "geometry_rewrite",
        ),
    },
    "topology_preservation": {
        "core_invariants": (
            "topology_stability",
            "connectivity_preservation",
            "region_relation_preservation",
        ),
        "neighbor_concepts": (
            "topological_growth",
            "shape_preservation",
            "replication",
        ),
        "forbidden_tokens": (
            "topology_splitting",
            "topology_expansion",
            "connectivity_change",
        ),
    },
    "symmetry_reasoning": {
        "core_invariants": (
            "symmetry_relation",
            "symmetry_axis",
            "object_pair_mapping",
            "relation_consistency",
            "relational_symmetry",
        ),
        "neighbor_concepts": (
            "symmetry_preservation",
            "reflection_relation",
            "spatial_inversion",
            "mirror_pairing",
        ),
        "forbidden_tokens": (
            "intrinsic_property_only",
            "axisless_symmetry",
            "unpaired_symmetry",
            "relation_conflict",
        ),
    },
}


class SemanticBoundaryEngine:
    """Measure whether a concept remains inside its intended definition."""

    system_name = "semantic_boundary_engine"

    def __init__(self):
        self.invariant_boundary_engine = InvariantBoundaryEngine()

    def evaluate(
        self,
        concept: str,
        semantic_context: Mapping[str, Any] | None = None,
        context_hierarchy: Mapping[str, Any] | None = None,
        contextual_truth_report: Mapping[str, Any] | None = None,
        task_metadata: Mapping[str, Any] | Iterable[Any] | None = None,
        transformation_traces: Iterable[Any] | Mapping[str, Any] | None = None,
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
        context_hierarchy = (
            context_hierarchy
            if isinstance(context_hierarchy, Mapping)
            else runtime_context.get("context_hierarchy", {})
        )
        boundary = self._boundary_for(concept, semantic_context)
        known_boundary = concept in CONCEPT_BOUNDARIES
        invariant_boundary = runtime_context.get(
            "invariant_boundary_report",
            {},
        )
        invariant_boundary = (
            invariant_boundary
            if isinstance(invariant_boundary, Mapping)
            else {}
        )
        if not invariant_boundary:
            invariant_boundary = self.invariant_boundary_engine.evaluate(
                concept,
                semantic_context=semantic_context,
                runtime_context=runtime_context,
                evidence=[
                    contextual_truth_report,
                    task_metadata,
                    transformation_traces,
                ],
            )
        core_invariants = sorted(boundary["core_invariants"])
        neighbor_concepts = sorted(boundary["neighbor_concepts"])
        forbidden_tokens = set(boundary["forbidden_tokens"])
        allowed_variations = set(
            invariant_boundary.get("allowed_variations", [])
        )
        required_invariants = set(
            invariant_boundary.get("required_invariants", [])
        )
        forbidden_tokens.update(
            invariant_boundary.get("forbidden_variations", [])
        )
        core_invariants = sorted(set(core_invariants) | required_invariants)

        evidence = [
            semantic_context,
            context_hierarchy,
            contextual_truth_report,
            task_metadata,
            transformation_traces,
            runtime_context.get("context_discovery"),
            runtime_context.get("causal_graph_alignment"),
            runtime_context.get("causal_validation"),
            runtime_context.get("relational_reasoning_report"),
        ]
        tokens = set()
        exact_tokens = set()
        for item in evidence:
            tokens.update(_tokens(item))
            exact_tokens.update(_exact_tokens(item))

        supported_invariants = [
            invariant
            for invariant in core_invariants
            if invariant in tokens
        ]
        forbidden_expansions = sorted(
            token
            for token in forbidden_tokens
            if token in exact_tokens
            and token not in allowed_variations
        )
        concept_overlap = self._concept_overlap(
            concept,
            tokens,
            neighbor_concepts,
        )
        overlap_score = clamp(
            sum(concept_overlap.values()) / max(len(concept_overlap), 1)
        )
        invariant_overlap_score = clamp(
            invariant_boundary.get("invariant_overlap_score", 0.0)
        )
        overlap_score = clamp(min(overlap_score, invariant_overlap_score))
        invariant_score = clamp(
            len(supported_invariants) / max(len(core_invariants), 1)
        )
        forbidden_score = clamp(
            len(forbidden_expansions) / max(len(forbidden_tokens), 1)
        )
        boundary_integrity = clamp(
            invariant_score * 0.58
            + (1.0 - forbidden_score) * 0.28
            + (1.0 - overlap_score) * 0.14
        )
        semantic_drift_score = clamp(
            (1.0 - boundary_integrity) * 0.58
            + forbidden_score * 0.42
            + overlap_score * 0.08
        )
        if forbidden_expansions:
            semantic_drift_score = max(semantic_drift_score, 0.22)
        review_required = (
            boundary_integrity < 0.80
            or semantic_drift_score > 0.18
            or bool(forbidden_expansions)
        )
        return {
            "system": self.system_name,
            "concept": concept,
            "semantic_drift_score": round(semantic_drift_score, 4),
            "boundary_integrity": round(boundary_integrity, 4),
            "core_invariants": core_invariants,
            "supported_core_invariants": supported_invariants,
            "neighbor_concepts": neighbor_concepts,
            "forbidden_expansions": forbidden_expansions,
            "concept_overlap": concept_overlap,
            "invariant_boundary_report": invariant_boundary,
            "invariant_overlap_score": invariant_overlap_score,
            "review_required": review_required,
            "boundary_validated": not review_required,
            "known_boundary": known_boundary,
            "preserve_conceptual_purity": True,
        }

    def _boundary_for(self, concept, semantic_context):
        if concept in CONCEPT_BOUNDARIES:
            return {
                key: set(value)
                for key, value in CONCEPT_BOUNDARIES[concept].items()
            }
        context_name = _normalize(
            semantic_context.get("context_name")
            or semantic_context.get("context")
            or semantic_context.get("semantic_context")
            or f"{concept}_context"
        )
        native = SemanticContextReasoner.TRUTH_NATIVE_CONTEXTS.get(
            context_name,
            {},
        )
        hierarchy_children = ContextHierarchy.ROOT_CONTEXTS.get(
            context_name,
            set(),
        )
        invariants = set(_plain_values(native.get("properties", [])))
        invariants.update(_plain_values(native.get("implications", [])))
        if not invariants:
            invariants.add(concept)
        neighbors = set(hierarchy_children) - {concept}
        forbidden = {
            item
            for item in neighbors
            if any(
                marker in item
                for marker in (
                    "reassignment",
                    "recoloring",
                    "splitting",
                    "expansion",
                    "deletion",
                    "remapping",
                )
            )
        }
        return {
            "core_invariants": invariants,
            "neighbor_concepts": neighbors,
            "forbidden_tokens": forbidden,
        }

    def _concept_overlap(self, concept, tokens, neighbor_concepts):
        overlap = {}
        for neighbor in neighbor_concepts:
            neighbor = _normalize(neighbor)
            if neighbor == concept:
                continue
            related = {neighbor}
            related.update(_split_parts(neighbor))
            score = clamp(len(tokens & related) / max(len(related), 1))
            if score > 0:
                overlap[neighbor] = round(score, 4)
        return overlap


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _plain_values(value):
    values = []
    if isinstance(value, Mapping):
        value = value.values()
    if isinstance(value, (str, bytes)):
        value = [value]
    try:
        iterable = list(value)
    except TypeError:
        iterable = [value]
    for item in iterable:
        if isinstance(item, Mapping):
            values.extend(_plain_values(item.values()))
        else:
            normalized = _normalize(item)
            if normalized:
                values.append(normalized)
    return values


def _tokens(item) -> set[str]:
    tokens = set()
    if item is None:
        return tokens
    if isinstance(item, Mapping):
        for key, value in item.items():
            key_token = _normalize(key)
            if key_token:
                tokens.add(key_token)
            tokens.update(_tokens(value))
    elif isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
        for value in item:
            tokens.update(_tokens(value))
    else:
        token = _normalize(item)
        if token:
            tokens.add(token)
            tokens.update(_split_parts(token))
    return tokens


def _exact_tokens(item) -> set[str]:
    tokens = set()
    if item is None:
        return tokens
    if isinstance(item, Mapping):
        for key, value in item.items():
            key_token = _normalize(key)
            if key_token:
                tokens.add(key_token)
            tokens.update(_exact_tokens(value))
    elif isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
        for value in item:
            tokens.update(_exact_tokens(value))
    else:
        token = _normalize(item)
        if token:
            tokens.add(token)
    return tokens


def _split_parts(token):
    return {
        part
        for part in _normalize(token).split("_")
        if part
    }


semantic_boundary_engine = SemanticBoundaryEngine()


__all__ = [
    "SemanticBoundaryEngine",
    "semantic_boundary_engine",
]
