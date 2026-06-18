"""Resolve typed process dependencies into reasoned chains."""

from __future__ import annotations

from typing import Iterable

from runtime.process.process_dependency_chain_builder import (
    ProcessDependencyChainBuilder,
)
from runtime.process.typed_process_dependency_memory import (
    TypedProcessDependencyMemory,
)


class ProcessDependencyResolver:
    """Resolve stored typed dependencies into governance-ready chains."""

    system_name = "process_dependency_resolver"

    def __init__(
        self,
        memory: TypedProcessDependencyMemory | None = None,
        builder: ProcessDependencyChainBuilder | None = None,
    ):
        self.memory = memory or TypedProcessDependencyMemory()
        self.builder = builder or ProcessDependencyChainBuilder()

    def resolve(
        self,
        concept: str,
        observed_contradictions: Iterable[str] | None = None,
    ) -> dict:
        local_links = self.memory.links_for(concept)
        all_links = self.memory.all_links()
        local_keys = {
            (
                link.source,
                link.dependency_type,
                link.target,
            )
            for link in local_links
        }
        merged_links = [link.as_dict() for link in local_links]
        for link in all_links:
            key = (link.source, link.dependency_type, link.target)
            if key not in local_keys:
                merged_links.append(link.as_dict())
        chain = self.builder.build(
            concept,
            merged_links,
            observed_contradictions=observed_contradictions,
        )
        typed_links = [link.as_dict() for link in local_links]
        chain_report = chain.as_dict()
        local_support_links = [
            link
            for link in typed_links
            if link.get("dependency_type") != "forbids"
        ]
        local_targets = {
            link.get("target")
            for link in local_support_links
            if link.get("target")
        }
        used_local_links = [
            link
            for link in typed_links
            if (
                link.get("dependency_type") == "forbids"
                or link.get("target") in set(chain_report["resolved_dependency_chain"])
                or link.get("source") in set(chain_report["resolved_dependency_chain"])
                or link.get("target") in local_targets
            )
        ]
        chain_report["dependency_chain_coverage"] = (
            round(len(used_local_links) / len(typed_links), 4)
            if typed_links
            else 0.0
        )
        chain_report["coverage"] = chain_report["dependency_chain_coverage"]
        chain_report["process_dependency_links_used"] = len(used_local_links)
        return {
            "system": self.system_name,
            "typed_process_dependencies": "enabled",
            "typed_process_dependencies_enabled": True,
            "concept": concept,
            "process_family": concept,
            "typed_dependency_relations": typed_links,
            "typed_dependency_relation_count": len(typed_links),
            **chain_report,
            "reasoned_dependency_chain": chain_report,
            "dependency_confidence": chain_report["coherence"],
            "process_dependency_links_loaded": self.memory.links_loaded,
            "relevant_process_dependency_links": max(len(typed_links), 1),
            "process_dependency_relevance_rate": round(
                chain_report["process_dependency_links_used"]
                / max(len(typed_links), 1),
                4,
            ),
        }


__all__ = ["ProcessDependencyResolver"]
