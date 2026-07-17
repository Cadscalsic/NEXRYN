"""Cognitive memory for reusable and historical hypotheses."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class HypothesisMemory:
    """Track successful, failed, reusable, and frequently successful hypotheses."""

    system_name = "hypothesis_memory"

    def __init__(self):
        self.successful_hypotheses: dict[str, dict[str, Any]] = {}
        self.failed_hypotheses: dict[str, dict[str, Any]] = {}
        self.reusable_hypotheses: dict[str, dict[str, Any]] = {}
        self.statistics: dict[str, dict[str, Any]] = {}

    def remember(
        self,
        hypothesis: Mapping[str, Any],
        *,
        success: bool,
        reusable: bool | None = None,
    ) -> dict[str, Any]:
        record = deepcopy(dict(hypothesis))
        hypothesis_id = str(record.get("hypothesis_id") or record.get("hypothesis_name"))
        record["memory_state"] = "SUCCESSFUL" if success else "FAILED"
        stats = self.statistics.setdefault(
            hypothesis_id,
            {
                "attempts": 0,
                "successes": 0,
                "failures": 0,
                "confidence_evolution": [],
            },
        )
        stats["attempts"] += 1
        if success:
            stats["successes"] += 1
            self.successful_hypotheses[hypothesis_id] = record
        else:
            stats["failures"] += 1
            self.failed_hypotheses[hypothesis_id] = record
        evolved = self._evolve_confidence(record, stats)
        record["evolved_confidence"] = evolved
        stats["confidence_evolution"].append(evolved)
        if reusable is None:
            reusable = bool(success and record.get("execution_ready"))
        if reusable:
            record["reusable"] = True
            self.reusable_hypotheses[hypothesis_id] = record
        return dict(record)

    def retrieve(
        self,
        concepts: list[str] | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        concept_set = {_normalize(item) for item in concepts or []}
        records = list(self.reusable_hypotheses.values())
        if concept_set:
            records = [
                record for record in records
                if concept_set.intersection({_normalize(item) for item in record.get("matched_concepts", []) or []})
                or _normalize(record.get("source_concept")) in concept_set
            ]
        records.sort(
            key=lambda item: (
                item.get("evolved_confidence", item.get("confidence", 0.0)),
                item.get("confidence", 0.0),
            ),
            reverse=True,
        )
        return [dict(item) for item in records[:limit]]

    def report(self) -> dict[str, Any]:
        frequently_successful = [
            hypothesis_id
            for hypothesis_id, stats in self.statistics.items()
            if stats.get("successes", 0) >= 2
        ]
        return {
            "system": self.system_name,
            "hypothesis_memory_operational": True,
            "successful_hypotheses": len(self.successful_hypotheses),
            "failed_hypotheses": len(self.failed_hypotheses),
            "reusable_hypotheses": len(self.reusable_hypotheses),
            "frequently_successful_hypotheses": frequently_successful,
            "hypothesis_statistics": deepcopy(self.statistics),
        }

    def reset(self) -> None:
        self.successful_hypotheses.clear()
        self.failed_hypotheses.clear()
        self.reusable_hypotheses.clear()
        self.statistics.clear()

    def _evolve_confidence(self, record: Mapping[str, Any], stats: Mapping[str, Any]) -> float:
        base = _score(record.get("confidence", 0.0))
        attempts = max(int(stats.get("attempts", 1)), 1)
        success_rate = float(stats.get("successes", 0)) / attempts
        return round(base * 0.70 + success_rate * 0.30, 4)


def _score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


hypothesis_memory = HypothesisMemory()

__all__ = ["HypothesisMemory", "hypothesis_memory"]
