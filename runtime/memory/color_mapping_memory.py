"""Memory for reusable color mapping functions."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, Mapping


class ColorMappingMemory:
    """Store successful and failed color mappings by stable signatures."""

    system_name = "color_mapping_memory"

    def __init__(self):
        self.successful_mappings = []
        self.failed_mappings = []
        self.signature_index = {}
        self.object_color_relationships = {}

    def build_signature(
        self,
        mapping_matrix: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> str:
        mapping_matrix = mapping_matrix if isinstance(mapping_matrix, Mapping) else {}
        context = context if isinstance(context, Mapping) else {}
        mapping = mapping_matrix.get("mapping", mapping_matrix)
        parts = [
            f"{key}->{mapping[key]}"
            for key in sorted(mapping, key=lambda item: str(item))
        ]
        context_bits = [
            f"{key}:{context[key]}"
            for key in sorted(context)
            if key in {"mapping_type", "scope", "condition_type"}
        ]
        return "|".join(parts + context_bits) or "empty_color_mapping"

    def remember(
        self,
        mapping_matrix: Mapping[str, Any],
        program: Mapping[str, Any] | None = None,
        accuracy: float = 0.0,
        success: bool | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        success = bool(accuracy >= 1.0) if success is None else bool(success)
        signature = self.build_signature(
            mapping_matrix,
            {
                "mapping_type": mapping_matrix.get("mapping_type"),
                "scope": mapping_matrix.get("scope"),
                "condition_type": mapping_matrix.get("condition_type"),
            },
        )
        record = {
            "signature": signature,
            "mapping_matrix": copy.deepcopy(dict(mapping_matrix)),
            "program": copy.deepcopy(dict(program or {})),
            "accuracy": round(float(accuracy or 0.0), 4),
            "success": success,
            "evidence": copy.deepcopy(dict(evidence or {})),
            "timestamp": str(datetime.utcnow()),
        }
        target = self.successful_mappings if success else self.failed_mappings
        target.append(record)
        self.signature_index[signature] = record

        for relation in mapping_matrix.get("object_color_relationships", []) or []:
            object_id = relation.get("input_object")
            if not object_id:
                continue
            self.object_color_relationships.setdefault(str(object_id), [])
            self.object_color_relationships[str(object_id)].append(record)

        return record

    def retrieve_successful(
        self,
        input_colors: list[int] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if not input_colors:
            return [
                copy.deepcopy(record)
                for record in self.successful_mappings[-limit:]
            ]

        color_keys = {str(int(color)) for color in input_colors}
        matches = []
        for record in self.successful_mappings:
            mapping = (
                record.get("mapping_matrix", {})
                .get("mapping", {})
            )
            if color_keys.intersection({str(key) for key in mapping}):
                matches.append(copy.deepcopy(record))
        return matches[-limit:]

    def build_report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "successful_mappings": len(self.successful_mappings),
            "failed_mappings": len(self.failed_mappings),
            "known_signatures": len(self.signature_index),
            "object_color_relationships": {
                key: len(value)
                for key, value in self.object_color_relationships.items()
            },
        }


color_mapping_memory = ColorMappingMemory()


__all__ = [
    "ColorMappingMemory",
    "color_mapping_memory",
]
