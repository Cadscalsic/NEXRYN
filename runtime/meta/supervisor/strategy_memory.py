"""Validated strategy memory for meta-cognitive reuse."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import time
from typing import Any, Mapping


@dataclass
class StrategyRecord:
    strategy_id: str
    strategy_name: str
    task_signature_id: str
    applicability_conditions: dict[str, Any] = field(default_factory=dict)
    success_rate: float = 0.0
    confidence: float = 0.0
    context_match: float = 0.0
    validated: bool = False
    integrity_verified: bool = False
    stale: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


class StrategyMemory:
    DEFAULT_PATH = (
        Path(__file__).resolve().parents[2]
        / "memory"
        / "storage"
        / "meta_supervisor"
        / "strategy_memory.json"
    )

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or self.DEFAULT_PATH)
        self.records: list[StrategyRecord] = []
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
            StrategyRecord(**item)
            for item in payload.get("strategies", [])
            if isinstance(item, dict)
        ]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"strategies": [asdict(record) for record in self.records]}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def remember(self, record: StrategyRecord) -> StrategyRecord:
        self.records = [
            existing
            for existing in self.records
            if existing.strategy_id != record.strategy_id
        ]
        self.records.append(record)
        self.save()
        return record

    def best_match(
        self,
        task_signature_id: str,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> StrategyRecord | None:
        candidates = [
            record
            for record in self.records
            if record.task_signature_id == task_signature_id
            and record.validated
            and record.integrity_verified
            and not record.stale
        ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda record: (
                record.success_rate,
                record.context_match,
                record.confidence,
            ),
        )


strategy_memory = StrategyMemory()


__all__ = [
    "StrategyMemory",
    "StrategyRecord",
    "strategy_memory",
]
