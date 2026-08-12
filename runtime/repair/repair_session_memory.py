from __future__ import annotations

from typing import Any, Mapping


class RepairSessionMemory:
    """Task-scoped repair session memory."""

    def __init__(self, repair_session_id: str) -> None:
        self.repair_session_id = repair_session_id
        self.iterations: list[dict[str, Any]] = []
        self.successful_deltas: list[dict[str, Any]] = []
        self.failed_deltas: list[dict[str, Any]] = []
        self.duplicate_repairs: list[dict[str, Any]] = []
        self.candidate_lineage: list[str] = []

    def record_iteration(self, iteration: Mapping[str, Any]) -> None:
        row = dict(iteration)
        self.iterations.append(row)
        candidate_id = str(row.get("current_candidate_id") or "")
        if candidate_id:
            self.candidate_lineage.append(candidate_id)
        if row.get("improvement_state") in {"REPAIR_IMPROVED", "REPAIR_EXACT_SUCCESS"}:
            self.successful_deltas.append(row)
        else:
            self.failed_deltas.append(row)

    def record_duplicate(self, duplicate: Mapping[str, Any]) -> None:
        self.duplicate_repairs.append(dict(duplicate))

    def as_dict(self) -> dict[str, Any]:
        return {
            "repair_session_id": self.repair_session_id,
            "candidate_lineage": list(self.candidate_lineage),
            "repair_iteration_lineage": [
                row.get("repair_iteration_id") for row in self.iterations
            ],
            "repair_iterations": list(self.iterations),
            "successful_deltas": list(self.successful_deltas),
            "failed_deltas": list(self.failed_deltas),
            "duplicate_repairs": list(self.duplicate_repairs),
            "duplicate_repair_count": len(self.duplicate_repairs),
        }


__all__ = ["RepairSessionMemory"]
