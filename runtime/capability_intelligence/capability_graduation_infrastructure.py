"""Capability graduation diagnostics for the operationalization phase.

This module measures graduation readiness and blockage causes. It does not
change governance, trust, decision authority, arena behavior, or promotion
thresholds.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping


GRADUATION_STAGES = (
    "INCUBATING_VALIDATION_GAP",
    "SURVIVING_CAPABILITY",
    "COGNITIVE_CITIZEN",
    "OPERATIONAL_CITIZEN",
)


class CapabilityGraduationInfrastructure:
    """Analyze capability graduation evidence and pipeline pressure."""

    def analyze(
        self,
        records: list[Mapping[str, Any]] | None,
        *,
        promotion_policy: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        rows = [dict(row) for row in records or [] if isinstance(row, Mapping)]
        policy = promotion_policy if isinstance(promotion_policy, Mapping) else {}
        thresholds = policy.get("sandbox_citizenship_thresholds")
        thresholds = thresholds if isinstance(thresholds, Mapping) else {}
        diagnostics = [self._capability_diagnostic(row, thresholds) for row in rows]
        candidates = [
            row for row in diagnostics
            if row["graduation_status"] in {
                "READY_FOR_GRADUATION_REVIEW",
                "BLOCKED_AT_FINAL_VALIDATION",
                "NEEDS_TARGETED_EVIDENCE",
            }
        ]
        backlog = [
            row for row in diagnostics
            if row["lifecycle_state"] in {
                "INCUBATING_VALIDATION_GAP",
                "SURVIVING_CAPABILITY",
            }
        ]
        operational = [
            row for row in diagnostics
            if row["lifecycle_state"] == "OPERATIONAL_CITIZEN"
        ]
        pipeline = self._pipeline(rows, diagnostics)
        promotion = self._promotion_interpretation(diagnostics)
        evidence_coverage = self._average(
            row["graduation_evidence_completeness"]
            for row in diagnostics
            if row["lifecycle_state"] in GRADUATION_STAGES
        )
        success_rate = self._ratio(len(operational), len(candidates) + len(operational))
        failure_rate = self._ratio(len(backlog), len(candidates) + len(operational) + len(backlog))
        queue_health = (
            "HEALTHY"
            if candidates and evidence_coverage >= 0.75
            else "BACKLOGGED"
            if backlog
            else "EMPTY"
        )
        pressure = self._ratio(
            len(candidates),
            max(len(operational), 1),
        )
        top = sorted(
            candidates,
            key=lambda row: (
                -row["capability_graduation_confidence"],
                -row["graduation_evidence_completeness"],
                -int(row.get("arena_quality_count") or 0),
                str(row.get("operation") or ""),
            ),
        )[:5]
        health = round(
            (
                evidence_coverage
                + success_rate
                + (1.0 - failure_rate)
                + (1.0 if top else 0.0)
            )
            / 4,
            4,
        )
        return {
            "system": "capability_graduation_infrastructure",
            "capability_graduation_health": health,
            "graduation_pipeline_health": pipeline["graduation_pipeline_health"],
            "graduation_success_rate": success_rate,
            "graduation_failure_rate": failure_rate,
            "graduation_queue_health": queue_health,
            "graduation_evidence_coverage": evidence_coverage,
            "graduation_infrastructure_readiness": (
                "READY"
                if health >= 0.80 and top
                else "PARTIAL"
                if health >= 0.50
                else "BLOCKED"
            ),
            "average_capability_graduation_time": self._average(
                row["average_graduation_time"]
                for row in diagnostics
                if row["average_graduation_time"] is not None
            ),
            "graduation_backlog_size": len(backlog),
            "capability_graduation_pressure": pressure,
            "capability_graduation_queue_health": queue_health,
            "capability_graduation_risk": (
                "HIGH"
                if any(row["capability_graduation_risk"] == "HIGH" for row in top)
                else "MEDIUM"
                if backlog
                else "LOW"
            ),
            "capability_graduation_complexity": (
                "HIGH"
                if any(row["capability_graduation_complexity"] == "HIGH" for row in top)
                else "MEDIUM"
                if top
                else "LOW"
            ),
            "capability_graduation_confidence": self._average(
                row["capability_graduation_confidence"] for row in top
            ),
            "graduation_pipeline_stages": pipeline["graduation_pipeline_stages"],
            "graduation_transition_rows": pipeline["graduation_transition_rows"],
            "capability_promotion_phase_state": promotion[
                "capability_promotion_phase_state"
            ],
            "capability_promotion_candidate_count": promotion[
                "capability_promotion_candidate_count"
            ],
            "capability_promotion_interpretation": promotion[
                "capability_promotion_interpretation"
            ],
            "evidence_acceptance_state": promotion["evidence_acceptance_state"],
            "evidence_acceptance_bottleneck": promotion[
                "evidence_acceptance_bottleneck"
            ],
            "evidence_acceptance_failure_count": promotion[
                "evidence_acceptance_failure_count"
            ],
            "evidence_acceptance_failure_share": promotion[
                "evidence_acceptance_failure_share"
            ],
            "capability_promotion_rows": promotion["capability_promotion_rows"],
            "capability_graduation_diagnostics": diagnostics,
            "top_graduation_priority": top[0] if top else {},
            "graduation_sprint_recommendations": [
                self._sprint_recommendation(row) for row in top
            ],
            "validator_failure_distribution": dict(
                sorted(Counter(row["validator_gap"] for row in diagnostics).items())
            ),
        }

    def _capability_diagnostic(
        self,
        row: Mapping[str, Any],
        thresholds: Mapping[str, Any],
    ) -> dict[str, Any]:
        state = str(row.get("lifecycle_state") or "UNKNOWN")
        distinct_tasks = self._int(row.get("distinct_task_count"))
        arena_quality = self._int(row.get("arena_quality_count"))
        arena_simulated = self._int(row.get("arena_simulated_count"))
        materialized = self._int(row.get("materialized_count"))
        validation_failures = self._int(row.get("validation_failures"))
        best_accuracy = self._float(row.get("best_accuracy"))
        average_accuracy = self._float(row.get("average_accuracy"))
        trend = str(row.get("improvement_trend") or "UNKNOWN")
        next_evidence = str(row.get("next_required_evidence") or "")
        min_tasks = self._int(thresholds.get("min_distinct_tasks"), 3)
        min_quality = self._int(thresholds.get("min_arena_quality_count"), 3)
        min_average = self._float(thresholds.get("min_average_accuracy"), 0.80)
        min_best = self._float(thresholds.get("min_best_accuracy"), 0.0)
        allowed_trends = set(
            thresholds.get("allowed_trends")
            or ("STABLE", "IMPROVING", "STABLE_HIGH_PERFORMANCE")
        )
        evidence = {
            "exact_validation_evidence": materialized >= 1,
            "governed_validation_evidence": state == "OPERATIONAL_CITIZEN"
            or bool(row.get("citizenship_basis")),
            "independent_task_evidence": distinct_tasks >= min_tasks,
            "operational_stability_evidence": trend in allowed_trends,
            "arena_evidence": arena_quality >= min_quality,
            "cross_domain_evidence": bool(row.get("domain")),
            "cross_source_evidence": bool(row.get("source_count", 0) or row.get("cross_source_count", 0)),
            "historical_evidence": distinct_tasks >= 5 or arena_simulated >= 5,
            "reuse_evidence": self._int(row.get("independent_reuse_success_count")) > 0
            or self._int(row.get("reuse_evidence_count")) > 0,
        }
        required = {
            "exact_or_governed_validation_success": (
                evidence["exact_validation_evidence"]
                or evidence["governed_validation_evidence"]
            ),
            "independent_task_evidence": evidence["independent_task_evidence"],
            "operational_stability_evidence": evidence["operational_stability_evidence"],
            "arena_evidence": evidence["arena_evidence"],
            "accuracy_evidence": (
                best_accuracy >= min_best and average_accuracy >= min_average
            ),
        }
        missing = [key for key, ok in required.items() if not ok]
        evidence_missing = [
            key for key, ok in evidence.items() if not ok
        ]
        validator_gap = self._validator_gap(
            missing=missing,
            next_evidence=next_evidence,
            validation_failures=validation_failures,
            best_accuracy=best_accuracy,
            average_accuracy=average_accuracy,
            min_best=min_best,
            min_average=min_average,
            trend=trend,
            allowed_trends=allowed_trends,
        )
        completeness = self._ratio(
            len([ok for ok in required.values() if ok]),
            len(required),
        )
        confidence = round(
            (
                self._ratio(distinct_tasks, 15)
                + self._ratio(arena_quality, 15)
                + self._ratio(best_accuracy, 0.90)
                + self._ratio(average_accuracy, 0.80)
                + completeness
            )
            / 5,
            4,
        )
        if state == "OPERATIONAL_CITIZEN":
            status = "GRADUATED_SANDBOX_ONLY"
        elif not missing and state in {"SURVIVING_CAPABILITY", "COGNITIVE_CITIZEN"}:
            status = "READY_FOR_GRADUATION_REVIEW"
        elif missing == ["exact_or_governed_validation_success"] and confidence >= 0.80:
            status = "BLOCKED_AT_FINAL_VALIDATION"
        elif confidence >= 0.65:
            status = "NEEDS_TARGETED_EVIDENCE"
        else:
            status = "NOT_MATURE"
        return {
            **dict(row),
            "graduation_status": status,
            "graduation_ready": status == "READY_FOR_GRADUATION_REVIEW",
            "graduation_blocker": missing[0] if missing else "none",
            "graduation_gap_type": self._gap_type(missing, validator_gap, row),
            "graduation_evidence_present": {
                key: ok for key, ok in sorted(evidence.items()) if ok
            },
            "graduation_evidence_missing": evidence_missing,
            "missing_graduation_evidence": missing,
            "priority_missing_evidence": missing[0] if missing else "none",
            "minimum_evidence_required": len(required),
            "graduation_evidence_completeness": completeness,
            "validator_gap": validator_gap,
            "validation_failure_reason": self._validation_failure_reason(
                validator_gap,
            ),
            "average_graduation_time": distinct_tasks if state != "OPERATIONAL_CITIZEN" else None,
            "capability_graduation_risk": (
                "HIGH"
                if validator_gap in {
                    "EXACT_MATCH_THRESHOLD_NOT_SATISFIED",
                    "OPERATIONAL_STABILITY_INSUFFICIENT",
                }
                else "MEDIUM"
                if missing
                else "LOW"
            ),
            "capability_graduation_complexity": (
                "HIGH"
                if len(missing) >= 3
                else "MEDIUM"
                if len(missing) >= 1
                else "LOW"
            ),
            "capability_graduation_confidence": confidence,
            "can_graduate_in_single_run": missing
            in ([], ["exact_or_governed_validation_success"]),
            "required_validation_type": (
                "exact_or_governed_validation"
                if "exact_or_governed_validation_success" in missing
                else "independent_task_validation"
                if "independent_task_evidence" in missing
                else "stability_validation"
                if "operational_stability_evidence" in missing
                else "none"
            ),
            "recommended_training_signal": self._training_signal(row, missing),
        }

    def _promotion_interpretation(
        self,
        diagnostics: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        promotion_rows = [
            row for row in diagnostics
            if row.get("lifecycle_state") in {
                "SURVIVING_CAPABILITY",
                "COGNITIVE_CITIZEN",
            }
            and row.get("capability_graduation_confidence", 0.0) >= 0.65
        ]
        validator_counts = Counter(
            row.get("validator_gap") for row in diagnostics
            if row.get("validator_gap") and row.get("validator_gap") != "NONE"
        )
        total_failures = sum(validator_counts.values())
        governed_failures = validator_counts.get(
            "GOVERNED_VALIDATION_INCOMPLETE",
            0,
        )
        governed_share = self._ratio(governed_failures, total_failures)
        acceptance_state = (
            "GOVERNED_EVIDENCE_ACCEPTANCE_BOTTLENECK"
            if governed_share >= 0.50 and governed_failures
            else "EVIDENCE_ACCEPTANCE_PENDING"
            if total_failures
            else "EVIDENCE_ACCEPTANCE_CLEAR"
        )
        return {
            "capability_promotion_phase_state": (
                "CAPABILITY_PROMOTION_PHASE_DETECTED"
                if promotion_rows
                else "NO_PROMOTION_PHASE_PRESSURE"
            ),
            "capability_promotion_candidate_count": len(promotion_rows),
            "capability_promotion_interpretation": (
                "promotion_interprets_evidence_before_trust_or_graduation"
            ),
            "evidence_acceptance_state": acceptance_state,
            "evidence_acceptance_bottleneck": (
                "governed_validation_evidence_acceptance"
                if acceptance_state == "GOVERNED_EVIDENCE_ACCEPTANCE_BOTTLENECK"
                else "none"
                if acceptance_state == "EVIDENCE_ACCEPTANCE_CLEAR"
                else "validation_evidence_acceptance"
            ),
            "evidence_acceptance_failure_count": governed_failures,
            "evidence_acceptance_failure_share": governed_share,
            "capability_promotion_rows": [
                {
                    "capability_id": row.get("capability_id"),
                    "operation": row.get("operation"),
                    "domain": row.get("domain"),
                    "lifecycle_state": row.get("lifecycle_state"),
                    "graduation_status": row.get("graduation_status"),
                    "validator_gap": row.get("validator_gap"),
                    "missing_graduation_evidence": row.get(
                        "missing_graduation_evidence"
                    ),
                    "capability_graduation_confidence": row.get(
                        "capability_graduation_confidence"
                    ),
                    "promotion_interpretation": (
                        "high_quality_evidence_requires_acceptance_before_trust"
                        if row.get("validator_gap")
                        == "GOVERNED_VALIDATION_INCOMPLETE"
                        else "promotion_review_candidate"
                    ),
                    "trusted_for_decision": bool(row.get("trusted_for_decision")),
                }
                for row in sorted(
                    promotion_rows,
                    key=lambda item: (
                        -float(item.get("capability_graduation_confidence") or 0.0),
                        str(item.get("operation") or ""),
                    ),
                )[:5]
            ],
        }

    def _pipeline(
        self,
        rows: list[Mapping[str, Any]],
        diagnostics: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        state_counts = Counter(str(row.get("lifecycle_state") or "UNKNOWN") for row in rows)
        diagnostic_by_id = {
            str(row.get("capability_id") or row.get("operation") or index): row
            for index, row in enumerate(diagnostics)
        }
        transition_rows = []
        pairs = [
            ("INCUBATING_VALIDATION_GAP", "SURVIVING_CAPABILITY"),
            ("SURVIVING_CAPABILITY", "COGNITIVE_CITIZEN"),
            ("COGNITIVE_CITIZEN", "OPERATIONAL_CITIZEN"),
        ]
        for source, target in pairs:
            source_rows = [
                row for row in diagnostics if row.get("lifecycle_state") == source
            ]
            stuck = [
                row for row in source_rows
                if row.get("graduation_status") != "READY_FOR_GRADUATION_REVIEW"
            ]
            transition_rows.append({
                "transition": f"{source}->{target}",
                "source_count": len(source_rows),
                "target_count": state_counts.get(target, 0),
                "stuck_count": len(stuck),
                "stuck_reasons": dict(Counter(row.get("graduation_blocker") for row in stuck)),
                "average_graduation_time": self._average(
                    row.get("average_graduation_time") for row in source_rows
                    if row.get("average_graduation_time") is not None
                ),
                "success_rate": self._ratio(state_counts.get(target, 0), len(source_rows) + state_counts.get(target, 0)),
            })
        return {
            "graduation_pipeline_health": (
                "HEALTHY"
                if not any(row["stuck_count"] for row in transition_rows)
                else "BACKLOGGED"
            ),
            "graduation_pipeline_stages": {
                stage: state_counts.get(stage, 0) for stage in GRADUATION_STAGES
            },
            "graduation_transition_rows": transition_rows,
            "diagnostic_by_id": diagnostic_by_id,
        }

    def _validator_gap(
        self,
        *,
        missing: list[str],
        next_evidence: str,
        validation_failures: int,
        best_accuracy: float,
        average_accuracy: float,
        min_best: float,
        min_average: float,
        trend: str,
        allowed_trends: set[str],
    ) -> str:
        if "exact_or_governed_validation_success" in missing:
            return "GOVERNED_VALIDATION_INCOMPLETE"
        if best_accuracy < min_best:
            return "EXACT_MATCH_THRESHOLD_NOT_SATISFIED"
        if average_accuracy < min_average:
            return "ACCURACY_STABILITY_INSUFFICIENT"
        if trend not in allowed_trends:
            return "OPERATIONAL_STABILITY_INSUFFICIENT"
        if "independent_task_evidence" in missing:
            return "MISSING_INDEPENDENT_EVIDENCE"
        if "arena_evidence" in missing:
            return "MISSING_ARENA_EVIDENCE"
        if validation_failures > 0 or next_evidence:
            return "VALIDATOR_ACCEPTANCE_PENDING"
        return "NONE"

    def _gap_type(
        self,
        missing: list[str],
        validator_gap: str,
        row: Mapping[str, Any],
    ) -> str:
        if validator_gap != "NONE":
            return "Validator Gap"
        if "independent_task_evidence" in missing:
            return "Evidence Gap"
        if "arena_evidence" in missing:
            return "Validation Gap"
        if not row.get("domain"):
            return "Domain Gap"
        return "none" if not missing else "Graduation Gap"

    def _validation_failure_reason(self, validator_gap: str) -> str:
        return {
            "MISSING_INDEPENDENT_EVIDENCE": "Missing Independent Evidence",
            "EXACT_MATCH_THRESHOLD_NOT_SATISFIED": "Exact Match Threshold not satisfied",
            "ACCURACY_STABILITY_INSUFFICIENT": "Operational Stability insufficient",
            "OPERATIONAL_STABILITY_INSUFFICIENT": "Operational Stability insufficient",
            "GOVERNED_VALIDATION_INCOMPLETE": "Governed Validation incomplete",
            "MISSING_ARENA_EVIDENCE": "Arena Evidence incomplete",
            "VALIDATOR_ACCEPTANCE_PENDING": "Validator acceptance pending",
        }.get(validator_gap, "none")

    def _sprint_recommendation(self, row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "capability_id": row.get("capability_id"),
            "operation": row.get("operation"),
            "priority": row.get("capability_graduation_confidence"),
            "minimum_required_evidence": row.get("priority_missing_evidence"),
            "recommended_validation_type": row.get("required_validation_type"),
            "recommended_training_signal": row.get("recommended_training_signal"),
            "can_graduate_in_single_run": row.get("can_graduate_in_single_run"),
            "estimated_runs_required": 1
            if row.get("can_graduate_in_single_run")
            else max(2, len(row.get("missing_graduation_evidence") or [])),
        }

    def _training_signal(self, row: Mapping[str, Any], missing: list[str]) -> str:
        operation = str(row.get("operation") or "capability")
        if "exact_or_governed_validation_success" in missing:
            return f"validator_acceptance_task_for:{operation}"
        if "independent_task_evidence" in missing:
            return f"independent_task_reappearance_for:{operation}"
        if "operational_stability_evidence" in missing:
            return f"stability_recovery_task_for:{operation}"
        return f"graduation_confirmation_task_for:{operation}"

    def _int(self, value: Any, default: int = 0) -> int:
        try:
            return int(value if value is not None else default)
        except (TypeError, ValueError):
            return default

    def _float(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default

    def _ratio(self, numerator: float, denominator: float) -> float:
        if not denominator:
            return 0.0
        return round(max(0.0, min(1.0, float(numerator) / float(denominator))), 4)

    def _average(self, values: Any) -> float | None:
        rows = [
            float(value)
            for value in values
            if isinstance(value, (int, float))
        ]
        if not rows:
            return None
        return round(sum(rows) / len(rows), 4)


capability_graduation_infrastructure = CapabilityGraduationInfrastructure()


__all__ = [
    "CapabilityGraduationInfrastructure",
    "capability_graduation_infrastructure",
]
