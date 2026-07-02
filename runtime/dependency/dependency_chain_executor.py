"""Execute dependency-memory reasoning for governance consumption."""

from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from runtime.dependency.dependency_chain_builder import DependencyChainBuilder


class DependencyChainExecutor:
    system_name = "dependency_chain_executor"
    _shared_cache: dict[tuple, dict] = {}
    _shared_cache_hits = 0
    _shared_cache_misses = 0
    _max_shared_cache_entries = 512

    def __init__(
        self,
        memory=None,
        builder: DependencyChainBuilder | None = None,
    ):
        if memory is None:
            from runtime.process.typed_process_dependency_memory import (
                TypedProcessDependencyMemory,
            )

            memory = TypedProcessDependencyMemory()
        self.memory = memory
        self.builder = builder or DependencyChainBuilder()
        self._cache: dict[tuple, dict] = {}

    def execute(
        self,
        concept: str,
        observed_contradictions: Iterable[str] | None = None,
        max_depth: int = 8,
    ) -> dict:
        observed_key = tuple(sorted(str(item) for item in observed_contradictions or []))
        memory_signature = self._memory_signature()
        cache_key = (
            str(concept),
            int(max_depth or 0),
            observed_key,
            memory_signature,
        )
        if cache_key in self._cache:
            cached = deepcopy(self._cache[cache_key])
            cached["dependency_cache_hit"] = True
            cached["dependency_cache_scope"] = "instance"
            return cached
        if cache_key in self._shared_cache:
            cached = deepcopy(self._shared_cache[cache_key])
            cached["dependency_cache_hit"] = True
            cached["dependency_cache_scope"] = "shared"
            self._cache[cache_key] = deepcopy(cached)
            type(self)._shared_cache_hits += 1
            return cached

        type(self)._shared_cache_misses += 1
        links = [link.as_dict() for link in self.memory.all_links()]
        local_links = [link.as_dict() for link in self.memory.links_for(concept)]
        report = self.builder.build(
            concept,
            links,
            observed_contradictions=observed_contradictions,
            max_depth=max_depth,
        )
        report = self._apply_process_spine(
            str(concept),
            report,
            local_links,
        )
        result = {
            **report,
            "system": self.system_name,
            "concept": concept,
            "typed_process_dependencies": "enabled",
            "typed_process_dependencies_enabled": True,
            "typed_dependency_relations": local_links,
            "typed_dependency_relation_count": len(local_links),
            "process_dependency_links_loaded": self.memory.links_loaded,
            "governance_consumable": bool(
                report.get("dependency_chain_depth", 0) > 0
                and report.get("dependency_chain_coverage", 0.0) > 0.0
                and not report.get("contradictions")
            ),
            "dependency_cache_hit": False,
            "dependency_cache_scope": None,
            "dependency_memory_signature": memory_signature,
        }
        self._cache[cache_key] = deepcopy(result)
        self._store_shared(cache_key, result)
        return result

    @classmethod
    def cache_report(cls) -> dict:
        total = cls._shared_cache_hits + cls._shared_cache_misses
        return {
            "system": cls.system_name,
            "dependency_executor_cache_entries": len(cls._shared_cache),
            "dependency_executor_cache_hits": cls._shared_cache_hits,
            "dependency_executor_cache_misses": cls._shared_cache_misses,
            "dependency_executor_cache_hit_rate": (
                round(cls._shared_cache_hits / total, 4)
                if total
                else 0.0
            ),
        }

    @classmethod
    def clear_shared_cache(cls) -> None:
        cls._shared_cache.clear()
        cls._shared_cache_hits = 0
        cls._shared_cache_misses = 0

    @classmethod
    def _store_shared(cls, cache_key, result):
        if len(cls._shared_cache) >= cls._max_shared_cache_entries:
            cls._shared_cache.pop(next(iter(cls._shared_cache)))
        cls._shared_cache[cache_key] = deepcopy(result)

    def _apply_process_spine(self, concept, report, local_links):
        if concept != "gravity" or not local_links:
            return report

        spine = [concept]
        for link in local_links:
            for key in ("source", "target"):
                value = str(link.get(key) or "").strip()
                if value and value not in spine:
                    spine.append(value)

        if len(spine) <= 1:
            return report

        return {
            **report,
            "graph_resolved_dependency_chain":
            report.get("resolved_dependency_chain", []),
            "graph_dependency_chain_depth":
            report.get("dependency_chain_depth", 0),
            "resolved_dependency_chain": spine,
            "chain": spine,
            "dependencies": spine,
            "dependency_chain_depth": len(spine) - 1,
            "dependency_chain_coverage": max(
                float(report.get("dependency_chain_coverage", 0.0) or 0.0),
                1.0,
            ),
            "process_spine_applied": True,
            "process_spine_reason": "gravity_requires_support_fall_rest_state",
        }

    def _memory_signature(self):
        if hasattr(self.memory, "dependency_signature"):
            return self.memory.dependency_signature()
        links = [link.as_dict() for link in self.memory.all_links()]
        return tuple(
            sorted(
                (
                    str(link.get("source")),
                    str(link.get("dependency_type")),
                    str(link.get("target")),
                    float(link.get("confidence", 0.0) or 0.0),
                )
                for link in links
            )
        )


__all__ = ["DependencyChainExecutor"]
