from runtime.capability_intelligence.capability_graduation_infrastructure import (
    CapabilityGraduationInfrastructure,
)


def test_graduation_infrastructure_diagnoses_final_validation_gap():
    report = CapabilityGraduationInfrastructure().analyze(
        [
            {
                "capability_id": (
                    "operational_capability:spatial:translate:directional_motion"
                ),
                "operation": "translate",
                "domain": "Spatial",
                "lifecycle_state": "SURVIVING_CAPABILITY",
                "distinct_task_count": 33,
                "arena_quality_count": 35,
                "arena_simulated_count": 35,
                "best_accuracy": 0.9444,
                "average_accuracy": 0.8125,
                "validation_failures": 31,
                "improvement_trend": "IMPROVING",
                "next_required_evidence": (
                    "exact_or_governed_validation_success"
                ),
            }
        ],
        promotion_policy={
            "sandbox_citizenship_thresholds": {
                "min_distinct_tasks": 3,
                "min_arena_quality_count": 3,
                "min_average_accuracy": 0.8,
                "min_best_accuracy": 0.0,
                "allowed_trends": [
                    "STABLE",
                    "IMPROVING",
                    "STABLE_HIGH_PERFORMANCE",
                ],
            },
        },
    )

    diagnostic = report["capability_graduation_diagnostics"][0]

    assert diagnostic["operation"] == "translate"
    assert diagnostic["graduation_status"] == "BLOCKED_AT_FINAL_VALIDATION"
    assert diagnostic["graduation_gap_type"] == "Validator Gap"
    assert diagnostic["validator_gap"] == "GOVERNED_VALIDATION_INCOMPLETE"
    assert diagnostic["validation_failure_reason"] == (
        "Governed Validation incomplete"
    )
    assert diagnostic["priority_missing_evidence"] == (
        "exact_or_governed_validation_success"
    )
    assert diagnostic["can_graduate_in_single_run"] is True
    assert report["capability_promotion_phase_state"] == (
        "CAPABILITY_PROMOTION_PHASE_DETECTED"
    )
    assert report["capability_promotion_candidate_count"] == 1
    assert report["capability_promotion_interpretation"] == (
        "promotion_interprets_evidence_before_trust_or_graduation"
    )
    assert report["evidence_acceptance_state"] == (
        "GOVERNED_EVIDENCE_ACCEPTANCE_BOTTLENECK"
    )
    assert report["evidence_acceptance_bottleneck"] == (
        "governed_validation_evidence_acceptance"
    )
    assert report["evidence_acceptance_failure_count"] == 1
    assert report["evidence_acceptance_failure_share"] == 1.0
    assert report["capability_promotion_rows"][0]["promotion_interpretation"] == (
        "high_quality_evidence_requires_acceptance_before_trust"
    )
    assert report["capability_promotion_rows"][0]["trusted_for_decision"] is False
    assert report["graduation_sprint_recommendations"][0][
        "recommended_validation_type"
    ] == "exact_or_governed_validation"
    assert report["graduation_queue_health"] == "HEALTHY"
