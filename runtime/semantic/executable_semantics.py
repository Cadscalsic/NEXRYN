"""Executable semantic validation for concepts that can become operations."""

from __future__ import annotations

from typing import Any, Mapping


EXECUTABLE_SEMANTICS = {
    "replication": {
        "required_primitives": ("duplicate_object",),
        "execution_path": "object_duplication",
        "primitive_family": "duplication_operations",
    },
    "duplication": {
        "required_primitives": ("duplicate_object",),
        "execution_path": "object_duplication",
        "primitive_family": "duplication_operations",
    },
    "object_creation": {
        "required_primitives": ("duplicate_object",),
        "execution_path": "object_duplication",
        "primitive_family": "duplication_operations",
    },
    "propagation": {
        "required_primitives": ("duplicate_object",),
        "execution_path": "pattern_propagation",
        "primitive_family": "growth_operations",
    },
    "color_preservation": {
        "required_primitives": ("preserve_colors",),
        "execution_path": "attribute_preservation",
        "primitive_family": "color_operations",
    },
    "color_mapping": {
        "required_primitives": ("replace_color",),
        "execution_path": "symbolic_color_mapping",
        "primitive_family": "color_operations",
    },
    "symbolic_remapping": {
        "required_primitives": ("replace_color",),
        "execution_path": "symbolic_remapping",
        "primitive_family": "symbolic_operations",
    },
    "topology_preservation": {
        "required_primitives": ("preserve_topology",),
        "execution_path": "topology_preservation",
        "primitive_family": "topology_operations",
    },
    "topological_growth": {
        "required_primitives": ("grow_topology", "expand_pattern"),
        "execution_path": "topology_growth",
        "primitive_family": "topology_operations",
    },
    "growth": {
        "required_primitives": ("grow_topology", "expand_pattern"),
        "execution_path": "growth_transform",
        "primitive_family": "growth_operations",
    },
    "symmetry_preservation": {
        "required_primitives": ("preserve_symmetry", "mirror_object"),
        "execution_path": "symmetry_preservation",
        "primitive_family": "symmetry_operations",
    },
    "symmetry_creation": {
        "required_primitives": ("mirror_object", "duplicate_object"),
        "execution_path": "symmetry_construction",
        "primitive_family": "symmetry_operations",
    },
    "directional_motion": {
        "required_primitives": ("translate",),
        "execution_path": "object_translation",
        "primitive_family": "motion_operations",
    },
    "position_preservation": {
        "required_primitives": ("preserve_grid",),
        "execution_path": "position_preservation",
        "primitive_family": "spatial_operations",
    },
    "object_identity_preservation": {
        "required_primitives": ("preserve_grid",),
        "execution_path": "identity_preservation",
        "primitive_family": "identity_operations",
    },
    "object_translation": {
        "required_primitives": ("translate",),
        "execution_path": "object_translation",
        "primitive_family": "motion_operations",
    },
    "rotation": {
        "required_primitives": ("rotate_grid",),
        "execution_path": "geometric_rotation",
        "primitive_family": "geometric_operations",
    },
    "orientation_change": {
        "required_primitives": ("rotate_grid",),
        "execution_path": "geometric_rotation",
        "primitive_family": "geometric_operations",
    },
    "reflection": {
        "required_primitives": ("mirror_object", "mirror_vertical"),
        "execution_path": "geometric_reflection",
        "primitive_family": "geometric_operations",
    },
    "rotation_reflection": {
        "required_primitives": ("rotate_grid", "mirror_object"),
        "execution_path": "geometric_transform",
        "primitive_family": "geometric_operations",
    },
    "scaling": {
        "required_primitives": ("expand_grid", "shrink_grid"),
        "execution_path": "scale_transform",
        "primitive_family": "scale_operations",
    },
    "scale_transformation": {
        "required_primitives": ("expand_grid", "shrink_grid"),
        "execution_path": "scale_transform",
        "primitive_family": "scale_operations",
    },
    "size_transformation": {
        "required_primitives": ("expand_grid", "shrink_grid"),
        "execution_path": "scale_transform",
        "primitive_family": "scale_operations",
    },
    "path_finding": {
        "required_primitives": ("construct_path",),
        "execution_path": "path_construction",
        "primitive_family": "path_operations",
    },
    "path_construction": {
        "required_primitives": ("construct_path",),
        "execution_path": "path_construction",
        "primitive_family": "path_operations",
    },
    "route_completion": {
        "required_primitives": ("construct_path",),
        "execution_path": "path_construction",
        "primitive_family": "path_operations",
    },
    "bridge_creation": {
        "required_primitives": ("connect_components",),
        "execution_path": "component_connection",
        "primitive_family": "topology_operations",
    },
    "component_connection": {
        "required_primitives": ("connect_components",),
        "execution_path": "component_connection",
        "primitive_family": "topology_operations",
    },
    "connectivity_change": {
        "required_primitives": ("connect_components",),
        "execution_path": "component_connection",
        "primitive_family": "topology_operations",
    },
    "topology_change": {
        "required_primitives": ("connect_components", "construct_path"),
        "execution_path": "component_connection",
        "primitive_family": "topology_operations",
    },
    "connectivity_restoration": {
        "required_primitives": ("connect_components", "construct_path"),
        "execution_path": "topology_repair",
        "primitive_family": "topology_operations",
    },
    "topology_repair": {
        "required_primitives": ("construct_path", "connect_components"),
        "execution_path": "topology_repair",
        "primitive_family": "topology_operations",
    },
    "hole_removal": {
        "required_primitives": ("construct_path",),
        "execution_path": "topology_repair",
        "primitive_family": "topology_operations",
    },
    "noise_removal": {
        "required_primitives": ("remove_object",),
        "execution_path": "noise_filtering",
        "primitive_family": "filter_operations",
    },
    "artifact_filtering": {
        "required_primitives": ("remove_object",),
        "execution_path": "noise_filtering",
        "primitive_family": "filter_operations",
    },
    "object_removal": {
        "required_primitives": ("remove_object",),
        "execution_path": "object_removal",
        "primitive_family": "filter_operations",
    },
}

NON_EXECUTABLE_CONCEPTS = {
    "context_support",
    "semantic_context",
    "truth_support",
    "causal_support",
    "identity_context",
    "density_preservation",
    "size_preservation",
    "position_preservation",
}


class ExecutableSemanticIntelligence:
    """Decide whether a concept has enough operational meaning to execute."""

    system_name = "executable_semantics"

    def evaluate(
        self,
        concept: str,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        concept = _normalize(concept)
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        available = _available_primitives(runtime_context)
        spec = EXECUTABLE_SEMANTICS.get(concept)
        explicitly_non_executable = concept in NON_EXECUTABLE_CONCEPTS
        required = list(spec.get("required_primitives", ()) if spec else ())
        missing = [
            primitive for primitive in required
            if available and primitive not in available
        ]
        is_executable = bool(spec) and not explicitly_non_executable
        if is_executable and missing:
            coverage_state = "MISSING_PRIMITIVES"
        elif is_executable:
            coverage_state = "EXECUTABLE"
        elif explicitly_non_executable:
            coverage_state = "NON_EXECUTABLE_SEMANTIC_CONTEXT"
        else:
            coverage_state = "UNSUPPORTED_EXECUTION_ROUTE"

        return {
            "system": self.system_name,
            "concept": concept,
            "is_executable": is_executable and not missing,
            "required_primitives": required,
            "execution_path": spec.get("execution_path") if spec else None,
            "primitive_family": spec.get("primitive_family") if spec else None,
            "coverage_state": coverage_state,
            "additional_information_required": bool(missing),
            "missing_primitives": missing,
        }


def _available_primitives(runtime_context: Mapping[str, Any]) -> set[str]:
    raw = runtime_context.get("available_primitives")
    if not raw:
        raw = runtime_context.get("primitive_registry")
    if not raw:
        return set()
    if isinstance(raw, Mapping):
        raw = raw.keys()
    return {_normalize(item) for item in raw if item}


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


executable_semantics = ExecutableSemanticIntelligence()

__all__ = [
    "EXECUTABLE_SEMANTICS",
    "NON_EXECUTABLE_CONCEPTS",
    "ExecutableSemanticIntelligence",
    "executable_semantics",
]
