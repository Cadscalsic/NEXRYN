"""Reuse existing contexts, truths, strategies, and programs before regeneration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


class KnowledgeReuseEngine:
    system_name = "knowledge_reuse_engine"

    def __init__(self) -> None:
        self.context_hits = 0
        self.truth_hits = 0
        self.strategy_hits = 0
        self.program_hits = 0
        self.context_misses = 0
        self.truth_misses = 0
        self.strategy_misses = 0
        self.program_misses = 0
        self.reuse_events: list[dict[str, Any]] = []
        self._strategy_cache: list[dict[str, Any]] | None = None

    def reuse_before_regenerate(
        self,
        query: Mapping[str, Any] | str | None,
        contexts: list[Mapping[str, Any]] | None = None,
        truths: list[Mapping[str, Any]] | None = None,
        strategies: list[Mapping[str, Any]] | None = None,
        programs: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        context = self._best(query, contexts or [], "context")
        truth = self._best(query, truths or [], "truth")
        strategy = self._best(
            query,
            strategies or self._stored_strategies(),
            "strategy",
        )
        program = self._best(query, programs or [], "program")
        self._count("context", context)
        self._count("truth", truth)
        self._count("strategy", strategy)
        self._count("program", program)
        reused = [item for item in (context, truth, strategy, program) if item]
        self.reuse_events.extend(reused)
        return {
            "system": self.system_name,
            "knowledge_reused": bool(reused),
            "reused_context": context,
            "reused_truth": truth,
            "reused_strategy": strategy,
            "reused_program": program,
            **self.metrics(),
            "reason": "reuse_before_regenerate" if reused else "no_reusable_knowledge_found",
        }

    def metrics(self) -> dict[str, Any]:
        hits = self.context_hits + self.truth_hits + self.strategy_hits + self.program_hits
        misses = self.context_misses + self.truth_misses + self.strategy_misses + self.program_misses
        return {
            "context_hits": self.context_hits,
            "truth_hits": self.truth_hits,
            "strategy_hits": self.strategy_hits,
            "program_hits": self.program_hits,
            "context_misses": self.context_misses,
            "truth_misses": self.truth_misses,
            "strategy_misses": self.strategy_misses,
            "program_misses": self.program_misses,
            "knowledge_reuse_rate": round(hits / max(hits + misses, 1), 4),
            "knowledge_reuse_events": hits,
        }

    def report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "KNOWLEDGE REUSE REPORT": True,
            "reuse_events": list(self.reuse_events),
            **self.metrics(),
        }

    def _best(
        self,
        query: Mapping[str, Any] | str | None,
        candidates: list[Mapping[str, Any]],
        kind: str,
    ) -> dict[str, Any]:
        ranked = []
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            score = _similarity(query, candidate)
            if score >= 0.5:
                ranked.append({**dict(candidate), "reuse_kind": kind, "reuse_score": score})
        ranked.sort(key=lambda item: item["reuse_score"], reverse=True)
        return ranked[0] if ranked else {}

    def _count(self, kind: str, item: Mapping[str, Any]) -> None:
        attr = f"{kind}_hits" if item else f"{kind}_misses"
        setattr(self, attr, getattr(self, attr) + 1)

    def _stored_strategies(self) -> list[dict[str, Any]]:
        if self._strategy_cache is not None:
            return list(self._strategy_cache)
        root = Path("runtime/memory/storage/strategies")
        strategies = []
        if root.exists():
            for path in list(root.glob("*.json"))[:200]:
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                if isinstance(payload, Mapping):
                    strategy = payload.get("strategy", payload)
                    record = dict(strategy) if isinstance(strategy, Mapping) else {}
                    record["strategy_id"] = payload.get("strategy_id") or path.stem
                    record["name"] = record.get("type") or path.stem
                    record["concept"] = record.get("concept") or record.get("type")
                    strategies.append(record)
        self._strategy_cache = strategies
        return list(strategies)


def _similarity(query: Mapping[str, Any] | str | None, candidate: Mapping[str, Any]) -> float:
    if isinstance(query, Mapping):
        concept = str(query.get("concept") or query.get("truth_name") or "")
        query_text = json.dumps(query, sort_keys=True, default=str)
    else:
        concept = str(query or "")
        query_text = concept
    candidate_concept = str(candidate.get("concept") or candidate.get("truth_name") or candidate.get("name") or "")
    score = 0.0
    if concept and candidate_concept and concept == candidate_concept:
        score += 0.65
    score += _overlap(query_text, json.dumps(candidate, sort_keys=True, default=str)) * 0.25
    score += _confidence(candidate) * 0.10
    return round(min(1.0, score), 4)


def _overlap(left: str, right: str) -> float:
    left_tokens = {token for token in left.lower().replace("_", " ").split() if len(token) > 2}
    right_tokens = {token for token in right.lower().replace("_", " ").split() if len(token) > 2}
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _confidence(candidate: Mapping[str, Any]) -> float:
    for key in ("confidence", "truth_confidence", "support_score", "promotion_score"):
        try:
            return max(0.0, min(1.0, float(candidate.get(key, 0.0) or 0.0)))
        except (TypeError, ValueError):
            continue
    return 0.0


knowledge_reuse_engine = KnowledgeReuseEngine()


__all__ = ["KnowledgeReuseEngine", "knowledge_reuse_engine"]
