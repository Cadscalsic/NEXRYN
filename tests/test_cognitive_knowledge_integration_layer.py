from runtime.knowledge import (
    CognitiveKnowledgeIntegrationLayer,
    CognitiveKnowledgeMemory,
)


def _engine(tmp_path):
    return CognitiveKnowledgeIntegrationLayer(
        memory=CognitiveKnowledgeMemory(tmp_path / "ckil_memory.json"),
    )


def _concept_report():
    return {
        "CONCEPT_FORMATION_REPORT": True,
        "discovered_concepts": [
            {
                "concept_id": "concept:a",
                "concept_name": "stable_concept",
                "confidence": 0.8,
                "utility": 0.75,
                "generalization_score": 0.7,
                "lifecycle": "VALIDATED",
                "supporting_evidence": [{"source": "pattern"}],
            }
        ],
        "top_concepts": [{"concept_id": "concept:a"}],
    }


def _program_report():
    return {
        "PROGRAM_SYNTHESIS_REPORT": True,
        "generated_programs": 1,
        "generated_program_objects": [
            {
                "program_id": "program:a",
                "program_name": "concept_program",
                "required_concepts": ["concept:a"],
                "confidence": 0.76,
                "utility": 0.7,
                "generalization_score": 0.68,
                "complexity": 0.25,
                "lifecycle": "VALIDATED",
                "validation_results": {"correctness": 0.8},
            }
        ],
        "winning_programs": [{"program_id": "program:a"}],
    }


def _route_report():
    return {
        "COGNITIVE_ROUTE_INTELLIGENCE_REPORT": True,
        "cognitive_routes": {
            "route:a": {
                "route_id": "route:a",
                "supporting_concepts": ["concept:a"],
                "supporting_programs": ["program:a"],
                "supporting_truths": [{"source": "truth:a"}],
                "supporting_memory": [{"source": "memory:a"}],
                "supporting_evidence": [{"source": "search"}],
                "current_confidence": 0.72,
                "current_utility": 0.7,
                "generalization_score": 0.64,
                "novelty": 0.4,
                "compression_score": 0.5,
                "proposed_state": "VALIDATED",
                "decision_justification": "route survived",
            }
        },
    }


def _evidence_report():
    return {
        "EVIDENCE_ARCHITECTURE_REPORT": True,
        "evidence_objects": [
            {
                "id": "evidence:a",
                "evidence_type": "transformation_evidence",
                "owner_runtime": "evidence_builder_runtime",
                "supporting_concepts": ["concept:a"],
                "supporting_programs": ["program:a"],
                "supporting_routes": ["route:a"],
                "confidence": 0.82,
                "reliability": 0.78,
                "completeness": 0.74,
                "lifecycle": "PUBLISHED",
            }
        ],
    }


def test_ckil_generates_unified_bus_graph_feedback_and_memory(tmp_path):
    report = _engine(tmp_path).build_report(
        concept_formation_report=_concept_report(),
        program_synthesis_report=_program_report(),
        adaptive_search_intelligence_report={"route_decisions": []},
        cognitive_route_intelligence_report=_route_report(),
        evidence_architecture_report=_evidence_report(),
        truth_report={"truth_candidates": [{"truth_id": "truth:a", "validated": True}]},
        memory_report={"reuse_rate": 0.5},
        reasoning_report={"reasoning_depth": 2},
        all_results=[{"task_id": "task:a", "success": True}],
    )

    assert report["COGNITIVE_KNOWLEDGE_INTEGRATION_REPORT"] is True
    assert report["knowledge_objects"]
    assert report["knowledge_graph"]["nodes"]
    assert report["knowledge_graph"]["edges"]
    assert report["knowledge_feedback"]["closed_loop_feedback"] is True
    assert report["knowledge_consolidation"]
    assert report["memory_growth"]["persistent_cognitive_memory"] is True
    assert report["integration_coverage"]["coverage_score"] == 1.0

    influence = report["influence_summary"]
    assert influence["concepts_influence_programs"] is True
    assert influence["programs_influence_search"] is True
    assert influence["search_influences_evidence"] is True
    assert influence["evidence_influences_knowledge"] is True
    assert influence["knowledge_influences_truth"] is True
    assert influence["search_influences_truth"] is False
    assert influence["truth_consumes_raw_cognitive_artifacts"] is False
    assert influence["truth_consumes_evidence_objects"] is True
    assert influence["truth_updates_concepts"] is True
    assert influence["stable_concepts_enter_memory"] is True
    assert influence["successful_programs_enter_memory"] is True


def test_ckil_memory_retrieval_improves_future_reasoning(tmp_path):
    engine = _engine(tmp_path)

    first = engine.build_report(
        concept_formation_report=_concept_report(),
        program_synthesis_report=_program_report(),
        cognitive_route_intelligence_report=_route_report(),
        evidence_architecture_report=_evidence_report(),
        truth_report={"truth_candidates": [{"truth_id": "truth:a", "validated": True}]},
        memory_report={"reuse_rate": 0.5},
    )
    second = engine.build_report(
        concept_formation_report=_concept_report(),
        program_synthesis_report=_program_report(),
        cognitive_route_intelligence_report=_route_report(),
        evidence_architecture_report=_evidence_report(),
        truth_report={"truth_candidates": [{"truth_id": "truth:a", "validated": True}]},
        memory_report={"reuse_rate": 0.5},
    )

    assert first["memory_growth"]["concept_library_size"] > 0
    assert second["knowledge_reuse"]["reasoning_starts_from_prior_knowledge"] is True
    assert second["knowledge_reuse"]["retrieved_concepts"]
    assert second["knowledge_reuse"]["retrieved_programs"]


def test_ckil_evolves_into_semantic_integration_and_ontology_engine(tmp_path):
    concept_report = {
        "CONCEPT_FORMATION_REPORT": True,
        "discovered_concepts": [
            {
                "concept_id": "concept:rotate-clockwise",
                "concept_name": "Rotate clockwise",
                "confidence": 0.86,
                "utility": 0.8,
                "generalization_score": 0.76,
                "lifecycle": "VALIDATED",
            },
            {
                "concept_id": "concept:mirror-reflection",
                "concept_name": "Mirror reflection",
                "confidence": 0.82,
                "utility": 0.79,
                "generalization_score": 0.74,
                "lifecycle": "VALIDATED",
            },
            {
                "concept_id": "concept:blue-to-green",
                "concept_name": "Blue to green color mapping",
                "confidence": 0.8,
                "utility": 0.75,
                "generalization_score": 0.7,
                "lifecycle": "VALIDATED",
            },
            {
                "concept_id": "concept:object-count",
                "concept_name": "Object count",
                "confidence": 0.78,
                "utility": 0.7,
                "generalization_score": 0.68,
                "lifecycle": "VALIDATED",
            },
        ],
    }
    program_report = {
        "PROGRAM_SYNTHESIS_REPORT": True,
        "generated_program_objects": [
            {
                "program_id": "program:spatial-transform",
                "program_name": "Spatial transformation solver",
                "required_concepts": ["concept:rotate-clockwise", "concept:mirror-reflection"],
                "confidence": 0.81,
                "utility": 0.77,
                "generalization_score": 0.72,
                "complexity": 0.2,
                "lifecycle": "VALIDATED",
            }
        ],
    }

    report = _engine(tmp_path).build_report(
        concept_formation_report=concept_report,
        program_synthesis_report=program_report,
        evidence_architecture_report={
            "evidence_objects": [
                {
                    "id": "evidence:spatial",
                    "evidence_type": "rotation and reflection evidence",
                    "supporting_concepts": ["concept:rotate-clockwise", "concept:mirror-reflection"],
                    "supporting_programs": ["program:spatial-transform"],
                    "confidence": 0.88,
                    "reliability": 0.84,
                    "completeness": 0.8,
                }
            ],
        },
        truth_report={
            "truth_candidates": [
                {
                    "truth_id": "truth:spatial-transformation",
                    "confidence": 0.85,
                    "validated": True,
                    "generalization": 0.78,
                }
            ],
        },
        memory_report={"reuse_rate": 0.6},
    )

    semantic = report["SEMANTIC_INTEGRATION_REPORT"]
    names = {item["canonical_name"] for item in semantic["canonical_concepts"]}

    assert semantic["SEMANTIC_INTEGRATION_REPORT"] is True
    assert "Spatial Transformation" in names
    assert "Color Mapping" in names
    assert "Counting" in names
    assert semantic["semantic_clusters"]
    assert semantic["ontology_tree"]["Geometry"]["Transformation"]["Spatial Transformation"]
    assert semantic["semantic_compression_ratio"] > 0
    assert semantic["semantic_coverage"] == 1.0
    assert semantic["truth_integration"]["truth_validates_abstractions"] is True
    assert semantic["memory_integration"]["memory_stores_abstractions"] is True
    assert semantic["situation_awareness_integration"]["situation_consumes_abstractions"] is True
    assert semantic["decision_intelligence_integration"]["decision_reasons_over_semantic_domains"] is True
    assert semantic["world_governance_integration"]["governance_allocates_by_semantic_domain"] is True
    assert semantic["world_model_integration"]["world_model_stores_semantic_knowledge"] is True
    assert semantic["dna_integration"]["dna_evolves_from_semantic_experience"] is True
    assert any(item["knowledge_type"] == "semantic_abstraction" for item in report["knowledge_objects"])
    assert report["runtime_alignment"]["creates_new_semantic_runtime"] is False
