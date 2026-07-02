from runtime.learning.training_report import (
    build_training_report,
    print_training_report,
)


def test_training_report_exposes_compact_results_and_concept_memory(capsys):
    report = build_training_report(
        training_batch={
            "selected_task_count": 2,
        },
        training_assistant_report={
            "completed_cycles": 1,
        },
        multi_task_results=[
            {
                "task": "task_014.json",
                "status": "completed",
                "result": {
                    "large_runtime_context": True,
                    "truth_candidate_report": {
                        "evaluations": [{
                            "concept": "symbolic_remapping",
                            "candidate_state":
                            "ADVANCING_TO_TRUTH_CANDIDATE",
                            "eligible_for_truth_candidate": False,
                            "eligibility_reason":
                            "truth_candidate_metric_gaps",
                            "blocked_metrics": [
                                "contradiction_score",
                            ],
                            "metrics": [{
                                "metric": "contradiction_score",
                                "current_value": 0.14,
                                "threshold": {
                                    "comparator": "<",
                                    "required": 0.10,
                                },
                                "gap": 0.04,
                                "status": "FAILED",
                            }],
                        }],
                    },
                    "epistemic_cognition_report": {
                        "evaluations": [{
                            "concept": "symbolic_remapping",
                            "truth_commit": {
                                "decision": "REMAIN_BELIEF",
                                "reason": "truth_candidate_required",
                                "failed_gates": [
                                    "truth_candidate",
                                ],
                            },
                            "identity_safe_truth_integration": {
                                "integration_state":
                                "AWAITING_TRUTH_CANDIDATE",
                                "failed_checks": [],
                            },
                            "semantic_spine_recovery": {
                                "recovery_state":
                                "WAITING_FOR_TRUTH_CANDIDATE",
                                "recovery_streak": 0,
                                "remaining_recovery_cycles": 3,
                            },
                        }],
                    },
                },
            },
            {
                "task": "task_015.json",
                "status": "failed",
                "error": "example failure",
            },
        ],
        ledger_report={
            "observed_task_count": 2,
            "concepts": [{
                "concept": "symbolic_remapping",
                "used_task_count": 2,
                "used_task_ids": [
                    "data/training/task_014.json",
                    "data/training/task_015.json",
                ],
                "independent_success_rate": 0.5,
            }],
        },
        concept_lifecycle_report={
            "concepts": [{
                "concept": "symbolic_remapping",
                "state": "SUPPORTED",
                "average_contradiction_score": 0.0552,
            }],
        },
    )

    print_training_report(report)
    output = capsys.readouterr().out

    assert report["tasks_selected"] == 2
    assert report["tasks_executed"] == [
        "task_014.json",
        "task_015.json",
    ]
    assert report["successful_tasks"] == 1
    assert report["failed_tasks"] == 1
    assert report["concepts_discovered"] == {
        "symbolic_remapping": 2,
    }
    assert report["concept_memory"]["symbolic_remapping"]["task_ids"] == [
        "data/training/task_014.json",
        "data/training/task_015.json",
    ]
    assert report["concept_memory"]["symbolic_remapping"][
        "lifecycle_state"
    ] == "DISCOVERING"
    assert report["truth_candidate_evaluations"] == {}
    assert report["concept_memory"]["symbolic_remapping"][
        "ledger_average_contradiction_score"
    ] == 0.0552
    assert report["truth_commit_evaluations"] == {}
    assert "RUNTIME INTELLIGENCE DASHBOARD" in output
    assert "CONCEPT REPORT" in output
    assert "FAILURES" in output
    assert "'concept_name': 'symbolic_remapping'" in output
    assert "TRUTH REPORT" in output
    assert "RECOMMENDATIONS" in output
    assert "CACHE REPORT" in output
    assert "'current_stage': 'DISCOVERING'" in output
    assert "'contradiction_score': 0.0552" in output
    assert "effective_contradiction=0.14" not in output
    assert "contradiction_threshold=0.1" not in output
    assert "dict_keys" not in output
    assert "large_runtime_context" not in output


def test_training_report_minimal_prints_compact_concept_report(capsys):
    report = build_training_report(
        training_batch={"selected_task_count": 1},
        multi_task_results=[{"task": "task_014.json", "status": "completed"}],
        ledger_report={
            "concepts": [{
                "concept": "replication",
                "used_task_count": 8,
                "used_task_ids": ["data/training/task_014.json"],
                "independent_success_rate": 0.93,
            }],
        },
        concept_lifecycle_report={
            "promotion_report": [{
                "concept": "replication",
                "promotion_score": 0.93,
                "current_stage": "TRUTH_CANDIDATE",
                "candidate_ready": True,
                "blocked_reason": None,
            }],
        },
    )

    print_training_report(report, report_level="minimal")
    output = capsys.readouterr().out

    assert "RUNTIME INTELLIGENCE DASHBOARD" in output
    assert "CONCEPT REPORT" in output
    assert "'concept_name': 'replication'" in output
    assert "TRUTH CANDIDATE REPORT" not in output
    assert "effective_contradiction=" not in output


def test_training_report_prints_curriculum_coverage_report(capsys):
    report = build_training_report(
        curriculum_coverage_report={
            "total_tasks": 12,
            "generated_tasks": 4,
            "concept_count": 8,
            "covered_concepts": ["containment", "path_finding"],
            "missing_concepts": [],
            "coverage_percentage": 1.0,
            "frontier_concepts": ["causal_reasoning"],
            "topology_tasks": 3,
            "containment_tasks": 2,
            "occlusion_tasks": 1,
            "path_reasoning_tasks": 2,
            "scaling_tasks": 1,
            "multi_concept_tasks": 5,
            "curriculum_balance_score": 0.91,
        },
    )

    print_training_report(report)
    output = capsys.readouterr().out

    assert "RUNTIME INTELLIGENCE DASHBOARD" in output
    assert "TASK MANAGER" in output
    assert "CACHE REPORT" in output
    assert "TRUTH REPORT" in output


def test_training_report_prints_selection_diversity_report(capsys):
    report = build_training_report(
        training_batch={
            "selected_task_count": 2,
            "selection_diversity_report": {
                "total_available_tasks": 40,
                "selected_tasks": ["task_011.json", "task_022.json"],
                "selection_mode": "weighted_random",
                "random_seed": 123,
                "previous_batch_overlap_count": 0,
                "unseen_tasks_selected": 2,
                "cooldown_filtered_tasks": 6,
                "average_task_selection_frequency": 0.0,
                "repeated_task_penalty_applied": False,
                "diversity_score": 1.0,
            },
        },
    )

    print_training_report(report)
    output = capsys.readouterr().out

    assert "RUNTIME INTELLIGENCE DASHBOARD" in output
    assert "TASK MANAGER" in output
    assert "CACHE REPORT" in output
    assert "TRUTH REPORT" in output
    assert "RECOMMENDATIONS" in output


def test_training_report_counts_incomplete_tasks(capsys):
    report = build_training_report(
        training_batch={"selected_task_count": 1},
        multi_task_results=[{
            "task": "task_057.json",
            "status": "incomplete",
            "result": {
                "evaluation_result": {
                    "success_state": "PREDICTION_NOT_PRODUCED",
                    "task_status": "TASK_INCOMPLETE",
                },
            },
        }],
    )

    print_training_report(report, report_level="minimal")
    output = capsys.readouterr().out

    assert report["successful_tasks"] == 0
    assert report["failed_tasks"] == 0
    assert report["incomplete_tasks"] == 1
    assert "'incomplete': 1" in output
    assert "'total': 1" in output


def test_training_report_preserves_context_candidate_in_discovery_mode():
    report = build_training_report(
        ledger_report={
            "concepts": [{
                "concept": "shape_preservation",
                "used_task_count": 125,
                "used_task_ids": [
                    f"data/training/task_{index:03d}.json"
                    for index in range(1, 126)
                ],
                "independent_success_rate": 0.824,
            }],
        },
        concept_lifecycle_report={
            "concepts": [{
                "concept": "shape_preservation",
                "state": "CONTEXT_CANDIDATE",
                "used_task_count": 125,
                "preliminary_truth_candidate_ready": False,
                "truth_candidate_promotion": {
                    "candidate_ready": False,
                    "context_candidate_ready": True,
                    "promotion_score": 0.82,
                    "promotion_dependency_score": 0.8848,
                    "promotion_dependency_bonus": 0.02,
                    "dependency_confidence": 0.8848,
                    "dependency_chain_depth": 5,
                    "dependency_chain_coverage": 0.9908,
                    "missing_dependencies": [],
                    "epistemic_graduation": {
                        "promotion_score": 0.82,
                        "promotion_stage": "PROCESS_CONTEXT",
                        "next_stage": "TRUTH_CANDIDATE",
                        "blocked_metrics": [
                            "context_support",
                        ],
                        "thresholds": {
                            "observation_saturation": 32,
                            "maximum_contradiction_rate": 0.10,
                            "TRUTH_CANDIDATE": 0.90,
                        },
                        "next_required_evidence": [{
                            "metric": "promotion_score",
                            "current_value": 0.82,
                            "required": 0.90,
                        }],
                    },
                    "failed_gates": [
                        "context_strength",
                    ],
                },
            }],
        },
        include_truth_evaluations=False,
    )

    memory = report["concept_memory"]["shape_preservation"]

    assert memory["lifecycle_state"] == "CONTEXT_CANDIDATE"
    assert memory["context_candidate_ready"] is True
    audit = report["concept_advancement_audit"]["shape_preservation"]
    assert audit["promotion_score"] == 0.82
    assert audit["promotion_score_required_next"] == 0.90
    assert audit["context_block"] is True
    assert audit["missing_promotion_score"] is False
    assert audit["missing_epistemic_graduation"] is False
    assert report["truth_candidate_evaluations"] == {}
    assert report["architecture_bottleneck_report"][
        "promotion_dependency_score"
    ] == 0.8848


def test_training_report_counts_lifecycle_generated_contexts():
    report = build_training_report(
        concept_lifecycle_report={
            "generated_contexts": [
                {
                    "context_id": "process_context:replication",
                    "context_name": "replication_process_context",
                    "context_type": "PROCESS_CONTEXT",
                    "concept": "replication",
                    "confidence": 0.9062,
                    "context_confidence": 0.9062,
                    "preconditions": ["concept_observed_across_tasks"],
                    "transitions": ["dependency_supported_behavior"],
                    "expected_outcomes": ["reusable_process_explanation"],
                    "process_context_generated": True,
                },
                {
                    "context_id": "semantic_context:replication",
                    "context_name": "replication_semantic_context",
                    "context_type": "SEMANTIC_CONTEXT",
                    "concept": "replication",
                    "confidence": 0.9062,
                    "semantic_definition":
                    "replication supported by promoted evidence",
                },
                {
                    "context_id": "dependency_surface:replication",
                    "context_name": "replication_dependency_surface",
                    "context_type": "DEPENDENCY_SURFACE",
                    "concept": "replication",
                    "confidence": 0.9062,
                    "dependency_confidence": 0.8848,
                    "dependency_chain_coverage": 0.9908,
                },
            ],
        },
    )

    architecture = report["architecture_bottleneck_report"]

    assert architecture["context_count"] == 1
    assert architecture["semantic_context_count"] == 1
    assert report["context_discovery_reports"]["replication"][
        "process_context_generated"
    ] is True
    assert report["semantic_context_reports"][
        "replication_semantic_context"
    ]["semantic_context_score"] == 0.9062
    assert report["context_hierarchy_reports"][
        "replication_dependency_surface"
    ]["hierarchy_ready"] is True


def test_training_report_consumes_discovered_context_for_truth_admission():
    report = build_training_report(
        concept_lifecycle_report={
            "concepts": [{
                "concept": "replication",
                "state": "CANDIDATE",
                "promotion_stage": "CANDIDATE",
                "used_task_count": 29,
                "candidate_ready": True,
                "preliminary_truth_candidate_ready": True,
                "eligible_for_context": True,
                "truth_candidate_promotion": {
                    "concept": "replication",
                    "candidate_ready": True,
                    "promotion_score": 0.9157,
                    "promotion_stage": "CANDIDATE",
                    "eligible_for_truth_candidate": False,
                    "stage_eligible_for_truth_candidate": True,
                    "blocked_metrics": [],
                },
            }],
            "generated_contexts": [{
                "context_id": "replication_process_context",
                "context_name": "replication",
                "context_type": "PROCESS_CONTEXT",
                "concept": "replication",
                "confidence": 0.9157,
                "preconditions": ["candidate_ready"],
                "transitions": ["candidate_to_process_context"],
                "expected_outcomes": ["truth_candidate_context_support"],
            }],
            "promotion_report": [{
                "concept": "replication",
                "promotion_score": 0.9157,
                "current_stage": "CANDIDATE",
                "next_stage": "PROCESS_CONTEXT",
                "candidate_ready": True,
                "blocked_reason": None,
            }],
        },
        include_truth_evaluations=True,
    )

    candidate = report["truth_candidate_evaluations"]["replication"]
    context = report["context_discovery_reports"]["replication"]
    promotion = report["concept_lifecycle"]["promotion_report"][0]

    assert candidate["context_strength"] == 0.9157
    assert candidate["context_strength_source"] == "context_scoring_pipeline"
    assert candidate["semantic_context"]["semantic_context_score"] == 0.9157
    assert candidate["context_hierarchy"]["context_hierarchy_score"] == 0.9157
    assert (
        candidate["contextual_truth"]["contextual_truth_score"]
        >= 0.91
    )
    assert candidate["eligible_for_truth_candidate"] is True
    assert (
        candidate["eligibility_reason"]
        == "context_scored_truth_candidate_admission"
    )
    assert context["context_name"] == "replication"
    assert context["transformation_family"] == "replication"
    assert len(context["transition_family"]) == 1
    assert len(context["preconditions"]) == 1
    assert len(context["expected_outcomes"]) == 1
    assert promotion["current_stage"] == "TRUTH_CANDIDATE"
    assert promotion["next_stage"] == "ESTABLISHED_TRUTH"
    assert "replication" in report["contextual_truth_reports"]


def test_training_report_normalizes_semantic_context_and_prints_string_properties(capsys):
    report = build_training_report(
        concept_lifecycle_report={
            "generated_contexts": [{
                "context_id": "semantic_context:replication",
                "context_name": "replication_process_context",
                "context_type": "SEMANTIC_CONTEXT",
                "concept": "replication",
                "confidence": 0.91,
                "semantic_definition": "replication context",
                "properties": ["creates_objects", "preserves_shape"],
            }],
        },
    )

    semantic = report["semantic_context_reports"]["replication_process_context"]

    assert semantic["context"]["context_id"] == "replication_process_context"
    assert semantic["context"]["context_type"] == "SEMANTIC_CONTEXT"

    print_training_report(report)
    output = capsys.readouterr().out

    assert "CONTEXT REPORT" in output
    assert "'semantic_context_count': 1" in output
    assert "CONTEXT PRINT FAILURE" not in output


def test_training_report_exposes_locked_truth_review_snapshot(capsys):
    report = build_training_report(
        multi_task_results=[{
            "task": "task_016.json",
            "status": "completed",
            "result": {
                "truth_candidate_report": {
                    "evaluations": [{
                        "concept": "topology_preservation",
                        "candidate_state": "TRUTH_STATE_LOCKED",
                        "eligible_for_truth_candidate": True,
                        "eligibility_reason":
                        "stable_truth_authority_locked",
                        "metrics": [],
                        "blocked_metrics": [],
                        "effective_contradiction_score": 0.1114,
                        "contradiction_threshold": 0.10,
                        "contradiction_gap": 0.0114,
                        "contradiction_review_required": True,
                        "contradiction_review_zone": 0.02,
                        "within_soft_review_zone": True,
                        "contradiction_review_severity":
                        "LOW_RISK_REVIEW",
                    }],
                },
                "epistemic_cognition_report": {
                    "evaluations": [{
                        "concept": "topology_preservation",
                        "truth_commit": {
                            "decision":
                            "TRUTH_REVOCATION_REVIEW_REQUIRED",
                            "metadata": {
                                "identity_governance_state":
                                "TEMPORARY_RECOVERY_HOLD",
                                "failed_identity_governance_gates": [
                                    "semantic_spine_stable",
                                ],
                                "final_commit_decision": {
                                    "final_commit_state":
                                    "LOCKED_TRUTH_REVIEW_REQUIRED",
                                    "effective_failed_gates": [
                                        "contradiction_below_limit",
                                    ],
                                    "forbid_automatic_truth_revocation":
                                    True,
                                    "revocation_severity":
                                    "LOW_RISK_REVIEW",
                                },
                            },
                        },
                        "semantic_spine_recovery": {
                            "recovery_state":
                            "REHEARSAL_VALIDATION_REQUIRED",
                            "rehearsal_validation_pending": True,
                            "recovery_blocker_type":
                            "VALIDATED_REVERSIBLE_REHEARSAL_PENDING",
                        },
                    }],
                },
            },
        }],
    )

    print_training_report(report)
    output = capsys.readouterr().out
    assert report["truth_candidate_evaluations"] == {}
    assert report["truth_commit_evaluations"] == {}
    assert "contradiction_review_required=True" not in output
    assert "within_soft_review_zone=True" not in output
    assert "rehearsal_validation_pending=True" not in output
    assert "revocation_severity=LOW_RISK_REVIEW" not in output
    assert "identity_governance_state=TEMPORARY_RECOVERY_HOLD" not in output


def test_training_report_detects_architecture_bottleneck_plateau(capsys):
    report = build_training_report(
        multi_task_results=[{
            "task": "task_101.json",
            "status": "completed",
            "result": {
                "epistemic_cognition_report": {
                    "causal_validation_engine": {
                        "evaluations": [{
                            "hypothesis": {
                                "target_concept": "color_preservation",
                            },
                            "validation_score": 0.8861,
                            "cross_task_stability": 1.0,
                            "contradiction_resistance": 0.8093,
                            "dependency_coherence": 0.6812,
                            "context_consistency": 0.94,
                            "identity_compatibility": 1.0,
                            "validation_state": "VALIDATED",
                        }],
                    },
                    "contextual_truth_engine": {
                        "evaluations": [{
                            "truth": "color_preservation",
                            "context_confidence": 0.9024,
                            "status": "CONTEXT_REVIEW_REQUIRED",
                        }],
                    },
                    "context_discovery_engine": {
                        "evaluations": [{
                            "task": "color_preservation",
                            "transformation_family": "duplication",
                            "confidence": 0.76,
                        }],
                    },
                    "semantic_context_reasoner": {
                        "evaluations": [{
                            "context": "duplication",
                            "semantic_context_score": 0.90,
                            "status": "SEMANTICALLY_VALIDATED",
                        }],
                    },
                },
            },
        }],
        concept_lifecycle_report={
            "concepts": [{
                "concept": "growth",
                "state": "BOUNDARY_REFINEMENT",
                "preliminary_truth_candidate_ready": False,
                "truth_candidate_promotion": {
                    "failed_gates": ["context_strength"],
                    "dependency_promotion_blockers": [
                        "promotion_gate_blocked:context_strength",
                    ],
                },
            }],
        },
    )

    print_training_report(report)
    output = capsys.readouterr().out
    architecture_report = report["architecture_bottleneck_report"]

    assert architecture_report["bottleneck_type"] == (
        "NO_ARCHITECTURE_BOTTLENECK_DETECTED"
    )
    assert architecture_report["architecture_bottleneck"] is False
    assert architecture_report["raw_dependency_coherence_average"] == 0.6812
    assert architecture_report["dependency_coherence_average"] > 0.80
    assert architecture_report["context_count"] == 1
    assert architecture_report[
        "dependency_reasoning_operator_available"
    ] is True
    assert architecture_report[
        "process_dependency_memory_available"
    ] is True
    assert architecture_report[
        "process_concepts_in_boundary_refinement"
    ] == ["growth"]
    assert architecture_report["recommended_next_step"] == (
        "continue_adaptive_training"
    )
    assert architecture_report["process_dependency_links_loaded"] >= 1
    assert architecture_report["process_dependency_links_used"] >= 1
    assert architecture_report["dependency_chain_depth"] >= 1
    assert architecture_report["dependency_chain_coverage"] > 0.0
    assert architecture_report["boundary_refinement_dependency_debug"][0][
        "concept"
    ] == "growth"
    assert architecture_report[
        "dependency_ready_boundary_refinement_blockers"
    ][0]["exact_blocker"] == [
        "promotion_gate_blocked:context_strength",
    ]
    assert "DEPENDENCY REPORT" in output
    assert "NO_ARCHITECTURE_BOTTLENECK_DETECTED" in output
    assert "'dependency_activation_state': 'NOT_REQUESTED'" in output
    assert "RECOMMENDATIONS" in output
    assert "'continue_adaptive_training'" in output
    assert "'dependency_chain_coverage':" in output
    assert "'dependency_chains_executed':" in output
    assert "'dependency_chain_depth':" in output
    assert "'dependency_coherence':" in output
    assert "WARNINGS" in output
    assert "TRUTH REPORT" in output


def test_architecture_bottleneck_uses_typed_process_dependency_evidence():
    report = build_training_report(
        multi_task_results=[{
            "task": "task_growth.json",
            "status": "completed",
            "result": {
                "truth_candidate_report": {
                    "evaluations": [{
                        "concept": "growth",
                        "eligible_for_truth_candidate": False,
                        "eligibility_reason":
                        "promotion_gate_blocked:context_strength",
                        "blocked_metrics": ["context_strength"],
                        "promotion_dependency_score": 0.9548,
                        "promotion_dependency_bonus": 0.0387,
                        "dependency_confidence": 0.9017,
                        "dependency_chain_depth": 5,
                        "dependency_chain_coverage": 0.8556,
                        "missing_dependencies": [],
                    }],
                },
                "epistemic_cognition_report": {
                    "causal_validation_engine": {
                        "evaluations": [{
                            "hypothesis": {
                                "target_concept": "growth",
                            },
                            "validation_score": 0.8861,
                            "cross_task_stability": 1.0,
                            "dependency_coherence": 0.6812,
                            "context_consistency": 0.94,
                            "identity_compatibility": 1.0,
                        }],
                    },
                    "contextual_truth_engine": {
                        "evaluations": [{
                            "truth": "growth",
                            "contextual_truth_score": 0.80,
                            "contextual_consistency": True,
                        }],
                    },
                    "context_discovery_engine": {
                        "evaluations": [{
                            "task": "growth",
                            "transformation_family": "growth",
                            "confidence": 0.86,
                        }],
                    },
                    "semantic_context_reasoner": {
                        "evaluations": [{
                            "context": "growth",
                            "semantic_context_score": 0.92,
                            "status": "SEMANTICALLY_VALIDATED",
                        }],
                    },
                },
            },
        }],
        concept_lifecycle_report={
            "concepts": [{
                "concept": "growth",
                "state": "BOUNDARY_REFINEMENT",
                "preliminary_truth_candidate_ready": False,
            }],
        },
    )

    architecture_report = report["architecture_bottleneck_report"]

    assert architecture_report["raw_dependency_coherence_average"] == 0.6812
    assert architecture_report["effective_dependency_evidence_average"] > 0.80
    assert architecture_report["dependency_plateau"] is False
    assert architecture_report["architecture_bottleneck"] is False
    assert {
        "concept": "growth",
        "source": "typed_process_dependency_memory",
        "promotion_dependency_score": 0.9548,
        "dependency_confidence": 0.9017,
        "dependency_chain_depth": 5,
        "dependency_chain_coverage": 0.8556,
    } in architecture_report["process_dependency_evidence_sources"]
    assert any(
        source["source"] == "typed_process_dependency_memory_relations"
        and source["relation_semantics_score"] > 0.80
        for source in architecture_report["process_dependency_evidence_sources"]
    )


def test_architecture_bottleneck_uses_typed_relation_semantics_from_memory():
    report = build_training_report(
        multi_task_results=[{
            "task": "task_growth.json",
            "status": "completed",
            "result": {
                "epistemic_cognition_report": {
                    "causal_validation_engine": {
                        "evaluations": [{
                            "hypothesis": {
                                "target_concept": "growth",
                            },
                            "validation_score": 0.8861,
                            "cross_task_stability": 1.0,
                            "dependency_coherence": 0.6737,
                            "context_consistency": 0.94,
                            "identity_compatibility": 1.0,
                        }],
                    },
                    "contextual_truth_engine": {
                        "evaluations": [{
                            "truth": "growth",
                            "contextual_truth_score": 0.80,
                            "contextual_consistency": True,
                        }],
                    },
                    "context_discovery_engine": {
                        "evaluations": [{
                            "task": "growth",
                            "transformation_family": "growth",
                            "confidence": 0.86,
                        }],
                    },
                    "semantic_context_reasoner": {
                        "evaluations": [{
                            "context": "growth",
                            "semantic_context_score": 0.92,
                            "status": "SEMANTICALLY_VALIDATED",
                        }],
                    },
                },
            },
        }],
        concept_lifecycle_report={
            "concepts": [{
                "concept": "growth",
                "state": "BOUNDARY_REFINEMENT",
                "preliminary_truth_candidate_ready": False,
            }],
        },
    )

    architecture_report = report["architecture_bottleneck_report"]
    typed_source = architecture_report["process_dependency_evidence_sources"][0]

    assert architecture_report["raw_dependency_coherence_average"] == 0.6737
    assert architecture_report["effective_dependency_evidence_average"] > 0.80
    assert architecture_report["architecture_bottleneck"] is False
    assert architecture_report["dependency_plateau"] is False
    assert typed_source["source"] == "typed_process_dependency_memory_relations"
    assert typed_source["relation_semantics_score"] > 0.80
    assert typed_source["typed_dependency_relation_count"] >= 1


def test_architecture_report_uses_executed_dependency_telemetry(capsys):
    report = build_training_report(
        multi_task_results=[{
            "task": "task_shape.json",
            "status": "completed",
            "result": {
                "process_dependency_chains": {
                    "shape_preservation": {
                        "concept": "shape_preservation",
                        "process_dependency_links_loaded": 97,
                        "process_dependency_links_used": 96,
                        "dependency_chain_depth": 4,
                        "dependency_chain_coverage": 0.9897,
                        "dependency_coherence_average": 0.8852,
                        "dependency_explanation_quality": 0.9041,
                        "dependency_explanation": {
                            "explanation_path": [
                                {
                                    "source": "shape_preservation",
                                    "target": "local_geometry_tracking",
                                },
                            ],
                        },
                    },
                },
                "epistemic_cognition_report": {
                    "causal_validation_engine": {
                        "evaluations": [{
                            "hypothesis": {
                                "target_concept": "shape_preservation",
                            },
                            "validation_score": 0.89,
                            "cross_task_stability": 0.94,
                            "dependency_coherence": 0.8071,
                            "context_consistency": 0.92,
                            "identity_compatibility": 0.96,
                        }],
                    },
                    "contextual_truth_engine": {
                        "evaluations": [{
                            "truth": "shape_preservation",
                            "contextual_truth_score": 0.86,
                        }],
                    },
                    "context_discovery_engine": {
                        "evaluations": [{
                            "task": "shape_preservation",
                            "confidence": 0.86,
                        }],
                    },
                    "semantic_context_reasoner": {
                        "evaluations": [{
                            "context": "shape_preservation",
                            "semantic_context_score": 0.91,
                        }],
                    },
                },
            },
        }],
    )

    architecture_report = report["architecture_bottleneck_report"]
    telemetry = architecture_report["dependency_telemetry_report"][0]

    assert architecture_report["dependency_coherence_average"] >= 0.8
    assert architecture_report["process_dependency_links_used"] == 96
    assert architecture_report["dependency_chain_depth"] >= 4
    assert architecture_report["dependency_chain_coverage"] >= 0.8
    assert architecture_report["dependency_explanation_quality"] == 0.9041
    assert architecture_report["architecture_bottleneck"] is False
    assert architecture_report["recommended_next_step"] == (
        "continue_adaptive_training"
    )
    assert telemetry["concept"] == "shape_preservation"
    assert telemetry["links_loaded"] == 97
    assert telemetry["links_used"] == 96
    assert telemetry["chain_depth"] == 4
    assert telemetry["coverage"] == 0.9897
    assert telemetry["coherence"] == 0.8852
    assert telemetry["explanation_path"]

    print_training_report(report)
    output = capsys.readouterr().out
    assert "DEPENDENCY REPORT" in output
    assert "'dependency_chain_depth':" in output


def test_boundary_refinement_prefers_reasoned_dependency_chain():
    report = build_training_report(
        concept_lifecycle_report={
            "concepts": [{
                "concept": "growth",
                "state": "BOUNDARY_REFINEMENT",
            }],
        },
        multi_task_results=[{
            "task": "task_growth.json",
            "status": "completed",
            "result": {
                "process_dependency_chains": {
                    "growth": {
                        "concept": "growth",
                        "reasoned_dependency_chain": True,
                        "process_dependency_links_loaded": 97,
                        "process_dependency_links_used": 96,
                        "dependency_chain_depth": 4,
                        "dependency_chain_coverage": 0.9897,
                        "dependency_coherence_average": 0.8862,
                        "dependency_explanation_quality": 0.9731,
                        "resolved_dependency_chain": [
                            "growth",
                            "object_identity_exists",
                            "area_increases",
                            "identity_preserved",
                            "topology_preserved",
                        ],
                    },
                },
            },
        }],
    )

    dependency_debug = report["architecture_bottleneck_report"][
        "boundary_refinement_dependency_debug"
    ][0]

    assert dependency_debug["concept"] == "growth"
    assert dependency_debug["reasoned_dependency_chain"] is True
    assert dependency_debug["resolved_dependency_chain"] != []
    assert dependency_debug["dependency_chain_depth"] == 4
    assert dependency_debug["dependency_chain_coverage"] == 0.9897


def test_architecture_bottleneck_reconciles_dependency_ready_blockers():
    report = build_training_report(
        multi_task_results=[{
            "task": "task_101.json",
            "status": "completed",
            "result": {
                "epistemic_cognition_report": {
                    "causal_validation_engine": {
                        "evaluations": [{
                            "hypothesis": {
                                "target_concept": "growth",
                            },
                            "validation_score": 0.8861,
                            "cross_task_stability": 1.0,
                            "contradiction_resistance": 0.8093,
                            "dependency_coherence": 0.6812,
                            "context_consistency": 0.94,
                            "identity_compatibility": 1.0,
                            "validation_state": "VALIDATED",
                        }],
                    },
                    "contextual_truth_engine": {
                        "evaluations": [{
                            "truth": "growth",
                            "context_confidence": 0.9024,
                            "status": "CONTEXT_REVIEW_REQUIRED",
                        }],
                    },
                    "context_discovery_engine": {
                        "evaluations": [{
                            "task": "growth",
                            "transformation_family": "growth",
                            "confidence": 0.76,
                        }],
                    },
                    "semantic_context_reasoner": {
                        "evaluations": [{
                            "context": "growth",
                            "semantic_context_score": 0.90,
                            "status": "SEMANTICALLY_VALIDATED",
                        }],
                    },
                },
            },
        }],
        concept_lifecycle_report={
            "concepts": [{
                "concept": "growth",
                "state": "BOUNDARY_REFINEMENT",
                "preliminary_truth_candidate_ready": False,
                "truth_candidate_promotion": {
                    "promotion_dependency_score": 0.0,
                    "promotion_dependency_bonus": 0.0,
                    "dependency_confidence": 0.0,
                    "dependency_chain_depth": 0,
                    "dependency_chain_coverage": 0.0,
                    "dependency_promotion_blockers": [
                        "dependency_confidence_below_promotion_floor",
                        "dependency_chain_depth_below_promotion_floor",
                    ],
                    "failed_gates": [],
                },
            }],
        },
    )

    blocker = report["architecture_bottleneck_report"][
        "dependency_ready_boundary_refinement_blockers"
    ][0]

    assert blocker["dependency_confidence"] > 0.85
    assert blocker["dependency_chain_depth"] >= 4
    assert blocker["promotion_dependency_score"] > 0.0
    assert blocker["promotion_dependency_bonus"] > 0.0
    assert blocker["exact_blocker"] == []
    assert "dependency_confidence_below_promotion_floor" not in blocker[
        "exact_blocker"
    ]
    assert "dependency_chain_depth_below_promotion_floor" not in blocker[
        "exact_blocker"
    ]
    assert blocker["dependency_promotion_metrics_source"] == (
        "process_dependency_memory"
    )


def test_training_report_extracts_process_context_strength_from_runtime():
    report = build_training_report(
        multi_task_results=[{
            "task": "task_202.json",
            "status": "completed",
            "result": {
                "epistemic_cognition_report": {
                    "truth_candidate_engine": {
                        "evaluations": [{
                            "concept": "growth",
                            "candidate_state": "ADVANCING_TO_TRUTH_CANDIDATE",
                            "eligible_for_truth_candidate": False,
                            "blocked_metrics": [],
                            "context_discovery": {
                                "task": "growth",
                                "transformation_family": "growth",
                                "confidence": 0.86,
                            },
                            "context_hierarchy": {
                                "context_hierarchy_score": 0.752,
                                "hierarchy_ready": True,
                            },
                            "semantic_context": {
                                "context": "growth",
                                "semantic_context_score": 0.9,
                                "semantically_validated": True,
                            },
                            "contextual_truth": {
                                "truth": "growth",
                                "contextual_truth_score": 0.71,
                            },
                            "contextual_truth_authority": {
                                "effective_contextual_truth": 0.71,
                                "contextual_truth_supported": True,
                            },
                            "promotion_dependency_score": 0.9548,
                            "promotion_dependency_bonus": 0.0387,
                            "dependency_promotion_blockers": [],
                        }],
                    },
                    "context_discovery_engine": {
                        "evaluations": [],
                    },
                    "context_hierarchy_engine": {
                        "evaluations": [],
                    },
                    "semantic_context_reasoner": {
                        "evaluations": [],
                    },
                    "contextual_truth_engine": {
                        "evaluations": [],
                    },
                },
            },
        }],
        concept_lifecycle_report={
            "concepts": [{
                "concept": "growth",
                "state": "BOUNDARY_REFINEMENT",
                "preliminary_truth_candidate_ready": False,
                "truth_candidate_promotion": {
                    "failed_gates": ["context_strength"],
                    "dependency_promotion_blockers": [
                        "promotion_gate_blocked:context_strength",
                    ],
                },
            }],
        },
    )

    assert report["truth_candidate_evaluations"] == {}
    assert report["context_discovery_reports"]["growth"][
        "transformation_family"
    ] == "growth"
    assert report["context_hierarchy_reports"]["growth"][
        "context_hierarchy_score"
    ] == 0.752
    assert report["semantic_context_reports"]["growth"][
        "semantic_context_score"
    ] == 0.9
    assert report["contextual_truth_reports"]["growth"][
        "contextual_truth_score"
    ] == 0.71


def test_training_report_recovers_lifecycle_truth_promotion_when_enabled():
    report = build_training_report(
        multi_task_results=[],
        concept_lifecycle_report={
            "concepts": [{
                "concept": "growth",
                "state": "TRUTH_CANDIDATE",
                "preliminary_truth_candidate_ready": True,
                "truth_candidate_promotion": {
                    "candidate_ready": True,
                    "promotion_score": 0.81,
                    "eligible_for_truth_candidate": True,
                    "stage_eligible_for_truth_candidate": True,
                    "promotion_dependency_score": 0.82,
                    "promotion_dependency_bonus": 0.18,
                    "dependency_confidence": 0.91,
                    "dependency_chain_depth": 4,
                    "dependency_chain_coverage": 0.94,
                    "missing_dependencies": [],
                    "failed_gates": [],
                    "dependency_promotion_blockers": [],
                },
            }],
        },
        include_truth_evaluations=True,
    )

    candidate = report["truth_candidate_evaluations"]["growth"]
    architecture = report["architecture_bottleneck_report"]

    assert candidate["candidate_ready"] is True
    assert candidate["eligible_for_truth_candidate"] is True
    assert candidate["promotion_score"] == 0.81
    assert candidate["promotion_dependency_score"] == 0.82
    assert architecture["candidate_ready"] is True
    assert architecture["eligible_for_truth_candidate"] is True
    assert architecture["promotion_score"] == 0.81
    assert architecture["promotion_dependency_score"] == 0.82


def test_training_report_extracts_process_context_discovery_reports(capsys):
    report = build_training_report(
        multi_task_results=[{
            "task": "task_growth.json",
            "status": "completed",
            "result": {
                "epistemic_cognition_report": {
                    "truth_candidate_engine": {
                        "evaluations": [{
                            "concept": "growth",
                            "process_context_discovery_report": {
                                "system": "process_context_discovery_engine",
                                "concept": "growth",
                                "context_name": "growth_context",
                                "preconditions": [{
                                    "source": "growth",
                                    "relation": "requires",
                                    "target": "object_core",
                                }],
                                "transition_family": [{
                                    "source": "growth",
                                    "relation": "transitions_to",
                                    "target": "area_increase",
                                }],
                                "expected_outcomes": [{
                                    "source": "area_increase",
                                    "relation": "results_in",
                                    "target": "identity_preserved",
                                }],
                                "context_confidence": 0.9276,
                                "process_context_discovered": True,
                            },
                        }],
                    },
                    "context_discovery_engine": {
                        "evaluations": [],
                    },
                },
            },
        }],
    )

    assert report["context_discovery_reports"]["growth"][
        "context_name"
    ] == "growth_context"
    assert report["architecture_bottleneck_report"]["context_count"] == 1

    print_training_report(report)
    output = capsys.readouterr().out
    assert "CONTEXT REPORT" in output
    assert "'context_count': 1" in output
    assert "TRUTH REPORT" in output
    assert "RECOMMENDATIONS" in output


def test_training_report_bridges_cognition_layer_contexts_to_candidates():
    report = build_training_report(
        multi_task_results=[{
            "task": "task_growth.json",
            "status": "completed",
            "result": {
                "epistemic_cognition_layer": {
                    "truth_candidate_engine": {
                        "evaluations": [{
                            "concept": "growth",
                            "candidate_state": "PRE_VALIDATION",
                            "eligible_for_truth_candidate": False,
                            "context_discovery": {
                                "concept": "growth",
                                "task": "task_growth.json",
                                "transformation_family": "growth",
                                "confidence": 0.88,
                            },
                            "context_hierarchy": {
                                "context_hierarchy_score": 0.76,
                                "hierarchy_ready": True,
                            },
                            "semantic_context": {
                                "context": "growth",
                                "semantic_context_score": 0.82,
                            },
                        }],
                    },
                    "evaluations": [{
                        "concept": "growth",
                        "truth_commit": {
                            "decision": "REMAIN_BELIEF",
                            "reason": "truth_candidate_required",
                        },
                    }],
                },
            },
        }],
        include_truth_evaluations=True,
    )

    candidate = report["truth_candidate_evaluations"]["growth"]

    assert candidate["candidate_ready"] is False
    assert candidate["eligible_for_truth_candidate"] is False
    assert candidate["stage_eligible_for_truth_candidate"] is False
    assert candidate["promotion_score"] == 0.82
    assert report["context_discovery_reports"]["growth"][
        "transformation_family"
    ] == "growth"
    assert report["context_hierarchy_reports"]["growth"][
        "context_hierarchy_score"
    ] == 0.76
    assert report["semantic_context_reports"]["growth"][
        "semantic_context_score"
    ] == 0.82
    assert report["truth_commit_evaluations"]["growth"][
        "decision"
    ] == "REMAIN_BELIEF"


def test_training_report_commits_and_reuses_ready_lifecycle_truths():
    report = build_training_report(
        multi_task_results=[],
        concept_lifecycle_report={
            "concepts": [{
                "concept": "growth",
                "state": "TRUTH_CANDIDATE",
                "preliminary_truth_candidate_ready": True,
                "truth_candidate_promotion": {
                    "candidate_ready": True,
                    "promotion_score": 0.94,
                    "confidence": 0.94,
                    "eligible_for_truth_candidate": True,
                    "stage_eligible_for_truth_candidate": True,
                    "dependency_confidence": 0.93,
                    "dependency_chain_coverage": 0.94,
                    "context_strength": 0.94,
                    "causal_validation_score": 0.92,
                    "cross_task_stability": 0.91,
                    "contradiction_rate": 0.0,
                    "failed_gates": [],
                    "dependency_promotion_blockers": [],
                },
            }],
        },
        include_truth_evaluations=True,
    )

    commit = report["truth_commit_evaluations"]["growth"]
    reuse = report["truth_reuse_report"]

    assert commit["decision"] == "TRUTH_COMMITTED"
    assert commit["final_commit_state"] == "TRUTH_COMMITTED"
    assert commit["established_truth_state"] == "ESTABLISHED_TRUTH"
    assert commit["commit_ready"] is True
    assert report["truth_commit_engine_report"]["truth_committed"] is True
    assert report["truth_registry_report"]["committed_truth_count"] == 1
    assert reuse["truth_hits"] == 1
    assert reuse["truth_misses"] == 0
    assert report["strategy_reuse_report"]["strategy_hits"] == 1
    assert report["strategy_reuse_report"]["strategy_misses"] == 0
    assert report["knowledge_reuse_report"]["strategy_hits"] == 1
    assert report["hypothesis_generation_report"]["hypothesis_count"] == 1
    assert (
        report["hypothesis_generation_report"]["accepted_hypothesis_count"]
        == 1
    )
    assert (
        report["counterfactual_reasoning_report"]["counterfactual_count"]
        == 1
    )
    assert (
        report["counterfactual_reasoning_report"]["counterfactual_hits"]
        == 1
    )
    assert (
        report["counterfactual_reuse_report"]["counterfactual_success"]
        == 1
    )
    assert report["concept_lifecycle"]["hypotheses"][0]["concept"] == "growth"
    assert (
        report["concept_lifecycle"]["counterfactuals"][0]["concept"]
        == "growth"
    )


def test_training_report_prints_real_strategy_objects(capsys):
    report = {
        "strategy_reuse_report": {
            "strategy_hits": 2,
            "strategy_misses": 0,
            "strategy_reuse_rate": 1.0,
            "reused_strategies": [
                {},
                {
                    "strategy_id": "strategy:growth:truth_guided_reuse",
                    "concept": "growth",
                    "reuse_state": "STRATEGY_REUSED",
                    "reuse_score": 0.94,
                    "method": "reuse committed growth as a solving constraint",
                },
            ],
        },
    }

    print_training_report(report)

    output = capsys.readouterr().out
    assert "CACHE REPORT" in output
    assert "'strategy_hits': 2" in output
    assert "None state=None score=None method=None" not in output


def test_training_report_prints_counterfactual_reuse_objects(capsys):
    report = {
        "counterfactual_reuse_report": {
            "counterfactual_hits": 1,
            "counterfactual_misses": 0,
            "counterfactual_reuse_rate": 1.0,
            "counterfactual_success_rate": 1.0,
            "reused_counterfactuals": [{
                "counterfactual_id": "counterfactual:growth:truth_removed",
                "concept": "growth",
                "counterfactual_reuse_state": "COUNTERFACTUAL_REUSED",
                "reuse_score": 0.94,
                "learned_from": "committed_truth_and_accepted_hypothesis",
            }],
        },
    }

    print_training_report(report)

    output = capsys.readouterr().out
    assert "RUNTIME INTELLIGENCE DASHBOARD" in output
    assert "CACHE REPORT" in output


def test_training_report_dashboard_uses_aggregated_performance_report(capsys):
    report = build_training_report(
        multi_task_results=[{
            "task": "task_reuse.json",
            "status": "completed",
            "result": {
                "performance_report": {
                    "strategy_hits": 15,
                    "truth_hits": 15,
                    "context_hits": 5,
                    "reuse_rate": 0.5667,
                    "adaptive_reuse_engine": {
                        "strategy_hits": 15,
                        "truth_hits": 15,
                        "context_hits": 5,
                        "reuse_rate": 0.5667,
                    },
                },
                "knowledge_reuse_report": {
                    "strategy_hits": 0,
                    "truth_hits": 0,
                    "context_hits": 0,
                    "reuse_rate": 0.0,
                },
            },
        }],
    )

    print_training_report(report)

    output = capsys.readouterr().out
    assert report["performance_report"]["strategy_hits"] == 15
    assert report["performance_report"]["truth_hits"] == 15
    assert report["performance_report"]["context_hits"] == 5
    assert report["performance_report"]["reuse_rate"] == 0.5667
    assert "'strategy_hits': 15" in output
    assert "'truth_hits': 15" in output
    assert "'context_hits': 5" in output
    assert "'reuse_rate': 0.5667" in output


def test_dependency_enabled_tool_reports_requested_not_not_requested():
    report = build_training_report(
        multi_task_results=[{
            "task": "task_dependency.json",
            "status": "completed",
            "result": {
                "enabled_tools": ["dependency_reasoning"],
                "tool_selection_report": {
                    "enabled_tools": ["dependency_reasoning"],
                },
            },
        }],
    )

    architecture = report["architecture_bottleneck_report"]
    assert architecture["dependency_activation_state"] == "REQUESTED"
