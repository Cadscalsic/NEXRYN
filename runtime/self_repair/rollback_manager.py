"""Rollback support for safe operational repairs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class RollbackRecord:
    repair_id: str
    reason: str
    rollback_used: bool
    timestamp: str = field(default_factory=lambda: str(datetime.utcnow()))

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RollbackManager:
    def __init__(self):
        self.snapshots: dict[str, dict[str, Any]] = {}
        self.rollback_history: list[RollbackRecord] = []
        self.unsafe_attempts: dict[str, int] = {}

    def snapshot(
        self,
        repair_id: str,
        runtime_context: dict[str, Any],
    ) -> dict[str, Any]:
        snapshot = deepcopy(runtime_context or {})
        self.snapshots[repair_id] = snapshot
        return snapshot

    def restore(
        self,
        repair_id: str,
        reason: str,
    ) -> dict[str, Any]:
        self.unsafe_attempts[repair_id] = (
            self.unsafe_attempts.get(repair_id, 0) + 1
        )
        record = RollbackRecord(
            repair_id=repair_id,
            reason=reason,
            rollback_used=True,
        )
        self.rollback_history.append(record)
        return deepcopy(self.snapshots.get(repair_id, {}))

    def should_prevent_attempt(self, repair_id: str) -> bool:
        return self.unsafe_attempts.get(repair_id, 0) >= 1

    def report(self) -> dict[str, Any]:
        return {
            "snapshot_count": len(self.snapshots),
            "rollback_count": len(self.rollback_history),
            "rollback_history": [
                record.as_dict()
                for record in self.rollback_history[-10:]
            ],
        }


rollback_manager = RollbackManager()


__all__ = [
    "RollbackManager",
    "RollbackRecord",
    "rollback_manager",
]
