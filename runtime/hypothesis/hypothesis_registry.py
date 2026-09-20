"""In-memory registry for active, accepted, rejected, and reusable hypotheses."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class HypothesisRegistry:
    """Store hypothesis lifecycle state without executing candidates."""

    system_name = "hypothesis_registry"

    def __init__(self):
        self.active_hypotheses: dict[str, dict[str, Any]] = {}
        self.accepted_hypotheses: dict[str, dict[str, Any]] = {}
        self.rejected_hypotheses: dict[str, dict[str, Any]] = {}
        self.reusable_hypotheses: dict[str, dict[str, Any]] = {}

    def register(self, hypothesis: Mapping[str, Any]) -> dict[str, Any]:
        record = self._normalize(hypothesis)
        self.active_hypotheses[record["hypothesis_id"]] = record
        if record.get("reusable"):
            self.reusable_hypotheses[record["hypothesis_id"]] = record
        return dict(record)

    def accept(self, hypothesis_id: str) -> dict[str, Any] | None:
        record = self.active_hypotheses.get(hypothesis_id)
        if not record:
            return None
        record = dict(record)
        record["registry_state"] = "ACCEPTED"
        self.accepted_hypotheses[hypothesis_id] = record
        self.active_hypotheses[hypothesis_id] = record
        if record.get("reusable"):
            self.reusable_hypotheses[hypothesis_id] = record
        return dict(record)

    def reject(self, hypothesis_id: str, reason: str | None = None) -> dict[str, Any] | None:
        record = self.active_hypotheses.get(hypothesis_id)
        if not record:
            return None
        record = dict(record)
        record["registry_state"] = "REJECTED"
        record["rejection_reason"] = reason
        self.rejected_hypotheses[hypothesis_id] = record
        self.active_hypotheses[hypothesis_id] = record
        self.reusable_hypotheses.pop(hypothesis_id, None)
        return dict(record)

    def reusable(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.reusable_hypotheses.values()]

    def report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "active_hypotheses": len(self.active_hypotheses),
            "accepted_hypotheses": len(self.accepted_hypotheses),
            "rejected_hypotheses": len(self.rejected_hypotheses),
            "reusable_hypotheses": len(self.reusable_hypotheses),
            "registry_state": "OPERATIONAL",
            "records": [dict(item) for item in self.active_hypotheses.values()],
        }

    def reset(self) -> None:
        self.active_hypotheses.clear()
        self.accepted_hypotheses.clear()
        self.rejected_hypotheses.clear()
        self.reusable_hypotheses.clear()

    def _normalize(self, hypothesis: Mapping[str, Any]) -> dict[str, Any]:
        record = deepcopy(dict(hypothesis))
        record.setdefault("hypothesis_id", _hypothesis_id(record))
        record.setdefault("hypothesis_name", record["hypothesis_id"])
        record.setdefault("hypothesis_type", "semantic")
        record.setdefault("confidence", 0.0)
        record.setdefault("semantic_support", record.get("confidence", 0.0))
        record.setdefault("context_support", 0.0)
        record.setdefault("execution_ready", False)
        record.setdefault("registry_state", "ACTIVE")
        record.setdefault("reusable", bool(record.get("execution_ready")))
        return record


def _hypothesis_id(record: Mapping[str, Any]) -> str:
    name = _normalize(record.get("hypothesis_name") or record.get("name") or "hypothesis")
    return f"hypothesis:{name}"


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


hypothesis_registry = HypothesisRegistry()

__all__ = ["HypothesisRegistry", "hypothesis_registry"]
