"""Runtime registry for committed truths."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Iterable, Mapping


class TruthRegistry:
    system_name = "truth_registry"

    def __init__(self):
        self._truths: dict[str, dict[str, Any]] = {}

    def register_truth(
        self,
        truth: Mapping[str, Any] | None,
        source: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(truth, Mapping):
            return {
                "system": self.system_name,
                "registered": False,
                "reason": "truth_not_mapping",
                "received_type": type(truth).__name__,
            }

        record = self._normalize_truth(truth, source=source)
        self._truths[record["truth_id"]] = record
        return {
            "system": self.system_name,
            "registered": True,
            "truth_id": record["truth_id"],
            "truth": dict(record),
            "report_state": "final",
        }

    def register_batch(
        self,
        truths: Iterable[Mapping[str, Any]] | None,
        source: str | None = None,
    ) -> dict[str, Any]:
        results = [
            self.register_truth(truth, source=source)
            for truth in list(truths or [])
        ]
        registered = [
            result["truth"]
            for result in results
            if result.get("registered")
        ]
        return {
            "system": self.system_name,
            "report_state": "final",
            "registered_truths": registered,
            "registered_truth_count": len(registered),
            "rejected_truth_count": len(results) - len(registered),
            **self.metrics(),
        }

    def get_truth(self, truth_id: str) -> dict[str, Any]:
        return dict(self._truths.get(str(truth_id or ""), {}))

    def search_truths(self, concept: str | None = None) -> list[dict[str, Any]]:
        if concept is None:
            return self.all_truths()
        concept = str(concept)
        return [
            dict(truth)
            for truth in self._truths.values()
            if truth.get("truth_name") == concept
            or truth.get("concept") == concept
        ]

    def all_truths(self) -> list[dict[str, Any]]:
        return [dict(truth) for truth in self._truths.values()]

    def metrics(self) -> dict[str, Any]:
        return {
            "truth_count": len(self._truths),
            "committed_truth_count": len(self._truths),
        }

    def report(self) -> dict[str, Any]:
        truths = self.all_truths()
        return {
            "system": self.system_name,
            "report_state": "final",
            "truths": truths,
            "committed_truths": truths,
            **self.metrics(),
        }

    def _normalize_truth(
        self,
        truth: Mapping[str, Any],
        source: str | None = None,
    ) -> dict[str, Any]:
        record = dict(truth)
        truth_name = str(
            record.get("truth_name")
            or record.get("concept")
            or record.get("truth")
            or "runtime_truth"
        )
        record["truth_name"] = truth_name
        record["concept"] = record.get("concept") or truth_name
        record["truth_type"] = record.get("truth_type") or "COMMITTED_TRUTH"
        record["truth_confidence"] = _score(
            record.get("truth_confidence", record.get("commit_score", 0.0))
        )
        record["supporting_contexts"] = _list(record.get("supporting_contexts"))
        record["supporting_dependencies"] = _list(
            record.get("supporting_dependencies")
        )
        record["supporting_tasks"] = _list(record.get("supporting_tasks"))
        record["truth_lineage"] = _list(record.get("truth_lineage"))
        record["commit_timestamp"] = (
            record.get("commit_timestamp") or datetime.utcnow().isoformat()
        )
        record["source"] = record.get("source") or source or self.system_name
        record["truth_id"] = (
            record.get("truth_id")
            or _stable_truth_id(record)
        )
        return record


def _stable_truth_id(record: Mapping[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, default=str)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    name = str(record.get("truth_name") or "runtime_truth").lower()
    return f"truth:{name}:{digest}"


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


truth_registry = TruthRegistry()


__all__ = ["TruthRegistry", "truth_registry"]
