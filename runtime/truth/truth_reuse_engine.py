"""Search and reuse committed truths before creating new truth candidates."""

from __future__ import annotations

import json
from typing import Any, Mapping


class TruthReuseEngine:
    system_name = "truth_reuse_engine"

    def __init__(self) -> None:
        self.truth_hits = 0
        self.truth_misses = 0
        self.reused_truths: list[dict[str, Any]] = []

    def search_truth(
        self,
        query: Mapping[str, Any] | str | None,
        truth_registry=None,
        truths: list[Mapping[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        candidates = list(truths or [])
        if truth_registry is not None and hasattr(truth_registry, "all_truths"):
            candidates.extend(truth_registry.all_truths())
        ranked = [
            {**dict(candidate), "truth_relevance": self.rank_truth_relevance(query, candidate)}
            for candidate in candidates
            if isinstance(candidate, Mapping)
        ]
        ranked = [item for item in ranked if item["truth_relevance"] > 0.0]
        ranked.sort(key=lambda item: item["truth_relevance"], reverse=True)
        return ranked

    def rank_truth_relevance(
        self,
        query: Mapping[str, Any] | str | None,
        truth: Mapping[str, Any] | None,
    ) -> float:
        truth = truth if isinstance(truth, Mapping) else {}
        if not truth:
            return 0.0
        query_concept = _concept(query)
        truth_concept = str(truth.get("concept") or truth.get("truth_name") or "")
        score = 0.0
        if query_concept and query_concept == truth_concept:
            score += 0.7
        score += _overlap(query, truth) * 0.2
        score += _score(truth.get("truth_confidence") or truth.get("commit_score")) * 0.1
        return round(min(1.0, score), 4)

    def reuse_truth(
        self,
        query: Mapping[str, Any] | str | None,
        truth_registry=None,
        truths: list[Mapping[str, Any]] | None = None,
        min_relevance: float = 0.6,
    ) -> dict[str, Any]:
        ranked = self.search_truth(query, truth_registry=truth_registry, truths=truths)
        reusable = [truth for truth in ranked if truth["truth_relevance"] >= min_relevance]
        if reusable:
            self.truth_hits += 1
            reused = {**reusable[0], "truth_reused": True}
            self.reused_truths.append(reused)
            return {
                "system": self.system_name,
                "truth_reused": True,
                "reused_truth": reused,
                "truth_contribution_score": self.truth_contribution_score(reused),
                **self.metrics(),
            }
        self.truth_misses += 1
        return {
            "system": self.system_name,
            "truth_reused": False,
            "reused_truth": {},
            "truth_contribution_score": 0.0,
            **self.metrics(),
        }

    def truth_contribution_score(self, truth: Mapping[str, Any] | None) -> float:
        truth = truth if isinstance(truth, Mapping) else {}
        return round(
            _score(truth.get("truth_relevance"))
            * 0.6
            + _score(truth.get("truth_confidence") or truth.get("commit_score"))
            * 0.4,
            4,
        )

    def metrics(self) -> dict[str, Any]:
        total = self.truth_hits + self.truth_misses
        return {
            "truth_hits": self.truth_hits,
            "truth_misses": self.truth_misses,
            "truth_reuse_rate": round(self.truth_hits / max(total, 1), 4),
        }

    def report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "TRUTH REUSE REPORT": True,
            "reused_truths": list(self.reused_truths),
            **self.metrics(),
        }


def _concept(value: Mapping[str, Any] | str | None) -> str:
    if isinstance(value, Mapping):
        return str(value.get("concept") or value.get("truth_name") or "")
    return str(value or "")


def _overlap(query: Any, truth: Mapping[str, Any]) -> float:
    left = json.dumps(query, sort_keys=True, default=str) if isinstance(query, Mapping) else str(query or "")
    right = json.dumps(truth, sort_keys=True, default=str)
    left_tokens = {token for token in left.lower().replace("_", " ").split() if len(token) > 2}
    right_tokens = {token for token in right.lower().replace("_", " ").split() if len(token) > 2}
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


truth_reuse_engine = TruthReuseEngine()


__all__ = ["TruthReuseEngine", "truth_reuse_engine"]
