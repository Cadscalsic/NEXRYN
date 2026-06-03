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
