"""Map executable semantic concepts to operation and primitive families."""

from __future__ import annotations

from typing import Any


SEMANTIC_OPERATION_MAP = {
    "replication": ("duplicate_object", 0.94, "duplication_operations"),
    "duplication": ("duplicate_object", 0.94, "duplication_operations"),
    "object_creation": ("duplicate_object", 0.90, "duplication_operations"),
    "color_preservation": ("preserve_color", 0.92, "color_operations"),
    "color_mapping": ("replace_color", 0.90, "color_operations"),
    "symbolic_remapping": ("remap_symbols", 0.88, "symbolic_operations"),
    "topology_preservation": ("preserve_topology", 0.90, "topology_operations"),
    "topological_growth": ("expand_topology", 0.88, "topology_operations"),
    "growth": ("grow_topology", 0.86, "growth_operations"),
    "symmetry_preservation": ("preserve_symmetry", 0.88, "symmetry_operations"),
    "symmetry_creation": ("mirror_object", 0.87, "symmetry_operations"),
    "directional_motion": ("translate_object", 0.90, "motion_operations"),
    "object_translation": ("translate_object", 0.90, "motion_operations"),
    "rotation": ("rotate", 0.90, "geometric_operations"),
    "orientation_change": ("rotate", 0.90, "geometric_operations"),
    "reflection": ("reflect", 0.88, "geometric_operations"),
    "rotation_reflection": ("rotate_or_reflect", 0.92, "geometric_operations"),
    "scaling": ("scale", 0.88, "scale_operations"),
    "scale_transformation": ("scale", 0.88, "scale_operations"),
    "size_transformation": ("scale", 0.88, "scale_operations"),
    "path_finding": ("construct_path", 0.88, "path_operations"),
    "route_completion": ("construct_path", 0.88, "path_operations"),
    "path_construction": ("construct_path", 0.88, "path_operations"),
    "bridge_creation": ("connect_components", 0.91, "topology_operations"),
    "component_connection": ("connect_components", 0.91, "topology_operations"),
    "connectivity_change": ("connect_components", 0.89, "topology_operations"),
    "topology_change": ("connect_components", 0.87, "topology_operations"),
    "connectivity_restoration": ("repair_topology", 0.84, "topology_operations"),
    "topology_repair": ("repair_topology", 0.84, "topology_operations"),
    "hole_removal": ("repair_topology", 0.84, "topology_operations"),
    "noise_removal": ("remove_noise", 0.84, "filter_operations"),
    "artifact_filtering": ("remove_noise", 0.84, "filter_operations"),
    "object_removal": ("remove_object", 0.86, "filter_operations"),
}


class SemanticOperationMapper:
    """Resolve a concept into a concrete operation candidate."""

    system_name = "semantic_operation_mapper"

    def map(self, concept: str) -> dict[str, Any]:
        concept = _normalize(concept)
        operation, confidence, family = SEMANTIC_OPERATION_MAP.get(
            concept,
            (None, 0.0, None),
        )
        return {
            "system": self.system_name,
            "concept": concept,
            "operation_name": operation,
            "confidence": round(float(confidence), 4),
            "primitive_family": family,
            "operation_ready": operation is not None,
        }


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


semantic_operation_mapper = SemanticOperationMapper()

__all__ = [
    "SEMANTIC_OPERATION_MAP",
    "SemanticOperationMapper",
    "semantic_operation_mapper",
]
