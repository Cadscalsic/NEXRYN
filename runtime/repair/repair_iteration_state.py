from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class RepairIterationState:
    repair_session_id: str
    repair_iteration_id: str
    iteration_index: int
    task_id: str
    run_id: str
    parent_candidate_id: str
    current_candidate_id: str
    residual_before: dict[str, Any]
    repair_candidate_id: str
    repair_route: str
    repair_operation: str
    residual_after: dict[str, Any]
    accuracy_before: float
    accuracy_after: float
    residual_reduction: int
    accuracy_delta: float
    improvement_state: str
    convergence_state: str
    created_at: str
    completed_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_iteration_state(
    *,
    repair_session_id: str,
    iteration_index: int,
    task_id: str,
    run_id: str,
    parent_candidate_id: str,
    current_candidate_id: str,
    residual_before: Mapping[str, Any],
    residual_after: Mapping[str, Any],
    accuracy_before: float,
    accuracy_after: float,
    repair_candidate_id: str,
    repair_route: str,
    repair_operation: str,
    improvement_state: str,
    convergence_state: str,
) -> RepairIterationState:
    created = str(datetime.utcnow())
    before = _residual_summary(residual_before)
    after = _residual_summary(residual_after)
    return RepairIterationState(
        repair_session_id=repair_session_id,
        repair_iteration_id=f"{repair_session_id}:iteration:{iteration_index}",
        iteration_index=iteration_index,
        task_id=task_id,
        run_id=run_id,
        parent_candidate_id=parent_candidate_id,
        current_candidate_id=current_candidate_id,
        residual_before=before,
        repair_candidate_id=repair_candidate_id,
        repair_route=repair_route,
        repair_operation=repair_operation,
        residual_after=after,
        accuracy_before=float(accuracy_before or 0.0),
        accuracy_after=float(accuracy_after or 0.0),
        residual_reduction=max(0, int(before["count"]) - int(after["count"])),
        accuracy_delta=round(float(accuracy_after or 0.0) - float(accuracy_before or 0.0), 4),
        improvement_state=improvement_state,
        convergence_state=convergence_state,
        created_at=created,
        completed_at=str(datetime.utcnow()),
    )


def _residual_summary(residual: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "count": int(residual.get("residual_difference_count", residual.get("count", 0)) or 0),
        "locations": list(residual.get("residual_locations", residual.get("locations", [])) or []),
        "type": str(residual.get("residual_type", residual.get("type", "none")) or "none"),
        "fingerprint": str(residual.get("residual_fingerprint", residual.get("fingerprint", "")) or ""),
    }


__all__ = ["RepairIterationState", "build_iteration_state"]
