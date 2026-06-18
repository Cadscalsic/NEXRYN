"""Discovery entry point for Alpha 1.1 process contexts."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.process.process_transition_extractor import (
    ProcessTransitionExtractor,
)


class ProcessContextDiscovery:
    """Discover known process context families from dependency chains."""

    system_name = "process_context_discovery"

    def __init__(self, extractor: ProcessTransitionExtractor | None = None):
        self.extractor = extractor or ProcessTransitionExtractor()

    def discover(
        self,
        concept: str,
        dependency_chain: list[str] | Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        extracted = self.extractor.extract(concept, dependency_chain)
        return {
            **extracted,
            "system": self.system_name,
            "process_context_generated": bool(
                extracted.get("process_context_discovered")
            ),
        }


__all__ = ["ProcessContextDiscovery"]
