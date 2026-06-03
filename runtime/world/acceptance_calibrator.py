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
        }


__all__ = [
    "WorldModelAcceptanceCalibrator",
]
