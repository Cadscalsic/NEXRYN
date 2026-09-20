"""Knowledge lifecycle accounting across creation, registration, injection, and reuse."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping


class KnowledgeFlowEngine:
    system_name = "knowledge_flow_engine"

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(
        self,
        stage: str,
        item: Mapping[str, Any] | str | None = None,
        concept: str | None = None,
        kind: str = "knowledge",
        reason: str | None = None,
    ) -> dict[str, Any]:
        event = {
            "stage": str(stage),
            "kind": str(kind),
            "concept": concept or _concept(item),
            "knowledge_id": _identity(item),
            "reason": reason,
        }
        self.events.append(event)
        return event

    def reconstruct(
        self,
        created: Iterable[Any] | None = None,
        registered: Iterable[Any] | None = None,
        injected: Iterable[Any] | None = None,
        consumed: Iterable[Any] | None = None,
        reused: Iterable[Any] | None = None,
        blocked: Iterable[Any] | None = None,
    ) -> dict[str, Any]:
        created_ids = {_identity(item) for item in created or []}
        registered_ids = {_identity(item) for item in registered or []}
        injected_ids = {_identity(item) for item in injected or []}
        consumed_ids = {_identity(item) for item in consumed or []}
        reused_ids = {_identity(item) for item in reused or []}
        blocked_ids = {_identity(item) for item in blocked or []}
        lost_ids = sorted(
            item_id
            for item_id in created_ids | registered_ids
            if item_id and item_id not in injected_ids and item_id not in consumed_ids
        )
        report = {
            "system": self.system_name,
            "KNOWLEDGE FLOW REPORT": True,
            "knowledge_created": len(created_ids),
            "knowledge_registered": len(registered_ids),
            "knowledge_injected": len(injected_ids),
            "knowledge_consumed": len(consumed_ids),
            "knowledge_reused": len(reused_ids),
            "knowledge_lost": len(lost_ids),
            "knowledge_blocked": len(blocked_ids),
            "lost_knowledge_ids": lost_ids,
            "blocked_knowledge_ids": sorted(item_id for item_id in blocked_ids if item_id),
            "knowledge_reuse_rate": round(
                len(reused_ids) / max(len(created_ids) + len(reused_ids), 1),
                4,
            ),
        }
        return report

    def report(self) -> dict[str, Any]:
        counts: dict[str, int] = defaultdict(int)
        for event in self.events:
            counts[event["stage"]] += 1
        return {
            "system": self.system_name,
            "KNOWLEDGE FLOW REPORT": True,
            "events": list(self.events),
            **{f"knowledge_{stage}": count for stage, count in counts.items()},
        }


def _identity(item: Any) -> str:
    if isinstance(item, Mapping):
        return str(
            item.get("context_id")
            or item.get("truth_id")
            or item.get("program_id")
            or item.get("strategy_id")
            or item.get("concept")
            or item.get("name")
            or ""
        )
    return str(item or "")


def _concept(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("concept") or item.get("truth_name") or item.get("name")
        return str(value) if value else None
    return str(item) if item else None


knowledge_flow_engine = KnowledgeFlowEngine()


__all__ = ["KnowledgeFlowEngine", "knowledge_flow_engine"]
