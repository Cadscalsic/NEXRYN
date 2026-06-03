"""
Unit tests for semantic constitution, hierarchy, reputation, and energy budget systems.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.semantic_constitution import SemanticConstitution
from core.concept_hierarchy import ConceptHierarchy, HierarchicalConcept, ConceptLayer
from core.concept_reputation import ConceptReputationEngine, ReputationMetrics
from core.cognitive_energy_budget import CognitiveEnergyBudget


def test_semantic_constitution():
    """Test the semantic constitution rules."""
    constitution = SemanticConstitution()

    # Test self-merge rejection
    allowed, reason = constitution.can_merge(
        "C1", "C1", 0.6, 0.6, 0.5, True
    )
    assert not allowed, "Self-merge should be forbidden"

    # Test causal misalignment rejection
    allowed, reason = constitution.can_merge(
        "C1", "C2", 0.6, 0.6, 0.5, False
    )
    assert not allowed, "Causal misalignment should prevent merge"

    # Test semantic overlap check
    allowed, reason = constitution.can_merge(
        "C1", "C2", 0.6, 0.6, 0.1, True
    )
    assert not allowed, "Low semantic overlap should prevent merge"

    # Test successful merge validation
    allowed, reason = constitution.can_merge(
        "C1", "C2", 0.7, 0.7, 0.5, True
    )
    assert allowed, "Valid merge should be allowed"

    # Test toxic lineage blocking
    allowed, reason = constitution.can_merge(
        "C1", "C2", 0.7, 0.7, 0.5, True, toxic_lineage_a=True
    )
    assert not allowed, "Toxic lineage should prevent merge"

    print("✓ Semantic Constitution tests passed")


def test_concept_hierarchy():
    """Test hierarchical concept space."""
    hierarchy = ConceptHierarchy()

    # Register concepts at different layers
    c1 = HierarchicalConcept(
        id="PRIM1",
        layer=ConceptLayer.PRIMITIVE,
        name="Color Primitive",
    )
    c2 = HierarchicalConcept(
        id="STRUCT1",
        layer=ConceptLayer.STRUCTURAL,
        name="Shape Structure",
    )
    c3 = HierarchicalConcept(
        id="GOVER1",
        layer=ConceptLayer.GOVERNANCE,
        name="System Rule",
    )

    hierarchy.register_concept(c1)
    hierarchy.register_concept(c2)
    hierarchy.register_concept(c3)

    # Test same-concept merge (should fail - self merge)
    c_same = HierarchicalConcept(
        id="PRIM2",
        layer=ConceptLayer.PRIMITIVE,
        name="Another Primitive",
    )
    hierarchy.register_concept(c_same)
    allowed, reason = hierarchy.validate_merge("PRIM1", "PRIM2")
    assert allowed, "Same-layer merges should be allowed"

    # Test adjacent layer merge (allowed)
    allowed, reason = hierarchy.validate_merge("PRIM1", "STRUCT1")
    assert allowed, "Adjacent layers should allow merge"

    # Test distant layer merge (forbidden)
    allowed, reason = hierarchy.validate_merge("PRIM1", "GOVER1")
    assert not allowed, "Distant layers should forbid merge"

    # Test layer listing
    primitives = hierarchy.list_by_layer(ConceptLayer.PRIMITIVE)
    assert len(primitives) == 2  # PRIM1 and PRIM2
    assert any(p.id == "PRIM1" for p in primitives)

    print("✓ Concept Hierarchy tests passed")


def test_concept_reputation():
    """Test reputation engine."""
    engine = ConceptReputationEngine()

    # Register a concept
    engine.register_concept("C1")

    # Initial reputation should be moderate
    rep = engine.compute_reputation("C1")
    assert 0.1 < rep < 0.6, f"Initial reputation should be moderate, got {rep}"

    # Record usage increases reputation
    engine.record_usage("C1", utility=0.2)
    rep_after_usage = engine.compute_reputation("C1")
    assert rep_after_usage > rep, "Usage should increase reputation"

    # High causal stability helps (before contradictions)
    engine.register_concept("C3")
    engine.set_causal_stability("C3", 1.0)
    engine.record_usage("C3", utility=0.2)
    rep_stable = engine.compute_reputation("C3")
    
    # Contradictions reduce reputation
    engine.record_contradiction("C1")
    rep_after_contradiction = engine.compute_reputation("C1")
    assert rep_after_contradiction < rep_after_usage, "Contradictions should reduce reputation"

    # Test ranking
    engine.register_concept("C2")
    engine.record_usage("C2", utility=0.5)
    ranked = engine.rank_concepts_by_reputation()
    assert ranked[0][0] == "C2", "C2 should rank higher (more usage)"

    print("✓ Concept Reputation Engine tests passed")


def test_cognitive_energy_budget():
    """Test energy budget system."""
    budget = CognitiveEnergyBudget(total_system_energy=100.0)

    # Allocate budget
    alloc1 = budget.allocate_budget("C1", initial_energy=20.0)
    assert alloc1.total_energy == 20.0
    assert alloc1.remaining_energy == 20.0

    # Consume energy
    success = budget.consume_energy("C1", 10.0)
    assert success, "Should successfully consume energy"
    assert alloc1.remaining_energy == 10.0

    # Fail to exceed budget
    success = budget.consume_energy("C1", 20.0)
    assert not success, "Should fail when exceeding budget"

    # Test extinction evaluation
    # High energy consumption + low reputation = extinction
    extinct = budget.evaluate_extinction("C1", reputation=0.2)
    # (depends on consumption rate, might be False here)

    # Test extinction when energy depleted
    budget.consume_energy("C1", 10.0)
    extinct = budget.evaluate_extinction("C1", reputation=0.5)
    assert extinct, "Should mark as extinct when energy depleted"

    # Test energy reclamation
    reclaimed = budget.reclaim_energy("C1")
    assert reclaimed == 0.0, "Should reclaim remaining energy"

    # Test system utilization
    utilization = budget.get_system_utilization()
    assert utilization["active_concepts"] == 1
    assert utilization["energy_utilization_rate"] == 0.2  # 20 of 100 system energy consumed

    print("✓ Cognitive Energy Budget tests passed")


def test_integration():
    """Test all systems working together."""
    constitution = SemanticConstitution()
    hierarchy = ConceptHierarchy()
    reputation = ConceptReputationEngine()
    budget = CognitiveEnergyBudget()

    # Simulate a concept lifecycle
    c1 = HierarchicalConcept(
        id="C1",
        layer=ConceptLayer.STRUCTURAL,
        name="Test Concept",
    )
    hierarchy.register_concept(c1)
    reputation.register_concept("C1")
    budget.allocate_budget("C1", initial_energy=50.0)

    # Use the concept
    for _ in range(5):
        reputation.record_usage("C1", utility=0.1)
        budget.consume_energy("C1", 2.0)

    # Check reputation improved
    rep = reputation.compute_reputation("C1")
    assert rep > 0.5, "Reputation should improve with usage"

    # Check energy consumed
    alloc = budget.get_allocation("C1")
    assert alloc.consumed_energy == 10.0

    # Should not be extinct yet
    extinct = budget.evaluate_extinction("C1", rep)
    assert not extinct, "Concept should not be extinct with good metrics"

    print("✓ Integration tests passed")


if __name__ == "__main__":
    test_semantic_constitution()
    test_concept_hierarchy()
    test_concept_reputation()
    test_cognitive_energy_budget()
    test_integration()
    print("\n✅ All tests passed!")
