"""Safe repair planning for operational anomalies."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import uuid
from typing import Any

from runtime.self_repair.anomaly_detector import Anomaly


@dataclass
class RepairPlan:
    repair_id: str
    anomaly_type: str
    severity: str
    actions: list[str] = field(default_factory=list)
    requires_rollback: bool = False
    requires_governance_review: bool = False
    safe_to_execute: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RepairPlanner:
    ACTIONS_BY_ANOMALY = {
        "TERMINATION_DESYNC": [
            "SET_SHUTDOWN_FAST",
            "MARK_EPISODE_COMPLETED",
            "STOP_BACKGROUND_LOOPS",
            "WRITE_REPAIR_MEMORY",
        ],
        "SUCCESS_SEMANTICS_CONFLICT": [
            "SYNC_SUCCESS_FLAGS",
            "WRITE_REPAIR_MEMORY",
        ],
        "CACHE_REUSE_FAILURE": [
            "INVALIDATE_TEMP_CACHE",
            "WRITE_REPAIR_MEMORY",
        ],
        "LEARNING_SATURATION_CONFLICT": [
            "SYNC_RECOMMENDED_NEXT_STEP",
            "WRITE_REPAIR_MEMORY",
        ],
        "LOCALIZATION_STATE_CONFLICT": [
            "REQUEST_GOVERNANCE_REVIEW",
            "WRITE_REPAIR_MEMORY",
        ],
        "EXECUTION_INTEGRITY_CONFLICT": [
            "REQUEST_GOVERNANCE_REVIEW",
            "WRITE_REPAIR_MEMORY",
        ],
        "IDENTITY_STATE_CONFLICT": [
            "REQUEST_GOVERNANCE_REVIEW",
            "WRITE_REPAIR_MEMORY",
        ],
        "GOVERNANCE_REVALIDATION_LOOP": [
            "REQUEST_GOVERNANCE_REVIEW",
            "WRITE_REPAIR_MEMORY",
        ],
    }

    def plan(self, anomalies: list[Anomaly]) -> list[RepairPlan]:
        return [self.plan_one(anomaly) for anomaly in anomalies]

    def plan_one(self, anomaly: Anomaly) -> RepairPlan:
        actions = list(self.ACTIONS_BY_ANOMALY.get(
            anomaly.anomaly_type,
            ["REQUEST_GOVERNANCE_REVIEW", "WRITE_REPAIR_MEMORY"],
        ))
        critical = anomaly.severity == "CRITICAL"
        governance_review = (
            critical
            or "REQUEST_GOVERNANCE_REVIEW" in actions
        )
        safe_to_execute = not critical and not governance_review
        return RepairPlan(
            repair_id=str(uuid.uuid4()),
            anomaly_type=anomaly.anomaly_type,
            severity=anomaly.severity,
            actions=actions,
            requires_rollback=not critical and safe_to_execute,
            requires_governance_review=governance_review,
            safe_to_execute=safe_to_execute,
        )


repair_planner = RepairPlanner()


__all__ = [
    "RepairPlan",
    "RepairPlanner",
    "repair_planner",
]
