from runtime.reporting.final_report_renderer import (
    REPORT_BEGIN_MARKER,
    REPORT_END_MARKER,
    SECTION_ORDER,
    DeterministicFinalReportRenderer,
)


def _report_state():
    return {
        "runtime_status": "completed",
        "tasks_executed": 3,
        "successful_tasks": 3,
        "generated_concepts": 4,
        "generated_programs": 2,
        "truth_candidate_count": 1,
        "PROGRAM_SYNTHESIS_REPORT": {
            "average_program_confidence": 0.82,
            "highest_confidence": 0.91,
            "lowest_confidence": 0.64,
            "validation_distribution": {"VALID": 2},
        },
        "TRANSFORMATION_SYNTHESIS_REPORT": {
            "detected_concepts": ["path_finding", "route_completion"],
            "transformation_confidence": 1.0,
            "transformation_accuracy": 1.0,
            "selected_program": {
                "steps": [
                    {
                        "operation": "construct_path",
                        "parameters": {
                            "path_color": 1,
                            "path_cells": [[0, 1], [0, 2]],
                        },
                    }
                ],
                "step_count": 1,
            },
            "semantic_to_transformation_compilation_report": {
                "semantic_to_transformation_compilation_success": True,
                "detected_intents": ["path_finding", "route_completion"],
                "execution_intents": [
                    {
                        "intent": "path_construction",
                        "operation": "construct_path",
                        "source": "semantic_intent_router",
                    }
                ],
                "semantic_intent_routing_report": {
                    "semantic_intent_routing_success": True,
                    "execution_intent_count": 1,
                },
                "selected_intent": "path_construction",
                "candidate_count": 1,
                "compiled_program": {
                    "steps": [
                        {
                            "operation": "construct_path",
                            "parameters": {
                                "path_color": 1,
                                "path_cells": [[0, 1], [0, 2]],
                            },
                        }
                    ],
                    "step_count": 1,
                },
                "validation": {
                    "accuracy": 1.0,
                    "exact_match": True,
                    "shape_match": True,
                },
                "transformation_plan": {
                    "plan_type": "semantic_to_transformation",
                    "rationale": "semantic_path_delta_to_explicit_path_cells",
                },
                "transformation_graph": {
                    "node_count": 1,
                    "edge_count": 0,
                },
            },
        },
        "COGNITIVE_SEARCH_REPORT": {
            "overall_search_quality": 0.76,
            "search_efficiency": 0.81,
            "search_coverage": 0.69,
            "search_entropy": 0.33,
            "average_route_quality": 0.71,
            "route_count": 3,
        },
        "RUNTIME_LIFECYCLE_REPORT": {
            "total_executions": 3,
            "completed_executions": 3,
            "archived_executions": 3,
            "execution_coverage": 1.0,
            "snapshot_coverage": 1.0,
            "lifecycle_coverage": 1.0,
        },
        "EXECUTION_BINDING_REPORT": {
            "binding_status": "BOUND",
            "missing_execution_instances": 0,
            "missing_snapshot_runtimes": 0,
        },
        "RUNTIME_METRIC_SYNCHRONIZATION_REPORT": {
            "metric_validation_status": "VALID",
        },
        "RUNTIME_OBSERVABILITY_REPORT": {
            "observability_status": "HEALTHY",
        },
        "execution_timing": {
            "execution_timing_state": {
                "total_wall_time": 10.0,
                "cognitive_runtime_time": 6.0,
                "unattributed_time": 0.5,
                "timing_coverage": 0.95,
                "report_generation_time": 0.2,
                "finalization_time": 0.3,
            },
            "timing_records": [
                {
                    "timing_scope": "BOOT_TIME",
                    "timing_status": "OBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 0.5,
                    "inclusive_duration_seconds": 0.5,
                    "exclusive_duration_seconds": 0.5,
                    "cpu_duration_seconds": 0.0,
                    "measurement_source": "execution_timing_unification_engine",
                    "measurement_method": "external_scope_duration_or_zero_when_unobserved",
                },
                {
                    "timing_scope": "REPORT_GENERATION_TIME",
                    "timing_status": "OBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 0.2,
                    "inclusive_duration_seconds": 0.2,
                    "exclusive_duration_seconds": 0.2,
                    "cpu_duration_seconds": 0.0,
                    "measurement_source": "execution_timing_unification_engine",
                    "measurement_method": "external_scope_duration_or_zero_when_unobserved",
                },
            ],
        },
        "performance_report": {
            "total_runtime_seconds": 10.0,
            "active_compute_time_seconds": 8.0,
            "untracked_runtime_seconds": 0.5,
            "stage_metrics": [
                {
                    "stage_name": "grid_analysis",
                    "total_duration": 1.0,
                    "execution_count": 1,
                },
                {
                    "stage_name": "reasoning",
                    "total_duration": 3.0,
                    "execution_count": 1,
                },
                {
                    "stage_name": "search",
                    "total_duration": 2.0,
                    "execution_count": 1,
                },
                {
                    "stage_name": "evaluation",
                    "total_duration": 0.4,
                    "execution_count": 1,
                },
            ],
        },
        "compact_report": {
            "heavy_keys_removed": 1,
            "arrays_summarized": 1,
            "repeated_reports_collapsed": 1,
        },
        "raw_nested_report": {"nested": {"not": "printed"}},
    }


def _metadata():
    return {
        "system": "NEXRYN",
        "mode": "test",
        "profile": "unit",
        "report_level": "normal",
        "execution_id": "exec-1",
        "timestamp": "2026-07-15T00:00:00Z",
        "runtime_status": "completed",
        "execution_time": 1.25,
    }


def test_render_has_boundaries_and_stable_section_order():
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    lines = report.splitlines()
    assert lines[:3] == ["=" * 50, REPORT_BEGIN_MARKER, "=" * 50]
    assert lines[-3:] == ["=" * 50, REPORT_END_MARKER, "=" * 50]
    positions = [report.index(section) for section in SECTION_ORDER]
    assert positions == sorted(positions)
    assert renderer.report()["report_complete"] is True


def test_render_includes_cognitive_domain_ecosystem_report():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    governance_pos = report.index("COGNITIVE DOMAIN GOVERNANCE REPORT")
    ecosystem_pos = report.index("COGNITIVE DOMAIN ECOSYSTEM REPORT")
    compilation_pos = report.index("SEMANTIC COMPILATION")

    assert governance_pos < ecosystem_pos < compilation_pos
    assert "Total Domains:" in report
    assert "Capability Coverage:" in report
    assert "Cognitive Bottlenecks:" in report
    assert "Ecosystem Maturity:" in report


def test_render_includes_cognitive_capability_coverage_map():
    state = _report_state()
    state["PROGRAM_GENERATION_REPORT"] = {
        "generated_programs": 2,
        "eligible_concepts": 2,
        "generated_blueprints": 2,
        "missing_requirements": ["compiler_support"],
    }
    state["CANDIDATE_PROPOSAL_REPORT"] = {
        "proposal_phase_entered": True,
        "eligible_source_count": 1,
        "proposal_count": 1,
        "knowledge_investment_policy": "OPERATIONAL_VALUE_PRIORITIZED",
        "knowledge_investment_authority": "candidate_proposal_runtime",
        "high_value_knowledge_items": 1,
        "medium_value_knowledge_items": 0,
        "low_value_knowledge_items": 0,
        "deprioritized_knowledge_items": 0,
        "candidate_proposals": [
            {
                "source": "program_generation",
                "proposal_status": "PROPOSED",
                "operation": "construct_path",
                "operational_value_score": 0.82,
                "investment_tier": "HIGH_VALUE",
                "investment_reason": "concrete_task_execution_signal",
            }
        ],
        "sources_with_proposals": ["program_generation"],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "arena_state": "SINGLE_SOURCE_ONLY",
            "candidate_count": 1,
            "source_count": 1,
            "sources_entered": ["normalized_program_candidates"],
            "proposal_sources_with_proposals": [
                "program_generation",
                "semantic_to_transformation_compiler",
            ],
            "candidate_source_flow_trace": [
                {
                    "source": "semantic_to_transformation_compiler",
                    "proposal_runtime_proposed": True,
                    "arena_proposal_built": False,
                    "gateway_accepted": False,
                    "entered_arena": False,
                    "flow_state": "PROPOSAL_NOT_BUILT_FOR_ARENA",
                    "blocked_stage": "arena_proposal_builder",
                    "build_failure_reason": "missing_program_representation",
                    "build_failure_detail": "program_field_missing_or_not_mapping",
                    "action": "preserve_proposal_runtime_source_in_arena_builder",
                }
            ],
            "cross_source_consensus_state": "NO_CROSS_SOURCE_CONSENSUS",
            "cross_source_consensus_count": 0,
            "arena_source_diversity_state": "LOW_SOURCE_DIVERSITY",
            "arena_source_diversity_action": "SOURCE_DIVERSITY_SPRINT_REQUIRED",
            "arena_to_compiled_bridge_state": "VALIDATION_PROBE_AVAILABLE",
            "arena_to_compiled_bridge_action": (
                "route_validation_probe_to_compiler_without_prediction_authority"
            ),
            "validation_probe_candidate_id": "semantic_program:path_finding",
            "validation_probe_operation": "construct_path",
            "validation_probe_source": "normalized_program_candidates",
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
            "target_candidate_sources": [
                "normalized_program_candidates",
                "semantic_compiler",
                "adaptive_reuse",
            ],
            "missing_candidate_sources": ["semantic_compiler", "adaptive_reuse"],
            "candidate_summary": [
                {
                    "source": "normalized_program_candidates",
                    "origin_source": "program_generation",
                    "origin_sources": ["program_generation"],
                    "normalized_source": "normalized_program_candidates",
                    "normalized_sources": ["normalized_program_candidates"],
                    "candidate_id": "semantic_program:path_finding",
                    "operation": "construct_path",
                    "entered_arena": True,
                }
            ],
            "selection_mode": "EVIDENCE_BASED_ARENA",
        }
    }
    state["EXECUTABLE_ACTIVATION_REPORT"] = {
        "arena_execution_recommendation_forwarded": True,
        "selected_arena_candidate_forwarded": False,
        "validation_probe_forwarded": True,
        "validation_probe_candidate_id": "semantic_program:path_finding",
        "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
        "validation_probe_consumed": True,
        "validation_probe_compiler_participation": 1,
        "validation_probe_admission_state": "VALIDATION_PROBE_COMPILED",
        "validation_probe_sandbox_validation_invoked": True,
        "validation_probe_validation_result_captured": True,
        "validation_probe_comparable_output_captured": True,
        "validation_probe_evidence_acceptance_evaluated": True,
        "validation_probe_evidence_acceptance_state": "ACCEPTED",
        "validation_probe_evidence_insufficiency_cause": "NONE",
        "validation_probe_required_evidence": "evidence_contract_satisfied",
        "validation_probe_recommended_validation_action": "retain_validation_evidence",
        "compiled_to_validated_probe_state": "VALIDATION_PROBE_VALIDATED",
    }
    state["OPERATIONAL_CAPABILITY_MATERIALIZATION_REPORT"] = {
        "materialized_operational_capabilities": 0,
        "known_operational_capability_count": 1,
        "known_operational_operations": ["replace_color"],
        "known_operational_domain_count": 1,
        "operational_experience_count": 4,
        "operational_experience_task_count": 4,
        "reuse_evidence_count": 3,
        "independent_reuse_success_count": 3,
        "capability_survival_rate": 0.0,
        "materialization_survival_rate": 0.0,
        "generated_survival_candidate_count": 3,
        "arena_simulated_survival_candidate_count": 2,
        "arena_quality_survival_candidate_count": 1,
        "incubating_operational_capability_count": 1,
        "operational_citizen_count": 0,
        "validation_bottleneck_inflation": 0.5,
        "validation_bottleneck_state": "VALIDATION_BOTTLENECK",
        "unresolved_validation_gap_candidate_count": 1,
        "operational_citizen_domain_distribution": {
            "Identity": 1,
        },
        "dominant_operational_domain": "Identity",
        "domain_monopoly_share": 1.0,
        "domain_operational_imbalance_state": "DOMAIN_MONOPOLY",
        "capability_stability_regression_count": 1,
        "crystallization_candidate_count": 1,
        "quality_to_citizen_crystallization_rate": 0.0,
        "candidate_to_citizen_crystallization_rate": 0.0,
        "generated_to_citizen_pressure_ratio": 3.0,
        "capability_crystallization_state": "SEVERE_CRYSTALLIZATION_FAILURE",
        "capability_graduation_candidate_count": 1,
        "capability_graduation_pressure": 0.92,
        "capability_graduation_pressure_state": "HIGH",
        "world_governance_graduation_action": "GRADUATION_SPRINT_REQUIRED",
        "capability_graduation_health": 0.8125,
        "graduation_pipeline_health": "BACKLOGGED",
        "graduation_success_rate": 0.5,
        "graduation_failure_rate": 0.3333,
        "graduation_queue_health": "HEALTHY",
        "graduation_evidence_coverage": 0.8,
        "graduation_infrastructure_readiness": "READY",
        "average_capability_graduation_time": 17.0,
        "graduation_backlog_size": 1,
        "capability_graduation_risk": "MEDIUM",
        "capability_graduation_complexity": "MEDIUM",
        "capability_graduation_confidence": 0.9444,
            "graduation_pipeline_stages": {
                "INCUBATING_VALIDATION_GAP": 1,
                "SURVIVING_CAPABILITY": 1,
                "COGNITIVE_CITIZEN": 0,
                "OPERATIONAL_CITIZEN": 0,
            },
            "capability_promotion_phase_state": (
                "CAPABILITY_PROMOTION_PHASE_DETECTED"
            ),
            "capability_promotion_candidate_count": 1,
            "capability_promotion_interpretation": (
                "promotion_interprets_evidence_before_trust_or_graduation"
            ),
            "evidence_acceptance_state": (
                "GOVERNED_EVIDENCE_ACCEPTANCE_BOTTLENECK"
            ),
            "evidence_acceptance_bottleneck": (
                "governed_validation_evidence_acceptance"
            ),
            "evidence_acceptance_failure_count": 1,
            "evidence_acceptance_failure_share": 1.0,
            "capability_promotion_rows": [
                {
                    "capability_id": (
                        "operational_capability:identity:preserve_size:size"
                    ),
                    "operation": "preserve_size",
                    "domain": "Identity",
                    "lifecycle_state": "COGNITIVE_CITIZEN",
                    "graduation_status": "BLOCKED_AT_FINAL_VALIDATION",
                    "validator_gap": "GOVERNED_VALIDATION_INCOMPLETE",
                    "capability_graduation_confidence": 0.91,
                    "promotion_interpretation": (
                        "high_quality_evidence_requires_acceptance_before_trust"
                    ),
                    "trusted_for_decision": False,
                }
            ],
            "graduation_transition_rows": [
            {
                "transition": (
                    "SURVIVING_CAPABILITY->COGNITIVE_CITIZEN"
                ),
                "source_count": 1,
                "target_count": 0,
                "stuck_count": 1,
                "success_rate": 0.0,
                "average_graduation_time": 17.0,
                "stuck_reasons": {
                    "exact_or_governed_validation_success": 1,
                },
            },
        ],
        "graduation_sprint_recommendations": [
            {
                "capability_id": (
                    "operational_capability:spatial:translate:spatial_reasoning"
                ),
                "operation": "translate",
                "priority": 0.9444,
                "minimum_required_evidence": (
                    "exact_or_governed_validation_success"
                ),
                "recommended_validation_type": "exact_or_governed_validation",
                "recommended_training_signal": (
                    "validator_acceptance_task_for:translate"
                ),
                "can_graduate_in_single_run": True,
                "estimated_runs_required": 1,
            },
        ],
        "validator_failure_distribution": {
            "GOVERNED_VALIDATION_INCOMPLETE": 1,
        },
        "top_graduation_candidates": [
            {
                "capability_id": "operational_capability:spatial:translate:spatial_reasoning",
                "operation": "translate",
                "domain": "Spatial",
                "lifecycle_state": "SURVIVING_CAPABILITY",
                "distinct_task_count": 17,
                "arena_quality_count": 16,
                "best_accuracy": 0.9444,
                "average_accuracy": 0.7772,
                "improvement_trend": "IMPROVING",
                "graduation_score": 0.92,
                "missing_graduation_evidence": "exact_or_governed_validation_success",
                "validator_gap": "GOVERNED_VALIDATION_INCOMPLETE",
                "capability_graduation_confidence": 0.9444,
                "world_governance_graduation_action": "GRADUATION_SPRINT_REQUIRED",
            }
        ],
        "world_governance_promotion_policy_state": "RELAX_SANDBOX_CITIZENSHIP",
        "sandbox_citizenship_thresholds": {
            "min_distinct_tasks": 3,
            "min_arena_quality_count": 3,
            "min_average_accuracy": 0.8,
            "min_best_accuracy": 0.0,
            "allowed_trends": [
                "STABLE",
                "IMPROVING",
                "STABLE_HIGH_PERFORMANCE",
                "DECLINING_MINOR",
            ],
        },
        "trusted_capability_policy": {
            "policy_state": "STRICT_REVIEW_REQUIRED",
        },
        "decision_authority_policy": {
            "policy_state": "SEPARATE_AUTHORITY_REVIEW_REQUIRED",
            "automatic_authority_transfer": False,
        },
            "validation_sponsorship_contract": {
                "contract_state": "WORLD_GOVERNANCE_VALIDATION_SPONSOR",
                "truth_preparation_gate": "OPPORTUNITY_PERMISSION_ONLY",
                "capability_merit_system": "VALIDATION_PRIORITY_ONLY",
                "truth_boundary_contract": [
                    "MERIT_NEVER_INFLUENCES_TRUTH_FORMATION",
                    "VALIDATION_SPONSORSHIP_NEVER_INFLUENCES_TRUST_FORMATION",
                ],
                "validation_requirements_changed": False,
            },
            "capability_survival_store_path": "runtime/test_survival.json",
        "capability_survival_state_distribution": {
            "GENERATED_CANDIDATE": 1,
            "ARENA_SIMULATED": 1,
            "INCUBATING_VALIDATION_GAP": 1,
            "SURVIVING_CAPABILITY": 0,
            "OPERATIONAL_CITIZEN": 0,
        },
        "top_incubating_capabilities": [
            {
                "capability_id": "operational_capability:topology:construct_path:path",
                "operation": "construct_path",
                "domain": "Topology",
                "lifecycle_state": "INCUBATING_VALIDATION_GAP",
                "distinct_task_count": 2,
                "arena_simulated_count": 2,
                "best_accuracy": 0.61,
                "average_accuracy": 0.55,
                "validation_attempts": 1,
                "improvement_trend": "IMPROVING",
                "next_required_evidence": "repeatable_validation_across_independent_task",
            }
        ],
        "top_operational_citizens": [
            {
                "capability_id": "operational_capability:identity:preserve_grid:object_identity_preservation",
                "operation": "preserve_grid",
                "domain": "Identity",
                "lifecycle_state": "OPERATIONAL_CITIZEN",
                "distinct_task_count": 3,
                "arena_simulated_count": 3,
                "best_accuracy": 0.9722,
                "average_accuracy": 0.9241,
                "citizenship_basis": "sandbox_governed_survival_evidence",
                "trusted_for_decision": False,
            }
        ],
        "capability_survival_report": {
            "capability_survival_rows": [
                {
                    "capability_id": "operational_capability:growth:duplicate_object:growth",
                    "operation": "duplicate_object",
                    "domain": "Growth",
                    "lifecycle_state": "SURVIVING_CAPABILITY",
                    "distinct_task_count": 35,
                    "arena_simulated_count": 60,
                    "best_accuracy": 1.0,
                    "average_accuracy": 0.1154,
                    "validation_attempts": 4,
                    "improvement_trend": "STABLE_HIGH_PERFORMANCE",
                    "trusted_for_decision": False,
                },
            ],
        },
        "capability_governance_contract_state": (
            "CAPABILITY_GOVERNANCE_ACTIVE"
        ),
        "capability_rights_policy": {
            "decision_authority": "trusted_capabilities_only",
            "request_validation": "sandbox_citizens",
        },
        "capability_obligations_policy": {
            "preserve_lineage": True,
            "respect_sandbox_limits": True,
        },
        "capability_reputation_average": 0.83,
        "capability_trust_average": 0.41,
        "capability_evidence_contamination_state": (
            "EVIDENCE_LEDGER_CONTAMINATION_RISK"
        ),
        "capability_evidence_contamination_count": 1,
        "capability_governance_rows": [
            {
                "capability_id": "operational_capability:identity:preserve_grid:object_identity_preservation",
                "operation": "preserve_grid",
                "domain": "Identity",
                "lifecycle_state": "OPERATIONAL_CITIZEN",
                "citizenship_tier": "SANDBOX_OPERATIONAL_CITIZEN",
                "authority_scope": "SANDBOX_REUSE_ONLY",
                "trust_state": "NOT_TRUSTED_FOR_DECISION",
                "rights": [
                    "participate_in_arena",
                    "accumulate_evidence",
                    "request_validation",
                    "join_clusters",
                ],
                "obligations": [
                    "report_failures",
                    "preserve_lineage",
                    "respect_sandbox_limits",
                    "undergo_regression_review",
                ],
                "reputation_score": 0.83,
                "trust_score": 0.41,
                "evidence_contamination_state": (
                    "ARENA_EXPOSURE_CONTAMINATION_RISK"
                ),
                "evidence_adjusted_accuracy": 0.5833,
                "relevant_task_attempt_count": 35,
                "arena_simulation_count": 60,
                "recommended_accuracy_basis": "relevant_task_attempt_accuracy",
                "evidence_ledger": {
                    "raw_average_accuracy": 0.1154,
                },
                "reputation_basis": {
                    "best_accuracy": 1.0,
                    "distinct_tasks": 35,
                },
            }
        ],
        "capability_evidence_contamination_rows": [
            {
                "operation": "duplicate_object",
                "evidence_contamination_state": (
                    "ARENA_EXPOSURE_CONTAMINATION_RISK"
                ),
                "evidence_adjusted_accuracy": 0.5833,
                "arena_simulation_count": 60,
                "recommended_accuracy_basis": "relevant_task_attempt_accuracy",
                "evidence_ledger": {
                    "raw_average_accuracy": 0.1154,
                },
                "reputation_basis": {
                    "best_accuracy": 1.0,
                    "distinct_tasks": 35,
                },
            }
        ],
        "top_crystallization_candidates": [
            {
                "capability_id": "operational_capability:spatial:preserve_shape:shape_preservation",
                "operation": "preserve_shape",
                "domain": "Spatial",
                "lifecycle_state": "INCUBATING_VALIDATION_GAP",
                "distinct_task_count": 3,
                "arena_quality_count": 3,
                "best_accuracy": 0.96,
                "average_accuracy": 0.84,
                "improvement_trend": "STABLE",
                "next_required_evidence": "repeatable_validation_across_independent_task",
            }
        ],
        "cognitive_citizen_count": 1,
        "cognitive_citizenship_definition": (
            "independent_high_quality_sandbox_evidence_without_decision_authority"
        ),
        "top_cognitive_citizens": [
            {
                "capability_id": "operational_capability:spatial:preserve_grid:object_identity_preservation",
                "operation": "preserve_grid",
                "domain": "Spatial",
                "lifecycle_state": "ARENA_SIMULATED",
                "distinct_task_count": 9,
                "arena_quality_count": 8,
                "best_accuracy": 0.9722,
                "average_accuracy": 0.8092,
                "improvement_trend": "STABLE_HIGH_PERFORMANCE",
            }
        ],
        "top_stability_regressions": [
            {
                "capability_id": "operational_capability:spatial:preserve_grid:object_identity_preservation",
                "operation": "preserve_grid",
                "domain": "Spatial",
                "lifecycle_state": "SURVIVING_CAPABILITY",
                "stability_state": "STABILITY_REGRESSION",
                "distinct_task_count": 6,
                "average_accuracy": 0.7763,
                "next_required_evidence": "stability_recovery_evidence",
            }
        ],
    }
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": False,
        "failure_reason": "no_supported_compiler_for_execution_intents",
        "compiler_resolution_trace": [
            {
                "semantic_intent": "unsupported_semantic",
                "operation": "density_modulation",
                "resolved_operation": "density_modulation",
                "resolved_compiler": "NONE",
                "compiler_found": False,
                "compilation_attempted": False,
                "candidate_emitted": False,
                "resolution_state": "RESOLVED_COMPILER_NOT_FOUND",
            }
        ],
        "compiler_failure_diagnostics": {
            "failure_reason_counts": {
                "operation_semantics_mismatch": 2,
                "missing_grid_pair": 1,
                "invalid_composition": 1,
            },
            "operational_grounding_failure_count": 1,
            "compiler_semantic_failure_count": 3,
            "operational_grounding_failure_rate": 0.25,
            "operational_grounding_state": "GROUNDING_FAILURE_PRESENT",
            "compiler_failure_interpretation": (
                "mixed_grounding_and_compiler_failure"
            ),
            "grounding_requirement_rows": [
                {
                    "program": "semantic_program_translate",
                    "operation": "translate",
                    "domain": "Spatial",
                    "missing_grounding": "input_output_grid_pair",
                    "required_task_property": (
                        "unambiguous_directional_translation_ground_truth"
                    ),
                }
            ],
            "grounding_required_for_operations": ["translate"],
            "grounding_required_for_domains": {"Spatial": 1},
            "failure_domain_distribution": {
                "Spatial": 2,
                "Topology": 1,
            },
            "failure_rows": [
                {
                    "operation": "preserve_grid",
                    "program": "semantic_program_preserve_grid",
                    "semantic_intent": "object_identity_preservation",
                    "expected_operation": "preserve_grid",
                    "resolved_operation": "translate",
                    "failure_stage": "semantic_operation_resolution",
                    "domain": "Spatial",
                    "reason": "operation_semantics_mismatch",
                    "compiler_rule": "RULE_GRID_PRESERVATION_01",
                    "detail": "candidate_not_emitted:preserve_grid",
                }
            ],
        },
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE CAPABILITY COVERAGE" in report
    assert "CONSTITUTIONAL CONTRACTS" in report
    assert "Truth Contract: TRUTH_IS_EVIDENCE_GOVERNED" in report
    assert "Trust Contract: TRUST_IS_EVIDENCE_GOVERNED" in report
    assert "Graduation Contract: GRADUATION_IS_EVIDENCE_GOVERNED" in report
    assert "Validation Sponsorship Contract:" in report
    assert "Evidence Sufficiency Contract:" in report
    assert "Overall Cognitive Capability Coverage:" in report
    assert "Architecture Freeze State:" in report
    assert "Execution Package Coverage Target:" in report
    assert "Compiler Runtime Coverage Target:" in report
    assert "Operational Capability Coverage Target:" in report
    assert "Operational Capability Coverage Semantics:" in report
    assert "Sandbox Operational Citizen Coverage:" in report
    assert "Sandbox Operational Citizen Coverage Semantics:" in report
    assert "Compiler Runtime Activated Programs:" in report
    assert "Execution Package Coverage:" in report
    assert "Execution Package Health Score:" in report
    assert "Primitive Operation Coverage:" in report
    assert "Compiler Infrastructure Health:" in report
    assert "Multi-Step Program Support:" in report
    assert "Execution Package Dependency Coverage:" in report
    assert "Primitive Infrastructure Coverage:" in report
    assert "Compiler Primitive Success Rate:" in report
    assert "Execution Package Utilization:" in report
    assert "Compiler Infrastructure Readiness:" in report
    assert "Execution Package Inventory State:" in report
    assert "Primitive Operation Inventory State:" in report
    assert "Execution Package Inventory Count:" in report
    assert "Primitive Operation Inventory Count:" in report
    assert "Executable Package Count:" in report
    assert "Executable Primitive Count:" in report
    assert "Candidate Attrition Coverage:" in report
    assert "End-To-End Program Lifecycle:" in report
    assert "Operationalization Bottleneck:" in report
    assert "Secondary Operationalization Bottleneck:" in report
    assert "Current Run Materialization Gap:" in report
    assert "Compiler Success Rate:" in report
    assert "Compiler Diagnostic State:" in report
    assert "Compiler Failure Count:" in report
    assert "Operational Grounding State:" in report
    assert "GROUNDING_FAILURE_PRESENT" in report
    assert "Operational Grounding Failure Count:" in report
    assert "Operational Grounding Failure Rate:" in report
    assert "Grounding Required For Operations:" in report
    assert "Grounding Required For Domains:" in report
    assert "Compiler Semantic Failure Count:" in report
    assert "Compiler Failure Interpretation:" in report
    assert "mixed_grounding_and_compiler_failure" in report
    assert "Grounding Adjusted Compiler Failure Pressure:" in report
    assert "Operational Grounding Requirements:" in report
    assert "unambiguous_directional_translation_ground_truth" in report
    assert "Package Utilization Gap Count:" in report
    assert "Package Utilization Gap State:" in report
    assert "Compiler Failure Detail Capture:" in report
    assert "Compiler Failure Reasons:" in report
    assert "operation_semantics_mismatch=2" in report
    assert "Compiler Failure Distribution By Domain:" in report
    assert "Spatial=2" in report
    assert "Top Compiler Failure Examples:" in report
    assert "program=semantic_program_preserve_grid" in report
    assert "intent=object_identity_preservation" in report
    assert "expected=preserve_grid" in report
    assert "resolved=translate" in report
    assert "stage=semantic_operation_resolution" in report
    assert "operation=preserve_grid" in report
    assert "rule=RULE_GRID_PRESERVATION_01" in report
    assert "source=compiler_failure_diagnostics" in report
    assert "Compiler Resolution Trace:" in report
    assert "operation=density_modulation" in report
    assert "compiler=NONE" in report
    assert "state=RESOLVED_COMPILER_NOT_FOUND" in report
    assert "Validation Success Rate:" in report
    assert "Capability Materialization Rate:" in report
    assert "Operational Yield From Concepts:" in report
    assert "Operational Yield From Programs:" in report
    assert "Operational Yield From Candidates:" in report
    assert "Operational Yield From Arena:" in report
    assert "Knowledge Production Efficiency:" in report
    assert "Knowledge Operationalization Efficiency:" in report
    assert "Operational Knowledge Waste:" in report
    assert "Operational Yield Stability:" in report
    assert "Operational Yield Stability Basis:" in report
    assert "Operational Yield Health State:" in report
    assert "Knowledge Investment Policy:" in report
    assert "Knowledge Investment Authority:" in report
    assert "High Value Knowledge Items:" in report
    assert "Medium Value Knowledge Items:" in report
    assert "Low Value Knowledge Items:" in report
    assert "Deprioritized Knowledge Items:" in report
    assert "Operational Investment Accuracy:" in report
    assert "Operational Investment Accuracy State:" in report
    assert "High Value Operational False Positives:" in report
    assert "Validation Efficiency:" in report
    assert "Validation Bottleneck Inflation:" in report
    assert "Validation Bottleneck State:" in report
    assert "High Value Validation Yield:" in report
    assert "Operational Capability Acquisition Rate:" in report
    assert "Capability Acquisition Rate Per 100 Tasks:" in report
    assert "Capability Survival Rate:" in report
    assert "Materialization Survival Rate:" in report
    assert "Candidate Retention Rate:" in report
    assert "Incubation Conversion Rate:" in report
    assert "Surviving Capability Conversion Rate:" in report
    assert "Operational Citizen Conversion Rate:" in report
    assert "Generated Survival Candidates:" in report
    assert "Arena-Simulated Survival Candidates:" in report
    assert "Arena-Quality Survival Candidates:" in report
    assert "Incubating Operational Capabilities:" in report
    assert "Operational Citizens:" in report
    assert "Current Run Operational Citizens:" in report
    assert "Historical Operational Citizens:" in report
    assert "Operational Domain Citizenship Coverage:" in report
    assert "Historical Operational Domain Citizens:" in report
    assert "Sandbox Operational Domain Citizens:" in report
    assert "Operational Domain Citizens:" in report
    assert "Expected Operational Domain Citizens:" in report
    assert "Surviving Capability Domain Count:" in report
    assert "Operational Citizen Domain Distribution:" in report
    assert "Historical Operational Domain Distribution:" in report
    assert "Sandbox Operational Domain Distribution:" in report
    assert "Combined Operational Domain Distribution:" in report
    assert "Dominant Operational Domain:" in report
    assert "Domain Monopoly Share:" in report
    assert "Domain Operational Imbalance State:" in report
    assert "Operational Domain Health:" in report
    assert "Operational Domain Coverage:" in report
    assert "Domain Operationalization Score:" in report
    assert "Domain Operationalization Bottleneck:" in report
    assert "Domain Population Balance:" in report
    assert "Domain Collaboration Score:" in report
    assert "Domain Operational Growth Rate:" in report
    assert "Domain Primitive Coverage:" in report
    assert "Domain Capability Diversity:" in report
    assert "Domain Infrastructure Readiness:" in report
    assert "role=" in report
    assert "arena_relationship=" in report
    assert "Operational Domain Population:" in report
    assert "Domain Diversification Score:" in report
    assert "Domain Monopoly Pressure:" in report
    assert "Operational Domain Growth Rate:" in report
    assert "Operational Domain Evolution Speed:" in report
    assert "Capability Ecology Health:" in report
    assert "Capability Cooperation Score:" in report
    assert "Capability Composition Score:" in report
    assert "Composite Capability Score:" in report
    assert "Capability Collaboration Diversity:" in report
    assert "Composite Operational Capability Count:" in report
    assert "Capability Interaction Density:" in report
    assert "Capability Composition Readiness:" in report
    assert "Composite Intelligence Readiness:" in report
    assert "Capability Economy Health:" in report
    assert "Operational Economy Health:" in report
    assert "Knowledge Attrition Health:" in report
    assert "Knowledge Attrition Loss Score:" in report
    assert "Knowledge Attrition State:" in report
    assert "Operational Investment Return:" in report
    assert "Operational Investment Return State:" in report
    assert "Knowledge Crystallization Efficiency:" in report
    assert "Knowledge Crystallization Pressure:" in report
    assert "Operational Population Growth Pressure:" in report
    assert "Capability Economy Crisis Score:" in report
    assert "Capability Economy Crisis State:" in report
    assert "Capability Lifecycle Efficiency:" in report
    assert "Knowledge To Citizen Efficiency:" in report
    assert "Candidate Attrition Cost:" in report
    assert "Candidate Attrition Cost State:" in report
    assert "Capability Investment Intelligence Phase:" in report
    assert "ROADMAP_ONLY" in report
    assert "Capability Investment Governance Principle:" in report
    assert "investment_allocates_validation_opportunities_only" in report
    assert "Capability Investment Truth Boundary:" in report
    assert "INVESTMENT_NEVER_INFLUENCES_TRUTH_FORMATION" in report
    assert "Capability Investment Authority Scope:" in report
    assert "validation_prioritization" in report
    assert "Capability Investment Forbidden Authority:" in report
    assert "trust_scores" in report
    assert "graduation_authority" in report
    assert "Capability Promotion Roadmap:" in report
    assert "capability_promotion" in report
    assert "Operational Economy Bottleneck:" in report
    assert "Knowledge Operationalization Choke Point:" in report
    assert "Knowledge Operationalization Symptom:" in report
    assert "Knowledge Operationalization Root Cause:" in report
    assert "Knowledge Operationalization Choke Cause:" in report
    assert "Knowledge Operationalization Choke Action:" in report
    assert "Knowledge Operationalization Loss Count:" in report
    assert "Knowledge Operationalization Loss Pressure:" in report
    assert "Knowledge Operationalization State:" in report
    assert "Execution Compilation Admission State:" in report
    assert "Execution Compilation Admission Reason:" in report
    assert "Execution Compilation Admission Action:" in report
    assert "Knowledge Operationalization Path:" in report
    assert "Operational Cluster Readiness:" in report
    assert "Operational Cluster Count:" in report
    assert "Ready Operational Cluster Count:" in report
    assert "Cluster Operationalization Candidate Count:" in report
    assert "Cluster To Materialization Gap:" in report
    assert "Cluster To Citizen Gap:" in report
    assert "Cluster Operationalization Pressure:" in report
    assert "Cluster Operationalization State:" in report
    assert "Cluster Operationalization Action:" in report
    assert "Missing Operational Citizen Domains:" in report
    assert "Surviving Capabilities:" in report
    assert "Validation Gap Candidate Count:" in report
    assert "Unresolved Validation Gap Candidate Count:" in report
    assert "Crystallization Candidate Count:" in report
    assert "Quality To Citizen Crystallization Rate:" in report
    assert "Candidate To Citizen Crystallization Rate:" in report
    assert "Generated To Citizen Pressure Ratio:" in report
    assert "Capability Crystallization State:" in report
    assert "Capability Graduation Candidates:" in report
    assert "Capability Graduation Pressure:" in report
    assert "Capability Graduation Pressure State:" in report
    assert "World Governance Graduation Action:" in report
    assert "Capability Graduation Health:" in report
    assert "Graduation Pipeline Health:" in report
    assert "Graduation Success Rate:" in report
    assert "Graduation Failure Rate:" in report
    assert "Graduation Queue Health:" in report
    assert "Graduation Evidence Coverage:" in report
    assert "Graduation Infrastructure Readiness:" in report
    assert "Average Capability Graduation Time:" in report
    assert "Graduation Backlog Size:" in report
    assert "Capability Graduation Risk:" in report
    assert "Capability Graduation Complexity:" in report
    assert "Capability Graduation Confidence:" in report
    assert "Cognitive Citizens:" in report
    assert "Cognitive Citizenship Definition:" in report
    assert "World Governance Promotion Policy:" in report
    assert "Sandbox Citizenship Thresholds:" in report
    assert "Trusted Capability Policy:" in report
    assert "Decision Authority Policy:" in report
    assert "Validation Sponsorship Contract State:" in report
    assert "WORLD_GOVERNANCE_VALIDATION_SPONSOR" in report
    assert "Truth Preparation Gate:" in report
    assert "OPPORTUNITY_PERMISSION_ONLY" in report
    assert "Capability Merit System:" in report
    assert "VALIDATION_PRIORITY_ONLY" in report
    assert "Validation Sponsorship Truth Boundary:" in report
    assert "MERIT_NEVER_INFLUENCES_TRUTH_FORMATION" in report
    assert "Capability Governance Contract State:" in report
    assert "Capability Rights Policy:" in report
    assert "Capability Obligations Policy:" in report
    assert "Capability Reputation Average:" in report
    assert "Capability Trust Average:" in report
    assert "Capability Evidence Contamination State:" in report
    assert "Capability Evidence Contamination Count:" in report
    assert "Capability Stability Regression Count:" in report
    assert "Capability Population Evolution Speed:" in report
    assert "Operational Experience Growth Speed:" in report
    assert "Capability Population Evolution Lag:" in report
    assert "Capability Population Evolution State:" in report
    assert "Expected Operational Capability Count:" in report
    assert "Capability Population Evolution Gap:" in report
    assert "Target Experience Per Capability:" in report
    assert "Materialized Operational Capabilities:" in report
    assert "Operational Confidence State:" in report
    assert "Authority Transfer State:" in report
    assert "Decision Trust State:" in report
    assert "Trusted For Decision:" in report
    assert "Known Operational Capabilities:" in report
    assert "Operational Capability Population Target:" in report
    assert "Known Operational Operations:" in report
    assert "Known Operational Domains:" in report
    assert "Operational Domain Population Target:" in report
    assert "Capability Population Diversification:" in report
    assert "Reuse Evidence Count:" in report
    assert "Operational Experience Store:" in report
    assert "Capability Survival Store:" in report
    assert "Capability Survival State Distribution:" in report
    assert "Top Incubating Capabilities:" in report
    assert "Top Operational Citizens:" in report
    assert "basis=sandbox_governed_survival_evidence" in report
    assert "tier=SANDBOX_OPERATIONAL_CITIZEN" in report
    assert "authority=SANDBOX_REUSE_ONLY" in report
    assert "trust_state=NOT_TRUSTED_FOR_DECISION" in report
    assert (
        "Graduation Semantics: citizenship_is_sandbox_reuse_not_decision_authority"
        in report
    )
    assert "Capability Governance Contracts:" in report
    assert "rights=" in report
    assert "obligations=" in report
    assert "reputation=" in report
    assert "trust=" in report
    assert "evidence_state=ARENA_EXPOSURE_CONTAMINATION_RISK" in report
    assert "adjusted_accuracy=58.33%" in report
    assert "relevant_attempts=35" in report
    assert "arena_simulations=60" in report
    assert "Capability Evidence Contamination Risks:" in report
    assert "raw_avg=11.54%" in report
    assert "basis=relevant_task_attempt_accuracy" in report
    assert "Top Crystallization Candidates:" in report
    assert "operation=preserve_shape" in report
    assert "Top Graduation Candidates:" in report
    assert "operation=translate" in report
    assert "graduation_score=92%" in report
    assert "missing=exact_or_governed_validation_success" in report
    assert "validator=GOVERNED_VALIDATION_INCOMPLETE" in report
    assert "confidence=94.44%" in report
    assert "action=GRADUATION_SPRINT_REQUIRED" in report
    assert "Graduation Pipeline Stages:" in report
    assert "Capability Promotion Phase State:" in report
    assert "CAPABILITY_PROMOTION_PHASE_DETECTED" in report
    assert "Capability Promotion Candidate Count:" in report
    assert "Capability Promotion Interpretation:" in report
    assert "promotion_interprets_evidence_before_trust_or_graduation" in report
    assert "Evidence Acceptance State:" in report
    assert "GOVERNED_EVIDENCE_ACCEPTANCE_BOTTLENECK" in report
    assert "Evidence Acceptance Bottleneck:" in report
    assert "governed_validation_evidence_acceptance" in report
    assert "Evidence Acceptance Failure Count:" in report
    assert "Evidence Acceptance Failure Share:" in report
    assert "Evidence Sufficiency State:" in report
    assert "EVIDENCE_SUFFICIENCY_REVIEW_REQUIRED" in report
    assert "Evidence Sufficiency Question:" in report
    assert "when_is_evidence_sufficient_for_trust_update_and_graduation" in report
    assert "Evidence Sufficiency Contract:" in report
    assert "Evidence Contribution State:" in report
    assert "EVIDENCE_CONTRIBUTION_DIAGNOSTIC_AVAILABLE" in report
    assert "Highest Remaining Evidence Deficit:" in report
    assert "ground_truth" in report
    assert "Highest Remaining Evidence Deficit Action:" in report
    assert "select_ground_truth_aligned_validation_tasks" in report
    assert "Evidence Deficit Progress State:" in report
    assert "NO_PRIOR_EVIDENCE_DEFICIT_BASELINE" in report
    assert "Overall Evidence Progress:" in report
    assert "BASELINE" in report
    assert "Evidence Deficit Progress:" in report
    assert "Evidence Contribution:" in report
    assert "independent_validation:" in report
    assert "operational_reuse:" in report
    assert "Capability Promotion Candidates:" in report
    assert "operation=preserve_size" in report
    assert "promotion=high_quality_evidence_requires_acceptance_before_trust" in report
    assert "Graduation Pipeline Transitions:" in report
    assert "SURVIVING_CAPABILITY->COGNITIVE_CITIZEN" in report
    assert "Validator Failure Distribution:" in report
    assert "Governed Validation Incomplete=1" in report
    assert "Governed Validation Bottleneck:" in report
    assert "governed_validation_infrastructure" in report
    assert "Governed Validation Bottleneck State:" in report
    assert "GOVERNED_VALIDATION_INFRASTRUCTURE_BOTTLENECK" in report
    assert "Governed Validation Failure Count:" in report
    assert "Governed Validation Failure Share:" in report
    assert "Governed Validation Action:" in report
    assert "select_governed_validation_evidence_tasks" in report
    assert "Governed Validation Required Evidence:" in report
    assert "Graduation Sprint Recommendations:" in report
    assert "minimum_evidence=exact_or_governed_validation_success" in report
    assert "validation=exact_or_governed_validation" in report
    assert "single_run=TRUE" in report
    assert "Top Cognitive Citizens:" in report
    assert "operation=preserve_grid" in report
    assert "authority=SANDBOX_ONLY trusted=FALSE" in report
    assert "Top Stability Regressions:" in report
    assert "next=stability_recovery_evidence" in report
    assert "Operational Experience Task Count:" in report
    assert "Operational Experience Per Capability:" in report
    assert "Operational Specialization Pressure:" in report
    assert "Current Operational Exploration Rate:" in report
    assert "Current Operational Exploitation Rate:" in report
    assert "Known Operational Candidate Count:" in report
    assert "Novel Operational Candidate Count:" in report
    assert "Operational Exploration Target:" in report
    assert "Historical Exploitation Bias:" in report
    assert "Exploration Exploitation Balance State:" in report
    assert "Capability Monopoly Share:" in report
    assert "Capability Monopoly Pressure:" in report
    assert "Dominant Operational Capability:" in report
    assert "Dominant Capability Experience Count:" in report
    assert "Experienced Capability Count:" in report
    assert "Independent Reuse Capability Count:" in report
    assert "Domain Architecture State:" in report
    assert "Operational Domain Diagnostics:" in report
    assert "Operational Domain Expansion Gaps:" in report
    assert "Operational Domain Collaborations:" in report
    assert "Operational Domain Targets:" in report
    assert "Domain Expansion Roadmap:" in report
    assert "Cognitive Domain Architecture:" in report
    assert "gap=" in report
    assert "Missing Compiler Requirements: compiler_support" in report
    assert "Origin Sources: program_generation" in report
    assert "Normalized Sources: normalized_program_candidates" in report
    assert "Cross Source Consensus State: NO_CROSS_SOURCE_CONSENSUS" in report
    assert "Cross Source Consensus Count: 0" in report
    assert "Arena Source Diversity State: LOW_SOURCE_DIVERSITY" in report
    assert "Proposal Sources With Proposals:" in report
    assert (
        "Arena Source Diversity Action: SOURCE_DIVERSITY_SPRINT_REQUIRED"
        in report
    )
    assert "Candidate Source Flow Trace:" in report
    assert "reason=missing_program_representation" in report
    assert "detail=program_field_missing_or_not_mapping" in report
    assert "Arena To Compiled Bridge State: VALIDATION_PROBE_AVAILABLE" in report
    assert (
        "Arena To Compiled Bridge Action: "
        "route_validation_probe_to_compiler_without_prediction_authority"
    ) in report
    assert "Validation Probe Candidate: semantic_program:path_finding" in report
    assert "Validation Probe Authority: SANDBOX_VALIDATION_ONLY" in report
    assert "Object Grounding Flow State:" in report
    assert "Validation Probe Grounding Context Received:" in report
    assert "Validation Probe Grounding Expected Payload Keys:" in report
    assert "Validation Probe Grounding Received Payload Keys:" in report
    assert "Validation Probe Grounding Missing Payload Keys:" in report
    assert "Validation Probe Grounding Empty Payload Keys:" in report
    assert "Object Grounding Input Source:" in report
    assert "Arena Execution Recommendation Forwarded: TRUE" in report
    assert "Selected Arena Candidate Forwarded: FALSE" in report
    assert "Validation Probe Forwarded: TRUE" in report
    assert "Forwarded Validation Probe Candidate: semantic_program:path_finding" in report
    assert "Validation Probe Sandbox Validation Invoked: TRUE" in report
    assert "Validation Probe Result Captured: TRUE" in report
    assert "Validation Probe Comparable Output Captured: TRUE" in report
    assert "Validation Probe Evidence Acceptance Evaluated: TRUE" in report
    assert "Validation Probe Evidence Acceptance State: ACCEPTED" in report
    assert "Validation Probe Evidence Insufficiency Cause: NONE" in report
    assert "Validation Probe Required Evidence: evidence_contract_satisfied" in report
    assert (
        "Validation Probe Recommended Validation Action: retain_validation_evidence"
        in report
    )
    assert "Compiled To Validated Probe State: VALIDATION_PROBE_VALIDATED" in report
    assert "value=0.82 tier=HIGH_VALUE" in report
    assert "reason=concrete_task_execution_signal" in report
    assert (
        "raw=program_generation -> adapter=candidate_proposal_runtime -> "
        "normalized=normalized_program_candidates -> arena=normalized_program_candidates"
    ) in report


def test_render_includes_cognitive_domain_constitution_report():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    ecosystem_pos = report.index("COGNITIVE DOMAIN ECOSYSTEM REPORT")
    constitution_pos = report.index("COGNITIVE DOMAIN CONSTITUTION REPORT")
    compilation_pos = report.index("SEMANTIC COMPILATION")

    assert ecosystem_pos < constitution_pos < compilation_pos
    assert "Constitutional Status:" in report
    assert "Constitutional Integrity:" in report
    assert "Constitutional Violations:" in report
    assert "Domain Constitutional Health:" in report


def test_render_has_single_final_status_and_no_raw_dict_repr():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
    )

    assert report.count("NEXRYN :: FINAL STATUS") == 1
    assert "{'nested'" not in report
    assert "raw_nested_report" not in report


def test_full_report_includes_critical_execution_trace_before_conclusion():
    state = _report_state()
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": False,
        "failure_reason": "no_supported_compiler_for_execution_intents",
        "compiler_resolution_trace": [
            {
                "semantic_intent": "translate",
                "operation": "translate",
                "resolved_operation": "translate",
                "resolved_compiler": "TranslationCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": False,
                "resolution_state": "RESOLVED_COMPILER_FOUND_NO_CANDIDATE",
                "compiler_entry_payload": {
                    "operation": "translate",
                    "semantic_match_count": 2,
                    "execution_intent_count": 1,
                },
                "compiler_exit_payload": {
                    "candidate_count": 0,
                    "total_candidate_count": 0,
                    "best_accuracy": None,
                },
                "candidate_rejection_reason": "shape_contract_mismatch",
            }
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "CRITICAL EXECUTION TRACE" in report
    assert "Intent: translate" in report
    assert "Operation: translate" in report
    assert "Resolved Compiler: TranslationCompiler" in report
    assert "Candidate Emitted: FALSE" in report
    assert "Compiler Entry Payload: operation=translate" in report
    assert "Compiler Exit Payload: candidate_count=0" in report
    assert "Candidate Rejection Reason: shape_contract_mismatch" in report
    assert report.index("CRITICAL EXECUTION TRACE") < report.index(
        "ENGINEERING CONCLUSION"
    )


def test_engineering_conclusion_attributes_compiler_emission_failure():
    state = _report_state()
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": False,
        "failure_reason": "AMBIGUOUS_COLOR_MAPPING",
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symbolic_remapping",
                "operation": "replace_color",
                "resolved_operation": "replace_color",
                "resolved_compiler": "ColorRemapCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": False,
                "resolution_state": "RESOLVED_COMPILER_FOUND_NO_CANDIDATE",
                "candidate_rejection_reason": "AMBIGUOUS_COLOR_MAPPING",
                "compiler_entry_payload": {
                    "operation": "replace_color",
                    "semantic_match_count": 3,
                    "execution_intent_count": 1,
                    "input_grid_available": True,
                    "target_grid_available": True,
                    "source_color": 1,
                    "target_color": 3,
                    "mapping_count": 1,
                    "affected_cell_count": 2,
                },
                "compiler_exit_payload": {
                    "candidate_count": 0,
                    "valid_candidate_count": 0,
                    "rejected_candidate_count": 1,
                    "total_candidate_count": 0,
                    "composition_step_count": 0,
                    "mapping_count": 1,
                    "candidate_schema_valid": False,
                    "best_candidate_confidence": None,
                    "best_accuracy": None,
                    "rejection_reason": "AMBIGUOUS_COLOR_MAPPING",
                },
            }
        ],
        "compiler_operation_diagnostics": [
            {
                "operation": "replace_color",
                "composition_diagnostic_type": "color_remap",
                "mapping_extraction_state": "MAPPING_EXTRACTED",
                "relevant_execution_intent_count": 1,
                "relevant_semantic_matches": [
                    "symbolic_remapping",
                    "replace_color",
                    "replace_color_mapping",
                ],
                "source_color": 1,
                "target_color": 3,
                "mapping_count": 1,
                "affected_cell_count": 2,
                "preserved_color_count": 1,
                "composition_step_count": 0,
                "candidate_schema_valid": False,
                "parameter_source": "grid_delta",
                "rejection_reason": "COMPOSITION_VALIDATION_FAILED",
                "predicted_accuracy": 0.5,
                "predicted_accuracy_breakdown": {
                    "estimator": "exact_grid_cell_match_after_global_color_remap",
                    "accuracy_basis": "correct_cells / total_cells",
                    "correct_cell_count": 2,
                    "incorrect_cell_count": 2,
                    "total_cell_count": 4,
                    "changed_target_cell_count": 2,
                    "mapped_source_cell_count": 3,
                    "collateral_remap_cell_count": 1,
                    "dominant_accuracy_loss_cause": (
                        "GLOBAL_REMAP_COLLATERAL_MISMATCH"
                    ),
                },
                "validation_threshold": 0.75,
                "dominant_accuracy_loss_cause": (
                    "GLOBAL_REMAP_COLLATERAL_MISMATCH"
                ),
                "composition_validation_state": (
                    "PREDICTED_ACCURACY_BELOW_CANDIDATE_THRESHOLD"
                ),
                "candidate_object_created": False,
                "candidate_registered": False,
                "candidate_count_incremented": False,
                "proposal_emission_ready": False,
                "materialization_blocked_stage": "composition_validation",
                "materialization_rejection_reason": (
                    "PREDICTED_ACCURACY_BELOW_CANDIDATE_THRESHOLD"
                ),
            }
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Current Bottleneck: semantic_compiler_candidate_emission" in report
    assert "Root Cause: AMBIGUOUS_COLOR_MAPPING" in report
    assert "Exact Responsible Component: ColorRemapCompiler" in report
    assert "CANDIDATE_ARENA" not in report[
        report.index("ENGINEERING CONCLUSION"):
    ]


def test_critical_trace_backfills_missing_compiler_payload_from_resolution_row():
    state = _report_state()
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": False,
        "failure_reason": "COMPOSITION_VALIDATION_FAILED",
        "execution_intents": [
            {
                "intent": "symbolic_remapping",
                "operation": "replace_color",
                "matched_concepts": ["replace_color_mapping"],
            }
        ],
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symbolic_remapping",
                "operation": "replace_color",
                "resolved_operation": "replace_color",
                "resolved_compiler": "ColorRemapCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": False,
                "resolution_state": "RESOLVED_COMPILER_FOUND_NO_CANDIDATE",
                "candidate_rejection_reason": "COMPOSITION_VALIDATION_FAILED",
                "compiler_entry_payload": {
                    "operation": "Not Available",
                    "semantic_match_count": None,
                    "execution_intent_count": "Not Available",
                    "input_grid_available": None,
                    "target_grid_available": None,
                },
                "compiler_exit_payload": {
                    "candidate_count": "Not Available",
                    "valid_candidate_count": None,
                    "rejected_candidate_count": None,
                    "candidate_schema_valid": None,
                },
            }
        ],
        "compiler_operation_diagnostics": [
            {
                "operation": "replace_color",
                "composition_diagnostic_type": "color_remap",
                "mapping_extraction_state": "MAPPING_EXTRACTED",
                "relevant_execution_intent_count": 1,
                "relevant_semantic_matches": [
                    "symbolic_remapping",
                    "replace_color",
                    "replace_color_mapping",
                ],
                "source_color": 1,
                "target_color": 3,
                "mapping_count": 1,
                "affected_cell_count": 2,
                "preserved_color_count": 1,
                "composition_step_count": 0,
                "candidate_schema_valid": False,
                "parameter_source": "grid_delta",
                "rejection_reason": "COMPOSITION_VALIDATION_FAILED",
                "predicted_accuracy": 0.5,
                "predicted_accuracy_breakdown": {
                    "estimator": "exact_grid_cell_match_after_global_color_remap",
                    "accuracy_basis": "correct_cells / total_cells",
                    "correct_cell_count": 2,
                    "incorrect_cell_count": 2,
                    "total_cell_count": 4,
                    "changed_target_cell_count": 2,
                    "mapped_source_cell_count": 3,
                    "collateral_remap_cell_count": 1,
                    "dominant_accuracy_loss_cause": (
                        "GLOBAL_REMAP_COLLATERAL_MISMATCH"
                    ),
                },
                "validation_threshold": 0.75,
                "dominant_accuracy_loss_cause": (
                    "GLOBAL_REMAP_COLLATERAL_MISMATCH"
                ),
                "composition_validation_state": (
                    "PREDICTED_ACCURACY_BELOW_CANDIDATE_THRESHOLD"
                ),
                "candidate_object_created": False,
                "candidate_registered": False,
                "candidate_count_incremented": False,
                "proposal_emission_ready": False,
                "materialization_blocked_stage": "composition_validation",
                "materialization_rejection_reason": (
                    "PREDICTED_ACCURACY_BELOW_CANDIDATE_THRESHOLD"
                ),
            }
        ],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "validation_probe_shared_input_trace": {
                "input_population_state": "SHARED_TASK_IO_AVAILABLE",
                "non_empty_keys": ["input_grid", "target_grid"],
            }
        }
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Compiler Entry Payload: operation=replace_color" in report
    assert "execution_intents=1" in report
    assert "input_grid=TRUE" in report
    assert "target_grid=TRUE" in report
    assert "source_color=1" in report
    assert "target_color=3" in report
    assert "mapping_count=1" in report
    assert "affected_cells=2" in report
    assert "Mapping Extraction State: MAPPING_EXTRACTED" in report
    assert "Compiler Exit Payload: candidate_count=0" in report
    assert "predicted_accuracy=0.5" in report
    assert "validation_threshold=0.75" in report
    assert "Predicted Accuracy Breakdown: estimator=exact_grid_cell_match_after_global_color_remap" in report
    assert "correct=2/4" in report
    assert "collateral_remap_cells=1" in report
    assert "dominant_loss=GLOBAL_REMAP_COLLATERAL_MISMATCH" in report
    assert "Candidate Materialization:" in report
    assert "Composition Validation: PREDICTED_ACCURACY_BELOW_CANDIDATE_THRESHOLD" in report
    assert "Candidate Object Created: FALSE" in report
    assert "Candidate Registered: FALSE" in report
    assert "Candidate Count Incremented: FALSE" in report
    assert "Proposal Emission Ready: FALSE" in report
    assert "Blocked Stage: composition_validation" in report
    assert "Materialization Rejection: PREDICTED_ACCURACY_BELOW_CANDIDATE_THRESHOLD" in report
    critical_section = report[
        report.index("CRITICAL EXECUTION TRACE"):
        report.index("ENGINEERING CONCLUSION")
    ]
    assert "operation=Not Available" not in critical_section
    assert "semantic_matches=Not Available" not in critical_section
    assert "input_grid=Not Available" not in critical_section
    assert "target_grid=Not Available" not in critical_section


def test_critical_trace_renders_flat_predicted_accuracy_breakdown_fields():
    state = _report_state()
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": False,
        "failure_reason": "PREDICTED_ACCURACY_BELOW_CANDIDATE_THRESHOLD",
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symbolic_remapping",
                "operation": "replace_color",
                "resolved_compiler": "ColorRemapCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": False,
                "resolution_state": "RESOLVED_COMPILER_FOUND_NO_CANDIDATE",
                "candidate_rejection_reason": (
                    "PREDICTED_ACCURACY_BELOW_CANDIDATE_THRESHOLD"
                ),
                "compiler_exit_payload": {
                    "candidate_count": 0,
                    "predicted_accuracy": 0.0903,
                    "validation_threshold": 0.75,
                    "accuracy_estimator": (
                        "exact_grid_cell_match_after_global_color_remap"
                    ),
                    "correct_cell_count": 9,
                    "incorrect_cell_count": 91,
                    "total_cell_count": 100,
                    "changed_target_cell_count": 6,
                    "mapped_source_cell_count": 97,
                    "collateral_remap_cell_count": 91,
                    "dominant_accuracy_loss_cause": (
                        "GLOBAL_REMAP_COLLATERAL_MISMATCH"
                    ),
                },
            }
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Predicted Accuracy Breakdown:" in report
    assert "estimator=exact_grid_cell_match_after_global_color_remap" in report
    assert "correct=9/100" in report
    assert "incorrect=91" in report
    assert "changed_cells=6" in report
    assert "mapped_source_cells=97" in report
    assert "collateral_remap_cells=91" in report
    assert "dominant_loss=GLOBAL_REMAP_COLLATERAL_MISMATCH" in report


def test_critical_trace_distinguishes_compiler_row_from_entered_source_flow():
    state = _report_state()
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": True,
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symmetry_reasoning",
                "operation": "preserve_symmetry",
                "resolved_compiler": "PreservationCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": False,
                "resolution_state": "RESOLVED_COMPILER_FOUND_NO_CANDIDATE",
                "candidate_rejection_reason": "operation_semantics_mismatch",
                "compiler_exit_payload": {
                    "candidate_count": 0,
                    "composition_step_count": 0,
                    "candidate_schema_valid": False,
                    "preservation_contract_state": (
                        "PRESERVATION_CONTRACT_FAILED_TARGET_CHANGED"
                    ),
                    "changed_cell_count": 6,
                    "preserved_cell_count": 138,
                    "composition_validation_state": (
                        "PRESERVATION_CONTRACT_FAILED_TARGET_CHANGED"
                    ),
                },
            }
        ],
        "compiler_operation_diagnostics": [
            {
                "operation": "preserve_symmetry",
                "composition_diagnostic_type": "preservation",
                "preservation_contract_state": (
                    "PRESERVATION_CONTRACT_FAILED_TARGET_CHANGED"
                ),
                "changed_cell_count": 6,
                "preserved_cell_count": 138,
                "composition_step_count": 0,
                "candidate_schema_valid": False,
                "composition_validation_state": (
                    "PRESERVATION_CONTRACT_FAILED_TARGET_CHANGED"
                ),
                "rejection_reason": "operation_semantics_mismatch",
            }
        ],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "candidate_source_flow_trace": [
                {
                    "source": "semantic_to_transformation_compiler",
                    "normalized_source": "semantic_compiler",
                    "operation": "replace_color",
                    "proposal_runtime_proposed": True,
                    "arena_proposal_built": True,
                    "gateway_accepted": True,
                    "entered_arena": True,
                    "flow_state": "ENTERED_ARENA",
                    "blocked_stage": "none",
                    "build_failure_reason": "none",
                }
            ]
        }
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Operation: preserve_symmetry" in report
    assert "Failure Reason: operation_semantics_mismatch" in report
    assert (
        "Compiler/Flow Alignment: SOURCE_ENTERED_ARENA_WITH_DIFFERENT_OPERATION "
        "source_operation=replace_color"
    ) in report
    assert (
        "Preservation Contract: PRESERVATION_CONTRACT_FAILED_TARGET_CHANGED "
        "changed_cells=6 preserved_cells=138"
    ) in report
    assert "Operation Identity Chain:" in report
    assert "Identity State: OPERATION_IDENTITY_DRIFT" in report
    assert "Compiler Operation: preserve_symmetry" in report
    assert "Proposal Operation: replace_color" in report
    assert "First Drift Stage: compiler_to_proposal" in report
    assert "Drift Detail: compiler_to_proposal: preserve_symmetry != replace_color" in report


def test_critical_trace_prefers_selected_successful_compiler_operation():
    state = _report_state()
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": True,
        "selected_intent": "symbolic_remapping",
        "compiled_program": {
            "steps": [
                {"operation": "replace_color", "parameters": {"color_mapping": {0: 6}}}
            ]
        },
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symmetry_reasoning",
                "operation": "preserve_symmetry",
                "resolved_compiler": "PreservationCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": False,
                "resolution_state": "RESOLVED_COMPILER_FOUND_NO_CANDIDATE",
                "candidate_rejection_reason": "operation_semantics_mismatch",
            },
            {
                "semantic_intent": "symbolic_remapping",
                "operation": "replace_color",
                "resolved_compiler": "ColorRemapCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": True,
                "resolution_state": "RESOLVED_COMPILER_EMITTED_CANDIDATE",
                "candidate_rejection_reason": "none",
            },
        ],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "winner_operation": "replace_color",
            "validation_probe_operation": "replace_color",
            "candidate_source_flow_trace": [
                {
                    "source": "semantic_to_transformation_compiler",
                    "normalized_source": "semantic_compiler",
                    "operation": "replace_color",
                    "proposal_runtime_proposed": True,
                    "arena_proposal_built": True,
                    "gateway_accepted": True,
                    "entered_arena": True,
                    "flow_state": "ENTERED_ARENA",
                    "blocked_stage": "none",
                    "build_failure_reason": "none",
                }
            ],
        }
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Intent: symbolic_remapping" in report
    assert "Operation: replace_color" in report
    assert "Resolved Compiler: ColorRemapCompiler" in report
    assert "Candidate Emitted: TRUE" in report
    assert "Identity State: CONSISTENT" in report
    assert "Compiler Operation: replace_color" in report
    assert "Proposal Operation: replace_color" in report
    assert "operation_semantics_mismatch" not in report[
        report.index("CRITICAL EXECUTION TRACE"):
        report.index("ENGINEERING CONCLUSION")
    ]


def test_engineering_conclusion_uses_current_successful_compiler_path():
    state = _report_state()
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": True,
        "selected_intent": "symbolic_remapping",
        "compiled_program": {
            "steps": [
                {
                    "operation": "replace_color",
                    "parameters": {
                        "color_mapping": {0: 6},
                        "application_scope": "localized_changed_cells",
                        "affected_positions": [(1, 1), (1, 2)],
                    },
                }
            ]
        },
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symmetry_reasoning",
                "operation": "preserve_symmetry",
                "resolved_compiler": "PreservationCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": False,
                "resolution_state": "RESOLVED_COMPILER_FOUND_NO_CANDIDATE",
                "candidate_rejection_reason": "operation_semantics_mismatch",
            },
            {
                "semantic_intent": "symbolic_remapping",
                "operation": "replace_color",
                "resolved_compiler": "ColorRemapCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": True,
                "resolution_state": "RESOLVED_COMPILER_EMITTED_CANDIDATE",
                "candidate_rejection_reason": "none",
                "compiler_exit_payload": {
                    "candidate_count": 1,
                    "valid_candidate_count": 1,
                    "rejected_candidate_count": 0,
                    "composition_step_count": 1,
                    "candidate_schema_valid": True,
                    "predicted_accuracy": 1.0,
                    "selected_scope": "localized_changed_cells",
                    "candidate_object_created": True,
                    "candidate_registered": True,
                    "candidate_count_incremented": True,
                    "proposal_emission_ready": True,
                    "materialization_outcome": "CANDIDATE_EMITTED",
                    "materialization_completion_stage": "candidate_registered",
                    "materialization_blocked_stage": "none",
                    "materialization_rejection_reason": "none",
                },
            },
        ],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "arena_state": "TIE_REQUIRES_REVIEW",
            "candidate_count": 2,
            "unique_candidate_count": 2,
            "source_count": 2,
            "cross_source_consensus_count": 1,
            "cross_source_consensus_state": "CROSS_SOURCE_CONSENSUS",
            "sources_entered": [
                "normalized_program_candidates",
                "semantic_to_transformation_compiler",
            ],
            "simulation_count": 2,
            "simulation_success_count": 2,
            "selection_mode": "EVIDENCE_BASED_ARENA",
            "selection_state": "TIE_REQUIRES_REVIEW",
            "prediction_quality_calibration_state": "CALIBRATION_NOT_TRIGGERED",
            "winner_score": 0.778,
            "second_best_score": 0.778,
            "selection_margin": 0.0,
            "selection_explanation": "Top candidates are within tie margin.",
            "winner_operation": "replace_color",
            "validation_probe_candidate_id": "semantic_program:replace_color",
            "validation_probe_operation": "replace_color",
            "validation_probe_source": "semantic_to_transformation_compiler",
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
            "validation_probe_shared_input_trace": {
                "input_population_state": "SHARED_TASK_IO_AVAILABLE",
                "task_io_source_status": "failed_task_io_fallback",
                "present_keys": ["input_grid", "target_grid"],
                "empty_keys": [],
                "non_empty_keys": ["input_grid", "target_grid"],
            },
            "candidate_source_flow_trace": [
                {
                    "source": "semantic_to_transformation_compiler",
                    "normalized_source": "semantic_compiler",
                    "operation": "replace_color",
                    "proposal_runtime_proposed": True,
                    "arena_proposal_built": True,
                    "gateway_accepted": True,
                    "entered_arena": True,
                    "flow_state": "ENTERED_ARENA",
                    "blocked_stage": "none",
                    "build_failure_reason": "none",
                }
            ],
        }
    }
    state["EXECUTABLE_INTELLIGENCE_REPORT"] = {
        "validated_programs": [{"operation": "replace_color"}],
        "validation_probe_consumed": True,
        "validation_probe_evidence_acceptance_evaluated": True,
        "validation_probe_evidence_acceptance_state": "ACCEPTED",
        "execution_success_rate": 1.0,
    }
    state["COGNITIVE_CAPABILITY_COVERAGE_REPORT"] = {
        "knowledge_operationalization_choke_point": (
            "semantic_compiler_candidate_emission"
        ),
        "knowledge_operationalization_choke_cause": "operation_semantics_mismatch",
        "knowledge_operationalization_evidence_responsibility": (
            "PreservationCompiler"
        ),
        "knowledge_operationalization_choke_action": (
            "repair_preservationcompiler_candidate_composition"
        ),
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata={
            **_metadata(),
            "run_id": "run-current",
            "task_id": "task-localized-remap",
            "timestamp": "2026-07-29T00:00:00Z",
        },
    )

    critical = report[
        report.index("CRITICAL EXECUTION TRACE"):
        report.index("ENGINEERING CONCLUSION")
    ]
    assert "Materialization Outcome: CANDIDATE_EMITTED" in critical
    assert "Completion Stage: candidate_registered" in critical
    assert "Blocked Stage: none" in critical
    assert "Materialization Rejection: none" in critical
    assert "Candidate Outcome: CANDIDATE_EMITTED" in critical
    assert "Candidate Rejection Reason: none" in critical
    assert (
        "Prediction Quality Calibration Cause: "
        "TIE_WITH_ACCEPTED_VALIDATION_PROBE_EVIDENCE"
    ) in report
    assert (
        "Prediction Quality Calibration Action: "
        "perform_sandbox_evidence_ranking_recalibration"
    ) in report
    assert (
        "Prediction Quality Calibration Trigger: "
        "TIE_WITH_ACCEPTED_VALIDATION_PROBE_EVIDENCE"
    ) in report
    assert (
        "Prediction Quality Calibration Authority Boundary: "
        "SANDBOX_EVIDENCE_MAY_SUPPORT_RANKING_REVIEW_NOT_TRUTH"
    ) in report
    assert "Prediction Quality Calibration Invoked: TRUE" in report
    assert (
        "Prediction Quality Calibration Review Outcome: "
        "RANKING_REVIEW_ELIGIBLE_NO_TRUTH_AUTHORITY"
    ) in report
    assert "Prediction Quality Calibration Truth Authority: NONE" in report
    assert (
        "Arena Decision Resolution State: "
        "DECISION_RESOLUTION_PENDING_AFTER_CALIBRATION"
    ) in report
    assert "Arena Decision Resolution Outcome: TIE_CONFIRMED" in report
    assert "Arena Decision Ranking Changed: FALSE" in report
    assert (
        "Arena Decision Final State: "
        "SANDBOX_VALIDATION_COMPLETE_EXECUTION_DECISION_PENDING"
    ) in report
    assert (
        "Arena Decision Execution Recommendation: "
        "continue_sandbox_validation_or_escalate_governed_review"
    ) in report
    assert "Evidence Acquisition State: EVIDENCE_ACQUISITION_PLAN_READY" in report
    assert "Required Evidence Category: INDEPENDENT_GOVERNED_VALIDATION" in report
    assert (
        "Required Evidence: repeatable_independent_validation_evidence"
    ) in report
    assert "Tie-Break Strategy: independent_repeat_validation" in report
    assert (
        "Required Validation Task: "
        "select_independent_tie_break_validation_task"
    ) in report
    assert "Expected Tie-Break Impact: HIGH" in report
    assert "Evidence Acquisition Truth Authority: NONE" in report
    assert "Evidence Acquisition Plan Forwarded: TRUE" in report
    assert "Training Assistant Consumed Plan: FALSE" in report
    assert "Task Selection Consumed Plan: FALSE" in report
    assert "Tie-Break Task Scheduled: FALSE" in report
    assert "Decision Orchestration State: PLAN_FORWARDED_AWAITING_TASK_SELECTION" in report
    assert (
        "Validation Probe Shared Input Source Status: "
        "failed_task_io_fallback"
    ) in report
    assert (
        "Validation Probe Shared Input Fallback Reason: "
        "Original Task IO unavailable"
    ) in report
    assert (
        "Validation Probe Shared Input Recovered From: "
        "Cached Runtime Context"
    ) in report
    evidence_generation = report[
        report.index("EVIDENCE GENERATION REPORT"):
        report.index("COUNTERFACTUAL REASONING REPORT")
    ]
    assert "Generation Required: FALSE" in evidence_generation
    assert "Existing Tasks Found: Not Available" in evidence_generation
    assert (
        "Generation Status: "
        "AWAITING_TRAINING_ASSISTANT_CURRICULUM_SEARCH"
    ) in evidence_generation
    assert (
        "Constitutional Boundary: "
        "GENERATED_TASKS_ARE_VALIDATION_OPPORTUNITIES_NOT_EVIDENCE"
    ) in evidence_generation
    conclusion = report[
        report.index("ENGINEERING CONCLUSION"):
        report.index("FINAL STATUS")
    ]
    assert "Largest Success: validated_program_produced" in conclusion
    assert "Largest Regression: none" in conclusion
    assert (
        "Current Open Decision: "
        "DECISION_RESOLUTION_PENDING_AFTER_CALIBRATION"
    ) in conclusion
    assert (
        "Next Decision Gate: "
        "select_independent_tie_break_validation_task"
    ) in conclusion
    assert "Current Bottleneck: training_assistant_plan_consumption" in conclusion
    assert (
        "Root Cause: "
        "evidence_acquisition_plan_not_consumed_by_training_assistant"
    ) in conclusion
    assert (
        "Exact Responsible Component: "
        "TRAINING_ASSISTANT"
    ) in conclusion
    assert (
        "Immediate Next Development Task: "
        "select_independent_tie_break_validation_task"
    ) in conclusion
    assert "Engineering Conclusion Integrity: VALID" in conclusion
    assert "Conclusion Scope: current_run" in conclusion
    assert "Conclusion Run Id: run-current" in conclusion
    assert "Conclusion Task Id: task-localized-remap" in conclusion
    assert "Conclusion Source Stage: current_successful_critical_execution_trace" in conclusion
    assert "Conclusion Is Current: TRUE" in conclusion
    assert "Conclusion Historical Issue Count: 1" in conclusion
    assert "PreservationCompiler" not in conclusion
    assert "operation_semantics_mismatch" not in conclusion
    assert "repair_preservationcompiler_candidate_composition" not in conclusion


def test_engineering_conclusion_derives_ids_when_metadata_is_incomplete():
    state = _report_state()
    state["execution_id"] = "exec-from-state"
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": True,
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symbolic_remapping",
                "operation": "replace_color",
                "resolved_compiler": "ColorRemapCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": True,
                "resolution_state": "RESOLVED_COMPILER_EMITTED_CANDIDATE",
                "candidate_rejection_reason": "none",
            }
        ],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "selection_mode": "EVIDENCE_BASED_ARENA",
            "selection_state": "TIE_REQUIRES_REVIEW",
            "winner_score": 0.778,
            "second_best_score": 0.778,
            "selection_margin": 0.0,
            "validation_probe_candidate_id": "semantic_program:replace_color",
            "validation_probe_operation": "replace_color",
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
            "candidate_source_flow_trace": [
                {
                    "source": "semantic_to_transformation_compiler",
                    "operation": "replace_color",
                    "proposal_runtime_proposed": True,
                    "arena_proposal_built": True,
                    "gateway_accepted": True,
                    "entered_arena": True,
                }
            ],
        }
    }
    state["EXECUTABLE_INTELLIGENCE_REPORT"] = {
        "validation_probe_evidence_acceptance_state": "ACCEPTED",
        "execution_success_rate": 1.0,
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata={"timestamp": "2026-07-29T00:00:00Z"},
    )
    conclusion = report[
        report.index("ENGINEERING CONCLUSION"):
        report.index("FINAL STATUS")
    ]

    assert "Conclusion Run Id: exec-from-state" in conclusion
    assert "Conclusion Task Id: semantic_program:replace_color" in conclusion
    assert "Conclusion Run Id: Not Available" not in conclusion
    assert "Conclusion Task Id: Not Available" not in conclusion


def test_engineering_conclusion_treats_persisted_plan_as_cross_run_handoff():
    state = _report_state()
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": True,
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symbolic_remapping",
                "operation": "replace_color",
                "resolved_compiler": "ColorRemapCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": True,
                "resolution_state": "RESOLVED_COMPILER_EMITTED_CANDIDATE",
                "candidate_rejection_reason": "none",
            }
        ],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "selection_mode": "EVIDENCE_BASED_ARENA",
            "selection_state": "TIE_REQUIRES_REVIEW",
            "winner_score": 0.778,
            "second_best_score": 0.778,
            "selection_margin": 0.0,
            "source_count": 2,
            "cross_source_consensus_count": 1,
            "cross_source_consensus_state": "CROSS_SOURCE_CONSENSUS",
            "winner_operation": "replace_color",
            "validation_probe_candidate_id": "semantic_program:replace_color",
            "validation_probe_operation": "replace_color",
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
            "candidate_source_flow_trace": [
                {
                    "source": "semantic_to_transformation_compiler",
                    "operation": "replace_color",
                    "proposal_runtime_proposed": True,
                    "arena_proposal_built": True,
                    "gateway_accepted": True,
                    "entered_arena": True,
                }
            ],
        }
    }
    state["EXECUTABLE_INTELLIGENCE_REPORT"] = {
        "validated_programs": [{"operation": "replace_color"}],
        "validation_probe_evidence_acceptance_state": "ACCEPTED",
        "execution_success_rate": 1.0,
    }
    state["evidence_plan_store_report"] = {
        "evidence_plan_store_state": "READY",
        "evidence_plan_persistence_attempted": True,
        "evidence_plan_persisted": True,
        "evidence_plan_id": "evidence_plan_run_20260730_074151_a84f290c",
        "evidence_plan_fingerprint": "fingerprint-a84f290c",
        "evidence_plan_lifecycle_state": "PENDING_NEXT_RUN",
        "evidence_plan_storage_state": "NEW_PLAN_PERSISTED",
        "evidence_plan_storage_path": (
            "runtime/state/evidence_acquisition_plans/pending/"
            "evidence_plan_run_20260730_074151_a84f290c.json"
        ),
        "equivalent_pending_plan_found": False,
        "duplicate_persistence_prevented": False,
        "pending_evidence_plan_count": 1,
        "evidence_plans_loaded_at_boot": 0,
        "evidence_plans_delivered_to_training_assistant": 0,
        "training_assistant_plan_available": False,
        "current_run_consumption_expected": False,
        "next_run_consumption_required": True,
        "current_run_consumption_failure": False,
        "plan_persistence_failure_reason": "none",
        "plan_schema_version": "1.0",
        "plan_constitutional_boundary": (
            "EVIDENCE_ACQUISITION_PLAN_IS_A_GOVERNED_REQUEST_FOR_VALIDATION_NOT_EVIDENCE"
        ),
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )
    conclusion = report[
        report.index("ENGINEERING CONCLUSION"):
        report.index("FINAL STATUS")
    ]

    assert "Evidence Plan Persisted: TRUE" in report
    assert (
        "Decision Orchestration State: "
        "PLAN_PERSISTED_FOR_NEXT_RUN_CONSUMPTION"
    ) in report
    assert (
        "Training Assistant Current Run Consumption Expected: FALSE"
    ) in report
    assert "Training Assistant Next Run Consumption Required: TRUE" in report
    assert "Largest Success: evidence_acquisition_plan_persisted" in conclusion
    assert (
        "Current Bottleneck: next_run_training_assistant_plan_consumption"
    ) in conclusion
    assert (
        "Root Cause: cross_run_evidence_plan_awaiting_next_runtime"
    ) in conclusion
    assert (
        "Exact Responsible Component: "
        "TRAINING_ASSISTANT_ORCHESTRATION_HANDOFF"
    ) in conclusion
    assert (
        "Immediate Next Development Task: "
        "consume_persisted_evidence_plan_during_next_run"
    ) in conclusion
    assert (
        "evidence_acquisition_plan_not_consumed_by_training_assistant"
        not in conclusion
    )


def test_report_renders_boot_loaded_plan_delivered_to_training_assistant():
    state = _report_state()
    state["evidence_plan_store_report"] = {
        "evidence_plan_store_state": "READY",
        "evidence_plan_boot_load_state": "PENDING_PLAN_DELIVERED",
        "evidence_plan_persistence_attempted": False,
        "evidence_plan_persisted": False,
        "evidence_plan_id": "evidence_plan_run_20260730_074151_a84f290c",
        "evidence_plan_fingerprint": "fingerprint-a84f290c",
        "evidence_plan_lifecycle_state": "CONSUMPTION_PENDING",
        "evidence_plan_storage_state": "CONSUMPTION_PENDING",
        "pending_evidence_plan_count": 1,
        "evidence_plans_loaded_at_boot": 1,
        "evidence_plans_delivered_to_training_assistant": 1,
        "training_assistant_plan_available": True,
        "current_run_consumption_expected": True,
        "next_run_consumption_required": False,
        "current_run_consumption_failure": False,
        "plan_persistence_failure_reason": "none",
        "plan_schema_version": "1.0",
        "plan_constitutional_boundary": (
            "EVIDENCE_ACQUISITION_PLAN_IS_A_GOVERNED_REQUEST_FOR_VALIDATION_NOT_EVIDENCE"
        ),
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Evidence Plans Loaded At Boot: 1" in report
    assert "Evidence Plans Delivered To Training Assistant: 1" in report
    assert "Training Assistant Plan Available: TRUE" in report
    assert "Training Assistant Current Run Consumption Expected: TRUE" in report
    assert "Training Assistant Next Run Consumption Required: FALSE" in report
    assert (
        "Decision Orchestration State: "
        "PENDING_PLAN_DELIVERED_TO_TRAINING_ASSISTANT"
    ) in report
    assert "Training Assistant Consumed Plan: FALSE" in report


def test_delivered_inbound_plan_takes_precedence_over_outbound_duplicate_reuse():
    state = _report_state()
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": True,
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symbolic_remapping",
                "operation": "replace_color",
                "resolved_compiler": "ColorRemapCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": True,
                "resolution_state": "RESOLVED_COMPILER_EMITTED_CANDIDATE",
                "candidate_rejection_reason": "none",
            }
        ],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "selection_mode": "EVIDENCE_BASED_ARENA",
            "selection_state": "TIE_REQUIRES_REVIEW",
            "winner_score": 0.778,
            "second_best_score": 0.778,
            "selection_margin": 0.0,
            "source_count": 1,
            "cross_source_consensus_count": 0,
            "cross_source_consensus_state": "NO_CROSS_SOURCE_CONSENSUS",
            "source_dominance_detected": True,
            "winner_operation": "replace_color",
            "validation_probe_candidate_id": "semantic_program:replace_color",
            "validation_probe_operation": "replace_color",
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
            "candidate_source_flow_trace": [
                {
                    "source": "semantic_to_transformation_compiler",
                    "operation": "replace_color",
                    "proposal_runtime_proposed": True,
                    "arena_proposal_built": True,
                    "gateway_accepted": True,
                    "entered_arena": True,
                }
            ],
        }
    }
    state["EXECUTABLE_INTELLIGENCE_REPORT"] = {
        "validated_programs": [{"operation": "replace_color"}],
        "validation_probe_evidence_acceptance_state": "ACCEPTED",
        "execution_success_rate": 1.0,
    }
    state["evidence_plan_store_report"] = {
        "evidence_plan_persistence_attempted": True,
        "evidence_plan_persisted": False,
        "evidence_plan_id": "evidence_plan_run_20260730_074151_a84f290c",
        "evidence_plan_fingerprint": "fingerprint-a84f290c",
        "evidence_plan_lifecycle_state": "CONSUMPTION_PENDING",
        "evidence_plan_storage_state": "EQUIVALENT_PENDING_PLAN_REUSED",
        "equivalent_pending_plan_found": True,
        "duplicate_persistence_prevented": True,
        "pending_evidence_plan_count": 1,
        "evidence_plans_loaded_at_boot": 1,
        "evidence_plans_delivered_to_training_assistant": 1,
        "training_assistant_plan_available": False,
        "current_run_consumption_expected": False,
        "next_run_consumption_required": True,
        "current_run_consumption_failure": False,
        "inbound_evidence_plan_state": (
            "PLAN_AVAILABLE_FOR_CURRENT_RUN_CONSUMPTION"
        ),
        "outbound_evidence_plan_state": "EQUIVALENT_PENDING_PLAN_REUSED",
        "outbound_evidence_plan_id": (
            "evidence_plan_run_20260730_074151_a84f290c"
        ),
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )
    conclusion = report[
        report.index("ENGINEERING CONCLUSION"):
        report.index("FINAL STATUS")
    ]

    assert "Equivalent Pending Plan Found: TRUE" in report
    assert "Duplicate Persistence Prevented: TRUE" in report
    assert "Evidence Plans Loaded At Boot: 1" in report
    assert "Evidence Plans Delivered To Training Assistant: 1" in report
    assert "Training Assistant Plan Available: TRUE" in report
    assert "Training Assistant Current Run Consumption Expected: TRUE" in report
    assert "Training Assistant Next Run Consumption Required: FALSE" in report
    assert (
        "Decision Orchestration State: "
        "PENDING_PLAN_DELIVERED_TO_TRAINING_ASSISTANT"
    ) in report
    assert "Current Bottleneck: training_assistant_plan_consumption" in conclusion
    assert (
        "Root Cause: training_assistant_consumption_logic_not_implemented"
        in conclusion
    )
    assert (
        "Exact Responsible Component: "
        "TRAINING_ASSISTANT_EVIDENCE_PLAN_CONSUMER"
    ) in conclusion


def test_engineering_conclusion_advances_after_validation_task_selection():
    state = _report_state()
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": True,
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symbolic_remapping",
                "operation": "replace_color",
                "resolved_compiler": "ColorRemapCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": True,
                "resolution_state": "RESOLVED_COMPILER_EMITTED_CANDIDATE",
                "candidate_rejection_reason": "none",
            }
        ],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "selection_mode": "EVIDENCE_BASED_ARENA",
            "selection_state": "TIE_REQUIRES_REVIEW",
            "winner_score": 0.778,
            "second_best_score": 0.778,
            "selection_margin": 0.0,
            "source_count": 1,
            "cross_source_consensus_count": 0,
            "cross_source_consensus_state": "NO_CROSS_SOURCE_CONSENSUS",
            "source_dominance_detected": True,
            "winner_operation": "replace_color",
            "validation_probe_candidate_id": "semantic_program:replace_color",
            "validation_probe_operation": "replace_color",
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
            "candidate_source_flow_trace": [
                {
                    "source": "semantic_to_transformation_compiler",
                    "operation": "replace_color",
                    "proposal_runtime_proposed": True,
                    "arena_proposal_built": True,
                    "gateway_accepted": True,
                    "entered_arena": True,
                }
            ],
        }
    }
    state["EXECUTABLE_INTELLIGENCE_REPORT"] = {
        "validated_programs": [{"operation": "replace_color"}],
        "validation_probe_evidence_acceptance_state": "ACCEPTED",
        "execution_success_rate": 1.0,
    }
    state["training_economy_alignment_report"] = {
        "evidence_acquisition_plan_forwarded": True,
        "evidence_acquisition_plan_consumed": True,
        "training_assistant_consumed_plan": True,
        "evidence_acquisition_task_scheduled": True,
        "task_selection_consumed_plan": True,
        "tie_break_task_scheduled": True,
        "evidence_acquisition_selected_task": "elite_validation_task_31",
        "selected_tie_break_task": "elite_validation_task_31",
        "decision_orchestration_state": (
            "VALIDATION_TASK_SELECTED_AWAITING_EXECUTION"
        ),
        "consumption_state": "MATCHING_COMPLETED",
        "curriculum_search_state": "COMPLETED",
        "matching_validation_tasks": 5,
        "best_matching_task": "elite_validation_task_31",
        "best_matching_curriculum": "Elite Validation Academy",
        "matching_score": 118.0,
        "matching_explanation": "primary_required_evidence_match",
        "selection_authority": "TRAINING_ASSISTANT",
        "selection_state": "WAITING_EXECUTION",
        "waiting_execution": True,
        "generation_eligible": False,
        "generation_invoked": False,
        "waiting_generator": False,
        "evidence_plan_consumption_report": {
            "plans_delivered": 1,
            "plans_consumed": 1,
            "current_plan_id": "plan-cross-source",
            "lifecycle_state": "WAITING_EXECUTION",
            "consumption_state": "MATCHING_COMPLETED",
            "current_required_evidence": "cross_source_consensus_evidence",
            "current_required_validation_task": (
                "select_cross_source_tie_break_validation_task"
            ),
            "current_target_operation": "replace_color",
            "current_tie_break_strategy": "cross_source_consensus",
            "registered_curricula": 1,
            "loaded_curricula": 1,
            "enabled_curricula": 1,
            "disabled_curricula": 0,
            "curricula_searched": 1,
            "total_validation_tasks": 50,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "execution_authority": "NONE",
        },
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )
    conclusion = report[
        report.index("ENGINEERING CONCLUSION"):
        report.index("FINAL STATUS")
    ]

    assert "TRAINING ASSISTANT PLAN CONSUMPTION" in report
    assert "Training Assistant Consumed Plan: TRUE" in report
    assert "Curriculum Search: COMPLETED" in report
    assert "Matching Validation Tasks: 5" in report
    assert "Selection State: WAITING_EXECUTION" in report
    assert "Largest Success: training_assistant_consumed_evidence_plan" in conclusion
    assert "Current Open Decision: WAITING_VALIDATION_TASK_EXECUTION" in conclusion
    assert "Next Decision Gate: execute_selected_validation_task" in conclusion
    assert "Current Bottleneck: validation_execution_pipeline" in conclusion
    assert "Root Cause: validation_task_execution_not_started" in conclusion
    assert (
        "Exact Responsible Component: VALIDATION_EXECUTION_PIPELINE"
        in conclusion
    )


def test_engineering_conclusion_generates_run_id_from_timestamp_when_ids_missing():
    state = _report_state()
    state.pop("execution_id", None)
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": True,
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symbolic_remapping",
                "operation": "replace_color",
                "resolved_compiler": "ColorRemapCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": True,
                "resolution_state": "RESOLVED_COMPILER_EMITTED_CANDIDATE",
                "candidate_rejection_reason": "none",
            }
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata={"timestamp": "2026-07-29 13:34:26.116468"},
    )
    conclusion = report[
        report.index("ENGINEERING CONCLUSION"):
        report.index("FINAL STATUS")
    ]

    assert "Conclusion Run Id: run_20260729_133426" in conclusion
    assert "Conclusion Run Id: current_run_unidentified" not in conclusion


def test_critical_trace_reports_consistent_operation_identity_chain():
    state = _report_state()
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": True,
        "compiler_resolution_trace": [
            {
                "semantic_intent": "symbolic_remapping",
                "operation": "replace_color",
                "resolved_compiler": "ColorRemapCompiler",
                "compiler_found": True,
                "compilation_attempted": True,
                "candidate_emitted": True,
                "resolution_state": "RESOLVED_COMPILER_EMITTED_CANDIDATE",
                "candidate_rejection_reason": "none",
            }
        ],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "winner_operation": "replace_color",
            "validation_probe_operation": "replace_color",
            "candidate_source_flow_trace": [
                {
                    "source": "semantic_to_transformation_compiler",
                    "normalized_source": "semantic_compiler",
                    "operation": "replace_color",
                    "proposal_runtime_proposed": True,
                    "arena_proposal_built": True,
                    "gateway_accepted": True,
                    "entered_arena": True,
                    "flow_state": "ENTERED_ARENA",
                    "blocked_stage": "none",
                    "build_failure_reason": "none",
                }
            ],
        }
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Operation Identity Chain:" in report
    assert "Identity State: CONSISTENT" in report
    assert "Compiler Operation: replace_color" in report
    assert "Proposal Operation: replace_color" in report
    assert "Arena Operation: replace_color" in report
    assert "Validation Probe Operation: replace_color" in report
    assert "First Drift Stage: none" in report


def test_report_lifecycle_contract_boundaries_and_metadata_are_emitted():
    renderer = DeterministicFinalReportRenderer(console_budget_chars=100_000)
    report = renderer.render(_report_state(), runtime_metadata=_metadata())
    lines = report.splitlines()

    assert lines[:3] == [
        "=" * 50,
        REPORT_BEGIN_MARKER,
        "=" * 50,
    ]
    assert "Report Schema Version: 1.0" in report
    assert "Report Integrity: VALID" in report
    assert "Console Emission Started: TRUE" in report
    assert "NEXRYN MAIN RUNTIME" in report
    assert "Console Emission Completed: TRUE" in report
    assert lines[-3:] == [
        "=" * 50,
        REPORT_END_MARKER,
        "=" * 50,
    ]
    assert renderer.report()["report_integrity"] == "VALID"
    assert renderer.report()["console_emission_started"] is True
    assert renderer.report()["console_emission_completed"] is True


def test_render_does_not_begin_or_end_with_partial_structure():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
    )

    first_after_marker = report[
        report.find(REPORT_BEGIN_MARKER) + len(REPORT_BEGIN_MARKER):
    ].lstrip()
    assert first_after_marker.startswith("=")
    assert not report.rstrip().endswith(("{", "[", ":", ","))


def test_identical_inputs_render_identically():
    renderer = DeterministicFinalReportRenderer()

    first = renderer.render(_report_state(), runtime_metadata=_metadata())
    second = renderer.render(_report_state(), runtime_metadata=_metadata())

    assert first == second


def test_console_budget_fallback_remains_complete():
    state = _report_state()
    state["huge_diagnostic"] = "x" * 5000
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": False,
        "failure_reason": "no_supported_compiler_for_execution_intents",
        "compiler_resolution_trace": [
            {
                "semantic_intent": "unsupported_semantic",
                "operation": "density_modulation",
                "resolved_operation": "density_modulation",
                "resolved_compiler": "NONE",
                "compiler_found": False,
                "compilation_attempted": False,
                "candidate_emitted": False,
                "resolution_state": "RESOLVED_COMPILER_NOT_FOUND",
            }
        ],
    }
    renderer = DeterministicFinalReportRenderer(console_budget_chars=200)

    report = renderer.render(state, runtime_metadata=_metadata())

    assert REPORT_BEGIN_MARKER in report.splitlines()[:3]
    assert REPORT_END_MARKER in report.splitlines()[-3:]
    assert "Report Integrity: TRUNCATED" in report
    assert "Console Appendix: omitted" in report
    assert renderer.report()["report_truncated"] is True
    assert renderer.report()["report_complete"] is True
    assert renderer.report()["report_integrity"] == "TRUNCATED"
    assert "EXECUTIVE RUNTIME SUMMARY" in report
    assert "CANDIDATE PIPELINE" in report
    assert "RUNTIME CHOKE POINT" in report
    assert "SOURCE COMPETITION SUMMARY" in report
    assert "CRITICAL EXECUTION TRACE" in report
    assert "Compiler Resolution Trace:" in report
    assert "Resolved Compiler: NONE" in report
    assert "Resolution State: RESOLVED_COMPILER_NOT_FOUND" in report
    assert report.index("CRITICAL EXECUTION TRACE") < report.index(
        "ENGINEERING CONCLUSION"
    )
    assert "KNOWLEDGE OPERATIONALIZATION" in report
    assert "VALIDATION SUMMARY" in report
    assert "EXECUTION SUMMARY DASHBOARD" in report
    assert "RUNTIME HEALTH" in report
    assert "ENGINEERING CONCLUSION" in report
    assert "PROGRAM GENERATION REPORT" not in report


def test_console_budget_writes_full_text_artifact(tmp_path):
    state = _report_state()
    state["huge_diagnostic"] = "x" * 5000
    renderer = DeterministicFinalReportRenderer(console_budget_chars=200)

    console_report = renderer.render(
        state,
        runtime_metadata=_metadata(),
        artifact_directory=tmp_path,
        write_artifact=True,
    )

    artifact_text = (tmp_path / "runtime_report.txt").read_text(
        encoding="utf-8",
    )
    assert "Console Appendix: omitted" in console_report
    assert "Console Appendix: omitted" not in artifact_text
    assert REPORT_BEGIN_MARKER in artifact_text.splitlines()[:3]
    assert REPORT_END_MARKER in artifact_text.splitlines()[-3:]


def test_text_artifact_matches_rendered_report(tmp_path):
    renderer = DeterministicFinalReportRenderer(console_budget_chars=100_000)
    report = renderer.render(
        _report_state(),
        runtime_metadata=_metadata(),
        artifact_directory=tmp_path,
        write_artifact=True,
    )

    artifact = tmp_path / "runtime_report.txt"
    assert artifact.read_text(encoding="utf-8") == report
    assert renderer.report()["report_artifact_written"] is True


def test_duplicate_section_detection():
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(_report_state(), runtime_metadata=_metadata())
    invalid_report = report.replace(
        "FINAL STATUS",
        "FINAL STATUS\nFINAL STATUS",
        1,
    )

    errors = renderer.validate(invalid_report)

    assert "duplicate_section:FINAL STATUS" in errors


def test_normal_report_restores_per_stage_timing_visibility():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE STAGE TIMING" in report
    assert "TIMING HIERARCHY SUMMARY" in report
    assert "RESOURCE CONSUMPTION RANKING" in report
    assert "stage_name" in report
    assert "Reasoning" in report
    assert "Search" in report
    assert "Grid Analysis" in report
    assert "percentage_of_active_compute" in report
    assert "Top Three Exclusive-Time Consumers" in report
    assert "ACTIVE_COMPUTE_TIME" in report
    assert "REPORTING TIMING SUMMARY" in report
    assert "Report Lifecycle Total Time:" in report


def test_timing_summary_flags_task_selection_cost_pressure():
    state = _report_state()
    state["performance_report"]["stage_metrics"].append({
        "stage_name": "task_selection",
        "total_duration": 4.0,
        "execution_count": 1,
    })

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Task Selection Cost State: TASK_SELECTION_COST_PRESSURE" in report
    assert (
        "Task Selection Cost Action: profile_training_signal_loading_and_cache_reuse"
        in report
    )


def test_normal_report_exposes_semantic_compilation_observability():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "SEMANTIC COMPILATION" in report
    assert "Semantic Intent Router Success: TRUE" in report
    assert "Semantic Intent Router Integration: ROUTER_DRIVEN" in report
    assert "Compiler Activation Source: semantic_intent_router" in report
    assert "Execution Intents: 1" in report
    assert "Compiler Triggered: TRUE" in report
    assert "Compiled Candidates: 1" in report
    assert "Selected Intent: path_construction" in report
    assert "Compiled Operation: construct_path" in report
    assert "Selected From Compiler: TRUE" in report
    assert "Compiler Advisory State: SELECTED_EXECUTABLE" in report
    assert "Compilation Status: SUCCESS" in report
    assert "Execution Status: SUCCESS" in report


def test_semantic_compilation_reports_fallback_bridge_when_router_fails():
    state = _report_state()
    compiler_report = state["TRANSFORMATION_SYNTHESIS_REPORT"][
        "semantic_to_transformation_compilation_report"
    ]
    compiler_report["semantic_intent_routing_report"] = {
        "semantic_intent_routing_success": False,
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Semantic Intent Router Success: FALSE" in report
    assert "Semantic Intent Router Integration: FALLBACK_BRIDGE_ACTIVE" in report
    assert "Compiler Activation Source: program_generation_activation_bridge" in report


def test_semantic_compilation_reports_exact_match_advisory_not_selected():
    state = _report_state()
    compiler_report = state["TRANSFORMATION_SYNTHESIS_REPORT"][
        "semantic_to_transformation_compilation_report"
    ]
    state["TRANSFORMATION_SYNTHESIS_REPORT"]["selected_program"] = {
        "steps": [{"operation": "preserve_grid", "parameters": {}}],
        "step_count": 1,
    }
    compiler_report["validation"] = {
        "accuracy": 1.0,
        "exact_match": True,
        "shape_match": True,
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Selected From Compiler: FALSE" in report
    assert "Compiler Advisory State: ADVISORY_EXACT_MATCH_NOT_SELECTED" in report
    assert "Execution Status: NOT_SELECTED" in report


def test_normal_report_exposes_unified_concept_lifecycle():
    state = _report_state()
    state["semantic_attribution_report"] = {
        "attributed_concepts": [
            "gravity",
            "falling",
        ],
    }
    state["semantic_memory_report"] = {
        "Semantic Entities": [
            {
                "concept": "gravity",
                "semantic_memory_id": "sem:gravity",
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "UNIFIED CONCEPT LIFECYCLE REPORT" in report
    assert report.index("UNIFIED CONCEPT LIFECYCLE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Concept: gravity" in report
    assert "Semantic Cluster: Physics" in report
    assert "Mental Model: Gravity Simulation" in report
    assert "Execution Package: FALSE" in report
    assert "Semantic Memory Integration: TRUE" in report
    assert "Lifecycle Status: DISCOVERED_BUT_NOT_EXECUTABLE" in report


def test_normal_report_exposes_program_generation_blueprints():
    state = _report_state()
    state["semantic_attribution_report"] = {
        "attributed_concepts": [
            "rotation",
            "gravity",
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "PROGRAM GENERATION REPORT" in report
    assert report.index("UNIFIED CONCEPT LIFECYCLE REPORT") < report.index("PROGRAM GENERATION REPORT")
    assert report.index("PROGRAM GENERATION REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Generated Blueprints:" in report
    assert "Program: Rotation Program" in report
    assert "Concept: rotation" in report
    assert "Generation Status: GENERATED" in report
    assert "Candidate Ready: FALSE" in report
    assert "Missing Requirements: candidate_proposal_support" in report


def test_normal_report_exposes_program_blueprint_intelligence():
    state = _report_state()
    state["PROGRAM_GENERATION_REPORT"] = {
        "program_blueprints": [
            {
                "program_id": "program_blueprint:gravity",
                "concept_name": "gravity",
                "semantic_cluster": "Physics",
                "program_type": "gravity_program",
                "compiler_supported": "TRUE",
                "generation_success": "FALSE",
                "generation_status": "BLOCKED",
                "execution_package_available": "FALSE",
                "candidate_ready": "FALSE",
                "missing_requirements": ["gravity_execution_package"],
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "PROGRAM BLUEPRINT INTELLIGENCE REPORT" in report
    assert report.index("PROGRAM GENERATION REPORT") < report.index("PROGRAM BLUEPRINT INTELLIGENCE REPORT")
    assert report.index("PROGRAM BLUEPRINT INTELLIGENCE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Program: Gravity Program" in report
    assert "Semantic Family: Physics" in report
    assert "Mental Model: Gravity Simulation" in report
    assert "Execution Readiness: MISSING_PACKAGE" in report
    assert "Candidate Readiness: WAITING_FOR_EXECUTION_PACKAGE" in report
    assert "Required Packages: gravity_execution_package" in report
    assert "Capability Status: WAITING_FOR_EXECUTION_PACKAGE" in report


def test_normal_report_exposes_cognitive_program_lifecycle():
    state = _report_state()
    state["PROGRAM_BLUEPRINT_INTELLIGENCE_REPORT"] = {
        "program_blueprint_intelligence": [
            {
                "blueprint_id": "program_intelligence:gravity_program",
                "program_type": "gravity_program",
                "semantic_family": "Physics",
                "mental_model": "Gravity Simulation",
                "supported_concepts": ["gravity", "falling"],
                "compiler_supported": "TRUE",
                "execution_ready": "MISSING_PACKAGE",
                "candidate_ready": "WAITING_FOR_EXECUTION_PACKAGE",
                "validation_ready": "FALSE",
                "required_packages": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                    "gravity_validation_support",
                ],
                "missing_requirements": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                    "gravity_validation_support",
                ],
                "capability_profile": {
                    "semantic_capabilities": ["gravity", "falling"],
                },
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE PROGRAM LIFECYCLE REPORT" in report
    assert report.index("PROGRAM BLUEPRINT INTELLIGENCE REPORT") < report.index("COGNITIVE PROGRAM LIFECYCLE REPORT")
    assert report.index("COGNITIVE PROGRAM LIFECYCLE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Program: Gravity Program" in report
    assert "Lifecycle Status: PACKAGE_REQUIREMENTS_IDENTIFIED" in report
    assert "Maturity Level: FOUNDATIONAL" in report
    assert "Execution Readiness: NOT_READY" in report
    assert "Candidate Readiness: NOT_READY" in report
    assert "Operational Readiness: NOT_READY" in report
    assert "Lifecycle Failures: EXECUTION_REQUIREMENTS_VALIDATED:NO_EXECUTION_PACKAGE" in report


def test_normal_report_exposes_cognitive_knowledge_domains():
    state = _report_state()
    state["semantic_attribution_report"] = {
        "attributed_concepts": [
            "gravity",
            "falling",
        ],
    }
    state["PROGRAM_BLUEPRINT_INTELLIGENCE_REPORT"] = {
        "program_blueprint_intelligence": [
            {
                "blueprint_id": "program_intelligence:gravity_program",
                "program_type": "gravity_program",
                "semantic_family": "Physics",
                "mental_model": "Gravity Simulation",
                "supported_concepts": ["gravity", "falling", "support"],
                "compiler_supported": "TRUE",
                "execution_ready": "MISSING_PACKAGE",
                "candidate_ready": "WAITING_FOR_EXECUTION_PACKAGE",
                "validation_ready": "FALSE",
                "required_packages": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                    "gravity_validation_support",
                ],
                "missing_requirements": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                    "gravity_validation_support",
                ],
                "capability_profile": {
                    "semantic_capabilities": ["gravity", "falling"],
                },
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE KNOWLEDGE DOMAINS REPORT" in report
    assert report.index("COGNITIVE PROGRAM LIFECYCLE REPORT") < report.index("COGNITIVE KNOWLEDGE DOMAINS REPORT")
    assert report.index("COGNITIVE KNOWLEDGE DOMAINS REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Domain: Physics Domain" in report
    assert "Semantic Families: Physics" in report
    assert "Mental Models: Gravity Simulation" in report
    assert "Program Blueprints: gravity_program" in report
    assert "Concept Count:" in report
    assert "Missing Capabilities:" in report
    assert "gravity_execution_package" in report
    assert "gravity_candidate_support" in report
    assert "gravity_validation_support" in report
    assert "Silent Domain Assignment Failures: FALSE" in report


def test_normal_report_exposes_cognitive_domain_intelligence():
    state = _report_state()
    state["COGNITIVE_KNOWLEDGE_DOMAINS_REPORT"] = {
        "domains": [
            {
                "domain_id": "domain:spatial",
                "domain_name": "Spatial Domain",
                "semantic_families": ["Spatial"],
                "semantic_concepts": ["relative_position"],
                "mental_models": ["Spatial Reasoning"],
            },
            {
                "domain_id": "domain:identity",
                "domain_name": "Identity Domain",
                "semantic_families": ["Identity"],
                "semantic_concepts": ["object_identity_preservation"],
                "mental_models": ["Object Identity"],
            },
            {
                "domain_id": "domain:topology",
                "domain_name": "Topology Domain",
                "semantic_families": ["Topology"],
                "mental_models": ["Topology Reasoning"],
                "program_blueprints": ["topology_program"],
                "semantic_concepts": ["bridge_creation", "topology_change"],
                "execution_packages": ["topology_execution_package"],
                "operational_capabilities": ["topology_execution"],
                "missing_capabilities": ["topology_candidate_support"],
                "maturity_level": "PARTIALLY_OPERATIONAL",
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE DOMAIN INTELLIGENCE REPORT" in report
    assert report.index("COGNITIVE KNOWLEDGE DOMAINS REPORT") < report.index("COGNITIVE DOMAIN INTELLIGENCE REPORT")
    assert report.index("COGNITIVE DOMAIN INTELLIGENCE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Domain Name: Topology Domain" in report
    assert "Semantic Capabilities: bridge_creation, topology_change" in report
    assert "Operational Capabilities: topology_execution" in report
    assert "Domain Dependencies: Spatial Domain, Identity Domain" in report
    assert "Mental Models: Topology Reasoning" in report
    assert "Program Blueprints: topology_program" in report
    assert "Execution Packages: topology_execution_package" in report
    assert "Missing Capabilities: topology_candidate_support" in report
    assert "Domain Readiness: PARTIALLY_OPERATIONAL" in report


def test_normal_report_exposes_cognitive_domain_lifecycle():
    state = _report_state()
    state["COGNITIVE_DOMAIN_INTELLIGENCE_REPORT"] = {
        "domain_intelligence": [
            {
                "domain_id": "domain:spatial",
                "domain_name": "Spatial Domain",
                "semantic_capabilities": ["relative_position"],
                "mental_models": ["Spatial Reasoning"],
            },
            {
                "domain_id": "domain:geometry",
                "domain_name": "Geometry Domain",
                "semantic_capabilities": ["shape_geometry"],
                "mental_models": ["Geometry Reasoning"],
            },
            {
                "domain_id": "domain:physics",
                "domain_name": "Physics Domain",
                "semantic_capabilities": ["gravity", "falling", "collision"],
                "mental_models": ["Gravity Simulation"],
                "program_blueprints": ["physics_program"],
                "missing_capabilities": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                ],
                "required_domains": ["Spatial Domain", "Geometry Domain"],
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE DOMAIN LIFECYCLE REPORT" in report
    assert report.index("COGNITIVE DOMAIN INTELLIGENCE REPORT") < report.index("COGNITIVE DOMAIN LIFECYCLE REPORT")
    assert report.index("COGNITIVE DOMAIN LIFECYCLE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Domain Name: Physics Domain" in report
    assert "Lifecycle Stage: PROGRAM_DEFINED" in report
    assert "Maturity Level: DEVELOPING" in report
    assert "Semantic=READY" in report
    assert "Mental Models=READY" in report
    assert "Programs=READY" in report
    assert "Execution=NOT_READY" in report
    assert "Candidate=NOT_READY" in report
    assert "Dependencies: Spatial Domain, Geometry Domain" in report
    assert "Missing Capabilities: gravity_execution_package, gravity_candidate_support" in report
    assert "Lifecycle Failures: EXECUTION_DEFINED:physics_execution_package_missing" in report


def test_normal_report_exposes_cognitive_domain_interaction():
    state = _report_state()
    state["COGNITIVE_DOMAIN_LIFECYCLE_REPORT"] = {
        "domain_registry": [
            {
                "domain_name": "Physics Domain",
                "semantic_capability_evolution": ["gravity"],
                "required_domains": ["Spatial Domain", "Geometry Domain"],
                "operational_capability_evolution": ["object_motion_reasoning"],
            },
            {
                "domain_name": "Spatial Domain",
                "semantic_capability_evolution": ["relative_position"],
            },
            {
                "domain_name": "Geometry Domain",
                "semantic_capability_evolution": ["object_shape"],
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE DOMAIN INTERACTION REPORT" in report
    assert report.index("COGNITIVE DOMAIN LIFECYCLE REPORT") < report.index("COGNITIVE DOMAIN INTERACTION REPORT")
    assert report.index("COGNITIVE DOMAIN INTERACTION REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Domain Name: Physics Domain" in report
    assert "Collaborating Domains: Spatial Domain, Geometry Domain" in report
    assert "Shared Capabilities: object_motion_reasoning" in report
    assert "Private Capabilities: collision_simulation" in report
    assert "Dependency Relationships: Spatial Domain, Geometry Domain" in report
    assert "Operational Capability Composition: Object Falling Simulation" in report
    assert "Cross-Domain Readiness:" in report
    assert "Operational Capability Lifecycle Count:" in report
    assert "Capability Promotion Candidates:" in report
    assert "Sandbox Operational Capabilities:" in report
    assert "Reusable Operational Capabilities:" in report
    assert "Capability Organisms:" in report
    assert "Emerging Capabilities:" in report
    assert "Capability Economy Watch:" in report
    assert "Capability Lifecycle:" in report
    assert "Capability Promotion:" in report
    assert "Capability Growth:" in report
    assert "Capability Identity:" in report
    assert "Capability Economy:" in report
    assert "Capability Resource Budget:" in report
    assert "Blocking Stage:" in report
    assert "Governance:" in report
    assert "Missing Collaborative Capabilities: Not Available" in report


def test_normal_report_exposes_cognitive_domain_governance():
    state = _report_state()
    state["COGNITIVE_DOMAIN_LIFECYCLE_REPORT"] = {
        "domain_registry": [
            {
                "domain_name": "Transformation Domain",
                "lifecycle_stage": "PROGRAM_DEFINED",
                "maturity_level": "DEVELOPING",
                "semantic_capability_evolution": ["rotation", "gravity"],
                "required_domains": ["Geometry Domain"],
            },
            {
                "domain_name": "Geometry Domain",
                "semantic_capability_evolution": ["object_shape"],
            },
        ],
    }
    state["COGNITIVE_DOMAIN_INTERACTION_REPORT"] = {
        "domain_interaction_reports": [],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE DOMAIN GOVERNANCE REPORT" in report
    assert report.index("COGNITIVE DOMAIN INTERACTION REPORT") < report.index("COGNITIVE DOMAIN GOVERNANCE REPORT")
    assert report.index("COGNITIVE DOMAIN GOVERNANCE REPORT") < report.index("SEMANTIC COMPILATION")
    assert "Domain Name: Transformation Domain" in report
    assert "Governance Status: BOUNDARY_VIOLATION" in report
    assert "Semantic Integrity:" in report
    assert "Ownership Integrity:" in report
    assert "Dependency Integrity:" in report
    assert "Domain Health Score:" in report
    assert "Boundary Violations:" in report


def test_normal_report_exposes_prediction_provenance_decision_owner():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "TRANSFORMATION DECISION" in report
    assert "Prediction Source: semantic_to_transformation_compiler" in report
    assert "Decision Owner: Semantic-to-Transformation Compiler" in report
    assert "Winning Candidate: construct_path" in report
    assert "Selected Operation: construct_path" in report
    assert "Compiler Participation: TRUE" in report
    assert "Program Validation: SUCCESS" in report
    assert "Generated Concepts Observed: 2.0" in report
    assert "Program Candidates: 1.0" in report
    assert "Decision Pipeline: Semantic Attribution -> Pattern Analysis -> Rule Analysis" in report


def test_prediction_provenance_reports_unresolved_when_success_source_is_missing():
    state = _report_state()
    state.pop("TRANSFORMATION_SYNTHESIS_REPORT")
    state["EVALUATION_REPORT"] = {
        "accuracy": 1.0,
        "success_state": "EXACT_SUCCESS",
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "TRANSFORMATION DECISION" in report
    assert "Prediction Source: Not Available" in report
    assert "Decision Owner: UNRESOLVED" in report
    assert "Program Validation: EXACT_SUCCESS" in report
    assert "Prediction Accuracy: 1" in report


def test_prediction_provenance_identifies_noncompiler_winning_program():
    state = _report_state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"][
        "semantic_to_transformation_compilation_report"
    ] = {
        "semantic_to_transformation_compilation_success": False,
        "detected_intents": ["inside_outside"],
        "compiled_program": {"steps": [], "step_count": 0},
        "candidate_count": 0,
        "failure_reason": "no_supported_semantic_delta",
        "validation": {"accuracy": 0.0, "exact_match": False},
    }
    state["TRANSFORMATION_SYNTHESIS_REPORT"]["transformation_accuracy"] = 1.0

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Compiler Participation: FALSE" in report
    assert "Prediction Source: transformation_synthesis" in report
    assert "Decision Owner: Transformation Synthesis Engine" in report
    assert "Selected Operation: construct_path" in report
    assert "Program Validation: SUCCESS" in report


def test_candidate_arena_reports_adaptive_reuse_single_source_dominance():
    state = _report_state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": ["bridge_creation", "component_connection"],
        "semantic_to_transformation_compilation_report": {
            "semantic_to_transformation_compilation_success": False,
            "detected_intents": ["bridge_creation", "component_connection"],
            "execution_intents": [],
            "semantic_intent_routing_report": {
                "semantic_intent_routing_success": False,
                "execution_intent_count": 0,
            },
            "candidate_count": 0,
            "compiled_program": {"steps": [], "step_count": 0},
            "failure_reason": "no_executable_semantic_intents",
        },
    }
    state["ADAPTIVE_REUSE_REPORT"] = {
        "reuse_success_rate": 1.0,
        "reused_programs": [
            {
                "steps": [
                    {
                        "operation": "inside_outside_reuse",
                        "parameters": {},
                    }
                ],
                "step_count": 1,
            }
        ],
    }
    state["PREDICTION_PROVENANCE_REPORT"] = {
        "prediction_source": "adaptive_reuse",
        "decision_owner": "Adaptive Reuse Layer",
        "winning_candidate": "adaptive_reuse_decision",
        "decision_confidence": 1.0,
        "program_validation": "SUCCESS",
        "prediction_accuracy": 1.0,
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE CANDIDATE ARENA" in report
    assert "Arena State: SINGLE_SOURCE_DOMINANCE" in report
    assert "Attempted Candidates: 2" in report
    assert "Explicit Rejections: 1" in report
    assert "Competitor Sources: adaptive_reuse" in report
    assert "Source Diversity Bottleneck:" in report
    assert "Candidate Source Materialization Gap Count:" in report
    assert "Candidate Source Materialization State:" in report
    assert "Candidate Source Materialization:" in report
    assert "Winner Takes All Detected: TRUE" in report
    assert "Dominance Source: adaptive_reuse" in report
    assert "Compiler Attempted: TRUE" in report
    assert "semantic_to_transformation_compiler: REJECTED reason=no_executable_semantic_intents" in report
    assert "Missing Competition Reason: Only one candidate source entered the arena." in report


def test_report_marks_selected_compiler_without_report_as_attempted_rejection():
    state = _report_state()
    state.pop("TRANSFORMATION_SYNTHESIS_REPORT")
    state["tool_selection_report"] = {
        "enabled_tools": ["semantic_to_transformation_compiler"],
    }
    state["ADAPTIVE_REUSE_REPORT"] = {
        "reuse_success_rate": 1.0,
        "reused_programs": [
            {
                "steps": [
                    {
                        "operation": "adaptive_reuse_program",
                        "parameters": {},
                    }
                ],
                "step_count": 1,
            }
        ],
    }
    state["PREDICTION_PROVENANCE_REPORT"] = {
        "prediction_source": "adaptive_reuse",
        "decision_owner": "Adaptive Reuse Layer",
        "winning_candidate": "adaptive_reuse_program",
        "program_validation": "SUCCESS",
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Compiler Triggered: TRUE" in report
    assert "Compilation Status: REQUIRED_REPORT_MISSING" in report
    assert "Compiler Attempted: TRUE" in report
    assert "CANDIDATE PROPOSAL PHASE" in report
    assert report.index("CANDIDATE PROPOSAL PHASE") < report.index("COGNITIVE CANDIDATE ARENA")
    assert "Proposal Phase Entered: TRUE" in report
    assert "Sources Rejected: semantic_to_transformation_compiler" in report
    assert "Attempted Candidates: 2" in report


def test_candidate_proposal_phase_renders_adaptive_reuse_admission_trace():
    state = _report_state()
    state["CANDIDATE_PROPOSAL_REPORT"] = {
        "proposal_phase_entered": True,
        "proposal_phase_status": "SINGLE_SOURCE",
        "eligible_source_count": 1,
        "proposal_count": 0,
        "explicit_rejection_count": 1,
        "sources_with_proposals": [],
        "sources_rejected": ["adaptive_reuse"],
        "knowledge_investment_policy": "OPERATIONAL_VALUE_PRIORITIZED",
        "knowledge_investment_authority": "candidate_proposal_runtime",
        "candidate_proposals": [
            {
                "source": "adaptive_reuse",
                "proposal_status": "REJECTED",
                "rejection_reason": "COGNITIVE_REUSE_ONLY",
            }
        ],
        "adaptive_reuse_admission_trace": [
            {
                "stage": "candidate_source_map",
                "reuse_status": "COGNITIVE_REUSE_ONLY",
                "reuse_output_mode": "COGNITIVE_REUSE_ONLY",
                "arena_admission_eligible": False,
                "reused_strategy_count": 3,
                "reused_program_count": 0,
                "program_steps_count": 0,
                "operational_independent_reuse_success_count": 32,
                "candidate_payload_present": False,
                "proposal_rejection_reason": None,
            },
            {
                "stage": "candidate_proposal_runtime",
                "reuse_status": "COGNITIVE_REUSE_ONLY",
                "reuse_output_mode": "COGNITIVE_REUSE_ONLY",
                "arena_admission_eligible": False,
                "reused_strategy_count": 3,
                "reused_program_count": 0,
                "program_steps_count": 0,
                "operational_independent_reuse_success_count": 32,
                "candidate_payload_present": False,
                "proposal_candidate_detected": False,
                "proposal_rejection_reason": "COGNITIVE_REUSE_ONLY",
            },
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Adaptive Reuse Admission Trace:" in report
    assert "candidate_source_map: status=COGNITIVE_REUSE_ONLY" in report
    assert "mode=COGNITIVE_REUSE_ONLY" in report
    assert "eligible=FALSE" in report
    assert "independent_reuse=32" in report
    assert "reason=COGNITIVE_REUSE_ONLY" in report


def test_report_exposes_executable_semantic_coverage():
    state = _report_state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"]["detected_concepts"] = [
        "density_increase",
        "symmetry_break",
        "relative_position",
        "spatial_relation",
        "transformation_sequence",
        "bridge_creation",
        "component_connection",
        "connectivity_change",
        "topology_change",
        "density_modulation",
        "growth",
        "propagation",
        "directional_motion",
        "position_preservation",
        "object_identity_preservation",
        "shape_preservation",
        "rotation",
        "reflection",
    ]
    state["TRANSFORMATION_SYNTHESIS_REPORT"].pop(
        "semantic_to_transformation_compilation_report",
    )

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "EXECUTABLE SEMANTIC COVERAGE" in report
    assert report.index("EXECUTABLE SEMANTIC COVERAGE") < report.index("TRANSFORMATION DECISION")
    assert "Generated Concepts: 18" in report
    assert "Executable Concepts: 13" in report
    assert "Unsupported Concepts: 5" in report
    assert "Coverage Status: HIGH" in report
    assert "Unsupported Operations:" in report
    assert "preserve_shape" in report
    assert "density_modulation" in report


def test_report_marks_executable_coverage_not_measurable_without_concept_inputs():
    state = _report_state()
    state["generated_concepts"] = 18
    state["TRANSFORMATION_SYNTHESIS_REPORT"].pop(
        "detected_concepts",
        None,
    )
    state["TRANSFORMATION_SYNTHESIS_REPORT"].pop(
        "semantic_to_transformation_compilation_report",
    )

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Generated Concepts: 18" in report
    assert "Measured Concepts: 0" in report
    assert "Coverage State: NOT_MEASURABLE" in report
    assert "Coverage: Not Available" in report
    assert "Coverage Status: NOT_MEASURABLE" in report
    assert "Measurement Blocker: NO_UNIFIED_CONCEPT_INPUT" in report


def test_report_uses_lifecycle_concepts_for_executable_coverage():
    state = _report_state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"].pop(
        "detected_concepts",
        None,
    )
    state["TRANSFORMATION_SYNTHESIS_REPORT"].pop(
        "semantic_to_transformation_compilation_report",
    )
    state["concept_lifecycle_report"] = {
        "concepts": [
            {"concept": "component_splitting"},
            {"concept": "connectivity_change"},
            {"concept": "topology_change"},
        ],
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Measured Concepts: 3" in report
    assert "Executable Concepts: 2" in report
    assert "Unsupported Concepts: 1" in report
    assert "component_splitting" in report


def test_candidate_arena_reports_competitive_sources_when_multiple_enter():
    state = _report_state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"]["ranked_candidates"] = [
        {
            "program": state["TRANSFORMATION_SYNTHESIS_REPORT"]["selected_program"],
            "score": 0.91,
            "prediction_accuracy": 1.0,
        },
        {
            "program": {
                "steps": [
                    {
                        "operation": "fill_region",
                        "parameters": {},
                    }
                ],
                "step_count": 1,
            },
            "score": 0.72,
            "prediction_accuracy": 0.75,
        },
    ]

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "Arena State: COMPETITIVE" in report
    assert "semantic_to_transformation_compiler" in report
    assert "transformation_synthesis" in report
    assert "Winner Takes All Detected: FALSE" in report
    assert "Final Report Rendering Time: 0.2 s" in report
    assert "Report Generation Time:" not in report
    assert "Total Wall Time: 10 s" in report
    assert "Active Compute Time: 7.1 s" in report
    assert "Untracked Time: 0.5 s" in report


def test_minimal_report_keeps_top_timing_summary_without_full_stage_table():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="minimal",
    )

    assert "TIMING SUMMARY" in report
    assert "Total Wall Time: 10 s" in report
    assert "Active Compute Time: 7.1 s" in report
    assert "Top Three Exclusive-Time Consumers" in report
    assert "Overlap Detected:" in report
    assert "Report Lifecycle Total Time:" in report
    assert "Final Report Rendering Time: 0.2 s" in report
    assert "Report Timing Status:" in report
    assert "REPORTING TIMING SUMMARY" not in report
    assert "Report Generation Time:" not in report
    assert "COGNITIVE STAGE TIMING" not in report


def test_diagnostic_report_exposes_timing_detail_fields():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="diagnostic",
    )

    assert "DIAGNOSTIC TIMING DETAIL" in report
    assert "inclusive=" in report
    assert "exclusive=" in report
    assert "source=ExecutionTimingState" in report
    assert "Reporting Final Report Rendering Time" in report
    assert "Legacy Reporting Field report_generation_time" in report


def test_final_report_renders_evidence_generation_report():
    state = _report_state()
    state["evidence_generation_report"] = {
        "generation_required": True,
        "generation_trigger": (
            "evidence_acquisition_plan_without_existing_task"
        ),
        "required_evidence": "cross_source_consensus_evidence",
        "required_validation_task": (
            "select_cross_source_tie_break_validation_task"
        ),
        "existing_tasks_found": False,
        "generated_tasks": 1,
        "generated_task_files": [
            "runtime/evidence_generation/generated_curriculum/task.json"
        ],
        "generated_curriculum_path": (
            "runtime/evidence_generation/generated_curriculum"
        ),
        "generated_curriculum_size": 1,
        "generated_domains": ["source_diversity"],
        "generation_strategy": "cross_source_consensus",
        "generation_governance": "POTENTIAL_VALIDATION_OPPORTUNITY_ONLY",
        "training_assistant_queue_updated": True,
        "future_execution_ready": True,
        "generation_status": "GENERATED_VALIDATION_OPPORTUNITY",
        "evidence_produced": False,
        "truth_authority": "NONE",
        "trust_authority": "NONE",
        "graduation_authority": "NONE",
        "constitutional_boundary": (
            "GENERATED_TASKS_ARE_VALIDATION_OPPORTUNITIES_NOT_EVIDENCE"
        ),
    }

    report = DeterministicFinalReportRenderer().render(state)

    assert "EVIDENCE GENERATION REPORT" in report
    assert "Generation Required: TRUE" in report
    assert "Required Evidence: cross_source_consensus_evidence" in report
    assert "Generated Tasks: 1" in report
    assert "Training Assistant Queue Updated: TRUE" in report
    assert "Future Execution Ready: TRUE" in report
    assert "Evidence Produced: FALSE" in report
    assert "Truth Authority: NONE" in report
    assert (
        "Constitutional Boundary: "
        "GENERATED_TASKS_ARE_VALIDATION_OPPORTUNITIES_NOT_EVIDENCE"
    ) in report


def test_warning_section_does_not_count_empty_state_as_warning():
    state = _report_state()
    state["performance_report"]["untracked_runtime_seconds"] = 0
    state["execution_timing"]["execution_timing_state"]["unattributed_time"] = 0
    report = DeterministicFinalReportRenderer().render(state)
    section = report[
        report.index("WARNINGS AND GAPS"):
        report.index("RUNTIME METADATA")
    ]

    assert "Warning Count: 0" in section
    assert "- No validated report warnings." in section
    assert "Warning Count: 1" not in section
