"""Bounded possibility generation for cognitive futures."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_FUTURE_TYPES: tuple[str, ...] = (
    "reuse_existing_strategy",
    "promote_new_strategy",
    "admit_new_context",
    "merge_similar_concepts",
    "keep_candidate_in_quarantine",
    "freeze_existing_truth",
    "expand_training_curriculum",
)


class PossibilitySpace:
    def generate(
        self,
        candidate: Mapping[str, Any] | Any,
        runtime_budget: Mapping[str, Any] | int | None = None,
    ) -> list[dict[str, Any]]:
        data = self._data(candidate)
        max_worlds = self._max_worlds(runtime_budget)
        candidate_type = str(data.get("candidate_type") or "concept")
        futures = []

        for future_type in DEFAULT_FUTURE_TYPES:
            if not self._future_applies(future_type, candidate_type):
                continue
            futures.append({
                "world_id": f"{self._candidate_name(data)}::{future_type}",
                "future_type": future_type,
                "candidate_type": candidate_type,
                "proposed_admission_level": self._level_for(future_type),
            })
            if len(futures) >= max_worlds:
                break

        return futures

    def _future_applies(self, future_type: str, candidate_type: str) -> bool:
        if future_type in {"reuse_existing_strategy", "promote_new_strategy"}:
            return candidate_type in {"strategy", "program"}
        if future_type == "admit_new_context":
            return candidate_type in {"context", "concept"}
        if future_type == "merge_similar_concepts":
            return candidate_type in {"concept", "context"}
        return True

    def _level_for(self, future_type: str) -> str:
        return {
            "reuse_existing_strategy": "TRUSTED_TOOL",
            "promote_new_strategy": "TRUSTED_TOOL",
            "admit_new_context": "WORLD_CITIZEN",
            "merge_similar_concepts": "OBSERVED_USEFUL",
            "keep_candidate_in_quarantine": "OUTSIDE_WORLD",
            "freeze_existing_truth": "OUTSIDE_WORLD",
            "expand_training_curriculum": "OBSERVED_USEFUL",
        }.get(future_type, "CANDIDATE")

    def _max_worlds(self, runtime_budget: Mapping[str, Any] | int | None) -> int:
        if isinstance(runtime_budget, int):
            return max(1, min(7, runtime_budget))
        if isinstance(runtime_budget, Mapping):
            value = runtime_budget.get("max_potential_worlds", runtime_budget.get("max_worlds"))
            try:
                return max(1, min(7, int(value)))
            except (TypeError, ValueError):
                return 7
        return 7

    def _candidate_name(self, data: Mapping[str, Any]) -> str:
        return str(data.get("candidate_name") or data.get("name") or "unnamed_candidate")

    def _data(self, value: Mapping[str, Any] | Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        data = {}
        for key in dir(value):
            if key.startswith("_"):
                continue
            item = getattr(value, key)
            if not callable(item):
                data[key] = item
        return data


possibility_space = PossibilitySpace()


__all__ = [
    "DEFAULT_FUTURE_TYPES",
    "PossibilitySpace",
    "possibility_space",
]
