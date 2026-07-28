from runtime.capability_intelligence.operational_economy_analysis import (
    OperationalEconomyAnalysis,
)


def test_operational_economy_measures_attrition_and_crisis_state():
    report = OperationalEconomyAnalysis().analyze(
        generated_concepts=100,
        generated_programs=50,
        candidate_count=30,
        arena_candidate_count=10,
        compiled_programs=2,
        validated_programs=1,
        materialized_operational_capabilities=0,
        operational_citizen_count=1,
        expected_operational_capability_count=13,
        known_operational_capability_count=2,
        operational_experience_count=78,
        candidate_attrition_summary={
            "rejected_before_arena": 5,
            "rejection_reasons": {
                "compiler_support_missing": 3,
                "execution_package_missing": 2,
            },
        },
        capability_ecology_report={
            "composite_capability_candidates": [
                {
                    "composite_name": "Topology Preserving Translation",
                    "required_capabilities": [
                        "translate",
                        "preserve_topology",
                        "preserve_colors",
                    ],
                    "present_capabilities": [
                        "translate",
                        "preserve_topology",
                        "preserve_colors",
                    ],
                    "missing_capabilities": [],
                    "participating_domains": ["Spatial", "Topology", "Color"],
                    "composition_readiness": 1.0,
                }
            ],
        },
        capability_population_evolution_lag=0.8462,
        crystallization_candidate_count=0,
        high_value_knowledge_items=10,
        medium_value_knowledge_items=15,
        low_value_knowledge_items=5,
    )

    assert report["knowledge_attrition_lifecycle"][0]["from_stage"] == (
        "generated_concepts"
    )
    assert report["operational_economy_bottleneck"] == (
        "validated_programs->materialized_operational_capabilities"
    )
    assert report["candidate_attrition_cost"] == 5
    assert report["capability_economy_crisis_state"] == "CAPABILITY_ECONOMY_CRISIS"
    assert report["operational_capability_clusters"][0]["cluster_state"] == (
        "OPERATIONAL_CLUSTER_READY"
    )
    assert report["operational_capability_clusters"][0]["required_grounding"][0][
        "required_evidence"
    ] == "exact_or_governed_validation_success"
    assert report["operational_capability_clusters"][0]["required_grounding"][0][
        "required_task_property"
    ] == "unambiguous_directional_translation_ground_truth"
    assert report["operational_cluster_readiness"] == 1.0
    assert report["ready_operational_cluster_count"] == 1
    assert report["cluster_operationalization_state"] == (
        "READY_CLUSTERS_AWAITING_MATERIALIZATION"
    )
    assert report["cluster_operationalization_action"] == (
        "TARGET_CLUSTER_VALIDATION_AND_GROUNDING"
    )
    assert report["cluster_to_materialization_gap"] == 1
    assert report["knowledge_to_citizen_efficiency"] == 0.01


def test_operational_economy_keeps_clusters_as_diagnostics_only():
    report = OperationalEconomyAnalysis().analyze(
        generated_concepts=10,
        generated_programs=8,
        candidate_count=6,
        arena_candidate_count=5,
        compiled_programs=4,
        validated_programs=3,
        materialized_operational_capabilities=2,
        operational_citizen_count=2,
        capability_ecology_report={
            "composite_capability_candidates": [
                {
                    "composite_name": "Identity Preserving Transformation",
                    "required_capabilities": ["preserve_grid", "translate"],
                    "present_capabilities": ["preserve_grid"],
                    "missing_capabilities": ["translate"],
                    "composition_readiness": 0.5,
                }
            ],
        },
    )

    assert report["operational_cluster_count"] == 1
    assert report["operational_capability_clusters"][0]["cluster_state"] == (
        "PARTIAL_OPERATIONAL_CLUSTER"
    )
    assert "capability_type" not in report["operational_capability_clusters"][0]
    assert "required_grounding" in report["operational_capability_clusters"][0]
    assert report["knowledge_crystallization_efficiency"] is None
    assert report["operational_economy_health"] <= 1.0


def test_ready_clusters_without_citizens_require_operationalization():
    report = OperationalEconomyAnalysis().analyze(
        generated_concepts=18,
        generated_programs=15,
        candidate_count=13,
        arena_candidate_count=8,
        compiled_programs=1,
        validated_programs=0,
        materialized_operational_capabilities=0,
        operational_citizen_count=0,
        operational_grounding_failure_count=13,
        operational_grounding_failure_rate=1.0,
        capability_ecology_report={
            "composite_capability_candidates": [
                {
                    "composite_name": "Identity Preserving Transformation",
                    "required_capabilities": ["preserve_grid", "translate"],
                    "present_capabilities": ["preserve_grid", "translate"],
                    "missing_capabilities": [],
                    "participating_domains": ["Identity", "Spatial"],
                    "composition_readiness": 1.0,
                },
                {
                    "composite_name": "Topology Preserving Translation",
                    "required_capabilities": [
                        "translate",
                        "preserve_topology",
                        "preserve_colors",
                    ],
                    "present_capabilities": [
                        "translate",
                        "preserve_topology",
                        "preserve_colors",
                    ],
                    "missing_capabilities": [],
                    "participating_domains": ["Topology", "Spatial", "Color"],
                    "composition_readiness": 1.0,
                },
            ],
        },
    )

    assert report["ready_operational_cluster_count"] == 2
    assert report["cluster_operationalization_candidate_count"] == 2
    assert report["cluster_to_materialization_gap"] == 2
    assert report["cluster_to_citizen_gap"] == 2
    assert report["cluster_operationalization_pressure"] == 1.0
    assert report["cluster_operationalization_state"] == (
        "READY_CLUSTERS_BLOCKED_BY_OPERATIONALIZATION"
    )
    assert report["cluster_operationalization_action"] == (
        "CLUSTER_OPERATIONALIZATION_REQUIRED"
    )
    assert any(
        row["priority"] == "cluster_operationalization"
        for row in report["operational_economy_roadmap"]
    )
    assert report["knowledge_operationalization_choke_point"] == (
        "arena_to_compiled"
    )
    assert report["knowledge_operationalization_choke_cause"] == (
        "operational_grounding"
    )
    assert report["knowledge_operationalization_choke_action"] == (
        "select_grounding_aligned_validation_tasks"
    )
    assert report["knowledge_operationalization_state"] == (
        "SEVERE_KNOWLEDGE_OPERATIONALIZATION_CHOKE"
    )
    assert report["knowledge_operationalization_path"][1]["lost_count"] == 7


def test_validation_probe_insufficiency_overrides_raw_arena_to_compiled_choke():
    report = OperationalEconomyAnalysis().analyze(
        generated_concepts=18,
        generated_programs=15,
        candidate_count=13,
        arena_candidate_count=8,
        compiled_programs=1,
        validated_programs=0,
        materialized_operational_capabilities=0,
        operational_citizen_count=0,
        operational_grounding_failure_count=13,
        operational_grounding_failure_rate=1.0,
        executable_intelligence_report={
            "validation_probe_admission_state": "VALIDATION_PROBE_COMPILED",
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
            "validation_probe_compiled_programs": 1,
            "validation_probe_evidence_acceptance_evaluated": True,
            "validation_probe_evidence_acceptance_state": "INSUFFICIENT",
            "validation_probe_evidence_insufficiency_cause": (
                "missing_object_grounding"
            ),
            "validation_probe_required_evidence": (
                "grounded_target_object_evidence"
            ),
            "validation_probe_recommended_validation_action": (
                "select_object_grounded_validation_task"
            ),
        },
        candidate_arena_report={
            "selection_state": "NO_SAFE_WINNER",
            "selection_explanation": (
                "Prediction quality below minimum threshold."
            ),
            "winner_selected_from_evidence": False,
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
            "prediction_quality_calibration_state": (
                "PREDICTION_QUALITY_CALIBRATION_GAP"
            ),
        },
    )

    assert report["knowledge_operationalization_choke_point"] == (
        "validation_evidence_grounding"
    )
    assert report["knowledge_operationalization_choke_cause"] == (
        "missing_object_grounding"
    )
    assert report["knowledge_operationalization_choke_action"] == (
        "select_object_grounded_validation_task"
    )
    assert report["knowledge_operationalization_evidence_responsibility"] == (
        "OBJECT_GROUNDING_LAYER"
    )
    assert report["knowledge_operationalization_required_evidence"] == (
        "grounded_target_object_evidence"
    )
    assert report["arena_to_compiled_admission_state"] == (
        "VALIDATION_PROBE_COMPILATION_AVAILABLE"
    )
    assert report["execution_compiled_program_count"] == 0
    assert report["validation_probe_compiled_program_count"] == 1
    assert report["arena_to_validation_compilation_rate"] == 0.125
    assert report["execution_compilation_admission_state"] == (
        "NO_EXECUTION_CANDIDATE_ADMITTED"
    )
    assert report["execution_compilation_admission_reason"] == "no_safe_winner"
    assert report["execution_compilation_admission_action"] == (
        "calibrate_prediction_quality_before_execution_admission"
    )
    assert "selection_state=NO_SAFE_WINNER" in report[
        "execution_compilation_blockers"
    ]
    assert "winner_selected_from_evidence=FALSE" in report[
        "execution_compilation_blockers"
    ]
    assert "validation_probe_authority=SANDBOX_VALIDATION_ONLY" in report[
        "execution_compilation_blockers"
    ]
    assert "execution_compiled_programs=0" in report[
        "execution_compilation_blockers"
    ]
    assert "validation_probe_compiled_programs=1" in report[
        "execution_compilation_blockers"
    ]
    compiled_to_validated = report["knowledge_operationalization_path"][2]
    assert compiled_to_validated["stage"] == "compiled_to_validated"
    assert compiled_to_validated["likely_cause"] == "missing_object_grounding"
    assert compiled_to_validated["action"] == "select_object_grounded_validation_task"
    assert compiled_to_validated["evidence_responsibility"] == "OBJECT_GROUNDING_LAYER"
    assert compiled_to_validated["required_evidence"] == (
        "grounded_target_object_evidence"
    )
