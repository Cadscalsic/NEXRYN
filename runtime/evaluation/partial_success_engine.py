class PartialSuccessEngine:
    """Classifies useful near-matches without weakening exact success."""

    def __init__(self, minimum_partial_accuracy=0.95):
        self.minimum_partial_accuracy = float(minimum_partial_accuracy)

    def evaluate(self, accuracy, exact_success=False):
        accuracy = max(min(float(accuracy), 1.0), 0.0)
        exact_success = exact_success is True
        partial_success = (
            not exact_success
            and accuracy >= self.minimum_partial_accuracy
        )
        return {
            "success_state": (
                "SUCCESS"
                if exact_success
                else "PARTIAL_SUCCESS"
                if partial_success
                else "FAILURE"
            ),
            "exact_success": exact_success,
            "partial_success": partial_success,
            "minimum_partial_accuracy": self.minimum_partial_accuracy,
        }


__all__ = [
    "PartialSuccessEngine",
]
