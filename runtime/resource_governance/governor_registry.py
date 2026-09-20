"""Registry of cognitive layers governed by the adaptive governor."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from runtime.resource_governance.layer_state_registry import (
    LayerExecutionCategory,
    LayerMetadata,
    LayerState,
    LayerStateRegistry,
)


DEFAULT_LAYER_DEFINITIONS = (
    {
        "name": "semantic_memory",
        "description": "Semantic memory access and retrieval layer.",
        "owner": "memory",
        "execution_category": LayerExecutionCategory.COGNITIVE_MEMORY,
    },
    {
        "name": "knowledge_fabric",
        "description": "Knowledge integration and fabric reasoning layer.",
        "owner": "runtime.knowledge",
        "execution_category": LayerExecutionCategory.COGNITIVE_MEMORY,
    },
    {
        "name": "semantic_compilation",
        "description": "Semantic-to-program compilation layer.",
        "owner": "runtime.synthesis",
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "color_mapping",
        "description": "Color remapping and value substitution capability.",
        "owner": "runtime.perception",
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "transformation_reasoning",
        "description": "Geometric and symbolic transformation reasoning layer.",
        "owner": "runtime.transformations",
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "program_generation",
        "description": "Candidate program generation layer.",
        "owner": "runtime.synthesis",
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "object_tracking",
        "description": "Object identity and continuity tracking layer.",
        "owner": "runtime.objects",
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "topology_reasoning",
        "description": "Topological relation reasoning layer.",
        "owner": "core",
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "spatial_reasoning",
        "description": "Spatial relation reasoning layer.",
        "owner": "runtime.spatial",
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "gravity_reasoning",
        "description": "Gravity, support, and falling-object reasoning layer.",
        "owner": "runtime.object_motion",
        "dependencies": ("object_tracking", "spatial_reasoning"),
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "rotation_execution",
        "description": "Rotation execution support layer.",
        "owner": "runtime.transformations",
        "dependencies": ("semantic_compilation",),
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "reflection_execution",
        "description": "Reflection execution support layer.",
        "owner": "runtime.transformations",
        "dependencies": ("semantic_compilation",),
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "scaling_execution",
        "description": "Scaling execution support layer.",
        "owner": "runtime.transformations",
        "dependencies": ("semantic_compilation",),
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "path_reasoning",
        "description": "Path relation and path execution planning layer.",
        "owner": "runtime.spatial",
        "dependencies": ("object_tracking", "spatial_reasoning"),
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "localized_repair",
        "description": "Localized residual repair layer.",
        "owner": "runtime.repair",
        "dependencies": ("object_tracking",),
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "counterfactual_repair",
        "description": "Counterfactual repair support layer.",
        "owner": "runtime.repair",
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "contradiction_resolution",
        "description": "Contradiction resolution and deeper validation layer.",
        "owner": "runtime.validation",
        "dependencies": ("dependency_reasoning",),
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "alternative_proposal_source",
        "description": "Alternative proposal source for source dominance mitigation.",
        "owner": "runtime.arena",
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "dependency_reasoning",
        "description": "Process and causal dependency reasoning layer.",
        "owner": "runtime.process",
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
    {
        "name": "diagnostic_probe",
        "description": "Diagnostic-only lightweight uncertainty probe.",
        "owner": "runtime.diagnostic",
        "execution_category": LayerExecutionCategory.DIAGNOSTIC,
    },
    {
        "name": "report_binding",
        "description": "Runtime result binding for reports.",
        "owner": "runtime.reporting",
        "execution_category": LayerExecutionCategory.REPORTING,
    },
    {
        "name": "report_rendering",
        "description": "Final report rendering layer.",
        "owner": "runtime.reporting",
        "execution_category": LayerExecutionCategory.REPORTING,
    },
    {
        "name": "candidate_arena",
        "description": "Candidate simulation and selection arena.",
        "owner": "runtime.arena",
        "execution_category": LayerExecutionCategory.COGNITIVE_REASONING,
    },
)


class GovernorRegistry:
    def __init__(self, state_registry: LayerStateRegistry | None = None):
        self.state_registry = state_registry or LayerStateRegistry()

    def register_layer(
        self,
        name: str,
        description: str = "",
        dependencies: Iterable[str] | None = None,
        owner: str = "runtime",
        default_state: str | LayerState = LayerState.REGISTERED,
        execution_category: str | LayerExecutionCategory = (
            LayerExecutionCategory.COGNITIVE_REASONING
        ),
        metadata: Mapping[str, Any] | None = None,
    ) -> LayerMetadata:
        layer_metadata = LayerMetadata.build(
            name=name,
            description=description,
            dependencies=dependencies,
            owner=owner,
            default_state=default_state,
            execution_category=execution_category,
            metadata=metadata,
        )
        return self.state_registry.register_layer(layer_metadata)

    def register_defaults(self) -> None:
        for definition in DEFAULT_LAYER_DEFINITIONS:
            self.register_layer(**definition)

    def get_metadata(self, layer_name: str) -> dict[str, Any]:
        metadata = self.state_registry.get_metadata(layer_name)
        return metadata.as_dict() if metadata is not None else {}

    def get_state(self, layer_name: str) -> LayerState:
        return self.state_registry.get_state(layer_name)

    def list_layers(self) -> list[str]:
        return self.state_registry.registered_layers()

    def summary(self) -> dict[str, Any]:
        return {
            "registered_layers": self.list_layers(),
            "registered_layer_count": len(self.list_layers()),
            "layer_metadata": self.state_registry.metadata(),
            "layer_states": self.state_registry.states(),
        }


__all__ = [
    "DEFAULT_LAYER_DEFINITIONS",
    "GovernorRegistry",
]
