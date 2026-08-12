from __future__ import annotations

from typing import Any, Mapping

from runtime.repair.residual_trajectory import classify_trajectory


class RepairConvergenceAssessor:
    """Decide whether a current repair session should continue."""

    def assess(
        self,
        trajectory: Mapping[str, Any] | None,
        *,
        remaining_budget: int,
    ) -> dict[str, Any]:
        data = trajectory if isinstance(trajectory, Mapping) else {}
        counts = list(data.get("residual_counts", []) or [])
        state = classify_trajectory(counts)
        exact = bool(counts and int(counts[-1]) == 0)
        stagnation_count = _stagnation_count(counts)
        oscillation = state == "OSCILLATION"
        regression = state == "REGRESSION"
        residual_velocity = (
            float(counts[-2] - counts[-1])
            if len(counts) >= 2
            else 0.0
        )
        continue_repair = (
            not exact
            and remaining_budget > 0
            and state not in {"STAGNATION", "OSCILLATION", "REGRESSION", "BUDGET_EXHAUSTED"}
            and (not counts or counts[-1] > 0)
        )
        recommended = "CONTINUE_MINIMAL_REPAIR" if continue_repair else "STOP_REPAIR"
        if exact:
            recommended = "CLOSE_EXACT_SUCCESS"
        elif remaining_budget <= 0:
            state = "BUDGET_EXHAUSTED"
            recommended = "STOP_BUDGET_EXHAUSTED"
            continue_repair = False
        return {
            "convergence_state": state,
            "continue_repair": continue_repair,
            "convergence_score": _score(counts),
            "residual_velocity": residual_velocity,
            "stagnation_count": stagnation_count,
            "oscillation_detected": oscillation,
            "regression_detected": regression,
            "exact_success_detected": exact,
            "recommended_next_action": recommended,
        }


def _stagnation_count(counts: list[int]) -> int:
    if len(counts) < 2:
        return 0
    last = counts[-1]
    count = 0
    for value in reversed(counts[:-1]):
        if value == last:
            count += 1
        else:
            break
    return count


def _score(counts: list[int]) -> float:
    if not counts:
        return 0.0
    initial = max(int(counts[0] or 0), 1)
    current = int(counts[-1] or 0)
    return round(max(0.0, min(1.0, (initial - current) / initial)), 4)


repair_convergence_assessor = RepairConvergenceAssessor()


__all__ = ["RepairConvergenceAssessor", "repair_convergence_assessor"]
