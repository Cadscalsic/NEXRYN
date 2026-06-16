"""Separate identity invariants from attribute invariants."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


INVARIANT_BOUNDARIES = {
    "color_preservation": {
        "required_invariants": (
            "color_stability",
            "attribute_mapping_preservation",
            "no_color_reassignment",
        ),
        "allowed_variations": (
            "position_change",
            "shape_preserved",
            "identity_persistence",
            "object_identity_preserved",
        ),
        "forbidden_variations": (
            "color_reassignment",
            "recoloring",
            "palette_change",
            "unmapped_recoloring",
            "hue_transform",
            "color_expansion",
            "attribute_remapping",
        ),
        "separate_from": (
            "object_identity_preservation",
            "identity_persistence",
        ),
    },
    "object_identity_preservation": {
        "required_invariants": (
            "object_persistence",
            "lineage_continuity",
            "identity_continuity",
            "object_core",
        ),
        "allowed_variations": (
            "color_reassignment",
            "recoloring",
            "palette_change",
            "attribute_remapping",
            "position_change",
            "size_change",
        ),
        "forbidden_variations": (
            "identity_split",
            "identity_reassignment",
            "object_deletion",
            "object_merge",
            "lineage_break",
        ),
        "separate_from": (
            "color_preservation",
            "shape_preservation",
            "position_preservation",
        ),
    },
    "identity_persistence": {
        "required_invariants": (
            "object_persistence",
            "identity_continuity",
            "object_core",
        ),
        "allowed_variations": (
            "color_reassignment",
            "recoloring",
            "palette_change",
            "attribute_remapping",
            "position_change",
        ),
        "forbidden_variations": (
            "identity_split",
            "identity_reassignment",
            "object_deletion",
            "lineage_break",
        ),
        "separate_from": (
            "color_preservation",
            "shape_preservation",
        ),
    },
    "symmetry_reasoning": {
        "required_invariants": (
            "symmetry_relation",
            "symmetry_axis",
            "object_pair_mapping",
            "relation_consistency",
            "relational_symmetry",
        ),
        "allowed_variations": (
            "symmetry_preservation",
            "reflection_relation",
            "mirror_pairing",
            "spatial_inversion",
        ),
        "forbidden_variations": (
            "intrinsic_property_only",
            "axisless_symmetry",
            "unpaired_symmetry",
            "relation_conflict",
        ),
        "separate_from": (
            "color_preservation",
            "shape_preservation",
            "object_identity_preservation",
        ),
    },
}


class InvariantBoundaryEngine:
    """Define which variations preserve a concept and which break it."""

    system_name = "invariant_boundary_engine"

    def evaluate(
        self,
        concept: str,
        semantic_context: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        evidence: Iterable[Any] | Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        concept = _normalize(concept)
        semantic_context = (
            semantic_context
            if isinstance(semantic_context, Mapping)
            else {}
        )
        runtime_context = (
            runtime_context
            if isinstance(runtime_context, Mapping)
            else {}
        )
        boundary = self._boundary_for(concept)
        required = sorted(boundary["required_invariants"])
        allowed = sorted(boundary["allowed_variations"])
        forbidden = sorted(boundary["forbidden_variations"])
        separate_from = sorted(boundary["separate_from"])

        tokens = set()
        tokens.update(_tokens(semantic_context))
        tokens.update(_tokens(runtime_context.get("context_hierarchy")))
        tokens.update(_tokens(runtime_context.get("context_discovery")))
        tokens.update(_tokens(runtime_context.get("causal_graph_alignment")))
        tokens.update(_tokens(runtime_context.get("causal_validation")))
        tokens.update(_tokens(runtime_context.get("relational_reasoning_report")))
        tokens.update(_tokens(evidence))

        required_hits = set(required) & tokens
        allowed_hits = set(allowed) & tokens
        forbidden_hits = set(forbidden) & tokens
        overlapping_concepts = [
            item
            for item in separate_from
            if item in tokens
        ]

        overlap_numerator = len(overlapping_concepts) + len(
            forbidden_hits & set(allowed)
        )
        overlap_denominator = max(len(separate_from) + len(forbidden), 1)
        invariant_overlap_score = clamp(
            overlap_numerator / overlap_denominator
        )
        separation_score = clamp(
            len(required_hits) / max(len(required), 1)
            + len(allowed_hits) / max(len(allowed), 1) * 0.25
            - invariant_overlap_score
        )
        return {
            "system": self.system_name,
            "concept": concept,
            "required_invariants": required,
            "allowed_variations": allowed,
            "forbidden_variations": forbidden,
            "observed_required_invariants": sorted(required_hits),
            "observed_allowed_variations": sorted(allowed_hits),
            "observed_forbidden_variations": sorted(forbidden_hits),
            "overlapping_concepts": overlapping_concepts,
            "invariant_overlap_score": round(invariant_overlap_score, 4),
            "invariant_separation_score": round(separation_score, 4),
            "identity_attribute_separated": invariant_overlap_score <= 0.20,
        }

    def _boundary_for(self, concept):
        if concept in INVARIANT_BOUNDARIES:
            return {
                key: set(value)
                for key, value in INVARIANT_BOUNDARIES[concept].items()
            }
        return {
            "required_invariants": {concept},
            "allowed_variations": set(),
            "forbidden_variations": set(),
            "separate_from": set(),
        }


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


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
            tokens.update(_phrase_prefixes(token))
            tokens.update(_split_parts(token))
    return tokens


def _split_parts(token):
    return {
        part
        for part in _normalize(token).split("_")
        if part
    }


def _phrase_prefixes(token):
    parts = [
        part
        for part in _normalize(token).split("_")
        if part
    ]
    return {
        "_".join(parts[:index])
        for index in range(2, len(parts) + 1)
    }


invariant_boundary_engine = InvariantBoundaryEngine()


__all__ = [
    "InvariantBoundaryEngine",
    "invariant_boundary_engine",
]
