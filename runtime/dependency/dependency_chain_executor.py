"""Execute dependency-memory reasoning for governance consumption."""

from __future__ import annotations

from typing import Iterable

from runtime.dependency.dependency_chain_builder import DependencyChainBuilder


class DependencyChainExecutor:
    system_name = "dependency_chain_executor"

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

    def execute(
        self,
        concept: str,
        observed_contradictions: Iterable[str] | None = None,
        max_depth: int = 8,
    ) -> dict:
        links = [link.as_dict() for link in self.memory.all_links()]
        local_links = [link.as_dict() for link in self.memory.links_for(concept)]
        report = self.builder.build(
            concept,
            links,
            observed_contradictions=observed_contradictions,
            max_depth=max_depth,
        )
        return {
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
        }


__all__ = ["DependencyChainExecutor"]
