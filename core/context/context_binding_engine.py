from core.epistemic_models import clamp


def _normalize(value, default="unknown"):
    if value is None:
        return default
    return str(value).strip().lower().replace(" ", "_") or default


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return list(value.keys())
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


class ContextBindingEngine:
    """Explains why a truth belongs to a discovered context."""

    FAMILY_MECHANISMS = {
        "duplication": [
            "structural_replication",
            "object_instance_creation",
            "shape_equivalence",
        ],
        "replication": [
            "structural_replication",
            "object_instance_creation",
            "shape_equivalence",
        ],
        "translation": [
            "spatial_translation",
            "stable_reference_frame",
            "shape_equivalence",
            "identity_continuity",
        ],
        "reflection": [
            "axis_reflection",
            "mirror_consistency",
            "shape_equivalence",
            "identity_continuity",
        ],
        "rotation": [
            "orientation_change",
            "shape_equivalence",
            "identity_continuity",
        ],
        "recoloring": [
            "attribute_remapping",
            "color_mapping_rule",
            "shape_equivalence",
            "topology_continuity",
        ],
        "symbolic_remapping": [
            "attribute_remapping",
            "color_mapping_rule",
            "role_continuity",
        ],
        "color_context": [
            "color_mapping_rule",
            "no_color_reassignment",
            "attribute_remapping",
        ],
        "symmetry_context": [
            "mirror_consistency",
            "axis_reflection",
            "symmetry_reasoning",
        ],
        "identity_preservation": [
            "lineage_continuity",
            "identity_continuity",
        ],
        "growth": [
            "source_pattern_preservation",
            "topology_expansion",
            "region_expansion",
        ],
        "topological_growth": [
            "source_pattern_preservation",
            "topology_expansion",
            "region_expansion",
            "topology_split_reasoning",
        ],
        "topological_growth_context": [
            "source_pattern_preservation",
            "topology_expansion",
            "region_expansion",
            "topology_split_reasoning",
        ],
        "propagation": [
            "source_pattern_preservation",
            "recursive_spread",
            "pattern_extension",
        ],
        "directional_motion": [
            "stable_reference_frame",
            "directional_transfer",
            "identity_continuity",
        ],
        "directional_motion_context": [
            "stable_reference_frame",
            "directional_transfer",
            "identity_continuity",
        ],
    }

    SIGNAL_MECHANISMS = {
        "preserves_shape": "shape_equivalence",
        "structure_preservation": "shape_equivalence",
        "structural_replication": "structural_replication",
        "creates_objects": "object_instance_creation",
        "object_creation": "object_instance_creation",
        "preserves_identity": "identity_continuity",
        "lineage_continuity": "lineage_continuity",
        "identity_continuity": "identity_continuity",
        "preserves_topology": "topology_continuity",
        "topology_continuity": "topology_continuity",
        "color_mapping_rule": "color_mapping_rule",
        "attribute_remapping": "attribute_remapping",
        "attribute_mapping": "attribute_remapping",
        "attribute_mapping_preservation": "color_mapping_rule",
        "color_stability": "no_color_reassignment",
        "contextual_color_stability": "no_color_reassignment",
        "color_preservation_reasoning": "color_mapping_rule",
        "no_color_reassignment": "no_color_reassignment",
        "mirror_consistency": "mirror_consistency",
        "symmetry_axis": "mirror_consistency",
        "axis_consistency": "axis_reflection",
        "symmetry_relation": "mirror_consistency",
        "symmetry_reasoning": "symmetry_reasoning",
        "mirror_consistency_check": "mirror_consistency",
        "coordinate_stability": "stable_reference_frame",
        "stable_reference_frame": "stable_reference_frame",
        "source_pattern_preserved": "source_pattern_preservation",
        "source_pattern_preservation": "source_pattern_preservation",
        "propagates_structure": "recursive_spread",
        "directional_spread": "recursive_spread",
        "signal_transfer": "pattern_extension",
        "position_delta": "stable_reference_frame",
        "directional_displacement": "directional_transfer",
        "source_pattern_motion": "source_pattern_preservation",
        "directional_transfer": "directional_transfer",
        "pattern_extension": "pattern_extension",
        "topology_growth": "topology_expansion",
        "topology_expansion": "topology_expansion",
        "region_expansion": "region_expansion",
        "object_count_growth": "region_expansion",
        "identity_preservation_under_growth": "identity_continuity",
        "structural_copying": "structural_replication",
        "identity_split_reasoning": "lineage_continuity",
    }

    CONCEPT_BINDINGS = {
        "shape_preservation": {
            "mechanisms": {
                "shape_equivalence",
                "structural_replication",
                "source_pattern_preservation",
            },
            "relation": "preserves_shape",
            "invalidators": {"shape_transform", "shape_change"},
        },
        "color_preservation": {
            "mechanisms": {
                "color_mapping_rule",
                "no_color_reassignment",
            },
            "relation": "preserves_color_semantics",
            "invalidators": {"changes_color_without_mapping"},
        },
        "position_preservation": {
            "mechanisms": {
                "stable_reference_frame",
                "coordinate_stability",
            },
            "relation": "preserves_position",
            "invalidators": {"spatial_translation"},
        },
        "symmetry_preservation": {
            "mechanisms": {
                "mirror_consistency",
                "axis_reflection",
            },
            "relation": "preserves_symmetry",
            "invalidators": {"symmetry_break"},
        },
        "symmetry_reasoning": {
            "mechanisms": {
                "mirror_consistency",
                "axis_reflection",
                "symmetry_reasoning",
            },
            "relation": "supports_symmetry_reasoning",
            "invalidators": {"symmetry_break"},
        },
        "topology_preservation": {
            "mechanisms": {
                "topology_continuity",
                "connectivity_continuity",
            },
            "relation": "preserves_topology",
            "invalidators": {"topology_break"},
        },
        "identity_persistence": {
            "mechanisms": {
                "identity_continuity",
                "lineage_continuity",
                "role_continuity",
            },
            "relation": "preserves_object_identity",
            "invalidators": {"identity_split"},
        },
        "identity_preservation": {
            "mechanisms": {
                "identity_continuity",
                "lineage_continuity",
                "role_continuity",
            },
            "relation": "preserves_identity",
            "invalidators": {"identity_split"},
        },
        "identity_forking": {
            "mechanisms": {
                "identity_forking",
                "identity_split",
                "lineage_continuity",
            },
            "relation": "creates_forked_identity",
            "invalidators": {"identity_preserved_without_new_instance"},
        },
        "growth": {
            "mechanisms": {
                "source_pattern_preservation",
                "topology_expansion",
                "region_expansion",
            },
            "relation": "supports_growth_truth",
            "invalidators": {"source_pattern_lost", "topology_contracts"},
        },
        "propagation": {
            "mechanisms": {
                "source_pattern_preservation",
                "recursive_spread",
                "pattern_extension",
            },
            "relation": "supports_propagation_truth",
            "invalidators": {"source_pattern_lost", "spread_discontinuous"},
        },
        "replication": {
            "mechanisms": {
                "structural_replication",
                "object_instance_creation",
                "shape_equivalence",
            },
            "relation": "supports_replication_truth",
            "invalidators": {"shape_transform", "identity_loss"},
        },
        "topological_growth": {
            "mechanisms": {
                "source_pattern_preservation",
                "topology_expansion",
                "region_expansion",
                "topology_split_reasoning",
            },
            "relation": "supports_topological_growth_truth",
            "invalidators": {"source_pattern_lost", "topology_contracts"},
        },
        "directional_motion": {
            "mechanisms": {
                "stable_reference_frame",
                "directional_transfer",
                "identity_continuity",
            },
            "relation": "supports_directional_motion_truth",
            "invalidators": {"position_reference_lost", "identity_loss"},
        },
    }

    def _semantic_signals(self, semantic_context_report=None):
        semantic_context_report = semantic_context_report or {}
        signals = set()
        for key in [
            "properties",
            "capabilities",
            "constraints",
            "implications",
        ]:
            for item in _as_list(semantic_context_report.get(key)):
                if isinstance(item, dict):
                    item = item.get(
                        "property_name",
                        item.get("name", item.get("capability")),
                    )
                signals.add(_normalize(item))
        return signals

    def _context_name(self, context_report=None):
        context_report = context_report or {}
        discovered = context_report.get("context_discovery", {})
        if isinstance(discovered, dict):
            context_report = {**context_report, **discovered}
        return _normalize(
            context_report.get(
                "transformation_family",
                context_report.get(
                    "context_name",
                    context_report.get("task_cluster"),
                ),
            )
        )

    def _mechanisms_for(
        self,
        context_name,
        context_report=None,
        semantic_context_report=None,
    ):
        context_report = context_report or {}
        signals = self._semantic_signals(semantic_context_report)
        mechanisms = set(self.FAMILY_MECHANISMS.get(context_name, []))
        mechanisms.update(
            mechanism
            for signal, mechanism in self.SIGNAL_MECHANISMS.items()
            if signal in signals
        )
        color_behavior = _normalize(
            context_report.get("color_behavior", context_report.get("color"))
        )
        identity_behavior = _normalize(
            context_report.get(
                "identity_behavior",
                context_report.get("identity"),
            )
        )
        topology_behavior = _normalize(
            context_report.get(
                "topology_behavior",
                context_report.get("topology"),
            )
        )
        if color_behavior in {"preserve", "unchanged", "same", "stable"}:
            mechanisms.add("no_color_reassignment")
        if identity_behavior in {
            "preserve",
            "identity_preserved",
            "unchanged",
            "stable",
        }:
            mechanisms.add("identity_continuity")
        if topology_behavior in {"preserve", "unchanged", "same", "stable"}:
            mechanisms.add("topology_continuity")
        return mechanisms

    def _hierarchy_score(self, context_hierarchy_report=None):
        report = context_hierarchy_report or {}
        if not isinstance(report, dict):
            return 0.5
        return clamp(report.get("context_hierarchy_score", 0.5))

    def _semantic_score(self, semantic_context_report=None):
        report = semantic_context_report or {}
        if not isinstance(report, dict):
            return 0.5
        return clamp(
            report.get(
                "semantic_context_score",
                report.get("confidence", 0.5),
            )
        )

    def bind(
        self,
        concept,
        context_report=None,
        semantic_context_report=None,
        context_hierarchy_report=None,
        contextual_truth_report=None,
        causal_validation_report=None,
    ):
        concept = _normalize(concept)
        context_report = context_report or {}
        semantic_context_report = semantic_context_report or {}
        contextual_truth_report = contextual_truth_report or {}
        causal_validation_report = causal_validation_report or {}
        context_name = self._context_name(context_report)
        mechanisms = self._mechanisms_for(
            context_name,
            context_report,
            semantic_context_report,
        )
        binding = self.CONCEPT_BINDINGS.get(concept, {
            "mechanisms": set(),
            "relation": f"supports_{concept}",
            "invalidators": set(),
        })
        supporting_mechanisms = sorted(
            mechanisms & set(binding["mechanisms"])
        )
        invalidators = sorted(
            mechanisms & set(binding.get("invalidators", set()))
        )
        semantic_score = self._semantic_score(semantic_context_report)
        hierarchy_score = self._hierarchy_score(context_hierarchy_report)
        contextual_truth_score = clamp(
            contextual_truth_report.get("contextual_truth_score", 0.5)
        )
        causal_score = clamp(
            causal_validation_report.get(
                "validation_score",
                causal_validation_report.get("causal_validation_score", 0.5),
            )
        )
        mechanism_coverage = clamp(
            len(supporting_mechanisms)
            / max(len(binding["mechanisms"]), 1)
        )
        contradiction_penalty = 0.25 if invalidators else 0.0
        binding_score = clamp(
            mechanism_coverage * 0.40
            + semantic_score * 0.20
            + hierarchy_score * 0.15
            + contextual_truth_score * 0.15
            + causal_score * 0.10
            - contradiction_penalty
        )
        why_valid = [
            " -> ".join([
                context_name,
                mechanism,
                binding["relation"],
                concept,
            ])
            for mechanism in supporting_mechanisms
        ]
        why_invalid = [
            " -> ".join([
                context_name,
                invalidator,
                "contradicts_context_binding",
                concept,
            ])
            for invalidator in invalidators
        ]
        return {
            "system": "context_binding_engine",
            "concept": concept,
            "context": context_name,
            "mechanisms": sorted(mechanisms),
            "supporting_mechanisms": supporting_mechanisms,
            "binding_chain": why_valid,
            "why_valid": why_valid,
            "why_invalid": why_invalid,
            "mechanism_coverage": mechanism_coverage,
            "semantic_context_score": semantic_score,
            "context_hierarchy_score": hierarchy_score,
            "contextual_truth_score": contextual_truth_score,
            "causal_validation_score": causal_score,
            "context_binding_score": binding_score,
            "binding_state": (
                "CONTEXT_BOUND"
                if binding_score >= 0.75 and why_valid
                else "BINDING_REVIEW_REQUIRED"
                if binding_score >= 0.55
                else "UNBOUND"
            ),
        }


__all__ = [
    "ContextBindingEngine",
]
