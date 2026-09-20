from __future__ import annotations

from typing import Any, Mapping


class ResidualTrajectory:
    """Current repair-session trajectory, isolated from historical metrics."""

    def __init__(self, repair_session_id: str) -> None:
        self.repair_session_id = repair_session_id
        self.residual_counts: list[int] = []
        self.accuracy_values: list[float] = []
        self.residual_fingerprints: list[str] = []
        self.candidate_ids: list[str] = []
        self.repair_operations: list[str] = []

    def record(
        self,
        *,
        residual_count: int,
        accuracy: float,
        residual_fingerprint: str = "",
        candidate_id: str = "",
        repair_operation: str = "",
    ) -> None:
        self.residual_counts.append(int(residual_count or 0))
        self.accuracy_values.append(round(float(accuracy or 0.0), 4))
        self.residual_fingerprints.append(str(residual_fingerprint or ""))
        self.candidate_ids.append(str(candidate_id or ""))
        self.repair_operations.append(str(repair_operation or ""))

    def as_dict(self) -> dict[str, Any]:
        initial = self.residual_counts[0] if self.residual_counts else 0
        current = self.residual_counts[-1] if self.residual_counts else 0
        return {
            "repair_session_id": self.repair_session_id,
            "residual_counts": list(self.residual_counts),
            "accuracy_values": list(self.accuracy_values),
            "residual_fingerprints": list(self.residual_fingerprints),
            "candidate_ids": list(self.candidate_ids),
            "repair_operations": list(self.repair_operations),
            "trajectory_length": len(self.residual_counts),
            "total_residual_reduction": max(0, initial - current),
            "best_residual_count": min(self.residual_counts) if self.residual_counts else 0,
            "best_accuracy": max(self.accuracy_values) if self.accuracy_values else 0.0,
            "trajectory_state": classify_trajectory(self.residual_counts),
        }


def classify_trajectory(counts: list[int] | tuple[int, ...]) -> str:
    values = [int(value or 0) for value in counts]
    if not values:
        return "NOT_STARTED"
    if values[-1] == 0:
        return "EXACT_SUCCESS"
    if len(values) == 1:
        return "IMPROVING"
    if values[-1] > values[-2]:
        return "REGRESSION"
    if _oscillates(values):
        return "OSCILLATION"
    if len(values) >= 3 and values[-1] == values[-2] == values[-3]:
        return "STAGNATION"
    if len(values) >= 2 and values[-1] == values[-2]:
        return "SLOW_CONVERGENCE"
    if all(values[index] > values[index + 1] for index in range(len(values) - 1)):
        return "MONOTONIC_CONVERGENCE"
    return "IMPROVING"


def trajectory_from_iterations(
    repair_session_id: str,
    initial_residual: Mapping[str, Any],
    initial_accuracy: float,
    iterations: list[Mapping[str, Any]],
) -> dict[str, Any]:
    trajectory = ResidualTrajectory(repair_session_id)
    trajectory.record(
        residual_count=int(initial_residual.get("residual_difference_count", 0) or 0),
        accuracy=float(initial_accuracy or 0.0),
        residual_fingerprint=str(initial_residual.get("residual_fingerprint", "") or ""),
        candidate_id=str(initial_residual.get("source_candidate_id", "current_candidate") or "current_candidate"),
        repair_operation="INITIAL_RESIDUAL",
    )
    for iteration in iterations:
        residual_after = iteration.get("residual_after", {}) if isinstance(iteration, Mapping) else {}
        trajectory.record(
            residual_count=int(residual_after.get("count", 0) or 0),
            accuracy=float(iteration.get("accuracy_after", 0.0) or 0.0),
            residual_fingerprint=str(residual_after.get("fingerprint", "") or ""),
            candidate_id=str(iteration.get("current_candidate_id", "") or ""),
            repair_operation=str(iteration.get("repair_operation", "") or ""),
        )
    return trajectory.as_dict()


def _oscillates(values: list[int]) -> bool:
    if len(values) < 4:
        return False
    return values[-1] == values[-3] and values[-2] > values[-1]


__all__ = ["ResidualTrajectory", "classify_trajectory", "trajectory_from_iterations"]
