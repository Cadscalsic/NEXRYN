"""Canonical transformation theory for ARC-style reasoning."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class TransformationTheory:
    concept: str
    transformation_class: str
    subtype: str
    mechanisms: tuple[str, ...]
    constraints: tuple[str, ...]
    dependencies: tuple[str, ...]
    composable: bool
    canonical_operations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("mechanisms", "constraints", "dependencies", "canonical_operations"):
            payload[key] = list(payload[key])
        return payload


class TransformationTheoryEngine:
    """Map semantic concepts into the transformation universe NEXRYN can search."""

    system_name = "transformation_theory_engine"

    THEORY_LIBRARY = {
        "density": TransformationTheory(
            concept="density_transformation",
            transformation_class="OBJECT_EXPANSION",
            subtype="DENSITY_MODULATION",
            mechanisms=("duplication", "propagation", "growth", "fill", "expansion"),
            constraints=("preserve_color_optional", "topology_may_change", "object_count_may_change"),
            dependencies=("spatial_relations", "object_identity", "topology"),
            composable=True,
            canonical_operations=("duplicate", "expand", "grow", "fill_region"),
        ),
        "spatial": TransformationTheory(
            concept="spatial_transformation",
            transformation_class="SPATIAL_TRANSFORMATION",
            subtype="POSITION_OR_ORIENTATION_CHANGE",
            mechanisms=("translation", "rotation", "reflection", "relative_placement"),
            constraints=("preserve_colors", "preserve_topology_optional", "reference_frame_required"),
            dependencies=("object_centroid", "grid_axis", "anchor_object"),
            composable=True,
            canonical_operations=("translate", "rotate", "mirror_horizontal", "mirror_vertical"),
        ),
        "color": TransformationTheory(
            concept="color_transformation",
            transformation_class="SYMBOLIC_TRANSFORMATION",
            subtype="COLOR_MAPPING",
            mechanisms=("global_remap", "local_remap", "symbolic_substitution", "object_color_rebinding"),
            constraints=("preserve_shape", "preserve_position", "mapping_must_be_consistent"),
            dependencies=("color_classes", "object_identity", "symbolic_roles"),
            composable=True,
            canonical_operations=("recolor",),
        ),
        "physics": TransformationTheory(
            concept="physics_transformation",
            transformation_class="PHYSICS_TRANSFORMATION",
            subtype="GRAVITY_OR_SUPPORT_DYNAMICS",
            mechanisms=("falling", "collision", "support", "component_merging", "rest_state"),
            constraints=("down_axis_required", "support_stops_motion", "collision_changes_topology_optional"),
            dependencies=("topology", "connectivity", "spatial_relations", "support_surfaces"),
            composable=True,
            canonical_operations=("translate", "connect_components"),
        ),
        "quantity": TransformationTheory(
            concept="quantity_transformation",
            transformation_class="QUANTITY_TRANSFORMATION",
            subtype="CARDINALITY_RULE",
            mechanisms=("object_grouping", "cardinality_extraction", "count_delta", "quantity_preservation"),
            constraints=("grouping_rule_required", "count_domain_required", "object_identity_optional"),
            dependencies=("object_components", "color_groups", "set_membership"),
            composable=True,
            canonical_operations=("duplicate", "remove_object", "select_object"),
        ),
        "topology": TransformationTheory(
            concept="topological_transformation",
            transformation_class="TOPOLOGICAL_TRANSFORMATION",
            subtype="CONNECTIVITY_CHANGE",
            mechanisms=("component_connection", "component_splitting", "containment_change", "boundary_fill"),
            constraints=("connectivity_must_be_validated", "shape_may_change", "color_policy_required"),
            dependencies=("connected_components", "adjacency", "region_boundaries"),
            composable=True,
            canonical_operations=("connect_components", "fill_region", "grow"),
        ),
        "compound": TransformationTheory(
            concept="compound_transformation",
            transformation_class="COMPOUND_TRANSFORMATION",
            subtype="TRANSFORMATION_SEQUENCE",
            mechanisms=("ordered_composition", "parallel_composition", "conditional_composition"),
            constraints=("operation_order_required", "intermediate_state_optional", "conflict_resolution_required"),
            dependencies=("selected_transformations", "mechanism_graphs", "execution_order"),
            composable=True,
            canonical_operations=("compose",),
        ),
    }

    CONCEPT_TO_THEORY = {
        "density_increase": "density",
        "object_creation": "density",
        "symmetry_creation": "spatial",
        "growth": "density",
        "topological_growth": "density",
        "object_expansion": "density",
        "relative_position": "spatial",
        "spatial_relation": "spatial",
        "object_translation": "spatial",
        "directional_motion": "spatial",
        "rotation": "spatial",
        "reflection": "spatial",
        "rotation_reflection": "spatial",
        "orientation_change": "spatial",
        "symbolic_remapping": "color",
        "color_mapping": "color",
        "gravity": "physics",
        "gravity_simulation": "physics",
        "falling": "physics",
        "support": "physics",
        "collision": "physics",
        "rest_state": "physics",
        "downward_motion": "physics",
        "object_counting": "quantity",
        "cardinality": "quantity",
        "quantity_preservation": "quantity",
        "quantity_transformation": "quantity",
        "numerical_reasoning": "quantity",
        "set_reasoning": "quantity",
        "connectivity_change": "topology",
        "component_connection": "topology",
        "bridge_creation": "topology",
        "component_merging": "topology",
        "topology_change": "topology",
        "region_filling": "topology",
        "transformation_sequence": "compound",
    }

    def build_theory(
        self,
        concepts: list[str] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        transformation_explanation_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        concepts = list(dict.fromkeys(str(item) for item in concepts or []))
        families = []
        for concept in concepts:
            family = self.CONCEPT_TO_THEORY.get(concept)
            if family and family not in families:
                families.append(family)
        explanation = (
            transformation_explanation_report
            if isinstance(transformation_explanation_report, Mapping)
            else {}
        )
        selected_explanation = explanation.get("selected_explanation", {})
        if isinstance(selected_explanation, Mapping):
            for family in selected_explanation.get("theory_families", []) or []:
                if family in self.THEORY_LIBRARY and family not in families:
                    families.append(family)
        theories = [self.THEORY_LIBRARY[family].to_dict() for family in families]
        operation_space = sorted({
            operation
            for theory in theories
            for operation in theory["canonical_operations"]
        })
        mechanism_space = sorted({
            mechanism
            for theory in theories
            for mechanism in theory["mechanisms"]
        })
        return {
            "system": self.system_name,
            "TRANSFORMATION_THEORY_REPORT": True,
            "input_concepts": concepts,
            "transformation_explanation_report": explanation,
            "macro_concept": explanation.get("macro_concept"),
            "theory_count": len(theories),
            "theory_families": families,
            "transformation_theories": theories,
            "transformation_space": {
                "classes": sorted({theory["transformation_class"] for theory in theories}),
                "subtypes": sorted({theory["subtype"] for theory in theories}),
                "mechanisms": mechanism_space,
                "operations": operation_space,
                "composable": any(theory["composable"] for theory in theories),
            },
            "worldview_count": len({theory["transformation_class"] for theory in theories}),
            "timestamp": str(datetime.utcnow()),
        }


transformation_theory_engine = TransformationTheoryEngine()


__all__ = [
    "TransformationTheory",
    "TransformationTheoryEngine",
    "transformation_theory_engine",
]
