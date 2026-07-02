class PartialSuccessEngine:
    """Classifies useful near-matches without weakening exact success."""

    def __init__(
        self,
        minimum_partial_accuracy=0.95,
        high_value_partial_accuracy=0.90,
        high_value_max_residual_cells=2,
    ):
        self.minimum_partial_accuracy = float(minimum_partial_accuracy)
        self.high_value_partial_accuracy = float(high_value_partial_accuracy)
        self.high_value_max_residual_cells = int(high_value_max_residual_cells)

    def evaluate(
        self,
        accuracy,
        exact_success=False,
        difference_count=None,
        final_score=None,
    ):
        accuracy = max(min(float(accuracy), 1.0), 0.0)
        final_score = accuracy if final_score is None else max(
            min(float(final_score), 1.0),
            0.0,
        )
        exact_success = exact_success is True
        partial_success = (
            not exact_success
            and accuracy >= self.minimum_partial_accuracy
        )
        try:
            residual_cells = int(difference_count)
        except (TypeError, ValueError):
            residual_cells = None
        high_value_partial_success = (
            not exact_success
            and not partial_success
            and accuracy >= self.high_value_partial_accuracy
            and (
                residual_cells is None
                or residual_cells <= self.high_value_max_residual_cells
            )
        )
        return {
            "success_state": (
                "SUCCESS"
                if exact_success
                else "PARTIAL_SUCCESS"
                if partial_success
                else "HIGH_VALUE_PARTIAL_SUCCESS"
                if high_value_partial_success
                else "FAILURE"
            ),
            "exact_success": exact_success,
            "partial_success": partial_success or high_value_partial_success,
            "high_value_partial_success": high_value_partial_success,
            "minimum_partial_accuracy": self.minimum_partial_accuracy,
            "high_value_partial_accuracy": self.high_value_partial_accuracy,
            "high_value_max_residual_cells":
            self.high_value_max_residual_cells,
        }


__all__ = [
    "PartialSuccessEngine",
]
