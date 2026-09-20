"""Detect recursive, duplicated, and oversized context serialization."""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping


class RecursiveContextAudit:
    system_name = "recursive_context_audit"

    def audit(self, contexts: Iterable[Any] | None) -> dict[str, Any]:
        rows = [self._audit_one(context) for context in list(contexts or [])]
        recursive = [row for row in rows if row["recursive_context_reference"]]
        oversized = [row for row in rows if row["serialized_context_bytes"] > 1_000_000]
        duplicates = _duplicates(rows)
        return {
            "system": self.system_name,
            "Recursive Context Audit": True,
            "context_count": len(rows),
            "recursive_context_references": len(recursive),
            "context_contains_context_count": sum(row["context_contains_context"] for row in rows),
            "duplicated_context_count": len(duplicates),
            "deep_serialization_loop_count": sum(row["max_depth"] > 8 for row in rows),
            "serialized_context_bytes": sum(row["serialized_context_bytes"] for row in rows),
            "bounded_serialized_context_size": not oversized,
            "audit_passed": not recursive and not oversized,
            "duplicates": duplicates,
            "contexts": rows,
        }

    def _audit_one(self, context: Any) -> dict[str, Any]:
        seen: set[int] = set()
        stats = {
            "recursive": False,
            "contains_context": False,
            "max_depth": 0,
        }
        self._walk(context, seen, stats, 0)
        try:
            payload = json.dumps(context, sort_keys=True, default=str)
        except (TypeError, ValueError):
            payload = str(context)
        return {
            "context_id": _context_id(context),
            "recursive_context_reference": stats["recursive"],
            "context_contains_context": stats["contains_context"],
            "max_depth": stats["max_depth"],
            "serialized_context_bytes": len(payload.encode("utf-8")),
        }

    def _walk(self, value: Any, seen: set[int], stats: dict[str, Any], depth: int) -> None:
        stats["max_depth"] = max(stats["max_depth"], depth)
        if isinstance(value, Mapping):
            object_id = id(value)
            if object_id in seen:
                stats["recursive"] = True
                return
            seen.add(object_id)
            if any("context" in str(key).lower() for key in value):
                stats["contains_context"] = True
            for item in value.values():
                self._walk(item, seen, stats, depth + 1)
        elif isinstance(value, (list, tuple, set)):
            for item in value[:200] if isinstance(value, list) else list(value)[:200]:
                self._walk(item, seen, stats, depth + 1)


def _context_id(context: Any) -> str:
    if isinstance(context, Mapping):
        return str(context.get("context_id") or context.get("context_name") or context.get("concept") or "")
    return str(context or "")


def _duplicates(rows: list[Mapping[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("context_id") or "")
        if key:
            counts[key] = counts.get(key, 0) + 1
    return sorted(key for key, count in counts.items() if count > 1)


recursive_context_audit = RecursiveContextAudit()


__all__ = ["RecursiveContextAudit", "recursive_context_audit"]
