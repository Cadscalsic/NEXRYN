class WorldModelAcceptanceCalibrator:
    """Separates exploratory simulation value from execution acceptance."""

    def __init__(
        self,
        minimum_search_accuracy=0.75,
        minimum_execution_accuracy=0.95,
        minimum_soft_execution_accuracy=0.90,
        maximum_soft_execution_difference_count=1,
        maximum_uncertainty=0.45,
    ):
        self.minimum_search_accuracy = minimum_search_accuracy
        self.minimum_execution_accuracy = minimum_execution_accuracy
        self.minimum_soft_execution_accuracy = minimum_soft_execution_accuracy
        self.maximum_soft_execution_difference_count = (
            maximum_soft_execution_difference_count
        )
        self.maximum_uncertainty = maximum_uncertainty

    def evaluate(
        self,
        prediction_report,
        uncertainty_report,
        minimum_search_accuracy=None,
    ):
        accuracy = prediction_report.get("prediction_accuracy", 0.0)
        uncertainty = uncertainty_report.get("simulation_uncertainty", 1.0)
        prediction_success = prediction_report.get("success", False) is True
        partial_success = (
            prediction_report.get("partial_success", False) is True
            or str(
                prediction_report.get("success_state", "")
            ).upper() == "PARTIAL_SUCCESS"
        )
        correct_cells = prediction_report.get("correct_cells")
        total_cells = prediction_report.get("total_cells")
        difference_count = (
            total_cells - correct_cells
            if isinstance(correct_cells, int)
            and isinstance(total_cells, int)
            and total_cells >= correct_cells
            else None
        )
        uncertainty_acceptable = uncertainty <= self.maximum_uncertainty
        effective_minimum_search_accuracy = (
            self.minimum_search_accuracy
            if minimum_search_accuracy is None
            else minimum_search_accuracy
        )
        search_candidate_accepted = (
            accuracy >= effective_minimum_search_accuracy
            and uncertainty_acceptable
        )
        execution_accepted = (
            accuracy >= self.minimum_execution_accuracy
            and prediction_success
            and uncertainty_acceptable
        )
        sandbox_execution_accepted = (
            not execution_accepted
            and partial_success
            and accuracy >= self.minimum_soft_execution_accuracy
            and difference_count is not None
            and difference_count <= self.maximum_soft_execution_difference_count
            and uncertainty_acceptable
        )
        calibration = self._calibrate_readiness(
            prediction_report=prediction_report,
            uncertainty_report=uncertainty_report,
            accuracy=accuracy,
            uncertainty=uncertainty,
            difference_count=difference_count,
            execution_accepted=execution_accepted,
            sandbox_execution_accepted=sandbox_execution_accepted,
            search_candidate_accepted=search_candidate_accepted,
        )
        return {
            "accepted": execution_accepted,
            "search_candidate_accepted": search_candidate_accepted,
            "execution_accepted": execution_accepted,
            "sandbox_execution_accepted": sandbox_execution_accepted,
            "acceptance_state": (
                "EXECUTION_ACCEPTED"
                if execution_accepted
                else "SOFT_EXECUTION_ZONE"
                if sandbox_execution_accepted
                else "SEARCH_CANDIDATE_ONLY"
                if search_candidate_accepted
                else "SIMULATION_REJECTED"
            ),
            "minimum_search_accuracy": self.minimum_search_accuracy,
            "effective_minimum_search_accuracy":
            effective_minimum_search_accuracy,
            "minimum_execution_accuracy": self.minimum_execution_accuracy,
            "minimum_soft_execution_accuracy":
            self.minimum_soft_execution_accuracy,
            "maximum_soft_execution_difference_count":
            self.maximum_soft_execution_difference_count,
            "residual_difference_count": difference_count,
            "maximum_uncertainty": self.maximum_uncertainty,
            "prediction_success_required_for_execution": True,
            "soft_execution_is_sandbox_only": True,
            "world_model_calibration": calibration,
        }

    def _calibrate_readiness(
        self,
        prediction_report,
        uncertainty_report,
        accuracy,
        uncertainty,
        difference_count,
        execution_accepted,
        sandbox_execution_accepted,
        search_candidate_accepted,
    ):
        dependency_coherence = self._read_metric(
            prediction_report,
            uncertainty_report,
            "dependency_coherence",
            default=0.50,
        )
        context_consistency = self._read_metric(
            prediction_report,
            uncertainty_report,
            "context_consistency",
            default=0.50,
        )
        identity_compatibility = self._read_metric(
            prediction_report,
            uncertainty_report,
            "identity_compatibility",
            default=self._read_metric(
                prediction_report,
                uncertainty_report,
                "identity_continuity",
                default=0.50,
            ),
        )
        cross_task_stability = self._read_metric(
            prediction_report,
            uncertainty_report,
            "cross_task_stability",
            default=0.50,
        )
        causal_support = self._read_metric(
            prediction_report,
            uncertainty_report,
            "causal_support",
            default=dependency_coherence,
        )
        support_average = self._clamp(
            (
                dependency_coherence
                + context_consistency
                + identity_compatibility
                + cross_task_stability
                + causal_support
            )
            / 5.0
        )
        uncertainty_resistance = self._clamp(1.0 - uncertainty)
        residual_penalty = (
            0.0
            if difference_count in (None, 0)
            else min(float(difference_count) * 0.025, 0.20)
        )
        calibrated_readiness = self._clamp(
            accuracy * 0.58
            + support_average * 0.27
            + uncertainty_resistance * 0.15
            - residual_penalty
        )
        calibration_state = (
            "EXECUTION_CALIBRATED_READY"
            if execution_accepted
            else "SANDBOX_CALIBRATED_READY"
            if sandbox_execution_accepted
            else "CALIBRATION_BRIDGE"
            if (
                search_candidate_accepted
                and calibrated_readiness >= 0.86
                and dependency_coherence < 0.80
            )
            else "SEARCH_CALIBRATED_ONLY"
            if search_candidate_accepted
            else "CALIBRATION_REJECTED"
        )
        return {
            "system": "world_model_acceptance_calibrator",
            "calibrated_readiness": round(calibrated_readiness, 4),
            "calibration_state": calibration_state,
            "support_average": round(support_average, 4),
            "dependency_coherence": round(dependency_coherence, 4),
            "context_consistency": round(context_consistency, 4),
            "identity_compatibility": round(identity_compatibility, 4),
            "cross_task_stability": round(cross_task_stability, 4),
            "causal_support": round(causal_support, 4),
            "uncertainty_resistance": round(uncertainty_resistance, 4),
            "residual_penalty": round(residual_penalty, 4),
            "execution_threshold_preserved": self.minimum_execution_accuracy,
            "recommended_next_step": (
                "strengthen_dependency_coherence"
                if calibration_state == "CALIBRATION_BRIDGE"
                else "sandbox_verify"
                if calibration_state == "SANDBOX_CALIBRATED_READY"
                else "execute"
                if calibration_state == "EXECUTION_CALIBRATED_READY"
                else "collect_world_model_evidence"
            ),
        }

    def _read_metric(
        self,
        prediction_report,
        uncertainty_report,
        key,
        default=0.0,
    ):
        value = prediction_report.get(key, uncertainty_report.get(key, default))
        try:
            return self._clamp(float(value))
        except Exception:
            return self._clamp(default)

    def _clamp(self, value, minimum=0.0, maximum=1.0):
        return max(minimum, min(float(value), maximum))


__all__ = [
    "WorldModelAcceptanceCalibrator",
]
