def build_training_report(
    training_batch=None,
    training_assistant_report=None,
    multi_task_results=None,
    ledger_report=None,
    concept_lifecycle_report=None,
):
    training_batch = training_batch or {}
    training_assistant_report = training_assistant_report or {}
    multi_task_results = list(multi_task_results or [])
    ledger_report = ledger_report or {}
    concept_lifecycle_report = concept_lifecycle_report or {}

    def candidate_metric(evaluation, metric_name):
        return next(
            (
                metric
                for metric in evaluation.get("metrics", [])
                if metric.get("metric") == metric_name
            ),
            {},
        )

    lifecycle_by_concept = {
        item.get("concept"): item
        for item in concept_lifecycle_report.get("concepts", [])
        if item.get("concept")
    }

    concept_memory = {}
    for concept in ledger_report.get("concepts", []):
        concept_name = concept.get("concept")
        if not concept_name:
            continue
        ledger_average_contradiction = lifecycle_by_concept.get(
            str(concept_name),
            {},
        ).get("average_contradiction_score", 1.0)
        concept_memory[str(concept_name)] = {
            "used_task_count": concept.get("used_task_count", 0),
            "task_ids": list(concept.get("used_task_ids", [])),
            "independent_success_rate":
            concept.get("independent_success_rate", 0.0),
            "lifecycle_state":
            lifecycle_by_concept.get(
                str(concept_name),
                {},
            ).get("state", "DISCOVERING"),
            "preliminary_truth_candidate_ready":
            lifecycle_by_concept.get(
                str(concept_name),
                {},
            ).get("preliminary_truth_candidate_ready", False),
            "ledger_average_contradiction_score":
            ledger_average_contradiction,
            "average_contradiction_score":
            ledger_average_contradiction,
        }

    task_results = [
        {
            "task": item.get("task"),
            "status": item.get("status"),
            **(
                {"error": item.get("error")}
                if item.get("error")
                else {}
            ),
        }
        for item in multi_task_results
    ]
    candidate_evaluations = {}
    truth_commit_evaluations = {}
    for item in multi_task_results:
        result = item.get("result", {})
        for evaluation in result.get(
            "truth_candidate_report",
            {},
        ).get("evaluations", []):
            concept = evaluation.get("concept")
            if not concept:
                continue
            contradiction_metric = candidate_metric(
                evaluation,
                "contradiction_score",
            )
            candidate_evaluations[str(concept)] = {
                "concept": str(concept),
                "candidate_state": evaluation.get("candidate_state"),
                "eligible_for_truth_candidate":
                evaluation.get("eligible_for_truth_candidate", False),
                "eligibility_reason":
                evaluation.get("eligibility_reason"),
                "blocked_metrics": list(
                    evaluation.get("blocked_metrics", [])
                ),
                "effective_contradiction_score":
                contradiction_metric.get(
                    "current_value",
                    evaluation.get("effective_contradiction_score"),
                ),
                "contradiction_threshold":
                contradiction_metric.get(
                    "threshold",
                    {},
                ).get(
                    "required",
                    evaluation.get("contradiction_threshold"),
                ),
                "contradiction_gap":
                contradiction_metric.get(
                    "gap",
                    evaluation.get("contradiction_gap"),
                ),
                "contradiction_metric_status":
                contradiction_metric.get("status"),
                "contradiction_review_required":
                evaluation.get(
                    "contradiction_review_required",
                    False,
                ),
                "contradiction_review_zone":
                evaluation.get("contradiction_review_zone"),
                "within_soft_review_zone":
                evaluation.get("within_soft_review_zone", False),
                "contradiction_review_severity":
                evaluation.get("contradiction_review_severity"),
                "contradiction_score_source":
                "truth_candidate_effective_runtime_aggregate",
            }
        for evaluation in result.get(
            "epistemic_cognition_report",
            {},
        ).get("evaluations", []):
            concept = evaluation.get("concept")
            if not concept:
                continue
            truth_commit = evaluation.get("truth_commit", {})
            identity_integration = evaluation.get(
                "identity_safe_truth_integration",
                {},
            )
            semantic_spine_recovery = evaluation.get(
                "semantic_spine_recovery",
                {},
            )
            final_commit = truth_commit.get(
                "metadata",
                {},
            ).get(
                "final_commit_decision",
                {},
            )
            truth_commit_evaluations[str(concept)] = {
                "concept": str(concept),
                "decision": truth_commit.get("decision"),
                "reason": truth_commit.get("reason"),
                "failed_gates": list(
                    final_commit.get(
                        "effective_failed_gates",
                        truth_commit.get("reasons", []),
                    )
                ),
                "final_commit_state":
                final_commit.get("final_commit_state"),
                "forbid_automatic_truth_revocation":
                final_commit.get(
                    "forbid_automatic_truth_revocation",
                    False,
                ),
                "revocation_severity":
                final_commit.get("revocation_severity"),
                "revocation_grace_period":
                final_commit.get("revocation_grace_period"),
                "revocation_grace_period_active":
                final_commit.get(
                    "revocation_grace_period_active",
                    False,
                ),
                "low_risk_review_streak":
                final_commit.get("low_risk_review_streak", 0),
                "preventive_review_observation":
                final_commit.get(
                    "preventive_review_observation",
                    False,
                ),
                "identity_governance_state":
                truth_commit.get(
                    "metadata",
                    {},
                ).get("identity_governance_state"),
                "failed_identity_governance_gates": list(
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("failed_identity_governance_gates", [])
                ),
                "identity_integration_state":
                identity_integration.get("integration_state"),
                "identity_failed_checks": list(
                    identity_integration.get("failed_checks", [])
                ),
                "recovery_state":
                semantic_spine_recovery.get("recovery_state"),
                "recovery_streak":
                semantic_spine_recovery.get("recovery_streak", 0),
                "remaining_recovery_cycles":
                semantic_spine_recovery.get(
                    "remaining_recovery_cycles",
                ),
                "rehearsal_validation_pending":
                semantic_spine_recovery.get(
                    "rehearsal_validation_pending",
                    False,
                ),
                "recovery_blocker_type":
                semantic_spine_recovery.get("recovery_blocker_type"),
                "recovery_failed_checks": list(
                    semantic_spine_recovery.get("failed_checks", [])
                ),
            }
    return {
        "system": "training_report",
        "tasks_selected": training_batch.get("selected_task_count", 0),
        "tasks_executed": [
            item["task"]
            for item in task_results
        ],
        "successful_tasks": sum(
            item.get("status") == "completed"
            for item in task_results
        ),
        "failed_tasks": sum(
            item.get("status") == "failed"
            for item in task_results
        ),
        "multi_task_results": task_results,
        "concepts_discovered": {
            concept: stats["used_task_count"]
            for concept, stats in concept_memory.items()
        },
        "concept_memory": concept_memory,
        "concept_lifecycle": concept_lifecycle_report,
        "truth_candidate_evaluations":
        candidate_evaluations,
        "truth_commit_evaluations":
        truth_commit_evaluations,
        "ledger_observed_task_count":
        ledger_report.get("observed_task_count", 0),
        "training_assistant_report": training_assistant_report,
    }


def print_training_report(report):
    print("TRAINING REPORT")
    print()
    print("tasks_selected:", report.get("tasks_selected", 0))
    print("tasks_executed:", report.get("tasks_executed", []))
    print("successful_tasks:", report.get("successful_tasks", 0))
    print("failed_tasks:", report.get("failed_tasks", 0))
    print("multi_task_results:", report.get("multi_task_results", []))
    print("concepts_discovered:", report.get("concepts_discovered", {}))
    print()
    print("CONCEPT DEBUG REPORT")
    print()
    for concept, stats in report.get("concept_memory", {}).items():
        print(
            concept,
            stats.get("used_task_count", 0),
            stats.get("lifecycle_state", "DISCOVERING"),
            "candidate_ready="
            f"{stats.get('preliminary_truth_candidate_ready', False)}",
            "ledger_average_contradiction="
            f"{stats.get('ledger_average_contradiction_score', 1.0)}",
            stats.get("task_ids", []),
        )
    print()
    print("TRUTH CANDIDATE REPORT")
    print()
    for concept, evaluation in report.get(
        "truth_candidate_evaluations",
        {},
    ).items():
        print(
            concept,
            "eligible="
            f"{evaluation.get('eligible_for_truth_candidate', False)}",
            "reason="
            f"{evaluation.get('eligibility_reason')}",
            "blocked="
            f"{evaluation.get('blocked_metrics', [])}",
            "effective_contradiction="
            f"{evaluation.get('effective_contradiction_score')}",
            "contradiction_threshold="
            f"{evaluation.get('contradiction_threshold')}",
            "contradiction_gap="
            f"{evaluation.get('contradiction_gap')}",
            "contradiction_review_required="
            f"{evaluation.get('contradiction_review_required', False)}",
            "contradiction_review_zone="
            f"{evaluation.get('contradiction_review_zone')}",
            "within_soft_review_zone="
            f"{evaluation.get('within_soft_review_zone', False)}",
            "contradiction_review_severity="
            f"{evaluation.get('contradiction_review_severity')}",
        )
    print()
    print("TRUTH COMMIT REPORT")
    print()
    for concept, evaluation in report.get(
        "truth_commit_evaluations",
        {},
    ).items():
        print(
            concept,
            "decision="
            f"{evaluation.get('decision')}",
            "reason="
            f"{evaluation.get('reason')}",
            "final_commit_state="
            f"{evaluation.get('final_commit_state')}",
            "forbid_automatic_truth_revocation="
            f"{evaluation.get('forbid_automatic_truth_revocation', False)}",
            "revocation_severity="
            f"{evaluation.get('revocation_severity')}",
            "revocation_grace_period="
            f"{evaluation.get('revocation_grace_period')}",
            "revocation_grace_period_active="
            f"{evaluation.get('revocation_grace_period_active', False)}",
            "low_risk_review_streak="
            f"{evaluation.get('low_risk_review_streak', 0)}",
            "preventive_review_observation="
            f"{evaluation.get('preventive_review_observation', False)}",
            "identity_governance_state="
            f"{evaluation.get('identity_governance_state')}",
            "failed_identity_governance_gates="
            f"{evaluation.get('failed_identity_governance_gates', [])}",
            "identity_state="
            f"{evaluation.get('identity_integration_state')}",
            "failed_gates="
            f"{evaluation.get('failed_gates', [])}",
            "identity_failed_checks="
            f"{evaluation.get('identity_failed_checks', [])}",
            "recovery_state="
            f"{evaluation.get('recovery_state')}",
            "recovery_streak="
            f"{evaluation.get('recovery_streak', 0)}",
            "remaining_recovery_cycles="
            f"{evaluation.get('remaining_recovery_cycles')}",
            "rehearsal_validation_pending="
            f"{evaluation.get('rehearsal_validation_pending', False)}",
            "recovery_blocker_type="
            f"{evaluation.get('recovery_blocker_type')}",
            "recovery_failed_checks="
            f"{evaluation.get('recovery_failed_checks', [])}",
        )


__all__ = [
    "build_training_report",
    "print_training_report",
]
