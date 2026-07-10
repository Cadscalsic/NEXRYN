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
