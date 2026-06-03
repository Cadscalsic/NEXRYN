"""
Semantic Constitution: Immutable rules governing concept merging, identity, and safety.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class IdentityRules:
    """Rules for concept identity preservation."""
    max_identity_drift: float = 0.25  # Max allowed divergence from original identity
    require_lineage_tracking: bool = True  # Must track concept ancestry
    forbid_recursive_self_merge: bool = True  # Cannot merge concept with itself


@dataclass
class CausalityRules:
    """Rules for maintaining causal coherence."""
    require_causal_alignment: bool = True  # Merged concepts must have compatible causality
    max_temporal_paradox_gap: float = 0.1  # Max allowed temporal inconsistency
    forbid_acyclic_violations: bool = True  # No cyclic causal dependencies


@dataclass
class MergeRules:
    """Rules for concept merging operations."""
    require_causal_alignment: bool = True
    require_topology_compatibility: bool = True
    max_identity_drift: float = 0.25
    min_semantic_overlap: float = 0.3  # Must share 30% conceptual meaning
    forbid_layer_mixing: bool = True  # Cannot merge concepts from different hierarchy levels
    min_reputation_for_merge: float = 0.5  # Min reputation score required


@dataclass
class ProtectionRules:
    """Safety rules for concept lifecycle."""
    forbid_merge_of_toxic_lineages: bool = True  # Don't merge with known dangerous concepts
    require_safety_audit_before_deploy: bool = True  # All concepts need vetting
    min_reputation_for_merge: float = 0.5  # Min reputation score required
    min_survival_duration_hours: float = 1.0  # Concept must exist 1+ hours before merging


class SemanticConstitution:
    """
    Immutable ruleset governing all concept operations.
    Derived from evolutionary graveyard analysis and safety requirements.
    """

    def __init__(self):
        self.identity_rules = IdentityRules()
        self.causality_rules = CausalityRules()
        self.merge_rules = MergeRules()
        self.protection_rules = ProtectionRules()

    def can_merge(
        self,
        concept_a_id: str,
        concept_b_id: str,
        reputation_a: float,
        reputation_b: float,
        semantic_overlap: float,
        causal_aligned: bool,
        toxic_lineage_a: bool = False,
        toxic_lineage_b: bool = False,
    ) -> tuple[bool, str]:
        """
        Validate if two concepts can safely merge.
        Returns (allowed, reason).
        """

        # Identity check
        if concept_a_id == concept_b_id and self.identity_rules.forbid_recursive_self_merge:
            return False, "Self-merge forbidden by identity rules"

        # Causality check
        if not causal_aligned and self.merge_rules.require_causal_alignment:
            return False, "Causal misalignment"

        # Topology check
        if self.merge_rules.require_topology_compatibility:
            # (placeholder for actual topology validation)
            pass

        # Semantic overlap check
        if semantic_overlap < self.merge_rules.min_semantic_overlap:
            return False, f"Insufficient semantic overlap: {semantic_overlap:.2f}"

        # Reputation check
        if reputation_a < self.merge_rules.min_reputation_for_merge:
            return False, f"Concept A reputation too low: {reputation_a:.2f}"
        if reputation_b < self.merge_rules.min_reputation_for_merge:
            return False, f"Concept B reputation too low: {reputation_b:.2f}"

        # Toxic lineage check
        if toxic_lineage_a or toxic_lineage_b:
            if self.protection_rules.forbid_merge_of_toxic_lineages:
                return False, "Toxic lineage detected"

        return True, "Merge allowed"

    def export_rules(self) -> Dict[str, Any]:
        """Export all rules as a dictionary for inspection."""
        return {
            "identity_rules": self.identity_rules.__dict__,
            "causality_rules": self.causality_rules.__dict__,
            "merge_rules": self.merge_rules.__dict__,
            "protection_rules": self.protection_rules.__dict__,
        }


# Global singleton constitution
GLOBAL_CONSTITUTION = SemanticConstitution()


__all__ = [
    "IdentityRules",
    "CausalityRules",
    "MergeRules",
    "ProtectionRules",
    "SemanticConstitution",
    "GLOBAL_CONSTITUTION",
]
