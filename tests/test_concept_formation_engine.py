from runtime.concepts import CognitiveConceptFormationEngine


def test_concept_formation_engine_creates_evidence_backed_concepts(tmp_path):
    engine = CognitiveConceptFormationEngine(
        memory_path=tmp_path / "concept_memory.json",
    )

    report = engine.build_report(
        all_results=[
            {
                "task": "task_a",
                "result": {
                    "hypotheses": [
                        {
                            "type": "color_transformation",
                            "primitive": "replace_color",
                            "confidence": 0.91,
                            "explanatory_power": 0.88,
                            "search_final_score": 0.77,
                        },
                        {
                            "type": "object_preservation",
                            "primitive": "preserve_objects",
                            "confidence": 0.86,
                            "explanatory_power": 0.82,
                        },
                    ],
                    "evaluation_result": {
                        "success": True,
                        "prediction_accuracy": 0.92,
                    },
                    "synthesized_program": {"step_count": 1},
                },
            }
        ],
        cognitive_search_report={
            "route_ranking": [
                {
                    "route_id": "r1",
                    "current_confidence": 0.87,
                    "expected_future_value": 0.72,
                }
            ],
            "search_space_graph": {
                "nodes": [
                    {
                        "id": "h1",
                        "type": "Hypothesis",
                        "label": "replace_color",
                    }
                ]
            },
        },
        truth_report={"truth_candidate_count": 1},
        memory_report={"context_hits": 1},
        dependency_report={"dependency_chains_executed_count": 1},
        causal_report={"causal_context_count": 1},
        lifecycle_report={
            "concepts": [
                {
                    "concept": "shape_preservation",
                    "confidence": 0.78,
                    "utility": 0.7,
                }
            ]
        },
    )

    assert report["CONCEPT_FORMATION_REPORT"] is True
    assert report["generated_concepts"] > 0
    assert report["concept_count"] > 0
    assert report["concept_cost"] > 0
    assert report["confidence"] > 0
    assert report["concept_graph"]["nodes"]
    assert report["concept_graph"]["edges"]

    concept = report["discovered_concepts"][0]
    assert concept["supporting_evidence"]
    assert concept["confidence"] > 0
    assert concept["utility"] > 0
    assert concept["generalization_score"] > 0
    assert concept["lifecycle"] in {
        "DISCOVERED",
        "CANDIDATE",
        "SUPPORTED",
        "VALIDATED",
        "GENERALIZED",
        "REUSED",
        "STABLE",
        "DOMINANT",
        "DEPRECATED",
        "ARCHIVED",
    }
    assert (
        concept["parent_concepts"]
        or concept["child_concepts"]
        or concept["related_concepts"]
        or report["concept_graph"]["edges"]
    )


def test_concept_formation_memory_tracks_reuse(tmp_path):
    memory_path = tmp_path / "concept_memory.json"
    engine = CognitiveConceptFormationEngine(memory_path=memory_path)
    payload = {
        "all_results": [
            {
                "task": "task_b",
                "result": {
                    "hypotheses": [
                        {
                            "type": "color_transformation",
                            "primitive": "replace_color",
                            "confidence": 0.9,
                            "explanatory_power": 0.8,
                        }
                    ]
                },
            }
        ]
    }

    first = engine.build_report(**payload)
    second = engine.build_report(**payload)

    assert first["concept_memory"]["concept_reuse"]["new_count"] > 0
    assert second["concept_memory"]["concept_reuse"]["reused_count"] > 0
    assert memory_path.exists()
