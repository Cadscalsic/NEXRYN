from dataclasses import dataclass, field

from core.epistemic_models import clamp


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
        "propagation": (
            "Extends a pattern from a source through adjacent or repeated "
            "structure."
        ),
        "growth": (
            "Expands an object or occupied region while preserving a source "
            "pattern."
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
        "propagation": [
            "propagates_structure",
            "expands_objects",
            "modifies_topology",
        ],
        "growth": ["expands_objects", "modifies_topology"],
        "deletion": ["removes_objects", "modifies_topology"],
        "insertion": ["creates_objects", "modifies_topology"],
        "identity_preservation": [
            "preserves_identity",
            "preserves_shape",
        ],
    }
    CAPABILITIES = {
        "duplication": ["object_creation", "structural_replication"],
        "replication": ["object_creation", "structural_replication"],
        "reflection": ["symmetry_generation", "spatial_inversion"],
        "translation": ["spatial_relocation", "structure_preservation"],
        "rotation": ["orientation_change", "structure_preservation"],
        "recoloring": ["attribute_remapping", "color_transformation"],
        "symbolic_remapping": [
            "attribute_remapping",
            "symbolic_role_transfer",
        ],
        "propagation": ["pattern_extension", "topology_growth"],
        "growth": ["region_expansion", "topology_growth"],
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
        "propagation": ["requires_source_pattern"],
        "growth": ["occupied_area_changes"],
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
        "propagation": ["pattern_extension", "topology_growth_possible"],
        "growth": ["object_expansion", "topology_growth_possible"],
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

    def infer_properties(self, context=None, evidence=None):
        context_name = _context_name(context)
        signature = _signature(context)
        evidence = list(evidence or [])
        evidence_count = max(len(evidence), 1)
        properties = {
            name: self._property(name, _confidence(context, 0.70), evidence_count)
            for name in self.BASE_PROPERTIES.get(context_name, [])
        }
        if signature.get("object_dynamics") == "object_created":
            properties["creates_objects"] = self._property(
                "creates_objects",
                0.90,
                evidence_count,
            )
        if signature.get("object_dynamics") == "object_removed":
            properties["removes_objects"] = self._property(
                "removes_objects",
                0.90,
                evidence_count,
            )
        if signature.get("topology_behavior") in [
            "topology_splitting",
            "topology_merging",
            "topology_expanding",
            "topology_restructured",
        ]:
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
        if signature.get("identity_behavior") in [
            "identity_split",
            "identity_merged",
        ]:
            properties["modifies_identity"] = self._property(
                "modifies_identity",
                0.82,
                evidence_count,
            )
        if signature.get("size_behavior") == "size_expanded":
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
        capabilities = set(self.CAPABILITIES.get(context_name, []))
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
        if "changes_color" in property_names:
            capabilities.add("attribute_remapping")
        return sorted(capabilities)

    def infer_constraints(self, context=None, properties=None):
        context_name = _context_name(context)
        constraints = set(self.CONSTRAINTS.get(context_name, []))
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
        implications = set(self.IMPLICATIONS.get(context_name, []))
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
        return sorted(implications)

    def generate_semantic_definition(self, context=None, properties=None):
        context_name = _context_name(context)
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
        properties = self.infer_properties(context, evidence)
        capabilities = self.infer_capabilities(context, properties)
        constraints = self.infer_constraints(context, properties)
        implications = self.infer_implications(context, properties)
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
