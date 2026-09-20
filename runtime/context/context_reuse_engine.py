"""Context reuse before context creation."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any, Iterable, Mapping

from runtime.cache.cache_keys import stable_hash


MAX_CONTEXT_SEARCH_RESULTS = 8
MAX_REUSE_ATTEMPTS = 3
MAX_TRUTH_VALIDATIONS = 24
MAX_CONTEXT_EXPANSION_DEPTH = 2


class ContextReuseEngine:
    system_name = "context_reuse_engine"

    def __init__(
        self,
        context_registry=None,
        cache_manager=None,
        max_results: int = MAX_CONTEXT_SEARCH_RESULTS,
        max_attempts: int = MAX_REUSE_ATTEMPTS,
    ):
        self.context_registry = context_registry
        self.cache_manager = cache_manager
        self.max_results = max(1, int(max_results or MAX_CONTEXT_SEARCH_RESULTS))
        self.max_attempts = max(1, int(max_attempts or MAX_REUSE_ATTEMPTS))
        self.lookup_count = 0
        self.context_hits = 0
        self.context_misses = 0
        self.reuse_events: list[dict[str, Any]] = []

    def search_similar_contexts(
        self,
        query: Mapping[str, Any] | str | None,
        registry=None,
        cache_manager=None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        self.lookup_count += 1
        registry = registry or self.context_registry
        cache_manager = cache_manager or self.cache_manager
        query_context = _normalize_query(query)
        candidates = self._registry_contexts(registry)
        candidates.extend(self._cache_contexts(cache_manager))
        ranked = []
        for candidate in candidates:
            score = self.rank_context_similarity(query_context, candidate)
            if score <= 0.0:
                continue
            ranked.append({
                **candidate,
                "similarity_score": score,
            })
        ranked.sort(
            key=lambda item: (
                item.get("similarity_score", 0.0),
                item.get("confidence", 0.0),
            ),
            reverse=True,
        )
        result_limit = max(1, min(int(limit or self.max_results), self.max_results))
        return ranked[:result_limit]

    def retrieve_context(
        self,
        context_id: str,
        registry=None,
        cache_manager=None,
    ) -> dict[str, Any]:
        registry = registry or self.context_registry
        if registry is not None and hasattr(registry, "get_context"):
            context = registry.get_context(context_id)
            if context:
                return context
        cache_manager = cache_manager or self.cache_manager
        if cache_manager is not None:
            value = cache_manager.get("context", key=str(context_id), context={})
            if isinstance(value, dict):
                return value
        return {}

    def rank_context_similarity(
        self,
        query: Mapping[str, Any] | str | None,
        context: Mapping[str, Any] | None,
    ) -> float:
        query = _normalize_query(query)
        context = dict(context) if isinstance(context, Mapping) else {}
        if not query or not context:
            return 0.0
        score = 0.0
        if query.get("concept") and query.get("concept") == context.get("concept"):
            score += 0.45
        if query.get("context_type") and query.get("context_type") == context.get("context_type"):
            score += 0.15
        score += _token_overlap(query, context) * 0.25
        score += _score(context.get("confidence", 0.0)) * 0.15
        return round(min(1.0, score), 4)

    def reuse_context(
        self,
        query: Mapping[str, Any] | str | None,
        registry=None,
        cache_manager=None,
        min_similarity: float = 0.62,
    ) -> dict[str, Any]:
        candidates = self.search_similar_contexts(
            query,
            registry=registry,
            cache_manager=cache_manager,
            limit=self.max_attempts,
        )
        reusable = [
            candidate
            for candidate in candidates
            if candidate.get("similarity_score", 0.0) >= min_similarity
        ]
        if reusable:
            self.context_hits += 1
            reused = [
                {
                    **candidate,
                    "context_reused": True,
                    "reuse_source": candidate.get("reuse_source", "context_registry"),
                }
                for candidate in reusable
            ]
            self.reuse_events.extend(reused)
            return {
                "system": self.system_name,
                "report_state": "final",
                "context_reused": True,
                "reused_contexts": reused,
                "context_lookup_count": self.lookup_count,
                "context_hits": self.context_hits,
                "context_misses": self.context_misses,
                "reuse_rate": self.reuse_rate,
                "reason": "similar_context_reused",
            }
        self.context_misses += 1
        return {
            "system": self.system_name,
            "report_state": "final",
            "context_reused": False,
            "reused_contexts": [],
            "context_lookup_count": self.lookup_count,
            "context_hits": self.context_hits,
            "context_misses": self.context_misses,
            "reuse_rate": self.reuse_rate,
            "reason": "no_similar_context_above_threshold",
        }

    @property
    def reuse_rate(self) -> float:
        total = self.context_hits + self.context_misses
        return round(self.context_hits / total, 4) if total else 0.0

    def report(self) -> dict[str, Any]:
        top = Counter(
            str(item.get("context_id") or item.get("concept") or "context")
            for item in self.reuse_events
        )
        return {
            "system": self.system_name,
            "report_state": "final",
            "context_lookup_count": self.lookup_count,
            "context_hits": self.context_hits,
            "context_misses": self.context_misses,
            "reuse_rate": self.reuse_rate,
            "top_reused_contexts": [
                {"context_id": context_id, "reuse_count": count}
                for context_id, count in top.most_common(5)
            ],
            "MAX_CONTEXT_SEARCH_RESULTS": self.max_results,
            "MAX_REUSE_ATTEMPTS": self.max_attempts,
            "MAX_TRUTH_VALIDATIONS": MAX_TRUTH_VALIDATIONS,
            "MAX_CONTEXT_EXPANSION_DEPTH": MAX_CONTEXT_EXPANSION_DEPTH,
            "adaptive_budget_control": {
                "reuse_before_creation": True,
                "reuse_is_cheaper_than_creation": True,
            },
        }

    def _registry_contexts(self, registry) -> list[dict[str, Any]]:
        if registry is None or not hasattr(registry, "all_contexts"):
            return []
        return [
            {**context, "reuse_source": "context_registry"}
            for context in registry.all_contexts()
            if isinstance(context, dict)
        ]

    def _cache_contexts(self, cache_manager) -> list[dict[str, Any]]:
        if cache_manager is None:
            return []
        try:
            store = cache_manager.caches["context"]
            store.load_with_timeout(getattr(cache_manager, "cache_load_timeout_seconds", 1.0))
        except Exception:
            return []
        contexts = []
        for key, entry in list(store.entries.items())[: self.max_results * 4]:
            value = entry.get("value") if isinstance(entry, dict) else None
            if isinstance(value, dict):
                contexts.append({
                    **value,
                    "context_id": value.get("context_id") or key,
                    "reuse_source": "context_cache",
                })
        return contexts


def _normalize_query(query: Mapping[str, Any] | str | None) -> dict[str, Any]:
    if isinstance(query, Mapping):
        return dict(query)
    if isinstance(query, str):
        return {
            "concept": query,
            "context_type": "SEMANTIC_CONTEXT",
            "query_signature": stable_hash(query),
        }
    return {}


def _token_overlap(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _tokens(value: Any) -> set[str]:
    try:
        text = json.dumps(value, sort_keys=True, default=str)
    except (TypeError, ValueError):
        text = str(value)
    return {
        token.strip().lower()
        for token in text.replace("_", " ").replace("-", " ").split()
        if len(token.strip()) > 2
    }


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


context_reuse_engine = ContextReuseEngine()


__all__ = [
    "ContextReuseEngine",
    "context_reuse_engine",
    "MAX_CONTEXT_SEARCH_RESULTS",
    "MAX_REUSE_ATTEMPTS",
    "MAX_TRUTH_VALIDATIONS",
    "MAX_CONTEXT_EXPANSION_DEPTH",
]
