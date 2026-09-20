"""Persistent repair memory to prevent repair loops."""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime
import json
from pathlib import Path
from typing import Any


@dataclass
class RepairMemoryRecord:
    timestamp: str
    anomaly_type: str
    severity: str
    repair_actions: list[str]
    success: bool
    rollback_used: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class RepairMemory:
    DEFAULT_PATH = (
        Path(__file__).resolve().parents[1]
        / "memory"
        / "storage"
        / "self_repair_memory.json"
    )

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or self.DEFAULT_PATH)
        self.records: list[RepairMemoryRecord] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.records = []
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.records = []
            return
        self.records = [
            RepairMemoryRecord(**item)
            for item in payload.get("repairs", [])
            if isinstance(item, dict)
        ]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "repairs": [
                record.as_dict()
                for record in self.records[-500:]
            ]
        }
        self.path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def record(
        self,
        anomaly_type: str,
        severity: str,
        repair_actions: list[str],
        success: bool,
        rollback_used: bool,
    ) -> RepairMemoryRecord:
        record = RepairMemoryRecord(
            timestamp=str(datetime.utcnow()),
            anomaly_type=anomaly_type,
            severity=severity,
            repair_actions=list(repair_actions),
            success=bool(success),
            rollback_used=bool(rollback_used),
        )
        self.records.append(record)
        self.save()
        return record

    def recent_attempts(
        self,
        anomaly_type: str,
        limit: int = 5,
    ) -> list[RepairMemoryRecord]:
        return [
            record
            for record in reversed(self.records)
            if record.anomaly_type == anomaly_type
        ][:limit]

    def loop_risk(self, anomaly_type: str) -> bool:
        recent = self.recent_attempts(anomaly_type, limit=3)
        return len(recent) >= 3 and all(not record.success for record in recent)

    def report(self) -> dict[str, Any]:
        return {
            "repair_memory_count": len(self.records),
            "latest_repairs": [
                record.as_dict()
                for record in self.records[-10:]
            ],
        }


repair_memory = RepairMemory()


__all__ = [
    "RepairMemory",
    "RepairMemoryRecord",
    "repair_memory",
]
