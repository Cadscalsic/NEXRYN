from dataclasses import asdict, dataclass


def _normalize(value, default="unknown"):
    if value is None:
        return default
    return str(value).strip().lower().replace(" ", "_") or default


@dataclass(frozen=True)
class ProcessAbstraction:
    concept: str
    context_id: str
    context_family: str
    surface: str
    definition: str
    properties: tuple
    capabilities: tuple
    constraints: tuple
    implications: tuple
    transfer_conditions: tuple
    validation_criteria: tuple
    native_contexts: tuple
    object_dynamics: str
    size_behavior: str
    topology_behavior: str
    identity_behavior: str
    propagation_behavior: str
    inherited_features: tuple
    dependency_contexts: tuple

    def discovery_surface(self):
        return {
            "context_id": self.context_id,
            "context_family": self.context_family,
            "surface": self.surface,
            "definition": self.definition,
            "native_contexts": list(self.native_contexts),
            "object_dynamics": self.object_dynamics,
            "size_behavior": self.size_behavior,
            "topology_behavior": self.topology_behavior,
            "identity_behavior": self.identity_behavior,
            "propagation_behavior": self.propagation_behavior,
            "transfer_conditions": list(self.transfer_conditions),
            "validation_criteria": list(self.validation_criteria),
        }

    def semantic_context(self):
        return {
            "definition": self.definition,
            "properties": list(self.properties),
            "capabilities": list(self.capabilities),
            "constraints": list(self.constraints),
            "implications": list(self.implications),
            "transfer_conditions": list(self.transfer_conditions),
            "validation_criteria": list(self.validation_criteria),
        }

    def hierarchy_root(self):
        return self.context_id, set(self.native_contexts + (self.concept,))

    def as_dict(self):
        result = asdict(self)
        for key, value in list(result.items()):
            if isinstance(value, tuple):
                result[key] = list(value)
        return result


class ProcessAbstractionLayer:
    ABSTRACTIONS = {
        "growth": ProcessAbstraction(
            concept="growth",
            context_id="growth_context",
            context_family="Growth Context",
            surface="topology_expansion",
            definition=(
                "Object count, area, or topology expands while preserving "
                "identity continuity."
            ),
            properties=(
                "topology_expansion",
                "object_count_growth",
                "identity_preservation_under_growth",
                "shape_anchor_required",
            ),
            capabilities=(
                "region_expansion",
                "topology_growth",
                "identity_preserving_growth",
            ),
            constraints=(
                "requires_identity_anchor",
                "requires_source_pattern",
                "requires_shape_anchor",
            ),
            implications=(
                "topology_expansion_expected",
                "object_count_or_area_growth_expected",
                "identity_continuity_under_growth_expected",
            ),
            transfer_conditions=(
                "source_object_remains_traceable",
                "expanded_region_preserves_local_shape",
                "object_count_or_area_increases",
            ),
            validation_criteria=(
                "dependency_chain_contains_identity_continuity",
                "semantic_context_contains_topology_expansion",
                "hierarchy_parent_is_growth_context",
            ),
            native_contexts=(
                "topology_expansion",
                "object_count_growth",
                "identity_preservation_under_growth",
            ),
            object_dynamics="object_expanded",
            size_behavior="size_expanded",
            topology_behavior="topology_expanding",
            identity_behavior="identity_preserved_under_growth",
            propagation_behavior="growth_expansion",
            inherited_features=(
                "topology_expansion",
                "object_count_growth",
                "identity_preservation_under_growth",
                "shape_anchor_required",
            ),
            dependency_contexts=(
                "identity_persistence",
                "object_persistence",
                "identity_continuity",
                "object_core",
                "shape_preservation",
                "topology_expansion",
                "object_count_growth",
                "identity_preservation_under_growth",
            ),
        ),
        "replication": ProcessAbstraction(
            concept="replication",
            context_id="replication_context",
            context_family="Replication Context",
            surface="structural_copying",
            definition=(
                "New object instances emerge through structural duplication."
            ),
            properties=(
                "object_creation",
                "identity_forking",
                "identity_split",
                "structural_copying",
                "shape_anchor_required",
            ),
            capabilities=(
                "object_creation",
                "structural_replication",
                "identity_split_reasoning",
            ),
            constraints=(
                "requires_source_object",
                "requires_shape_anchor",
                "object_count_changes",
            ),
            implications=(
                "object_count_increase",
                "identity_split_expected",
                "structural_copy_expected",
            ),
            transfer_conditions=(
                "source_shape_remains_recognizable",
                "new_instance_derives_from_source_object",
                "identity_split_is_explainable",
            ),
            validation_criteria=(
                "dependency_chain_contains_identity_split",
                "semantic_context_contains_structural_copying",
                "hierarchy_parent_is_replication_context",
            ),
            native_contexts=(
                "object_creation",
                "identity_split",
                "structural_copying",
            ),
            object_dynamics="object_created",
            size_behavior="size_preserved",
            topology_behavior="topology_splitting",
            identity_behavior="identity_split",
            propagation_behavior="replication_detected",
            inherited_features=(
                "structural_copying",
                "object_creation",
                "identity_split",
                "shape_anchor_required",
            ),
            dependency_contexts=(
                "structural_copying",
                "object_creation",
                "identity_split",
                "object_count_increase",
                "topology_splitting",
                "local_shape",
                "shape_preservation",
            ),
        ),
        "propagation": ProcessAbstraction(
            concept="propagation",
            context_id="propagation_context",
            context_family="Propagation Context",
            surface="directional_spread",
            definition=(
                "Structure or information spreads while preserving source "
                "lineage."
            ),
            properties=(
                "directional_spread",
                "source_pattern_preservation",
                "source_pattern_preserved",
                "signal_transfer",
            ),
            capabilities=(
                "pattern_extension",
                "directional_transfer",
                "source_pattern_preservation",
            ),
            constraints=(
                "requires_source_pattern",
                "requires_directional_path",
            ),
            implications=(
                "directional_motion_expected",
                "source_pattern_preservation_expected",
            ),
            transfer_conditions=(
                "source_pattern_remains_identifiable",
                "spread_has_directional_continuity",
                "target_cells_preserve_lineage_signal",
            ),
            validation_criteria=(
                "dependency_chain_contains_directional_motion",
                "semantic_context_contains_directional_spread",
                "hierarchy_parent_is_propagation_context",
            ),
            native_contexts=(
                "directional_spread",
                "source_pattern_preservation",
                "source_pattern_preserved",
                "signal_transfer",
            ),
            object_dynamics="object_propagated",
            size_behavior="size_expanded",
            topology_behavior="topology_propagating",
            identity_behavior="identity_propagated",
            propagation_behavior="propagation_detected",
            inherited_features=(
                "recursive_spread",
                "multi_cell_effect",
                "source_pattern_preserved",
                "directional_spread",
                "signal_transfer",
            ),
            dependency_contexts=(
                "directional_spread",
                "source_pattern_preservation",
                "signal_transfer",
                "source_pattern_preserved",
                "directional_motion",
                "position_change",
                "position_preservation",
                "local_shape",
            ),
        ),
        "topological_growth": ProcessAbstraction(
            concept="topological_growth",
            context_id="topological_growth_context",
            context_family="Topological Growth Context",
            surface="topology_expansion",
            definition=(
                "Connectivity complexity increases while local structure "
                "remains stable."
            ),
            properties=(
                "topology_expansion",
                "region_expansion",
                "topology_splitting",
                "identity_preservation_under_growth",
            ),
            capabilities=(
                "region_expansion",
                "topology_growth",
                "topology_split_reasoning",
                "identity_preserving_growth",
            ),
            constraints=(
                "requires_growth_dependency",
                "requires_shape_anchor",
            ),
            implications=(
                "topology_expansion_expected",
                "growth_dependency_required",
            ),
            transfer_conditions=(
                "expanded_topology_remains_connected_to_source",
                "local_shape_features_survive_expansion",
                "growth_dependency_is_resolved",
            ),
            validation_criteria=(
                "dependency_chain_contains_growth",
                "semantic_context_contains_topology_expansion",
                "hierarchy_parent_is_topological_growth_context",
            ),
            native_contexts=(
                "topology_expansion",
                "region_expansion",
                "topology_splitting",
                "identity_preservation_under_growth",
            ),
            object_dynamics="object_expanded",
            size_behavior="size_expanded",
            topology_behavior="topology_expanding",
            identity_behavior="identity_preserved_under_growth",
            propagation_behavior="growth_expansion",
            inherited_features=(
                "topology_expansion",
                "topology_splitting",
                "growth_dependency_required",
                "shape_anchor_required",
            ),
            dependency_contexts=(
                "growth",
                "topology_expansion",
                "region_expansion",
                "topology_splitting",
                "identity_preservation_under_growth",
                "local_shape",
                "shape_preservation",
            ),
        ),
        "directional_motion": ProcessAbstraction(
            concept="directional_motion",
            context_id="directional_motion_context",
            context_family="Directional Motion Context",
            surface="position_delta",
            definition=(
                "Object position changes according to consistent directional "
                "rules."
            ),
            properties=(
                "position_delta",
                "directional_displacement",
                "source_pattern_motion",
            ),
            capabilities=(
                "spatial_relocation",
                "directional_transfer",
                "source_pattern_preservation",
            ),
            constraints=(
                "requires_position_reference",
                "requires_object_persistence",
            ),
            implications=(
                "position_change_expected",
                "identity_continuity_expected",
            ),
            transfer_conditions=(
                "source_object_persists_after_motion",
                "position_delta_is_directionally_consistent",
                "source_pattern_motion_remains_traceable",
            ),
            validation_criteria=(
                "dependency_chain_contains_position_change",
                "semantic_context_contains_position_delta",
                "hierarchy_parent_is_directional_motion_context",
            ),
            native_contexts=(
                "position_delta",
                "directional_displacement",
                "source_pattern_motion",
            ),
            object_dynamics="object_moved",
            size_behavior="size_preserved",
            topology_behavior="topology_restructured",
            identity_behavior="identity_preserved",
            propagation_behavior="directional_motion_detected",
            inherited_features=(
                "position_delta",
                "directional_displacement",
                "object_persistence_required",
                "source_pattern_motion",
            ),
            dependency_contexts=(
                "position_delta",
                "directional_displacement",
                "source_pattern_motion",
                "position_change",
                "propagation",
                "identity_persistence",
            ),
        ),
    }

    @classmethod
    def get(cls, concept):
        concept = _normalize(concept)
        abstraction = cls.ABSTRACTIONS.get(concept)
        if abstraction:
            return abstraction
        for item in cls.ABSTRACTIONS.values():
            if item.context_id == concept:
                return item
        return None

    @classmethod
    def has_process_context(cls, concept):
        return cls.get(concept) is not None

    @classmethod
    def discovery_surfaces(cls):
        return {
            concept: abstraction.discovery_surface()
            for concept, abstraction in cls.ABSTRACTIONS.items()
        }

    @classmethod
    def semantic_contexts(cls):
        contexts = {}
        for concept, abstraction in cls.ABSTRACTIONS.items():
            context = abstraction.semantic_context()
            contexts[concept] = context
            contexts[abstraction.context_id] = context
        return contexts

    @classmethod
    def hierarchy_roots(cls):
        return {
            abstraction.context_id: set(
                abstraction.native_contexts + (abstraction.concept,)
            )
            for abstraction in cls.ABSTRACTIONS.values()
        }

    @classmethod
    def inherited_features(cls):
        entries = {}
        for abstraction in cls.ABSTRACTIONS.values():
            entries[abstraction.context_id] = list(
                abstraction.inherited_features
            )
            entries[abstraction.concept] = list(abstraction.inherited_features)
        return entries

    @classmethod
    def dependency_contexts(cls):
        contexts = {}
        for abstraction in cls.ABSTRACTIONS.values():
            dependencies = list(abstraction.dependency_contexts)
            contexts[abstraction.concept] = dependencies
            contexts[abstraction.context_id] = dependencies
        return contexts

    @classmethod
    def report(cls, concepts=None):
        selected = [
            _normalize(concept)
            for concept in concepts
        ] if concepts else sorted(cls.ABSTRACTIONS)
        abstractions = [
            cls.ABSTRACTIONS[concept].as_dict()
            for concept in selected
            if concept in cls.ABSTRACTIONS
        ]
        return {
            "system": "process_abstraction_layer",
            "process_abstraction_count": len(abstractions),
            "process_abstractions": abstractions,
            "process_context_ready": bool(abstractions),
        }


__all__ = [
    "ProcessAbstraction",
    "ProcessAbstractionLayer",
]
