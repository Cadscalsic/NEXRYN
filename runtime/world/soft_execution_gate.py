class SoftExecutionGate:
    """Evaluates whether partial world-model outputs qualify for sandbox execution."""

    SOFT_EXECUTION_STATE = "SOFT_EXECUTION_ZONE"
    DEFAULT_MINIMUM_SOFT_EXECUTION_ACCURACY = 0.90
    DEFAULT_MAXIMUM_SOFT_EXECUTION_DIFFERENCE_COUNT = 2

    def evaluate(
        self,
        anticipation_report=None,
        minimum_soft_execution_accuracy=None,
        maximum_soft_execution_difference_count=None,
    ):
        anticipation_report = (
            anticipation_report
            if isinstance(anticipation_report, dict)
            else {}
        )
        acceptance_state = str(
            anticipation_report.get("acceptance_state", "")
        ).upper()
        soft_execution_enabled = (
            anticipation_report.get("sandbox_execution_accepted", False)
            is True
        )
        residual_difference_count = anticipation_report.get(
            "residual_difference_count"
        )
        prediction_report = anticipation_report.get(
            "prediction_report",
            {}
        )
        prediction_accuracy = prediction_report.get("prediction_accuracy")
        partial_success = (
            prediction_report.get("partial_success") is True
            or str(
                prediction_report.get("success_state", "")
            ).upper() == "PARTIAL_SUCCESS"
        )
        minimum_accuracy = (
            self.DEFAULT_MINIMUM_SOFT_EXECUTION_ACCURACY
            if minimum_soft_execution_accuracy is None
            else float(minimum_soft_execution_accuracy)
        )
        maximum_difference_count = (
            self.DEFAULT_MAXIMUM_SOFT_EXECUTION_DIFFERENCE_COUNT
            if maximum_soft_execution_difference_count is None
            else int(maximum_soft_execution_difference_count)
        )
        fallback_soft_execution = (
            soft_execution_enabled
            or (
                partial_success is True
                and isinstance(prediction_accuracy, (int, float))
                and prediction_accuracy >= minimum_accuracy
                and isinstance(residual_difference_count, int)
                and residual_difference_count <= maximum_difference_count
            )
        )
        soft_execution_authorized = (
            fallback_soft_execution
            and acceptance_state == self.SOFT_EXECUTION_STATE
        )
        override_authorized = (
            not anticipation_report.get("sandbox_execution_accepted", False)
            and fallback_soft_execution
            and acceptance_state != self.SOFT_EXECUTION_STATE
        )
        if override_authorized:
            soft_execution_authorized = True

        return {
            "system": "soft_execution_gate",
            "soft_execution_authorized": soft_execution_authorized,
            "soft_execution_enabled": fallback_soft_execution,
            "acceptance_state": acceptance_state,
            "soft_execution_state": self.SOFT_EXECUTION_STATE,
            "minimum_soft_execution_accuracy": minimum_accuracy,
            "maximum_soft_execution_difference_count": maximum_difference_count,
            "residual_difference_count": residual_difference_count,
            "prediction_accuracy": prediction_accuracy,
            "partial_success": partial_success,
            "soft_execution_override_applied": override_authorized,
        }


soft_execution_gate = SoftExecutionGate()


__all__ = [
    "SoftExecutionGate",
    "soft_execution_gate",
]
