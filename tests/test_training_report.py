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
    ] == "SUPPORTED"
    assert report["truth_candidate_evaluations"]["symbolic_remapping"][
        "blocked_metrics"
    ] == ["contradiction_score"]
    assert report["concept_memory"]["symbolic_remapping"][
        "ledger_average_contradiction_score"
    ] == 0.0552
    assert report["truth_candidate_evaluations"]["symbolic_remapping"][
        "effective_contradiction_score"
    ] == 0.14
    assert report["truth_candidate_evaluations"]["symbolic_remapping"][
        "contradiction_threshold"
    ] == 0.10
    assert report["truth_commit_evaluations"]["symbolic_remapping"][
        "decision"
    ] == "REMAIN_BELIEF"
    assert report["truth_commit_evaluations"]["symbolic_remapping"][
        "remaining_recovery_cycles"
    ] == 3
    assert "CONCEPT DEBUG REPORT" in output
    assert "TRUTH CANDIDATE REPORT" in output
    assert "TRUTH COMMIT REPORT" in output
    assert "symbolic_remapping 2 SUPPORTED" in output
    assert "ledger_average_contradiction=0.0552" in output
    assert "effective_contradiction=0.14" in output
    assert "contradiction_threshold=0.1" in output
    assert "dict_keys" not in output
    assert "large_runtime_context" not in output


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
    candidate = report["truth_candidate_evaluations"][
        "topology_preservation"
    ]
    commitment = report["truth_commit_evaluations"][
        "topology_preservation"
    ]

    assert candidate["effective_contradiction_score"] == 0.1114
    assert candidate["contradiction_review_required"] is True
    assert candidate["within_soft_review_zone"] is True
    assert candidate["contradiction_review_severity"] == (
        "LOW_RISK_REVIEW"
    )
    assert commitment["rehearsal_validation_pending"] is True
    assert commitment["identity_governance_state"] == (
        "TEMPORARY_RECOVERY_HOLD"
    )
    assert commitment["failed_identity_governance_gates"] == [
        "semantic_spine_stable",
    ]
    assert commitment["revocation_severity"] == "LOW_RISK_REVIEW"
    assert commitment["recovery_blocker_type"] == (
        "VALIDATED_REVERSIBLE_REHEARSAL_PENDING"
    )
    assert "contradiction_review_required=True" in output
    assert "within_soft_review_zone=True" in output
    assert "rehearsal_validation_pending=True" in output
    assert "revocation_severity=LOW_RISK_REVIEW" in output
    assert "identity_governance_state=TEMPORARY_RECOVERY_HOLD" in output


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
    assert "ARCHITECTURE BOTTLENECK REPORT" in output
    assert "bottleneck_type=NO_ARCHITECTURE_BOTTLENECK_DETECTED" in output
    assert (
        "dependency_reasoning_operator_available=True"
        in output
    )
    assert (
        "process_dependency_memory_available=True"
        in output
    )
    assert "recommended_next_step=continue_adaptive_training" in output
    assert "process_dependency_links_loaded=" in output
    assert "process_dependency_links_used=" in output
    assert "dependency_chain_depth=" in output
    assert "dependency_chain_coverage=" in output
    assert "boundary_refinement_dependency concept=growth" in output
    assert "dependency_ready_boundary_refinement_blocker concept=growth" in output


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
    assert "DEPENDENCY TELEMETRY REPORT" in output
    assert "dependency_telemetry concept=shape_preservation" in output


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

    candidate = report["truth_candidate_evaluations"]["growth"]

    assert candidate["context_strength"] == 0.9
    assert candidate["context_strength_source"] == (
        "epistemic_cognition_report.truth_candidate_engine"
    )
    assert candidate["context_discovery"]["transformation_family"] == "growth"
    assert candidate["context_hierarchy"]["context_hierarchy_score"] == 0.752
    assert candidate["semantic_context"]["semantic_context_score"] == 0.9
    assert candidate["contextual_truth"]["contextual_truth_score"] == 0.71
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
