from __future__ import annotations

from typing import Any, Mapping


class ExactSuccessDetector:
    def apply(
        self,
        evaluation_result: Mapping[str, Any] | None,
        *,
        governance_valid: bool = True,
        execution_integrity_valid: bool = True,
    ) -> dict[str, Any]:
        evaluation = dict(evaluation_result if isinstance(evaluation_result, Mapping) else {})
        exact = (
            int(evaluation.get("difference_count", evaluation.get("residual_difference_count", 1)) or 0) == 0
            and float(evaluation.get("prediction_accuracy", evaluation.get("accuracy", 0.0)) or 0.0) >= 1.0
            and governance_valid
            and execution_integrity_valid
        )
        if exact:
            evaluation.update({
                "success": True,
                "exact_success": True,
                "partial_success": False,
                "success_state": "EXACT_SUCCESS",
                "failure_detected": False,
                "episode_completed": True,
                "retry_allowed": False,
                "repair_stop_reason": "EXACT_SUCCESS",
            })
        return evaluation


exact_success_detector = ExactSuccessDetector()


__all__ = ["ExactSuccessDetector", "exact_success_detector"]
