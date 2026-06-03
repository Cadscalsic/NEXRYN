# ============================================
# NEXRYN SEMANTIC ONTOLOGY
# ============================================

from dataclasses import dataclass


# ============================================
# MULTI-RESOLUTION SEMANTIC COMPRESSION
# ============================================

@dataclass(frozen=True)
class SemanticCompressionLevel:

    local_identity: str

    structural_identity: str

    causal_identity: str

    archetypal_identity: str

    topology_signature: str = "none"


SEMANTIC_ONTOLOGY = {

    "duplicate_object": {
        "semantic_concept": "replication",
        "category": "object_causality",
        "causal_effect": "increase_object_count",
        "spatial_effect": "copy",
        "semantic_class": "multiplicative"
    },

    "expand_object": {
        "semantic_concept": "growth",
        "category": "object_causality",
        "causal_effect": "increase_area",
        "spatial_effect": "expand",
        "semantic_class": "additive"
    },

    "expand_pattern": {
        "semantic_concept": "propagation",
        "category": "spatial_causality",
        "causal_effect": "increase_density",
        "spatial_effect": "spread",
        "semantic_class": "diffusive"
    },

    "grow_topology": {
        "semantic_concept": "topological_growth",
        "category": "topology_causality",
        "causal_effect": "increase_connectivity",
        "spatial_effect": "extension",
        "semantic_class": "structural"
    },

    "replace_color": {
        "semantic_concept": "symbolic_remapping",
        "category": "attribute_causality",
        "causal_effect": "attribute_substitution",
        "spatial_effect": "surface_relabeling",
        "semantic_class": "symbolic"
    },

    "translate_right": {
        "semantic_concept": "directional_motion",
        "category": "spatial_causality",
        "causal_effect": "position_shift",
        "spatial_effect": "right_translation",
        "semantic_class": "kinematic"
    },

    "translate_left": {
        "semantic_concept": "directional_motion",
        "category": "spatial_causality",
        "causal_effect": "position_shift",
        "spatial_effect": "left_translation",
        "semantic_class": "kinematic"
    },

    "translate_up": {
        "semantic_concept": "directional_motion",
        "category": "spatial_causality",
        "causal_effect": "position_shift",
        "spatial_effect": "up_translation",
        "semantic_class": "kinematic"
    },

    "translate_down": {
        "semantic_concept": "directional_motion",
        "category": "spatial_causality",
        "causal_effect": "position_shift",
        "spatial_effect": "down_translation",
        "semantic_class": "kinematic"
    },

    "mirror_object": {
        "semantic_concept": "reflection",
        "category": "spatial_causality",
        "causal_effect": "orientation_flip",
        "spatial_effect": "mirror",
        "semantic_class": "symmetry"
    },

    "fill_region": {
        "semantic_concept": "containment",
        "category": "region_causality",
        "causal_effect": "enclosure_completion",
        "spatial_effect": "fill",
        "semantic_class": "topological"
    },

    "preserve_objects": {
        "semantic_concept": "object_identity_preservation",
        "category": "stability",
        "causal_effect": "preserve_object_count",
        "spatial_effect": "none",
        "semantic_class": "invariant"
    },

    "preserve_shape": {
        "semantic_concept": "shape_preservation",
        "category": "stability",
        "causal_effect": "preserve_grid_shape",
        "spatial_effect": "none",
        "semantic_class": "invariant"
    },

    "preserve_colors": {
        "semantic_concept": "color_preservation",
        "category": "stability",
        "causal_effect": "preserve_palette",
        "spatial_effect": "none",
        "semantic_class": "invariant"
    },

    "preserve_position": {
        "semantic_concept": "position_preservation",
        "category": "stability",
        "causal_effect": "preserve_position",
        "spatial_effect": "none",
        "semantic_class": "invariant"
    },

    "preserve_size": {
        "semantic_concept": "size_preservation",
        "category": "stability",
        "causal_effect": "preserve_area",
        "spatial_effect": "none",
        "semantic_class": "invariant"
    },

    "preserve_density": {
        "semantic_concept": "density_preservation",
        "category": "stability",
        "causal_effect": "preserve_density",
        "spatial_effect": "none",
        "semantic_class": "invariant"
    },

    "preserve_topology": {
        "semantic_concept": "topology_preservation",
        "category": "stability",
        "causal_effect": "preserve_connectivity",
        "spatial_effect": "none",
        "semantic_class": "invariant"
    },

    "preserve_symmetry": {
        "semantic_concept": "symmetry_preservation",
        "category": "stability",
        "causal_effect": "preserve_symmetry",
        "spatial_effect": "none",
        "semantic_class": "invariant"
    }
}


SEMANTIC_CONSTRAINTS = {

    "preserve_position": {
        "position_preservation",
        "stability",
        "invariant"
    },

    "preserve_size": {
        "size_preservation",
        "stability",
        "invariant"
    },

    "preserve_density": {
        "density_preservation",
        "stability",
        "invariant"
    },

    "preserve_topology": {
        "topology_preservation",
        "stability",
        "invariant"
    },

    "preserve_symmetry": {
        "symmetry_preservation",
        "stability",
        "invariant"
    },

    "preserve_objects": {
        "object_identity_preservation",
        "stability",
        "invariant"
    },

    "translate_right": {
        "directional_motion",
        "spatial_causality",
        "kinematic"
    },

    "translate_left": {
        "directional_motion",
        "spatial_causality",
        "kinematic"
    },

    "translate_up": {
        "directional_motion",
        "spatial_causality",
        "kinematic"
    },

    "translate_down": {
        "directional_motion",
        "spatial_causality",
        "kinematic"
    },

    "replace_color": {
        "symbolic_remapping",
        "attribute_causality",
        "symbolic"
    },

    "duplicate_object": {
        "replication",
        "object_causality",
        "multiplicative"
    },

    "expand_object": {
        "growth",
        "object_causality",
        "additive"
    },

    "expand_pattern": {
        "propagation",
        "spatial_causality",
        "diffusive"
    },

    "grow_topology": {
        "topological_growth",
        "topology_causality",
        "structural"
    }
}


HYPOTHESIS_ONTOLOGY = {

    "color_change":
    "symbolic_remapping",

    "color_transformation":
    "symbolic_remapping",

    "object_translation":
    "directional_motion",

    "object_size":
    "growth",

    "object_count":
    "replication",

    "object_count_delta":
    "object_cardinality",

    "density_change":
    "density_modulation",

    "symmetry_analysis":
    "symmetry_reasoning",

    "topology_analysis":
    "topological_reasoning",

    "topology_change":
    "topological_change",

    "shape_transformation":
    "shape_relation"
}


ONTOLOGY_COMPRESSION_MAP = {

    "replication":
    "multiplicative_replication",

    "duplicate_pattern":
    "multiplicative_replication",

    "copy_structure":
    "multiplicative_replication",

    "propagation":
    "spatial_propagation",

    "directional_motion":
    "kinematic_translation",

    "position_shift":
    "kinematic_translation",

    "symbolic_remapping":
    "attribute_remapping"
}


SEMANTIC_COMPRESSION_LEVELS = {

    "replication":
    SemanticCompressionLevel(
        local_identity="object_replication",
        structural_identity="object_count_expansion",
        causal_identity="increase_object_count",
        archetypal_identity="multiplicative_replication",
        topology_signature="object_copy"
    ),

    "growth":
    SemanticCompressionLevel(
        local_identity="object_area_growth",
        structural_identity="local_spatial_expansion",
        causal_identity="increase_area",
        archetypal_identity="additive_growth",
        topology_signature="local_area"
    ),

    "topological_growth":
    SemanticCompressionLevel(
        local_identity="connectivity_growth",
        structural_identity="topology_restructuring",
        causal_identity="increase_connectivity",
        archetypal_identity="additive_growth",
        topology_signature="connectivity"
    ),

    "propagation":
    SemanticCompressionLevel(
        local_identity="pattern_propagation",
        structural_identity="distributed_spread",
        causal_identity="increase_density",
        archetypal_identity="spatial_propagation",
        topology_signature="diffusion"
    ),

    "directional_motion":
    SemanticCompressionLevel(
        local_identity="directional_translation",
        structural_identity="position_shift",
        causal_identity="position_shift",
        archetypal_identity="kinematic_translation",
        topology_signature="motion"
    ),

    "symbolic_remapping":
    SemanticCompressionLevel(
        local_identity="attribute_substitution",
        structural_identity="surface_relabeling",
        causal_identity="attribute_substitution",
        archetypal_identity="attribute_remapping",
        topology_signature="none"
    )
}


ADAPTIVE_COMPRESSION_GROUPS = {

    "invariant_preservation": {
        "concepts": {
            "color_preservation",
            "shape_preservation",
            "density_preservation",
            "topology_preservation",
            "symmetry_preservation",
            "position_preservation",
            "size_preservation",
            "object_identity_preservation"
        },
        "threshold": 0.20
    }
}


def lookup_operator_semantics(
    primitive
):

    return SEMANTIC_ONTOLOGY.get(
        primitive,
        {}
    )


def lookup_hypothesis_concept(
    hypothesis_type
):

    hypothesis_type = str(
        hypothesis_type
    )

    for pattern, concept in HYPOTHESIS_ONTOLOGY.items():

        if pattern in hypothesis_type:

            return concept

    return "generic_transformation"


def compress_semantic_concept(
    semantic_concept,
    semantic_distance=0.0
):

    direct_compression = ONTOLOGY_COMPRESSION_MAP.get(
        semantic_concept
    )

    if direct_compression:

        return direct_compression

    for compressed_concept, config in ADAPTIVE_COMPRESSION_GROUPS.items():

        if semantic_concept not in config.get(
            "concepts",
            set()
        ):

            continue

        threshold = config.get(
            "threshold",
            0.0
        )

        if semantic_distance <= threshold:

            return compressed_concept

    return semantic_concept


def compression_level_for_concept(
    semantic_concept
):

    return SEMANTIC_COMPRESSION_LEVELS.get(
        semantic_concept,
        SemanticCompressionLevel(
            local_identity=semantic_concept,
            structural_identity=semantic_concept,
            causal_identity=semantic_concept,
            archetypal_identity=semantic_concept,
            topology_signature="none"
        )
    )


def semantic_compression_allowed(
    first_level,
    second_level,
    causal_threshold=1.0,
    structural_threshold=1.0,
    topology_divergence_limit=0.0
):

    causal_overlap = (
        1.0
        if first_level.causal_identity
        ==
        second_level.causal_identity
        else 0.0
    )

    structural_overlap = (
        1.0
        if first_level.structural_identity
        ==
        second_level.structural_identity
        else 0.0
    )

    topology_divergence = (
        0.0
        if first_level.topology_signature
        ==
        second_level.topology_signature
        else 1.0
    )

    return {
        "allowed":
        (
            causal_overlap >= causal_threshold
            and
            structural_overlap >= structural_threshold
            and
            topology_divergence <= topology_divergence_limit
        ),

        "causal_overlap":
        causal_overlap,

        "structural_overlap":
        structural_overlap,

        "topology_divergence":
        topology_divergence
    }


def validate_semantic_consistency(
    primitive,
    semantic_concept,
    category,
    semantic_class
):

    allowed = SEMANTIC_CONSTRAINTS.get(
        primitive
    )

    if not allowed:

        return {
            "consistent": True,
            "penalty": 0,
            "reason": "unconstrained_primitive"
        }

    observed = {
        semantic_concept,
        category,
        semantic_class
    }

    if observed.intersection(
        allowed
    ):

        return {
            "consistent": True,
            "penalty": 0,
            "reason": "semantic_constraint_satisfied"
        }

    return {
        "consistent": False,
        "penalty": 1,
        "reason": "semantic_constraint_violation",
        "allowed": sorted(
            allowed
        ),
        "observed": sorted([
            value
            for value in observed
            if value
        ])
    }
