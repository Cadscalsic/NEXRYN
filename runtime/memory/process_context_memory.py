"""Memory for reusable process context models."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, Mapping


class ProcessContextMemory:
    """Store successful and failed process models by transition signature."""

    system_name = "process_context_memory"

    def __init__(self):
        self.successful_processes = []
        self.failed_processes = []
        self.signature_index = {}
        self.transition_patterns = {}
        self.dependency_structures = {}

    def build_signature(
        self,
        process_model: Mapping[str, Any] | None = None,
    ) -> str:
        process_model = process_model if isinstance(process_model, Mapping) else {}
        family = str(process_model.get("process_family", "unknown"))
        transitions = [
            str(item)
            for item in process_model.get("transition_sequence", []) or []
        ]
        dependencies = [
            str(item)
            for item in process_model.get("dependencies", []) or []
        ]
        return "|".join([family, *transitions, *dependencies]) or "empty_process"

    def remember(
        self,
        process_model: Mapping[str, Any],
        simulation_accuracy: float = 0.0,
        success: bool | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        success = (
            bool(simulation_accuracy >= 0.95)
            if success is None
            else bool(success)
        )
        signature = self.build_signature(process_model)
        record = {
            "signature": signature,
            "process_model": copy.deepcopy(dict(process_model)),
            "simulation_accuracy": round(float(simulation_accuracy or 0.0), 4),
            "success": success,
            "evidence": copy.deepcopy(dict(evidence or {})),
            "timestamp": str(datetime.utcnow()),
        }
        target = self.successful_processes if success else self.failed_processes
        target.append(record)
        self.signature_index[signature] = record

        family = str(process_model.get("process_family", "unknown"))
        self.transition_patterns.setdefault(family, [])
        self.transition_patterns[family].append(
            list(process_model.get("transition_sequence", []) or [])
        )
        self.dependency_structures.setdefault(family, [])
        self.dependency_structures[family].append(
            list(process_model.get("dependencies", []) or [])
        )
        return record

    def retrieve_successful(
        self,
        process_family: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if not process_family:
            return [
                copy.deepcopy(record)
                for record in self.successful_processes[-limit:]
            ]
        matches = [
            record
            for record in self.successful_processes
            if record.get("process_model", {}).get("process_family") == process_family
        ]
        return [copy.deepcopy(record) for record in matches[-limit:]]

    def build_report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "successful_processes": len(self.successful_processes),
            "failed_processes": len(self.failed_processes),
            "known_signatures": len(self.signature_index),
            "process_families": sorted(self.transition_patterns),
        }


process_context_memory = ProcessContextMemory()


__all__ = [
    "ProcessContextMemory",
    "process_context_memory",
]
