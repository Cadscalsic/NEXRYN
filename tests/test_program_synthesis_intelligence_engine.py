from runtime.synthesis import ProgramSynthesisIntelligenceEngine


def _concept_report():
    return {
        "CONCEPT_FORMATION_REPORT": True,
        "discovered_concepts": [
            {
                "concept_id": "concept:color",
                "concept_name": "color_correspondence_pattern",
                "concept_category": "attribute_cognition",
                "concept_type": "symbolic_correspondence",
                "confidence": 0.86,
                "utility": 0.82,
                "generalization_score": 0.74,
                "truth_support": 0.5,
                "search_support": 0.4,
                "lifecycle": "VALIDATED",
            },
            {
                "concept_id": "concept:shape",
                "concept_name": "shape_equivalence_pattern",
                "concept_category": "structural_cognition",
                "concept_type": "structural_pattern",
                "confidence": 0.8,
                "utility": 0.76,
                "generalization_score": 0.7,
                "lifecycle": "SUPPORTED",
            },
            {
                "concept_id": "concept:spatial",
                "concept_name": "spatial_translation_pattern",
                "concept_category": "spatial_cognition",
                "concept_type": "spatial_pattern",
                "confidence": 0.78,
                "utility": 0.72,
                "generalization_score": 0.79,
                "lifecycle": "SUPPORTED",
            },
        ],
        "concept_graph": {
            "nodes": [
                {"id": "concept:color"},
                {"id": "concept:shape"},
                {"id": "concept:spatial"},
            ],
            "edges": [
                {
                    "source": "concept:color",
                    "target": "concept:shape",
                    "relation": "supports",
                }
            ],
        },
    }


def test_program_synthesis_intelligence_generates_validated_programs(tmp_path):
    engine = ProgramSynthesisIntelligenceEngine(
        memory_path=tmp_path / "program_memory.json",
    )

    report = engine.build_report(
        concept_formation_report=_concept_report(),
        cognitive_search_report={
            "route_ranking": [
                {
                    "route_id": "route:1",
                    "current_confidence": 0.82,
                    "expected_future_value": 0.7,
                }
            ]
        },
        dependency_report={"dependency_chain_depth": 2},
        causal_report={"causal_context_count": 1},
        all_results=[
            {
                "task": "task_a",
                "result": {
                    "synthesized_program": {
                        "steps": [{"operation": "replace_color"}],
                        "step_count": 1,
                    }
                },
            }
        ],
    )

    assert report["PROGRAM_SYNTHESIS_REPORT"] is True
    assert report["generated_programs"] > 0
    assert report["program_candidates"] > 0
    assert report["program_graph"]["nodes"]
    assert report["program_graph"]["edges"]
    assert report["program_ranking"]
    assert report["program_validation"]

    program = report["generated_program_objects"][0]
    assert program["required_concepts"]
    assert program["generalization_score"] > 0
    assert program["execution_strategy"]["steps"]
    assert program["validation_results"]
    assert program["lifecycle"] in {
        "DISCOVERED",
        "CANDIDATE",
        "COMPOSED",
        "VALIDATED",
        "PROMOTED",
        "REUSED",
        "GENERALIZED",
        "STABLE",
        "DEPRECATED",
        "ARCHIVED",
    }


def test_program_synthesis_memory_tracks_reuse(tmp_path):
    memory_path = tmp_path / "program_memory.json"
    engine = ProgramSynthesisIntelligenceEngine(memory_path=memory_path)

    first = engine.build_report(concept_formation_report=_concept_report())
    second = engine.build_report(concept_formation_report=_concept_report())

    assert first["program_reuse"]["new_count"] > 0
    assert second["program_reuse"]["reused_count"] > 0
    assert memory_path.exists()
