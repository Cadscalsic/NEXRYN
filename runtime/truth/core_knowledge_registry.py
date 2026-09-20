"""Registry view for concepts that should remain available but not dominate."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping


class CoreKnowledgeRegistry:
    system_name = "core_knowledge_registry"

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}

    def register_graduated(
        self,
        graduation_records: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        timestamp = datetime.utcnow().isoformat()
        registered = []
        for item in graduation_records or []:
            if not isinstance(item, Mapping):
                continue
            concept = str(item.get("concept") or "")
            if not concept:
                continue
            level = str(item.get("graduation_level") or "TRUTH_COMMITTED")
            if level not in {
                "STABLE_TRUTH",
                "FOUNDATIONAL_TRUTH",
                "CORE_KNOWLEDGE",
            }:
                continue
            record = {
                "concept": concept,
                "graduation_level": level,
                "mastery_score": _score(item.get("mastery_score")),
                "stability_score": _score(item.get("stability_score")),
                "reuse_score": _score(item.get("reuse_score")),
                "last_validation_timestamp": timestamp,
                "validation_frequency": _validation_frequency(level),
                "training_dominance_penalty": _dominance_penalty(level),
            }
            self._records[concept] = record
            registered.append(record)
        return {
            "system": self.system_name,
            "registered_core_concepts": registered,
            "core_concept_count": len(self._records),
            "core_concepts": sorted(self._records),
        }

    def all_records(self) -> list[dict[str, Any]]:
        return [dict(record) for record in self._records.values()]

    def as_concept_states(self) -> dict[str, str]:
        return {
            concept: record["graduation_level"]
            for concept, record in self._records.items()
        }

    def report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "core_knowledge": self.all_records(),
            "core_concept_count": len(self._records),
            "core_concepts": sorted(self._records),
        }


def _validation_frequency(level: str) -> str:
    return {
        "STABLE_TRUTH": "periodic",
        "FOUNDATIONAL_TRUTH": "occasional",
        "CORE_KNOWLEDGE": "rare_guardrail",
    }.get(level, "normal")


def _dominance_penalty(level: str) -> float:
    return {
        "STABLE_TRUTH": 0.35,
        "FOUNDATIONAL_TRUTH": 0.55,
        "CORE_KNOWLEDGE": 0.75,
    }.get(level, 0.0)


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


__all__ = ["CoreKnowledgeRegistry"]
