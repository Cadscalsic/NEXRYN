"""Dependency runtime visibility and cache accounting."""

from __future__ import annotations

from time import perf_counter
from typing import Any, Mapping


class DependencyVisibilityEngine:
    system_name = "dependency_visibility_engine"

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.cache_hits = 0
        self.cache_misses = 0

    def start_chain(self, concept: str) -> dict[str, Any]:
        return {"concept": concept, "started_at": perf_counter()}

    def finish_chain(
        self,
        token: Mapping[str, Any],
        node_count: int = 0,
        expansion_count: int = 0,
        recursion_count: int = 0,
        cache_hit: bool | None = None,
    ) -> dict[str, Any]:
        seconds = round(max(0.0, perf_counter() - float(token.get("started_at", perf_counter()))), 6)
        if cache_hit is True:
            self.cache_hits += 1
        elif cache_hit is False:
            self.cache_misses += 1
        record = {
            "concept": token.get("concept"),
            "dependency_chain_execution_time": seconds,
            "dependency_node_count": int(node_count or 0),
            "dependency_expansion_count": int(expansion_count or 0),
            "dependency_recursion_count": int(recursion_count or 0),
            "dependency_cache_hits": self.cache_hits,
            "dependency_cache_misses": self.cache_misses,
        }
        self.records.append(record)
        return record

    def summarize(self, dependency_report: Mapping[str, Any] | None = None) -> dict[str, Any]:
        dependency_report = dependency_report if isinstance(dependency_report, Mapping) else {}
        execution_time = sum(item["dependency_chain_execution_time"] for item in self.records)
        node_count = sum(item["dependency_node_count"] for item in self.records)
        expansion_count = sum(item["dependency_expansion_count"] for item in self.records)
        recursion_count = sum(item["dependency_recursion_count"] for item in self.records)
        return {
            "system": self.system_name,
            "dependency_chain_execution_time": round(
                max(execution_time, _number(dependency_report.get("dependency_reasoning_time_seconds"))),
                4,
            ),
            "dependency_node_count": max(node_count, int(_number(dependency_report.get("dependency_node_count")))),
            "dependency_expansion_count": max(expansion_count, int(_number(dependency_report.get("dependency_expansion_count")))),
            "dependency_recursion_count": max(recursion_count, int(_number(dependency_report.get("dependency_recursion_count")))),
            "dependency_cache_hits": self.cache_hits + int(_number(dependency_report.get("dependency_cache_hits"))),
            "dependency_cache_misses": self.cache_misses + int(_number(dependency_report.get("dependency_cache_misses"))),
            "dependency_records": list(self.records),
        }


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


dependency_visibility_engine = DependencyVisibilityEngine()


__all__ = ["DependencyVisibilityEngine", "dependency_visibility_engine"]
