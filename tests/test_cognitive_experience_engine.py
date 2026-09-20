from runtime.experience import ExperienceEngine


def _engine(tmp_path):
    return ExperienceEngine(tmp_path / "experiences")


def _semantic_report():
    return {
        "SEMANTIC_INTEGRATION_REPORT": True,
        "discovered_domains": ["Geometry", "Color Theory"],
        "canonical_concepts": [
            {
                "semantic_id": "semantic:spatial",
                "canonical_name": "Spatial Transformation",
                "domain": "Geometry",
                "confidence": 0.84,
            },
            {
                "semantic_id": "semantic:color",
                "canonical_name": "Color Mapping",
                "domain": "Color Theory",
                "confidence": 0.8,
            },
        ],
        "semantic_clusters": [
            {"cluster_name": "Spatial Transformation", "members": ["concept:rotate", "concept:mirror"]},
            {"cluster_name": "Color Mapping", "members": ["concept:blue-green"]},
        ],
        "ontology_growth": {"abstractions_created": 2, "domains_discovered": 2},
        "semantic_confidence": 0.82,
        "generalization_quality": 0.78,
        "dna_integration": {
            "semantic_domain_traits": {
                "Geometry": "increase_exploration_bias",
                "Color Theory": "increase_transformation_reuse",
            }
        },
        "recommendations": ["Promote stable abstractions."],
    }


def test_experience_engine_builds_one_complete_reusable_experience(tmp_path):
    engine = _engine(tmp_path)

    report = engine.build_report(
        task_identity="arc:spatial-color-task",
        execution_id="execution:001",
        execution_report={"success": True, "execution_time": 0.12, "execution_profile": "deep"},
        reasoning_report={"reasoning_depth": 3, "reasoning_graph": {"nodes": ["reason:a"]}},
        search_report={
            "cognitive_routes": {
                "route:a": {"route_id": "route:a", "current_confidence": 0.76}
            },
            "route_decisions": [{"route_id": "route:a", "decision": "keep"}],
        },
        concept_report={
            "discovered_concepts": [
                {"concept_id": "concept:rotate", "concept_name": "Rotate", "confidence": 0.86},
                {"concept_id": "concept:blue-green", "concept_name": "Blue to green", "confidence": 0.8},
            ],
        },
        program_report={
            "generated_program_objects": [
                {
                    "program_id": "program:spatial-color",
                    "program_name": "Spatial color solver",
                    "confidence": 0.82,
                    "generalization_score": 0.72,
                    "complexity": 0.24,
                }
            ],
            "winning_programs": [{"program_id": "program:spatial-color"}],
        },
        acsc_report={"thermal_decisions": [{"route_id": "route:a", "temperature": "cool"}]},
        evidence_report={
            "evidence_objects": [
                {"id": "evidence:a", "confidence": 0.88, "reliability": 0.84}
            ]
        },
        knowledge_report={
            "knowledge_object_count": 8,
            "SEMANTIC_INTEGRATION_REPORT": _semantic_report(),
            "knowledge_consolidation": {"repeated_knowledge_compressed": 1},
        },
        truth_report={
            "truth_candidates": [{"truth_id": "truth:a", "confidence": 0.83}],
            "validated_truths": [{"truth_id": "truth:a", "confidence": 0.83}],
        },
        memory_report={"reuse_rate": 0.6, "memory_promotions": ["semantic:spatial"]},
        situation_report={
            "current_goal": "solve spatial color task",
            "confidence": 0.81,
            "situation_stability": 0.75,
            "situation_complexity": 0.45,
            "final_situation": {"outcome": "resolved"},
        },
        policy_report={
            "selected_policy": {"policy_id": "policy:deep-investigation"},
            "rejected_policies": [{"policy_id": "policy:low-resource"}],
        },
        decision_report={
            "selected_decision": {"decision_id": "decision:spatial"},
            "candidate_decisions": [{"decision_id": "decision:spatial"}],
            "rejected_alternatives": [{"decision_id": "decision:memory-only"}],
            "decision_confidence": 0.79,
        },
        analytics_report={
            "overall_cognitive_intelligence_score": 0.77,
            "recommended_actions": ["Reuse this pattern for similar tasks."],
        },
        governance_report={
            "execution_intent": {
                "Goal": "solve spatial color task",
                "Confidence Target": 0.8,
            },
            "runtime_budgets": {"search_runtime": 3},
        },
        world_model_report={"committed_updates": ["experience:spatial-color"]},
        dna_report={"traits": {"Geometry": "spatial_bias"}},
    )

    experience = report["experience"]

    assert report["COGNITIVE_EXPERIENCE_REPORT"] is True
    assert report["experience_count"] == 1
    assert report["exactly_one_experience_per_execution"] is True
    assert experience["execution_id"] == "execution:001"
    assert experience["task_identity"] == "arc:spatial-color-task"
    assert set(experience["semantic_domains"]) == {"Geometry", "Color Theory"}
    assert experience["concepts"]
    assert experience["programs"]
    assert experience["evidence"]
    assert experience["truth"]
    assert experience["policies_used"]
    assert experience["decisions_taken"]
    assert experience["search_routes"]
    assert experience["success_state"] == "success"
    assert report["semantic_abstractions"]["canonical_concepts"]
    assert report["mental_model_updates"]
    assert report["world_model_updates"]["world_model_stores_experiences"] is True
    assert report["dna_updates"]["experience_driven_dna"] is True
    assert report["meta_cognitive_reflection"]["should_be_remembered"] is True
    assert report["experience_graph"]["nodes"]
    assert report["experience_reusability_score"] > 0
    assert report["storage"]["stored"] is True
    assert report["runtime_alignment"]["duplicates_memory_runtime"] is False
    assert report["runtime_alignment"]["replaces_truth_runtime"] is False


def test_experience_retrieval_uses_complete_experiences_for_transfer(tmp_path):
    engine = _engine(tmp_path)
    first = engine.build_report(
        task_identity="arc:spatial-color-task",
        execution_id="execution:first",
        execution_report={"success": True},
        semantic_report=_semantic_report(),
        concept_report={"discovered_concepts": [{"concept_id": "concept:rotate"}]},
        program_report={"generated_program_objects": [{"program_id": "program:rotate"}]},
        truth_report={"validated_truths": [{"truth_id": "truth:rotate", "confidence": 0.8}]},
        situation_report={"confidence": 0.8},
    )

    second = engine.build_report(
        task_identity="arc:spatial-color-variant",
        execution_id="execution:second",
        execution_report={"success": True},
        semantic_report=_semantic_report(),
        concept_report={"discovered_concepts": [{"concept_id": "concept:mirror"}]},
        program_report={"generated_program_objects": [{"program_id": "program:mirror"}]},
        truth_report={"validated_truths": [{"truth_id": "truth:mirror", "confidence": 0.78}]},
        situation_report={"confidence": 0.78},
    )

    assert first["storage"]["stored"] is True
    assert second["experience_retrieval"]["retrieved"] is True
    assert second["experience_retrieval"]["ranked_experiences"]
    assert second["experience_graph"]["edges"]
    assert second["transfer_learning_opportunities"]
