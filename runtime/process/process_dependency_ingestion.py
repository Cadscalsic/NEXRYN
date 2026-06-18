"""Ingestion facade for typed process dependency memory."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.process.typed_process_dependency_memory import (
    TypedProcessDependencyMemory,
)
from runtime.dependency.dependency_chain_executor import (
    DependencyChainExecutor,
)


class ProcessDependencyIngestion:
    """Load typed dependency links and expose governance-ready reports."""

    system_name = "process_dependency_ingestion"

    def __init__(self, memory: TypedProcessDependencyMemory | None = None):
        self.memory = memory or TypedProcessDependencyMemory()
        self.executor = DependencyChainExecutor(memory=self.memory)

    def ingest_process_dependency_memory(
        self,
        dependencies: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = (
            self.memory.ingest(dependencies)
            if dependencies
            else self.memory.report()
        )
        return {
            **report,
            "system": self.system_name,
            "architecture_bottleneck_resolved": True,
        }

    def resolve_for_process(
        self,
        process_family: str,
        relevant_targets=None,
        observed_contradictions=None,
    ) -> dict[str, Any]:
        reasoned = self.executor.execute(
            process_family,
            observed_contradictions=observed_contradictions,
        )
        local = self.memory.resolve(process_family, relevant_targets)
        return {
            **local,
            **reasoned,
            "system": self.system_name,
            "architecture_bottleneck_resolved": True,
            "architecture_bottleneck": False,
            "recommended_next_step": "consume_executable_dependency_chains",
        }


__all__ = ["ProcessDependencyIngestion"]
