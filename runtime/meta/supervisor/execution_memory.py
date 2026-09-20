"""Execution trace and governance outcome memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import time
from typing import Any


@dataclass
class ExecutionRecord:
    execution_id: str
    task_signature_id: str
    execution_trace: list[dict[str, Any]] = field(default_factory=list)
    residual_analysis: dict[str, Any] = field(default_factory=dict)
    failure_recovery: dict[str, Any] = field(default_factory=dict)
    governance_outcome: dict[str, Any] = field(default_factory=dict)
    episode_completed: bool = False
    integrity_verified: bool = False
    updated_at: float = field(default_factory=time.time)


class ExecutionMemory:
    DEFAULT_PATH = (
        Path(__file__).resolve().parents[2]
        / "memory"
        / "storage"
        / "meta_supervisor"
        / "execution_memory.json"
    )

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or self.DEFAULT_PATH)
        self.records: list[ExecutionRecord] = []
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
            ExecutionRecord(**item)
            for item in payload.get("executions", [])
            if isinstance(item, dict)
        ]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"executions": [asdict(record) for record in self.records]}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def remember(self, record: ExecutionRecord) -> ExecutionRecord:
        self.records = [
            existing
            for existing in self.records
            if existing.execution_id != record.execution_id
        ]
        self.records.append(record)
        self.save()
        return record

    def completed_episode(self, task_signature_id: str) -> ExecutionRecord | None:
        matches = [
            record
            for record in self.records
            if record.task_signature_id == task_signature_id
            and record.episode_completed
            and record.integrity_verified
        ]
        if not matches:
            return None
        return max(matches, key=lambda record: record.updated_at)


execution_memory = ExecutionMemory()


__all__ = [
    "ExecutionMemory",
    "ExecutionRecord",
    "execution_memory",
]
