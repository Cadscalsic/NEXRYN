"""Executable program memory for reuse-first cognition."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import time
from typing import Any


@dataclass
class ProgramRecord:
    program_id: str
    task_signature_id: str
    program: dict[str, Any] = field(default_factory=dict)
    operation_sequence: list[dict[str, Any]] = field(default_factory=list)
    match_confidence: float = 0.0
    validation_state: str = "unvalidated"
    integrity_verified: bool = False
    stale: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


class ProgramMemory:
    DEFAULT_PATH = (
        Path(__file__).resolve().parents[2]
        / "memory"
        / "storage"
        / "meta_supervisor"
        / "program_memory.json"
    )

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or self.DEFAULT_PATH)
        self.records: list[ProgramRecord] = []
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
            ProgramRecord(**item)
            for item in payload.get("programs", [])
            if isinstance(item, dict)
        ]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"programs": [asdict(record) for record in self.records]}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def remember(self, record: ProgramRecord) -> ProgramRecord:
        self.records = [
            existing
            for existing in self.records
            if existing.program_id != record.program_id
        ]
        self.records.append(record)
        self.save()
        return record

    def best_match(self, task_signature_id: str) -> ProgramRecord | None:
        candidates = [
            record
            for record in self.records
            if record.task_signature_id == task_signature_id
            and record.validation_state in {"validated", "stable"}
            and record.integrity_verified
            and not record.stale
        ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda record: record.match_confidence,
        )


program_memory = ProgramMemory()


__all__ = [
    "ProgramMemory",
    "ProgramRecord",
    "program_memory",
]
