from dataclasses import dataclass, field

from core.epistemic_models import clamp
from core.process_abstraction import ProcessAbstractionLayer
from core.process_context_generation import ProcessContextGenerationEngine


def _normalize(value, default="unknown"):
    if value is None:
        return default
    return str(value).strip().lower().replace(" ", "_") or default


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _signature(context):
    if hasattr(context, "features"):
        return dict(getattr(context, "features") or {})
    if not isinstance(context, dict):
        return {}
    if isinstance(context.get("context_signature"), dict):
        return dict(context["context_signature"])
    if isinstance(context.get("signature"), dict):
        return dict(context["signature"])
    discovered = context.get("discovered_context", {})
    if isinstance(discovered, dict):
        features = discovered.get("features", {})
        if isinstance(features, dict):
            return dict(features)
    features = context.get("features", {})
    if isinstance(features, dict):
        return dict(features)
    return dict(context)


def _context_name(context):
    if isinstance(context, SemanticContext):
        return context.context_name
    if hasattr(context, "context_name"):
        return _normalize(getattr(context, "context_name"))
    if isinstance(context, str):
        return _normalize(context)
    if isinstance(context, dict):
        signature = _signature(context)
        return _normalize(
            context.get(
                "context_name",
                context.get(
                    "transformation_family",
                    signature.get("transformation_family"),
                ),
            )
        )
    return "unknown"


def _confidence(context, default=0.0):
    if isinstance(context, SemanticContext):
        return context.confidence
    if hasattr(context, "confidence"):
        return clamp(getattr(context, "confidence"))
    if isinstance(context, dict):
        signature = _signature(context)
        return clamp(context.get("confidence", signature.get(
            "confidence",
            default,
        )))
    return clamp(default)


@dataclass
class ContextProperty:
    property_name: str
    confidence: float = 0.0
    evidence_count: int = 0

    def __post_init__(self):
        self.property_name = _normalize(self.property_name)
        self.confidence = clamp(self.confidence)
        self.evidence_count = int(self.evidence_count or 0)

    def as_dict(self):
        return {
            "property_name": self.property_name,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
        }


@dataclass
class SemanticContext:
    context_name: str
    semantic_definition: str = ""
    capabilities: list = field(default_factory=list)
    constraints: list = field(default_factory=list)
    implications: list = field(default_factory=list)
    confidence: float = 0.0
    supporting_evidence: list = field(default_factory=list)
    properties: list = field(default_factory=list)

    def __post_init__(self):
        self.context_name = _normalize(self.context_name)
        self.confidence = clamp(self.confidence)
        self.capabilities = sorted({
            _normalize(item)
            for item in self.capabilities
        })
        self.constraints = sorted({
            _normalize(item)
            for item in self.constraints
        })
        self.implications = sorted({
            _normalize(item)
            for item in self.implications
        })
        self.properties = [
            item
            if isinstance(item, ContextProperty)
            else ContextProperty(**item)
            if isinstance(item, dict)
            else ContextProperty(item)
            for item in self.properties
        ]

    def describe(self):
        return {
            "context": self.context_name,
            "definition": self.semantic_definition,
            "properties": [
                item.as_dict()
                for item in self.properties
            ],
            "capabilities": list(self.capabilities),
            "constraints": list(self.constraints),
            "implications": list(self.implications),
            "confidence": self.confidence,
        }

    def explain(self):
        return {
            "what_is_this_context": self.semantic_definition,
            "what_does_it_do": list(self.capabilities),
            "what_properties_define_it": [
                item.property_name
                for item in self.properties
            ],
            "what_limits_does_it_have": list(self.constraints),
            "what_consequences_follow": list(self.implications),
            "why_it_exists": list(self.supporting_evidence),
        }

    def infer_implications(self):
        return list(self.implications)

    def as_dict(self):
        return {
            "context_name": self.context_name,
            "semantic_definition": self.semantic_definition,
            "properties": [
                item.as_dict()
                for item in self.properties
            ],
            "capabilities": list(self.capabilities),
            "constraints": list(self.constraints),
            "implications": list(self.implications),
            "confidence": self.confidence,
            "supporting_evidence": list(self.supporting_evidence),
            "explanation": self.explain(),
        }


class SemanticContextReasoner:
    PROCESS_ABSTRACTIONS = ProcessContextGenerationEngine.semantic_contexts()
    PRESERVATION_CONTEXTS = {
        "color_context",
        "shape_context",
        "topology_context",
        "position_context",
        "symmetry_context",
        "identity_preservation",
        "identity_persistence",
    }
    PROCESS_TRAIT_PROPERTIES = {
        "creates_objects",
        "modifies_topology",
        "expands_objects",
        "modifies_identity",
        "removes_objects",
    }
    PROCESS_TRAIT_CAPABILITIES = {
        "object_creation",
        "structural_replication",
        "identity_split_reasoning",
        "topology_growth",
    }
    PROCESS_TRAIT_CONSTRAINTS = {
        "object_count_changes",
        "identity_continuity_may_split",
        "identity_continuity_may_change",
    }
    PROCESS_TRAIT_IMPLICATIONS = {
        "object_count_increase",
        "object_count_decrease",
        "identity_split_expected",
        "topology_modification_possible",
    }
    TRUTH_NATIVE_CONTEXTS = {
        "shape_context": {
            "properties": [
                "shape_stability",
                "local_shape_preservation",
                "boundary_geometry_preservation",
            ],
            "capabilities": [
                "shape_preservation_reasoning",
                "local_geometry_tracking",
                "boundary_consistency_check",
            ],
            "constraints": [
                "requires_shape_observation",
                "invalid_under_untracked_shape_transform",
            ],
            "implications": [
                "shape_preservation_expected",
                "local_shape_preservation_expected",
            ],
        },
        "topology_context": {
            "properties": [
                "topology_stability",
                "connectivity_preservation",
                "region_relation_preservation",
            ],
            "capabilities": [
                "topology_preservation_reasoning",
                "connectivity_tracking",
                "region_relation_check",
            ],
            "constraints": [
                "requires_topology_observation",
                "invalid_under_untracked_topology_transform",
            ],
            "implications": [
                "topology_preservation_expected",
                "connectivity_preservation_expected",
            ],
        },
        "position_context": {
            "properties": [
                "position_stability",
                "coordinate_anchor_preservation",
                "relative_position_preservation",
            ],
            "capabilities": [
                "position_preservation_reasoning",
                "coordinate_anchor_tracking",
                "relative_position_check",
            ],
            "constraints": [
                "requires_position_observation",
                "invalid_under_untracked_translation",
            ],
            "implications": [
                "position_preservation_expected",
                "coordinate_anchor_preservation_expected",
            ],
        },
        "color_context": {
            "properties": [
                "color_stability",
                "attribute_mapping_preservation",
                "no_color_reassignment",
            ],
            "capabilities": [
                "color_preservation_reasoning",
                "attribute_mapping",
                "contextual_color_stability",
            ],
            "constraints": [
                "requires_color_observation",
                "invalid_under_unmapped_recoloring",
            ],
            "implications": [
                "color_preservation_expected",
                "attribute_mapping_preservation_expected",
            ],
        },
        "symmetry_context": {
            "properties": [
                "symmetry_relation",
                "axis_consistency",
                "mirror_consistency",
            ],
            "capabilities": [
                "symmetry_reasoning",
                "mirror_consistency_check",
                "axis_based_generalization",
            ],
            "constraints": [
                "requires_symmetry_evidence",
                "requires_axis_or_pair_relation",
            ],
            "implications": [
                "symmetry_preservation_expected",
                "mirror_consistency_expected",
            ],
        },
        "identity_persistence": {
            "properties": [
                "identity_persistence",
                "object_persistence",
                "identity_continuity",
            ],
            "capabilities": [
                "identity_persistence_reasoning",
                "object_lineage_tracking",
                "attribute_change_tolerance",
            ],
            "constraints": [
                "requires_identity_anchor",
                "identity_split_absent",
                "topology_splitting_absent",
            ],
            "implications": [
                "identity_preserved",
                "identity_split_false",
                "topology_splitting_false",
            ],
        },
        "identity_forking": {
            "properties": [
                "identity_forking",
                "identity_split",
                "object_count_increase",
                "topology_splitting",
            ],
            "capabilities": [
                "identity_forking_reasoning",
                "source_lineage_tracking",
                "new_identity_derivation",
            ],
            "constraints": [
                "requires_source_identity",
                "requires_new_identity_instance",
                "preserves_identity_false",
            ],
            "implications": [
                "identity_split_expected",
                "topology_splitting_expected",
                "object_count_increase_expected",
            ],
        },
    }
    PROCESS_NATIVE_CONTEXTS = {
        "growth": {
            "properties": [
                "topology_expansion",
                "object_count_growth",
                "identity_preservation_under_growth",
            ],
            "capabilities": [
                "region_expansion",
                "topology_growth",
                "identity_preserving_growth",
            ],
            "constraints": [
                "requires_identity_anchor",
                "requires_source_pattern",
            ],
            "implications": [
                "topology_expansion_expected",
                "object_count_or_area_growth_expected",
                "identity_continuity_under_growth_expected",
            ],
        },
        "topological_growth": {
            "properties": [
                "topology_expansion",
                "region_expansion",
                "topology_splitting",
                "identity_preservation_under_growth",
            ],
            "capabilities": [
                "region_expansion",
                "topology_growth",
                "topology_split_reasoning",
                "identity_preserving_growth",
            ],
            "constraints": [
                "requires_growth_dependency",
                "requires_shape_anchor",
            ],
            "implications": [
                "topology_expansion_expected",
                "growth_dependency_required",
            ],
        },
        "directional_motion": {
            "properties": [
                "position_delta",
                "directional_displacement",
                "source_pattern_motion",
            ],
            "capabilities": [
                "spatial_relocation",
                "directional_transfer",
                "source_pattern_preservation",
            ],
            "constraints": [
                "requires_position_reference",
                "requires_object_persistence",
            ],
            "implications": [
                "position_change_expected",
                "identity_continuity_expected",
            ],
        },
        "propagation": {
            "properties": [
                "directional_spread",
                "source_pattern_preservation",
                "signal_transfer",
            ],
            "capabilities": [
                "pattern_extension",
                "directional_transfer",
                "source_pattern_preservation",
            ],
            "constraints": [
                "requires_source_pattern",
                "requires_directional_path",
            ],
            "implications": [
                "directional_motion_expected",
                "source_pattern_preservation_expected",
            ],
        },
        "replication": {
            "properties": [
                "object_creation",
                "identity_split",
                "structural_copying",
            ],
            "capabilities": [
                "object_creation",
                "structural_replication",
                "identity_split_reasoning",
            ],
            "constraints": [
                "requires_source_object",
                "requires_shape_anchor",
            ],
            "implications": [
                "object_count_increase",
                "identity_split_expected",
                "structural_copy_expected",
            ],
        },
    }
    DEFINITIONS = {
        "duplication": (
            "Creates one or more additional object instances while partially "
            "preserving structural characteristics."
        ),
        "replication": (
            "Reproduces an existing structure into an additional instance."
        ),
        "reflection": (
            "Inverts spatial arrangement across an axis while preserving "
            "recognizable structure."
        ),
        "translation": (
            "Moves objects through space while preserving their internal "
            "structure."
        ),
        "rotation": (
            "Changes orientation around a center while preserving object "
            "structure."
        ),
        "recoloring": (
            "Alters color mapping while preserving spatial and topological "
            "structure."
        ),
        "symbolic_remapping": (
            "Changes symbolic attributes while preserving the role of the "
            "underlying object or pattern."
        ),
        "color_context": (
            "Evaluates whether color or attribute mappings remain stable "
            "inside a task context."
        ),
        "shape_context": (
            "Evaluates whether local shape and boundary geometry remain "
            "stable inside a task context."
        ),
        "topology_context": (
            "Evaluates whether connectivity and region relations remain "
            "stable inside a task context."
        ),
        "position_context": (
            "Evaluates whether absolute and relative position anchors remain "
            "stable inside a task context."
        ),
        "symmetry_context": (
            "Evaluates axis, mirror, and relational symmetry evidence inside "
            "a task context."
        ),
        "propagation": (
            "Transfers a source pattern through directional spread while "
            "preserving the pattern's causal lineage."
        ),
        "growth": (
            "Expands object count, occupied region, or topology while "
            "maintaining identity anchors under growth."
        ),
        "topological_growth": (
            "Expands occupied topology through growth dependencies while "
            "preserving shape and identity anchors."
        ),
        "directional_motion": (
            "Changes object position along a direction while preserving "
            "identity and a source pattern reference."
        ),
        "deletion": "Removes objects or structure from the scene.",
        "insertion": "Introduces new objects or structure into the scene.",
        "identity_preservation": (
            "Maintains object identity across observed transformations."
        ),
    }
    BASE_PROPERTIES = {
        "duplication": [
            "creates_objects",
            "preserves_shape",
            "modifies_topology",
        ],
        "replication": ["creates_objects", "preserves_shape"],
        "reflection": [
            "preserves_shape",
            "preserves_symmetry",
            "spatial_inversion",
        ],
        "translation": [
            "preserves_shape",
            "preserves_identity",
            "changes_position",
        ],
        "rotation": [
            "preserves_shape",
            "preserves_identity",
            "changes_orientation",
        ],
        "recoloring": [
            "changes_color",
            "preserves_shape",
            "preserves_topology",
        ],
        "symbolic_remapping": [
            "changes_color",
            "preserves_topology",
            "modifies_symbolic_attributes",
        ],
        "color_context": [
            "color_stability",
            "attribute_mapping_preservation",
            "no_color_reassignment",
        ],
        "shape_context": [
            "shape_stability",
            "local_shape_preservation",
            "boundary_geometry_preservation",
        ],
        "topology_context": [
            "topology_stability",
            "connectivity_preservation",
            "region_relation_preservation",
        ],
        "position_context": [
            "position_stability",
            "coordinate_anchor_preservation",
            "relative_position_preservation",
        ],
        "symmetry_context": [
            "symmetry_relation",
            "axis_consistency",
            "mirror_consistency",
        ],
        "propagation": [
            "propagates_structure",
            "expands_objects",
            "modifies_topology",
            "source_pattern_preserved",
            "directional_spread",
            "signal_transfer",
        ],
        "growth": [
            "expands_objects",
            "modifies_topology",
            "source_pattern_preserved",
            "topology_expansion",
            "object_count_growth",
            "identity_preservation_under_growth",
        ],
        "topological_growth": [
            "expands_objects",
            "modifies_topology",
            "source_pattern_preserved",
            "topology_expansion",
            "region_expansion",
            "topology_splitting",
            "identity_preservation_under_growth",
        ],
        "directional_motion": [
            "position_delta",
            "directional_displacement",
            "source_pattern_motion",
            "preserves_identity",
        ],
        "deletion": ["removes_objects", "modifies_topology"],
        "insertion": ["creates_objects", "modifies_topology"],
        "identity_preservation": [
            "preserves_identity",
            "preserves_shape",
        ],
    }
    CAPABILITIES = {
        "duplication": ["object_creation", "structural_replication"],
        "replication": [
            "object_creation",
            "structural_replication",
            "identity_split_reasoning",
        ],
        "reflection": ["symmetry_generation", "spatial_inversion"],
        "translation": ["spatial_relocation", "structure_preservation"],
        "rotation": ["orientation_change", "structure_preservation"],
        "recoloring": ["attribute_remapping", "color_transformation"],
        "symbolic_remapping": [
            "attribute_remapping",
            "symbolic_role_transfer",
        ],
        "color_context": [
            "color_preservation_reasoning",
            "attribute_mapping",
            "contextual_color_stability",
        ],
        "shape_context": [
            "shape_preservation_reasoning",
            "local_geometry_tracking",
            "boundary_consistency_check",
        ],
        "topology_context": [
            "topology_preservation_reasoning",
            "connectivity_tracking",
            "region_relation_check",
        ],
        "position_context": [
            "position_preservation_reasoning",
            "coordinate_anchor_tracking",
            "relative_position_check",
        ],
        "symmetry_context": [
            "symmetry_reasoning",
            "mirror_consistency_check",
            "axis_based_generalization",
        ],
        "propagation": [
            "pattern_extension",
            "topology_growth",
            "directional_transfer",
            "source_pattern_preservation",
        ],
        "growth": [
            "region_expansion",
            "topology_growth",
            "identity_preserving_growth",
        ],
        "topological_growth": [
            "region_expansion",
            "topology_growth",
            "source_pattern_preservation",
            "topology_split_reasoning",
        ],
        "directional_motion": [
            "spatial_relocation",
            "directional_transfer",
            "source_pattern_preservation",
        ],
        "deletion": ["object_removal"],
        "insertion": ["object_creation"],
        "identity_preservation": ["identity_tracking"],
    }
    CONSTRAINTS = {
        "duplication": [
            "object_count_cannot_remain_constant",
            "identity_continuity_may_split",
        ],
        "replication": ["object_count_changes"],
        "reflection": ["requires_spatial_axis"],
        "translation": ["relative_shape_must_remain_stable"],
        "rotation": ["requires_orientation_reference"],
        "recoloring": ["color_cannot_be_preserved", "color_mapping_changes"],
        "symbolic_remapping": ["symbolic_value_changes"],
        "color_context": [
            "requires_color_observation",
            "invalid_under_unmapped_recoloring",
        ],
        "shape_context": [
            "requires_shape_observation",
            "invalid_under_untracked_shape_transform",
        ],
        "topology_context": [
            "requires_topology_observation",
            "invalid_under_untracked_topology_transform",
        ],
        "position_context": [
            "requires_position_observation",
            "invalid_under_untracked_translation",
        ],
        "symmetry_context": [
            "requires_symmetry_evidence",
            "requires_axis_or_pair_relation",
        ],
        "propagation": ["requires_source_pattern"],
        "growth": ["occupied_area_changes"],
        "topological_growth": [
            "occupied_area_changes",
            "topology_must_expand",
        ],
        "directional_motion": [
            "requires_position_reference",
            "requires_object_persistence",
        ],
        "deletion": ["object_count_decreases"],
        "insertion": ["object_count_increases"],
        "identity_preservation": ["identity_must_remain_traceable"],
    }
    IMPLICATIONS = {
        "duplication": [
            "object_count_increase",
            "replication_behavior",
            "topology_change_possible",
        ],
        "replication": ["object_count_increase", "replication_behavior"],
        "reflection": ["symmetry_preservation", "spatial_inversion_expected"],
        "translation": ["position_change", "shape_preservation_expected"],
        "rotation": ["orientation_change", "shape_preservation_expected"],
        "recoloring": ["color_change", "identity_may_be_modified"],
        "symbolic_remapping": ["attribute_change", "role_preservation"],
        "color_context": [
            "color_preservation_expected",
            "attribute_mapping_preservation_expected",
        ],
        "shape_context": [
            "shape_preservation_expected",
            "local_shape_preservation_expected",
        ],
        "topology_context": [
            "topology_preservation_expected",
            "connectivity_preservation_expected",
        ],
        "position_context": [
            "position_preservation_expected",
            "coordinate_anchor_preservation_expected",
        ],
        "symmetry_context": [
            "symmetry_preservation_expected",
            "mirror_consistency_expected",
        ],
        "propagation": ["pattern_extension", "topology_growth_possible"],
        "growth": ["object_expansion", "topology_growth_possible"],
        "topological_growth": [
            "object_expansion",
            "topology_growth_possible",
        ],
        "directional_motion": [
            "position_change",
            "identity_continuity_expected",
        ],
        "deletion": ["object_count_decrease"],
        "insertion": ["object_count_increase"],
        "identity_preservation": ["identity_continuity_expected"],
    }
    SEMANTIC_ALIASES = {
        ("duplication", "replication"): 0.82,
    }

    def __init__(self):
        self.profiles = {}
        self.property_confidence_history = {}

    def _property(self, property_name, confidence, evidence_count):
        return ContextProperty(property_name, confidence, evidence_count)

    def _is_preservation_context(self, context_name):
        return _normalize(context_name) in self.PRESERVATION_CONTEXTS

    def _process_traits(self, context=None):
        signature = _signature(context)
        process_operator = _normalize(signature.get("process_operator", ""))
        if not process_operator:
            return {
                "process_operator": "unknown",
                "properties": [],
                "capabilities": [],
                "constraints": [],
                "implications": [],
                "stored_separately": True,
            }
        return {
            "process_operator": process_operator,
            "properties": list(self.BASE_PROPERTIES.get(process_operator, [])),
            "capabilities": list(self.CAPABILITIES.get(process_operator, [])),
            "constraints": list(self.CONSTRAINTS.get(process_operator, [])),
            "implications": list(self.IMPLICATIONS.get(process_operator, [])),
            "stored_separately": True,
        }

    def _purify_preservation_profile(
        self,
        context_name,
        properties,
        capabilities,
        constraints,
        implications,
    ):
        if not self._is_preservation_context(context_name):
            return properties, capabilities, constraints, implications

        properties = [
            item
            for item in properties
            if item.property_name not in self.PROCESS_TRAIT_PROPERTIES
        ]
        capabilities = sorted(
            set(capabilities) - self.PROCESS_TRAIT_CAPABILITIES
        )
        constraints = sorted(
            set(constraints) - self.PROCESS_TRAIT_CONSTRAINTS
        )
        implications = sorted(
            set(implications) - self.PROCESS_TRAIT_IMPLICATIONS
        )
        return properties, capabilities, constraints, implications

    def infer_properties(self, context=None, evidence=None):
        context_name = _context_name(context)
        signature = _signature(context)
        process_operator = _normalize(signature.get("process_operator", ""))
        evidence = list(evidence or [])
        evidence_count = max(len(evidence), 1)
        properties = {
            name: self._property(name, _confidence(context, 0.70), evidence_count)
            for name in self.BASE_PROPERTIES.get(context_name, [])
        }
        if not self._is_preservation_context(context_name):
            for name in self.BASE_PROPERTIES.get(process_operator, []):
                properties[name] = self._property(
                    name,
                    _confidence(context, 0.70),
                    evidence_count,
                )
        process_context = {
            **self.PROCESS_NATIVE_CONTEXTS.get(context_name, {}),
            **self.PROCESS_ABSTRACTIONS.get(context_name, {}),
        }
        truth_context = self.TRUTH_NATIVE_CONTEXTS.get(context_name, {})
        process_native_contexts = set(
            _normalize(item)
            for item in _as_list(signature.get("process_native_contexts"))
        )
        process_native_contexts.update(process_context.get("properties", []))
        process_native_contexts.update(
            _normalize(item)
            for item in _as_list(signature.get("truth_native_contexts"))
        )
        process_native_contexts.update(truth_context.get("properties", []))
        process_native_contexts.update(
            _normalize(item)
            for item in _as_list(signature.get("native_contexts"))
        )
        if signature.get("process_context_surface") not in {None, "none"}:
            process_native_contexts.add(
                _normalize(signature["process_context_surface"])
            )
        for name in process_native_contexts:
            properties[name] = self._property(
                name,
                max(_confidence(context, 0.70), 0.88),
                evidence_count,
            )
        preservation_context = self._is_preservation_context(context_name)
        if (
            not preservation_context
            and signature.get("object_dynamics") == "object_created"
        ):
            properties["creates_objects"] = self._property(
                "creates_objects",
                0.90,
                evidence_count,
            )
        if (
            not preservation_context
            and signature.get("object_dynamics") == "object_removed"
        ):
            properties["removes_objects"] = self._property(
                "removes_objects",
                0.90,
                evidence_count,
            )
        if (
            not preservation_context
            and signature.get("topology_behavior") in [
            "topology_splitting",
            "topology_merging",
            "topology_expanding",
            "topology_restructured",
            ]
        ):
            properties["modifies_topology"] = self._property(
                "modifies_topology",
                0.86,
                evidence_count,
            )
        if signature.get("topology_behavior") == "topology_preserved":
            properties["preserves_topology"] = self._property(
                "preserves_topology",
                0.86,
                evidence_count,
            )
        if signature.get("color_behavior") in [
            "color_changed",
            "color_mapped",
            "color_reassigned",
            "color_expanding",
        ]:
            properties["changes_color"] = self._property(
                "changes_color",
                0.86,
                evidence_count,
            )
        if signature.get("color_behavior") == "color_preserved":
            properties["preserves_color"] = self._property(
                "preserves_color",
                0.86,
                evidence_count,
            )
        if signature.get("identity_behavior") == "identity_preserved":
            properties["preserves_identity"] = self._property(
                "preserves_identity",
                0.86,
                evidence_count,
            )
        if (
            not preservation_context
            and signature.get("identity_behavior") in [
            "identity_split",
            "identity_merged",
            ]
        ):
            properties["modifies_identity"] = self._property(
                "modifies_identity",
                0.82,
                evidence_count,
            )
        if (
            not preservation_context
            and signature.get("size_behavior") == "size_expanded"
        ):
            properties["expands_objects"] = self._property(
                "expands_objects",
                0.84,
                evidence_count,
            )
        if signature.get("symmetry_behavior") in [
            "symmetry_preserved",
            "preserved",
            "retained",
        ]:
            properties["preserves_symmetry"] = self._property(
                "preserves_symmetry",
                0.84,
                evidence_count,
            )
        result = sorted(properties.values(), key=lambda item: item.property_name)
        self.property_confidence_history.setdefault(context_name, []).append([
            item.as_dict()
            for item in result
        ])
        return result

    def infer_capabilities(self, context=None, properties=None):
        context_name = _context_name(context)
        process_operator = _normalize(_signature(context).get(
            "process_operator",
            "",
        ))
        capabilities = set(self.CAPABILITIES.get(context_name, []))
        if not self._is_preservation_context(context_name):
            capabilities.update(self.CAPABILITIES.get(process_operator, []))
        capabilities.update(
            self.PROCESS_NATIVE_CONTEXTS.get(context_name, {}).get(
                "capabilities",
                [],
            )
        )
        capabilities.update(
            self.PROCESS_ABSTRACTIONS.get(context_name, {}).get(
                "capabilities",
                [],
            )
        )
        capabilities.update(
            self.TRUTH_NATIVE_CONTEXTS.get(context_name, {}).get(
                "capabilities",
                [],
            )
        )
        property_names = {
            item.property_name if isinstance(item, ContextProperty) else str(item)
            for item in list(properties or [])
        }
        if "creates_objects" in property_names:
            capabilities.add("object_creation")
        if "preserves_shape" in property_names:
            capabilities.add("structure_preservation")
        if "propagates_structure" in property_names:
            capabilities.add("pattern_extension")
        if "directional_spread" in property_names:
            capabilities.add("directional_transfer")
        if "directional_displacement" in property_names:
            capabilities.add("directional_transfer")
        if "position_delta" in property_names:
            capabilities.add("spatial_relocation")
        if "source_pattern_preservation" in property_names:
            capabilities.add("source_pattern_preservation")
        if "structural_copying" in property_names:
            capabilities.add("structural_replication")
        if "topology_expansion" in property_names:
            capabilities.add("topology_growth")
        if "changes_color" in property_names:
            capabilities.add("attribute_remapping")
        if "color_stability" in property_names:
            capabilities.add("color_preservation_reasoning")
        if "mirror_consistency" in property_names:
            capabilities.add("mirror_consistency_check")
        return sorted(capabilities)

    def infer_constraints(self, context=None, properties=None):
        context_name = _context_name(context)
        process_operator = _normalize(_signature(context).get(
            "process_operator",
            "",
        ))
        constraints = set(self.CONSTRAINTS.get(context_name, []))
        if not self._is_preservation_context(context_name):
            constraints.update(self.CONSTRAINTS.get(process_operator, []))
        constraints.update(
            self.PROCESS_NATIVE_CONTEXTS.get(context_name, {}).get(
                "constraints",
                [],
            )
        )
        constraints.update(
            self.PROCESS_ABSTRACTIONS.get(context_name, {}).get(
                "constraints",
                [],
            )
        )
        constraints.update(
            self.TRUTH_NATIVE_CONTEXTS.get(context_name, {}).get(
                "constraints",
                [],
            )
        )
        property_names = {
            item.property_name if isinstance(item, ContextProperty) else str(item)
            for item in list(properties or [])
        }
        if "creates_objects" in property_names:
            constraints.add("object_count_changes")
        if "changes_color" in property_names:
            constraints.add("color_mapping_changes")
        if "modifies_identity" in property_names:
            constraints.add("identity_continuity_may_change")
        return sorted(constraints)

    def infer_implications(self, context=None, properties=None):
        context_name = _context_name(context)
        process_operator = _normalize(_signature(context).get(
            "process_operator",
            "",
        ))
        implications = set(self.IMPLICATIONS.get(context_name, []))
        if not self._is_preservation_context(context_name):
            implications.update(self.IMPLICATIONS.get(process_operator, []))
        implications.update(
            self.PROCESS_NATIVE_CONTEXTS.get(context_name, {}).get(
                "implications",
                [],
            )
        )
        implications.update(
            self.PROCESS_ABSTRACTIONS.get(context_name, {}).get(
                "implications",
                [],
            )
        )
        implications.update(
            self.TRUTH_NATIVE_CONTEXTS.get(context_name, {}).get(
                "implications",
                [],
            )
        )
        property_names = {
            item.property_name if isinstance(item, ContextProperty) else str(item)
            for item in list(properties or [])
        }
        if "creates_objects" in property_names:
            implications.add("object_count_increase")
        if "changes_color" in property_names:
            implications.add("color_change")
        if "preserves_shape" in property_names:
            implications.add("shape_preservation_expected")
        if "modifies_topology" in property_names:
            implications.add("topology_modification_possible")
        if "topology_expansion" in property_names:
            implications.add("topology_expansion_expected")
        if "directional_spread" in property_names:
            implications.add("directional_motion_expected")
        if "directional_displacement" in property_names:
            implications.add("position_change_expected")
        if "structural_copying" in property_names:
            implications.add("structural_copy_expected")
        return sorted(implications)

    def generate_semantic_definition(self, context=None, properties=None):
        context_name = _context_name(context)
        abstraction = self.PROCESS_ABSTRACTIONS.get(context_name, {})
        if abstraction.get("definition"):
            return abstraction["definition"]
        if context_name in self.DEFINITIONS:
            return self.DEFINITIONS[context_name]
        property_names = [
            item.property_name if isinstance(item, ContextProperty) else str(item)
            for item in list(properties or [])
        ]
        if property_names:
            return (
                f"Context characterized by {', '.join(sorted(property_names))}."
            )
        return "Insufficient evidence to assign stable semantic meaning."

    def generate_semantic_profile(self, context=None, evidence=None):
        context_name = _context_name(context)
        process_context_report = ProcessContextGenerationEngine().generate_context(
            context_name,
        )
        properties = self.infer_properties(context, evidence)
        capabilities = self.infer_capabilities(context, properties)
        constraints = self.infer_constraints(context, properties)
        implications = self.infer_implications(context, properties)
        properties, capabilities, constraints, implications = (
            self._purify_preservation_profile(
                context_name,
                properties,
                capabilities,
                constraints,
                implications,
            )
        )
        definition = self.generate_semantic_definition(context, properties)
        confidence = clamp(
            (
                _confidence(context, 0.0)
                + sum(item.confidence for item in properties)
                / max(len(properties), 1)
                + (1.0 if capabilities else 0.0)
                + (1.0 if implications else 0.0)
            )
            / 4.0
        )
        semantic_required = context_name != "unknown" or confidence >= 0.50
        semantic_context = SemanticContext(
            context_name=context_name,
            semantic_definition=definition,
            capabilities=capabilities,
            constraints=constraints,
            implications=implications,
            confidence=confidence,
            supporting_evidence=[
                f"context classified as {context_name}",
                *[
                    str(item)
                    for item in _as_list(_signature(context).get(
                        "classification_reasons",
                    ))
                ],
            ],
            properties=properties,
        )
        profile = {
            "system": "semantic_context_reasoner",
            "phase": "5.7",
            "context": context_name,
            "semantic_profile": semantic_context.as_dict(),
            "properties": [
                item.as_dict()
                for item in properties
            ],
            "capabilities": capabilities,
            "constraints": constraints,
            "implications": implications,
            "process_traits": self._process_traits(context),
            "process_traits_stored_separately": True,
            "preservation_context": self._is_preservation_context(
                context_name,
            ),
            "preservation_context_pure": (
                not self._is_preservation_context(context_name)
                or (
                    not (
                        {
                            item.property_name
                            for item in properties
                        }
                        & self.PROCESS_TRAIT_PROPERTIES
                    )
                    and not (
                        set(capabilities)
                        & self.PROCESS_TRAIT_CAPABILITIES
                    )
                    and not (
                        set(constraints)
                        & self.PROCESS_TRAIT_CONSTRAINTS
                    )
                )
            ),
            "transfer_conditions": self.PROCESS_ABSTRACTIONS.get(
                context_name,
                {},
            ).get("transfer_conditions", []),
            "validation_criteria": self.PROCESS_ABSTRACTIONS.get(
                context_name,
                {},
            ).get("validation_criteria", []),
            "process_abstraction": (
                ProcessAbstractionLayer.get(context_name).as_dict()
                if ProcessAbstractionLayer.get(context_name)
                else {}
            ),
            "process_abstraction_ready": bool(
                ProcessAbstractionLayer.get(context_name)
            ),
            "process_context_generation": process_context_report,
            "process_context_generated": bool(
                process_context_report.get("process_context_generated")
            ),
            "semantic_definition": definition,
            "confidence": confidence,
            "semantic_context_score": confidence,
            "semantic_required": semantic_required,
            "semantically_validated": (not semantic_required) or confidence >= 0.75,
            "status": (
                "SEMANTICALLY_VALIDATED"
                if (not semantic_required) or confidence >= 0.75
                else "SEMANTIC_REVIEW_REQUIRED"
            ),
            "property_confidence_history":
            self.property_confidence_history.get(context_name, []),
            "explainability": semantic_context.explain(),
        }
        self.profiles[context_name] = profile
        return profile

    def semantic_context_similarity(self, first, second):
        first_name = _context_name(first)
        second_name = _context_name(second)
        if first_name == second_name:
            return 1.0
        alias_pair = tuple(sorted([first_name, second_name]))
        for pair, similarity in self.SEMANTIC_ALIASES.items():
            if tuple(sorted(pair)) == alias_pair:
                return similarity
        first_profile = (
            first
            if isinstance(first, dict)
            and first.get("semantic_profile")
            else self.generate_semantic_profile(first)
        )
        second_profile = (
            second
            if isinstance(second, dict)
            and second.get("semantic_profile")
            else self.generate_semantic_profile(second)
        )
        first_semantics = first_profile.get(
            "semantic_profile",
            {},
        )
        second_semantics = second_profile.get(
            "semantic_profile",
            {},
        )
        first_terms = set(first_semantics.get("capabilities", []))
        first_terms.update(first_semantics.get("constraints", []))
        first_terms.update(first_semantics.get("implications", []))
        first_terms.update(
            item.get("property_name")
            for item in first_semantics.get("properties", [])
            if isinstance(item, dict)
        )
        second_terms = set(second_semantics.get("capabilities", []))
        second_terms.update(second_semantics.get("constraints", []))
        second_terms.update(second_semantics.get("implications", []))
        second_terms.update(
            item.get("property_name")
            for item in second_semantics.get("properties", [])
            if isinstance(item, dict)
        )
        if not first_terms and not second_terms:
            return 1.0
        return clamp(
            len(first_terms & second_terms)
            / max(len(first_terms | second_terms), 1)
        )

    def explain_context(self, context=None):
        profile = self.generate_semantic_profile(context)
        return {
            "system": "semantic_context_explanation_engine",
            "context": profile["context"],
            "what_is_this_context": profile["semantic_definition"],
            "what_does_it_mean": profile["semantic_definition"],
            "why_does_it_exist":
            profile["semantic_profile"]["supporting_evidence"],
            "what_can_it_do": profile["capabilities"],
            "what_limits_does_it_have": profile["constraints"],
            "what_consequences_follow": profile["implications"],
            "properties": profile["properties"],
            "confidence": profile["confidence"],
            "status": profile["status"],
        }

    def report(self):
        return {
            "system": "semantic_context_reasoner",
            "phase": "5.7",
            "profiles": list(self.profiles.values()),
            "property_confidence_history":
            dict(self.property_confidence_history),
        }


def generate_semantic_profile(context=None, evidence=None):
    return SemanticContextReasoner().generate_semantic_profile(
        context,
        evidence,
    )


def semantic_context_similarity(first, second):
    return SemanticContextReasoner().semantic_context_similarity(first, second)


def explain_context(context=None):
    return SemanticContextReasoner().explain_context(context)


__all__ = [
    "ContextProperty",
    "SemanticContext",
    "SemanticContextReasoner",
    "explain_context",
    "generate_semantic_profile",
    "semantic_context_similarity",
]
