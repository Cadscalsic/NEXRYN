from __future__ import annotations

from typing import Any, Mapping


class RepairStopPolicy:
    def decide(
        self,
        *,
        exact_success: bool,
        remaining_budget: int,
        actionable_residual: bool,
        convergence: Mapping[str, Any] | None,
        duplicate_state: str = "NOVEL_REPAIR",
        candidate_count: int = 0,
    ) -> dict[str, Any]:
        data = convergence if isinstance(convergence, Mapping) else {}
        state = data.get("convergence_state")
        reason = None
        if exact_success:
            reason = "EXACT_SUCCESS"
        elif remaining_budget <= 0:
            reason = "REPAIR_BUDGET_EXHAUSTED"
        elif duplicate_state in {"DUPLICATE_REPAIR", "EQUIVALENT_REPAIR", "REPEATED_NONPRODUCTIVE_REPAIR", "REPAIR_CYCLE_DETECTED"}:
            reason = "DUPLICATE_REPAIR_CYCLE"
        elif data.get("oscillation_detected") is True or state == "OSCILLATION":
            reason = "OSCILLATION_DETECTED"
        elif data.get("regression_detected") is True or state == "REGRESSION":
            reason = "REGRESSION_DETECTED"
        elif state == "STAGNATION":
            reason = "STAGNATION_DETECTED"
        elif not actionable_residual:
            reason = "RESIDUAL_NOT_ACTIONABLE"
        elif candidate_count <= 0:
            reason = "NO_VALID_REPAIR_CANDIDATE"
        return {
            "repair_should_stop": reason is not None,
            "repair_stop_reason": reason,
        }


repair_stop_policy = RepairStopPolicy()


__all__ = ["RepairStopPolicy", "repair_stop_policy"]
