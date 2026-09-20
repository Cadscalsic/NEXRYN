from __future__ import annotations

from copy import deepcopy
from typing import Any

from runtime.cache.cache_keys import stable_hash


class ConceptLifecycleCache:
    def __init__(self, max_entries: int = 128):
        self.max_entries = max_entries
        self._entries: dict[str, dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0
        self.stores = 0

    def key(
        self,
        ledger_report: dict[str, Any] | None,
        truth_candidate_report: dict[str, Any] | None,
        report_level: str = "normal",
    ) -> str:
        return stable_hash({
            "ledger": self._ledger_projection(ledger_report),
            "truth_candidates": truth_candidate_report or {},
            "report_level": report_level,
        })

    def get(self, key: str) -> dict[str, Any] | None:
        entry = self._entries.get(key)
        if entry is None:
            self.misses += 1
            return None
        self.hits += 1
        cached = deepcopy(entry)
        cached["concept_lifecycle_cache_hit"] = True
        cached["concept_lifecycle_cache_report"] = self.report()
        return cached

    def put(self, key: str, report: dict[str, Any]) -> dict[str, Any]:
        if len(self._entries) >= self.max_entries:
            self._entries.pop(next(iter(self._entries)))
        stored = deepcopy(report)
        stored["concept_lifecycle_cache_hit"] = False
        self._entries[key] = stored
        self.stores += 1
        result = deepcopy(stored)
        result["concept_lifecycle_cache_report"] = self.report()
        return result

    def report(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "system": "concept_lifecycle_cache",
            "cache_entries": len(self._entries),
            "concept_lifecycle_cache_hits": self.hits,
            "concept_lifecycle_cache_misses": self.misses,
            "concept_lifecycle_cache_stores": self.stores,
            "concept_lifecycle_cache_hit_rate": (
                round(self.hits / total, 4) if total else 0.0
            ),
        }

    def _ledger_projection(self, ledger_report):
        ledger_report = ledger_report if isinstance(ledger_report, dict) else {}
        concepts = []
        for item in ledger_report.get("concepts", []):
            if not isinstance(item, dict):
                continue
            concepts.append({
                "concept": item.get("concept"),
                "used_task_count": item.get("used_task_count"),
                "independent_success_rate":
                item.get("independent_success_rate"),
                "cross_task_support": item.get("cross_task_support"),
                "average_contradiction_score":
                item.get("average_contradiction_score"),
                "record_count": len(item.get("records", []))
                if isinstance(item.get("records"), list)
                else 0,
            })
        return {
            "concepts": sorted(
                concepts,
                key=lambda item: str(item.get("concept")),
            ),
            "concept_count": len(concepts),
        }


concept_lifecycle_cache = ConceptLifecycleCache()


__all__ = ["ConceptLifecycleCache", "concept_lifecycle_cache"]
