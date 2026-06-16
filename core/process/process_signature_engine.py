"""Canonical process signature extraction from dependency-chain evidence."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from core.process_abstraction import ProcessAbstractionLayer


PROCESS_SIGNATURE_RULES = {
    "replication": {
        "signature": "replication_signature",
        "context_surface": "replication_context",
        "required": (
            "identity_forking",
            "identity_split",
            "object_count_increase",
            "topology_splitting",
        ),
    },
    "propagation": {
        "signature": "propagation_signature",
        "context_surface": "propagation_context",
        "required": (
            "source_pattern_preserved",
            "directional_motion",
            "position_change",
        ),
    },
    "growth": {
        "signature": "growth_signature",
        "context_surface": "growth_context",
        "required": (
            "identity_persistence",
            "topology_expansion",
            "shape_preservation",
        ),
    },
    "topological_growth": {
        "signature": "topological_growth_signature",
        "context_surface": "topological_growth_context",
        "required": (
            "topology_expansion",
            "local_shape",
            "topology_preservation",
        ),
    },
    "directional_motion": {
        "signature": "directional_motion_signature",
        "context_surface": "directional_motion_context",
        "required": (
            "directional_motion",
            "position_delta",
            "position_change",
        ),
    },
    "symmetry_reasoning": {
        "signature": "symmetry_signature",
        "context_surface": "symmetry_context",
        "required": (
            "symmetry_preservation",
            "reflection_relation",
        ),
    },
    "symmetry": {
        "signature": "symmetry_signature",
        "context_surface": "symmetry_context",
        "required": (
            "symmetry_preservation",
            "reflection_relation",
        ),
    },
    "color": {
        "signature": "color_signature",
        "context_surface": "color_context",
        "required": (
            "color_relation",
            "color_mapping",
        ),
    },
    "shape": {
        "signature": "shape_signature",
        "context_surface": "shape_context",
        "required": (
            "shape_preservation",
            "local_shape",
        ),
    },
    "topology": {
        "signature": "topology_signature",
        "context_surface": "topology_context",
        "required": (
            "topology_relation",
            "topology_preservation",
        ),
    },
}


STATIC_SIGNATURES = {
    "replication_signature": {
        "constraints": ("requires_source_object",),
        "capabilities": ("identity_split_reasoning",),
        "invariants": ("identity_split", "structural_copying"),
    },
    "propagation_signature": {
        "constraints": ("requires_source_pattern", "requires_directional_path"),
        "capabilities": ("directional_transfer", "pattern_extension"),
        "invariants": ("source_pattern_preserved", "position_change"),
    },
    "growth_signature": {
        "constraints": ("requires_identity_anchor", "requires_shape_anchor"),
        "capabilities": ("identity_preserving_growth", "topology_growth"),
        "invariants": ("identity_persistence", "shape_preservation"),
    },
    "topological_growth_signature": {
        "constraints": ("requires_connectivity_reference",),
        "capabilities": ("topology_growth", "topology_relation_inference"),
        "invariants": ("topology_expansion", "topology_preservation"),
    },
    "directional_motion_signature": {
        "constraints": ("requires_reference_frame", "requires_position_delta"),
        "capabilities": ("directional_motion_reasoning",),
        "invariants": ("position_change", "position_delta"),
    },
    "symmetry_signature": {
        "constraints": ("requires_axis_or_reflection_reference",),
        "capabilities": ("relational_symmetry_inference",),
        "invariants": ("reflection_relation", "symmetry_preservation"),
    },
    "color_signature": {
        "constraints": ("requires_color_mapping",),
        "capabilities": ("color_relation_inference",),
        "invariants": ("color_mapping", "palette_relation"),
    },
    "shape_signature": {
        "constraints": ("requires_shape_anchor",),
        "capabilities": ("shape_relation_inference",),
        "invariants": ("shape_preservation", "local_shape"),
    },
    "topology_signature": {
        "constraints": ("requires_connectivity_reference",),
        "capabilities": ("topology_relation_inference",),
        "invariants": ("topology_preservation", "connectivity_relation"),
    },
}


class ProcessSignatureEngine:
    """Convert dependency chains into reusable canonical process signatures."""

    system_name = "process_signature_engine"

    def extract_signature(
        self,
        concept: str,
        dependency_chain: Iterable[Any] | None = None,
        typed_dependencies: Iterable[Mapping[str, Any]] | None = None,
        process_dependency_memory: Mapping[str, Any] | None = None,
        transformation_report: Mapping[str, Any] | None = None,
        semantic_context: Mapping[str, Any] | None = None,
        dependency_semantics_score: float = 0.0,
    ) -> dict[str, Any]:
        concept = _normalize(concept)
        process_memory = (
            process_dependency_memory
            if isinstance(process_dependency_memory, Mapping)
            else {}
        )
        chain = list(
            dependency_chain
            or process_memory.get("resolved_dependency_chain")
            or []
        )
        dependencies = list(
            typed_dependencies
            or process_memory.get("typed_dependency_relations")
            or []
        )
        nodes = self._nodes_from(chain, dependencies)
        signals = self._signals_from(
            nodes,
            transformation_report=transformation_report,
            semantic_context=semantic_context,
        )
        matched = self._matched_signatures(concept, signals)
        primary = matched[0] if matched else self._fallback_signature(concept)
        confidence = self._signature_confidence(
            primary,
            signals,
            process_memory,
            dependency_semantics_score,
        )
        canonical = self._canonical_payload(
            concept,
            primary,
            confidence,
            signals,
            transformation_report,
            semantic_context,
        )
        required = tuple(primary.get("required", ())) if primary else ()
        matched_features = [
            feature
            for feature in required
            if signals.get(feature)
        ]
        missing_features = [
            feature
            for feature in required
            if not signals.get(feature)
        ]
        signature = primary.get("signature") if primary else None
        context_surface = primary.get("context_surface") if primary else None
        leakage = self._identity_scope_leakage(concept, signals, primary)
        return {
            "system": self.system_name,
            "concept": concept,
            "signature": signature,
            "signature_id": signature,
            "signature_context": context_surface,
            "canonical_process_context": context_surface,
            "context_surface": context_surface,
            "signature_confidence": confidence,
            "signature_strength": confidence,
            "signature_invariants": canonical["signature_invariants"],
            "signature_constraints": canonical["signature_constraints"],
            "signature_capabilities": canonical["signature_capabilities"],
            "concept_signature": canonical["concept_signature"],
            "process_signature_generated": bool(primary),
            "required_features": list(required),
            "matched_features": matched_features,
            "missing_features": missing_features,
            "matched_signatures": [
                item["signature"]
                for item in matched
            ],
            "process_signatures": matched,
            "signature_tokens": sorted(
                key for key, value in signals.items() if value
            ),
            "signals": signals,
            "dependency_nodes": sorted(nodes),
            "dependency_chain": chain,
            "dependency_chain_depth": int(
                process_memory.get(
                    "dependency_chain_depth",
                    max(len(chain) - 1, 0),
                )
                or 0
            ),
            "dependency_chain_coverage": clamp(
                process_memory.get(
                    "dependency_chain_coverage",
                    1.0 if chain else 0.0,
                )
            ),
            "process_dependency_links_used": int(
                process_memory.get(
                    "process_dependency_links_used",
                    max(len(chain) - 1, 0),
                )
                or 0
            ),
            "identity_scope_leakage_detected": leakage,
        }

    def signature_dependency(
        self,
        concept: str,
        signature_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        signature = signature_report.get("signature")
        return {
            "source": _normalize(concept),
            "target": signature,
            "relation": "supports",
            "confidence": clamp(
                signature_report.get("signature_confidence", 0.0)
            ),
            "dependency_type": "process_signature",
            "required": False,
            "supported": bool(signature),
            "transfer_success": bool(signature)
            and not signature_report.get("identity_scope_leakage_detected"),
            "metadata": {
                "process_signature": True,
                "signature": signature,
                "context_surface": signature_report.get("context_surface"),
                "signature_invariants": list(
                    signature_report.get("signature_invariants", [])
                ),
                "signature_capabilities": list(
                    signature_report.get("signature_capabilities", [])
                ),
            },
        }

    def _matched_signatures(self, concept, signals):
        ordered = [concept] + [
            item
            for item in (
                "replication",
                "propagation",
                "growth",
                "topological_growth",
                "directional_motion",
                "symmetry_reasoning",
                "symmetry",
                "color",
                "shape",
                "topology",
            )
            if item != concept
        ]
        matches = []
        for name in ordered:
            rule = PROCESS_SIGNATURE_RULES.get(name)
            if not rule:
                continue
            required = rule["required"]
            matched = sum(1 for feature in required if signals.get(feature))
            if matched == len(required):
                matches.append({
                    **rule,
                    "concept": name,
                    "matched_feature_count": matched,
                })
        return matches

    def _fallback_signature(self, concept):
        rule = PROCESS_SIGNATURE_RULES.get(concept)
        if not rule:
            return None
        return {
            **rule,
            "concept": concept,
            "matched_feature_count": 0,
        }

    def _signature_confidence(
        self,
        signature,
        signals,
        process_memory,
        dependency_score,
    ):
        if not signature:
            return 0.0
        required = signature["required"]
        matched_ratio = (
            sum(1 for feature in required if signals.get(feature))
            / max(len(required), 1)
        )
        memory_confidence = clamp(
            process_memory.get("dependency_confidence", dependency_score)
        )
        coverage = clamp(process_memory.get("dependency_chain_coverage", 0.0))
        if coverage == 0.0 and matched_ratio > 0.0:
            coverage = matched_ratio
        support_bonus = min(
            sum(1 for value in signals.values() if value) / 12.0,
            1.0,
        )
        return clamp(
            matched_ratio * 0.54
            + max(memory_confidence, clamp(dependency_score)) * 0.26
            + coverage * 0.12
            + support_bonus * 0.08
        )

    def _nodes_from(self, dependency_chain, typed_dependencies):
        nodes = {
            _normalize(node)
            for node in dependency_chain or []
            if node
        }
        for dependency in typed_dependencies or []:
            if not isinstance(dependency, Mapping):
                continue
            for key in ("source", "target", "relation"):
                value = dependency.get(key)
                if value:
                    nodes.add(_normalize(value))
            evidence = dependency.get("evidence", {})
            if isinstance(evidence, Mapping):
                for key, value in evidence.items():
                    if value is True:
                        nodes.add(_normalize(key))
            metadata = dependency.get("metadata", {})
            if isinstance(metadata, Mapping):
                for key, value in metadata.items():
                    if value is True:
                        nodes.add(_normalize(key))
        return nodes

    def _signals_from(
        self,
        nodes,
        transformation_report=None,
        semantic_context=None,
    ):
        transformation_report = (
            transformation_report
            if isinstance(transformation_report, Mapping)
            else {}
        )
        semantic_context = (
            semantic_context
            if isinstance(semantic_context, Mapping)
            else {}
        )
        algebra = transformation_report.get("transformation_algebra", {})
        algebra = algebra if isinstance(algebra, Mapping) else {}
        invariants = algebra.get("invariants", {})
        invariants = invariants if isinstance(invariants, Mapping) else {}
        signature = transformation_report.get("transformation_signature", {})
        signature = signature if isinstance(signature, Mapping) else {}
        types = {
            _normalize(item)
            for item in algebra.get("transformation_types", [])
            if item
        }
        operator_types = {
            _normalize(item)
            for item in signature.get("operator_types", [])
            if item
        }
        semantic_tokens = {
            _normalize(item)
            for key in (
                "properties",
                "capabilities",
                "constraints",
                "invariants",
                "native_contexts",
            )
            for item in semantic_context.get(key, []) or []
            if item
        }
        all_tokens = set(nodes) | semantic_tokens | types | operator_types
        return {
            "identity_forking": bool(
                nodes & {"identity_forking", "identity_split", "forks"}
                or invariants.get("forks_identity")
                or "replication" in types
            ),
            "identity_split": bool(
                nodes & {"identity_split", "identity_forking"}
                or invariants.get("forks_identity")
                or "replication" in types
            ),
            "object_count_increase": bool(
                nodes & {"object_count_increase", "object_creation"}
                or "replication" in types
            ),
            "topology_splitting": bool(
                nodes & {"topology_splitting", "identity_split"}
            ),
            "source_pattern_preserved": bool(
                "source_pattern_preserved" in nodes
            ),
            "directional_motion": bool(
                nodes & {"directional_motion", "directional_displacement"}
                or types & {"propagation", "translation"}
            ),
            "position_change": bool(
                nodes
                & {
                    "position_change",
                    "position_delta",
                    "position_preservation",
                    "position",
                }
                or types & {"propagation", "translation"}
            ),
            "position_delta": bool(
                nodes & {"position_delta", "directional_motion"}
            ),
            "identity_persistence": bool(
                nodes
                & {
                    "identity_persistence",
                    "identity_continuity",
                    "object_persistence",
                }
                or invariants.get("preserves_identity")
                or "growth" in types
            ),
            "topology_expansion": bool(
                nodes
                & {
                    "topology_expansion",
                    "topological_growth",
                    "region_expansion",
                    "growth",
                }
                or invariants.get("modifies_topology")
                or types
                & {"growth", "topological_growth", "topology_expansion"}
            ),
            "shape_preservation": bool(
                nodes
                & {
                    "shape_preservation",
                    "local_shape",
                    "object_core",
                }
                or invariants.get("preserves_shape")
            ),
            "local_shape": bool(
                nodes & {"local_shape", "shape_preservation"}
            ),
            "topology_preservation": bool(
                nodes
                & {
                    "topology_preservation",
                    "local_shape",
                    "shape_preservation",
                }
                or invariants.get("preserves_topology")
            ),
            "symmetry_preservation": bool(
                all_tokens
                & {
                    "symmetry_preservation",
                    "symmetry_reasoning",
                    "symmetry",
                }
            ),
            "reflection_relation": bool(
                all_tokens
                & {
                    "reflection",
                    "reflection_relation",
                    "mirror",
                    "flip_horizontal",
                    "flip_vertical",
                }
            ),
            "color_relation": bool(
                all_tokens & {"color", "color_relation", "recolor"}
                or not signature.get("preserves_color", True)
            ),
            "color_mapping": bool(
                all_tokens & {"color_mapping", "palette_relation", "recolor"}
            ),
            "topology_relation": bool(
                all_tokens
                & {
                    "topology",
                    "topology_relation",
                    "topology_expansion",
                    "topological_growth",
                }
                or invariants.get("modifies_topology")
            ),
        }

    def _identity_scope_leakage(self, concept, signals, signature):
        if not signature:
            return False
        preserving_signature = signature["signature"] == "growth_signature"
        forking_signature = signature["signature"] in {
            "replication_signature",
            "topological_growth_signature",
        }
        return bool(
            signals.get("identity_forking")
            and signals.get("identity_persistence")
            and not (preserving_signature or forking_signature)
            and concept not in {"replication", "topological_growth"}
        )

    def _canonical_payload(
        self,
        concept,
        signature,
        confidence,
        signals,
        transformation_report,
        semantic_context,
    ):
        if not signature:
            return {
                "concept_signature": None,
                "signature_constraints": [],
                "signature_capabilities": [],
                "signature_invariants": [],
            }
        abstraction = ProcessAbstractionLayer.get(concept)
        static = STATIC_SIGNATURES.get(signature["signature"], {})
        semantic_context = (
            semantic_context
            if isinstance(semantic_context, Mapping)
            else {}
        )
        constraints = _dedupe(
            list(getattr(abstraction, "constraints", ()) if abstraction else ())
            + list(static.get("constraints", ()))
            + list(semantic_context.get("constraints", []) or [])
        )
        capabilities = _dedupe(
            list(getattr(abstraction, "capabilities", ()) if abstraction else ())
            + list(static.get("capabilities", ()))
            + list(semantic_context.get("capabilities", []) or [])
        )
        invariants = self._canonical_invariants(
            signature,
            signals,
            transformation_report,
            abstraction,
            static,
            semantic_context,
        )
        return {
            "concept_signature": {
                "signature": signature["signature"],
                "signature_id": signature["signature"],
                "concept": concept,
                "canonical_process_context": signature["context_surface"],
                "context_surface": signature["context_surface"],
                "required_features": list(signature["required"]),
                "constraints": constraints,
                "capabilities": capabilities,
                "invariants": invariants,
                "signature_confidence": confidence,
            },
            "signature_constraints": constraints,
            "signature_capabilities": capabilities,
            "signature_invariants": invariants,
        }

    def _canonical_invariants(
        self,
        signature,
        signals,
        transformation_report,
        abstraction,
        static,
        semantic_context,
    ):
        transformation_report = (
            transformation_report
            if isinstance(transformation_report, Mapping)
            else {}
        )
        algebra = transformation_report.get("transformation_algebra", {})
        algebra = algebra if isinstance(algebra, Mapping) else {}
        algebra_invariants = algebra.get("invariants", {})
        algebra_invariants = (
            algebra_invariants
            if isinstance(algebra_invariants, Mapping)
            else {}
        )
        invariant_tokens = [
            key for key, value in algebra_invariants.items() if value
        ]
        invariant_tokens.extend(
            key
            for key, value in signals.items()
            if value and key in signature["required"]
        )
        invariant_tokens.extend(static.get("invariants", ()))
        if abstraction:
            invariant_tokens.extend(abstraction.inherited_features)
        invariant_tokens.extend(semantic_context.get("invariants", []) or [])
        return _dedupe(invariant_tokens)


def _normalize(value, default="unknown"):
    if value is None:
        return default
    return str(value).strip().lower().replace(" ", "_") or default


def _dedupe(values):
    seen = set()
    result = []
    for value in values:
        normalized = _normalize(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


__all__ = [
    "PROCESS_SIGNATURE_RULES",
    "ProcessSignatureEngine",
]
