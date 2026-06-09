from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from core.epistemic_models import clamp


DEFAULT_DEPENDENCY_CHAIN_LEDGER_PATH = (
    Path("runtime") / "memory" / "storage" / "dependency_chain_ledger.json"
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _chain_id(nodes: Iterable[Any]) -> str:
    return " -> ".join(str(node).strip() for node in nodes if str(node).strip())


@dataclass
class DependencyChainRecord:
    source: str
    target: str
    nodes: list[str]
    confidence: float
    relation: str = "causes"
    support_count: int = 1
    first_observed: str = field(default_factory=_timestamp)
    last_observed: str = field(default_factory=_timestamp)
    contexts: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.nodes = [str(node).strip() for node in self.nodes if str(node).strip()]
        self.source = str(self.source or (self.nodes[0] if self.nodes else "")).strip()
        self.target = str(self.target or (self.nodes[-1] if self.nodes else "")).strip()
        self.confidence = clamp(self.confidence)
        self.support_count = max(int(self.support_count or 0), 1)
        self.contexts = sorted({
            str(context).strip()
            for context in self.contexts
            if str(context).strip()
        })
        self.evidence = dict(self.evidence or {})
        self.metadata = dict(self.metadata or {})

    @property
    def chain_id(self) -> str:
        return _chain_id(self.nodes)

    def as_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            **asdict(self),
        }

    def as_reasoning_record(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "signals": list(self.nodes),
            "evidence": {
                **dict(self.evidence),
                "confidence": self.confidence,
            },
            "metadata": {
                **dict(self.metadata),
                "dependency_chain_ledger": True,
                "support_count": self.support_count,
                "contexts": list(self.contexts),
            },
        }


class DependencyChainLedger:
    """Persistent memory for explicit reasoned dependency chains."""

    def __init__(self, storage_path: str | Path | None = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self.records: dict[str, DependencyChainRecord] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_path is None or not self.storage_path.exists():
            return
        with self.storage_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        records = payload.get("records", {})
        self.records = {}
        for chain_id, data in records.items():
            if not isinstance(data, dict):
                continue
            clean = dict(data)
            clean.pop("chain_id", None)
            try:
                record = DependencyChainRecord(**clean)
            except TypeError:
                continue
            self.records[chain_id] = record

    def _persist(self) -> None:
        if self.storage_path is None:
            return
        temporary_path = self.storage_path.with_suffix(
            f"{self.storage_path.suffix}.tmp"
        )
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(self.report(), file, indent=2, sort_keys=True)
            temporary_path.replace(self.storage_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def add_chain(
        self,
        nodes: Iterable[Any],
        confidence: float,
        relation: str = "causes",
        context: str | None = None,
        evidence: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        source: str | None = None,
        target: str | None = None,
    ) -> dict[str, Any]:
        nodes = [str(node).strip() for node in nodes if str(node).strip()]
        if len(nodes) < 2:
            return {
                "added": False,
                "reason": "dependency_chain_requires_at_least_two_nodes",
            }
        chain_id = _chain_id(nodes)
        now = _timestamp()
        contexts = [context] if context else []
        if chain_id in self.records:
            record = self.records[chain_id]
            record.confidence = max(record.confidence, clamp(confidence))
            record.support_count += 1
            record.last_observed = now
            record.contexts = sorted(set(record.contexts + contexts))
            record.evidence.update(evidence or {})
            record.metadata.update(metadata or {})
            added = False
        else:
            record = DependencyChainRecord(
                source=source or nodes[0],
                target=target or nodes[-1],
                nodes=nodes,
                relation=relation,
                confidence=confidence,
                contexts=contexts,
                evidence=evidence or {},
                metadata=metadata or {},
                first_observed=now,
                last_observed=now,
            )
            self.records[chain_id] = record
            added = True
        self._persist()
        return {
            "added": added,
            "chain_id": chain_id,
            "record": record.as_dict(),
        }

    def record_reasoning_report(
        self,
        reasoning_report: dict[str, Any],
        context: str | None = None,
    ) -> dict[str, Any]:
        chain = reasoning_report.get("dependency_chain") or {}
        nodes = chain.get("nodes") or []
        return self.add_chain(
            nodes,
            confidence=reasoning_report.get("confidence", 0.0),
            relation="causes",
            context=context,
            evidence={
                "observed_signals": reasoning_report.get("observed_signals", []),
                "inferred_signals": reasoning_report.get("inferred_signals", []),
            },
            metadata={
                "system": reasoning_report.get("system"),
                "reasoning_state": reasoning_report.get("reasoning_state"),
                "recommended_action": reasoning_report.get("recommended_action"),
            },
            source=reasoning_report.get("source"),
            target=reasoning_report.get("target"),
        )

    def reasoning_records(self) -> list[dict[str, Any]]:
        return [
            record.as_reasoning_record()
            for record in sorted(
                self.records.values(),
                key=lambda item: (-item.confidence, item.chain_id),
            )
        ]

    def report(self) -> dict[str, Any]:
        records = {
            chain_id: record.as_dict()
            for chain_id, record in sorted(self.records.items())
        }
        return {
            "system": "dependency_chain_ledger",
            "record_count": len(records),
            "records": records,
            "persistent_storage_enabled": self.storage_path is not None,
            "storage_path": str(self.storage_path) if self.storage_path else None,
        }


__all__ = [
    "DEFAULT_DEPENDENCY_CHAIN_LEDGER_PATH",
    "DependencyChainLedger",
    "DependencyChainRecord",
]
