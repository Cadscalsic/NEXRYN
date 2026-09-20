"""Executable program memory for reuse-first cognition."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import time
from typing import Any, Mapping


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
            and self._reusable(record)
        ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda record: record.match_confidence,
        )

    def best_match_for_signature(self, task_signature: Any) -> ProgramRecord | None:
        exact = self.best_match(task_signature.stable_id())
        if exact is not None:
            return exact

        query = (
            task_signature.as_dict()
            if hasattr(task_signature, "as_dict")
            else {}
        )
        ranked = []
        for record in self.records:
            if not self._reusable(record):
                continue
            score = self._semantic_match_score(query, record)
            if score >= 0.65:
                ranked.append((score, record))
        if not ranked:
            return None
        return max(
            ranked,
            key=lambda item: (item[0], item[1].match_confidence),
        )[1]

    def _reusable(self, record: ProgramRecord) -> bool:
        return (
            record.validation_state in {"validated", "stable"}
            and record.integrity_verified
            and not record.stale
        )

    def _semantic_match_score(
        self,
        query: Mapping[str, Any],
        record: ProgramRecord,
    ) -> float:
        query_tokens = _signature_tokens(query)
        record_signature = record.metadata.get("task_signature", {})
        record_tokens = _signature_tokens(
            record_signature if isinstance(record_signature, Mapping) else {}
        )
        record_tokens.update(_program_tokens(record))
        if not query_tokens or not record_tokens:
            return 0.0
        overlap = len(query_tokens & record_tokens) / len(query_tokens | record_tokens)
        confidence = max(0.0, min(1.0, float(record.match_confidence or 0.0)))
        return round((overlap * 0.75) + (confidence * 0.25), 4)


def _signature_tokens(signature: Mapping[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for value in signature.values():
        if isinstance(value, str):
            tokens.add(value)
        elif isinstance(value, (list, tuple, set)):
            tokens.update(str(item) for item in value if item)
    return {token for token in tokens if token}


def _program_tokens(record: ProgramRecord) -> set[str]:
    tokens = set()
    metadata = record.metadata if isinstance(record.metadata, Mapping) else {}
    concept = metadata.get("concept")
    if concept:
        tokens.add(str(concept))
    for step in record.operation_sequence:
        if not isinstance(step, Mapping):
            continue
        operation = step.get("operation") or step.get("operator")
        if operation:
            tokens.add(str(operation))
    return tokens


program_memory = ProgramMemory()


__all__ = [
    "ProgramMemory",
    "ProgramRecord",
    "program_memory",
]
