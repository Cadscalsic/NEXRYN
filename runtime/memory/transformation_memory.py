"""Memory for synthesized transformation programs."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, Mapping


class TransformationMemory:
    """Store successful and failed transformation programs by signature."""

    system_name = "transformation_memory"

    def __init__(self):
        self.successful_transformations = []
        self.failed_transformations = []
        self.concept_transformations = {}
        self.signature_index = {}

    def build_signature(
        self,
        concepts: list[str] | None = None,
        program: Mapping[str, Any] | None = None,
    ) -> str:
        concepts = sorted(set(concepts or []))
        steps = []
        for step in (program or {}).get("steps", []) or []:
            operation = step.get("operation", step.get("primitive", "unknown"))
            parameters = step.get("parameters", {})
            steps.append(f"{operation}:{self._stable(parameters)}")
        return "|".join(concepts + steps) or "empty_signature"

    def remember(
        self,
        program: Mapping[str, Any],
        concepts: list[str] | None = None,
        accuracy: float = 0.0,
        success: bool | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        success = bool(accuracy >= 1.0) if success is None else bool(success)
        signature = self.build_signature(concepts, program)
        record = {
            "signature": signature,
            "concepts": list(concepts or []),
            "program": copy.deepcopy(dict(program)),
            "accuracy": round(float(accuracy or 0.0), 4),
            "success": success,
            "evidence": copy.deepcopy(dict(evidence or {})),
            "timestamp": str(datetime.utcnow()),
        }
        target = (
            self.successful_transformations
            if success
            else self.failed_transformations
        )
        target.append(record)
        self.signature_index[signature] = record

        for concept in concepts or []:
            self.concept_transformations.setdefault(concept, [])
            self.concept_transformations[concept].append(record)

        return record

    def retrieve_successful(
        self,
        concepts: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if not concepts:
            return [
                copy.deepcopy(record)
                for record in self.successful_transformations[-limit:]
            ]

        concept_set = set(concepts)
        matches = []
        for record in self.successful_transformations:
            if concept_set.intersection(record.get("concepts", [])):
                matches.append(copy.deepcopy(record))
        return matches[-limit:]

    def concept_mappings(self) -> dict[str, list[str]]:
        mappings = {}
        for concept, records in self.concept_transformations.items():
            mappings[concept] = [
                step.get("operation", "unknown")
                for record in records
                for step in record.get("program", {}).get("steps", []) or []
            ]
        return mappings

    def build_report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "successful_transformations": len(self.successful_transformations),
            "failed_transformations": len(self.failed_transformations),
            "known_signatures": len(self.signature_index),
            "concept_transformation_mappings": self.concept_mappings(),
        }

    def _stable(self, value: Any) -> str:
        if isinstance(value, Mapping):
            parts = [
                f"{key}:{self._stable(value[key])}"
                for key in sorted(value)
            ]
            return "{" + ",".join(parts) + "}"
        if isinstance(value, (list, tuple)):
            return "[" + ",".join(self._stable(item) for item in value) + "]"
        return str(value)


transformation_memory = TransformationMemory()


__all__ = [
    "TransformationMemory",
    "transformation_memory",
]
