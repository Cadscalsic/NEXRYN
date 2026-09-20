# ============================================
# NEXRYN GRADUATED PENALTY ENGINE
# ============================================

from runtime.motivation.motivation_state import clamp


class PenaltyEngine:

    LEVELS = {
        "minor": 1,
        "moderate": 2,
        "major": 3,
        "critical": 4,
    }

    def evaluate(self, runtime_context=None):

        context = runtime_context if isinstance(runtime_context, dict) else {}
        evaluation = self._mapping(context.get("evaluation_result"))
        failure = self._mapping(context.get("failure_analysis"))
        integrity = self._mapping(context.get("execution_integrity_report"))

        exact_success = evaluation.get("exact_success") is True
        success_state = evaluation.get(
            "success_state",
            context.get("success_state"),
        )
        success_with_residuals = (
            success_state == "SUCCESS_WITH_RESIDUALS"
        )
        difference_count = evaluation.get("difference_count", 0)
        failure_cause = (
            context.get("failure_cause")
            or failure.get("failure_cause")
            or failure.get("dominant_failure_cause")
        )
        contradiction = (
            context.get("contradiction_detected") is True
            or bool(context.get("unresolved_contradictions"))
            or bool(context.get("semantic_contradictions"))
        )
        identity_unstable = self._identity_unstable(context)
        integrity_violation = (
            integrity.get("integrity_preserved") is False
            or integrity.get("execution_drift_detected") is True
        )
        truth_corruption = context.get("truth_corruption_detected") is True
        unsafe_self_modification = (
            context.get("unsafe_self_modification") is True
        )
        repeated_failure = (
            context.get("repeated_failure") is True
            or self._number(context.get("failure_repeat_count")) >= 2
        )

        penalties = []

        if exact_success or success_with_residuals:
            pass
        elif truth_corruption or unsafe_self_modification or integrity_violation:
            penalties.append(self._event(
                "critical",
                "critical_safety_violation",
                1.0,
                "immediate_execution_block_rollback_deep_audit",
            ))
        elif contradiction or identity_unstable:
            penalties.append(self._event(
                "major",
                "governance_or_identity_instability",
                0.72,
                "governance_escalation_temporary_quarantine",
            ))
        elif repeated_failure:
            penalties.append(self._event(
                "moderate",
                "repeated_ineffective_strategy",
                0.45,
                "reduce_strategy_priority_require_validation",
            ))
        elif failure_cause == "localized_prediction_mismatch":
            penalties.append(self._event(
                "minor",
                "localized_prediction_mismatch",
                0.16,
                "request_localization_evidence",
            ))
        elif isinstance(difference_count, int) and difference_count > 0:
            penalties.append(self._event(
                "minor",
                "recoverable_prediction_error",
                min(0.12 + difference_count * 0.03, 0.30),
                "slight_confidence_reduction",
            ))

        if not penalties:
            penalties.append(self._event(
                "minor",
                "no_material_penalty",
                0.0,
                "none",
            ))

        distribution = {
            "minor": 0.0,
            "moderate": 0.0,
            "major": 0.0,
            "critical": 0.0,
        }
        for event in penalties:
            distribution[event["severity"]] += event["penalty"]
        distribution = {
            key: round(clamp(value), 4)
            for key, value in distribution.items()
        }
        penalty_score = max(distribution.values())

        return {
            "system": "graduated_penalty_engine",
            "penalty_score": round(clamp(penalty_score), 4),
            "penalty_distribution": distribution,
            "penalties": penalties,
            "highest_severity": max(
                penalties,
                key=lambda item: self.LEVELS[item["severity"]],
            )["severity"],
            "punish_causes_not_outcomes": True,
        }

    def classify_outcome(
        self,
        runtime_context,
        reward_report,
        penalty_report,
    ):

        context = runtime_context if isinstance(runtime_context, dict) else {}
        evaluation = self._mapping(context.get("evaluation_result"))
        accuracy = self._number(
            evaluation.get(
                "accuracy",
                self._mapping(context.get("prediction_report")).get(
                    "prediction_accuracy",
                    0.0,
                ),
            )
        )
        if penalty_report.get("highest_severity") == "critical":
            return "critical_failure"
        if penalty_report.get("highest_severity") == "major":
            return "critical_failure"
        if context.get("repeated_failure") is True:
            return "repeated_failure"
        if evaluation.get("exact_success") is True:
            return "exact_success"
        if evaluation.get("success_state") == "SUCCESS_WITH_RESIDUALS":
            return "success_with_residuals"
        if accuracy >= 0.97 and reward_report.get("reward_score", 0.0) >= 0.80:
            return "high_value_success"
        if evaluation.get("partial_success") is True or accuracy >= 0.80:
            return "partial_success"
        if reward_report.get("reward_distribution", {}).get(
            "discovery_reward",
            0.0,
        ) > 0.0:
            return "knowledge_gain"
        if penalty_report.get("highest_severity") in {"minor", "moderate"}:
            return "recoverable_failure"
        return "recoverable_failure"

    def _event(self, severity, cause, penalty, effect):

        return {
            "severity": severity,
            "cause": cause,
            "penalty": round(clamp(penalty), 4),
            "effect": effect,
        }

    def _identity_unstable(self, context):

        state = str(
            context.get(
                "identity_runtime_state",
                context.get("identity_governance_state", ""),
            )
        ).upper()
        return state in {
            "UNSTABLE",
            "IDENTITY_GOVERNANCE_UNSTABLE",
            "TEMPORARY_RECOVERY_HOLD",
        }

    def _mapping(self, value):

        return value if isinstance(value, dict) else {}

    def _number(self, value, default=0.0):

        try:
            return float(value)
        except (TypeError, ValueError):
            return default
