from runtime.experience import ExperienceEngine
from runtime.memory import SemanticMemoryEngine, SemanticMemoryRegistry
from runtime.reflection import ReflectionEngine


def _experience_report(tmp_path):
    return ExperienceEngine(tmp_path / "experiences").build_report(
        execution_id="exec:semantic-memory",
        task_identity="geometry symmetry task",
        concept_report={
            "discovered_concepts": [
                {
                    "concept_id": "concept:symmetry",
                    "concept_name": "spatial symmetry",
                    "confidence": 0.84,
                }
            ]
        },
        program_report={
            "generated_program_objects": [
                {
                    "program_id": "program:symmetry",
                    "program_name": "symmetry strategy",
                    "confidence": 0.78,
                }
            ]
        },
        evidence_report={
            "evidence_objects": [
                {
                    "id": "evidence:symmetry",
                    "confidence": 0.86,
                    "reliability": 0.82,
                }
            ]
        },
        truth_report={
            "truth_candidates": [
                {"truth_id": "truth:symmetry", "confidence": 0.91}
            ],
            "validated_truths": [
                {"truth_id": "truth:symmetry", "confidence": 0.91}
            ],
        },
        semantic_report={
            "discovered_domains": ["Geometry"],
            "semantic_confidence": 0.88,
            "canonical_concepts": [{"canonical_name": "Spatial Symmetry"}],
        },
        persist=False,
    )


def _reflection_report():
    reflection = ReflectionEngine().reflect(
        episode={
            "episode_id": "episode:semantic-memory",
            "execution_id": "exec:semantic-memory",
            "episode_status": "CLOSED",
            "episode_outcome": "SUCCESS",
            "episode_summary": "SUCCESS: geometry symmetry episode.",
            "episode_confidence": 0.85,
            "statistics": {
                "object_count": 3,
                "concept_count": 1,
                "evidence_count": 1,
                "truth_count": 1,
            },
            "quality": {"episode_quality": 0.82, "evidence_quality": 0.4, "truth_quality": 0.4},
            "content": {
                "concept_objects": ["concept:symmetry"],
                "evidence_objects": ["evidence:symmetry"],
                "truth_objects": ["truth:symmetry"],
            },
        },
        objects=[
            {
                "object_id": "concept:symmetry",
                "object_type": "CONCEPT",
                "object_confidence": 0.84,
                "semantic_payload": {"domain": "Geometry"},
            },
            {
                "object_id": "evidence:symmetry",
                "object_type": "EVIDENCE",
                "object_confidence": 0.86,
                "evidence_payload": {"reliability": 0.82},
            },
            {
                "object_id": "truth:symmetry",
                "object_type": "TRUTH",
                "object_confidence": 0.91,
            },
        ],
    )
    return reflection.reflection_report


def test_semantic_memory_organizes_experience_and_reflection_into_domains(tmp_path):
    engine = SemanticMemoryEngine()
    report = engine.integrate(
        experience_report=_experience_report(tmp_path),
        reflection_report=_reflection_report(),
    )

    assert report["SEMANTIC_MEMORY_REPORT"] is True
    assert report["Integration Contracts"]["creates_new_runtime"] is False
    assert report["Integration Contracts"]["duplicates_storage"] is False
    assert report["Integration Contracts"]["stores_raw_execution"] is False
    assert report["Integration Contracts"]["stores_organized_meaning"] is True
    assert "Geometry" in report["Domains"]
    assert report["semantic_entity_count"] >= 8
    assert report["Relationships"]
    assert report["Knowledge Hierarchy"]["Knowledge"]["Geometry"]
    assert report["Semantic Clusters"]
    assert report["Graph Statistics"]["node_count"] == report["semantic_entity_count"]
    assert report["Graph Statistics"]["edge_count"] >= 1


def test_semantic_memory_registry_deduplicates_relationships_with_marker_index():
    registry = SemanticMemoryRegistry()
    relationship = {
        "source": "sem:left",
        "target": "sem:right",
        "relationship_type": "Supports",
        "confidence": 0.8,
    }

    registry.add_relationship(relationship)
    registry.add_relationship(relationship)

    assert registry.relationships == [
        {
            "source": "sem:left",
            "target": "sem:right",
            "relationship_type": "Supports",
            "confidence": 0.8,
            "lineage": {},
        }
    ]
    assert len(registry._relationship_markers) == 1


def test_semantic_memory_entities_preserve_context_lineage_and_maturity(tmp_path):
    engine = SemanticMemoryEngine()
    report = engine.integrate(
        experience_report=_experience_report(tmp_path),
        reflection_report=_reflection_report(),
    )

    entities = report["Semantic Entities"]

    assert all(entity["semantic_memory_id"] for entity in entities)
    assert all(entity["semantic_identity"] for entity in entities)
    assert all(entity["semantic_domain"] for entity in entities)
    assert all(entity["semantic_category"] for entity in entities)
    assert all(entity["semantic_level"] for entity in entities)
    assert all(entity["semantic_summary"] for entity in entities)
    assert all(entity["semantic_version"] >= 1 for entity in entities)
    assert all(entity["semantic_history"] for entity in entities)
    assert all(entity["semantic_status"] in {
        "Candidate",
        "Emerging",
        "Stable",
        "Canonical",
        "Fundamental",
        "Deprecated",
        "Archived",
    } for entity in entities)
    assert report["Knowledge Maturity"]["promotion_requires_accumulated_evidence"] is True
    assert report["Semantic Consistency"]["identity_consistency"] is True

    reinforced = engine.integrate(
        experience_report=_experience_report(tmp_path),
        reflection_report=_reflection_report(),
    )
    assert reinforced["Canonical Knowledge"]


def test_semantic_retrieval_is_meaning_domain_and_similarity_based(tmp_path):
    engine = SemanticMemoryEngine()
    engine.integrate(
        experience_report=_experience_report(tmp_path),
        reflection_report=_reflection_report(),
    )

    by_meaning = engine.retrieve(meaning="spatial symmetry", top_k=3)
    by_domain = engine.retrieve(domain="Geometry", top_k=3)
    report = engine.build_report()

    assert by_meaning["semantic_retrieval"] is True
    assert by_meaning["retrieval_mode"] == "semantic_not_chronological"
    assert by_meaning["retrieved_count"] >= 1
    assert by_domain["retrieved_count"] >= 1
    assert report["Retrieval Statistics"]["retrieval_count"] == 2
    assert report["Retrieval Statistics"]["retrieval_by_transfer_potential"] is True


def test_semantic_memory_tracks_compression_differentiation_and_downstream_contracts(tmp_path):
    engine = SemanticMemoryEngine()
    first = engine.integrate(
        experience_report=_experience_report(tmp_path),
        reflection_report=_reflection_report(),
    )
    second = engine.integrate(
        experience_report=_experience_report(tmp_path),
        reflection_report=_reflection_report(),
    )

    assert second["Compression Statistics"]["meaning_preserved"] is True
    assert second["Compression Statistics"]["items_after_compression"] <= second["Compression Statistics"]["items_before_compression"]
    assert second["Differentiation Statistics"]["false_generalization_guard"] is True
    assert second["Evolution Trends"]["history_destroyed"] is False
    assert second["Evolution Trends"]["evolution_cycles"] == 2
    assert second["Integration Contracts"]["mental_models_emerge_from_semantic_memory"] is True
    assert second["Integration Contracts"]["world_model_consumes_semantic_knowledge"] is True
    assert second["Integration Contracts"]["dna_adapts_from_semantic_evolution"] is True
    assert second["Integration Contracts"]["executive_governance_reasons_over_semantic_memory"] is True
    assert first["semantic_entity_count"] == second["semantic_entity_count"]
