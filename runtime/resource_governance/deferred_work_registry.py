"""Canonical ledger for deferred maintenance work."""

from __future__ import annotations

from datetime import datetime

from runtime.resource_governance.deferred_maintenance_plan import (
    MaintenanceWorkItem,
    MaintenanceWorkStatus,
)


class DeferredWorkRegistry:
    def __init__(self):
        self._items: dict[str, MaintenanceWorkItem] = {}
        self.idempotency_events: list[dict[str, str]] = []

    def register(self, item: MaintenanceWorkItem) -> MaintenanceWorkItem:
        existing = self._items.get(item.idempotency_key)
        if existing is not None:
            self.idempotency_events.append({
                "event": "duplicate_maintenance_rejected",
                "idempotency_key": item.idempotency_key,
                "existing_work_id": existing.work_id,
            })
            return existing
        self._items[item.idempotency_key] = item
        return item

    def mark_completed(self, idempotency_key: str) -> None:
        item = self._items.get(idempotency_key)
        if item is not None:
            item.status = MaintenanceWorkStatus.COMPLETED.value
            item.completed_at = str(datetime.utcnow())

    def mark_stale(self, idempotency_key: str) -> None:
        item = self._items.get(idempotency_key)
        if item is not None:
            item.status = MaintenanceWorkStatus.DEFERRED.value

    def skip_unchanged(self, idempotency_key: str) -> MaintenanceWorkItem | None:
        item = self._items.get(idempotency_key)
        if item is not None:
            item.status = MaintenanceWorkStatus.SKIPPED_UNCHANGED.value
            self.idempotency_events.append({
                "event": "skipped_unchanged",
                "idempotency_key": idempotency_key,
            })
        return item

    def pending(self) -> list[MaintenanceWorkItem]:
        return [
            item for item in self._items.values()
            if item.status in {MaintenanceWorkStatus.PLANNED.value, MaintenanceWorkStatus.READY.value, MaintenanceWorkStatus.DEFERRED.value}
        ]

    def all_items(self) -> list[MaintenanceWorkItem]:
        return list(self._items.values())

    def summary(self) -> dict[str, object]:
        return {
            "pending_count": len(self.pending()),
            "total_count": len(self._items),
            "items": [item.as_dict() for item in self.all_items()],
            "idempotency_events": list(self.idempotency_events),
        }


__all__ = ["DeferredWorkRegistry"]
