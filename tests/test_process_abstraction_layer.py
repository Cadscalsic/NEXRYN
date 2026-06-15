from core.concept_lifecycle.concept_maturity import ConceptMaturityTracker
from core.context_discovery import ContextDiscoveryEngine
from core.context_hierarchy import ContextDifferentiationEngine
from core.contextual_truth import ContextualTruthEngine
from core.process_abstraction import ProcessAbstractionLayer
from core.process_context_generation import ProcessContextGenerationEngine
from core.semantic_context import SemanticContextReasoner


PROCESS_CONCEPTS = {
    "growth": (
        "growth_context",
        "Growth Context",
        "topology_expansion",
        "Object count, area, or topology expands while preserving identity "
        "continuity.",
    ),
    "replication": (
        "replication_context",
        "Replication Context",
        "structural_copying",
        "New object instances emerge through structural duplication.",
    ),
    "propagation": (
        "propagation_context",
        "Propagation Context",
        "directional_spread",
        "Structure or information spreads while preserving source lineage.",
    ),
    "topological_growth": (
        "topological_growth_context",
        "Topological Growth Context",
        "topology_expansion",
        "Connectivity complexity increases while local structure remains "
        "stable.",
    ),
    "directional_motion": (
        "directional_motion_context",
        "Directional Motion Context",
        "position_delta",
        "Object position changes according to consistent directional rules.",
    ),
}


def maturity_concept(concept):
    return {
        "concept": concept,
        "used_task_count": 8,
        "used_task_ids": [f"task_{index}" for index in range(8)],
        "independent_success_rate": 0.875,
        "cross_task_support": 0.84,
        "records": [
            {
                "success": index < 7,
                "contradiction_score": 0.05,
                "causal_alignment": 0.90,
            }
            for index in range(8)
        ],
        "identity_strength": 0.75,
    }


def test_process_abstraction_layer_defines_first_class_contexts():
    report = ProcessAbstractionLayer.report()

    assert report["process_context_ready"] is True
    assert report["process_abstraction_count"] == len(PROCESS_CONCEPTS)

    for concept, (
        context_id,
        context_family,
        surface,
        definition,
    ) in PROCESS_CONCEPTS.items():
        abstraction = ProcessAbstractionLayer.get(concept)

        assert abstraction is not None
        assert abstraction.context_id == context_id
        assert abstraction.context_family == context_family
        assert abstraction.surface == surface
        assert abstraction.definition == definition
        assert abstraction.properties
        assert abstraction.capabilities
        assert abstraction.constraints
        assert abstraction.implications
        assert abstraction.transfer_conditions
        assert abstraction.validation_criteria


def test_process_context_generation_engine_generates_context_entities():
    report = ProcessContextGenerationEngine.report()

    assert report["process_context_generation_ready"] is True
    assert report["process_context_count"] == len(PROCESS_CONCEPTS)

    for concept, (
        context_id,
        context_family,
        surface,
        definition,
    ) in PROCESS_CONCEPTS.items():
        generated = ProcessContextGenerationEngine().generate_context(concept)

        assert generated["process_context_generated"] is True
        assert generated["process_context_ready"] is True
        assert generated["concept"] == concept
        assert generated["process_context"] == context_id
        assert generated["context_name"] == context_id
        assert generated["context_family"] == context_family
        assert generated["context_surface"] == surface
        assert generated["definition"] == definition
        assert generated["properties"]
        assert generated["capabilities"]
        assert generated["constraints"]
        assert generated["implications"]
        assert generated["transfer_conditions"]


def test_context_discovery_consumes_process_abstraction_surfaces():
    engine = ContextDiscoveryEngine()

    for concept, (
        context_id,
        context_family,
        surface,
        _definition,
    ) in PROCESS_CONCEPTS.items():
        discovery = engine.discover_context({
            "concept": concept,
            "active_concepts": [concept],
            "task_id": f"task_{concept}",
        })
        signature = discovery["context_signature"]

        assert discovery["semantic_context"] == context_id
        assert discovery["discovered_context"]["context_name"] == context_id
        assert discovery["process_operator"] == concept
        assert discovery["cluster"] == context_family
        assert signature["process_context_surface"] == surface
        assert signature["process_abstraction_ready"] is True
        assert signature["process_context_generated"] is True
        assert signature["process_context_generation"]["process_context"] == (
            context_id
        )
        assert signature["process_abstraction"]["definition"]
        assert surface in signature["native_contexts"]


def test_semantic_context_uses_process_abstraction_definitions():
    reasoner = SemanticContextReasoner()

    for concept, (
        _context_id,
        _context_family,
        surface,
        definition,
    ) in PROCESS_CONCEPTS.items():
        discovery = ContextDiscoveryEngine().discover_context({
            "concept": concept,
            "active_concepts": [concept],
        })
        profile = reasoner.generate_semantic_profile(discovery)
        properties = {
            item["property_name"]
            for item in profile["properties"]
        }

        assert profile["semantic_definition"] == definition
        assert profile["process_abstraction_ready"] is True
        assert profile["process_context_generated"] is True
        assert profile["process_context_generation"]["process_context"] == (
            _context_id
        )
        assert profile["transfer_conditions"]
        assert profile["validation_criteria"]
        assert surface in properties
        assert profile["semantic_context_score"] >= 0.90
        assert profile["semantically_validated"] is True


def test_context_hierarchy_consumes_process_abstraction_roots():
    engine = ContextDifferentiationEngine()

    for concept, (
        context_id,
        _context_family,
        _surface,
        _definition,
    ) in PROCESS_CONCEPTS.items():
        discovery = ContextDiscoveryEngine().discover_context({
            "concept": concept,
            "active_concepts": [concept],
        })
        report = engine.refine_clusters([discovery])
        inheritance = report["inheritance"][0]

        assert inheritance["context"] == context_id
        assert inheritance["parent_context"] is None
        assert inheritance["process_dependency_contexts"]
        assert inheritance["inheritance_integrity"] == 1.0
        assert report["context_hierarchy_score"] >= 0.75
        assert report["hierarchy_ready"] is True
        assert report["hierarchy"]["process_abstraction_layer"][
            "process_context_ready"
        ] is True
        assert report["hierarchy"]["process_context_generation_engine"][
            "process_context_generation_ready"
        ] is True


def test_contextual_truth_exposes_process_abstraction_contexts():
    for concept, (
        _context_id,
        context_family,
        surface,
        _definition,
    ) in PROCESS_CONCEPTS.items():
        discovery = ContextDiscoveryEngine().discover_context({
            "concept": concept,
            "active_concepts": [concept],
        })
        semantic = SemanticContextReasoner().generate_semantic_profile(
            discovery
        )
        hierarchy = ContextDifferentiationEngine().refine_clusters([
            discovery,
        ])
        report = ContextualTruthEngine().generate_contextual_truth_report(
            concept,
            context={
                "context_discovery": discovery,
                "semantic_context": semantic,
                "context_hierarchy": hierarchy,
            },
            causal_validation={"validation_score": 0.92},
            identity_compatibility=0.90,
        )

        assert report["process_abstraction_ready"] is True
        assert report["process_context_generated"] is True
        assert report["process_context_generation"]["process_context"] == (
            _context_id
        )
        assert report["process_context_family"] == context_family
        assert report["process_context_surface"] == surface
        assert report["transfer_conditions"]
        assert report["validation_criteria"]
        assert report["contextual_consistency"] is True


def test_process_abstraction_context_strength_clears_promotion_gate():
    evaluations = []
    for concept in PROCESS_CONCEPTS:
        discovery = ContextDiscoveryEngine().discover_context({
            "concept": concept,
            "active_concepts": [concept],
        })
        semantic = SemanticContextReasoner().generate_semantic_profile(
            discovery
        )
        hierarchy = ContextDifferentiationEngine().refine_clusters([
            discovery,
        ])
        evaluations.append({
            "concept": concept,
            "causal_validation": {
                "promotion_dependency_score": 0.92,
                "dependency_promotion_evidence": {
                    "dependency_confidence": 0.90,
                    "dependency_chain_depth": 5,
                    "dependency_chain_coverage": 1.0,
                    "missing_dependencies": [],
                },
            },
            "context_hierarchy": hierarchy,
            "semantic_context": semantic,
            "contextual_truth_authority": {
                "effective_contextual_truth": 0.86,
                "contextual_truth_supported": True,
            },
            "identity_safe_truth_integration": {
                "identity_continuity": 0.75,
            },
        })

    report = ConceptMaturityTracker().evaluate(
        {
            "concepts": [
                maturity_concept(concept)
                for concept in PROCESS_CONCEPTS
            ],
        },
        {"evaluations": evaluations},
    )

    for concept in report["concepts"]:
        promotion = concept["truth_candidate_promotion"]

        assert promotion["readiness_gates"]["context_strength"] is True
        assert promotion["context_strength"] >= 0.86
        assert promotion["process_abstraction_ready"] is True
        assert promotion["process_context_generated"] is True
        assert promotion["process_context_generation"]["process_context"]
        assert promotion["context_strength_evidence"]["semantic_context"] >= (
            0.90
        )
        assert promotion["context_strength_evidence"]["context_hierarchy"] >= (
            0.75
        )
        assert "promotion_gate_blocked:context_strength" not in (
            promotion["dependency_promotion_blockers"]
        )
