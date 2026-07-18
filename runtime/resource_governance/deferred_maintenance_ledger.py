"""Canonical deferred maintenance ledger."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.resource_governance.deferred_maintenance_plan import (
    MaintenanceWorkItem,
    MaintenanceWorkStatus,
)


@dataclass
class DeferredMaintenanceLedger:
    items: dict[str, MaintenanceWorkItem] = field(default_factory=dict)
    idempotency_index: dict[str, str] = field(default_factory=dict)
    recovery_events: list[dict[str, str]] = field(default_factory=list)

    def register(self, item: MaintenanceWorkItem) -> MaintenanceWorkItem:
        existing_id = self.idempotency_index.get(item.idempotency_key)
        if existing_id and existing_id in self.items:
            return self.items[existing_id]
        item.status = item.status or MaintenanceWorkStatus.PLANNED.value
        self.items[item.work_id] = item
        self.idempotency_index[item.idempotency_key] = item.work_id
        return item

    def mark_ready(self, work_id: str) -> bool:
        return self._set_status(work_id, MaintenanceWorkStatus.READY)

    def mark_running(self, work_id: str) -> bool:
        return self._set_status(work_id, MaintenanceWorkStatus.RUNNING)

    def mark_completed(self, work_id: str) -> bool:
        return self._set_status(work_id, MaintenanceWorkStatus.COMPLETED)

    def mark_failed(self, work_id: str, error: str, retryable: bool = True) -> bool:
        item = self.items.get(work_id)
        if item is None:
            return False
        item.last_error = str(error)
        item.status = (
            MaintenanceWorkStatus.FAILED_RETRYABLE.value
            if retryable
            else MaintenanceWorkStatus.FAILED_PERMANENT.value
        )
        return True

    def recover_retryable(self) -> list[MaintenanceWorkItem]:
        recovered = []
        for item in self.items.values():
            if item.status == MaintenanceWorkStatus.FAILED_RETRYABLE.value:
                item.attempts += 1
                item.status = MaintenanceWorkStatus.READY.value
                self.recovery_events.append({"work_id": item.work_id, "status": "READY"})
                recovered.append(item)
        return recovered

    def _set_status(self, work_id: str, status: MaintenanceWorkStatus) -> bool:
        item = self.items.get(work_id)
        if item is None:
            return False
        item.status = status.value
        return True

    def summary(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for item in self.items.values():
            counts[item.status] = counts.get(item.status, 0) + 1
        return {
            "work_count": len(self.items),
            "status_counts": counts,
            "idempotency_key_count": len(self.idempotency_index),
            "recovery_event_count": len(self.recovery_events),
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "items": [item.as_dict() for item in self.items.values()],
            "summary": self.summary(),
            "recovery_events": list(self.recovery_events),
        }


__all__ = ["DeferredMaintenanceLedger"]
