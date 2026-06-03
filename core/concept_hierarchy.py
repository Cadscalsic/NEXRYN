"""
Hierarchical Concept Space: Layered classification preventing invalid merges.
"""

from dataclasses import dataclass, field
from typing import Optional, Set, List
from enum import Enum


class ConceptLayer(Enum):
    """Five-layer concept hierarchy."""
    PRIMITIVE = 1  # Basic sensory/atomic concepts
    STRUCTURAL = 2  # Relationships between primitives
    CAUSAL = 3  # Causal mechanisms and dynamics
    META_COGNITIVE = 4  # Self-referential, governance concepts
    GOVERNANCE = 5  # System-level policy and rules


@dataclass
class HierarchicalConcept:
    """A concept with explicit layer assignment."""
    id: str
    layer: ConceptLayer
    name: str
    description: str = ""
    allowed_merge_layers: Set[ConceptLayer] = field(default_factory=set)
    primitive_dependencies: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize allowed merge layers if not provided."""
        if not self.allowed_merge_layers:
            # By default, allow merging with same layer and adjacent layers
            self.allowed_merge_layers = {self.layer}
            if self.layer.value > 1:
                self.allowed_merge_layers.add(ConceptLayer(self.layer.value - 1))
            if self.layer.value < 5:
                self.allowed_merge_layers.add(ConceptLayer(self.layer.value + 1))


class ConceptHierarchy:
    """
    Manager for hierarchical concept space.
    Enforces layer constraints and prevents invalid cross-layer merges.
    """

    def __init__(self):
        self._concepts: dict[str, HierarchicalConcept] = {}
        self._concepts_by_layer: dict[ConceptLayer, Set[str]] = {
            layer: set() for layer in ConceptLayer
        }

    def register_concept(self, concept: HierarchicalConcept) -> None:
        """Register a new hierarchical concept."""
        self._concepts[concept.id] = concept
        self._concepts_by_layer[concept.layer].add(concept.id)

    def get_concept(self, concept_id: str) -> Optional[HierarchicalConcept]:
        """Retrieve a concept by ID."""
        return self._concepts.get(concept_id)

    def list_by_layer(self, layer: ConceptLayer) -> List[HierarchicalConcept]:
        """Get all concepts in a specific layer."""
        return [
            self._concepts[cid]
            for cid in self._concepts_by_layer.get(layer, set())
        ]

    def can_merge_layers(
        self, layer_a: ConceptLayer, layer_b: ConceptLayer
    ) -> bool:
        """Check if two layers can merge directly."""
        # Only same-layer or adjacent layers (with special rules)
        layer_diff = abs(layer_a.value - layer_b.value)
        return layer_diff <= 1

    def validate_merge(
        self, concept_a_id: str, concept_b_id: str
    ) -> tuple[bool, str]:
        """
        Validate if two concepts can merge based on layer rules.
        Returns (allowed, reason).
        """
        concept_a = self.get_concept(concept_a_id)
        concept_b = self.get_concept(concept_b_id)

        if not concept_a or not concept_b:
            return False, "One or both concepts not found"

        # Check if merge is allowed by layer rules
        if not self.can_merge_layers(concept_a.layer, concept_b.layer):
            return (
                False,
                f"Cannot merge {concept_a.layer.name} (layer {concept_a.layer.value}) "
                f"with {concept_b.layer.name} (layer {concept_b.layer.value})",
            )

        # Check if concept_b's layer is in concept_a's allowed merge layers
        if concept_b.layer not in concept_a.allowed_merge_layers:
            return (
                False,
                f"Concept {concept_a_id} forbids merging with layer {concept_b.layer.name}",
            )

        # Check if concept_a's layer is in concept_b's allowed merge layers
        if concept_a.layer not in concept_b.allowed_merge_layers:
            return (
                False,
                f"Concept {concept_b_id} forbids merging with layer {concept_a.layer.name}",
            )

        return True, "Merge allowed by hierarchy rules"

    def get_layer(self, concept_id: str) -> Optional[ConceptLayer]:
        """Get the layer of a concept."""
        concept = self.get_concept(concept_id)
        return concept.layer if concept else None

    def export_hierarchy(self) -> dict:
        """Export the concept hierarchy as a dict."""
        return {
            layer.name: [
                {
                    "id": self._concepts[cid].id,
                    "name": self._concepts[cid].name,
                    "allowed_merge_layers": [
                        l.name for l in self._concepts[cid].allowed_merge_layers
                    ],
                }
                for cid in self._concepts_by_layer[layer]
            ]
            for layer in ConceptLayer
        }


__all__ = [
    "ConceptLayer",
    "HierarchicalConcept",
    "ConceptHierarchy",
]
